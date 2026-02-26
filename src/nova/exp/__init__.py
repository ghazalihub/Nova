class Experiment:
    def __init__(self, project):
        self.project = project
        self.metrics = {}

    def log_metric(self, name, value):
        print(f"[Experiment {self.project}] Logging {name}: {value}")
        self.metrics[name] = value

_active_run = None

def start_run(name):
    global _active_run
    print(f"Starting experiment run: {name}")
    _active_run = Experiment(name)
    return _active_run

def log_metric(name, value):
    if _active_run:
        _active_run.log_metric(name, value)
    else:
        print(f"Warning: No active run. Metric {name} = {value} not saved.")

__all__ = ["start_run", "log_metric"]
