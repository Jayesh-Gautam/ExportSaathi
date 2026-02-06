#!/bin/bash
# Database setup script for ExportSathi

set -e

echo "=== ExportSathi Database Setup ==="
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "Error: PostgreSQL is not installed"
    echo "Please install PostgreSQL 15+ from https://www.postgresql.org/"
    exit 1
fi

# Database configuration
DB_NAME="exportsathi"
DB_USER="exportsathi_user"
DB_PASSWORD="exportsathi_password"

echo "Database configuration:"
echo "  Name: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Prompt for confirmation
read -p "Do you want to create the database? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Database setup cancelled"
    exit 0
fi

# Create database user
echo "Creating database user..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "User already exists"

# Create database
echo "Creating database..."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || echo "Database already exists"

# Grant privileges
echo "Granting privileges..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Apply schema
echo ""
echo "Applying database schema..."
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -f backend/database/schema.sql

echo ""
echo "=== Database Setup Complete ==="
echo ""
echo "Database connection string:"
echo "postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
echo ""
echo "Update this in your backend/.env file as DATABASE_URL"
echo ""
