from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import uuid
import os
import shutil

from ..database import get_db, File, Agent
from ...utils.vector_store import VectorStoreManager
from ...utils.logger import get_logger, log_error
from ...utils.validators import (
    validate_uuid,
    validate_file,
    sanitize_filename,
    ValidationError as ValidatorError
)

router = APIRouter()
logger = get_logger(__name__)

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
    try:
        agent_id = validate_uuid(agent_id, "Agent ID")
    except ValidatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        logger.warning(f"Agent not found when listing files", extra={
            'extra_fields': {'agent_id': agent_id}
        })
        raise HTTPException(status_code=404, detail="Agent not found")
    
    files = db.query(File).filter(File.agent_id == agent_id).all()
    
    logger.info(f"Listed files for agent", extra={
        'extra_fields': {
            'agent_id': agent_id,
            'agent_name': agent.name,
            'file_count': len(files)
        }
    })
    
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
    # Validate agent_id format
    try:
        agent_id = validate_uuid(agent_id, "Agent ID")
    except ValidatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        logger.warning(f"Agent not found when uploading file", extra={
            'extra_fields': {'agent_id': agent_id}
        })
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Validate file before processing
    try:
        # Read file to get size
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file
        safe_filename, validated_size = validate_file(file.filename, file_size)
        
        # Reset file pointer
        await file.seek(0)
    except ValidatorError as e:
        logger.warning(f"File validation failed", extra={
            'extra_fields': {
                'agent_id': agent_id,
                'filename': file.filename,
                'error': str(e)
            }
        })
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        # Generate unique ID and filepath
        file_id = str(uuid.uuid4())
        filepath = os.path.join(UPLOAD_DIR, f"{file_id}_{safe_filename}")
        
        logger.info(f"Uploading file", extra={
            'extra_fields': {
                'agent_id': agent_id,
                'agent_name': agent.name,
                'filename': safe_filename,
                'file_id': file_id,
                'file_size': file_size
            }
        })
        
        # Save file
        with open(filepath, "wb") as buffer:
            buffer.write(file_content)
        
        # Store in database
        new_file = File(
            id=file_id,
            name=safe_filename,
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
            chunks_count = vsm.ingest_file(filepath, file_id=file_id)
            logger.info(f"File ingested into vector store", extra={
                'extra_fields': {
                    'agent_id': agent_id,
                    'file_id': file_id,
                    'filename': safe_filename,
                    'chunks_count': chunks_count
                }
            })
        except Exception as e:
            logger.warning(f"Failed to ingest file into vector store", extra={
                'extra_fields': {
                    'agent_id': agent_id,
                    'filename': file.filename,
                    'error': str(e)
                }
            })
            # Don't fail the upload if ingestion fails
        
        return FileResponse(
            id=new_file.id,
            name=new_file.name,
            size=new_file.size,
            uploadedAt=new_file.uploaded_at.isoformat()
        )
    except Exception as e:
        log_error(
            error=e,
            context="upload_file_to_agent",
            agent_id=agent_id,
            filename=file.filename
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}/files/{file_id}")
async def delete_agent_file(agent_id: str, file_id: str, db: Session = Depends(get_db)):
    """Delete a file from a specific agent"""
    # Validate UUIDs
    try:
        agent_id = validate_uuid(agent_id, "Agent ID")
        file_id = validate_uuid(file_id, "File ID")
    except ValidatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    file = db.query(File).filter(
        File.id == file_id,
        File.agent_id == agent_id
    ).first()
    
    if not file:
        logger.warning(f"File not found for deletion", extra={
            'extra_fields': {
                'agent_id': agent_id,
                'file_id': file_id
            }
        })
        raise HTTPException(status_code=404, detail="File not found")
    
    filename = file.name
    filepath = file.filepath
    
    # Delete physical file
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Delete from database
    db.delete(file)
    db.commit()
    
    # Delete embeddings from ChromaDB
    try:
        vsm = VectorStoreManager(agent_id=agent_id)
        deleted_chunks = vsm.delete_file(file_id)
        logger.info(f"Deleted file and embeddings", extra={
            'extra_fields': {
                'agent_id': agent_id,
                'file_id': file_id,
                'filename': filename,
                'chunks_deleted': deleted_chunks
            }
        })
    except Exception as e:
        logger.warning(f"Failed to delete embeddings from vector store", extra={
            'extra_fields': {
                'agent_id': agent_id,
                'file_id': file_id,
                'error': str(e)
            }
        })
        # Don't fail the deletion if vector store cleanup fails
    
    return {"message": "File deleted successfully"}

