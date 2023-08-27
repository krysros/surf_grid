import argparse
import numpy as np

parser = argparse.ArgumentParser(description='Plot surface')
parser.add_argument('filename', help='npz file')
parser.add_argument('--backend', default='matplotlib', help='matplotlib or plotly')
args = parser.parse_args()

with np.load(args.filename) as npzfile:
    x = npzfile['x']
    y = npzfile['y']
    z = npzfile['z']

if args.backend == 'matplotlib':

    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import cm
    matplotlib.use('qtagg')

    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    surf = ax.plot_trisurf(x, y, z, cmap=cm.terrain)
    plt.show()

elif args.backend == 'plotly':

    from plotly.graph_objects import Figure
    from plotly.graph_objects import Mesh3d

    fig = Figure(data=[Mesh3d(x=x, y=y, z=z, opacity=0.5)])
    fig.show()

else:
    print('Unknown backend')
