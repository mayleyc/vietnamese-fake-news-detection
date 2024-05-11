# -*- coding: utf-8 -*-
"""240508 hlt project 6.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1YmIv6gM0u_macKkoSuVDZXkjc4XK8Hc9
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from transformers import AutoModel, AutoTokenizer
from sklearn.model_selection import KFold
from matplotlib import pyplot as plt

# build SVM fake news detection and compare with PhoBERT
# https://github.com/VFND/VFND-vietnamese-fake-news-datasets

device = 'cuda' if torch.cuda.is_available() else 'cpu'

#With 10-fold

# Load pre-trained model and tokenizer
model = AutoModel.from_pretrained("vinai/phobert-base-v2").to(device)
tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base-v2")

# Define classification head
class ClassificationHead(nn.Module):
    def __init__(self, input_size, num_labels):
        super(ClassificationHead, self).__init__()
        
        # Dropout layer to prevent overfitting
        self.dropout = nn.Dropout(0.1)
        
        # Fully connected layer to map input features to output labels
        self.fc = nn.Linear(input_size, num_labels)

    def forward(self, x):
        # Apply dropout to the input tensor
        x = self.dropout(x)
        
        # Pass the dropout-applied tensor through the fully connected layer
        x = self.fc(x)
        
        # Return the output tensor
        return x


# Add classification head to the model
num_labels = 2  # Real/Fake classes for classification
classification_head = ClassificationHead(model.config.hidden_size, num_labels).to(device)
model.classification_head = classification_head

# Define loss function and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.AdamW(model.parameters(), lr=1e-5)

# List of file paths
folder_path = 'txt/train'

losses = []

# Define number of folds for cross-validation
num_folds = 10
kf = KFold(n_splits=num_folds, shuffle=True)

# Training loop with k-fold cross-validation
for fold, (train_indices, val_indices) in enumerate(kf.split(os.listdir(folder_path))):
    print(f"Fold {fold + 1}/{num_folds}")

    # Split data into training and validation sets for this fold
    train_files = [os.listdir(folder_path)[i] for i in train_indices]
    val_files = [os.listdir(folder_path)[i] for i in val_indices]

    # Training loop for each file in training set
    for filename in train_files:
        # Skip non-text files
        if not filename.endswith(".txt"):
            continue
        file_path = os.path.join(folder_path, filename)
        # Read the content of the file
        with open(file_path, 'r') as input_file:
            text = input_file.read()

        # Extract label from file name
        label = 1 if "fake" in file_path.lower() else 0

        # Tokenize and encode the text
        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=256).to(device)

        # Convert the label to tensor
        label_tensor = torch.tensor([label]).to(device)

        # Custom training loop
        model.train()
        # Clear gradients
        optimizer.zero_grad()
        # Forward pass
        outputs = model(**inputs)
        last_hidden_state = outputs.last_hidden_state
        logits = classification_head(last_hidden_state[:, 0, :])
        # Find the loss
        loss = criterion(logits, label_tensor)
        # Calculate gradients
        loss.backward()
        # Update weights
        optimizer.step()

        # Print the loss
        print(f"Training Loss for {filename}: {loss.item()}")
        losses.append(loss.item())

    # Validation loop for each file in validation set
    val_losses = []
    for filename in val_files:
        # Skip non-text files
        if not filename.endswith(".txt"):
            continue
        file_path = os.path.join(folder_path, filename)
        # Read the content of the file
        with open(file_path, 'r') as input_file:
            text = input_file.read()

        # Extract label from file name
        label = 1 if "fake" in file_path.lower() else 0

        # Tokenize and encode the text
        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=256).to(device)

        # Convert the label to tensor
        label_tensor = torch.tensor([label]).to(device)

        # Validation
        model.eval()
        with torch.no_grad():
            outputs = model(**inputs)
            last_hidden_state = outputs.last_hidden_state
            logits = classification_head(last_hidden_state[:, 0, :])
            val_loss = criterion(logits, label_tensor)
            val_losses.append(val_loss.item())

    avg_val_loss = sum(val_losses) / len(val_losses)
    print(f"Avg Validation Loss for Fold {fold + 1}: {avg_val_loss}")

# Save model checkpoint at the end (approx. 1.5GB)
'''checkpoint_path = "final_model_checkpoint.pt"
torch.save({
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'avg_val_loss': avg_val_loss,
    'train_losses': losses
}, checkpoint_path)
print(f"Final model checkpoint saved at {checkpoint_path}")'''

# Plot the losses if needed 
'''plt.plot(losses, label='training_loss')
plt.legend()
plt.show()''' 


# Define a single evaluation text and its label
# Load model checkpoint
'''checkpoint = torch.load(checkpoint_path)
model.load_state_dict(checkpoint['model_state_dict'])'''

#Set model to evaluation state
model.eval()

def evaluate(dir):
  with open(dir, 'r') as f:
      evaluation_text = f.read()
      #Read the label from the filename
      evaluation_label = 1 if "fake" in dir.lower() else 0

  # Tokenize and encode the evaluation text
  evaluation_encoding = tokenizer(evaluation_text, return_tensors='pt', truncation=True, padding=True, max_length=256).to(device)

  # Convert the label to a tensor
  evaluation_label_tensor = torch.tensor([evaluation_label]).to(device)

  # Forward pass
  with torch.no_grad():
      outputs = model(**evaluation_encoding)
      pooled_output = outputs.pooler_output  # Pooled output from the [CLS] token
      logits = model.classification_head(pooled_output)

  # Generate predictions
  prediction = torch.argmax(logits, dim=1).item()

  # Compute accuracy: if prediction aligns with evaluation_label_tensor, then it's True
  accuracy = (prediction == evaluation_label_tensor.item())
  return accuracy
    
#Iterate over folder
folder = 'txt/test'
total_acc = 0
for item in os.listdir(folder):
  dir = os.path.join(folder, item)
  acc = evaluate(dir)
  if acc:
    total_acc += 1
  print(acc)
percent = total_acc/len(os.listdir(folder))
print(percent)
