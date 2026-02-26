import numpy as np
try:
    import torch
except ImportError:
    torch = None

class Tensor:
    def __init__(self, data):
        self._data = np.array(data)

    def __repr__(self):
        return f"Nova.Tensor({self._data})"

    @staticmethod
    def randn(shape):
        if torch:
            return torch.randn(shape, requires_grad=True)
        return np.random.randn(*shape)

def train_loop(model, dataset, options=None):
    print(f"Starting training on {model} with {dataset}...")
    epochs = (options or {}).get("epochs", 5)
    for epoch in range(epochs):
        print(f"Epoch {epoch+1}/{epochs} complete.")
    print("Training finished.")

def save(model, path):
    print(f"Saving model to {path}...")
    if torch:
        torch.save(model.state_dict(), path)

def load(model, path):
    print(f"Loading model from {path}...")
    if torch:
        model.load_state_dict(torch.load(path))

def freeze(model, layer_name=None):
    print(f"Freezing {layer_name or 'all'} layers...")
    if torch:
        for name, param in model.named_parameters():
            if layer_name is None or layer_name in name:
                param.requires_grad = False

def dim_index(tensor, dim_name, index):
    print(f"Indexing tensor on dimension '{dim_name}' at index {index}")
    if hasattr(tensor, "select") and callable(tensor.select):
        return tensor.select(dim=dim_name, index=index)
    return tensor[index]

def relu(x):
    if torch:
        return torch.nn.functional.relu(x)
    return np.maximum(0, x)

def sigmoid(x):
    if torch:
        return torch.nn.functional.sigmoid(x)
    return 1 / (1 + np.exp(-x))

__all__ = ["Tensor", "train_loop", "dim_index", "relu", "sigmoid", "save", "load", "freeze"]
