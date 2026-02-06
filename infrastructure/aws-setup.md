# AWS Infrastructure Setup Guide for ExportSathi

This guide provides step-by-step instructions for setting up the AWS infrastructure required for ExportSathi.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Terraform (optional, for infrastructure as code)

## Required AWS Services

### 1. AWS RDS PostgreSQL Database

**Purpose**: Store user data, reports, certifications, documents, and analytics

**Setup Steps**:

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier exportsathi-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username exportsathi_admin \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20 \
  --storage-type gp2 \
  --vpc-security-group-ids sg-XXXXXXXXX \
  --db-subnet-group-name default \
  --backup-retention-period 7 \
  --publicly-accessible false \
  --multi-az false
```

**Configuration**:
- Instance Class: db.t3.micro (free tier eligible)
- Storage: 20 GB General Purpose SSD
- Engine: PostgreSQL 15.4
- Backup: 7 days retention
- Multi-AZ: Disabled (for cost savings)

**Post-Setup**:
1. Note the endpoint URL
2. Update DATABASE_URL in backend/.env
3. Run schema.sql to create tables

### 2. AWS S3 Buckets

**Purpose**: Store knowledge base documents, product images, and generated documents

**Setup Steps**:

```bash
# Create knowledge base bucket
aws s3 mb s3://exportsathi-knowledge-base --region us-east-1

# Create product images bucket
aws s3 mb s3://exportsathi-product-images --region us-east-1

# Create generated documents bucket
aws s3 mb s3://exportsathi-generated-docs --region us-east-1

# Enable versioning on knowledge base bucket
aws s3api put-bucket-versioning \
  --bucket exportsathi-knowledge-base \
  --versioning-configuration Status=Enabled

# Set lifecycle policy for product images (delete after 90 days)
aws s3api put-bucket-lifecycle-configuration \
  --bucket exportsathi-product-images \
  --lifecycle-configuration file://s3-lifecycle-policy.json
