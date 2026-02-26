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
        return self._df[condition_func(self._df)]

    def __repr__(self):
        return repr(self._df)

def plot(x, y, type="scatter"):
    import matplotlib.pyplot as plt
    if type == "scatter":
        plt.scatter(x, y)
    else:
        plt.plot(x, y)
    plt.show()

# Export common names
__all__ = ["Tensor", "DataFrame", "plot"]
