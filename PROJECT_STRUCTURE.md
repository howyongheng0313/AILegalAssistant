# 🏗️ Legal Assistant - API Gateway Architecture

## 📁 Project Structure (Cleaned)

```
legal_assistant/
├── 📁 src/                          # React Frontend
│   ├── App.js                       # Main React component
│   ├── App.css                      # Styling
│   ├── index.js                     # React entry point
│   └── index.css                    # Global styles
├── 📁 public/                       # Static assets
│   ├── index.html                   # HTML template
│   ├── favicon.ico                  # App icon
│   ├── manifest.json                # PWA manifest
│   └── robots.txt                   # SEO robots file
├── 📁 lambda/                       # AWS Lambda Functions
│   └── 📁 api-handler/              # Main API Lambda (replaces Flask backend)
│       ├── lambda_function.py       # Combined backend + analysis logic
│       └── requirements.txt         # Python dependencies
├── 📄 package.json                  # React dependencies
├── 📄 package-lock.json             # Dependency lock file
├── 📄 .env.example                  # Environment variables template
├── 📄 .env                          # Local environment variables
└── 📄 .gitignore                    # Git ignore rules
```

## 🗑️ Removed Files (No Longer Needed)

- ❌ `backend/` folder - Replaced by Lambda function
- ❌ `lambda/bedrock-analyzer/` - Merged into api-handler

## 🚀 New Architecture Benefits

### Before (Complex)
```
React → Elastic Beanstalk (Flask) → S3 → Lambda → Bedrock
```

### After (Simple)
```
React → API Gateway → Lambda → S3/DynamoDB/Bedrock
```

## 📦 Deployment Package

For AWS deployment, you only need to zip:
- `lambda/api-handler/` folder → Upload to Lambda
- Frontend code → Deploy to Amplify

## 🔧 Environment Variables Needed

### Lambda Function
- `S3_BUCKET_NAME`: Your S3 bucket name
- `DYNAMODB_TABLE_NAME`: `legal-assistant-results`
- `BEDROCK_MODEL_ID`: `amazon.nova-pro-v1:0`

### React Frontend (Amplify)
- `REACT_APP_BACKEND_URL`: Your API Gateway URL

## ✅ Ready for Deployment

The project is now cleaned and ready for the simplified API Gateway architecture!
