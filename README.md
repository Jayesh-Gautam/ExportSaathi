# ExportSathi - AI-Powered Export Compliance & Certification Co-Pilot

ExportSathi helps Indian MSMEs (Micro, Small, and Medium Enterprises) start exporting within 7 days by providing:

- **HS Code Prediction**: Automatic product classification from images and descriptions
- **Certification Navigation**: Step-by-step guidance for FDA, CE, REACH, BIS, ZED, SOFTEX certifications
- **Smart Documentation**: Auto-generation and validation of export documents
- **Finance Planning**: Working capital, RoDTEP benefits, and pre-shipment credit analysis
- **Logistics Risk Assessment**: LCL vs FCL decisions, RMS probability, route analysis
- **7-Day Action Plan**: Day-by-day tasks to become export-ready

## Architecture

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: Python FastAPI + LangChain
- **AI Services**: AWS Bedrock (Claude/Llama), AWS Textract, AWS Comprehend
- **Database**: AWS RDS PostgreSQL
- **Storage**: AWS S3
- **Vector Store**: FAISS for RAG pipeline

## Project Structure

```
exportsathi/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # Application entry point
│   ├── config.py           # Configuration settings
│   ├── requirements.txt    # Python dependencies
│   ├── routers/            # API route handlers
│   ├── services/           # Business logic services
│   ├── models/             # Pydantic data models
│   └── database/           # Database schema and ORM
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   ├── types/          # TypeScript types
│   │   └── main.tsx        # Application entry point
│   ├── package.json        # Node dependencies
│   └── vite.config.ts      # Vite configuration
├── infrastructure/         # AWS setup documentation
└── .kiro/specs/           # Project specifications

```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- AWS Account with Bedrock access

### Backend Setup

1. **Create Python virtual environment**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your AWS credentials and database URL
```

4. **Set up database**:
```bash
# Create PostgreSQL database
createdb exportsathi

# Apply schema
psql -d exportsathi -f database/schema.sql
```

5. **Run backend server**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### Frontend Setup

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your API base URL
```

3. **Run development server**:
```bash
npm run dev
```

Frontend will be available at http://localhost:3000

### AWS Infrastructure Setup

Follow the detailed guide in `infrastructure/aws-setup.md` to:
1. Create RDS PostgreSQL database
2. Set up S3 buckets for knowledge base, images, and documents
3. Enable AWS Bedrock and request model access
4. Configure IAM roles and security groups
5. Set up CloudWatch logging

## Development

### Backend Development

- **Add new API endpoint**: Create route in `backend/routers/`
- **Add business logic**: Create service in `backend/services/`
- **Add data model**: Create Pydantic model in `backend/models/`
- **Run tests**: `pytest`
- **Run property tests**: `pytest -m property`

### Frontend Development

- **Add new component**: Create in `frontend/src/components/`
- **Add new page**: Add route in `frontend/src/App.tsx`
- **Add API call**: Update `frontend/src/services/api.ts`
- **Run tests**: `npm test`
- **Build for production**: `npm run build`

## Testing

### Backend Testing

```bash
cd backend
pytest                          # Run all tests
pytest -m property             # Run property-based tests
pytest tests/test_reports.py   # Run specific test file
```

### Frontend Testing

```bash
cd frontend
npm test                       # Run all tests
npm run test:ui               # Run tests with UI
```

## Deployment

### Backend Deployment (AWS EC2)

1. Launch EC2 instance (t3.micro or larger)
2. Install Python and dependencies
3. Configure environment variables
4. Set up systemd service for uvicorn
5. Configure nginx as reverse proxy
6. Enable HTTPS with Let's Encrypt

### Frontend Deployment (AWS Amplify or S3 + CloudFront)

**Option 1: AWS Amplify**
```bash
npm run build
# Deploy via AWS Amplify Console
```

**Option 2: S3 + CloudFront**
```bash
npm run build
aws s3 sync dist/ s3://your-bucket-name
# Configure CloudFront distribution
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

### Backend (.env)

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# AWS Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# AWS S3
S3_KNOWLEDGE_BASE_BUCKET=exportsathi-knowledge-base
S3_PRODUCT_IMAGES_BUCKET=exportsathi-product-images
S3_GENERATED_DOCS_BUCKET=exportsathi-generated-docs

# Database
DATABASE_URL=postgresql://user:pass@host:5432/exportsathi

# Security
SECRET_KEY=your-secret-key
```

### Frontend (.env)

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Features

### Core Features (MVP)

- [x] Project structure and infrastructure setup
- [ ] RAG pipeline with vector store
- [ ] HS code prediction from product images
- [ ] Export readiness report generation
- [ ] Certification guidance system
- [ ] Document generation and validation
- [ ] Finance readiness module
- [ ] Logistics risk assessment
- [ ] 7-day action plan
- [ ] Interactive chat Q&A

### User Personas

1. **Manufacturing MSMEs**: LED lights, textiles, toys, chemicals
   - Focus: Certification guidance, HS code mapping, rejection prevention
   
2. **SaaS/Service Exporters**: Software and digital services
   - Focus: SOFTEX filing, payment reconciliation, service classification
   
3. **Merchant Exporters**: Trading companies
   - Focus: LCL shipment risks, RMS checks, customs broker selection

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

## Support

For questions or issues:
- Create an issue in the repository
- Contact: support@exportsathi.com

## Acknowledgments

- AWS Bedrock for LLM capabilities
- LangChain for RAG pipeline
- FastAPI for backend framework
- React for frontend framework
- DGFT, Customs, FDA, and EU regulatory bodies for data sources
