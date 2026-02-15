"""
Test suite for users API router
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from main import app
from database.models import Base, User as DBUser, UserMetrics as DBUserMetrics
from database.connection import get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database before each test"""
    db = TestingSessionLocal()
    db.query(DBUserMetrics).delete()
    db.query(DBUser).delete()
    db.commit()
    db.close()
    yield


def test_register_user_success():
    """Test successful user registration"""
    response = client.post(
        "/api/users/register",
        json={
            "email": "test@example.com",
            "password": "Test1234",
            "business_type": "Manufacturing",
            "company_size": "Small",
            "company_name": "Test Company",
            "monthly_volume": 10000.0
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "test@example.com"
    assert data["business_type"] == "Manufacturing"
    assert data["token_type"] == "bearer"


def test_register_user_duplicate_email():
    """Test registration with duplicate email"""
    # Register first user
    client.post(
        "/api/users/register",
        json={
            "email": "test@example.com",
            "password": "Test1234",
            "business_type": "Manufacturing",
            "company_size": "Small",
            "company_name": "Test Company"
        }
    )
    
    # Try to register with same email
    response = client.post(
        "/api/users/register",
        json={
            "email": "test@example.com",
            "password": "Test5678",
            "business_type": "SaaS",
            "company_size": "Micro",
            "company_name": "Another Company"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_user_invalid_email():
    """Test registration with invalid email"""
    response = client.post(
        "/api/users/register",
        json={
            "email": "invalid-email",
            "password": "Test1234",
            "business_type": "Manufacturing",
            "company_size": "Small",
            "company_name": "Test Company"
        }
    )
    
    assert response.status_code == 422


def test_register_user_weak_password():
    """Test registration with weak password"""
    response = client.post(
        "/api/users/register",
        json={
            "email": "test@example.com",
            "password": "weak",
            "business_type": "Manufacturing",
            "company_size": "Small",
            "company_name": "Test Company"
        }
    )
    
    assert response.status_code == 422


def test_login_success():
    """Test successful login"""
    # Register user first
    client.post(
        "/api/users/register",
        json={
            "email": "test@example.com",
            "password": "Test1234",
            "business_type": "Manufacturing",
            "company_size": "Small",
            "company_name": "Test Company"
        }
    )
    
    # Login
    response = client.post(
        "/api/users/login",
        json={
            "email": "test@example.com",
            "password": "Test1234"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "test@example.com"
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    """Test login with wrong password"""
    # Register user first
    client.post(
        "/api/users/register",
        json={
            "email": "test@example.com",
            "password": "Test1234",
            "business_type": "Manufacturing",
            "company_size": "Small",
            "company_name": "Test Company"
        }
    )
    
    # Login with wrong password
    response = client.post(
        "/api/users/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword123"
        }
    )
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_user():
    """Test login with nonexistent user"""
    response = client.post(
        "/api/users/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Test1234"
        }
    )
    
    assert response.status_code == 401


def test_get_profile_success():
    """Test getting user profile"""
    # Register user
    register_response = client.post(
        "/api/users/register",
        json={
            "email": "test@example.com",
            "password": "Test1234",
            "business_type": "Manufacturing",
            "company_size": "Small",
            "company_name": "Test Company",
            "monthly_volume": 10000.0
        }
    )
    
    token = register_response.json()["access_token"]
    
    # Get profile
    response = client.get(
        "/api/users/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["business_type"] == "Manufacturing"
    assert data["company_size"] == "Small"
    assert data["company_name"] == "Test Company"
    assert data["monthly_volume"] == 10000.0


def test_get_profile_unauthorized():
    """Test getting profile without authentication"""
    response = client.get("/api/users/profile")
    
    assert response.status_code == 403


def test_get_profile_invalid_token():
    """Test getting profile with invalid token"""
    response = client.get(
        "/api/users/profile",
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    assert response.status_code == 401


def test_update_profile_success():
    """Test updating user profile"""
    # Register user
    register_response = client.post(
        "/api/users/register",
        json={
            "email": "test@example.com",
            "password": "Test1234",
            "business_type": "Manufacturing",
            "company_size": "Small",
            "company_name": "Test Company"
        }
    )
    
    token = register_response.json()["access_token"]
    
    # Update profile
    response = client.put(
        "/api/users/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "company_name": "Updated Company",
            "monthly_volume": 20000.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Updated Company"
    assert data["monthly_volume"] == 20000.0


def test_update_profile_partial():
    """Test partial profile update"""
    # Register user
    register_response = client.post(
        "/api/users/register",
        json={
            "email": "test@example.com",
            "password": "Test1234",
            "business_type": "Manufacturing",
            "company_size": "Small",
            "company_name": "Test Company",
            "monthly_volume": 10000.0
        }
    )
    
    token = register_response.json()["access_token"]
    
    # Update only company name
    response = client.put(
        "/api/users/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "company_name": "New Company Name"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "New Company Name"
    assert data["monthly_volume"] == 10000.0  # Should remain unchanged


def test_update_profile_unauthorized():
    """Test updating profile without authentication"""
    response = client.put(
        "/api/users/profile",
        json={
            "company_name": "Updated Company"
        }
    )
    
    assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
