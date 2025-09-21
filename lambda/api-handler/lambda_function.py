import json
import boto3
import base64
import uuid
from datetime import datetime
import logging
import pdfplumber
import io
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

# Environment variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'AnalysisJobs')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'amazon.nova-pro-v1:0')

# DynamoDB table for storing analysis results
try:
    results_table = dynamodb.Table(DYNAMODB_TABLE_NAME)
except Exception as e:
    logger.error(f"Failed to connect to DynamoDB: {str(e)}")
    results_table = None

def lambda_handler(event, context):
    """Main Lambda handler for API Gateway requests"""
    try:
        # Parse the request
        http_method = event.get('httpMethod')
        path = event.get('path')
        
        # CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        }
        
        # Handle preflight requests
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Route requests
        if path == '/upload' and http_method == 'POST':
            return handle_upload(event, cors_headers)
        elif path.startswith('/analysis-status/') and http_method == 'GET':
            file_id = path.split('/')[-1]
            return handle_status_check(file_id, cors_headers)
        elif path == '/chat' and http_method == 'POST':
            return handle_chat(event, cors_headers)
        elif path == '/health' and http_method == 'GET':
            return handle_health_check(cors_headers)
        else:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def handle_upload(event, cors_headers):
    """Handle file upload requests"""
    try:
        # Parse the multipart form data
        content_type = event.get('headers', {}).get('content-type', '')
        if 'multipart/form-data' not in content_type:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'success': False, 'message': 'Content-Type must be multipart/form-data'})
            }
        
        # Decode base64 body
        body = event.get('body', '')
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body)
        else:
            body = body.encode('utf-8')
        
        # Parse multipart data (simplified - in production, use proper multipart parser)
        # For now, assume the file content is in the body
        file_content = body
        
        # Validate file size (10MB limit)
        if len(file_content) > 10 * 1024 * 1024:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'success': False, 'message': 'File size must be less than 10MB'})
            }
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"contract_{timestamp}.pdf"  # Default filename
        s3_key = f"pdfs/{timestamp}_{file_id}_{filename}"
        
        # Upload to S3
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType='application/pdf'
        )
        
        # Store initial status in DynamoDB
        if results_table:
            results_table.put_item(
                Item={
                    'fileId': file_id,
                    'status': 'processing',
                    'message': 'PDF uploaded, analysis in progress...',
                    'timestamp': datetime.now().isoformat(),
                    'fileName': filename,
                    's3Key': s3_key
                }
            )
        
        # Start analysis asynchronously
        analyze_document_async(file_id, s3_key, file_content)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'success': True,
                'fileId': file_id,
                'fileName': filename,
                'message': 'PDF uploaded successfully'
            })
        }
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'success': False, 'message': f'Upload failed: {str(e)}'})
        }

def handle_status_check(file_id, cors_headers):
    """Check analysis status"""
    try:
        if not results_table:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'success': False, 'message': 'Database not available'})
            }
        
        # Get status from DynamoDB
        response = results_table.get_item(Key={'fileId': file_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'success': False, 'message': 'File not found'})
            }
        
        item = response['Item']
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'success': True,
                'status': item.get('status'),
                'message': item.get('message'),
                'analysisResult': item.get('analysisResult'),
                'documentText': item.get('documentText'),
                'clausePositions': item.get('clausePositions', [])
            })
        }
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'success': False, 'message': str(e)})
        }

def handle_chat(event, cors_headers):
    """Handle chat requests"""
    try:
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', '')
        
        if not message:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'success': False, 'message': 'No message provided'})
            }
        
        # Simple chat response for now
        response_message = f"Thanks for your question: '{message}'. This is a prototype chat response."
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'success': True,
                'response': response_message,
                'message': 'Chat response generated'
            })
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'success': False, 'message': f'Chat failed: {str(e)}'})
        }

def handle_health_check(cors_headers):
    """Health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        's3_configured': S3_BUCKET_NAME is not None,
        'dynamodb_configured': results_table is not None,
        'bedrock_configured': True
    }
    
    return {
        'statusCode': 200,
        'headers': cors_headers,
        'body': json.dumps(health_status)
    }

def analyze_document_async(file_id, s3_key, file_content):
    """Analyze document with Bedrock (async)"""
    try:
        # Extract text from PDF
        document_text = extract_pdf_text(file_content)
        if not document_text:
            update_analysis_status(file_id, 'failed', 'Failed to extract text from PDF')
            return
        
        # Analyze with Bedrock
        analysis_result = analyze_with_bedrock(document_text)
        if not analysis_result:
            update_analysis_status(file_id, 'failed', 'Failed to analyze PDF')
            return
        
        # Update status with results
        update_analysis_status(
            file_id, 
            'completed', 
            'Analysis completed successfully',
            analysis_result,
            document_text
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        update_analysis_status(file_id, 'failed', f'Analysis failed: {str(e)}')

def extract_pdf_text(file_content):
    """Extract text from PDF content"""
    try:
        text = ""
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
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
    """Analyze document with Bedrock"""
    try:
        prompt = f"""You are a legal assistant specializing in rental agreements for university students. 
Analyze the following rental agreement and identify problematic clauses. 
Return your analysis in valid JSON format with the following structure:

{{
    "overall_assessment": {{
        "risk_level": "high|medium|low",
        "risk_score": 0-100,
        "summary": "Brief overall assessment"
    }},
    "dangerous_clauses": [
        {{
            "clause_id": "unique_id",
            "original_text": "exact clause text",
            "explanation": "why this is dangerous",
            "suggestion": "what to do about it",
            "legal_basis": "relevant law or regulation"
        }}
    ],
    "caution_clauses": [...],
    "normal_clauses": [...],
    "key_information": {{
        "rent_amount": "amount",
        "lease_duration": "duration",
        "deposit": "amount"
    }},
    "recommendations": ["list of general recommendations"]
}}

RENTAL AGREEMENT:
{document_text[:8000]}"""

        body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 3000,
                "temperature": 0.1
            }
        }

        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )

        result = json.loads(response['body'].read())
        completion = result.get("outputText", "")
        
        # Extract JSON from response
        start_idx = completion.find('{')
        end_idx = completion.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            return json.loads(completion[start_idx:end_idx])
        return None
        
    except Exception as e:
        logger.error(f"Bedrock analysis error: {str(e)}")
        return None

def update_analysis_status(file_id, status, message, analysis_result=None, document_text=None):
    """Update analysis status in DynamoDB"""
    try:
        if not results_table:
            return
        
        update_data = {
            'status': status,
            'message': message,
            'updatedAt': datetime.now().isoformat()
        }
        
        if analysis_result:
            update_data['analysisResult'] = analysis_result
        if document_text:
            update_data['documentText'] = document_text
            update_data['clausePositions'] = []  # TODO: Implement clause positioning
        
        results_table.update_item(
            Key={'fileId': file_id},
            UpdateExpression='SET ' + ', '.join([f'#{k} = :{k}' for k in update_data.keys()]),
            ExpressionAttributeNames={f'#{k}': k for k in update_data.keys()},
            ExpressionAttributeValues={f':{k}': v for k, v in update_data.items()}
        )
        
        logger.info(f"Updated status for {file_id}: {status}")
        
    except Exception as e:
        logger.error(f"Failed to update status: {str(e)}")
