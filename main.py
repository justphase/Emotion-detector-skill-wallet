from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
import csv
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models and training script
from bilstm_model import BiLSTMWrapper, EMOTIONS
from bert_model import RobertaWrapper

app = FastAPI(title="Emotion-Aware Learning Support Platform API")

# Setup folder structure: ensure "static" exists
os.makedirs("static", exist_ok=True)

# File Paths
LOG_FILE = "logs.csv"
BILSTM_WEIGHTS = "bilstm_model.pth"
BILSTM_VOCAB = "vocab.json"

# Check and train BiLSTM if weights are missing
if not os.path.exists(BILSTM_WEIGHTS) or not os.path.exists(BILSTM_VOCAB):
    print("BiLSTM weights or vocab not found. Training model automatically on GoEmotions subset...")
    import train_bilstm
    try:
        train_bilstm.train()
    except Exception as e:
        print(f"Error during automatic BiLSTM training: {e}")
        # Continue starting, wrappers will handle errors gracefully

# Initialize wrappers
bilstm_wrapper = BiLSTMWrapper(model_path=BILSTM_WEIGHTS, vocab_path=BILSTM_VOCAB)
roberta_wrapper = RobertaWrapper()

# Fallback Responses for validation & action steps
FALLBACK_TEMPLATES = {
    "Bored": (
        "It looks like you're feeling a bit disengaged with {field}. That's completely normal when dealing "
        "with tricky or dry topics! Try taking a short 5-minute break to stretch or rest. When you return, "
        "try looking at a different angle of the problem, or try to relate it to a practical real-world application. "
        "Sometimes a quick change of pace or a hands-on example is all you need to spark your interest again!"
    ),
    "Confident": (
        "Fantastic! You're approaching this {field} problem with confidence, which is a great mental starting point. "
        "Keep this positive momentum going! To reinforce what you know, try explaining the concept in your own words "
        "to a friend, or challenge yourself with a slightly harder version of the problem. Teaching others is one "
        "of the best ways to test your own mastery!"
    ),
    "Confused": (
        "It's completely okay to feel confused! Confusion is just a sign that your brain is actively working to construct "
        "new understanding in {field}. Let's break this down into smaller, simpler parts. Try writing out the given information, "
        "reviewing the core definitions, or attempting a simpler, related example in your notes. You've got this!"
    ),
    "Curious": (
        "I love your curiosity about {field}! This is a wonderful and highly effective mindset for learning. "
        "Leverage this state of mind: ask yourself *why* this rule or formula behaves the way it does, rather than just "
        "trying to memorize it. Explore online resources, watch a visualization, or draw a diagram to feed your interest."
    ),
    "Frustrated": (
        "I hear you, and it's completely understandable to feel frustrated. Studying {field} can be challenging, and getting "
        "stuck is really tough. Take a deep breath. Let's step back from the details. Try reviewing a similar, fully solved "
        "problem in your text, or review the basic rules first. Remember, every mistake is a step closer to understanding."
    )
}

class PredictRequest(BaseModel):
    field: str
    problem_text: str
    use_ai: bool = True
    selected_model: Optional[str] = "Model A"  # "Model A" = RoBERTa, "Model B" = BiLSTM

