# README

Surface reconstruction from scattered data points.

The input data (xyz coordinates of points) is read from the dxf file. On their basis, interpolation of surfaces (e.g. terrain surfaces) is performed. The results in the form of a grid of squares are saved in a dxf file on separate layer and a csv file. These data can be used to calculate the volume of earthworks using the square method.

## Installation

```console
python -m pip install -r requirements.txt
```

## Calculations

```console
python main.py
```

## Visualization

You can also visualize the reconstructed surface.

```console
python dxf2npz.py output.dxf
python skar.py output.npz
```