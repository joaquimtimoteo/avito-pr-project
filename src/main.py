from fastapi import FastAPI, Depends, HTTPException, Request, status, Body
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List
import random
from datetime import datetime

from . import crud, schemas, database

# Создаем таблицы в БД при старте
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="PR Reviewer Assignment Service",
    version="1.0.0",
)

# --- Кастомный обработчик ошибок ---
class DomainException(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail={"error": {"code": code, "message": message}})

@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)

# --- Вспомогательная функция для форматирования PR ---
def format_pr_response(db_pr: database.PullRequest) -> schemas.PullRequest:
    return schemas.PullRequest(
        pull_request_id=db_pr.pull_request_id,
        pull_request_name=db_pr.pull_request_name,
        author_id=db_pr.author_id,
        status=db_pr.status,
        assigned_reviewers=db_pr.reviewers.split(',') if db_pr.reviewers else [],
        createdAt=db_pr.created_at,
        mergedAt=db_pr.merged_at
    )

# --- Эндпоинты ---

@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/docs")

@app.post("/team/add", response_model=schemas.TeamResponse, status_code=status.HTTP_201_CREATED, tags=["Teams"])
def add_team(
    team_data: schemas.TeamAddRequest = Body(..., example={"team_name": "backend-squad", "members": [{"user_id": "u1", "username": "Alice", "is_active": True}]}), 
    db: Session = Depends(database.get_db)
):
    if crud.get_team_by_name(db, team_data.team_name):
        raise DomainException(status.HTTP_400_BAD_REQUEST, "TEAM_EXISTS", "team_name already exists")
    db_team = crud.create_team_with_members(db, team_data)
    return schemas.TeamResponse(team=schemas.Team.from_orm(db_team))

# 🆕 NOVO ENDPOINT: Adicionar membros a uma equipe existente
@app.post("/team/addMembers", response_model=schemas.TeamResponse, status_code=status.HTTP_201_CREATED, tags=["Teams"])
def add_team_members(
    team_name: str = Body(..., embed=True),
    members: List[schemas.TeamMember] = Body(..., embed=True, example=[{"user_id": "u3", "username": "Bob", "is_active": True}]),
    db: Session = Depends(database.get_db)
):
    """
    Adiciona novos membros a uma equipe existente.
    
    Exemplo:
    {
      "team_name": "backend-squad",
      "members": [
        {"user_id": "u3", "username": "Bob", "is_active": true},
        {"user_id": "u4", "username": "Charlie", "is_active": true}
      ]
    }
    """
    # Verifica se a equipe existe
    db_team = crud.get_team_by_name(db, team_name)
    if not db_team:
        raise DomainException(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "team not found")
    
    # Adiciona os novos membros
    for member in members:
        # Verifica se o usuário já existe
        existing_user = crud.get_user_by_id(db, member.user_id)
        
        if existing_user:
            # Se o usuário já existe, atualiza para esta equipe
            existing_user.username = member.username
            existing_user.team_name = team_name
            existing_user.is_active = member.is_active
        else:
            # Cria novo usuário
            db_user = database.User(
                user_id=member.user_id,
                username=member.username,
                team_name=team_name,
                is_active=member.is_active
            )
            db.add(db_user)
    
    db.commit()
    db.refresh(db_team)
    
    return schemas.TeamResponse(team=schemas.Team.from_orm(db_team))

@app.get("/team/get", response_model=schemas.Team, tags=["Teams"])
def get_team(team_name: str, db: Session = Depends(database.get_db)):
    db_team = crud.get_team_by_name(db, team_name)
    if not db_team:
        raise DomainException(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "team not found")
    return schemas.Team.from_orm(db_team)

@app.post("/team/deactivateMembers", response_model=schemas.DeactivationResponse, tags=["Teams"])
def deactivate_team_members(
    request: schemas.DeactivateTeamMembersRequest = Body(..., example={"team_name": "backend-squad", "user_ids": ["u1"]}), 
    db: Session = Depends(database.get_db)
):
    team = crud.get_team_by_name(db, request.team_name)
    if not team:
        raise DomainException(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "team not found")
    reassigned_prs = crud.deactivate_and_reassign(db, team, request.user_ids)
    return schemas.DeactivationResponse(deactivated_users=request.user_ids, reassigned_prs=reassigned_prs)

