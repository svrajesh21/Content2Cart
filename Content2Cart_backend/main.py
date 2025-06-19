# main.py
import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
from app.core.firebase_init import firebase
import logging
from dotenv import load_dotenv

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Instagram Analyzer API")

SERVER_IP = os.getenv('SERVER_IP')
SERVER_PORT = int(os.getenv('SERVER_PORT', '3000'))
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Configure CORS
origins = ["*"] if ENVIRONMENT == 'development' else [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://content2cart.firebaseapp.com",
    "https://content2cart.web.app",
]

if SERVER_IP:
    origins.extend([
        f"http://{SERVER_IP}:3000",
        f"http://{SERVER_IP}:8000",
        f"http://{SERVER_IP}"
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMPORTANT: Remove the prefix here since it's already in the router
app.include_router(router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "server_ip": SERVER_IP,
        "server_port": SERVER_PORT
    }

if __name__ == "__main__":
    if not SERVER_IP:
        logger.error("SERVER_IP environment variable is not set!")
        sys.exit(1)
        
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVER_PORT,
        reload=True,
        log_level="info"
    )# main.py
import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
from app.core.firebase_init import firebase
import logging
from dotenv import load_dotenv

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Instagram Analyzer API")

SERVER_IP = os.getenv('SERVER_IP')
SERVER_PORT = int(os.getenv('SERVER_PORT', '3000'))
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Configure CORS
origins = ["*"] if ENVIRONMENT == 'development' else [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://content2cart.firebaseapp.com",
    "https://content2cart.web.app",
]

if SERVER_IP:
    origins.extend([
        f"http://{SERVER_IP}:3000",
        f"http://{SERVER_IP}:8000",
        f"http://{SERVER_IP}"
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMPORTANT: Remove the prefix here since it's already in the router
app.include_router(router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "server_ip": SERVER_IP,
        "server_port": SERVER_PORT
    }

if __name__ == "__main__":
    if not SERVER_IP:
        logger.error("SERVER_IP environment variable is not set!")
        sys.exit(1)
        
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVER_PORT,
        reload=True,
        log_level="info"
    )
