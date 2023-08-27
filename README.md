# README

Surface reconstruction from scattered data points.

The input data (xyz coordinates of points) is read from the dxf file. On their basis, interpolation of surfaces (e.g. terrain surfaces) is performed. The results in the form of a grid of squares are saved in a dxf file on separate layer and a csv file. These data can be used to calculate the volume of earthworks using the square method. You can also visualize the reconstructed surface using a [skar.py](https://github.com/krysros/skarpy.git).

## Installation

```console
python -m pip install -r requirements.txt
```

## Calculations

```console
python main.py
```