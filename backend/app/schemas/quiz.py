from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models import QuestionTypeEnum

class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool

class ChoiceCreate(ChoiceBase):
    pass

class ChoiceUpdate(BaseModel):
    choice_text: Optional[str] = None
    is_correct: Optional[bool] = None

class ChoiceResponse(ChoiceBase):
    id: UUID
    question_id: UUID
    
    model_config = ConfigDict(from_attributes=True)

class QuestionBase(BaseModel):
    type: QuestionTypeEnum
    question_text: str

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(BaseModel):
    type: Optional[QuestionTypeEnum] = None
    question_text: Optional[str] = None

class QuestionResponse(QuestionBase):
    id: UUID
    topic_id: UUID
    choices: List[ChoiceResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class QuizSubmit(BaseModel):
    # Mapping of question UUID string to selected choice UUID string (or text answer string)
    answers: Dict[str, str]

class QuizResultResponse(BaseModel):
    id: UUID
    user_id: UUID
    topic_id: UUID
    score: int
    percentage: float
    answers: Optional[Dict[str, Any]] = None
    completed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
