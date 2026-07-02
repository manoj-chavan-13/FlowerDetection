import os
import json
import uuid
import boto3
from datetime import datetime
from decimal import Decimal
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from dotenv import load_dotenv
import io

# Automatically load environment variables from .env if present
load_dotenv()

app = Flask(__name__)
CORS(app)

# AWS Configuration loaded from .env
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")
S3_BUCKET = os.environ.get("S3_BUCKET", "flowers-images-for-demo")
DYNAMODB_TABLE = os.environ.get("TABLE_NAME", "FlowerDetectionResults")
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

# Initialize boto3 clients using environment variables if defined
boto3_kwargs = {"region_name": AWS_REGION}
if AWS_ACCESS_KEY and AWS_SECRET_KEY:
    boto3_kwargs["aws_access_key_id"] = AWS_ACCESS_KEY
    boto3_kwargs["aws_secret_access_key"] = AWS_SECRET_KEY

s3_client = boto3.client("s3", **boto3_kwargs)
dynamodb = boto3.resource("dynamodb", **boto3_kwargs)
table = dynamodb.Table(DYNAMODB_TABLE)

# Helper to serialize Decimal objects from DynamoDB
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 > 0:
                return float(obj)
            else:
                return int(obj)
        return super(DecimalEncoder, self).default(obj)

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/style.css")
def serve_css():
    return send_file("style.css", mimetype="text/css")

@app.route("/script.js")
def serve_js():
    return send_file("script.js", mimetype="application/javascript")

@app.route("/api/upload", methods=["POST"])
def upload_image():
    """Uploads flower image directly to S3 root which triggers AWS Lambda."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in request"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if not ext:
        ext = ".jpg"
    unique_id = f"flower_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:6]}{ext}"
    s3_key = unique_id  # Stored directly in root
    
    try:
        file_bytes = file.read()
        
        # Upload directly to S3 root (automatically triggers AWS Lambda in cloud)
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_bytes,
            ContentType=file.content_type or 'image/jpeg'
        )
        
        return jsonify({
            "success": True,
            "imageId": unique_id,
            "s3Key": s3_key,
            "bucketName": S3_BUCKET
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/results/<path:image_id>", methods=["GET"])
def get_results(image_id):
    """Query DynamoDB table FlowerDetectionResults populated by AWS Lambda."""
    try:
        clean_id = os.path.basename(image_id)
        response = table.get_item(Key={'imageId': clean_id})
        item = response.get('Item')
        
        if not item and clean_id != image_id:
            response = table.get_item(Key={'imageId': image_id})
            item = response.get('Item')
            
        if item:
            return Response(
                json.dumps({"success": True, "status": "completed", "data": item}, cls=DecimalEncoder),
                mimetype="application/json"
            )
        else:
            return jsonify({"success": True, "status": "processing"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/image/<path:image_id>", methods=["GET"])
def get_image_proxy(image_id):
    """Proxy S3 image stream to frontend."""
    s3_key = os.path.basename(image_id)
    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        file_stream = io.BytesIO(obj['Body'].read())
        content_type = obj.get('ContentType', 'image/jpeg')
        return send_file(file_stream, mimetype=content_type)
    except Exception as e:
        return jsonify({"error": f"Image not found in S3: {str(e)}"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
