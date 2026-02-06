# Implementation Plan: ExportSathi

## Overview

This implementation plan breaks down the ExportSathi AI-powered Export Compliance & Certification Co-Pilot into discrete, actionable coding tasks. The platform helps Indian MSMEs start exporting within 7 days by providing HS code prediction, certification guidance, document generation, finance planning, and logistics risk assessment.

The implementation follows a phased approach:
1. **Foundation**: Core infrastructure, data models, and AWS services setup ✅ MOSTLY COMPLETE
2. **AI Layer**: RAG pipeline, vector store, and LLM integration ✅ COMPLETE
3. **Core Features**: Report generation, HS code prediction, certification solver ⚠️ IN PROGRESS
4. **Documentation & Finance**: Document generation/validation, finance module ❌ NOT STARTED
5. **Logistics & Chat**: Logistics risk shield, chat interface ❌ NOT STARTED
6. **Frontend**: React UI with persona-specific features ⚠️ PARTIALLY COMPLETE
7. **Integration & Polish**: End-to-end integration, testing, deployment ❌ NOT STARTED

## Current Status Summary

**Completed:**
- ✅ Project structure and infrastructure setup
- ✅ All Pydantic models and TypeScript interfaces
- ✅ Database schema and migrations
- ✅ RAG pipeline with vector store (FAISS)
- ✅ Embedding service
- ✅ LLM clients (Bedrock and Groq)
- ✅ AWS Textract and Comprehend integration
- ✅ HS Code Predictor service
- ✅ Report Generator service (basic implementation)
- ✅ Reports API router (fully implemented)
- ✅ Frontend QueryForm component
- ✅ Frontend ReportDisplay component (basic)
- ✅ Frontend React setup with routing

**In Progress:**
- ⚠️ Report generation needs enhancement (certification identification, risk calculation)
- ⚠️ Frontend report display components need expansion

**Not Started:**
- ❌ Certification Solver service
- ❌ Document Generator and Validator services
- ❌ Finance Module services
- ❌ Logistics Risk Shield services
- ❌ Action Plan Generator service
- ❌ Chat Service
- ❌ Most API router implementations (stubs only)
- ❌ Most frontend feature components
- ❌ Security and authentication
- ❌ Deployment configuration

## Tasks

- [x] 1. Set up project structure and core infrastructure
  - Create backend directory structure with FastAPI application
  - Create frontend directory structure with React + TypeScript
  - Set up Python virtual environment and install dependencies (FastAPI, Pydantic, LangChain, Boto3, SQLAlchemy, Hypothesis)
  - Set up Node.js project and install dependencies (React, TypeScript, Axios, React Query, Tailwind CSS, fast-check)
  - Configure environment variables for AWS services (Bedrock, Textract, Comprehend, RDS, S3)
  - Set up AWS RDS PostgreSQL database and create initial schema
  - Configure AWS S3 buckets (knowledge base, product images, generated documents)
  - Set up IAM roles and security groups for AWS services
  - _Requirements: 12.1, 12.2, 12.3, 12.7, 12.9_

- [ ] 2. Implement data models and database schema
  - [x] 2.1 Create Pydantic models for backend
    - Define enums (BusinessType, CompanySize, CertificationType, DocumentType, etc.)
    - Create request models (QueryInput, ChatRequest, etc.)
    - Create response models (ExportReadinessReport, CertificationGuidance, FinanceAnalysis, etc.)
    - Create domain models (HSCodePrediction, Certification, Risk, ActionPlan, etc.)
    - Add validation rules using Pydantic validators
    - _Requirements: 1.1, 2.7, 3.1, 4.1, 5.1, 6.1_

  - [ ]* 2.2 Write property test for data model validation
    - **Property 2: Invalid inputs are rejected with validation feedback**
    - **Validates: Requirements 1.5, 8.5, 8.6**

  - [x] 2.3 Create TypeScript interfaces for frontend
    - Define all data models matching backend Pydantic models
    - Create type definitions for API requests and responses
    - Add type guards for runtime validation
    - _Requirements: 1.1, 2.7, 3.1, 4.1, 5.1, 6.1_

  - [x] 2.4 Implement database schema in PostgreSQL
    - Create tables: users, reports, certification_progress, generated_documents, action_plan_progress, chat_sessions, chat_messages, finance_analysis, logistics_analysis, user_metrics
    - Add indexes for performance optimization
    - Create database migration scripts
    - _Requirements: 12.8, 17.2_

  - [ ]* 2.5 Write unit tests for database operations
    - Test CRUD operations for each table
    - Test foreign key constraints and cascading deletes
    - Test index usage for common queries
    - _Requirements: 12.8_


- [ ] 3. Build RAG pipeline and vector store foundation
  - [x] 3.1 Implement embedding service
    - Set up sentence-transformers with all-mpnet-base-v2 model
    - Create EmbeddingService class with embed_query and embed_documents methods
    - Implement batch processing for efficient embedding generation
    - Add caching mechanism for repeated queries
    - _Requirements: 10.1_

  - [ ]* 3.2 Write property test for embedding generation
    - **Property 37: Query embedding generation**
    - **Validates: Requirements 10.1**

  - [x] 3.3 Implement vector store with FAISS
    - Create VectorStore abstract interface
    - Implement FAISSVectorStore with add_documents, search, and search_by_metadata methods
    - Add metadata filtering capabilities
    - Implement index persistence to S3
    - _Requirements: 9.2, 9.3, 9.4_

  - [ ]* 3.4 Write property test for document round-trip persistence
    - **Property 39: Document round-trip persistence**
    - **Validates: Requirements 9.2**

  - [x] 3.5 Create knowledge base document loader
    - Implement script to load documents from S3 knowledge base bucket
    - Parse document metadata (source type, country, product categories, certifications)
    - Generate embeddings for all documents
    - Build and save FAISS index
    - _Requirements: 9.1, 9.2, 9.7_

  - [x] 3.6 Implement RAG pipeline orchestration
    - Create RAGPipeline service with retrieve_documents and generate_with_context methods
    - Implement query embedding and semantic search
    - Add document ranking by relevance score
    - Implement context injection for LLM prompts
    - Add government source prioritization logic
    - _Requirements: 10.2, 10.3, 10.4, 10.6_

  - [ ]* 3.7 Write property test for document retrieval ranking
    - **Property 38: Document retrieval ranking**
    - **Validates: Requirements 10.2**

  - [ ]* 3.8 Write property test for semantic search similarity
    - **Property 40: Semantic search similarity**
    - **Validates: Requirements 9.3**


