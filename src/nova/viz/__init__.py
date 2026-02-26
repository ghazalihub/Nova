import matplotlib.pyplot as plt

def theme(name="dark"):
    if name == "dark":
        plt.style.use('dark_background')
    else:
        plt.style.use('default')

class Dashboard:
    def __init__(self, title):
        self.title = title
        print(f"Created Dashboard: {self.title}")

    def add_plot(self, plot_func):
        print(f"Adding plot to dashboard {self.title}")
        plot_func()

def plot(data, type="scatter"):
    if type == "scatter":
        plt.scatter(range(len(data)), data)
    else:
        plt.plot(data)
    plt.show()

__all__ = ["theme", "Dashboard", "plot"]
