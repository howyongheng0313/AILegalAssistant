import json
import boto3
import os
import requests
import logging
import pdfplumber
import io

# Simple logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')

# Environment variables
BACKEND_CALLBACK_URL = os.environ.get('BACKEND_CALLBACK_URL', 'http://10.112.80.120:5000/analysis-result')

def lambda_handler(event, context):
    """Simple PDF analysis function"""
    try:
        logger.info("Processing PDF upload event")
        
        # Parse S3 event
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            logger.info(f"Processing PDF: {key}")
            
            # Extract file ID from S3 key (format: pdfs/{timestamp}_{fileId}_{filename})
            file_id = key.split('_')[1] if '_' in key else None
            
            if not file_id:
                logger.error(f"Could not extract file ID from: {key}")
                continue
            
            # Extract text from PDF
            document_text = extract_pdf_text(bucket, key)
            
            if not document_text:
                send_error_callback(file_id, "Failed to extract text from PDF")
                continue
            
            # Simple analysis with Bedrock
            analysis_result = analyze_with_bedrock(document_text)
            
            if not analysis_result:
                send_error_callback(file_id, "Failed to analyze PDF")
                continue
            
            # Send results back
            send_success_callback(file_id, analysis_result, document_text)
            
        return {'statusCode': 200, 'body': json.dumps({'message': 'PDF processed'})}
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

def extract_file_id(s3_key):
    """Extract file ID from S3 key: pdfs/{timestamp}_{fileId}_{filename}"""
    try:
        filename = s3_key.split('/')[-1]  # Get filename part
        parts = filename.split('_')       # Split by underscore
        return parts[1] if len(parts) >= 3 else None
    except:
        return None

def extract_pdf_text(bucket, key):
    """Extract text from PDF using simple method"""
    try:
        import pdfplumber
        import io
        
        # Download PDF from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        pdf_content = response['Body'].read()
        
        # Extract text
        text = ""
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text.strip()
        
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        return None

def analyze_with_bedrock(document_text):
    """Simple Bedrock analysis for rental contracts"""
    try:
        prompt = f"""
Analyze this rental agreement for university students. Identify problematic clauses.

Return JSON format:
{{
  "overall_assessment": {{
    "risk_level": "high|medium|low",
    "risk_score": 75,
    "summary": "Brief assessment"
  }},
  "dangerous_clauses": [
    {{
      "clause_id": "clause_1",
      "original_text": "Exact text from document",
      "explanation": "Why this is problematic",
      "suggestion": "How to address it"
    }}
  ],
  "caution_clauses": [],
  "normal_clauses": [],
  "recommendations": ["Advice for student"]
}}

RENTAL AGREEMENT:
{document_text[:8000]}
"""
        
        # Call Bedrock
        body = {
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": 3000,
            "temperature": 0.1
        }
        
        response = bedrock.invoke_model(
            modelId="anthropic.claude-v2",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        completion = response_body.get('completion', '')
        
        # Parse JSON from response
        start_idx = completion.find('{')
        end_idx = completion.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = completion[start_idx:end_idx]
            return json.loads(json_str)
        
        return None
        
    except Exception as e:
        logger.error(f"Bedrock analysis error: {str(e)}")
        return None

def send_success_callback(file_id, analysis_result, document_text):
    """Send results to backend"""
    try:
        payload = {
            'fileId': file_id,
            'analysisResult': analysis_result,
            'documentText': document_text,
            'clausePositions': []  # Simple version - no highlighting yet
        }
        
        response = requests.post(BACKEND_CALLBACK_URL, json=payload, timeout=30)
        logger.info(f"Sent results for {file_id}: {response.status_code}")
        
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")

def send_error_callback(file_id, error_message):
    """Send error to backend"""
    try:
        payload = {'fileId': file_id, 'error': error_message, 'status': 'failed'}
        requests.post(BACKEND_CALLBACK_URL, json=payload, timeout=30)
        logger.info(f"Sent error for {file_id}: {error_message}")
    except Exception as e:
        logger.error(f"Error callback failed: {str(e)}")
