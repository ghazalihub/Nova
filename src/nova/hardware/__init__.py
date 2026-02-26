import torch

def get_device():
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"

import contextlib
def gpu(index=0):
    if torch.cuda.is_available():
        return torch.cuda.device(index)
    return contextlib.nullcontext()

gpu_context = gpu

__all__ = ["get_device", "gpu", "gpu_context"]
