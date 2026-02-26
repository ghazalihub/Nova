from src.nova.ai import *
from src.nova.data import *
from src.nova.eval import *
from src.nova.hardware import *
from src.nova.exp import *
from src.nova.viz import *
from src.nova.storage import *

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

def secret(name):
    import os
    print(f"Accessing secret: {name}")
    return os.getenv(name)

def llm(prompt):
    print(f"[Nova AI] Processing prompt: {prompt}")
    return "AI-generated result based on: " + prompt

def deploy_model(model, options):
    print(f"[Nova Deploy] Deploying {model} with options: {options}")
    return True

def taint(target):
    print(f"[Nova Safety] Tainting {target} for safety tracking")
    return target

__all__ = [
    "Tensor", "DataFrame", "Dataset", "plot", "LazyProxy", "train_loop", "dim_index",
    "classification_report", "confusion_matrix", "get_device", "gpu", "gpu_context",
    "start_run", "log_metric", "theme", "Dashboard", "llm", "secret", "read", "write",
    "save", "load", "freeze", "plot3d", "hist", "animate", "annotate", "show_map",
    "deploy_model", "taint"
]
