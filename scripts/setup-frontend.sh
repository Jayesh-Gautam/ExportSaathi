#!/bin/bash
# Frontend setup script for ExportSathi

set -e

echo "=== ExportSathi Frontend Setup ==="
echo ""

# Check Node.js version
echo "Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

node_version=$(node --version)
echo "Node.js version: $node_version"

# Check npm version
npm_version=$(npm --version)
echo "npm version: $npm_version"

# Navigate to frontend directory
cd frontend

# Install dependencies
echo ""
echo "Installing Node.js dependencies..."
npm install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created frontend/.env"
fi

echo ""
echo "=== Frontend Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Ensure backend is running on http://localhost:8000"
echo "2. Run: cd frontend && npm run dev"
echo "3. Open http://localhost:3000 in your browser"
echo ""