def get_gemini_response(field: str, text: str, emotion: str, mixed: List[List[Any]]) -> str:
    """
    Attempts to call Gemini API to generate an empathetic response.
    Falls back to predefined templates on failure or if credentials are missing.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Gemini API key missing. Using fallback template.")
        return FALLBACK_TEMPLATES.get(emotion, "").format(field=field)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Build prompt
        mixed_str = ", ".join([f"{e} ({round(s*100)}%)" for e, s in mixed])
        secondary_part = f" with secondary emotions: {mixed_str}" if mixed_str else ""
        
        prompt = (
            f"You are a warm, empathetic, and field-aware learning assistant. A student studying {field} is stuck.\n"
            f"Their problem description: \"{text}\"\n"
            f"The emotion detection system analyzed their text and classified their primary emotion as: {emotion}{secondary_part}.\n\n"
            f"Write a response that:\n"
            f"1. Validates and addresses their emotional state directly (e.g. if they are frustrated, acknowledge it warmly; if they are confident, encourage them).\n"
            f"2. Is field-aware: reference {field} and the general context of their block where appropriate.\n"
            f"3. Provides concrete, actionable learning strategy suggestions (next steps) to guide them.\n\n"
            f"Keep the response concise (between 2 to 4 paragraphs), encouraging, and supportive. Use clean text formatting."
        )
        
        # Try latest gemini-2.5-flash, fall back to gemini-1.5-flash
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text
            
    except Exception as e:
        print(f"Gemini API generation failed: {e}. Falling back to template.")
        return FALLBACK_TEMPLATES.get(emotion, "").format(field=field)

def log_session(field: str, problem_text: str, model_a_pred: Dict, model_b_pred: Dict, selected_model: str, mixed_emotions: List, final_response: str):
    """
    Appends a record of the session to logs.csv.
    """
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp", "field", "problem_text", 
                "model_a_pred", "model_b_pred", 
                "selected_model", "mixed_emotions", "final_response"
            ])
            
        writer.writerow([
            datetime.datetime.now().isoformat(),
            field,
            problem_text,
            json.dumps(model_a_pred),
            json.dumps(model_b_pred),
            selected_model,
            json.dumps(mixed_emotions),
            final_response
        ])

@app.post("/predict")
def predict_endpoint(req: PredictRequest):
    if not req.problem_text.strip():
        raise HTTPException(status_code=400, detail="Problem description cannot be empty.")

    # 1. Run inferences
    try:
        model_a_res = roberta_wrapper.predict(req.problem_text)
    except Exception as e:
        print(f"Error in RoBERTa inference: {e}")
        model_a_res = {
            "primary_emotion": "Confused",
            "primary_confidence": 0.0,
            "all_emotions": {em: 0.0 for em in EMOTIONS},
            "mixed_emotions": []
        }

    try:
        model_b_res = bilstm_wrapper.predict(req.problem_text)
    except Exception as e:
        print(f"Error in BiLSTM inference: {e}")
        model_b_res = {
            "primary_emotion": "Confused",
            "primary_confidence": 0.0,
            "all_emotions": {em: 0.0 for em in EMOTIONS},
            "mixed_emotions": []
        }

    # Determine which model is selected for Response Guidance
    selected_res = model_a_res if req.selected_model == "Model A" else model_b_res
    primary_emotion = selected_res["primary_emotion"]
    mixed_emotions = selected_res["mixed_emotions"]

    # 2. Response Generation
    if req.use_ai:
        response_text = get_gemini_response(req.field, req.problem_text, primary_emotion, mixed_emotions)
    else:
        response_text = FALLBACK_TEMPLATES.get(primary_emotion, "").format(field=req.field)

    # 3. Log the session
    try:
        log_session(
            req.field, 
            req.problem_text, 
            model_a_res, 
            model_b_res, 
            req.selected_model or "Model A", 
            mixed_emotions, 
            response_text
        )
    except Exception as e:
        print(f"Failed to log session: {e}")

    # Return prediction summaries
    return {
        "model_a": model_a_res,
        "model_b": model_b_res,
        "selected_model": req.selected_model,
        "response": response_text
    }

@app.get("/history")
def history_endpoint():
    """
    Returns the log history for display in frontend table and Chart.js aggregation.
    """
    if not os.path.exists(LOG_FILE):
        return []
    
    logs = []
    try:
        with open(LOG_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row["model_a_pred"] = json.loads(row["model_a_pred"])
                    row["model_b_pred"] = json.loads(row["model_b_pred"])
                    row["mixed_emotions"] = json.loads(row["mixed_emotions"])
                except Exception:
                    pass
                logs.append(row)
    except Exception as e:
        print(f"Error reading log file: {e}")
        
    return logs

# Serve static files response for Root path
@app.get("/")
def read_index():
    return FileResponse("static/index.html")

# Mount the static directory to serve index.html, style.css, app.js
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    # Use environment port or default to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
