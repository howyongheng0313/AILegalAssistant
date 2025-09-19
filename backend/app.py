import os
from flask import Flask, request
import boto3
from dotenv import load_dotenv

# 1️⃣ 读取 .env 文件
load_dotenv()

# 2️⃣ 获取 Key 和 Region
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION')

# 3️⃣ 创建 S3 客户端
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    s3.upload_fileobj(file, 'your-bucket-name', file.filename)
    return {'message': 'Upload Successful'}, 200

if __name__ == '__main__':
    app.run(debug=True)
