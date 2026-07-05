from transformers import pipeline
import numpy as np

# Define the 5 target emotions in alphabetical order
EMOTIONS = ["Bored", "Confident", "Confused", "Curious", "Frustrated"]

# Map GoEmotions category labels to target emotions
ROBERTA_MAPPING = {
    "confusion": "Confused",
    "curiosity": "Curious",
    "annoyance": "Frustrated",
    "anger": "Frustrated",
    "disapproval": "Frustrated",
    "approval": "Confident",
    "pride": "Confident",
    "admiration": "Confident",
    "optimism": "Confident",
    "neutral": "Bored",
    "disappointment": "Bored",
    "sadness": "Bored"
}

class RobertaWrapper:
    def __init__(self, model_name="SamLowe/roberta-base-go_emotions"):
        print(f"Loading pretrained RoBERTa model: {model_name}...")
        self.classifier = pipeline("text-classification", model=model_name, top_k=None)
        print("Pretrained RoBERTa model loaded successfully.")

    def predict(self, text):
        """
        Runs inference on the input text and returns predictions mapped to the 5 target emotions.
        """
        if not text.strip():
            # Handle empty input
            flat_score = 1.0 / len(EMOTIONS)
            return {
                "primary_emotion": EMOTIONS[0],
                "primary_confidence": round(flat_score, 4),
                "all_emotions": {e: round(flat_score, 4) for e in EMOTIONS},
                "mixed_emotions": []
            }

        # Run model inference
        results = self.classifier(text)[0]
        
        # Initialize target emotions scores
        target_scores = {e: 0.0 for e in EMOTIONS}
        
        # Accumulate scores based on mapping
        for item in results:
            label = item["label"]
            score = item["score"]
            if label in ROBERTA_MAPPING:
                target_emotion = ROBERTA_MAPPING[label]
                target_scores[target_emotion] += score

        # Clean/normalize scores to be between 0.0 and 1.0 (some sums might slightly exceed 1.0 due to floating point)
        for emotion in target_scores:
            target_scores[emotion] = min(max(round(float(target_scores[emotion]), 4), 0.0), 1.0)

        # Find primary emotion
        primary_emotion = max(target_scores, key=target_scores.get)
        primary_confidence = target_scores[primary_emotion]

        # Mixed emotions: any emotion other than the top one with confidence >= 15%
        mixed_emotions = []
        for emotion, prob in target_scores.items():
            if emotion != primary_emotion and prob >= 0.15:
                mixed_emotions.append([emotion, round(prob, 4)])

        # Sort mixed emotions descending by score
        mixed_emotions.sort(key=lambda x: x[1], reverse=True)

        return {
            "primary_emotion": primary_emotion,
            "primary_confidence": primary_confidence,
            "all_emotions": target_scores,
            "mixed_emotions": mixed_emotions
        }