- [ ] 4. Integrate AWS services and LLM clients
  - [x] 4.1 Implement AWS Bedrock client
    - Create BedrockClient class using Boto3
    - Implement generate method with model selection (Claude 3, Llama 3, Mixtral)
    - Add generate_structured method for JSON responses
    - Implement retry logic with exponential backoff
    - Add rate limiting and error handling
    - _Requirements: 11.1, 11.2, 11.4_

  - [x] 4.2 Implement Groq API client as alternative
    - Create GroqClient class with same interface as BedrockClient
    - Implement API authentication and request handling
    - Add retry logic and error handling
    - _Requirements: 11.1_

  - [x] 4.3 Create unified LLM client interface
    - Define LLMClient abstract interface
    - Implement factory pattern for client selection (Bedrock or Groq)
    - Add configuration for model selection and parameters
    - _Requirements: 11.1_

  - [x] 4.4 Implement AWS Textract integration
    - Create ImageProcessor service using AWS Textract
    - Implement extract_text method for product images
    - Implement extract_features method for visual analysis
    - Add image preprocessing and validation
    - _Requirements: 1.2, 12.4_

  - [x] 4.5 Implement AWS Comprehend integration
    - Create ComplianceTextAnalyzer service using AWS Comprehend
    - Implement entity extraction for compliance terms
    - Implement key phrase extraction
    - Add document validation capabilities
    - _Requirements: 12.5_

  - [ ]* 4.6 Write unit tests for AWS service integrations
    - Mock AWS API calls and test error handling
    - Test retry logic for transient failures
    - Test rate limiting behavior
    - _Requirements: 11.1, 12.4, 12.5_


- [ ] 5. Implement HS code prediction and product analysis
  - [x] 5.1 Create HS code predictor service
    - Implement HSCodePredictor with predict_hs_code method
    - Integrate image feature extraction using Textract
    - Combine image features with product description and BOM
    - Query vector store for similar products with known HS codes
    - Use LLM to predict HS code with confidence score
    - Return prediction with alternatives if confidence < 70%
    - _Requirements: 2.1, 2.8_

  - [ ]* 5.2 Write property test for HS code prediction completeness
    - **Property 6: HS code prediction completeness**
    - **Validates: Requirements 2.1**

  - [ ] 5.3 Implement restricted substances analyzer
    - Create service to identify restricted substances from ingredients/BOM
    - Query knowledge base for substance regulations by destination country
    - Return list of restricted substances with reasons and regulations
    - _Requirements: 2.3_

  - [ ]* 5.4 Write property test for restricted substances analysis
    - **Property 11: Restricted substances analysis**
    - **Validates: Requirements 2.3**

  - [ ] 5.5 Implement past rejection data retrieval
    - Query FDA refusal database and EU RASFF for similar products
    - Filter by product type and destination country
    - Return rejection reasons with source and date
    - _Requirements: 2.4_

  - [ ]* 5.6 Write property test for past rejection data retrieval
    - **Property 12: Past rejection data retrieval**
    - **Validates: Requirements 2.4**


- [ ] 6. Build export readiness report generator
  - [x] 6.1 Create report generator service
    - Implement ReportGenerator with generate_report method
    - Orchestrate HS code prediction, certification identification, risk analysis
    - Generate compliance roadmap with timeline and dependencies
    - Calculate risk score (0-100) based on product complexity and historical data
    - Estimate costs (certifications, documentation, logistics)
    - Identify applicable subsidies (ZED, RoDTEP, etc.)
    - Retrieve and include source citations from knowledge base
    - _Requirements: 2.2, 2.5, 2.6, 2.7_

  - [ ]* 6.2 Write property test for report structure completeness
    - **Property 7: Export readiness report structure completeness**
    - **Validates: Requirements 2.7, 13.1**

  - [ ]* 6.3 Write property test for certifications identification
    - **Property 8: Certifications identification**
    - **Validates: Requirements 2.2**

  - [ ]* 6.4 Write property test for risk score bounds
    - **Property 9: Risk score bounds**
    - **Validates: Requirements 2.6**

  - [x] 6.5 Enhance certification identifier in report generator
    - Query knowledge base for required certifications by HS code and destination
    - Identify mandatory vs optional certifications
    - Estimate cost ranges and timelines for each certification
    - Prioritize certifications (high/medium/low)
    - Support FDA, CE, REACH, BIS, ZED, SOFTEX, and others
    - _Requirements: 2.2, 3.8_

  - [ ] 6.6 Enhance risk calculator in report generator
    - Calculate risk score based on product complexity, destination regulations, historical rejections
    - Identify specific risks with severity levels
    - Generate mitigation strategies for each risk
    - _Requirements: 2.6_

  - [ ] 6.7 Create prompt templates for report generation
    - Design master prompt with ExportSathi persona and guardrails
    - Create section-specific prompts (certifications, risks, timeline, costs)
    - Include retrieved documents as context
    - Enforce structured output format
    - _Requirements: 11.3, 11.6, 11.7_

  - [ ]* 6.8 Write unit tests for enhanced report generation components
    - Test certification identification with known HS codes
    - Test risk calculation with sample data
    - Test prompt template construction
    - _Requirements: 2.2, 2.6_


