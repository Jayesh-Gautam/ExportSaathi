# Database Quick Start Guide

This guide will help you set up and use the ExportSathi database.

## Prerequisites

1. PostgreSQL 12+ installed and running
2. Python 3.10+ with dependencies installed
3. Environment variables configured in `.env`

## Step 1: Configure Database Connection

Edit your `.env` file:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/exportsathi
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

For AWS RDS:
```env
DATABASE_URL=postgresql://exportsathi_user:your_password@your-rds-endpoint.region.rds.amazonaws.com:5432/exportsathi
```

## Step 2: Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE exportsathi;

# Create user (optional)
CREATE USER exportsathi_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE exportsathi TO exportsathi_user;

# Exit
\q
```

## Step 3: Initialize Database Schema

### Option A: Using the initialization script

```bash
python backend/database/init_db.py
```

### Option B: Using Alembic migrations

```bash
# Apply all migrations
alembic upgrade head
```

### Option C: Using Python directly

```python
from backend.database import init_db, check_db_connection

# Check connection
if check_db_connection():
    print("✓ Database connected!")
    
# Create tables
init_db()
print("✓ Tables created!")
```

## Step 4: Verify Setup

```python
from backend.database import db_connection, User

# Test connection
with db_connection.session_scope() as session:
    # Create a test user
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        business_type="Manufacturing",
        company_size="Small",
        company_name="Test Company"
    )
    session.add(user)
    session.commit()
    
    print(f"✓ Created user: {user.email}")
    
    # Query user
    found_user = session.query(User).filter(User.email == "test@example.com").first()
    print(f"✓ Found user: {found_user.email}")
```

## Common Operations

### Create a User

```python
from backend.database import db_connection, User

with db_connection.session_scope() as session:
    user = User(
        email="user@example.com",
        password_hash="hashed_password",
        business_type="Manufacturing",
        company_size="Small",
        company_name="ABC Exports"
    )
    session.add(user)
```

### Create a Report

```python
from backend.database import db_connection, Report

with db_connection.session_scope() as session:
    report = Report(
        user_id=user_id,
        product_name="Turmeric Powder",
        destination_country="USA",
        business_type="Manufacturing",
        company_size="Small",
        hs_code="0910.30",
        hs_code_confidence=92.5,
        risk_score=35,
        report_data={
            "certifications": ["FDA"],
            "risks": ["contamination"],
            "timeline": 60
        }
    )
    session.add(report)
```

### Query Reports

```python
from backend.database import db_connection, Report

with db_connection.session_scope() as session:
    # Get all reports for a user
    reports = session.query(Report).filter(
        Report.user_id == user_id
    ).all()
    
    # Get reports by destination
    usa_reports = session.query(Report).filter(
        Report.destination_country == "USA"
    ).all()
    
    # Get recent reports
    recent = session.query(Report).order_by(
        Report.created_at.desc()
    ).limit(10).all()
```

### Track Certification Progress

```python
from backend.database import db_connection, CertificationProgress

with db_connection.session_scope() as session:
    progress = CertificationProgress(
        user_id=user_id,
        report_id=report_id,
        certification_id="fda-food",
        certification_name="FDA Food Facility Registration",
        certification_type="FDA",
        status="in_progress",
        documents_completed=["company_registration", "product_list"]
    )
    session.add(progress)
```

### Create Chat Session

```python
from backend.database import db_connection, ChatSession, ChatMessage

with db_connection.session_scope() as session:
    # Create session
    chat_session = ChatSession(
        user_id=user_id,
        report_id=report_id,
        context_data={"product": "Turmeric", "destination": "USA"}
    )
    session.add(chat_session)
    session.flush()  # Get the session ID
    
    # Add messages
    user_msg = ChatMessage(
        session_id=chat_session.id,
        role="user",
        content="What certifications do I need?"
    )
    session.add(user_msg)
    
    assistant_msg = ChatMessage(
        session_id=chat_session.id,
        role="assistant",
        content="For exporting turmeric to USA, you need FDA registration...",
        sources=[{"title": "FDA Guide", "url": "..."}]
    )
    session.add(assistant_msg)
```

## Using with FastAPI

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from backend.database import get_db, User, Report

app = FastAPI()

@app.get("/users/{user_id}/reports")
def get_user_reports(user_id: str, db: Session = Depends(get_db)):
    """Get all reports for a user."""
    reports = db.query(Report).filter(Report.user_id == user_id).all()
    return reports

@app.post("/users")
def create_user(email: str, password_hash: str, db: Session = Depends(get_db)):
    """Create a new user."""
    user = User(
        email=email,
        password_hash=password_hash,
        business_type="Manufacturing",
        company_size="Small"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

## Database Migrations

### Create a new migration

```bash
# After modifying models.py
alembic revision --autogenerate -m "Add new column to users table"
```

### Apply migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>
```

### Rollback migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

## Troubleshooting

### Connection refused

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql
```

### Authentication failed

- Verify username and password in DATABASE_URL
- Check PostgreSQL pg_hba.conf for authentication settings
- Ensure user has proper permissions

### Tables not created

```bash
# Drop and recreate
python -c "from backend.database import drop_db, init_db; drop_db(); init_db()"

# Or use Alembic
alembic downgrade base
alembic upgrade head
```

### Import errors

```bash
# Ensure backend is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in development mode
pip install -e .
```

## Testing

Run database tests:

```bash
# Run all tests
pytest backend/database/test_database.py -v

# Run specific test
pytest backend/database/test_database.py::TestUserModel::test_create_user -v
```

## Production Considerations

1. **Connection Pooling**: Adjust pool size based on load
   ```env
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=40
   ```

2. **SSL/TLS**: Enable for production
   ```env
   DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
   ```

3. **Backups**: Set up automated backups
   ```bash
   pg_dump exportsathi > backup.sql
   ```

4. **Monitoring**: Use CloudWatch for RDS monitoring

5. **Read Replicas**: Consider for heavy read workloads

6. **Indexes**: Monitor slow queries and add indexes as needed
   ```sql
   CREATE INDEX idx_custom ON table_name(column_name);
   ```

## Next Steps

1. ✓ Database schema implemented
2. → Implement database CRUD operations in services
3. → Integrate with FastAPI routers
4. → Add authentication and authorization
5. → Implement data validation
6. → Add comprehensive tests
