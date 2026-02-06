# Requirements Document: ExportSathi

## Introduction

ExportSathi is an AI-powered Export Compliance & Certification Co-Pilot designed to help Indian MSMEs (Micro, Small, and Medium Enterprises) start exporting within 7 days without hiring expensive consultants or understanding 200+ regulations. The platform addresses the critical "Liquidity-Compliance Trap" where startups fail between GST refunds, certifications, and documentation errors rather than lack of demand.

The platform acts as a comprehensive export enabler providing:
- **Compliance Brain**: Product-to-market compliance mapping with HS code prediction and certification requirements
- **Certification Navigator**: Step-by-step guidance for obtaining FDA, CE, REACH, BIS, ZED, RoDTEP and other certifications
- **Documentation Auto-Pilot**: Auto-generation and validation of commercial invoices, packing lists, shipping bills, GST LUT, SOFTEX, and certificates of origin
- **Finance Readiness Layer**: Working capital planning, pre-shipment credit eligibility, RoDTEP benefit calculation, and currency hedging advice
- **Logistics Risk Shield**: LCL risk analysis, RMS probability estimation, route delay prediction, and freight cost estimation

The platform serves three primary user personas:
1. **Manufacturing MSMEs** (first-time exporters of LED lights, textiles, toys, chemicals) who need certification guidance and shipment rejection prevention
2. **SaaS/Service Exporters** struggling with SOFTEX filings and payment reconciliation
3. **Merchant Exporters** dealing with LCL shipment risks and RMS checks

All AI responses are grounded in retrieved regulatory documents from DGFT, Customs RMS rules, FDA refusal database, EU RASFF, GSTN, and RoDTEP schedules using Retrieval-Augmented Generation (RAG) to ensure accuracy.

## Glossary

- **ExportSathi**: The AI-Powered Export Compliance & Certification Co-Pilot platform
- **MSME**: Micro, Small, and Medium Enterprise - the primary target users
- **User**: An Indian MSME exporter (manufacturing, SaaS, or merchant) seeking export guidance
- **Export_Readiness_Report**: A comprehensive document containing HS code, certifications, compliance requirements, risks, costs, timelines, and subsidies for exporting a specific product
- **HS_Code**: Harmonized System Code - international product classification code required for customs
- **Compliance_Roadmap**: Step-by-step plan showing all certifications, documents, and actions needed to become export-ready
- **Certification**: Required approvals such as FDA, CE, REACH, BIS, ZED, SOFTEX for specific products and markets
- **RAG_Pipeline**: The Retrieval-Augmented Generation system that retrieves relevant regulatory documents and generates grounded responses
- **Knowledge_Base**: Collection of DGFT rules, Customs RMS rules, FDA refusal database, EU RASFF, GSTN data, and RoDTEP schedules
- **Vector_Store**: The FAISS or ChromaDB database storing document embeddings for semantic search
- **Frontend**: The React-based web user interface
- **Backend**: The Python FastAPI server handling API requests and AI orchestration
- **LLM_Service**: AWS Bedrock or Groq API for LLM inference
- **GST_LUT**: Letter of Undertaking for GST - allows exports without paying IGST
- **RoDTEP**: Remission of Duties and Taxes on Exported Products - government refund scheme
- **SOFTEX**: Software Export declaration required for SaaS/software service exports
- **RMS**: Risk Management System - customs screening system that flags shipments for inspection
- **LCL**: Less than Container Load - partial container shipment with higher risk
- **FCL**: Full Container Load - complete container shipment with lower risk
- **BOM**: Bill of Materials - list of ingredients/components in a product
- **DGFT**: Directorate General of Foreign Trade - Indian government export authority
- **ZED**: Zero Defect Zero Effect certification scheme with 80% subsidy for micro enterprises
- **RASFF**: Rapid Alert System for Food and Feed - EU food safety alert system
- **Liquidity_Compliance_Trap**: Cash flow crisis caused by delayed GST refunds while waiting for certifications and documentation

## Requirements

### Requirement 1: Product and Destination Input with Image Upload

**User Story:** As a user, I want to input my product details (name, image, BOM, ingredients) and destination country, so that I can receive tailored export guidance with HS code prediction.

#### Acceptance Criteria

