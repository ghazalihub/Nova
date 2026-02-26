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

def plot3d(x, y, z):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(x, y, z)
    plt.show()

def hist(data):
    plt.hist(data)
    plt.show()

def animate(series):
    print("Animating series...")

def annotate(text, pos):
    plt.annotate(text, pos)

def show_map(df):
    print("Displaying interactive map...")

__all__ = ["theme", "Dashboard", "plot", "plot3d", "hist", "animate", "annotate", "show_map"]