- [ ] 7. Implement certification solver and guidance system
  - [x] 7.1 Create certification solver service
    - Implement CertificationSolver with generate_guidance method
    - Retrieve certification-specific documents from knowledge base
    - Generate step-by-step acquisition roadmap
    - Create document checklist with mandatory/optional flags
    - Identify approved test labs with contact information
    - List available consultants from marketplace
    - Identify applicable subsidies (e.g., ZED 80% for micro enterprises)
    - Generate common rejection reasons and mock audit questions
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.6_

  - [ ]* 7.2 Write property test for certification guidance completeness
    - **Property 13: Certification guidance completeness**
    - **Validates: Requirements 3.1, 3.2, 3.4, 3.5, 3.6**

  - [ ] 7.3 Implement certification progress tracking
    - Create database operations for certification_progress table
    - Implement update_progress method to mark certifications as in-progress/completed
    - Track document completion status
    - _Requirements: 3.7_

  - [ ]* 7.4 Write property test for certification progress persistence
    - **Property 14: Certification progress persistence**
    - **Validates: Requirements 3.7**

  - [ ] 7.5 Create consultant marketplace integration
    - Define consultant data model with ratings and cost ranges
    - Implement search and filter functionality
    - Add contact information and specialization details
    - _Requirements: 3.4_

  - [ ]* 7.6 Write unit tests for certification solver
    - Test guidance generation for specific certifications (FDA, CE, BIS)
    - Test document checklist creation
    - Test subsidy identification for different company sizes
    - _Requirements: 3.1, 3.5_


- [ ] 8. Build smart documentation layer
  - [ ] 8.1 Create document generator service
    - Implement DocumentGenerator with generate_document method
    - Support document types: commercial invoice, packing list, shipping bill, GST LUT, SOFTEX, certificate of origin
    - Load India-specific templates for each document type
    - Auto-fill templates with user data from reports and profiles
    - Generate documents in PDF and editable formats
    - _Requirements: 4.1, 4.2, 4.5_

  - [ ]* 8.2 Write property test for document generation support
    - **Property 15: Document generation support**
    - **Validates: Requirements 4.1**

  - [ ] 8.3 Implement document validator service
    - Create DocumentValidator with validate method
    - Implement port code mismatch detection
    - Validate invoice format compliance
    - Check GST vs Shipping Bill data matching
    - Detect RMS risk trigger keywords
    - Use AWS Comprehend for compliance text validation
    - _Requirements: 4.3, 4.4, 4.8_

  - [ ]* 8.4 Write property test for document validation execution
    - **Property 16: Document validation execution**
    - **Validates: Requirements 4.3**

  - [ ]* 8.5 Write property test for validation error reporting
    - **Property 17: Validation error reporting**
    - **Validates: Requirements 4.4**

  - [ ] 8.4 Create document templates
    - Design India-specific templates for all document types
    - Include mandatory fields and formatting requirements
    - Add SOFTEX template for SaaS exporters
    - Ensure templates comply with DGFT and customs requirements
    - _Requirements: 4.2, 4.6_

  - [ ] 8.5 Implement RMS risk trigger detection
    - Create list of red flag keywords that trigger RMS checks
    - Scan product descriptions and documents for these keywords
    - Provide warnings and alternative wording suggestions
    - _Requirements: 4.3, 6.5_

  - [ ]* 8.6 Write unit tests for document generation and validation
    - Test document generation for each type with sample data
    - Test validation rules with valid and invalid documents
    - Test RMS keyword detection with known triggers
    - _Requirements: 4.1, 4.3, 4.8_


- [ ] 9. Implement finance readiness module
  - [ ] 9.1 Create finance module service
    - Implement FinanceModule with calculate_working_capital method
    - Calculate total working capital (product + certification + logistics + documentation + buffer)
    - Assess pre-shipment credit eligibility based on company profile
    - Generate cash flow timeline with expense and income events
    - Identify liquidity gap periods
    - Suggest financing options and bank referral programs
    - _Requirements: 5.1, 5.2, 5.5, 5.6, 5.7_

  - [ ]* 9.2 Write property test for working capital calculation completeness
    - **Property 21: Working capital calculation completeness**
    - **Validates: Requirements 5.1**

  - [ ]* 9.3 Write property test for cash flow timeline generation
    - **Property 24: Cash flow timeline generation**
    - **Validates: Requirements 5.5, 5.6**

  - [ ] 9.2 Implement RoDTEP calculator
    - Create RoDTEPCalculator with calculate_benefit method
    - Load RoDTEP schedules from knowledge base
    - Calculate benefit amount based on HS code and destination
    - Return rate percentage and estimated amount
    - _Requirements: 5.3_

  - [ ]* 9.4 Write property test for RoDTEP benefit calculation
    - **Property 23: RoDTEP benefit calculation**
    - **Validates: Requirements 5.3**

  - [ ] 9.3 Implement GST refund estimator
    - Calculate GST refund amount based on export value
    - Estimate refund timeline (typically 30-60 days)
    - List requirements for GST refund application
    - _Requirements: 5.8_

  - [ ]* 9.5 Write property test for GST refund estimation
    - **Property 27: GST refund estimation**
    - **Validates: Requirements 5.8**

  - [ ] 9.4 Create credit eligibility assessor
    - Implement logic to assess pre-shipment credit eligibility
    - Consider company size, order value, banking relationships
    - Calculate estimated credit amount and interest rate
    - _Requirements: 5.2_

  - [ ] 9.5 Implement currency hedging advisor
    - Provide currency hedging recommendations based on order value
    - Suggest hedging strategies (forward contracts, options)
    - Estimate potential savings from hedging
    - _Requirements: 5.4_

  - [ ]* 9.6 Write unit tests for finance module components
    - Test working capital calculation with various inputs
    - Test RoDTEP calculation with known HS codes
    - Test credit eligibility assessment logic
    - _Requirements: 5.1, 5.2, 5.3_


