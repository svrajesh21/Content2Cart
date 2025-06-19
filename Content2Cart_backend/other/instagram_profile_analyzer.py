import os
os.environ['GRPC_ENABLE_FORK_SUPPORT'] = '0'
os.environ['GRPC_PYTHON_LOG_LEVEL'] = 'ERROR'
import asyncio
import aiohttp
import google.generativeai as genai
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import re
from PIL import Image
import requests
from io import BytesIO

@dataclass
class ProductInfo:
    title: str
    description: str 
    price: float
    estimated_price: bool
    category: str
    brand: str  # Added brand field
    images: List[Dict]
    features: List[str]
    specs: Dict[str, str]

class GeminiImageAnalyzer:
    def __init__(self, google_api_key: str):
        self.api_key = google_api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    
    def __del__(self):
        """Cleanup method"""
        if hasattr(self, 'model'):
            del self.model    

    def analyze_image(self, image_urls: List[Dict]) -> str:
        """Analyze first carousel image"""
        try:
            if not image_urls:
                return ""
            
            response = requests.get(image_urls[0]['url'])
            img = Image.open(BytesIO(response.content))
            
            prompt = """Analyze this product image in detail. Focus on:
            1. Product type and main category
            2. Colors and materials visible
            3. Key design features
            4. Any visible text or logos
            5. Style and intended use
            Be specific and detailed but concise. Do not make assumptions about the brand."""
            
            response = self.model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return ""