1. WHEN a user accesses ExportSathi, THE Frontend SHALL display an input form with fields for product name, product image upload, ingredients/BOM, target country, business type (Manufacturing/SaaS/Merchant), company size (Micro/Small/Medium), monthly volume, price range, and payment mode
2. WHEN a user uploads a product image, THE Backend SHALL process the image to assist with product identification and HS code prediction
3. WHEN a user submits valid product and destination inputs, THE Backend SHALL accept the query and initiate the AI Export Readiness Engine
4. THE Frontend SHALL support selection of any country worldwide as the destination
5. WHEN a user submits an empty or invalid input, THE ExportSathi SHALL prevent submission and display validation feedback
6. THE ExportSathi SHALL support all product categories (manufacturing products, SaaS/services, merchant exports) without artificial restrictions

### Requirement 2: AI Export Readiness Engine with HS Code Prediction

**User Story:** As a user, I want the AI to analyze my product and automatically predict the HS code, required certifications, restricted substances, and past rejection reasons, so that I can understand compliance requirements without expert knowledge.

#### Acceptance Criteria

1. WHEN a valid query with product details is received, THE AI Export Readiness Engine SHALL predict the HS Code with confidence percentage
2. THE AI Export Readiness Engine SHALL identify all mandatory certifications required for the product-market combination (FDA, CE, REACH, BIS, ZED, SOFTEX, etc.)
3. THE AI Export Readiness Engine SHALL identify restricted substances and ingredients that may cause rejection
4. THE AI Export Readiness Engine SHALL retrieve past rejection reasons from FDA refusal database and EU RASFF for similar products
5. THE AI Export Readiness Engine SHALL calculate estimated compliance cost and timeline
6. THE AI Export Readiness Engine SHALL generate a risk score (0-100) based on product complexity, destination regulations, and historical rejection data
7. THE Export_Readiness_Report SHALL include all sections: HS code, certifications, prohibited risks, timeline, cost, and risk score
8. IF the AI cannot confidently predict HS code or certifications, THEN THE ExportSathi SHALL request additional product information from the user

### Requirement 3: Certification Solver and Navigator

**User Story:** As a user, I want step-by-step guidance for obtaining each required certification with document checklists, test labs, consultants, subsidies, and common rejection reasons, so that I can navigate the certification process without hiring expensive consultants.

#### Acceptance Criteria

1. FOR each required certification identified in the Export_Readiness_Report, THE Certification Solver SHALL provide a detailed roadmap including: why required, steps to obtain, required documents, approved test labs, consultant options, government subsidies available, common rejection reasons, cost range, and timeline
2. THE Certification Solver SHALL generate a document checklist for each certification showing exactly what paperwork is needed
3. THE Certification Solver SHALL provide auto form filling assistance where possible to reduce manual data entry
4. THE Certification Solver SHALL connect users to a consultant marketplace where they can hire certified experts if needed
5. THE Certification Solver SHALL identify applicable subsidies (such as ZED 80% subsidy for micro enterprises) and show how to apply
6. THE Certification Solver SHALL provide mock audit questions to help users prepare before the real audit
7. WHEN a user marks a certification as in-progress or complete, THE Frontend SHALL persist the status and update the compliance roadmap
8. THE Certification Solver SHALL support certifications including but not limited to: US FDA, CE marking, REACH, BIS, ZED, RoDTEP mapping, and SOFTEX for SaaS exports

### Requirement 4: Smart Documentation Layer with Auto-Generation and Validation

**User Story:** As a user, I want the platform to auto-generate and validate all export documents (commercial invoice, packing list, shipping bill, GST LUT, SOFTEX, certificate of origin) with error checking, so that I can avoid documentation errors that cause shipment delays or GST refund rejections.

#### Acceptance Criteria