- [ ] 10. Build logistics risk shield
  - [ ] 10.1 Create logistics risk shield service
    - Implement LogisticsRiskShield with analyze_risks method
    - Compare LCL vs FCL options based on volume and product type
    - Estimate RMS probability using product description and HS code
    - Predict route delays based on geopolitical factors
    - Estimate freight costs for different routes and modes
    - Recommend insurance coverage based on shipment value
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.6_

  - [ ]* 10.2 Write property test for LCL vs FCL comparison
    - **Property 28: LCL vs FCL comparison**
    - **Validates: Requirements 6.1**

  - [ ]* 10.3 Write property test for RMS probability estimation
    - **Property 29: RMS probability estimation**
    - **Validates: Requirements 6.2, 6.5**

  - [ ] 10.2 Implement RMS predictor
    - Create RMSPredictor with predict_probability method
    - Load customs RMS rules from knowledge base
    - Identify risk factors based on product, HS code, description
    - Detect red flag keywords in product descriptions
    - Calculate probability percentage (0-100)
    - Provide mitigation tips
    - _Requirements: 6.2, 6.5_

  - [ ] 10.3 Implement freight estimator
    - Create FreightEstimator with estimate_cost method
    - Calculate sea freight and air freight costs
    - Consider route, volume, weight, and destination
    - Recommend shipping mode based on urgency and cost
    - _Requirements: 6.4_

  - [ ] 10.4 Implement route analyzer
    - Analyze available shipping routes to destination
    - Predict delays based on geopolitical situations (e.g., Red Sea disruptions)
    - Consider seasonal factors affecting transit times
    - Estimate transit time for each route
    - _Requirements: 6.3, 6.7_

  - [ ]* 10.5 Write unit tests for logistics risk shield
    - Test LCL vs FCL comparison with different volumes
    - Test RMS probability calculation with known risk factors
    - Test freight estimation with sample routes
    - _Requirements: 6.1, 6.2, 6.4_


- [ ] 11. Implement 7-day action plan generator
  - [ ] 11.1 Create action plan generator service
    - Implement ActionPlanGenerator with generate_plan method
    - Prioritize tasks based on dependencies (GST LUT before shipment, critical certifications first)
    - Distribute tasks across 7 days with realistic timelines
    - Account for government processing times
    - Flag certifications requiring >7 days with interim steps
    - Generate tasks for: Day 1 (GST LUT, HS code confirmation), Day 2-3 (certifications), Day 4-5 (documents), Day 6 (logistics), Day 7 (review)
    - _Requirements: 13.1, 13.2, 13.3, 13.5, 13.6_

  - [ ]* 11.2 Write property test for action plan day distribution
    - **Property 44: Action plan day distribution**
    - **Validates: Requirements 13.3**

  - [ ]* 11.3 Write property test for task dependency ordering
    - **Property 45: Task dependency ordering**
    - **Validates: Requirements 13.2**

  - [ ] 11.2 Implement action plan progress tracker
    - Create database operations for action_plan_progress table
    - Implement update_task_status method to mark tasks as completed
    - Calculate progress percentage based on completed tasks
    - Estimate export-ready date based on remaining tasks
    - _Requirements: 13.4_

  - [ ]* 11.4 Write property test for task completion persistence
    - **Property 46: Task completion persistence**
    - **Validates: Requirements 13.4**

  - [ ] 11.3 Implement PDF export for action plan
    - Generate PDF checklist from action plan data
    - Include day-by-day tasks with checkboxes
    - Add progress tracking section
    - _Requirements: 13.7_

  - [ ]* 11.5 Write unit tests for action plan generator
    - Test task prioritization logic
    - Test dependency resolution
    - Test progress calculation
    - _Requirements: 13.2, 13.4_


- [ ] 12. Build chat interface and Q&A system
  - [ ] 12.1 Create chat service
    - Implement ChatService with process_question method
    - Retrieve conversation history from database
    - Maintain query context (product type, destination, report ID)
    - Use RAG pipeline to retrieve relevant documents for questions
    - Generate responses with source citations
    - Store messages in chat_messages table
    - _Requirements: 7.2, 7.3, 7.4, 7.7_

  - [ ]* 12.2 Write property test for chat context preservation
    - **Property 33: Chat context preservation**
    - **Validates: Requirements 7.2, 7.4**

  - [ ]* 12.3 Write property test for conversation history maintenance
    - **Property 34: Conversation history maintenance**
    - **Validates: Requirements 7.3**

  - [ ] 12.2 Implement session management
    - Create chat_sessions table operations
    - Implement create_session and clear_session methods
    - Add session TTL (time-to-live) for automatic cleanup
    - Ensure new queries create new sessions
    - _Requirements: 7.5_

  - [ ]* 12.4 Write property test for new query session isolation
    - **Property 35: New query session isolation**
    - **Validates: Requirements 7.5**

  - [ ] 12.3 Add source citation extraction
    - Extract source information from retrieved documents
    - Include title, source type, excerpt, and relevance score
    - Format citations for display in chat responses
    - _Requirements: 7.7, 10.4_

  - [ ]* 12.5 Write unit tests for chat service
    - Test question processing with context
    - Test conversation history retrieval
    - Test session creation and cleanup
    - _Requirements: 7.2, 7.3, 7.5_


