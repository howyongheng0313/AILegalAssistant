# Praetor - Project Structure

## 📁 **Clean Project Organization**

```
praetor/
├── 📂 backend/                 # Flask API (Beanstalk)
│   ├── application.py          # Main Flask application
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # Backend environment variables
│
├── 📂 lambda/                  # AWS Lambda Functions
│   └── bedrock-analyzer/       # Document analysis function
│       ├── lambda_function.py  # Main Lambda handler
│       ├── requirements.txt    # Lambda dependencies
│       └── lambda-deployment.zip
│
├── 📂 src/                     # React Frontend (Amplify)
│   ├── App.js                  # Main React component
│   ├── App.css                 # Praetor styling
│   ├── index.js                # React entry point
│   └── index.css               # Global styles
│
├── 📂 public/                  # Static Assets
│   ├── favicon.ico             # Browser icon
│   ├── index.html              # HTML template
│   ├── manifest.json           # PWA manifest
│   └── robots.txt              # SEO configuration
│
├── 📄 package.json             # Frontend dependencies
├── 📄 .env.example             # Environment template
├── 📄 .gitignore               # Git ignore rules
├── 📄 amplify.yml              # Amplify build config
├── 📄 AWS_SETUP_GUIDE.md       # Deployment guide
└── 📄 README.md                # Project documentation
```

## 🎯 **Key Features**

- **Clean Architecture**: Separated frontend, backend, and serverless functions
- **Modern UI**: Beautiful color scheme with professional design
- **AWS Integration**: Optimized for Amplify + Beanstalk + Lambda
- **Production Ready**: Proper environment configuration and security

## 🚀 **Deployment Stack**

- **Frontend**: AWS Amplify (React)
- **Backend**: AWS Elastic Beanstalk (Flask)
- **Processing**: AWS Lambda + Bedrock Nova Pro
- **Storage**: AWS S3

## 🎨 **Color Scheme**

- **Background**: #fffffe
- **Headlines**: #272343  
- **Text**: #2d334a
- **Buttons**: #ffd803
- **Accents**: #e3f6f5, #bae8e8

---

*Praetor - Empowering university students with AI-powered legal document analysis*