1. THE Smart Documentation Layer SHALL auto-generate the following documents based on user inputs: Commercial Invoice, Packing List, Shipping Bill, GST LUT (Letter of Undertaking), SOFTEX (for SaaS exports), and Certificate of Origin
2. WHEN generating documents, THE Smart Documentation Layer SHALL use India-specific formats and templates that comply with DGFT and customs requirements
3. THE Smart Documentation Layer SHALL perform AI validation checks including: port code mismatch detection, invoice format validation, GST vs Shipping Bill matching, and RMS risk trigger detection
4. WHEN validation errors are detected, THE ExportSathi SHALL highlight the specific errors and provide correction suggestions
5. THE Smart Documentation Layer SHALL support document download in PDF and editable formats
6. FOR SaaS exporters, THE Smart Documentation Layer SHALL generate SOFTEX declarations with proper service classification
7. THE Smart Documentation Layer SHALL validate that all mandatory fields are filled and cross-reference data consistency across documents
8. THE Smart Documentation Layer SHALL provide a GST refund rejection guard that checks for common errors before submission

### Requirement 5: Finance Readiness Module

**User Story:** As a user, I want to understand my working capital requirements, pre-shipment credit eligibility, RoDTEP benefits, and currency hedging options, so that I can plan my finances and avoid the liquidity-compliance trap.

#### Acceptance Criteria

1. THE Finance Readiness Module SHALL calculate total working capital requirements based on product cost, certification costs, logistics costs, and timeline
2. THE Finance Readiness Module SHALL assess pre-shipment credit eligibility based on company size, order value, and banking relationships
3. THE Finance Readiness Module SHALL calculate RoDTEP (Remission of Duties and Taxes on Exported Products) benefit amount based on HS code and destination
4. THE Finance Readiness Module SHALL provide currency hedging advice for foreign exchange risk management
5. THE Finance Readiness Module SHALL generate a cash-flow timeline showing when expenses occur and when refunds/payments are expected
6. THE Finance Readiness Module SHALL identify the liquidity gap period and suggest financing options
7. THE Finance Readiness Module SHALL connect users to bank referral programs for export financing
8. THE Finance Readiness Module SHALL estimate GST refund timeline and amount

### Requirement 6: Logistics Risk Shield

**User Story:** As a user, I want to understand logistics risks including LCL vs FCL decisions, RMS probability, route delays, and freight costs, so that I can make informed shipping decisions and avoid costly mistakes.

#### Acceptance Criteria

1. THE Logistics Risk Shield SHALL analyze LCL (Less than Container Load) vs FCL (Full Container Load) risks based on shipment volume and provide recommendations
2. THE Logistics Risk Shield SHALL estimate RMS (Risk Management System) probability - the likelihood that customs will flag the shipment for physical inspection
3. THE Logistics Risk Shield SHALL predict route delays based on current geopolitical situations (e.g., Red Sea route disruptions) and seasonal factors
4. THE Logistics Risk Shield SHALL provide freight cost estimates for different shipping options
5. THE Logistics Risk Shield SHALL identify red flag keywords in product descriptions that may trigger RMS checks
6. THE Logistics Risk Shield SHALL recommend insurance coverage based on shipment value and risk level
7. THE Logistics Risk Shield SHALL estimate transit time for different routes and carriers
8. THE Logistics Risk Shield SHALL warn about port-specific requirements and restrictions

### Requirement 7: Interactive Chat Q&A with Context

**User Story:** As a user, I want to ask follow-up questions about my export requirements with the AI maintaining context of my product and situation, so that I can clarify specific concerns without repeating information.

#### Acceptance Criteria

1. WHEN an Export_Readiness_Report is displayed, THE Frontend SHALL provide a chat interface for follow-up questions
2. WHEN a user submits a chat question, THE Backend SHALL process it through the RAG_Pipeline with context from the original query (product, destination, certifications, etc.)
3. WHEN a chat response is generated, THE Frontend SHALL display it in the chat interface while maintaining conversation history
4. THE ExportSathi SHALL maintain conversation context across multiple questions within the same session
5. WHEN a user starts a new query, THE ExportSathi SHALL clear previous conversation history and start a new session
6. THE Chat interface SHALL support questions about certifications, documentation, costs, timelines, subsidies, and logistics
7. THE Chat SHALL provide source citations from DGFT, customs rules, or other regulatory documents when answering questions

**User Story:** As a developer, I want a well-defined REST API, so that the frontend and backend can communicate reliably.

#### Acceptance Criteria

