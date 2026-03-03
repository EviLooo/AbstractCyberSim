import mesa
print("Mesa version:", mesa.__version__)
try:
    from mesa.visualization import SolaraViz
    print("SolaraViz found!")
except ImportError:
    print("SolaraViz not in mesa.visualization")

try:
    from mesa.visualization import make_plot_component
    print("make_plot_component found!")
except ImportError:
    print("make_plot_component not found")

try:
    from mesa.visualization import SpaceRenderer
    print("SpaceRenderer found!")
except ImportError:
    print("SpaceRenderer not found")
