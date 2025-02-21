# app/services/image_analyzer.py
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO
from typing import List, Dict

class GeminiImageAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    
    def __del__(self):
        if hasattr(self, 'model'):
            del self.model    

    def analyze_image(self, image_urls: List[Dict]) -> str:
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
