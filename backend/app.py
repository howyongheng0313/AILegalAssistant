import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from dotenv import load_dotenv
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# AWS configuration
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Create S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

app = Flask(__name__)
CORS(app)

# Simple in-memory storage for analysis results
analysis_results = {}

@app.route('/upload', methods=['POST'])
def upload_pdf():
    """Upload PDF file only"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # File type validation - PDF ONLY for prototype
        if file.content_type != 'application/pdf':
            return jsonify({'success': False, 'message': 'Please upload PDF files only.'}), 400
        
        # File size validation (10MB limit)
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            return jsonify({'success': False, 'message': 'File size must be less than 10MB'}), 400
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"pdfs/{timestamp}_{file_id}_{file.filename}"
        
        # Upload to S3
        s3.upload_fileobj(file, S3_BUCKET_NAME, s3_key)
        
        # Initialize analysis status
        analysis_results[file_id] = {
            'status': 'processing',
            'message': 'PDF uploaded, analysis in progress...',
            'timestamp': datetime.now().isoformat(),
            'fileName': file.filename,
            's3Key': s3_key
        }
        
        return jsonify({
            'success': True,
            'fileId': file_id,
            'fileName': file.filename,
            'message': 'PDF uploaded successfully'
        }), 200
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500

@app.route('/analysis-result', methods=['POST'])
def receive_analysis_result():
    """Receive analysis results from Lambda"""
    try:
        data = request.get_json()
        
        file_id = data.get('fileId')
        analysis_result = data.get('analysisResult')
        document_text = data.get('documentText')
        clause_positions = data.get('clausePositions', [])
        
        if not file_id or not analysis_result:
            return jsonify({'success': False, 'message': 'Missing required data'}), 400
        
        # Store results
        analysis_results[file_id] = {
            'status': 'completed',
            'message': 'Analysis completed successfully',
            'analysisResult': analysis_result,
            'documentText': document_text,
            'clausePositions': clause_positions,
            'completedAt': datetime.now().isoformat()
        }
        
        print(f"Analysis completed for file {file_id}")
        return jsonify({'success': True, 'message': 'Results stored'}), 200
        
    except Exception as e:
        print(f"Error receiving results: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/analysis-status/<file_id>', methods=['GET'])
def get_analysis_status(file_id):
    """Check analysis status"""
    try:
        if file_id not in analysis_results:
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        result = analysis_results[file_id]
        return jsonify({
            'success': True,
            'status': result['status'],
            'message': result['message'],
            'analysisResult': result.get('analysisResult'),
            'documentText': result.get('documentText'),
            'clausePositions': result.get('clausePositions', [])
        }), 200
        
    except Exception as e:
        print(f"Error getting status: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Simple chat endpoint for prototype"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'message': 'No message provided'}), 400
        
        # Simple response for prototype
        response_message = f"Thanks for your question: '{message}'. This is a prototype chat response. Full chat functionality will be available after AWS setup is complete."
        
        return jsonify({
            'success': True,
            'response': response_message,
            'message': 'Chat response generated'
        }), 200
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({'success': False, 'message': f'Chat failed: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    print(" PDF Legal Assistant Backend Starting...")
    print(f" S3 Bucket: {S3_BUCKET_NAME}")
    print(" Supports: PDF files only")
    app.run(debug=True, host='0.0.0.0', port=5000)