1. THE Backend SHALL expose a REST API endpoint for submitting product and destination queries
2. THE Backend SHALL expose a REST API endpoint for submitting chat questions
3. THE Backend SHALL expose a REST API endpoint for requesting Acquisition_Guidance for specific checklist items
4. THE Backend SHALL expose a REST API endpoint for retrieving report generation status
5. WHEN an API request is received, THE Backend SHALL validate the request format and parameters
6. WHEN an API request is invalid, THE Backend SHALL return an appropriate HTTP error code and error message
7. THE Backend SHALL return responses in JSON format with consistent structure

### Requirement 8: Knowledge Base with Regulatory Data Sources

**User Story:** As a system administrator, I want to store and manage export regulations from DGFT, Customs RMS rules, FDA refusal database, EU RASFF, GSTN, and RoDTEP schedules, so that the platform has accurate and up-to-date information to retrieve.

#### Acceptance Criteria

1. THE Knowledge_Base SHALL store documents from the following sources: DGFT (Directorate General of Foreign Trade) regulations, Customs RMS (Risk Management System) rules, FDA refusal database, EU RASFF (Rapid Alert System for Food and Feed), GSTN (GST Network) data, and RoDTEP schedules
2. WHEN documents are added to the Knowledge_Base, THE ExportSathi SHALL generate embeddings and store them in the Vector_Store
3. THE Vector_Store SHALL support semantic search using embedding similarity
4. THE ExportSathi SHALL use either FAISS or ChromaDB as the Vector_Store implementation
5. THE Knowledge_Base SHALL be queryable by the RAG_Pipeline during report generation, certification guidance, and chat interactions
6. THE Knowledge_Base SHALL support periodic updates to reflect changes in regulations and trade policies
7. THE Knowledge_Base SHALL tag documents with metadata including source, country, product category, and last updated date

**User Story:** As a user, I want AI-generated reports to be well-structured and easy to understand, so that I can quickly identify action items.

#### Acceptance Criteria

1. THE Backend SHALL use the Groq_API for all LLM inference operations
2. WHEN generating an Export_Readiness_Report, THE Backend SHALL request structured output with sections for checklist items, risks, and timelines
3. THE Backend SHALL provide prompt templates to the Groq_API that enforce structured response formats
4. WHEN the Groq_API returns a response, THE Backend SHALL validate the structure before sending to the Frontend
5. IF the Groq_API response is malformed, THEN THE Backend SHALL retry with a refined prompt or return an error

### Requirement 9: Document Retrieval and Grounding with RAG Pipeline

**User Story:** As a user, I want all AI responses to be based on actual regulatory documents from trusted sources, so that I receive accurate and trustworthy information without hallucinations.

#### Acceptance Criteria

1. WHEN a query is processed, THE RAG_Pipeline SHALL convert the query into an embedding vector
2. WHEN an embedding is created, THE Vector_Store SHALL return the most semantically similar documents from the Knowledge_Base
3. THE RAG_Pipeline SHALL provide Retrieved_Documents as context to the LLM for response generation
4. THE Backend SHALL ensure all generated responses reference the Retrieved_Documents and include source citations
5. WHEN no relevant documents are found, THE ExportSathi SHALL inform the user that information is unavailable rather than generating unsupported content
6. THE RAG_Pipeline SHALL prioritize documents from official government sources (DGFT, Customs) over third-party sources
7. THE RAG_Pipeline SHALL retrieve documents specific to the user's product category and destination country when available

**User Story:** As a developer, I want to deploy the platform using AWS free tier services, so that the project remains cost-effective for a hackathon.

#### Acceptance Criteria

1. THE ExportSaathi SHALL be deployable on AWS free tier services only
2. THE Frontend SHALL be hosted on AWS Amplify or S3 with CloudFront
3. THE Backend SHALL be hosted on AWS EC2 free tier instances
4. THE Knowledge_Base documents SHALL be stored in AWS S3
5. THE ExportSaathi SHALL NOT use AWS SageMaker or AWS Bedrock services
6. THE ExportSaathi SHALL use AWS security groups and IAM roles for access control

### Requirement 10: API Structure and Communication

**User Story:** As a developer, I want a well-defined REST API, so that the frontend and backend can communicate reliably and support all platform features.

#### Acceptance Criteria

