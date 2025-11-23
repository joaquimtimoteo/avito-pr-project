import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from ..src.main import app
from ..src.database import Base, get_db

# Используем отдельную БД для тестов
TEST_DATABASE_URL = os.getenv("DATABASE_URL") + "_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Переопределяем зависимость get_db на тестовую
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Создаем таблицы перед запуском тестов
    Base.metadata.create_all(bind=engine)
    yield
    # Удаляем таблицы после завершения тестов
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    # Очищаем таблицы перед каждым тестом
    for table in reversed(Base.metadata.sorted_tables):
        engine.execute(table.delete())
    return TestClient(app)
