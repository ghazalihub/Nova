# Nova Standard Library (Python side)
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
            return torch.randn(shape)
        return np.random.randn(*shape)

class DataFrame:
    def __init__(self, data):
        import pandas as pd
        self._df = pd.DataFrame(data)

    def where(self, condition_func):
        # In Nova, we can pass a lambda or a boolean series
        if callable(condition_func):
            return DataFrame(self._df[condition_func(self._df)])
        return DataFrame(self._df[condition_func])

    def select(self, *columns):
        return DataFrame(self._df[list(columns)])

    def avg_by(self, column):
        return DataFrame(self._df.groupby(column).mean())

    def __getattr__(self, name):
        return getattr(self._df, name)

    def __repr__(self):
        return repr(self._df)

def plot(x, y, type="scatter"):
    import matplotlib.pyplot as plt
    if type == "scatter":
        plt.scatter(x, y)
    else:
        plt.plot(x, y)
    plt.show()

class LazyProxy:
    def __init__(self, factory):
        self._factory = factory
        self._instance = None

    def _get_instance(self):
        if self._instance is None:
            self._instance = self._factory()
        return self._instance

    def __getattr__(self, name):
        return getattr(self._get_instance(), name)

    def __repr__(self):
        return repr(self._get_instance())

def train_loop(model, dataset, options=None):
    print(f"Starting training on {model} with {dataset}...")
    epochs = (options or {}).get("epochs", 5)
    for epoch in range(epochs):
        print(f"Epoch {epoch+1}/{epochs} complete.")
    print("Training finished.")

def dim_index(tensor, dim_name, index):
    # Proof of concept for dimension labeling
    print(f"Indexing tensor on dimension '{dim_name}' at index {index}")
    if hasattr(tensor, "select") and callable(tensor.select):
        return tensor.select(dim=dim_name, index=index)
    return tensor[index] # Fallback

# Export common names
__all__ = ["Tensor", "DataFrame", "plot", "LazyProxy", "train_loop", "dim_index"]
