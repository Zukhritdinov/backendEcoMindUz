import os
from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models import ContentTypeEnum

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

class ContentBlockBase(BaseModel):
    type: ContentTypeEnum
    order_index: int
    content_data: Dict[str, Any]

class ContentBlockCreate(ContentBlockBase):
    pass

class ContentBlockUpdate(BaseModel):
    order_index: Optional[int] = None
    content_data: Optional[Dict[str, Any]] = None

class ContentBlockResponse(ContentBlockBase):
    id: UUID
    topic_id: UUID
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('content_data', mode='after')
    @classmethod
    def format_urls(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        # Convert local relative paths to full public URLs
        if v and "url" in v and isinstance(v["url"], str) and v["url"].startswith("/uploads/"):
            v["url"] = f"{BASE_URL}{v['url']}"
        return v

class TopicBase(BaseModel):
    title: str
    short_description: Optional[str] = None
    category: Optional[str] = None

class TopicCreate(TopicBase):
    pass

class TopicUpdate(BaseModel):
    title: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    is_published: Optional[bool] = None

class TopicResponse(TopicBase):
    id: UUID
    is_published: bool
    author_id: UUID
    created_at: datetime
    content_blocks: List[ContentBlockResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class BlockReorderItem(BaseModel):
    id: UUID
    order_index: int

class BlockReorderRequest(BaseModel):
    blocks: List[BlockReorderItem]
