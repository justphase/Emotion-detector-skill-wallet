import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from datasets import load_dataset
import json
import collections
import os
from bilstm_model import BiLSTMClassifier, tokenize, text_to_indices, clean_text, EMOTIONS

# Map GoEmotions indices to our 5 target emotions:
# 27: neutral, 9: disappointment, 25: sadness -> Bored
# 4: approval, 21: pride, 0: admiration, 20: optimism -> Confident
# 6: confusion -> Confused
# 7: curiosity -> Curious
# 3: annoyance, 2: anger, 10: disapproval -> Frustrated
MAPPING = {
    "Bored": [27, 9, 25],
    "Confident": [4, 21, 0, 20],
    "Confused": [6],
    "Curious": [7],
    "Frustrated": [3, 2, 10]
}

class EmotionDataset(Dataset):
    def __init__(self, samples, vocab, max_len=50):
        self.samples = samples
        self.vocab = vocab
        self.max_len = max_len
        
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        text, label_idx = self.samples[idx]
        indices = text_to_indices(text, self.vocab, self.max_len)
        return torch.tensor(indices, dtype=torch.long), torch.tensor(label_idx, dtype=torch.long)

def build_dataset_subset():
    print("Loading google-research-datasets/go_emotions train dataset...")
    # Load all splits of go_emotions to guarantee we find enough samples
    splits = ["train", "validation", "test"]
    ds_parts = []
    for s in splits:
        try:
            ds_parts.append(load_dataset("google-research-datasets/go_emotions", split=s))
        except Exception as e:
            print(f"Warning: could not load split {s}: {e}")
            
    # Keep track of collected samples per category (target size: 250 each)
    samples_by_emotion = {e: [] for e in EMOTIONS}
    target_count = 250
    
    for ds in ds_parts:
        for item in ds:
            labels = item["labels"]
            text = item["text"]
            
            # Find which of our target emotions matches this sample
            matched_targets = []
            for target_emotion, source_labels in MAPPING.items():
                if any(l in source_labels for l in labels):
                    matched_targets.append(target_emotion)
            
            # Use only unambiguous single-label mappings for training quality
            if len(matched_targets) == 1:
                emotion = matched_targets[0]
                if len(samples_by_emotion[emotion]) < target_count:
                    samples_by_emotion[emotion].append(text)
                    
            # Check if we have collected enough samples for all emotions
            if all(len(v) >= target_count for v in samples_by_emotion.values()):
                break
                
        if all(len(v) >= target_count for v in samples_by_emotion.values()):
            break

    # Print summary
    print("Collected training samples per target emotion:")
    for e, v in samples_by_emotion.items():
        print(f"  {e}: {len(v)} samples")
        
    # Combine into a single list of (text, label_index)
    train_samples = []
    for emotion, texts in samples_by_emotion.items():
        label_idx = EMOTIONS.index(emotion)
        for t in texts:
            train_samples.append((t, label_idx))
            
    return train_samples

def train():
    # Build the dataset
    samples = build_dataset_subset()
    
    # Build vocabulary
    print("Building vocabulary...")
    word_counts = collections.Counter()
    for text, _ in samples:
        word_counts.update(tokenize(text))
        
    # Create vocab mapping: 0 for <pad>, 1 for <unk>
    vocab = {"<pad>": 0, "<unk>": 1}
    for word, count in word_counts.items():
        # Keep words that appear at least once to cover our tiny dataset fully
        if count >= 1:
            vocab[word] = len(vocab)
            
    print(f"Vocabulary size: {len(vocab)}")
    
    # Save vocabulary
    vocab_path = "vocab.json"
    with open(vocab_path, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)
    print(f"Vocabulary saved to {vocab_path}")
    
    # DataLoader
    dataset = EmotionDataset(samples, vocab)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    # Initialize model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training BiLSTM model on device: {device}")
    
    model = BiLSTMClassifier(vocab_size=len(vocab))
    model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.005)
    
    # Training Loop
    epochs = 8
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        correct = 0
        total = 0
        for texts, labels in dataloader:
            texts, labels = texts.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(texts)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item() * len(labels)
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total += len(labels)
            
        epoch_loss = total_loss / total
        epoch_acc = correct / total
        print(f"Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f} - Accuracy: {epoch_acc:.4f}")
        
    # Save weights
    model_path = "bilstm_model.pth"
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train()
