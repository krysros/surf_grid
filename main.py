import argparse

import ezdxf
import matplotlib.pyplot as plt
import numpy as np
from ezdxf import zoom
from ezdxf.enums import TextEntityAlignment
from matplotlib import cm
from scipy.interpolate import griddata

parser = argparse.ArgumentParser(description="Plot surface")
parser.add_argument("filename", help="dxf file")
parser.add_argument("--layer", default=0, help="dxf layer")
parser.add_argument("--typ", default="CIRCLE", help="CIRCLE or POINT")
args = parser.parse_args()

print("Reading dxf...")

doc = ezdxf.readfile(args.filename)

doc.header["$PDMODE"] = 32
doc.header["$PDSIZE"] = 0.25

doc.styles.new("myStandard", dxfattribs={"font": "Arial.ttf"})
doc.layers.new(name="PY")

msp = doc.modelspace()
coords = []

match args.typ:
    case "CIRCLE":
        pts = msp.query(f'CIRCLE[layer=="{args.layer}"]')
        for p in pts:
            coords.append(p.dxf.center)
    case "POINT":
        pts = msp.query(f'POINT[layer=="{args.layer}"]')
        for p in pts:
            coords.append(p.dxf.location)

print("Interpolation...")

coords = np.array(coords)
points = coords[:, :2]
values = coords[:, 2]

min_x = np.min(coords[:, 0])
max_x = np.max(coords[:, 0])
min_y = np.min(coords[:, 1])
max_y = np.max(coords[:, 1])

delta_x = max_x - min_x
delta_y = max_y - min_y

step = 2
delta_x = np.around(delta_x / step)
delta_y = np.around(delta_y / step)

grid_x = np.arange(0, delta_x) * step + min_x
grid_y = np.arange(0, delta_y) * step + min_y

X, Y = np.meshgrid(grid_x, grid_y)
Z = griddata(points, values, (X, Y), method="linear")
Z = Z.T

print("Adding to dxf...")

num = 0
icoords = []
squares = []

for i, x in enumerate(grid_x):
    for j, y in enumerate(grid_y):
        num += 1
        msp.add_text(
            f"{num}",
            height=0.25,
            dxfattribs={"layer": "PY", "color": 4, "style": "myStandard"},
        ).set_placement((x + step / 2, y + step / 2), align=TextEntityAlignment.CENTER)
        z = Z[i, j]
        try:
            squares.append([num, Z[i, j], Z[i + 1, j], Z[i, j + 1], Z[i + 1, j + 1]])
        except IndexError:
            pass
        if not np.isnan(z):
            icoords.append((x, y, z))
            msp.add_point((x, y, z), dxfattribs={"layer": "PY", "color": 6})

print("Saving dxf...")

zoom.extents(msp)
doc.saveas(args.filename[:-4] + "_output.dxf")

squares = np.array(squares)
icoords = np.array(icoords)

x = icoords[:, 0]
y = icoords[:, 1]
z = icoords[:, 2]

print("Saving csv...")

np.savetxt(
    args.filename[:-4] + "_output.csv",
    squares,
    delimiter=";",
    fmt=["%i", "%10.4f", "%10.4f", "%10.4f", "%10.4f"],
    encoding="utf-8",
)

print("Plotting surface...")

fig = plt.figure()
ax = fig.add_subplot(projection="3d")
surf = ax.plot_trisurf(x, y, z, cmap=cm.terrain)
plt.show()
