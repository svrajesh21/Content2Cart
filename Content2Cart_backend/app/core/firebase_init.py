# app/core/firebase_init.py
import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import Config
from typing import Optional

class FirebaseInit:
    _instance = None
    _db = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseInit, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not FirebaseInit._initialized:
            self._initialize_firebase()

    def _initialize_firebase(self):
        try:
            config = Config.load_config()
            if not config:
                raise Exception("Failed to load configuration")

            # Check if Firebase is already initialized
            if not len(firebase_admin._apps):
                cred = credentials.Certificate(config.firebase_creds_path)
                firebase_admin.initialize_app(cred)
                print("Firebase initialized successfully")
            
            FirebaseInit._db = firestore.client()
            FirebaseInit._initialized = True
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            raise

    @property
    def db(self) -> Optional[firestore.Client]:
        if not self._initialized:
            self._initialize_firebase()
        return self._db

firebase = FirebaseInit()
