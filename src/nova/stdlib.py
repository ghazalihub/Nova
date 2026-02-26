from src.nova.ai import *
from src.nova.data import *
from src.nova.eval import *

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

def plot(x, y, type="scatter"):
    import matplotlib.pyplot as plt
    if type == "scatter":
        plt.scatter(x, y)
    else:
        plt.plot(x, y)
    plt.show()

__all__ = ["Tensor", "DataFrame", "plot", "LazyProxy", "train_loop", "dim_index", "classification_report", "confusion_matrix"]
