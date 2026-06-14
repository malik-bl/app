<<<<<<< HEAD
# 🎯 InterviewAI — AI-Powered Interview Coach

A full-stack web application that analyzes your CV, conducts live video interviews, and provides comprehensive feedback with personalized course recommendations — powered by **Groq AI (LLaMA 3.3 70B)**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Auth** | Sign up / Login with session management |
| 📄 **CV Analysis** | Upload PDF/DOCX/TXT — AI extracts skills, gaps & strengths |
| 🎯 **Custom Questions** | 7 AI-generated questions tailored to your CV & field |
| 🎥 **Live Interview** | Real-time video with body language detection |
| 🎙️ **Smart Mic** | Speech recognition with auto-restart, no-speech fallback, type mode |
| 📊 **Deep Feedback** | Per-answer scores: clarity, relevance, confidence |
| 🚀 **AI Courses** | AI-generated course recommendations tied to your exact gaps |

---

## 🏗️ Tech Stack

**Backend:** Python 3.10+, Flask 3.0, Groq API (LLaMA 3.3 70B), PyPDF2, python-docx  
**Frontend:** HTML5 / CSS3 / Vanilla JS, Web Speech API, MediaDevices API

---

## 🚀 Quick Start

### 1. Get a Groq API Key
Visit [console.groq.com](https://console.groq.com) and create a free API key.

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY=gsk_your_key_here
```

### 3. Run
```bash
chmod +x run.sh && ./run.sh
# OR manually:
pip install -r requirements.txt
python app.py
```

### 4. Open Browser
Navigate to **http://localhost:5000**

---

## 📁 Project Structure

```
InterviewAI/
├── app.py                  # Flask routes & API endpoints
├── groq_service.py         # Groq AI: CV analysis, questions, feedback, AI courses
├── cv_analyzer.py          # CV text extraction (PDF, DOCX, TXT)
├── body_language.py        # Body language scoring (eye contact, confidence, engagement)
├── requirements.txt        # Python dependencies
├── run.sh                  # Quick start script
├── .env.example            # Environment template
└── templates/
    ├── index.html          # Landing page + Auth modal
    ├── dashboard.html      # CV upload + field selection
    ├── interview.html      # Live interview (video + speech)
    └── results.html        # Report + AI course recommendations
```

---

## ⚙️ Environment Variables

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
SECRET_KEY=your-random-secret-key-here
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/signup` | Register new user |
| POST | `/api/login` | Login |
| POST | `/api/logout` | Logout |
| GET | `/api/auth/status` | Check auth state |
| POST | `/api/upload-cv` | Upload & analyze CV |
| POST | `/api/generate-questions` | Generate 7 interview questions |
| POST | `/api/process-answer` | Analyze spoken answer + body language |
| POST | `/api/generate-feedback` | Generate final report + AI course recommendations |
| GET | `/api/get-results` | Retrieve last results |

---

## 📝 License
MIT License — Free for personal and commercial use
=======
# app
>>>>>>> dc0675fd6cbbf0702063a307f86680b4ade998eb
