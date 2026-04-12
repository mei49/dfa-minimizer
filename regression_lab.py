import torch
import torch.nn as nn

# 1. Setup Data as Tensors
# X = Hours Studied, y = Pass (1) or Fail (0)
X = torch.tensor([[0.5], [1.0], [2.0], [3.0], [4.0], [5.0]], dtype=torch.float32)
y = torch.tensor([[0], [0], [0], [1], [1], [1]], dtype=torch.float32)

# 2. Define the Architecture
class SimpleNN(nn.Module):
    def __init__(self):
        super(SimpleNN, self).__init__()
        self.linear = nn.Linear(1, 1)  # 1 input (hours), 1 output (pass/fail)
        self.sigmoid = nn.Sigmoid()    # Activation function to get probability

    def forward(self, x):
        return self.sigmoid(self.linear(x))

model = SimpleNN()

# 3. Define Loss (Binary Cross Entropy) and Optimizer (Stochastic Gradient Descent)
criterion = nn.BCELoss() 
optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

# 4. Training Loop
print("Training model...")
for epoch in range(500): # Increased epochs for better accuracy
    # Forward pass
    y_pred = model(X)
    loss = criterion(y_pred, y)
    
    # Backward pass (Backpropagation)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    if (epoch + 1) % 100 == 0:
        print(f'Epoch [{epoch+1}/500], Loss: {loss.item():.4f}')

print("\nPyTorch Model Trained!")

# --- 5. NEW: PREDICTION / INFERENCE ---
model.eval() # Set to evaluation mode
with torch.no_grad():
    test_val = torch.tensor([[3.5]], dtype=torch.float32)
    prediction = model(test_val)
    
    print("-" * 30)
    print(f"Prediction for 3.5 hours: {prediction.item():.4f}")
    print(f"Conclusion: {'PASS' if prediction.item() > 0.5 else 'FAIL'}")
    print("-" * 30)

# --- 6. NEW: LEARNED PARAMETERS ---
# This shows the weights and bias the model learned
print("\nFinal Learned Parameters (W and b):")
for name, param in model.named_parameters():
    print(f"{name}: {param.data.numpy()}")