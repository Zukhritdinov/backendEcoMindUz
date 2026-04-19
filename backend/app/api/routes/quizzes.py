from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.api.deps import SessionDep, CurrentUser, get_current_admin
from app.models import Topic, Question, Choice, QuizResult, User, QuestionTypeEnum
from app.schemas.quiz import (
    QuestionCreate, QuestionUpdate, QuestionResponse, 
    ChoiceCreate, ChoiceUpdate, ChoiceResponse, 
    QuizSubmit, QuizResultResponse
)

router = APIRouter()

# --- Admin Endpoints ---

@router.post("/topics/{topic_id}/questions", response_model=QuestionResponse)
def create_question(
    topic_id: UUID,
    question_in: QuestionCreate,
    db: SessionDep,
    current_admin: User = Depends(get_current_admin)
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    question = Question(
        topic_id=topic_id,
        type=question_in.type,
        question_text=question_in.question_text
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question

@router.post("/topics/{topic_id}/questions/{question_id}/choices", response_model=ChoiceResponse)
def add_choice(
    topic_id: UUID,
    question_id: UUID,
    choice_in: ChoiceCreate,
    db: SessionDep,
    current_admin: User = Depends(get_current_admin)
):
    question = db.query(Question).filter(Question.id == question_id, Question.topic_id == topic_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    choice = Choice(
        question_id=question_id,
        choice_text=choice_in.choice_text,
        is_correct=choice_in.is_correct
    )
    db.add(choice)
    db.commit()
    db.refresh(choice)
    return choice
@router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: UUID,
    question_in: QuestionUpdate,
    db: SessionDep,
    current_admin: User = Depends(get_current_admin)
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    update_data = question_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)
        
    db.commit()
    db.refresh(question)
    return question

@router.delete("/questions/{question_id}")
def delete_question(
    question_id: UUID,
    db: SessionDep,
    current_admin: User = Depends(get_current_admin)
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully"}

@router.put("/choices/{choice_id}", response_model=ChoiceResponse)
def update_choice(
    choice_id: UUID,
    choice_in: ChoiceUpdate,
    db: SessionDep,
    current_admin: User = Depends(get_current_admin)
):
    choice = db.query(Choice).filter(Choice.id == choice_id).first()
    if not choice:
        raise HTTPException(status_code=404, detail="Choice not found")
        
    update_data = choice_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(choice, field, value)
        
    db.commit()
    db.refresh(choice)
    return choice

@router.delete("/choices/{choice_id}")
def delete_choice(
    choice_id: UUID,
    db: SessionDep,
    current_admin: User = Depends(get_current_admin)
):
    choice = db.query(Choice).filter(Choice.id == choice_id).first()
    if not choice:
        raise HTTPException(status_code=404, detail="Choice not found")
        
    db.delete(choice)
    db.commit()
    return {"message": "Choice deleted successfully"}

# --- User Endpoints ---

@router.get("/topics/{topic_id}/questions", response_model=List[QuestionResponse])
def get_topic_questions(
    topic_id: UUID,
    db: SessionDep,
    current_user: CurrentUser
):
    """
    Returns the questions + choices for a specific topic.
    If the user is not admin and topic isn't published, returns 403.
    """
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    if not topic.is_published and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Topic is not published yet")
        
    return topic.questions

@router.put("/topics/{topic_id}/submit", response_model=QuizResultResponse)
def submit_quiz(
    topic_id: UUID,
    submission: QuizSubmit,
    db: SessionDep,
    current_user: CurrentUser
):
    """
    Evaluates quiz submissions, securely scoring choice questions on the backend.
    Awards user points safely, only granting the difference if beating a previous high score.
    Text-based answers are saved for manual review later but currently skipped in MVP auto-scoring.
    """
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    questions = topic.questions
    if not questions:
        raise HTTPException(status_code=400, detail="This topic has no quiz questions setup")

    correct_answers_count = 0
    total_choice_questions = 0
    POINTS_PER_CORRECT_ANSWER = 10

    # 1. Evaluate user's answers against the database securely
    for question in questions:
        if question.type == QuestionTypeEnum.choice:
            total_choice_questions += 1
            user_selected_choice_id = submission.answers.get(str(question.id))
            
            if user_selected_choice_id:
                # Iterate internal choices to find the match and verify correctness natively
                for choice in question.choices:
                    if str(choice.id) == user_selected_choice_id and choice.is_correct:
                        correct_answers_count += 1
                        break
        # Text-style answers are inherently tracked inside `submission.answers` 
        # but logically bypassed for the automated `correct_answers_count` metric in MVP.

    # 2. Calculate percentages and base points safely
    if total_choice_questions == 0:
        # Failsafe: Quiz only contains text questions
        percentage = 100.0
        points_earned = 0
    else:
        percentage = round((correct_answers_count / total_choice_questions) * 100.0, 2)
        points_earned = correct_answers_count * POINTS_PER_CORRECT_ANSWER

    # 3. Check for existing prior attempts for this exact user and topic
    existing_result = db.query(QuizResult).filter(
        QuizResult.user_id == current_user.id,
        QuizResult.topic_id == topic_id
    ).first()

    if existing_result:
        # The user has taken this quiz before. Only award points if they beat their high score!
        if correct_answers_count > existing_result.score:
            
            # Safely calculate the point difference (delta) to avoid double-awarding past points
            points_delta = (correct_answers_count - existing_result.score) * POINTS_PER_CORRECT_ANSWER
            current_user.points += points_delta
            
            # Overwrite the tracking result record
            existing_result.score = correct_answers_count
            existing_result.percentage = percentage
            existing_result.answers = submission.answers
            
            db.commit()
            db.refresh(existing_result)
            db.refresh(current_user) # Keep user object rigorously in sync
            return existing_result
        else:
            # The user didn't beat their high score. Gracefully return the existing best result.
            return existing_result
            
    else:
        # First-time completion. Award the full points earned.
        current_user.points += points_earned
        
        new_result = QuizResult(
            user_id=current_user.id,
            topic_id=topic_id,
            score=correct_answers_count,
            percentage=percentage,
            answers=submission.answers
        )
        db.add(new_result)
        db.commit()
        db.refresh(new_result)
        db.refresh(current_user) # Keep user object rigorously in sync
        return new_result

@router.get("/me/results", response_model=List[QuizResultResponse])
def get_my_results(db: SessionDep, current_user: CurrentUser):
    results = db.query(QuizResult).filter(QuizResult.user_id == current_user.id).all()
    return results