- [ ] 13. Implement API endpoints and routing
  - [x] 13.1 Create reports API router
    - Implement POST /api/reports/generate endpoint with multipart form data
    - Implement GET /api/reports/{report_id} endpoint
    - Implement GET /api/reports/{report_id}/status endpoint
    - Implement PUT /api/reports/{report_id}/hs-code endpoint for manual override
    - Add request validation using Pydantic models
    - Add error handling and appropriate HTTP status codes
    - _Requirements: 8.1, 8.2, 8.3, 8.6_

  - [ ]* 13.2 Write property test for API responses are valid JSON
    - **Property 5: API responses are valid JSON with consistent structure**
    - **Validates: Requirements 8.7**

  - [ ] 13.3 Implement certifications API router
    - Implement GET /api/certifications endpoint
    - Implement POST /api/certifications/{cert_id}/guidance endpoint
    - Implement GET /api/certifications/{cert_id}/test-labs endpoint
    - Implement PUT /api/certifications/{cert_id}/progress endpoint
    - _Requirements: 8.1_

  - [ ] 13.4 Implement documents API router
    - Implement POST /api/documents/generate endpoint
    - Implement POST /api/documents/validate endpoint
    - Implement GET /api/documents/{doc_id}/download endpoint
    - _Requirements: 8.1_

  - [ ] 13.5 Implement finance API router
    - Implement GET /api/finance/analysis/{report_id} endpoint
    - Implement POST /api/finance/rodtep-calculator endpoint
    - Implement POST /api/finance/working-capital endpoint
    - _Requirements: 8.1_

  - [ ] 13.6 Implement logistics API router
    - Implement POST /api/logistics/risk-analysis endpoint
    - Implement POST /api/logistics/rms-probability endpoint
    - Implement POST /api/logistics/freight-estimate endpoint
    - _Requirements: 8.1_

  - [ ] 13.7 Implement action plan API router
    - Implement GET /api/action-plan/{report_id} endpoint
    - Implement PUT /api/action-plan/{report_id}/tasks/{task_id} endpoint
    - Implement GET /api/action-plan/{report_id}/download endpoint
    - _Requirements: 8.1_

  - [ ] 13.8 Implement chat API router
    - Implement POST /api/chat endpoint
    - Implement GET /api/chat/{session_id}/history endpoint
    - Implement DELETE /api/chat/{session_id} endpoint
    - _Requirements: 8.1_

  - [ ] 13.9 Implement users API router
    - Implement POST /api/users/register endpoint
    - Implement POST /api/users/login endpoint
    - Implement GET /api/users/profile endpoint
    - Implement PUT /api/users/profile endpoint
    - _Requirements: 8.1_

  - [ ]* 13.10 Write integration tests for API endpoints
    - Test complete report generation flow
    - Test certification guidance request flow
    - Test document generation and validation flow
    - Test chat conversation flow
    - _Requirements: 8.1, 8.2_


- [ ] 14. Implement security and error handling
  - [ ] 14.1 Add input validation and sanitization
    - Implement validation for all user inputs (text, files, parameters)
    - Sanitize inputs to prevent SQL injection and XSS attacks
    - Add file size limits for image uploads (10 MB)
    - Validate file types for uploads (images only)
    - _Requirements: 17.6_

  - [ ]* 14.2 Write property test for input sanitization
    - **Property 4: Input sanitization prevents injection**
    - **Validates: Requirements 17.6**

  - [ ] 14.2 Implement rate limiting
    - Add rate limiting middleware (100 requests per hour per user)
    - Return 429 Too Many Requests when limit exceeded
    - Track requests by IP address or user ID
    - _Requirements: 17.5_

  - [ ] 14.3 Add authentication and authorization
    - Implement JWT-based authentication
    - Create login and registration endpoints
    - Add authentication middleware for protected routes
    - Store password hashes (never plain text)
    - _Requirements: 17.7_

  - [ ] 14.4 Implement data encryption
    - Enable encryption at rest for RDS database
    - Use HTTPS for all client-server communication
    - Encrypt sensitive data in database (product details, BOM, pricing)
    - _Requirements: 17.1, 17.2_

  - [ ] 14.5 Add comprehensive error handling
    - Implement error handlers for all API endpoints
    - Return appropriate HTTP status codes (400, 401, 403, 404, 422, 429, 500, 503)
    - Provide user-friendly error messages without exposing technical details
    - Log errors with full context for debugging
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [ ] 14.6 Implement CloudWatch logging
    - Configure structured logging with JSON format
    - Log all API requests and responses
    - Log errors with stack traces
    - Set up log levels (ERROR, WARNING, INFO, DEBUG)
    - _Requirements: 12.10, 15.4_

  - [ ]* 14.7 Write unit tests for security features
    - Test input validation with malicious inputs
    - Test rate limiting behavior
    - Test authentication and authorization
    - _Requirements: 17.5, 17.6, 17.7_


- [ ] 15. Checkpoint - Backend core functionality complete
  - Ensure all backend services are implemented and tested
  - Verify RAG pipeline retrieves relevant documents
  - Verify report generation produces complete reports
  - Verify all API endpoints return valid responses
  - Run all unit tests and property tests
  - Ask the user if questions arise

- [ ] 16. Build React frontend foundation
  - [x] 16.1 Set up React application structure
    - Create component directory structure
    - Set up React Router for navigation
    - Configure Tailwind CSS for styling
    - Set up Axios for API calls
    - Configure React Query for server state management
    - _Requirements: 1.1_

  - [ ] 16.2 Create API client service
    - Implement API client with methods for all endpoints
    - Add request/response interceptors for error handling
    - Add authentication token management
    - Implement retry logic for failed requests
    - _Requirements: 8.1_

  - [ ] 16.3 Implement custom hooks
    - Create useLocalStorage hook for checklist persistence
    - Create useApi hook for API calls with loading/error states
    - Create useAuth hook for authentication state
    - _Requirements: 7.3_

  - [ ] 16.4 Create common components
    - Implement LoadingSpinner component with progress messages
    - Implement ErrorBoundary component for error handling
    - Create Button, Input, Select, and other form components
    - Create Modal component for dialogs
    - _Requirements: 15.5_

  - [ ]* 16.5 Write unit tests for common components
    - Test LoadingSpinner rendering
    - Test ErrorBoundary error catching
    - Test form components with user interactions
    - _Requirements: 15.5_


