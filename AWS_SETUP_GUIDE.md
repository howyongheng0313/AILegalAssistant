# AWS Setup Guide - Legal Assistant

## 🚀 Complete AWS Infrastructure Setup

### **Step 1: Create S3 Bucket**

```bash
# In AWS Console → S3:
1. Create bucket: "legal-documents-[your-name]-2024"
2. Region: us-east-1 (recommended)
3. Block public access: Keep enabled
4. Versioning: Enable
5. Encryption: Enable (SSE-S3)
```

**Bucket Policy (Replace bucket name):**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:role/LegalAssistantLambdaRole"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::legal-documents-[your-name]-2024/*"
        }
    ]
}
```

**CORS Configuration:**
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

### **Step 2: Create IAM Role for Lambda**

```bash
# In AWS Console → IAM → Roles:
1. Create role → AWS service → Lambda
2. Role name: "LegalAssistantLambdaRole"
3. Attach policies:
```

**Custom Policy - LegalAssistantPolicy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::legal-documents-[your-name]-2024/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-v2"
        }
    ]
}
```

### **Step 3: Enable Bedrock Models**

```bash
# In AWS Console → Bedrock → Model access:
1. Request access to: "Anthropic Claude"
2. Wait for approval (usually instant)
3. Test model availability
```

### **Step 4: Create Lambda Function**

```bash
# In AWS Console → Lambda:
1. Create function → Author from scratch
2. Function name: "legal-document-analyzer"
3. Runtime: Python 3.11
4. Architecture: x86_64
5. Execution role: Use existing → LegalAssistantLambdaRole
```

**Configuration:**
- **Memory:** 1024 MB
- **Timeout:** 5 minutes
- **Environment variables:**
  ```
  BACKEND_CALLBACK_URL = https://your-backend-url.com/analysis-result
  ```

### **Step 5: Deploy Lambda Code**

```bash
# Create deployment package:
cd lambda/bedrock-analyzer
pip install -r requirements.txt -t .
zip -r lambda-deployment.zip .

# Upload via AWS Console or CLI:
aws lambda update-function-code \
    --function-name legal-document-analyzer \
    --zip-file fileb://lambda-deployment.zip
```

### **Step 6: Configure S3 Event Trigger**

```bash
# In S3 Bucket → Properties → Event notifications:
1. Create event notification
2. Name: "document-upload-trigger"
3. Prefix: "legal-documents/"
4. Event types: "s3:ObjectCreated:*"
5. Destination: Lambda function → legal-document-analyzer
```

### **Step 7: Update Backend Configuration**

Update your `backend/.env` file:
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=legal-documents-[your-name]-2024
```

### **Step 8: Create Frontend Environment**

```bash
# In project root:
cp .env.example .env

# Edit .env:
REACT_APP_BACKEND_URL=http://localhost:5000
```

## 🧪 Testing the Complete Flow

### **Test 1: Backend Connection**
```bash
cd backend
python app.py
# Should show: "🚀 Legal Assistant Backend Starting..."
```

### **Test 2: Frontend Connection**
```bash
npm start
# Should open http://localhost:3000
```

### **Test 3: S3 Upload**
```bash
# Upload a test PDF through the UI
# Check S3 bucket for file
# Check Lambda logs for execution
```

### **Test 4: End-to-End Analysis**
```bash
# Upload rental agreement PDF
# Wait for analysis (should take 30-60 seconds)
# Verify split-screen display with highlights
```

## 🔧 Troubleshooting

### **Common Issues:**

**Lambda Timeout:**
- Increase timeout to 5 minutes
- Check memory allocation (1024 MB recommended)

**Bedrock Access Denied:**
- Verify model access is enabled
- Check IAM permissions for bedrock:InvokeModel

**S3 Permissions:**
- Verify bucket policy allows Lambda role access
- Check CORS configuration for web uploads

**Backend Callback Failed:**
- Ensure backend is accessible from Lambda
- Check BACKEND_CALLBACK_URL environment variable

### **Monitoring:**

**CloudWatch Logs:**
- Lambda: `/aws/lambda/legal-document-analyzer`
- Check for errors and execution time

**S3 Events:**
- Verify events are triggering Lambda
- Check S3 access logs

## 🚀 Production Deployment

### **Backend Deployment Options:**
1. **AWS Elastic Beanstalk** (Recommended)
2. **AWS ECS with Fargate**
3. **AWS Lambda + API Gateway**

### **Frontend Deployment:**
1. **AWS S3 + CloudFront** (Static hosting)
2. **Netlify** (Easy deployment)
3. **Vercel** (Alternative)

### **Environment Variables for Production:**
```bash
# Frontend (.env):
REACT_APP_BACKEND_URL=https://your-api-domain.com

# Lambda:
BACKEND_CALLBACK_URL=https://your-api-domain.com/analysis-result
```

## 📋 Final Checklist

- [ ] S3 bucket created with proper permissions
- [ ] IAM role created with required policies  
- [ ] Bedrock models enabled and accessible
- [ ] Lambda function deployed with correct code
- [ ] S3 event trigger configured
- [ ] Backend environment variables set
- [ ] Frontend environment file created
- [ ] End-to-end test completed successfully

Your Legal Assistant is now ready to analyze rental contracts for university students! 🎓⚖️