1. THE Backend SHALL expose REST API endpoints for: submitting product queries with image upload, generating export readiness reports, requesting certification guidance, auto-generating documents, calculating finance readiness, analyzing logistics risks, submitting chat questions, and retrieving report status
2. THE Backend SHALL validate all API request formats and parameters
3. WHEN an API request is invalid, THE Backend SHALL return an appropriate HTTP error code (400, 422) and error message
4. THE Backend SHALL return responses in JSON format with consistent structure
5. THE Backend SHALL support file upload endpoints for product images and BOM documents
6. THE Backend SHALL implement proper error handling for all endpoints
7. THE API SHALL support pagination for list endpoints (e.g., certification list, document list)

**User Story:** As a user, I want clear communication about what the platform does and does not provide, so that I have appropriate expectations.

#### Acceptance Criteria

1. THE ExportSaathi SHALL support queries for exporting from India to any country worldwide
2. THE ExportSaathi SHALL only support one product category (agricultural products or SaaS) in the initial version
3. THE Frontend SHALL clearly communicate that ExportSaathi provides guidance only and does not issue certificates, approvals, or financing
4. WHEN a user attempts to query outside the supported product category, THE ExportSaathi SHALL display a clear message explaining the limitation

### Requirement 11: LLM Integration and Structured Outputs

**User Story:** As a user, I want AI-generated reports to be well-structured and easy to understand, so that I can quickly identify action items and make decisions.

#### Acceptance Criteria

1. THE Backend SHALL use AWS Bedrock or Groq API for all LLM inference operations
2. WHEN generating an Export_Readiness_Report, THE Backend SHALL request structured output with sections for: HS code prediction, certifications, compliance roadmap, risks, timeline, costs, subsidies, and risk score
3. THE Backend SHALL provide prompt templates to the LLM that enforce structured response formats following the ExportSathi master prompt guidelines
4. WHEN the LLM returns a response, THE Backend SHALL validate the structure before sending to the Frontend
5. IF the LLM response is malformed, THEN THE Backend SHALL retry with a refined prompt or return an error
6. THE LLM prompts SHALL include guardrails to: use Indian regulations only, not give illegal avoidance advice, highlight safety and quality first, warn about food/medical risks, and ask for missing information when needed
7. THE LLM SHALL behave as a DGFT consultant, customs broker, GST refund expert, certification navigator, logistics risk analyst, and finance advisor

**User Story:** As a user, I want clear feedback when errors occur, so that I understand what went wrong and how to proceed.

#### Acceptance Criteria

1. WHEN the Groq_API is unavailable, THE ExportSaathi SHALL display an error message and suggest retrying later
2. WHEN the Vector_Store fails to retrieve documents, THE ExportSaathi SHALL log the error and inform the user
3. WHEN the Backend encounters an unexpected error, THE ExportSaathi SHALL display a generic error message without exposing technical details
4. THE ExportSaathi SHALL log all errors with sufficient detail for debugging
5. WHEN an operation is in progress, THE Frontend SHALL display loading indicators to inform the user

### Requirement 12: AWS Infrastructure Deployment

**User Story:** As a developer, I want to deploy the platform using AWS services optimized for AI workloads, so that the platform is scalable, reliable, and cost-effective.

#### Acceptance Criteria

1. THE Frontend SHALL be hosted on AWS Amplify or S3 with CloudFront for global content delivery
2. THE Backend SHALL be hosted on AWS EC2 instances or AWS Lambda for serverless deployment
3. THE Backend SHALL use AWS Bedrock for LLM inference (Claude, Llama, or Mixtral models)
4. THE Backend SHALL use AWS Textract for invoice reading and document extraction from uploaded images
5. THE Backend SHALL use AWS Comprehend for compliance text extraction from regulatory documents
6. THE Backend MAY use AWS SageMaker for custom risk prediction models
7. THE Knowledge_Base documents SHALL be stored in AWS S3 with versioning enabled
8. THE Backend SHALL use AWS RDS (PostgreSQL or MySQL) for storing user data, reports, and session information
9. THE ExportSathi SHALL use AWS security groups and IAM roles for access control
10. THE ExportSathi SHALL implement AWS CloudWatch for logging and monitoring

**User Story:** As a user, I want the platform to respond quickly, so that I can efficiently gather export information.

#### Acceptance Criteria