- [ ] 17. Implement onboarding and query form
  - [ ] 17.1 Create OnboardingForm component
    - Implement business type selection (Manufacturing/SaaS/Merchant)
    - Add company size selection (Micro/Small/Medium)
    - Add company name and monthly volume inputs
    - Validate form inputs before submission
    - Store user profile in state and localStorage
    - _Requirements: 1.1, 18.4_

  - [x] 17.2 Create QueryForm component
    - Implement product name input field
    - Add product image upload with preview
    - Add ingredients/BOM text area
    - Add destination country autocomplete
    - Add monthly volume and price range inputs
    - Implement form validation (required fields, max lengths)
    - Handle image file upload to backend
    - _Requirements: 1.1, 1.2, 1.4, 1.5_

  - [ ]* 17.3 Write property test for valid inputs acceptance
    - **Property 1: Valid inputs are accepted and processed**
    - **Validates: Requirements 1.3**

  - [ ]* 17.4 Write unit tests for form components
    - Test form validation with valid and invalid inputs
    - Test image upload functionality
    - Test form submission
    - _Requirements: 1.1, 1.5_


- [ ] 18. Build export readiness report display
  - [x] 18.1 Create ReportDisplay component
    - Implement main report container with expandable sections
    - Display loading state during report generation
    - Handle report generation errors
    - Show report metadata (generated date, status)
    - _Requirements: 2.7_

  - [ ] 18.2 Create HSCodeSection component
    - Display HS code with confidence percentage
    - Show confidence indicator (color-coded)
    - Display alternative codes if confidence < 70%
    - Add manual override option
    - _Requirements: 2.1_

  - [ ] 18.3 Create CertificationSection component
    - Display list of required certifications
    - Show certification cards with priority indicators
    - Display estimated cost and timeline for each
    - Add click handler to view detailed guidance
    - _Requirements: 2.2_

  - [ ] 18.4 Create ComplianceRoadmap component
    - Display visual timeline of compliance steps
    - Show step dependencies
    - Display duration for each step
    - Add progress tracking
    - _Requirements: 2.7_

  - [ ] 18.5 Create RisksSection component
    - Display identified risks with severity indicators
    - Show risk cards with color-coding (high/medium/low)
    - Display mitigation strategies
    - Show overall risk score (0-100)
    - _Requirements: 2.6_

  - [ ] 18.6 Create CostBreakdown component
    - Display cost breakdown by category (certifications, documentation, logistics)
    - Show total estimated cost
    - Display subsidies and potential savings
    - _Requirements: 2.5_

  - [ ] 18.7 Create TimelineSection component
    - Display estimated timeline in days
    - Show phase breakdown
    - Highlight critical path items
    - _Requirements: 2.5_

  - [ ]* 18.8 Write unit tests for report display components
    - Test component rendering with sample report data
    - Test expandable sections
    - Test error handling
    - _Requirements: 2.7_


- [ ] 19. Implement certification guidance interface
  - [ ] 19.1 Create CertificationDetailModal component
    - Display detailed certification guidance in modal
    - Show step-by-step acquisition roadmap
    - Display document checklist with completion tracking
    - Show test labs with contact information
    - Display consultant marketplace
    - Show subsidy information
    - Display mock audit questions
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.6_

  - [ ] 19.2 Create DocumentChecklist component
    - Display interactive checklist with checkboxes
    - Persist completion status to backend
    - Show mandatory vs optional documents
    - Add auto-fill assistance buttons
    - _Requirements: 3.2, 3.3, 3.7_

  - [ ] 19.3 Create TestLabList component
    - Display approved test labs with contact info
    - Show accreditation details
    - Add click-to-call and email functionality
    - _Requirements: 3.4_

  - [ ] 19.4 Create ConsultantMarketplace component
    - Display available consultants with ratings
    - Show specialization and cost ranges
    - Add filter and sort functionality
    - Implement contact/hire buttons
    - _Requirements: 3.4_

  - [ ]* 19.5 Write unit tests for certification guidance components
    - Test modal display and close functionality
    - Test checklist interaction and persistence
    - Test consultant filtering
    - _Requirements: 3.1, 3.7_


- [ ] 20. Build action plan interface
  - [ ] 20.1 Create ActionPlanSection component
    - Display 7-day action plan with daily tasks
    - Show progress bar with completion percentage
    - Add task checkboxes with persistence
    - Display task categories with color coding
    - Show task dependencies
    - Add PDF download button
    - _Requirements: 13.1, 13.3, 13.4, 13.7_

  - [ ] 20.2 Create DayPlan component
    - Display tasks for a specific day
    - Show day title and task count
    - Implement collapsible day sections
    - _Requirements: 13.3_

  - [ ] 20.3 Create Task component
    - Display task with checkbox
    - Show task description and estimated duration
    - Handle task completion toggle
    - Persist completion status to backend
    - _Requirements: 13.4_

  - [ ]* 20.4 Write unit tests for action plan components
    - Test task completion toggling
    - Test progress calculation
    - Test PDF download functionality
    - _Requirements: 13.4, 13.7_


- [ ] 21. Implement documentation hub
  - [ ] 21.1 Create DocumentationHub component
    - Display available document types
    - Show document generation status
    - Add document type selector
    - Display generated documents list
    - _Requirements: 4.1_

  - [ ] 21.2 Create DocumentGenerator component
    - Implement document type selection
    - Show auto-fill form with user data
    - Add manual editing capability
    - Trigger document generation API call
    - Display validation results
    - _Requirements: 4.1, 4.3_

  - [ ] 21.3 Create ValidationResults component
    - Display validation errors with severity
    - Show error location and suggested fixes
    - Highlight fields with errors
    - Add re-validation button
    - _Requirements: 4.4_

  - [ ] 21.4 Create DocumentPreview component
    - Display generated document preview
    - Show PDF and editable format options
    - Add download buttons
    - _Requirements: 4.5_

  - [ ]* 21.5 Write unit tests for documentation components
    - Test document generation flow
    - Test validation error display
    - Test document download
    - _Requirements: 4.1, 4.3, 4.5_


