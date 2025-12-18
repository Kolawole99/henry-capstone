from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import uuid
import os
import shutil

from ..database import get_db, File
from ...utils.vector_store import VectorStoreManager

router = APIRouter()

# Upload directory
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize vector store manager (singleton)
vector_store_manager = None

def get_vector_store_manager():
    global vector_store_manager
    if vector_store_manager is None:
        vector_store_manager = VectorStoreManager()
    return vector_store_manager

# Response models
class FileResponse(BaseModel):
    id: str
    name: str
    size: int
    uploadedAt: str

    class Config:
        from_attributes = True

@router.get("/files", response_model=List[FileResponse])
async def list_files(db: Session = Depends(get_db)):
    """Get all uploaded files"""
    files = db.query(File).all()
    return [
        FileResponse(
            id=f.id,
            name=f.name,
            size=f.size,
            uploadedAt=f.uploaded_at.isoformat()
        )
        for f in files
    ]

@router.post("/files", response_model=FileResponse)
async def upload_file(file: UploadFile = FastAPIFile(...), db: Session = Depends(get_db)):
    """Upload a file for RAG ingestion"""
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
            size=file_size
        )
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        
        # Trigger RAG ingestion
        try:
            vsm = get_vector_store_manager()
            vsm.ingest_file(filepath)
            print(f"✓ File {file.filename} ingested into vector store")
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

@router.delete("/files/{file_id}")
async def delete_file(file_id: str, db: Session = Depends(get_db)):
    """Delete a file"""
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete physical file
    if os.path.exists(file.filepath):
        os.remove(file.filepath)
    
    # Delete from database
    db.delete(file)
    db.commit()
    return {"message": "File deleted successfully"}
