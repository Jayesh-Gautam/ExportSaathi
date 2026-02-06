#!/bin/bash
# Complete setup script for ExportSathi

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ExportSathi - Complete Setup Script               ║"
echo "║  AI-Powered Export Compliance & Certification Co-Pilot    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Step 1: Backend setup
echo "Step 1/3: Setting up backend..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash scripts/setup-backend.sh

# Step 2: Frontend setup
echo ""
echo "Step 2/3: Setting up frontend..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash scripts/setup-frontend.sh

# Step 3: Database setup
echo ""
echo "Step 3/3: Setting up database..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Do you want to set up the local PostgreSQL database? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash scripts/setup-database.sh
else
    echo "Skipping database setup. You can run it later with: bash scripts/setup-database.sh"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Setup Complete! 🎉                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure AWS Services:"
echo "   - Follow the guide in infrastructure/aws-setup.md"
echo "   - Set up RDS, S3, Bedrock, Textract, Comprehend"
echo "   - Update backend/.env with AWS credentials"
echo ""
echo "2. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn main:app --reload"
echo ""
echo "3. Start the frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "For more information, see README.md"
echo ""
