
# 🧠 Socratica – Emotion-Aware Learning Companion

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-4285F4)
![Status](https://img.shields.io/badge/Status-Active-success)

</p>

> An AI-powered learning companion that understands a student's emotional state and provides personalized learning support using **RoBERTa**, **BiLSTM**, and **Google Gemini AI**.

---

# ✨ Key Features

- 🧠 Emotion Detection using two AI models
- ⚖️ Side-by-side comparison of RoBERTa & BiLSTM
- 🤖 AI-generated learning guidance with Gemini
- 📊 Emotion analytics dashboard
- 📝 Session history logging
- ⚡ FastAPI backend with REST APIs
- 📱 Responsive modern UI

---

# 🏗️ Tech Stack

| Category | Technology |
|----------|------------|
| Backend | FastAPI, Uvicorn |
| Frontend | HTML, CSS, JavaScript |
| AI | Google Gemini |
| Deep Learning | PyTorch |
| NLP | RoBERTa, BiLSTM |
| Charts | Chart.js |

---

# 📂 Project Structure

```text
Emotion-detector-skill-wallet
│
├── main.py
├── bert_model.py
├── bilstm_model.py
├── train_bilstm.py
├── requirements.txt
├── static/
├── templates/
└── utils/
```

---

# 🚀 Installation

```bash
git clone https://github.com/justphase/Emotion-detector-skill-wallet.git
cd Emotion-detector-skill-wallet
python -m venv venv
```

Activate environment

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create `.env`

```env
GEMINI_API_KEY=YOUR_API_KEY
```

Run application

```bash
python main.py
```

Open:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

---

# 🔌 API Endpoints

| Method | Endpoint | Purpose |
|---------|----------|---------|
| GET | / | Home |
| POST | /predict | Predict Emotion |
| POST | /generate | Generate AI Response |
| POST | /log | Save Session |
| GET | /sessions | Analytics Data |

---

# 🎯 Emotion Categories

- 😴 Bored
- 😎 Confident
- 🤔 Confused
- 🔍 Curious
- 😤 Frustrated

Secondary emotions are displayed whenever confidence is **15% or higher**.

---

# 📊 Workflow

```text
User Input
     │
     ▼
 Emotion Detection
(RoBERTa + BiLSTM)
     │
     ▼
 Gemini AI Response
     │
     ▼
 Session Logging
     │
     ▼
 Analytics Dashboard
```

---

# 📈 Future Improvements

- User Authentication
- Database Support
- Cloud Deployment
- Model Optimization
- More Emotion Classes

---

# 👥 Team

- Aaditya Mishra – AI Models
- Dhruv Sain – Backend APIs
- Zenul Aabedeen Khan – Frontend
- Palak Agarwal – Environment & Setup
- Priya Sharma – Documentation

---

# 📄 License

This project is intended for educational and research purposes.
## Links
- *Live Demo*: https://huggingface.co/spaces/crazyaadi/socratica-companion
- *GitHub Repository*: https://github.com/justphase/Emotion-detector-skill-wallet
- *Dataset Used*: GoEmotions (Hugging Face) — https://huggingface.co/datasets/go_emotions
- *Pre-trained Model*: RoBERTa fine-tuned on GoEmotions — https://huggingface.co/SamLowe/roberta-base-go_emotions
- *Gemini API Documentation*: https://ai.google.dev/gemini-api/docs

## Conclusion
The AI-Driven Emotion Detection & Personalized Learning Support Platform successfully
demonstrates how deep learning-based emotion classification can be combined with
generative AI to deliver real-time, empathetic academic support. By comparing a
pre-trained transformer model (RoBERTa) against a lightweight custom-trained BiLSTM,
the platform highlights the trade-off between accuracy and training cost — a key
consideration in real-world ML deployment.

The system detects both primary and secondary (mixed) emotional states from a
learner's free-text input, and uses this signal to generate contextual, field-aware
guidance via the Gemini API, with a graceful template-based fallback when AI
generation is unavailable. Session logging and analytics further support the
platform's goal of enabling continuous learning and long-term insight into a
learner's emotional patterns over time.

This project reinforced practical skills across the ML lifecycle — data preparation,
model comparison, prompt engineering, and full-stack integration — while working
under real time constraints, mirroring the kind of trade-offs made in production
AI systems.