- [ ] 22. Build finance and logistics modules
  - [ ] 22.1 Create FinanceModule component
    - Display working capital breakdown
    - Show pre-shipment credit eligibility
    - Display RoDTEP benefit calculation
    - Show GST refund estimation
    - Display currency hedging recommendations
    - Show financing options
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.7, 5.8_

  - [ ] 22.2 Create CashFlowTimeline component
    - Implement interactive timeline visualization using Chart.js or Recharts
    - Display expense events (red) and income events (green)
    - Highlight liquidity gap periods
    - Add zoom and pan functionality
    - _Requirements: 5.5, 5.6_

  - [ ] 22.3 Create LogisticsRiskShield component
    - Display LCL vs FCL comparison
    - Show RMS probability with risk factors
    - Display route analysis with delays
    - Show freight cost estimates
    - Display insurance recommendations
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.6_

  - [ ] 22.4 Create RMSProbability component
    - Display probability gauge (0-100%)
    - Show identified risk factors
    - Highlight red flag keywords
    - Display mitigation tips
    - _Requirements: 6.2, 6.5_

  - [ ]* 22.5 Write unit tests for finance and logistics components
    - Test cash flow timeline rendering
    - Test RMS probability display
    - Test LCL vs FCL comparison
    - _Requirements: 5.5, 6.1, 6.2_


- [ ] 23. Implement chat interface
  - [ ] 23.1 Create ChatInterface component
    - Display chat messages in conversation format
    - Show user and assistant messages with distinct styling
    - Add message input field with send button
    - Display loading indicator during response generation
    - Show source citations with links
    - Implement auto-scroll to latest message
    - _Requirements: 7.1, 7.3, 7.7_

  - [ ] 23.2 Implement chat message handling
    - Send chat questions to backend API
    - Maintain conversation history in component state
    - Display error messages for failed requests
    - Handle session creation and management
    - _Requirements: 7.2, 7.4_

  - [ ] 23.3 Create SourceCitation component
    - Display source title and excerpt
    - Add click-to-expand functionality
    - Show relevance score
    - Add link to full source document
    - _Requirements: 7.7_

  - [ ]* 23.4 Write unit tests for chat interface
    - Test message sending and receiving
    - Test conversation history display
    - Test source citation rendering
    - _Requirements: 7.1, 7.3, 7.7_


- [ ] 24. Implement persona-specific features
  - [ ] 24.1 Create PersonaDashboard component
    - Display persona-specific widgets based on business type
    - Show relevant quick actions
    - Display progress tracking
    - _Requirements: 18.1, 18.2, 18.3, 18.4_

  - [ ] 24.2 Implement Manufacturing MSME features
    - Emphasize certification guidance (CE, FDA, REACH, BIS)
    - Show HS code mapping and ingredient/BOM analysis
    - Highlight shipment rejection prevention tips
    - Display physical product labeling requirements
    - _Requirements: 18.1_

  - [ ] 24.3 Implement SaaS exporter features
    - Emphasize SOFTEX filing guidance
    - Show payment reconciliation (Stripe, PayPal)
    - Display service classification
    - Highlight cross-border payment compliance
    - _Requirements: 18.2_

  - [ ] 24.4 Implement Merchant exporter features
    - Emphasize LCL shipment risks
    - Show RMS check probability
    - Display customs broker selection guidance
    - Highlight re-export regulations
    - _Requirements: 18.3_

  - [ ]* 24.5 Write unit tests for persona-specific features
    - Test persona detection and routing
    - Test feature visibility based on business type
    - Test persona-specific recommendations
    - _Requirements: 18.1, 18.2, 18.3_


- [ ] 25. Implement user metrics and progress tracking
  - [ ] 25.1 Create ProgressDashboard component
    - Display export readiness progress percentage
    - Show cost savings vs consultant fees
    - Display timeline to export-ready
    - Show success metrics
    - _Requirements: 19.1, 19.5_

  - [ ] 25.2 Implement metrics tracking service
    - Track report generation events
    - Track certification completion events
    - Track export success events
    - Calculate cost savings and timeline reduction
    - _Requirements: 19.1, 19.2_

  - [ ] 25.3 Create UserMetrics component
    - Display user's success metrics
    - Show reports generated count
    - Show certifications completed count
    - Display cost savings amount
    - Show timeline savings in days
    - _Requirements: 19.1_

  - [ ]* 25.4 Write unit tests for metrics tracking
    - Test metrics calculation logic
    - Test progress percentage calculation
    - Test cost savings calculation
    - _Requirements: 19.1_


- [ ] 26. Checkpoint - Frontend core functionality complete
  - Ensure all frontend components are implemented and tested
  - Verify query form accepts inputs and submits to backend
  - Verify report display shows all sections correctly
  - Verify chat interface sends and receives messages
  - Verify action plan tracks task completion
  - Run all unit tests and property tests
  - Ask the user if questions arise

- [ ] 27. Implement end-to-end integration
  - [ ] 27.1 Connect frontend to backend APIs
    - Configure API base URL in environment variables
    - Test all API endpoints from frontend
    - Handle authentication tokens
    - Implement error handling for API failures
    - _Requirements: 8.1_

  - [ ] 27.2 Implement image upload flow
    - Request presigned URL from backend
    - Upload image directly to S3
    - Pass image URL to report generation API
    - _Requirements: 1.2_

  - [ ] 27.3 Implement state persistence
    - Persist checklist completion to backend
    - Persist action plan progress to backend
    - Persist certification progress to backend
    - Sync state between localStorage and backend
    - _Requirements: 3.7, 13.4_

  - [ ]* 27.4 Write integration tests for complete flows
    - Test complete report generation flow (query → report → display)
    - Test certification guidance flow (select cert → view guidance → complete checklist)
    - Test document generation flow (select type → generate → validate → download)
    - Test chat flow (ask question → receive answer → view sources)
    - _Requirements: 1.3, 3.1, 4.1, 7.2_


