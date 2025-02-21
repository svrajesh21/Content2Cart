# app/services/instagram_service.py
import aiohttp
from typing import List, Dict, Optional
import json
from app.services.image_analyzer import GeminiImageAnalyzer
from app.models.schemas import ProductInfo
from openai import OpenAI
import re
from app.core.firebase_init import firebase
from firebase_admin import firestore

class InstagramService:
    def _init_(self, config):
        self.rapidapi_key = config.rapidapi_key
        self.openai_client = OpenAI(api_key=config.openai_key)
        self.gemini_analyzer = GeminiImageAnalyzer(config.google_api_key)
        self.api_url = "https://instagram-scraper-api2.p.rapidapi.com/v1.1/posts"
        self.db = firebase.db

    async def fetch_profile_posts(self, username: str) -> List[Dict]:
        print(f"\nFetching posts for username: {username}")
        async with aiohttp.ClientSession() as session:
            username = username.strip().replace('@', '')
            
            headers = {
                "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com",
                "x-rapidapi-key": "c5d251f0ecmsh248b5965cc738dbp1b91aejsnf6f019c58a1c"
            }
            
            # Using the v1.1 endpoint as specified in the curl command
            url = f"https://instagram-scraper-api2.p.rapidapi.com/v1.1/posts"
            params = {
                "username_or_id_or_url": username
            }
            
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    print(f"Request URL: {response.url}")
                    print(f"Request Headers: {headers}")
                    print(f"Response Status: {response.status}")
                    
                    if response.status != 200:
                        print(f"API returned status code: {response.status}")
                        response_text = await response.text()
                        print(f"Error response: {response_text}")
                        return []

                    data = await response.json()
                    print(f"API response structure: {list(data.keys())}")
                    
                    if 'data' not in data:
                        print("No data in API response")
                        return []
                    
                    data_content = data.get("data", {})
                    if not isinstance(data_content, dict):
                        print(f"Unexpected data type: {type(data_content)}")
                        return []

                    items = data_content.get("items", [])
                    if not isinstance(items, list):
                        print(f"Unexpected items type: {type(items)}")
                        return []

                    print(f"Found {len(items)} total posts")
                    
                    image_posts = []
                    skipped_count = 0
                    
                    for post in items:
                        try:
                            if self._is_image_post(post):
                                processed_post = self._process_single_post(post)
                                if processed_post:
                                    image_posts.append(processed_post)
                                    print(f"Found image post {len(image_posts)}/5: {processed_post['post_link']}")
                                    if len(image_posts) >= 5:
                                        break
                            else:
                                skipped_count += 1
                                print(f"Skipped non-image post: {post.get('code')} (media_type: {post.get('media_type')})")
                        except Exception as post_error:
                            print(f"Error processing individual post: {post_error}")
                            continue
                    
                    print(f"\nTotal posts processed: {len(image_posts)} (Skipped {skipped_count} non-image posts)")
                    return image_posts

            except Exception as e:
                print(f"Error making request: {e}")
                print(f"Error type: {type(e)}")
                print(f"Error details: {str(e)}")
                return []
    def _is_image_post(self, post: Dict) -> bool:
        media_type = post.get("media_type")
        
        # Handle carousel media (type 8 is a carousel/album)
        if media_type == 8 or "carousel_media" in post:
            # For carousels, check if at least one item is an image
            if "carousel_media" in post and isinstance(post["carousel_media"], list):
                return any(self._is_media_item_image(item) for item in post["carousel_media"])
            return True
        
        # For single posts
        if isinstance(media_type, int):
            is_image = media_type == 1
        else:
            media_type = str(media_type).lower()
            is_image = media_type in ["image", "photo", "1"]
        
        return is_image

    def _is_media_item_image(self, item: Dict) -> bool:
        media_type = item.get("media_type")
        
        # Consider all items with a thumbnail_url as valid images
        if "thumbnail_url" in item:
            return True
        
        if isinstance(media_type, int):
            return media_type == 1
        
        media_type = str(media_type).lower()
        return media_type in ["image", "photo", "1"]
      
    def _process_single_post(self, post: Dict) -> Optional[Dict]:
        try:
            if not isinstance(post, dict):
                print(f"Invalid post type: {type(post)}")
                return None

            # Extract and validate post code
            post_code = post.get('code')
            if not post_code:
                print("No post code found")
                return None

            instagram_post_url = f"https://www.instagram.com/p/{post_code}/"
            
            # Handle carousel posts (media_type 8 or has resources)
            carousel_images = []
            if post.get('media_type') == 8 and 'resources' in post:
                print("Processing carousel post")
                # Get images from resources
                for resource in post['resources']:
                    if (resource.get('image_versions') and 
                        isinstance(resource['image_versions'], list) and 
                        len(resource['image_versions']) > 0):
                        img_url = resource['image_versions'][0]['url']
                        carousel_images.append(img_url)
                
                # Main image is the first carousel item
                main_image_url = carousel_images[0] if carousel_images else ''
                
            else:
                # For single image posts, get from image_versions
                print("Processing single image post")
                main_image_url = (post.get('image_versions', [{}])[0].get('url', '') 
                                if post.get('image_versions') else '')
                carousel_images = []

            # Extract caption safely
            caption_data = post.get("caption", {})
            caption_text = ""
            if isinstance(caption_data, dict):
                caption_text = caption_data.get("text", "")
            elif isinstance(caption_data, str):
                caption_text = caption_data

            processed_post = {
                "post_link": instagram_post_url,
                "image_url": main_image_url,
                "carousel_images": carousel_images,
                "images": [{"url": main_image_url, "source": "Image", "id": str(post.get("id", "Unknown"))}] + [
                    {"url": img_url, "source": "Image", "id": f"carousel_{idx}"} 
                    for idx, img_url in enumerate(carousel_images)
                ],
                "caption": caption_text,
                "media_type": str(post.get("media_type", "")),
                "title": "",
                "description": "",
                "price": 0.0
            }
            
            print(f"Successfully processed post:")
            print(f"- URL: {processed_post['post_link']}")
            print(f"- Main image: {processed_post['image_url']}")
            print(f"- Carousel images: {len(processed_post['carousel_images'])}")
            
            return processed_post
                
        except Exception as e:
            print(f"Error processing post: {e}")
            print(f"Post data: {json.dumps(post, indent=2)}")
            return None
                    

    def _extract_images(self, post: Dict) -> List[Dict]:
        images = []
        
        if "carousel_media" in post:
            for media in post["carousel_media"]:
                if image_url := self._get_image_url(media):
                    images.append(image_url)
        elif image_url := self._get_image_url(post):
            images.append(image_url)
            
        return images

    def _get_image_url(self, media: Dict) -> Optional[Dict]:
        if "image_versions" in media and "items" in media["image_versions"]:
            first_image = media["image_versions"]["items"][0]
            if "url" in first_image:
                return self._create_image_dict(first_image, media.get("id", "Unknown"))
        
        if "image_versions2" in media and "candidates" in media["image_versions2"]:
            first_image = media["image_versions2"]["candidates"][0]
            if "url" in first_image:
                return self._create_image_dict(first_image, media.get("id", "Unknown"))
        
        return None

    def _create_image_dict(self, image: Dict, image_id: str) -> Dict:
        return {
            "url": image["url"],
            "source": "Image",
            "id": str(image_id),
            "width": image.get("width", 0),
            "height": image.get("height", 0)
        }

    def analyze_post_content(self, post_data: Dict) -> Optional[ProductInfo]:
            try:
                if 'images' not in post_data:
                    print("No images key in post_data")
                    return None
                    
                images = post_data['images']
                post_url = post_data['post_link']
                main_image_url = post_data['image_url']
                carousel_images = post_data.get('carousel_images', [])
                  
                print(f"Processing post with URL: {post_url}")
                print(f"Main image URL: {main_image_url}")
                print(f"Number of carousel images: {len(carousel_images)}")
                
                # Enhanced price extraction patterns to match more formats
                price_patterns = [
                    r'(?:INR|₹|Rs\.?)\s*(\d+(?:,\d+)*(?:\.\d+)?)',  # INR 3999 or ₹3,999 or Rs. 3999
                    r'priced at (?:INR|₹|Rs\.?)\s*(\d+(?:,\d+)*(?:\.\d+)?)',  # priced at INR 3999
                    r'price[d]?\s*(?:is|:)?\s*(?:INR|₹|Rs\.?)\s*(\d+(?:,\d+)*(?:\.\d+)?)',  # price: INR 3999
                    r'(?:INR|₹|Rs\.?)\s*(\d+(?:,\d+)(?:\.\d+)?)\s(?:only|onwards)?',  # INR 3999 only
                    r'(\d+(?:,\d+)(?:\.\d+)?)\s/-',  # 3,900/-
                    r'Rs\.\s*(\d+(?:,\d+)*(?:\.\d+)?)',  # Rs. 3999
                    r'(\d+(?:,\d+)(?:\.\d+)?)\s(?:Rs\.?|₹|INR)'  # 3999 Rs or 3999 ₹
                ]
                
                price = None
                for pattern in price_patterns:
                    price_match = re.search(pattern, post_data['caption'], re.IGNORECASE)
                    if price_match:
                        price = float(price_match.group(1).replace(',', ''))
                        print(f"Found explicit price in caption: {price}")
                        break
                
                brand = self._extract_brand_from_text(post_data['caption'])
                image_analysis = self.gemini_analyzer.analyze_image(images)
                    
                prompt = f"""
                Create a detailed product listing using this information:
                Image Analysis: {image_analysis}
                Caption: {post_data['caption']}
                Brand: {brand}
                Number of carousel images: {len(carousel_images)}
                
                Return a JSON with these exact fields:
                {{
                    "title": "product name (without assuming brand if unknown)",
                    "description": "detailed product description",
                    "category": "product category",
                    "features": ["3 key features"],
                    "specifications": {{"key specs": "values"}}
                }}
                Focus on accuracy and include only confirmed details from the image or caption.
                Do not make assumptions about the brand name.
                """

                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Create accurate product listings from social media posts without making brand assumptions."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=300
                )

                ai_data = json.loads(response.choices[0].message.content)
                
                # Only estimate price if no explicit price was found
                if price is None:
                    price = self._estimate_price(
                        ai_data.get('category', ''),
                        ai_data.get('features', []),
                        ai_data.get('specifications', {}),
                        brand
                    )
                    estimated = True
                else:
                    estimated = False
                
                return ProductInfo(
                    title=ai_data.get('title', 'Product name not available'),
                    description=ai_data.get('description', 'No description available'),
                    price=price,
                    estimated_price=estimated,
                    category=ai_data.get('category', 'Category not available'),
                    brand=brand,
                    image_url=main_image_url,
                    carousel_images=carousel_images,
                    images=images,
                    features=ai_data.get('features', []),
                    specs=ai_data.get('specifications', {}),
                    post_url=post_url
                )
            except Exception as e:
                print(f"Error in post analysis: {e}")
                return None

    def _extract_brand_from_text(self, text: str) -> str:
        try:
            hashtags = re.findall(r'#(\w+)', text)
            prompt = f"""
            Extract the brand name from this text and hashtags. Only return a brand name if it's explicitly mentioned.
            If no brand is clearly mentioned, return "Unknown".
            
            Text: {text}
            Hashtags: {', '.join(hashtags)}
            
            Return only the brand name or "Unknown" with no additional text.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract brand names from text, defaulting to Unknown if uncertain."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50
            )
            
            brand = response.choices[0].message.content.strip()
            return "Unknown" if brand.lower() == "unknown" else brand

        except Exception as e:
            print(f"Error extracting brand: {e}")
            return "Unknown"

    def _estimate_price(self, category: str, features: List[str], specs: Dict[str, str], brand: str) -> float:
        try:
            prompt = f"""
            Based on the following product details, estimate a reasonable market price in Indian Rupees (₹):
            Category: {category}
            Brand: {brand}
            Features: {', '.join(features)}
            Specifications: {json.dumps(specs)}
            
            Consider factors like:
            1. Material quality and craftsmanship
            2. Similar products in the Indian market
            3. Design complexity and features
            
            Return only a number representing the estimated price in INR without any text.
            Example: 2499
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a retail pricing expert for the Indian market."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50
            )
            
            price_text = response.choices[0].message.content.strip()
            price = float(re.sub(r'[^\d.]', '', price_text))
            return price
        except Exception as e:
            print(f"Error estimating price: {e}")
            return 0.0

    async def analyze_profile(self, username: str, user_id: str) -> List[ProductInfo]:
        posts = await self.fetch_profile_posts(username)
        results = []
        
        if posts:
            print(f"\nAnalyzing {len(posts)} posts...")
            for i, post in enumerate(posts, 1):
                print(f"\n{'='*50}")
                print(f"Processing post {i}/{len(posts)}")
                print(f"Post Link: {post.get('post_link')}")
                print(f"Image URL: {post.get('image_url')}")
                print(f"Carousel images: {len(post.get('carousel_images', []))}")
                
                result = self.analyze_post_content(post)
                if result:
                    results.append(result)
                    print(f"Successfully analyzed post {i}")
                else:
                    print(f"Failed to analyze post {i}")
        
        return results

    async def analyze_single_post(self, post_url: str) -> Optional[ProductInfo]:
        try:
            post_code = post_url.split('/')[-1]
            if not post_code:
                return None

            params = {"post_code": post_code}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url,
                    headers={
                        "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com",
                        "x-rapidapi-key": self.rapidapi_key
                    },
                    params=params
                ) as response:
                    data = await response.json()
                    if 'data' not in data:
                        return None

                    post = data['data']
                    processed_post = self._process_single_post(post)
                    if not processed_post:
                        return None

                    return self.analyze_post_content(processed_post)

        except Exception as e:
            print(f"Error in analyze_single_post: {e}")
            return None
