from sqlalchemy.orm import Session
from . import database, schemas
import random

# --- Функции для работы с Team ---

def get_team_by_name(db: Session, team_name: str):
    return db.query(database.Team).filter(database.Team.team_name == team_name).first()

def create_team_with_members(db: Session, team_data: schemas.TeamAddRequest):
    db_team = database.Team(team_name=team_data.team_name)
    db.add(db_team)

    for member_data in team_data.members:
        user = db.query(database.User).filter(database.User.user_id == member_data.user_id).first()
        if user:
            user.username = member_data.username
            user.is_active = member_data.is_active
            user.team = db_team
        else:
            user = database.User(
                user_id=member_data.user_id,
                username=member_data.username,
                is_active=member_data.is_active,
                team=db_team,
            )
        db.add(user)
    
    db.commit()
    db.refresh(db_team)
    return db_team

# --- Функции для работы с User ---

def get_user_by_id(db: Session, user_id: str):
    return db.query(database.User).filter(database.User.user_id == user_id).first()

def set_user_active(db: Session, user_id: str, is_active: bool):
    user = get_user_by_id(db, user_id)
    if user:
        user.is_active = is_active
        db.commit()
        db.refresh(user)
    return user

# --- Функции для работы с PullRequest ---

def get_pr_by_id(db: Session, pr_id: str):
    return db.query(database.PullRequest).filter(database.PullRequest.pull_request_id == pr_id).first()

def create_pr(db: Session, pr_data: schemas.PullRequestCreateRequest, reviewer_ids: list[str]):
    db_pr = database.PullRequest(
        pull_request_id=pr_data.pull_request_id,
        pull_request_name=pr_data.pull_request_name,
        author_id=pr_data.author_id,
        reviewers=",".join(reviewer_ids)
    )
    db.add(db_pr)
    db.commit()
    db.refresh(db_pr)
    return db_pr

def get_reviews_for_user(db: Session, user_id: str):
    return db.query(database.PullRequest).filter(database.PullRequest.reviewers.contains(user_id)).all()

# --- Функция для массовой деактивации ---

def deactivate_and_reassign(db: Session, team: database.Team, user_ids: list[str]):
    reassigned_prs = set()
    
    open_prs_to_check = db.query(database.PullRequest).filter(database.PullRequest.status == 'OPEN').all()

    for user_id in user_ids:
        db.query(database.User).filter(database.User.user_id == user_id).update({"is_active": False})

        for pr in open_prs_to_check:
            reviewers = pr.reviewers.split(',') if pr.reviewers else []
            if user_id in reviewers:
                candidates = [
                    m.user_id for m in team.members 
                    if m.is_active and m.user_id not in user_ids and m.user_id != pr.author_id and m.user_id not in reviewers
                ]
                
                if candidates:
                    new_reviewer = random.choice(candidates)
                    reviewers.remove(user_id)
                    reviewers.append(new_reviewer)
                    pr.reviewers = ",".join(reviewers)
                    reassigned_prs.add(pr.pull_request_id)

    db.commit()
    return list(reassigned_prs)
