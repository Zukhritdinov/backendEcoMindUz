import json
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
from uuid import UUID

from app.api.deps import SessionDep, CurrentUser, get_current_admin
from app.models import Topic, ContentBlock, ContentTypeEnum, User
from app.schemas.topic import (
    TopicCreate, TopicUpdate, TopicResponse, 
    ContentBlockUpdate, ContentBlockResponse, BlockReorderRequest
)
from app.utils.upload import save_upload_file

router = APIRouter()

# --- Topic Endpoints ---

@router.get("/", response_model=List[TopicResponse])
def get_published_topics(db: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100):
    topics = db.query(Topic).filter(Topic.is_published == True).offset(skip).limit(limit).all()
    return topics

@router.get("/admin/", response_model=List[TopicResponse])
def get_all_topics_admin(db: SessionDep, current_admin: User = Depends(get_current_admin), skip: int = 0, limit: int = 100):
    topics = db.query(Topic).offset(skip).limit(limit).all()
    return topics

@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: UUID, db: SessionDep, current_user: CurrentUser):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    if not topic.is_published and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Topic is not published yet")
    return topic

@router.post("/", response_model=TopicResponse)
def create_topic(topic_in: TopicCreate, db: SessionDep, current_admin: User = Depends(get_current_admin)):
    topic = Topic(
        title=topic_in.title,
        short_description=topic_in.short_description,
        category=topic_in.category,
        author_id=current_admin.id
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic

@router.put("/{topic_id}", response_model=TopicResponse)
def update_topic(topic_id: UUID, topic_in: TopicUpdate, db: SessionDep, current_admin: User = Depends(get_current_admin)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    update_data = topic_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(topic, field, value)
    
    db.commit()
    db.refresh(topic)
    return topic

@router.delete("/{topic_id}")
def delete_topic(topic_id: UUID, db: SessionDep, current_admin: User = Depends(get_current_admin)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(topic)
    db.commit()
    return {"message": "Topic deleted successfully"}


# --- ContentBlock Endpoints ---

@router.post("/{topic_id}/blocks", response_model=ContentBlockResponse)
def add_content_block(
    topic_id: UUID,
    db: SessionDep,
    type: ContentTypeEnum = Form(...),
    order_index: int = Form(...),
    content_data_json: Optional[str] = Form(None), # Used for text/youtube
    file: Optional[UploadFile] = File(None),       # Used for image/video
    current_admin: User = Depends(get_current_admin)
):
    """
    Creates a new ContentBlock. Safely handles Form payload data mapping.
    """
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    content_dict = {}
    
    if type in [ContentTypeEnum.image, ContentTypeEnum.video]:
        if not file:
            raise HTTPException(status_code=400, detail="File is required for image or video block type")
        # Returns exactly {"url": "/uploads/xxx.ext", "filename": "..."}
        content_dict = save_upload_file(file)
        
    elif type == ContentTypeEnum.youtube:
        if not content_data_json:
            raise HTTPException(status_code=400, detail="content_data_json is required for YouTube block type. Ex: {'url':'...'}")
        try:
            content_dict = json.loads(content_data_json)
            if "url" not in content_dict:
                raise HTTPException(status_code=400, detail="YouTube block must contain 'url' in JSON string")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format in content_data_json")
            
    else:  # Text type -> e.g. {"html": "..."} or {"content": ...}
        if not content_data_json:
            raise HTTPException(status_code=400, detail="content_data_json is required for text block type")
        try:
            content_dict = json.loads(content_data_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format in content_data_json")

    block = ContentBlock(
        topic_id=topic_id,
        type=type,
        order_index=order_index,
        content_data=content_dict
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block

@router.put("/{topic_id}/blocks/reorder", status_code=status.HTTP_200_OK)
def reorder_content_blocks(
    topic_id: UUID,
    reorder_req: BlockReorderRequest,
    db: SessionDep,
    current_admin: User = Depends(get_current_admin)
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    for item in reorder_req.blocks:
        block = db.query(ContentBlock).filter(ContentBlock.id == item.id, ContentBlock.topic_id == topic_id).first()
        if block:
            block.order_index = item.order_index
            
    db.commit()
    return {"message": "Blocks reordered successfully"}

@router.put("/{topic_id}/blocks/{block_id}", response_model=ContentBlockResponse)
def update_content_block(
    topic_id: UUID,
    block_id: UUID,
    block_in: ContentBlockUpdate,
    db: SessionDep,
    current_admin: User = Depends(get_current_admin)
):
    block = db.query(ContentBlock).filter(ContentBlock.id == block_id, ContentBlock.topic_id == topic_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Content block not found")
    
    if block_in.order_index is not None:
        block.order_index = block_in.order_index
    if block_in.content_data is not None:
        block.content_data = block_in.content_data
    
    db.commit()
    db.refresh(block)
    return block

@router.delete("/{topic_id}/blocks/{block_id}")
def delete_content_block(
    topic_id: UUID,
    block_id: UUID,
    db: SessionDep,
    current_admin: User = Depends(get_current_admin)
):
    block = db.query(ContentBlock).filter(ContentBlock.id == block_id, ContentBlock.topic_id == topic_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Content block not found")
    db.delete(block)
    db.commit()
    return {"message": "Content block deleted successfully"}
