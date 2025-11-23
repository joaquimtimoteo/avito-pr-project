from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- Schemas para respostas API ---
# from_attributes=True permite converter automaticamente
# objetos SQLAlchemy em schemas Pydantic, se os nomes dos campos coincidirem.

class TeamMember(BaseModel):
    user_id: str
    username: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class Team(BaseModel):
    team_name: str
    members: List[TeamMember]

    model_config = ConfigDict(from_attributes=True)

class User(BaseModel):
    user_id: str
    username: str
    team_name: Optional[str] = None  # team_name pode ser null
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str

    model_config = ConfigDict(from_attributes=True)

class PullRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str
    assigned_reviewers: List[str] = Field(default_factory=list)
    createdAt: Optional[datetime] = Field(None, alias='created_at')
    mergedAt: Optional[datetime] = Field(None, alias='merged_at')

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True  # Substitui allow_population_by_field_name
    )


# --- Schemas para Request Bodies ---

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


# --- Schemas para "wrappers" de respostas ---

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
