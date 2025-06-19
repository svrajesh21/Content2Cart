# cli_analyzer.py
import sys
import os
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

import asyncio
from typing import List, Dict, Optional
import json
import aiohttp
from openai import OpenAI
import re

# Import your existing classes
try:
    from app.services.instagram_service import InstagramService
    from app.core.config import Settings
except ImportError:
    # If imports fail, define minimal config class
    class Settings:
        def __init__(self):
            self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
            self.openai_key = os.getenv('OPENAI_API_KEY')
            self.google_api_key = os.getenv('GOOGLE_API_KEY')

    # Import other necessary classes
    from app.services.image_analyzer import GeminiImageAnalyzer
    from app.models.schemas import ProductInfo

async def analyze_profile_cli():
    # Initialize settings and service
    config = Settings()
    instagram_service = InstagramService(config)
    
    while True:
        print("\n" + "="*50)
        print("Instagram Profile Analyzer")
        print("="*50)
        username = input("\nEnter Instagram username (or 'exit' to quit): ").strip()
        
        if username.lower() == 'exit':
            print("\nExiting program...")
            break
            
        print(f"\nAnalyzing profile: @{username}")
        print("This may take a few minutes...\n")
        
        try:
            # Use a placeholder user_id since we don't need authentication for CLI
            results = await instagram_service.analyze_profile(username, "cli_user")
            
            if not results:
                print("No results found for this profile.")
                continue
                
            print("\n" + "="*50)
            print(f"Analysis Results for @{username}")
            print("="*50)
            
            for i, product in enumerate(results, 1):
                print(f"\nProduct {i}:")
                print("-" * 30)
                print(f"Title: {product.title}")
                print(f"Brand: {product.brand}")
                print(f"Category: {product.category}")
                print(f"Price: ₹{product.price:.2f}")
                if product.estimated_price:
                    print("(Estimated price)")
                print(f"\nDescription: {product.description}")
                print("\nFeatures:")
                for feature in product.features:
                    print(f"- {feature}")
                print("\nSpecifications:")
                for key, value in product.specs.items():
                    print(f"- {key}: {value}")
                print(f"\nPost URL: {product.post_url}")
                print("-" * 30)
            
        except Exception as e:
            print(f"\nError analyzing profile: {e}")
            print("Please try again with a different username.")

def main():
    # Check if required environment variables are set
    required_env_vars = ['RAPIDAPI_KEY', 'OPENAI_API_KEY', 'GOOGLE_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease set these environment variables before running the script.")
        return

    # Run the CLI analyzer
    asyncio.run(analyze_profile_cli())

if __name__ == "__main__":
    main()