@app.post("/users/setIsActive", response_model=schemas.UserResponse, tags=["Users"])
def set_user_is_active(
    request: schemas.SetUserActiveRequest = Body(..., example={"user_id": "u1", "is_active": False}), 
    db: Session = Depends(database.get_db)
):
    user = crud.set_user_active(db, request.user_id, request.is_active)
    if not user:
        raise DomainException(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "user not found")
    return schemas.UserResponse(user=schemas.User.from_orm(user))

@app.get("/users/getReview", response_model=schemas.UserReviewResponse, tags=["Users"])
def get_user_reviews(user_id: str, db: Session = Depends(database.get_db)):
    if not crud.get_user_by_id(db, user_id):
        raise DomainException(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "user not found")
    prs = crud.get_reviews_for_user(db, user_id)
    return schemas.UserReviewResponse(user_id=user_id, pull_requests=[schemas.PullRequestShort.from_orm(pr) for pr in prs])

@app.post("/pullRequest/create", response_model=schemas.PullRequestResponse, status_code=status.HTTP_201_CREATED, tags=["PullRequests"])
def create_pull_request(
    pr_data: schemas.PullRequestCreateRequest = Body(..., example={"pull_request_id": "pr-1001", "pull_request_name": "New feature", "author_id": "u1"}), 
    db: Session = Depends(database.get_db)
):
    if crud.get_pr_by_id(db, pr_data.pull_request_id):
        raise DomainException(status.HTTP_409_CONFLICT, "PR_EXISTS", "PR id already exists")
    author = crud.get_user_by_id(db, pr_data.author_id)
    if not author or not author.team:
        raise DomainException(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "author or author's team not found")
    candidates = [m for m in author.team.members if m.is_active and m.user_id != author.user_id]
    random.shuffle(candidates)
    reviewer_ids = [r.user_id for r in candidates[:2]]
    db_pr = crud.create_pr(db, pr_data, reviewer_ids)
    return schemas.PullRequestResponse(pr=format_pr_response(db_pr))

@app.post("/pullRequest/merge", response_model=schemas.PullRequestResponse, tags=["PullRequests"])
def merge_pull_request(
    request: schemas.PullRequestMergeRequest = Body(..., example={"pull_request_id": "pr-1001"}), 
    db: Session = Depends(database.get_db)
):
    db_pr = crud.get_pr_by_id(db, request.pull_request_id)
    if not db_pr:
        raise DomainException(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "PR not found")
    if db_pr.status != "MERGED":
        db_pr.status = "MERGED"
        db_pr.merged_at = datetime.utcnow()
        db.commit()
        db.refresh(db_pr)
    return schemas.PullRequestResponse(pr=format_pr_response(db_pr))

@app.post("/pullRequest/reassign", response_model=schemas.ReassignResponse, tags=["PullRequests"])
def reassign_reviewer(
    request: schemas.PullRequestReassignRequest = Body(..., example={"pull_request_id": "pr-1001", "old_user_id": "u2"}), 
    db: Session = Depends(database.get_db)
):
    db_pr = crud.get_pr_by_id(db, request.pull_request_id)
    if not db_pr:
        raise DomainException(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "PR not found")
    if db_pr.status == "MERGED":
        raise DomainException(status.HTTP_409_CONFLICT, "PR_MERGED", "cannot reassign on merged PR")
    reviewers = db_pr.reviewers.split(',') if db_pr.reviewers else []
    if request.old_user_id not in reviewers:
        raise DomainException(status.HTTP_409_CONFLICT, "NOT_ASSIGNED", "reviewer is not assigned to this PR")
    old_reviewer = crud.get_user_by_id(db, request.old_user_id)
    if not old_reviewer or not old_reviewer.team:
        raise DomainException(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "old reviewer's team not found")
    candidates = [m for m in old_reviewer.team.members if m.is_active and m.user_id != db_pr.author_id and m.user_id not in reviewers]
    if not candidates:
        raise DomainException(status.HTTP_409_CONFLICT, "NO_CANDIDATE", "no active replacement candidate in team")
    new_reviewer = random.choice(candidates)
    reviewers.remove(request.old_user_id)
    reviewers.append(new_reviewer.user_id)
    db_pr.reviewers = ",".join(reviewers)
    db.commit()
    db.refresh(db_pr)
    return schemas.ReassignResponse(pr=format_pr_response(db_pr), replaced_by=new_reviewer.user_id)
