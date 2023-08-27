import argparse
import ezdxf
import numpy as np

parser = argparse.ArgumentParser(description='Save coords of points from DXF file as NumPy arrays in .npz file')
parser.add_argument('filename', help='DXF file')
args = parser.parse_args()

print('Reading DXF...')
dwg = ezdxf.readfile(args.filename)
modelspace = dwg.modelspace()
points = modelspace.query('POINT[layer=="PY"]')
coords = [p.dxf.location for p in points]

print('Preparing numpy arrays...')
x = np.array([i[0] for i in coords])
y = np.array([i[1] for i in coords])
z = np.array([i[2] for i in coords])

print('Saving to file...')
np.savez(args.filename[:-4] + '.npz', x=x, y=y, z=z)
