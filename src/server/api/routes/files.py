from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import uuid
import os
import shutil

from ..database import get_db, File, Agent
from ...utils.vector_store import VectorStoreManager

router = APIRouter()

# Upload directory
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Response models
class FileResponse(BaseModel):
    id: str
    name: str
    size: int
    uploadedAt: str

    class Config:
        from_attributes = True

@router.get("/agents/{agent_id}/files", response_model=List[FileResponse])
async def list_agent_files(agent_id: str, db: Session = Depends(get_db)):
    """Get all files for a specific agent"""
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    files = db.query(File).filter(File.agent_id == agent_id).all()
    return [
        FileResponse(
            id=f.id,
            name=f.name,
            size=f.size,
            uploadedAt=f.uploaded_at.isoformat()
        )
        for f in files
    ]

@router.post("/agents/{agent_id}/files", response_model=FileResponse)
async def upload_file_to_agent(
    agent_id: str, 
    file: UploadFile = FastAPIFile(...), 
    db: Session = Depends(get_db)
):
    """Upload a file to a specific agent for RAG ingestion"""
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        # Generate unique ID and filepath
        file_id = str(uuid.uuid4())
        filepath = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
        
        # Save file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        # Store in database
        new_file = File(
            id=file_id,
            name=file.filename,
            filepath=filepath,
            size=file_size,
            agent_id=agent_id
        )
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        
        # Trigger RAG ingestion into agent-specific collection
        try:
            vsm = VectorStoreManager(agent_id=agent_id)
            vsm.ingest_file(filepath)
            print(f"✓ File {file.filename} ingested into agent {agent.name}'s vector store")
        except Exception as e:
            print(f"⚠️  Warning: Failed to ingest file into vector store: {e}")
            # Don't fail the upload if ingestion fails
        
        return FileResponse(
            id=new_file.id,
            name=new_file.name,
            size=new_file.size,
            uploadedAt=new_file.uploaded_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}/files/{file_id}")
async def delete_agent_file(agent_id: str, file_id: str, db: Session = Depends(get_db)):
    """Delete a file from a specific agent"""
    file = db.query(File).filter(
        File.id == file_id,
        File.agent_id == agent_id
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete physical file
    if os.path.exists(file.filepath):
        os.remove(file.filepath)
    
    # Delete from database
    db.delete(file)
    db.commit()
    
    # Note: Vector embeddings remain in ChromaDB collection
    # Could add cleanup logic here if needed
    
    return {"message": "File deleted successfully"}
