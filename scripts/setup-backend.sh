#!/bin/bash
# Backend setup script for ExportSathi

set -e

echo "=== ExportSathi Backend Setup ==="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Navigate to backend directory
cd backend

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your AWS credentials and database URL"
fi

# Create data directory for FAISS index
echo ""
echo "Creating data directory..."
mkdir -p data/faiss_index

echo ""
echo "=== Backend Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your configuration"
echo "2. Set up PostgreSQL database and run schema.sql"
echo "3. Configure AWS services (see infrastructure/aws-setup.md)"
echo "4. Run: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo ""