- [ ] 28. Implement performance optimizations
  - [ ] 28.1 Add response time monitoring
    - Implement timing for report generation (target: <30s)
    - Implement timing for chat responses (target: <10s)
    - Implement timing for document generation (target: <5s)
    - Log slow requests for optimization
    - _Requirements: 16.2, 16.3, 16.5_

  - [ ] 28.2 Optimize frontend performance
    - Implement lazy loading for large components
    - Add pagination for large lists
    - Optimize image loading with compression
    - Implement code splitting for route-based chunks
    - _Requirements: 16.7_

  - [ ] 28.3 Optimize backend performance
    - Add caching for repeated queries
    - Optimize database queries with indexes
    - Implement connection pooling for RDS
    - Add Redis caching for session data (optional)
    - _Requirements: 16.4_

  - [ ] 28.4 Add loading indicators
    - Display loading spinners during async operations
    - Show estimated time remaining for long operations
    - Provide progress updates for report generation
    - _Requirements: 15.5, 16.6_

  - [ ]* 28.5 Write performance tests
    - Test report generation completes within 30 seconds
    - Test chat responses complete within 10 seconds
    - Test document generation completes within 5 seconds
    - _Requirements: 16.2, 16.3, 16.5_


- [ ] 29. Deploy to AWS infrastructure
  - [ ] 29.1 Set up AWS S3 for frontend hosting
    - Create S3 bucket for static website hosting
    - Configure bucket policy for public read access
    - Enable versioning for rollback capability
    - _Requirements: 12.1_

  - [ ] 29.2 Set up CloudFront distribution
    - Create CloudFront distribution with S3 origin
    - Configure HTTPS only (redirect HTTP to HTTPS)
    - Enable Gzip/Brotli compression
    - Set caching policies (1 year for assets, no cache for index.html)
    - _Requirements: 12.1_

  - [ ] 29.3 Deploy backend to EC2 or Lambda
    - Launch EC2 instance (t3.medium) or create Lambda functions
    - Install Python dependencies and FastAPI application
    - Configure Nginx reverse proxy (EC2) or API Gateway (Lambda)
    - Set up SSL certificate with Let's Encrypt or ACM
    - Configure security groups (HTTPS, SSH)
    - _Requirements: 12.2_

  - [ ] 29.4 Configure AWS RDS PostgreSQL
    - Create RDS instance (db.t3.micro or db.t3.small)
    - Enable automated backups with 7-day retention
    - Enable encryption at rest
    - Configure security group (access from backend only)
    - Run database migrations
    - _Requirements: 12.8_

  - [ ] 29.5 Set up S3 buckets for data storage
    - Create knowledge base bucket (private)
    - Create product images upload bucket (private with presigned URLs)
    - Create generated documents bucket (private)
    - Configure lifecycle policies
    - _Requirements: 12.7_

  - [ ] 29.6 Configure IAM roles and policies
    - Create EC2/Lambda execution role
    - Grant access to S3, RDS, Bedrock, Textract, Comprehend
    - Apply principle of least privilege
    - _Requirements: 12.9_

  - [ ] 29.7 Set up CloudWatch monitoring
    - Configure application logs
    - Set up metrics for CPU, memory, API latency
    - Create alarms for high error rates and latency
    - _Requirements: 12.10_

  - [ ] 29.8 Initialize knowledge base
    - Upload regulatory documents to S3 knowledge base bucket
    - Run script to generate embeddings and build FAISS index
    - Verify vector store is accessible from backend
    - _Requirements: 9.1, 9.2_

  - [ ]* 29.9 Run smoke tests on deployed application
    - Test frontend loads correctly
    - Test API endpoints are accessible
    - Test report generation end-to-end
    - Test chat functionality
    - _Requirements: 12.1, 12.2_


- [ ] 30. Final testing and quality assurance
  - [ ]* 30.1 Run complete test suite
    - Run all backend unit tests (pytest)
    - Run all backend property tests (Hypothesis, 100 iterations)
    - Run all frontend unit tests (Jest)
    - Run all frontend property tests (fast-check, 100 iterations)
    - Run integration tests
    - Generate coverage reports
    - _Requirements: All_

  - [ ]* 30.2 Perform manual testing
    - Test query submission with valid inputs
    - Test query submission with invalid inputs
    - Test report generation for different product types
    - Test certification guidance modal
    - Test document generation and validation
    - Test chat interface with multiple questions
    - Test action plan task completion
    - Test on mobile devices
    - Test in different browsers (Chrome, Firefox, Safari)
    - _Requirements: All_

  - [ ] 30.3 Verify security requirements
    - Verify HTTPS is enforced
    - Verify input sanitization prevents injection
    - Verify rate limiting works
    - Verify authentication protects routes
    - Verify data encryption at rest
    - _Requirements: 17.1, 17.2, 17.5, 17.6, 17.7_

  - [ ] 30.4 Verify performance requirements
    - Verify report generation completes within 30 seconds
    - Verify chat responses complete within 10 seconds
    - Verify document generation completes within 5 seconds
    - Verify vector store retrieves documents within 2 seconds
    - _Requirements: 16.2, 16.3, 16.4, 16.5_

  - [ ] 30.5 Verify error handling
    - Test LLM service unavailability
    - Test vector store failures
    - Test database connection errors
    - Test network timeouts
    - Verify user-friendly error messages
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 31. Final checkpoint - Production ready
  - Ensure all tests pass
  - Verify deployment is stable
  - Verify all features work end-to-end
  - Verify performance meets requirements
  - Verify security measures are in place
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases
- The implementation follows a phased approach: backend foundation → AI layer → core features → frontend → integration → deployment
- AWS services (Bedrock, Textract, Comprehend, RDS, S3) are used throughout for AI workloads and data storage
- The platform supports three user personas: Manufacturing MSMEs, SaaS exporters, and Merchant exporters
- All AI responses are grounded in retrieved regulatory documents using RAG to prevent hallucinations
