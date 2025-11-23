from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Схемы для ответов API ---
# orm_mode = True позволяет автоматически преобразовывать
# объекты SQLAlchemy в Pydantic схемы, если имена полей совпадают.

class TeamMember(BaseModel):
    user_id: str
    username: str
    is_active: bool

    class Config:
        orm_mode = True

class Team(BaseModel):
    team_name: str
    members: List[TeamMember]

    class Config:
        orm_mode = True

class User(BaseModel):
    user_id: str
    username: str
    team_name: Optional[str] = None # team_name может быть null
    is_active: bool

    class Config:
        orm_mode = True

class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str

    class Config:
        orm_mode = True

class PullRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str
    assigned_reviewers: List[str] = Field(default_factory=list)
    createdAt: Optional[datetime] = Field(None, alias='created_at')
    mergedAt: Optional[datetime] = Field(None, alias='merged_at')

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


# --- Схемы для тел запросов (Request Bodies) ---

class TeamAddRequest(BaseModel):
    team_name: str
    members: List[TeamMember]

class SetUserActiveRequest(BaseModel):
    user_id: str
    is_active: bool

class PullRequestCreateRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str

class PullRequestMergeRequest(BaseModel):
    pull_request_id: str

class PullRequestReassignRequest(BaseModel):
    pull_request_id: str
    old_user_id: str

class DeactivateTeamMembersRequest(BaseModel):
    team_name: str
    user_ids: List[str]


# --- Схемы для "оберток" ответов ---

class TeamResponse(BaseModel):
    team: Team

class UserResponse(BaseModel):
    user: User

class PullRequestResponse(BaseModel):
    pr: PullRequest

class ReassignResponse(BaseModel):
    pr: PullRequest
    replaced_by: str

class UserReviewResponse(BaseModel):
    user_id: str
    pull_requests: List[PullRequestShort]

class DeactivationResponse(BaseModel):
    deactivated_users: List[str]
    reassigned_prs: List[str]
