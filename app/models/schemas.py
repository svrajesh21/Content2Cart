# app/models/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from dataclasses import dataclass

class ImageInfo(BaseModel):
    url: str
    source: str
    id: str
    width: int
    height: int

class ProductResponse(BaseModel):
    title: str
    description: str
    price: float
    estimated_price: bool
    category: str
    brand: str
    image_url: str  # Main image URL
    carousel_images: List[str] = []  # Optional carousel images
    features: List[str]
    specs: dict

class AnalyzeRequest(BaseModel):
    username: str

class ConvertRequest(BaseModel):
    post_url: str

@dataclass
class ProductInfo:
    title: str
    description: str 
    price: float
    estimated_price: bool
    category: str
    brand: str
    image_url: str  # Main image URL
    carousel_images: List[str]  # Carousel images
    images: List[Dict]  # Keep full image info for analysis
    features: List[str]
    specs: Dict[str, str]
    post_url: str  # Instagram post URL
