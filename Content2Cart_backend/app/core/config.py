# app/core/config.py
from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

@dataclass
class Config:
    rapidapi_key: str
    openai_key: str
    google_api_key: str
    firebase_creds_path: str

    @classmethod
    def load_config(cls) -> Optional['Config']:
        load_dotenv()
        required_keys = [
            'RAPIDAPI_KEY', 
            'OPENAI_API_KEY', 
            'GOOGLE_API_KEY',
            'FIREBASE_CREDENTIALS_PATH'
        ]
        
        if not all(os.getenv(key) for key in required_keys):
            return None
            
        return cls(
            rapidapi_key=os.getenv('RAPIDAPI_KEY'),
            openai_key=os.getenv('OPENAI_API_KEY'),
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            firebase_creds_path=os.getenv('FIREBASE_CREDENTIALS_PATH')
        )
