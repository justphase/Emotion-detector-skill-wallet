---
title: Socratica Companion
emoji: 🧠
colorFrom: indigo
colorTo: green
sdk: docker
app_port: 8000
pinned: false
---

# Socratica | Emotion-Aware Learning Companion

Socratica is a lightweight, custom-built web application designed to support learners by detecting their emotional state as they work through study roadblocks. By analyzing a free-text problem statement, Socratica compares a pre-trained RoBERTa model side-by-side with a custom-trained BiLSTM model to identify target emotions, and uses the Gemini API (with seamless fallback templates) to provide highly empathetic, subject-aware learning strategies.

This project was built to address all PRD constraints, avoiding default Streamlit looks or template designs, and utilizing a custom HSL-based modern edtech design system.

---

## Team & Owner Attribution

- **Aaditya Mishra (Lead)**: Model inference wrappers (pretrained RoBERTa & custom BiLSTM), unified prediction schema, and mixed-emotion classification logic.
- **Dhruv Sain**: Backend API routing (`/predict`, `/history`, `/log`), CSV log formatting and writing, Gemini API integration, and response regeneration logic.
- **Zenul Aabedeen Khan**: Frontend HTML/CSS/JS architecture, customized progress bars, responsive layout, and Chart.js analytics dashboards.
- **Palak Agarwal**: Environment setup (`requirements.txt`), template configurations (`.env`), and startup automation scripting.
- **Priya Sharma**: Documentation, setup guide, and final walkthrough write-up.

---

## Tech Stack & Architecture

- **Backend**: Python (FastAPI + Uvicorn) for REST endpoints.
- **Frontend**: Vanilla HTML5 / CSS3 / JavaScript (Modern custom theme) using Google Fonts ('Outfit' display pairing with 'Plus Jakarta Sans' body text).
- **Machine Learning**: 
  - **Model A (RoBERTa)**: Inference-only pipeline using `SamLowe/roberta-base-go_emotions` (500MB) from Hugging Face Hub, mapped onto the 5 target emotions.
  - **Model B (BiLSTM)**: Small PyTorch BiLSTM (Embedding dim=64, Hidden dim=64, Mean Pooling) trained from scratch on a clean, single-label mapped subset of 1,250 examples of GoEmotions.
- **AI Integration**: Google GenAI / Gemini API for contextual feedback.
- **Visualizations & Assets**: Chart.js (CDN) for overall emotion distribution history (Polar Area Chart).

---

## Prerequisites
- Python 3.12+ (Tested on Python 3.14)
- Pip package manager

---

## Project Flow
 
1. User selects a study subject and describes their problem in free text.
2. On clicking "Analyze & Get Support", the input is sent to the backend `/predict` endpoint.
3. Two models independently classify the emotion: a pre-trained RoBERTa model and a
   custom-trained lightweight BiLSTM — both return the same structured prediction format
   (primary emotion, confidence, all emotion scores, mixed/secondary emotions ≥15%).
4. Results from both models are displayed side by side for comparison.
5. If the "Use AI Assistant" toggle is on, the detected emotion + subject + problem text
   are sent to the Gemini API to generate an empathetic, field-specific response;
   otherwise a template-based fallback response is shown.
6. Every interaction (inputs, both models' predictions, selected response) is logged
   to a session file for later analysis.
7. The Analytics tab visualizes emotion trends across all logged sessions using charts.
---



## Setup & Running Instructions

### 1. Clone & Set Up the Environment
Open a terminal in the project folder and run the following:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your Gemini API Key in the template .env file
# Open the .env file in a text editor and update:
# GEMINI_API_KEY=your_actual_gemini_api_key
```

### 2. Run the Application
Start the FastAPI server:

```bash
python main.py
```

*Note: On startup, the backend automatically checks if the custom BiLSTM model (`bilstm_model.pth` and `vocab.json`) exists. If not found, it programmatically downloads a subset of GoEmotions, trains the BiLSTM model on CPU (takes ~5-15 seconds), saves the files, and launches the server.*

### 3. Open the Client
Once Uvicorn is running, open your web browser and navigate to:
```
http://localhost:8000
```

---

## Emotion Classification Mapping Rules

The GoEmotions source labels are mapped to Socratica's 5 target emotions as follows:
- **Bored**: `neutral`, `disappointment`, `sadness`
- **Confident**: `approval`, `pride`, `admiration`, `optimism`
- **Confused**: `confusion`
- **Curious**: `curiosity`
- **Frustrated**: `annoyance`, `anger`, `disapproval`

*Mixed Emotion Detection*: Any target emotion (other than the primary top-scoring emotion) with a confidence score greater than or equal to **15%** is categorized as a secondary emotion.

## Epic 5. Streamlit UI Implementation
 
The frontend is built with plain HTML/CSS/JS (no framework), organized into three
main views accessible from the top navigation bar: **Workspace**, **Analytics**, and
**Session Log**.
 
**Workspace view — layout and sections:**
- *Input panel (left)*: Study subject dropdown, free-text problem textarea, "Use AI
  Assistant" toggle, model selector (RoBERTa / BiLSTM) for which model's emotion drives
  the response, and the "Analyze & Get Support" submit button.
- *Response panel (top right)*: Displays the generated learning support response, with
  a manual "Regenerate" icon button to re-run generation without re-submitting the form.
- *Model comparison panel (bottom right)*: Two cards, one per model, each showing the
  primary emotion (with icon + confidence %), secondary/mixed emotions (≥15%
  confidence), and a confidence breakdown bar chart for all 5 emotions.
**Design system:**
- Each of the 5 emotions has one fixed color used consistently across badges, chart
  bars, and card accents (not a decorative gradient) — this makes the same emotion
  instantly recognizable everywhere in the UI.
- Form controls show clear loading states (spinner on the submit button) while
  waiting on the `/predict` and Gemini response calls, and inline error messages if
  a call fails (e.g. missing/invalid Gemini API key) instead of failing silently.
**Session state handling:**
- The last submitted input, both models' results, and the current response are kept
  in front-end state so switching between Workspace/Analytics/Session Log tabs does
  not lose the current result.
- Toggling "Use AI Assistant" or changing the input triggers a regeneration request
  without re-running the emotion classification twice unnecessarily — classification
  results are cached client-side until the input text actually changes.
**Analytics view:**
- Built with Chart.js, reading from the session log (CSV/SQLite) via a `/sessions`
  endpoint.
- Shows an emotion-distribution chart (count of each primary emotion detected across
  all past sessions) so trends over time are visible at a glance.
**Responsiveness & accessibility:**
- Layout collapses to a single column below ~768px width.
- All interactive elements have visible keyboard focus states.
- Emotions are distinguished by icon + label in addition to color, not color alone.
---