class InstagramAnalyzer:
    def __init__(self, rapidapi_key: str, openai_key: str, google_api_key: str):
        self.rapidapi_key = rapidapi_key
        self.openai_client = OpenAI(api_key=openai_key)
        self.gemini_analyzer = GeminiImageAnalyzer(google_api_key)
        self.api_url = "https://instagram-scraper-api2.p.rapidapi.com/v1.2/posts"

    def extract_brand_from_text(self, text: str) -> str:
        """Extract brand name from caption or hashtags"""
        try:
            # Look for hashtags with brand names
            hashtags = re.findall(r'#(\w+)', text)
            
            # Create a prompt to identify brand from text and hashtags
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

    def estimate_price(self, category: str, features: List[str], specs: Dict[str, str], brand: str) -> float:
        """Estimate product price based on category and features"""
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

    async def fetch_profile_posts(self, username: str) -> List[Dict]:
      async with aiohttp.ClientSession() as session:
          username = username.strip().replace('@', '')
          headers = {
              "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com",
              "x-rapidapi-key": self.rapidapi_key
          }
          
          params = {"username_or_id_or_url": username}
          
          try:
              async with session.get(self.api_url, headers=headers, params=params) as response:
                  data = await response.json()
                  
                  if 'data' not in data:
                      return []
                  
                  all_posts = data.get("data", {}).get("items", [])
                  if not all_posts:
                      return []
                  
                  posts_to_process = all_posts[:5] if len(all_posts) > 5 else all_posts
                  processed_posts = []
                  
                  for post in posts_to_process:
                      images = []
                      
                      # Handle carousel media
                      if "carousel_media" in post:
                          for index, media in enumerate(post["carousel_media"], 1):
                              if "image_versions" in media and "items" in media["image_versions"]:
                                  first_image = media["image_versions"]["items"][0]
                                  if "url" in first_image:
                                      images.append({
                                          "url": first_image["url"],
                                          "source": f"Image {index}",
                                          "id": media.get("id", "Unknown ID"),
                                          "width": first_image.get("width", 0),
                                          "height": first_image.get("height", 0)
                                      })
                      
                      # Handle single image - try image_versions first
                      if not images:
                          if "image_versions" in post and "items" in post["image_versions"]:
                              main_image = post["image_versions"]["items"][0]
                              if "url" in main_image:
                                  images.append({
                                      "url": main_image["url"],
                                      "source": "Main Image",
                                      "id": post.get("id", "Unknown ID"),
                                      "width": main_image.get("width", 0),
                                      "height": main_image.get("height", 0)
                                  })
                          
                          # If still no images, try image_versions2
                          if not images and "image_versions2" in post:
                              if "candidates" in post["image_versions2"]:
                                  main_image = post["image_versions2"]["candidates"][0]
                                  if "url" in main_image:
                                      images.append({
                                          "url": main_image["url"],
                                          "source": "Main Post Image",
                                          "id": post.get("id", "Unknown ID"),
                                          "width": main_image.get("width", 0),
                                          "height": main_image.get("height", 0)
                                      })
                      
                      if images:
                          processed_posts.append({
                              "post_link": f"https://www.instagram.com/p/{post.get('code')}/",
                              "caption": post.get("caption", {}).get("text", ""),
                              "media_type": post.get("media_type", ""),
                              "images": images
                          })
                  
                  return processed_posts
                      
          except Exception as e:
              return []

    def analyze_post_content(self, post_data: Dict) -> Optional[ProductInfo]:
        """Analyze post content with carousel images and price estimation"""
        try:
            # Extract price if present
            price_match = re.search(r'(?:₹|Rs\.?)\s*(\d+(?:,\d+)*(?:\.\d+)?)', post_data['caption'])
            price = float(price_match.group(1).replace(',', '')) if price_match else None
            
            # Extract brand from caption and hashtags
            brand = self.extract_brand_from_text(post_data['caption'])
            
            # Analyze images
            image_analysis = self.gemini_analyzer.analyze_image(post_data['images'])
                
            # Create product info using GPT
            prompt = f"""
            Create a detailed product listing using this information:
            Image Analysis: {image_analysis}
            Caption: {post_data['caption']}
            Brand: {brand}
            Number of carousel images: {len(post_data.get('images', []))}
            
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
            
            # If no price found, estimate it
            if price is None:
                price = self.estimate_price(
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
                images=post_data.get('images', []),
                features=ai_data.get('features', []),
                specs=ai_data.get('specifications', {})
            )
        except Exception as e:
            print(f"Error in post analysis: {e}")
            return None

    async def analyze_profile(self, username: str) -> List[ProductInfo]:
        """Analyze all posts from a profile"""
        posts = await self.fetch_profile_posts(username)
        results = []
        
        if posts:
            print(f"\nAnalyzing {len(posts)} posts...")
            for i, post in enumerate(posts, 1):
                print(f"\nAnalyzing post {i}/{len(posts)}")
                print(f"Number of carousel images found: {len(post.get('images', []))}")
                result = self.analyze_post_content(post)
                if result:
                    results.append(result)
        
        return results

async def main():
    try:
        rapidapi_key = os.getenv('RAPIDAPI_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        google_api_key = os.getenv('GOOGLE_API_KEY')
        
        if not all([rapidapi_key, openai_key, google_api_key]):
            print("Please set all required API keys in .env file")
            return
        
        analyzer = InstagramAnalyzer(rapidapi_key, openai_key, google_api_key)
        profile = input("Enter Instagram username or profile URL: ")
        
        results = await analyzer.analyze_profile(profile)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\nProduct {i}:")
                print(f"Title: {result.title}")
                print(f"Brand: {result.brand}")
                print(f"Description: {result.description}")
                print(f"Price: ₹{result.price:.2f}" + (" (Estimated)" if result.estimated_price else ""))
                print(f"Category: {result.category}")
                print(f"Features: {', '.join(result.features)}")
                print("Specifications:")
                for key, value in result.specs.items():
                    print(f"  {key}: {value}")
                print("\nImages:")
                for img in result.images:
                    print(f"  {img['url']}")
                print("-" * 50)
            print(f"\nTotal posts analyzed: {len(results)}")
        else:
            print("No results found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        if os.name == 'nt':  # Windows
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    finally:
        # Properly close the event loop
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        except:
            pass





# uvicorn main:app --host 0.0.0.0 --port 3000 --reload --log-level debug
