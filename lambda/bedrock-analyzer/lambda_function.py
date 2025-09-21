import json
import boto3
import os
import requests
import logging
import pdfplumber
import io

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')

# Keep default value here, set public address in lambda environmental variable
BACKEND_CALLBACK_URL = os.environ.get('BACKEND_CALLBACK_URL')

def lambda_handler(event, context):
    try:
        if not BACKEND_CALLBACK_URL:
            logger.error("Environment variable BACKEND_CALLBACK_URL not set.")
            return {'statusCode': 500, 'body': json.dumps({'error': 'BACKEND_CALLBACK_URL not configured'})}

        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            logger.info(f"Processing PDF: {key}")

            file_id = key.split('_')[1] if '_' in key else None
            if not file_id:
                send_error_callback(None, f"Could not extract file ID from: {key}")
                continue

            document_text = extract_pdf_text(bucket, key)
            if not document_text:
                send_error_callback(file_id, "Failed to extract text from PDF")
                continue

            analysis_result = analyze_with_bedrock(document_text)
            if not analysis_result:
                send_error_callback(file_id, "Failed to analyze PDF")
                continue

            send_success_callback(file_id, analysis_result, document_text)

        return {'statusCode': 200, 'body': json.dumps({'message': 'PDF processed'})}

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

def extract_pdf_text(bucket, key):
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        pdf_content = response['Body'].read()
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
    try:
        prompt = (
            "You are a legal assistant. Analyze the following rental agreement for university students. "
            "Identify problematic clauses. Return valid JSON with the following schema: {...}\n\n"
            f"RENTAL AGREEMENT:\n{document_text[:8000]}"
        )

        body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 3000,
                "temperature": 0.1
            }
        }

        model_id = os.environ.get('BEDROCK_MODEL_ID', 'amazon.nova-pro-v1:0')

        response = bedrock.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )

        result = json.loads(response['body'].read())
        completion = result.get("outputText", "")
        start_idx = completion.find('{')
        end_idx = completion.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            return json.loads(completion[start_idx:end_idx])
        return None
    except Exception as e:
        logger.error(f"Bedrock analysis error: {str(e)}")
        return None

def send_success_callback(file_id, analysis_result, document_text):
    try:
        payload = {
            'fileId': file_id,
            'analysisResult': analysis_result,
            'documentText': document_text,
            'clausePositions': []
        }
        requests.post(BACKEND_CALLBACK_URL, json=payload, timeout=30)
        logger.info(f"Sent results for {file_id}")
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")

def send_error_callback(file_id, error_message):
    try:
        payload = {'fileId': file_id, 'error': error_message, 'status': 'failed'}
        requests.post(BACKEND_CALLBACK_URL, json=payload, timeout=30)
        logger.info(f"Sent error for {file_id}: {error_message}")
    except Exception as e:
        logger.error(f"Error callback failed: {str(e)}")