1. WHEN a query is submitted, THE ExportSaathi SHALL acknowledge receipt within 1 second
2. WHEN generating an Export_Readiness_Report, THE ExportSaathi SHALL complete processing within 30 seconds under normal conditions
3. WHEN processing a chat question, THE ExportSaathi SHALL return a response within 10 seconds under normal conditions
4. THE Vector_Store SHALL return retrieved documents within 2 seconds for typical queries
5. IF processing exceeds expected time limits, THE ExportSaathi SHALL inform the user of the delay

### Requirement 13: 7-Day Export Readiness Action Plan

**User Story:** As a user, I want a day-by-day action plan that guides me to become export-ready within 7 days, so that I can start exporting quickly without getting overwhelmed.

#### Acceptance Criteria

1. WHEN an Export_Readiness_Report is generated, THE ExportSathi SHALL include a 7-day action plan with specific tasks for each day
2. THE 7-Day Action Plan SHALL prioritize tasks based on dependencies (e.g., GST LUT before first shipment, critical certifications before optional ones)
3. THE 7-Day Action Plan SHALL include tasks such as: Day 1 - GST LUT application and HS code confirmation, Day 2-3 - Critical certification applications, Day 4-5 - Document preparation, Day 6 - Logistics planning, Day 7 - Final review and readiness check
4. WHEN a user completes a task, THE Frontend SHALL allow marking it as done and show progress percentage
5. THE 7-Day Action Plan SHALL be realistic and account for government processing times
6. IF certain certifications require more than 7 days, THE Action Plan SHALL clearly indicate this and provide interim steps
7. THE 7-Day Action Plan SHALL be downloadable as a PDF checklist

### Requirement 14: Revenue Model and Monetization

**User Story:** As a platform operator, I want to generate revenue through SaaS subscriptions, per-certification fees, success fees, marketplace commissions, and finance lead referrals, so that the platform is financially sustainable.

#### Acceptance Criteria

1. THE ExportSathi SHALL offer SaaS subscription tiers priced at ₹999, ₹1999, and ₹2999 per month with different feature access levels
2. THE ExportSathi SHALL charge per-certification fees ranging from ₹5,000 to ₹25,000 for premium certification assistance services
3. THE ExportSathi SHALL charge a 1% success fee on completed export orders for users who opt into the premium success-based pricing model
4. THE ExportSathi SHALL operate a marketplace connecting users with test labs, consultants, and customs house agents (CHAs) and earn commission on transactions
5. THE ExportSathi SHALL earn referral fees from banks and financial institutions for connecting users to export financing products
6. THE Frontend SHALL clearly display pricing information and allow users to upgrade their subscription tier
7. THE Backend SHALL track usage metrics to enforce subscription tier limits (e.g., number of reports per month, number of certifications)

### Requirement 15: Error Handling and User Feedback

**User Story:** As a user, I want clear feedback when errors occur, so that I understand what went wrong and how to proceed.

#### Acceptance Criteria

1. WHEN the LLM service (AWS Bedrock or Groq API) is unavailable, THE ExportSathi SHALL display an error message and suggest retrying later
2. WHEN the Vector_Store fails to retrieve documents, THE ExportSathi SHALL log the error and inform the user
3. WHEN the Backend encounters an unexpected error, THE ExportSathi SHALL display a generic error message without exposing technical details
4. THE ExportSathi SHALL log all errors with sufficient detail for debugging including timestamp, user context, and stack trace
5. WHEN an operation is in progress (report generation, document creation, certification analysis), THE Frontend SHALL display loading indicators with estimated time remaining
6. WHEN image upload or processing fails, THE ExportSathi SHALL provide clear error messages and allow retry
7. WHEN HS code prediction confidence is low, THE ExportSathi SHALL warn the user and suggest manual verification

### Requirement 16: Performance and Response Time

**User Story:** As a user, I want the platform to respond quickly, so that I can efficiently gather export information and make decisions.

#### Acceptance Criteria

