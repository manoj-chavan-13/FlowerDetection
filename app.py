import os
import json
import uuid
import boto3
from datetime import datetime
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
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

# Initialize boto3 S3 client using environment variables if defined
boto3_kwargs = {"region_name": AWS_REGION}
if AWS_ACCESS_KEY and AWS_SECRET_KEY:
    boto3_kwargs["aws_access_key_id"] = AWS_ACCESS_KEY
    boto3_kwargs["aws_secret_access_key"] = AWS_SECRET_KEY

s3_client = boto3.client("s3", **boto3_kwargs)

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
    """Uploads flower image directly to S3 input/ folder which triggers AWS Lambda."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in request"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if not ext:
        ext = ".jpg"
    unique_id = f"flower_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:6]}{ext}"
    s3_key = f"input/{unique_id}"  # Stored in input/ folder
    
    try:
        file_bytes = file.read()
        
        # Upload directly to S3 input/ folder (automatically triggers AWS Lambda in cloud)
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
    """Query S3 text/ folder (.txt file) populated by AWS Lambda."""
    try:
        clean_id = os.path.basename(image_id)
        base_name = os.path.splitext(clean_id)[0]

        # 1. Check S3 text/ folder (and fallback output/) for .txt file
        txt_keys_to_try = [
            f"text/{clean_id}.txt",        # e.g. text/flower_123.jpg.txt
            f"text/{base_name}.txt",       # e.g. text/flower_123.txt
            f"text/{clean_id}",
            f"output/{clean_id}.txt",      # fallback e.g. output/flower_123.jpg.txt
            f"output/{base_name}.txt",     # fallback e.g. output/flower_123.txt
            f"output/{clean_id}",
        ]
        
        txt_content = None
        for key in txt_keys_to_try:
            try:
                obj = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
                txt_content = obj['Body'].read().decode('utf-8')
                break
            except Exception:
                continue

        if not txt_content:
            try:
                for prefix in [f"text/{clean_id}", f"text/{base_name}", f"output/{clean_id}", f"output/{base_name}"]:
                    resp = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
                    if resp.get("Contents"):
                        for item_obj in resp["Contents"]:
                            if item_obj["Key"].endswith(".txt"):
                                obj = s3_client.get_object(Bucket=S3_BUCKET, Key=item_obj["Key"])
                                txt_content = obj['Body'].read().decode('utf-8')
                                break
                    if txt_content:
                        break
            except Exception:
                pass

        if txt_content:
            parsed_data = {
                "imageId": clean_id,
                "flowerName": "Detected Flower",
                "flowerColor": "N/A",
                "flowerCondition": "Fresh",
                "flowerCount": 1,
                "confidence": 100.0,
            }
            
            clean_lines = []
            for line in txt_content.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                # Remove "thank you" or similar closing messages as requested
                if "thank you" in stripped.lower() or "thnk you" in stripped.lower():
                    continue
                clean_lines.append(stripped)
                
                # Extract key-value attributes
                if ":" in stripped:
                    parts = stripped.split(":", 1)
                    key_str = parts[0].strip().lower()
                    val_str = parts[1].strip().rstrip(".")
                    if "name" in key_str:
                        parsed_data["flowerName"] = val_str
                    elif "color" in key_str:
                        parsed_data["flowerColor"] = val_str
                    elif "condition" in key_str:
                        parsed_data["flowerCondition"] = val_str
                    elif "count" in key_str:
                        try:
                            parsed_data["flowerCount"] = int(val_str)
                        except ValueError:
                            pass
                    elif "confidence" in key_str:
                        try:
                            parsed_data["confidence"] = float(val_str.replace("%", "").strip())
                        except ValueError:
                            pass

            parsed_data["rawText"] = "\n\n".join(clean_lines)
            
            return jsonify({"success": True, "status": "completed", "data": parsed_data})
        else:
            return jsonify({"success": True, "status": "processing"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/image/<path:image_id>", methods=["GET"])
def get_image_proxy(image_id):
    """Proxy S3 image stream from input/ folder or root to frontend."""
    clean_id = os.path.basename(image_id)
    keys_to_try = [f"input/{clean_id}", clean_id, image_id]
    for key in keys_to_try:
        try:
            obj = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
            file_stream = io.BytesIO(obj['Body'].read())
            content_type = obj.get('ContentType', 'image/jpeg')
            return send_file(file_stream, mimetype=content_type)
        except Exception:
            continue
    return jsonify({"error": f"Image not found in S3: {clean_id}"}), 404

@app.route("/api/audio/<path:image_id>", methods=["GET"])
def get_audio_proxy(image_id):
    """Proxy S3 audio stream (.mp3) from output/ or audio/ folder to frontend."""
    clean_id = os.path.basename(image_id)
    base_name = os.path.splitext(clean_id)[0]
    
    keys_to_try = [
        f"output/{clean_id}.mp3",     # e.g. output/flower_123.jpg.mp3
        f"output/{base_name}.mp3",    # e.g. output/flower_123.mp3
        f"output/{clean_id}",
        f"audio/{clean_id}.mp3",      # e.g. audio/flower_123.jpg.mp3
        f"audio/{base_name}.mp3",     # e.g. audio/flower_123.mp3
        f"audio/{clean_id}",
    ]
    
    for key in keys_to_try:
        try:
            obj = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
            file_stream = io.BytesIO(obj['Body'].read())
            content_type = obj.get('ContentType', 'audio/mpeg')
            return send_file(file_stream, mimetype=content_type)
        except Exception:
            continue
            
    # Fallback: list objects in output/ or audio/ prefix matching base_name or clean_id
    try:
        for prefix in [f"output/{clean_id}", f"output/{base_name}", f"audio/{clean_id}", f"audio/{base_name}"]:
            resp = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
            if resp.get("Contents"):
                for item_obj in resp["Contents"]:
                    if item_obj["Key"].endswith(".mp3"):
                        key = item_obj["Key"]
                        obj = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
                        file_stream = io.BytesIO(obj['Body'].read())
                        return send_file(file_stream, mimetype="audio/mpeg")
    except Exception:
        pass
        
    return jsonify({"error": f"Audio file (.mp3) not found in S3 output/ or audio/ folder for: {clean_id}"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
