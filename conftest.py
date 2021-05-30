import pytest
from app import create_app
from database import db

@pytest.fixture
def app():
    test_app=create_app()
    with test_app.app_context():
        db.create_all()
    yield test_app

@pytest.fixture
def client(app):
    ctx = app.app_context()
    ctx.push()
    return app.test_client()
    ctx.pop()