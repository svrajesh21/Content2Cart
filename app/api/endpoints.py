# app/api/endpoints.py
from datetime import datetime
import json
import re
import aiohttp
from fastapi import APIRouter, HTTPException, Header, Depends, Request, Response
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.models.schemas import ImageInfo, ProductInfo, ProductResponse, AnalyzeRequest, ConvertRequest
from app.core.config import Config
from app.services.instagram_service import InstagramService
from firebase_admin import auth, firestore
from app.core.firebase_init import firebase
from app.services.firebase_service import FirebaseService

# Initialize router with prefix
router = APIRouter(prefix="/api")
firebase_service = FirebaseService()

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = authorization.replace('Bearer ', '')
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/analyze")
async def analyze_profile(request: AnalyzeRequest, auth_info: dict = Depends(get_current_user)):
    try:
        print(f"\nAnalyzing profile for username: {request.username}")
        
        config = Config.load_config()
        if not config:
            print("API configuration missing")
            raise HTTPException(status_code=500, detail="API configuration missing")
        
        instagram_service = InstagramService(config)
        results = await instagram_service.analyze_profile(request.username, auth_info['uid'])
        
        if not results:
            print("No results returned from Instagram service")
            return []
            
        print(f"Found {len(results)} posts to process")
        
        response_data = []
        current_timestamp = datetime.now().isoformat()
        
        for result in results:
            if not result:
                continue
                
            # Create post data incorporating both main image and carousel images
            post_data = {
                "post_url": result.post_url,
                "image_url": result.image_url,  # Main image URL
                "carousel_images": result.carousel_images,  # Carousel images array
                "title": result.title,
                "description": result.description,
                "price": result.price,
                "is_converted": False,
                "category": result.category,
                "brand": result.brand,
                "features": result.features,
                "specs": result.specs,
                "estimated_price": result.estimated_price,
                "timestamp": current_timestamp
            }
            
            try:
                print(f"\nSaving post data to Firebase:")
                print(f"Post URL: {post_data['post_url']}")
                print(f"Main Image URL: {post_data['image_url']}")
                print(f"Number of carousel images: {len(post_data['carousel_images'])}")
                
                posts_ref = firebase.db.collection('users').document(auth_info['uid']).collection('posts')
                
                firebase_data = post_data.copy()
                firebase_data['created_at'] = firestore.SERVER_TIMESTAMP
                del firebase_data['timestamp']
                
                query = posts_ref.where(filter=firestore.FieldFilter("post_url", "==", post_data['post_url']))
                existing_posts = query.limit(1).get()
                
                if not list(existing_posts):
                    doc_ref = posts_ref.add(firebase_data)
                    post_data['id'] = doc_ref[1].id
                    print(f"Created new post with ID: {post_data['id']}")
                else:
                    existing_post = list(existing_posts)[0]
                    post_data['id'] = existing_post.id
                    print(f"Post exists with ID: {post_data['id']}")
            
            except Exception as e:
                print(f"Error saving to Firebase: {e}")
            
            response_data.append(post_data)
        
        return response_data
        
    except Exception as e:
        print(f"Error in analyze_profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ImageConversionRequest(BaseModel):
    main_image_url: str
    carousel_image_urls: List[str] = []

# app/api/endpoints.py
@router.post("/proxy-image")
async def proxy_image(request: Request):
    try:
        data = await request.json()
        main_url = data.get('main_url')
        carousel_urls = data.get('carousel_urls', [])
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "image/webp,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.instagram.com/"
        }

        async with aiohttp.ClientSession() as session:
            # Get main image
            main_image = None
            if main_url:
                async with session.get(main_url, headers=headers) as response:
                    if response.status == 200:
                        main_image = await response.read()

            # Get carousel images
            carousel_images = []
            for url in carousel_urls:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        image = await response.read()
                        carousel_images.append(image)

        return Response(
            content=main_image if main_url else None,
            headers={'X-Carousel-Count': str(len(carousel_images))},
            media_type="image/jpeg"
        )

    except Exception as e:
        print(f"Error proxying images: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/posts")
async def get_user_posts(auth_info: dict = Depends(get_current_user)):
    try:
        posts_ref = firebase.db.collection('users').document(auth_info['uid']).collection('posts')
        posts = posts_ref.order_by('created_at', direction=firestore.Query.DESCENDING).get()
        
        response_data = []
        for doc in posts:
            post_data = doc.to_dict()
            if 'created_at' in post_data and post_data['created_at']:
                post_data['created_at'] = post_data['created_at'].isoformat() if hasattr(post_data['created_at'], 'isoformat') else None
            response_data.append({'id': doc.id, **post_data})
            
        return response_data
    except Exception as e:
        print(f"Error fetching user posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
