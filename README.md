# 🌸 AWS FloraSense | AI Flower Detection Studio

<div align="center">

![AWS FloraSense Banner](https://img.shields.io/badge/AWS-FloraSense-10B981?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![AWS Serverless](https://img.shields.io/badge/AWS-Serverless_Pipeline-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**An ultra-modern, serverless, mobile-first botanical recognition application powered by Amazon Rekognition, AWS Lambda, and S3 (`input/`, `text/`, `output/` folders).**

---

</div>

## ✨ Overview

**AWS FloraSense** is a cutting-edge serverless AI portal designed to instantly recognize flower species and count blooms with industrial precision. Built with a **Native Mobile App UX**, it features organic glassmorphism, asynchronous live-camera capture, and laser-scanning animations that seamlessly link to an event-driven AWS cloud backend.

### 📱 Key Frontend & UX Features
- **Pure Mobile-First Architecture**: Single-card segmented interface built specifically for smartphone viewports and touch interaction.
- **Organic Glassmorphic Blending**: Features asymmetric corner dissolution and dynamic radial mesh glow gradients.
- **Dual Capture Pipeline**: Switch effortlessly between **File Upload** and **Live Camera Capture** with native smartphone fallback (`capture="environment"`).
- **Interactive Scanning Telemetry**: Real-time laser scanner visualizer with polling indicators while AWS Lambda analyzes botanical markers in the cloud.

---

## 🏗️ Serverless Cloud Architecture

```
[ Mobile Frontend / Flask API ]
             │
             ├── (POST /api/upload) ──> [ AWS S3 Bucket: input/ folder ]
             │                                       │
             │                                (S3 PutEvent Trigger)
             │                                       ▼
             │                        [ AWS Lambda: FlowerProcessingLambda ]
             │                                       │
             │                          (Amazon Rekognition API)
             │                                       │
             │                                       ▼
             └── (GET /api/results) <── [ AWS S3 Bucket: text/ (.txt) & output/ (.mp3) ]
```

### 🌍 AWS Environment Details
* **Region**: `ap-south-1` (Asia Pacific - Mumbai)
* **Storage Bucket (`S3`)**: Multi-folder pipeline (`input/`, `text/`, `output/`)
* **AI Analysis Engine**: **Amazon Rekognition** (`DetectLabels` API)
* **Serverless Execution**: **AWS Lambda** (`FlowerProcessingLambda` on Python 3.12)

---

## 📊 Exact Output Verification

When an image is processed, the system outputs precisely 4 verified biometric attributes:
1. **Flower Name**: Recognized species label (e.g., *Rose*, *Sunflower*, *Orchid*).
2. **Flower Count**: Exactly enumerated bloom instances detected within the frame.
3. **Confidence Level**: High-precision recognition percentage (`100.0%`).
4. **Image ID**: Cryptographic unique storage identifier (`uuid4.jpg`).

---

## 🚀 Quickstart & Installation

### Prerequisites
* **Python 3.9+** installed locally.
* **AWS CLI** configured (`aws configure`) with access to S3 and Rekognition.

### 1. Clone the Repository
```bash
git clone https://github.com/manoj-chavan-13/FlowerDetection.git
cd FlowerDetection
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and set your credentials:
```bash
cp .env.example .env
```
*(Note: If you already use `~/.aws/credentials`, `boto3` will resolve them automatically without editing `.env`!)*

### 4. Launch the Local Server
```bash
python app.py
```
Visit `http://localhost:5000` in your web browser or mobile phone connected to your local Wi-Fi!

---

## 🐳 Docker Deployment

Run **AWS FloraSense** in an isolated, lightweight container environment using Docker or Docker Compose.

### Option A: Using Docker Compose (Recommended)
Ensure your `.env` file is configured with your AWS credentials, then launch the service:
```bash
docker compose up -d --build
```
Access the application at `http://localhost:5000`. To stop the application:
```bash
docker compose down
```

### Option B: Using Standalone Docker CLI
1. **Build the image**:
   ```bash
   docker build -t florasense:latest .
   ```
2. **Run the container**:
   ```bash
   docker run -d -p 5000:5000 --env-file .env --name florasense-app florasense:latest
   ```

### Option C: Run Directly from Docker Hub
You can run the published image directly without cloning or building locally:
```bash
docker run -d -p 5000:5000 --env-file .env --name florasense-app manojc13/florasense:latest
```

---

## 📁 Project Directory Structure

```text
FlowerDetectionProject/
├── app.py             # Flask API Server & AWS SDK Controller
├── index.html         # Single-Page Mobile Native Interface
├── script.js          # Camera Controller & S3 Polling Client
├── style.css          # Glassmorphic Utilities & Scan Animations
├── requirements.txt   # Python Dependencies (flask, boto3, dotenv)
├── Dockerfile         # Production-Grade Lightweight Python Container
├── docker-compose.yml # Docker Compose Orchestration Config
├── .dockerignore      # Exclusions for Docker Build Context
├── .env.example       # Environment Variables Template
└── .gitignore         # Security exclusions for .env & cache
```

---

<div align="center">
  <p font-size="12px">© 2026 AWS FloraSense. All rights reserved.</p>
</div>
