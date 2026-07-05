import torch
import torch.nn as nn
import re
import json
import os

# Define the 5 target emotions in alphabetical order for consistency
EMOTIONS = ["Bored", "Confident", "Confused", "Curious", "Frustrated"]

class BiLSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim=64, hidden_dim=64, output_dim=5):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim * 2, output_dim)
        
    def forward(self, x):
        # x shape: [batch, seq_len]
        embedded = self.embedding(x)  # [batch, seq_len, embedding_dim]
        lstm_out, _ = self.lstm(embedded)  # [batch, seq_len, hidden_dim * 2]
        # Mean pooling over sequence dimension
        pooled = torch.mean(lstm_out, dim=1)  # [batch, hidden_dim * 2]
        logits = self.fc(pooled)  # [batch, output_dim]
        return logits

def clean_text(text):
    """
    Cleans text by lowercasing, removing non-alphanumeric characters except spaces,
    and removing extra whitespaces.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize(text):
    """
    Tokenizes clean text into a list of words.
    """
    return clean_text(text).split()

def text_to_indices(text, vocab, max_len=50):
    """
    Converts a text string into a list of vocabulary indices with padding/truncation.
    """
    words = tokenize(text)
    indices = []
    for w in words:
        indices.append(vocab.get(w, 1))  # 1 is <unk>
    
    # Pad or truncate
    if len(indices) < max_len:
        indices += [0] * (max_len - len(indices))  # 0 is <pad>
    else:
        indices = indices[:max_len]
        
    return indices

class BiLSTMWrapper:
    def __init__(self, model_path="bilstm_model.pth", vocab_path="vocab.json"):
        self.model_path = model_path
        self.vocab_path = vocab_path
        self.model = None
        self.vocab = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        if os.path.exists(model_path) and os.path.exists(vocab_path):
            self.load()
            
    def load(self):
        # Load vocabulary
        with open(self.vocab_path, "r", encoding="utf-8") as f:
            self.vocab = json.load(f)
            
        # Initialize and load model weights
        vocab_size = len(self.vocab)
        self.model = BiLSTMClassifier(vocab_size)
        self.model.load_state_dict(torch.load(self.model_path, map_location=self.device, weights_only=True))
        self.model.to(self.device)
        self.model.eval()
        
    def predict(self, text):
        """
        Runs inference on the input text and returns predictions in the unified schema.
        """
        if self.model is None or self.vocab is None:
            # If not loaded, return default flat predictions
            flat_score = 1.0 / len(EMOTIONS)
            all_emotions = {e: flat_score for e in EMOTIONS}
            return {
                "primary_emotion": EMOTIONS[0],
                "primary_confidence": round(flat_score, 4),
                "all_emotions": {e: round(flat_score, 4) for e in EMOTIONS},
                "mixed_emotions": []
            }
            
        indices = text_to_indices(text, self.vocab)
        tensor = torch.tensor([indices], dtype=torch.long).to(self.device)
        
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze().cpu().numpy()
            
        all_emotions = {}
        for emotion, prob in zip(EMOTIONS, probs):
            all_emotions[emotion] = round(float(prob), 4)
            
        # Find primary emotion
        primary_emotion = max(all_emotions, key=all_emotions.get)
        primary_confidence = all_emotions[primary_emotion]
        
        # Mixed emotions: any emotion other than the top one with confidence >= 15%
        mixed_emotions = []
        for emotion, prob in all_emotions.items():
            if emotion != primary_emotion and prob >= 0.15:
                mixed_emotions.append([emotion, round(prob, 4)])
                
        # Sort mixed emotions descending by score
        mixed_emotions.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "primary_emotion": primary_emotion,
            "primary_confidence": primary_confidence,
            "all_emotions": all_emotions,
            "mixed_emotions": mixed_emotions
        }
