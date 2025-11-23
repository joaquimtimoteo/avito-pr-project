import os
from sqlalchemy import create_engine, Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# IMPORTANTE: Use DATABASE_PUBLIC_URL primeiro, depois fallback para a URL pública hardcoded
DATABASE_URL = (
    os.getenv('DATABASE_PUBLIC_URL') or 
    os.getenv('DATABASE_URL') or
    # Fallback: URL pública do Railway (acessível de qualquer lugar)
    "postgresql://postgres:xdBUjvmTDIoCKHVmVwcnVpauUfNVxVbE@nozomi.proxy.rlwy.net:51678/railway"
)

# DEBUG: Ver qual host está sendo usado
print(f"🔍 Conectando ao: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'ERRO'}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- ORM Modelos ---

class Team(Base):
    __tablename__ = "teams"
    team_name = Column(String, primary_key=True, index=True)
    members = relationship("User", back_populates="team")

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    team_name = Column(String, ForeignKey("teams.team_name"))
    team = relationship("Team", back_populates="members")

class PullRequest(Base):
    __tablename__ = "pull_requests"
    pull_request_id = Column(String, primary_key=True, index=True)
    pull_request_name = Column(String, nullable=False)
    author_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    status = Column(String, default="OPEN", nullable=False)
    reviewers = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    merged_at = Column(DateTime, nullable=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
