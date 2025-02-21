# app/services/firebase_service.py
from typing import Dict, Any, List, Optional
from app.core.firebase_init import firebase
from firebase_admin import firestore

class FirebaseService:
    def __init__(self):
        self.db = firebase.db

    async def save_product_info(self, user_id: str, product_info: Dict[str, Any]) -> Optional[str]:
        try:
            # Create a reference to the user's products collection
            products_ref = self.db.collection('users').document(user_id).collection('products')
            
            # Add the product
            doc_ref = products_ref.add({
                'title': product_info.get('title'),
                'description': product_info.get('description'),
                'price': product_info.get('price'),
                'estimated_price': product_info.get('estimated_price', True),
                'category': product_info.get('category'),
                'brand': product_info.get('brand'),
                'images': product_info.get('images', []),
                'features': product_info.get('features', []),
                'specs': product_info.get('specs', {}),
                'created_at': firestore.SERVER_TIMESTAMP,
                'post_url': product_info.get('post_url')
            })
            
            return doc_ref[1].id
        except Exception as e:
            print(f"Error saving product info: {e}")
            return None

    async def save_post_link(self, user_id: str, post_link: str) -> Optional[str]:
        try:
            # Create a reference to the user's posts collection
            posts_ref = self.db.collection('users').document(user_id).collection('posts')
            
            # Add the post
            doc_ref = posts_ref.add({
                'post_url': post_link,
                'is_converted': False,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            
            return doc_ref[1].id
        except Exception as e:
            print(f"Error saving post link: {e}")
            return None
