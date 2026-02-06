# ExportSathi Database Package

This package contains the database schema, ORM models, and connection management for the ExportSathi platform.

## Structure

```
database/
├── __init__.py           # Package exports
├── models.py             # SQLAlchemy ORM models
├── connection.py         # Database connection and session management
├── schema.sql            # Raw SQL schema (reference)
├── init_db.py            # Database initialization script
├── alembic/              # Database migrations
│   ├── env.py            # Alembic environment configuration
│   ├── script.py.mako    # Migration template
│   └── versions/         # Migration scripts
│       └── 001_initial_schema.py
└── README.md             # This file
```

## Database Schema

The database uses PostgreSQL with the following tables:

### Core Tables

1. **users** - User accounts and profiles
   - Stores user authentication and business information
   - Tracks business type (Manufacturing/SaaS/Merchant) and company size

2. **reports** - Export readiness reports
   - Contains product details, HS code predictions, and risk assessments
   - Stores complete report data as JSONB for flexibility

3. **certification_progress** - Certification tracking
   - Tracks progress on required certifications (FDA, CE, REACH, etc.)
   - Stores document completion status

4. **generated_documents** - Export documents
   - Stores generated documents (invoices, packing lists, etc.)
   - Includes validation results and document URLs

5. **action_plan_progress** - 7-day action plan tracking
   - Tracks completion of daily tasks
   - Organized by day number (1-7)

### Communication Tables

6. **chat_sessions** - Chat conversation sessions
   - Maintains context for Q&A interactions
   - Includes session expiration

7. **chat_messages** - Individual chat messages
   - Stores user and assistant messages
   - Includes source citations

### Analysis Tables

8. **finance_analysis** - Finance readiness data
   - Working capital calculations
   - RoDTEP benefits and GST refund estimates

9. **logistics_analysis** - Logistics risk assessments
   - LCL vs FCL comparisons
   - RMS probability and freight estimates

10. **user_metrics** - User success metrics
    - Tracks reports generated, certifications completed
    - Calculates cost savings and timeline reductions

## Usage

### Initialize Database

```python
from backend.database import init_db, check_db_connection

# Check connection
if check_db_connection():
    print("Database connected!")

# Create all tables
init_db()
```

### Get Database Session

```python
from backend.database import get_db
from fastapi import Depends

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

### Use Session Context Manager

```python
from backend.database import db_connection

with db_connection.session_scope() as session:
    user = User(email="test@example.com", ...)
    session.add(user)
    # Automatically commits on success, rolls back on error
```

### Query with ORM Models

```python
from backend.database import User, Report
from sqlalchemy.orm import Session

def get_user_reports(db: Session, user_id: str):
    return db.query(Report).filter(Report.user_id == user_id).all()

def create_user(db: Session, email: str, password_hash: str, business_type: str):
    user = User(
        email=email,
        password_hash=password_hash,
        business_type=business_type,
        company_size="Small"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

## Database Migrations

### Using Alembic

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current revision
alembic current
```

### Manual Initialization

```bash
# Run the initialization script
python backend/database/init_db.py
```

## Configuration

Database configuration is managed through environment variables in `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/exportsathi
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

## Connection Pooling

The database connection uses SQLAlchemy's QueuePool with:
- Pool size: 10 connections (configurable)
- Max overflow: 20 additional connections (configurable)
- Pre-ping: Verifies connections before use
- Pool recycle: Recycles connections after 1 hour

## Features

### Automatic Timestamps

All tables with `created_at` and `updated_at` columns have automatic timestamp management:
- `created_at` is set on insert
- `updated_at` is automatically updated on every update

### Cascade Deletes

Foreign key relationships use `CASCADE` delete:
- Deleting a user deletes all their reports, documents, etc.
- Deleting a report deletes all associated data

### JSONB Storage

Complex data structures are stored as JSONB for:
- Flexibility in schema evolution
- Efficient querying with PostgreSQL JSONB operators
- Reduced need for additional tables

### Indexes

Performance-optimized indexes on:
- Foreign keys (user_id, report_id)
- Frequently queried fields (email, hs_code, destination_country)
- Status fields for filtering
- Timestamp fields for sorting

## Testing

```python
import pytest
from backend.database import Base, db_connection

@pytest.fixture
def db_session():
    """Create a test database session."""
    # Create tables
    Base.metadata.create_all(bind=db_connection.engine)
    
    session = db_connection.get_session()
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=db_connection.engine)

def test_create_user(db_session):
    user = User(email="test@example.com", ...)
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.email == "test@example.com"
```

## Security Considerations

1. **Password Storage**: Always store password hashes, never plain text
2. **SQL Injection**: Use ORM queries or parameterized queries
3. **Connection Security**: Use SSL/TLS for database connections in production
4. **Data Encryption**: Enable encryption at rest in RDS settings
5. **Access Control**: Use IAM roles for AWS RDS access

## Troubleshooting

### Connection Issues

```python
from backend.database import check_db_connection

if not check_db_connection():
    print("Database connection failed!")
    # Check DATABASE_URL in .env
    # Verify PostgreSQL is running
    # Check network connectivity
```

### Migration Issues

```bash
# Reset migrations (WARNING: Deletes all data)
alembic downgrade base
alembic upgrade head

# Or manually drop and recreate
python -c "from backend.database import drop_db, init_db; drop_db(); init_db()"
```

### Performance Issues

- Check query execution plans: `EXPLAIN ANALYZE SELECT ...`
- Add indexes for frequently queried columns
- Use JSONB operators efficiently
- Monitor connection pool usage
- Consider read replicas for heavy read workloads
