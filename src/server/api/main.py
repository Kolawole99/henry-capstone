from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from .database import init_db
from .routes import chat, agents, files
from .middleware import LoggingMiddleware
from ..utils.logger import setup_logging, get_logger

# Initialize logging system
setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nexus-Mind API",
    description="Multi-Agent Corporate Knowledge System API",
    version="1.0.0"
)

# Add logging middleware (should be first to capture all requests)
app.add_middleware(LoggingMiddleware)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, tags=["chat"])
app.include_router(agents.router, tags=["agents"])
app.include_router(files.router, tags=["files"])

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Nexus-Mind API server")
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    logger.info("API server ready", extra={
        'extra_fields': {
            'host': '0.0.0.0',
            'port': 8001,
            'docs_url': 'http://0.0.0.0:8001/docs'
        }
    })

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Nexus-Mind API server")

@app.get("/")
async def root():
    return {
        "message": "Nexus-Mind API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