1. WHEN a query is submitted, THE ExportSathi SHALL acknowledge receipt within 1 second
2. WHEN generating an Export_Readiness_Report with HS code prediction and certification analysis, THE ExportSathi SHALL complete processing within 30 seconds under normal conditions
3. WHEN processing a chat question, THE ExportSathi SHALL return a response within 10 seconds under normal conditions
4. THE Vector_Store SHALL return retrieved documents within 2 seconds for typical queries
5. WHEN generating documents (invoice, packing list, etc.), THE ExportSathi SHALL complete generation within 5 seconds
6. IF processing exceeds expected time limits, THE ExportSathi SHALL inform the user of the delay and provide progress updates
7. THE Frontend SHALL implement lazy loading and pagination for large lists to maintain responsiveness

### Requirement 17: Data Privacy and Security

**User Story:** As a user, I want my queries, product information, and business data to be handled securely, so that my confidential business information remains protected.

#### Acceptance Criteria

1. THE ExportSathi SHALL use HTTPS for all client-server communication
2. THE Backend SHALL encrypt sensitive data at rest including product details, BOM, pricing, and business information
3. THE Backend SHALL not store user queries permanently unless explicitly configured for analytics with user consent
4. THE ExportSathi SHALL not share user data with third parties except AWS services for processing and LLM inference
5. THE Backend SHALL implement rate limiting to prevent abuse (e.g., 100 requests per hour per user)
6. THE ExportSathi SHALL validate and sanitize all user inputs including text, images, and file uploads to prevent injection attacks
7. THE Backend SHALL implement authentication and authorization for user accounts
8. THE ExportSathi SHALL comply with Indian data protection regulations and provide users with data export and deletion options

### Requirement 18: User Personas and Targeted Features

**User Story:** As a platform designer, I want to provide persona-specific features for Manufacturing MSMEs, SaaS exporters, and Merchant exporters, so that each user type gets relevant guidance.

#### Acceptance Criteria

1. FOR Manufacturing MSME users, THE ExportSathi SHALL emphasize certification guidance (CE, FDA, REACH, BIS), HS code mapping, ingredient/BOM analysis, shipment rejection prevention, and physical product labeling requirements
2. FOR SaaS/Service exporter users, THE ExportSathi SHALL emphasize SOFTEX filing, payment reconciliation (Stripe, PayPal), service classification, GST on digital services, and cross-border payment compliance
3. FOR Merchant exporter users, THE ExportSathi SHALL emphasize LCL shipment risks, RMS check probability, customs broker selection, and re-export regulations
4. THE Frontend SHALL allow users to select their business type during onboarding (Manufacturing/SaaS/Merchant)
5. THE AI Export Readiness Engine SHALL tailor recommendations based on the selected business type
6. THE Certification Solver SHALL prioritize certifications relevant to the user's business type
7. THE Documentation Layer SHALL generate documents appropriate for the business type (e.g., SOFTEX for SaaS, detailed packing lists for manufacturing)

### Requirement 19: Success Metrics and Platform Goals

**User Story:** As a platform operator, I want to track key success metrics that demonstrate the platform's value in reducing costs, accelerating timelines, and preventing failures.

#### Acceptance Criteria

1. THE ExportSathi SHALL track and display to users: percentage reduction in consultant costs (target: 80%), percentage reduction in certification timeline (target: 60%), GST refund rejection prevention rate, shipment rejection prevention rate, and number of successful first-time exports
2. THE Backend SHALL collect anonymized aggregate metrics for platform improvement including: most common product categories, most requested certifications, most frequent errors, and average time to export readiness
3. THE ExportSathi SHALL display success stories and case studies on the platform showing real MSMEs who successfully exported using the platform
4. THE Backend SHALL track user journey completion rates (how many users complete the 7-day action plan)
5. THE ExportSathi SHALL provide users with a personalized dashboard showing their progress metrics and cost savings
6. THE Platform SHALL aim to help users achieve: 80% reduction in consultant costs, 60% faster certification, prevention of GST rejection errors, and zero shipment refusals due to documentation errors

**User Story:** As a user, I want my queries and data to be handled securely, so that my business information remains confidential.

#### Acceptance Criteria

1. THE ExportSaathi SHALL use HTTPS for all client-server communication
2. THE Backend SHALL not store user queries permanently unless explicitly configured for analytics
3. THE ExportSaathi SHALL not share user data with third parties except the Groq_API for processing
4. THE Backend SHALL implement rate limiting to prevent abuse
5. THE ExportSaathi SHALL validate and sanitize all user inputs to prevent injection attacks