```

**Bucket Policies**:
- Knowledge Base: Private, read access for backend
- Product Images: Private, temporary signed URLs for upload/download
- Generated Docs: Private, temporary signed URLs for download

**CORS Configuration** (for product images bucket):
```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["http://localhost:3000", "https://yourdomain.com"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

### 3. AWS Bedrock

**Purpose**: LLM inference for report generation, chat, and AI features

**Setup Steps**:

1. Enable AWS Bedrock in your region (us-east-1 recommended)
2. Request model access:
   - Anthropic Claude 3 Sonnet
   - Meta Llama 3
   - Mistral Mixtral 8x7B

```bash
# Check available models
aws bedrock list-foundation-models --region us-east-1

# Request model access (via AWS Console)
# Go to AWS Bedrock > Model access > Request access
```

**Recommended Models**:
- Primary: `anthropic.claude-3-sonnet-20240229-v1:0`
- Alternative: `meta.llama3-70b-instruct-v1:0`
- Budget: `mistral.mixtral-8x7b-instruct-v0:1`

**Pricing** (as of 2024):
- Claude 3 Sonnet: $3/1M input tokens, $15/1M output tokens
- Llama 3 70B: $0.99/1M input tokens, $2.65/1M output tokens

### 4. AWS Textract

**Purpose**: Extract text and features from product images

**Setup Steps**:

No setup required - service is available by default with AWS account.

**Usage**:
```python
import boto3

textract = boto3.client('textract', region_name='us-east-1')
response = textract.detect_document_text(
    Document={'S3Object': {'Bucket': 'bucket', 'Name': 'image.jpg'}}
)
```

**Pricing**:
- Detect Document Text: $1.50 per 1,000 pages
- Analyze Document: $50 per 1,000 pages

### 5. AWS Comprehend

**Purpose**: Compliance text analysis and entity extraction

**Setup Steps**:

No setup required - service is available by default with AWS account.

**Usage**:
```python
import boto3

comprehend = boto3.client('comprehend', region_name='us-east-1')
response = comprehend.detect_entities(
    Text='Your compliance text',
    LanguageCode='en'
)
```

**Pricing**:
- Entity Detection: $0.0001 per unit (100 characters)
- Key Phrase Extraction: $0.0001 per unit

### 6. IAM Roles and Policies

**Purpose**: Secure access control for AWS services

**Backend Service Role**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::exportsathi-knowledge-base/*",
        "arn:aws:s3:::exportsathi-product-images/*",
        "arn:aws:s3:::exportsathi-generated-docs/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::exportsathi-knowledge-base",
        "arn:aws:s3:::exportsathi-product-images",
        "arn:aws:s3:::exportsathi-generated-docs"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*:*:foundation-model/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText",
        "textract:AnalyzeDocument"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "comprehend:DetectEntities",
        "comprehend:DetectKeyPhrases"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:Connect"
      ],
      "Resource": "arn:aws:rds:*:*:db:exportsathi-db"
    }
  ]
}
```

**Create IAM Role**:
```bash
aws iam create-role \
  --role-name ExportSathiBackendRole \
  --assume-role-policy-document file://trust-policy.json

aws iam put-role-policy \
  --role-name ExportSathiBackendRole \
  --policy-name ExportSathiBackendPolicy \
  --policy-document file://backend-policy.json
```

### 7. Security Groups

**RDS Security Group**:
```bash
# Create security group for RDS
aws ec2 create-security-group \
  --group-name exportsathi-rds-sg \
  --description "Security group for ExportSathi RDS" \
  --vpc-id vpc-XXXXXXXXX

# Allow PostgreSQL access from backend EC2 instances
aws ec2 authorize-security-group-ingress \
  --group-id sg-XXXXXXXXX \
  --protocol tcp \
  --port 5432 \
  --source-group sg-BACKEND-SG-ID
```

**Backend EC2 Security Group**:
```bash
# Create security group for backend
aws ec2 create-security-group \
  --group-name exportsathi-backend-sg \
  --description "Security group for ExportSathi backend" \
  --vpc-id vpc-XXXXXXXXX

# Allow HTTP/HTTPS
aws ec2 authorize-security-group-ingress \
  --group-id sg-XXXXXXXXX \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-XXXXXXXXX \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Allow SSH (for management)
aws ec2 authorize-security-group-ingress \
  --group-id sg-XXXXXXXXX \
  --protocol tcp \
  --port 22 \
  --cidr YOUR-IP/32
```

### 8. CloudWatch Logging

**Purpose**: Monitor application logs and metrics

**Setup Steps**:

```bash
# Create log group
aws logs create-log-group \
  --log-group-name /exportsathi/backend

# Set retention policy (30 days)
aws logs put-retention-policy \
  --log-group-name /exportsathi/backend \
  --retention-in-days 30
```

**Backend Configuration**:
```python
import watchtower
import logging

logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler(
    log_group='/exportsathi/backend',
    stream_name='application'
))
```

## Environment Variables

After setting up AWS services, update your backend/.env file:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# AWS Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# AWS S3
S3_KNOWLEDGE_BASE_BUCKET=exportsathi-knowledge-base
S3_PRODUCT_IMAGES_BUCKET=exportsathi-product-images
S3_GENERATED_DOCS_BUCKET=exportsathi-generated-docs

# AWS RDS
DATABASE_URL=postgresql://exportsathi_admin:password@exportsathi-db.xxxxx.us-east-1.rds.amazonaws.com:5432/exportsathi
```

## Cost Estimation

**Monthly Costs** (estimated for moderate usage):

- RDS db.t3.micro: $15-20/month
- S3 Storage (50 GB): $1-2/month
- Bedrock (10K requests): $50-100/month
- Textract (1K images): $1.50/month
- Comprehend (100K units): $10/month
- Data Transfer: $5-10/month

**Total**: ~$80-150/month

## Security Best Practices

1. **Never commit AWS credentials** to version control
2. **Use IAM roles** instead of access keys when possible
3. **Enable MFA** on AWS root account
4. **Rotate credentials** regularly
5. **Use VPC** for RDS and EC2 instances
6. **Enable encryption** at rest for S3 and RDS
7. **Use HTTPS** for all API communication
8. **Implement rate limiting** to prevent abuse
9. **Monitor CloudWatch** for unusual activity
10. **Regular security audits** using AWS Security Hub

## Deployment Checklist

- [ ] RDS PostgreSQL instance created and accessible
- [ ] Database schema applied (schema.sql)
- [ ] S3 buckets created with proper policies
- [ ] Bedrock model access granted
- [ ] IAM roles and policies configured
- [ ] Security groups configured
- [ ] CloudWatch logging enabled
- [ ] Environment variables configured
- [ ] Backend can connect to RDS
- [ ] Backend can access S3 buckets
- [ ] Backend can invoke Bedrock models
- [ ] Textract and Comprehend accessible

## Troubleshooting

**Cannot connect to RDS**:
- Check security group allows inbound on port 5432
- Verify VPC and subnet configuration
- Check RDS instance is in "available" state

**Bedrock access denied**:
- Verify model access has been granted in AWS Console
- Check IAM role has bedrock:InvokeModel permission
- Ensure using correct model ID

**S3 access denied**:
- Verify IAM role has s3:GetObject and s3:PutObject permissions
- Check bucket policy allows access
- Ensure bucket names are correct in environment variables

## Next Steps

After completing AWS setup:
1. Initialize database with schema.sql
2. Upload knowledge base documents to S3
3. Test backend connectivity to all AWS services
4. Deploy backend application
5. Configure frontend to point to backend API
