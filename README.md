# AcneSense Monorepo

<div align="center">
  <img width="1102" height="412" alt="Group 52" src="https://github.com/user-attachments/assets/374c6f47-d6e6-47d5-bc59-a35501501c16" width="100"/>
  <h2>AI-Powered Acne Detection, Analysis & Knowledge Platform</h2>
  <p><em>Machine Learning · Flask API (Models & RAG) · Express.js Fullstack · Supabase · Vertex AI · Docker · Cloud Run · PWA</em></p>
</div>

---

## 🌟 Overview

AcneSense is an integrated platform for AI-powered acne detection, analysis, and skincare guidance.  
- The Express.js app (`web/`) is a fullstack application serving both frontend (UI, views) and backend (authentication, routing, API endpoints, business logic).
- The Flask API (`api/`) is a dedicated service for machine learning model inference and RAG-powered Q&A (retrieval-augmented generation, e.g. LLM Q&A), consumed by the web app.

---

## 📁 Repository Structure

```
.
├── ml/      # Machine learning research & notebooks
├── api/     # Flask API service for models and RAG
├── web/     # Fullstack Express.js app (frontend & backend)
```

---

## 🚀 Features

- 🧠 ML model training, evaluation, and experimentation
- 🔎 AI-powered acne diagnosis (image + user info)
- 📊 RAG-based Q&A endpoint (Gemini/Vertex AI)
- 📷 Real-time acne detection (camera/image upload)
- 📊 Detection history & analytics
- 🤖 AI chatbot for skincare
- 📱 PWA: offline support, installable
- 💾 Supabase cloud database
- 🐳 Docker & Cloud Run ready

---

## 💻 Technology Stack

- **ML**: Python (Jupyter Notebooks), TensorFlow/Keras, scikit-learn, pandas, numpy, matplotlib
- **API**: Python 3.11, Flask, TFLite, Vertex AI, Qdrant, Supabase, Docker, Cloud Run
- **Web**: Node.js, Express.js, EJS, Tailwind CSS, Vite, Supabase, Docker, PWA

---

## ⚡ Quick Start

### Clone the Repo

```bash
git clone https://github.com/andyathsid/acne-sense-monorepo.git
```

---

### ML Development (`ml/`)

#### Prerequisites

- Python 3.8+
- Jupyter Notebook or JupyterLab

#### Setup

```bash
cd ml
python -m venv venv
source venv/bin/activate
pip install jupyter pandas numpy scikit-learn tensorflow matplotlib
jupyter notebook
```

#### Usage

- Open notebooks in `ml/notebooks/` with Jupyter.
- Run cells to train, evaluate, and experiment with models.
- Export trained models for use in the API or web modules.

---

### API (`api/`)

#### Prerequisites

- Python 3.11+
- pip
- Docker (optional)
- Supabase account/project
- Google Cloud service account (for Vertex AI/Gemini)

#### Setup

```bash
cd api
pip install -r requirements.dev.txt
cp .env.example .env
cp .flaskenv.example .flaskenv
# Edit .env and .flaskenv with your credentials
flask run
# Or use Gunicorn for production
gunicorn --bind 0.0.0.0:8000 'app:create_app()'
```

#### Docker

```bash
docker build -t acne-sense-api -f Dockerfile.dev .
docker run -p 8000:8000 --env-file .env acne-sense-api
```

#### Docker Compose

```bash
docker-compose -f docker-compose.dev.yaml up --build
```

#### Main Endpoints

| Route                | Method | Description                       |
|----------------------|--------|-----------------------------------|
| `/health`            | GET    | Health check                      |
| `/image-diagnosis`   | POST   | Diagnose acne from image          |
| `/combined-diagnosis`| POST   | Diagnose acne (image + user info) |
| `/question`          | POST   | Ask acne-related question (RAG)   |
| `/feedback`          | POST   | Submit feedback for answer        |
| `/diagnosis`         | POST   | Get treatment recommendations     |

---

### Web Fullstack App (`web/`)

#### Prerequisites

- Node.js (v14+)
- npm
- Supabase account/project
- AI detection service (port 5000)

#### Setup

```bash
cd web
npm install
cp .env.example .env
# Edit .env with your Supabase credentials
npm run dev
# For production
npm run build
npm start
```

#### Docker

```bash
docker build -t acne-sense-web .
docker run -p 3000:3000 acne-sense-web
```

#### Main Endpoints

| Route             | Method | Description                  |
|-------------------|--------|------------------------------|
| `/register`       | POST   | User registration            |
| `/login`          | POST   | User login                   |
| `/logout`         | POST   | User logout                  |
| `/dashboard`      | GET    | User dashboard               |
| `/deteksi`        | GET    | Detection page               |
| `/preview`        | GET    | Image preview                |
| `/chatbot`        | GET    | AI chatbot                   |
| `/riwayat`        | GET    | Detection history            |
| `/hasil/:id`      | GET    | Detection results            |
| `/save-detection` | POST   | Save detection results       |
| `/api/session-status` | GET | Check login status           |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Make changes 
4. Test thoroughly
5. Submit a pull request

---

## 📄 **License**

This project is licensed under the **MIT License** - see the [LICENSE](https://choosealicense.com/licenses/mit/) here

```
MIT License - Open Source Freedom
├── ✅ Commercial use
├── ✅ Modification
├── ✅ Distribution
├── ✅ Private use
└── ❌ Liability & Warranty
```

---
