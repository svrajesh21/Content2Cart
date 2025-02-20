{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "outputs": [
    {
     "ename": "ModuleNotFoundError",
     "evalue": "No module named 'dotenv'",
     "output_type": "error",
     "traceback": [
      "\u001b[1;31m---------------------------------------------------------------------------\u001b[0m",
      "\u001b[1;31mModuleNotFoundError\u001b[0m                       Traceback (most recent call last)",
      "Cell \u001b[1;32mIn[1], line 6\u001b[0m\n\u001b[0;32m      4\u001b[0m \u001b[38;5;28;01mimport\u001b[39;00m \u001b[38;5;21;01mos\u001b[39;00m\n\u001b[0;32m      5\u001b[0m \u001b[38;5;28;01mfrom\u001b[39;00m \u001b[38;5;21;01mopenai\u001b[39;00m \u001b[38;5;28;01mimport\u001b[39;00m OpenAI\n\u001b[1;32m----> 6\u001b[0m \u001b[38;5;28;01mfrom\u001b[39;00m \u001b[38;5;21;01mdotenv\u001b[39;00m \u001b[38;5;28;01mimport\u001b[39;00m load_dotenv\n\u001b[0;32m      8\u001b[0m \u001b[38;5;66;03m# Load environment variables\u001b[39;00m\n\u001b[0;32m      9\u001b[0m load_dotenv()\n",
      "\u001b[1;31mModuleNotFoundError\u001b[0m: No module named 'dotenv'"
     ]
    }
   ],
   "source": [
    "import requests\n",
    "from typing import Dict, List, Optional\n",
    "from dataclasses import dataclass\n",
    "import os\n",
    "from openai import OpenAI\n",
    "from dotenv import load_dotenv\n",
    "\n",
    "# Load environment variables\n",
    "load_dotenv()\n",
    "\n",
    "@dataclass\n",
    "class ProductInfo:\n",
    "    title: str\n",
    "    description: str\n",
    "    price: float\n",
    "    category: str\n",
    "    images: List[str]\n",
    "    features: List[str]\n",
    "    specs: Dict[str, str]\n",
    "\n",
    "class InstagramAIAnalyzer:\n",
    "    def __init__(self, instagram_api_key: str = None, openai_api_key: str = None):\n",
    "        # Use parameters if provided, otherwise use environment variables\n",
    "        self.instagram_api_key = instagram_api_key or os.getenv('INSTAGRAM_API_KEY')\n",
    "        openai_key = openai_api_key or os.getenv('OPENAI_API_KEY')\n",
    "        \n",
    "        if not self.instagram_api_key:\n",
    "            raise ValueError(\"Instagram API key is required. Set INSTAGRAM_API_KEY environment variable or pass it to the constructor.\")\n",
    "        \n",
    "        if not openai_key:\n",
    "            raise ValueError(\"OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to the constructor.\")\n",
    "            \n",
    "        self.ai_client = OpenAI(api_key=openai_key)\n",
    "\n",
    "    def fetch_post_data(self, post_url: str) -> Dict:\n",
    "        \"\"\"\n",
    "        Fetch data from Instagram Business API\n",
    "        \"\"\"\n",
    "        if not post_url:\n",
    "            raise ValueError(\"Post URL is required\")\n",
    "            \n",
    "        # Extract post ID from URL\n",
    "        try:\n",
    "            post_id = post_url.split('/')[-2]\n",
    "        except IndexError:\n",
    "            raise ValueError(\"Invalid Instagram post URL format\")\n",
    "        \n",
    "        headers = {'Authorization': f'Bearer {self.instagram_api_key}'}\n",
    "        endpoint = f'https://graph.instagram.com/v17.0/{post_id}'  # Updated to v17.0\n",
    "        params = {\n",
    "            'fields': 'id,caption,media_type,media_url,permalink,thumbnail_url,children{media_url}'\n",
    "        }\n",
    "        \n",
    "        try:\n",
    "            response = requests.get(endpoint, headers=headers, params=params)\n",
    "            response.raise_for_status()  # Raise exception for bad status codes\n",
    "            return response.json()\n",
    "        except requests.exceptions.RequestException as e:\n",
    "            print(f\"Error fetching Instagram data: {e}\")\n",
    "            return {}\n",
    "\n",
    "    # ... rest of the code remains the same ...\n",
    "\n",
    "def main():\n",
    "    try:\n",
    "        # Initialize analyzer (will use environment variables)\n",
    "        analyzer = InstagramAIAnalyzer()\n",
    "        \n",
    "        # Example usage\n",
    "        post_url = input(\"Enter Instagram post URL: \")\n",
    "        result = analyzer.analyze_post(post_url)\n",
    "        \n",
    "        if result:\n",
    "            print(\"\\nProduct Analysis Results:\")\n",
    "            print(f\"Title: {result.title}\")\n",
    "            print(f\"Description: {result.description}\")\n",
    "            print(f\"Price: ${result.price}\")\n",
    "            print(f\"Category: {result.category}\")\n",
    "            print(f\"Images: {len(result.images)} found\")\n",
    "            print(f\"Features: {', '.join(result.features)}\")\n",
    "            print(f\"Specifications: {result.specs}\")\n",
    "        else:\n",
    "            print(\"No results found or error occurred\")\n",
    "            \n",
    "    except Exception as e:\n",
    "        print(f\"Error: {e}\")\n",
    "\n",
    "if __name__ == \"__main__\":\n",
    "    main()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.9"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
