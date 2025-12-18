from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .database import init_db
from .routes import chat, agents, files

# Initialize FastAPI app
app = FastAPI(
    title="Nexus-Mind API",
    description="Multi-Agent Corporate Knowledge System API",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
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
    print("Initializing database...")
    init_db()
    print("Database initialized successfully")
    print(f"API server ready at http://0.0.0.0:8000")
    print(f"API docs available at http://0.0.0.0:8000/docs")

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
