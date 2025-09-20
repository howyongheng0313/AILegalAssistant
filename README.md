# Legal Assistant

A React-based legal document analysis application that uses AWS services for document processing and AI analysis.

## 🎯 Features

- **Document Upload**: Support for PDF, DOC, DOCX, TXT files
- **AI Analysis**: Powered by AWS Bedrock for intelligent document review
- **Risk Assessment**: Automatic categorization of clauses by risk level
- **Real-time Status**: Live polling for analysis progress
- **Interactive Chat**: Ask questions about your analyzed documents
- **Modern UI**: Clean, responsive interface with progress indicators

## 🏗️ Architecture

```
Frontend (React) → Backend (Flask) → S3 → Lambda → Bedrock
     ↑                ↑                        ↓
     └── Polling ←── Caching ←── HTTP Callback ←┘
```

### Data Flow
1. **Upload**: Frontend → Backend → S3 storage
2. **Trigger**: S3 event → Lambda function
3. **Analysis**: Lambda → Bedrock AI processing
4. **Callback**: Lambda → Backend API endpoint
5. **Polling**: Frontend checks status every 3 seconds
6. **Display**: Results shown in categorized sections

## 📁 Project Structure

```
legal_assistant/
├── src/                    # React frontend
│   ├── App.js             # Main component with polling logic
│   ├── App.css            # Modern UI styling
│   └── index.js           # React entry point
├── backend/               # Flask API server
│   ├── app.py            # API endpoints + result caching
│   ├── requirements.txt   # Python dependencies
│   └── .env.example      # Environment template
└── lambda/               # AWS Lambda functions (to be created)
    └── bedrock-analyzer/ # Document analysis function
```

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- Python 3.8+
- AWS Account with Bedrock access

### 1. Frontend Setup
```bash
# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit REACT_APP_BACKEND_URL=http://localhost:5000

# Start development server
npm start
```

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Configure AWS credentials
cp .env.example .env
# Edit with your AWS credentials and S3 bucket name

# Start Flask server
python app.py
```

### 3. AWS Configuration (Required)
- Create S3 bucket for document storage
- Set up Lambda function for Bedrock integration
- Configure IAM roles and permissions
- Enable Bedrock models in your region

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/upload` | Upload document, returns `fileId` |
| `GET` | `/analysis-status/{fileId}` | Check analysis progress |
| `POST` | `/analysis-result` | Lambda callback endpoint |
| `POST` | `/chat` | Interactive Q&A about documents |
| `GET` | `/health` | Service health check |

## 📊 Analysis Categories

Documents are automatically categorized into:

### 🔴 High Risk Clauses
- Potentially unfair or problematic terms
- Requires immediate attention
- May need legal review

### 🟡 Caution Clauses  
- Terms requiring careful consideration
- Standard but worth noting
- May need clarification

### 🟢 Normal Clauses
- Standard acceptable terms
- No immediate concerns
- Typical industry language

## ⚙️ Configuration

### Backend Environment (.env)
```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your-legal-documents-bucket
```

### Frontend Environment (.env)
```bash
REACT_APP_BACKEND_URL=http://localhost:5000
```

## 🔧 Development Features

- **Real-time Polling**: Automatic status updates every 3 seconds
- **Progress Indicators**: Visual upload and analysis progress
- **Error Handling**: Comprehensive error messages and recovery
- **Responsive Design**: Works on desktop and mobile devices
- **File Validation**: Type and size checking before upload

## 🚦 Status Flow

1. **Idle** → Ready for document upload
2. **Uploading** → File transfer to backend/S3
3. **Processing** → Bedrock analysis in progress
4. **Completed** → Results available for viewing
5. **Failed** → Error occurred, retry available

## 🛠️ Next Steps

### Phase 1: Core Functionality ✅
- [x] File upload with validation
- [x] Backend API with S3 integration
- [x] Polling mechanism for status updates
- [x] Modern UI with progress indicators

### Phase 2: AWS Integration (In Progress)
- [ ] Lambda function for Bedrock analysis
- [ ] S3 event triggers
- [ ] IAM roles and permissions
- [ ] Bedrock model configuration

### Phase 3: Advanced Features
- [ ] User authentication
- [ ] Document history
- [ ] Export functionality
- [ ] Multi-language support

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

**Upload Issues**: Check file type/size limits and backend connectivity
**Analysis Stuck**: Verify Lambda function and Bedrock permissions
**Polling Errors**: Ensure backend is running and accessible
**AWS Errors**: Check credentials and service availability
