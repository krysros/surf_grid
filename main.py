import argparse
import logging
import sys
from pathlib import Path

import ezdxf
import matplotlib.pyplot as plt
import numpy as np
from ezdxf import zoom
from ezdxf.enums import TextEntityAlignment
from matplotlib import cm
from scipy.interpolate import griddata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

VALID_TYPES = ["CIRCLE", "POINT"]
STEP = 2
TEXT_HEIGHT = 0.25
TEXT_COLOR = 4
POINT_COLOR = 6
DELIMITER = ";"


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Plot surface from DXF coordinates")
    parser.add_argument("filename", help="DXF file path")
    parser.add_argument("--layer", default=0, help="DXF layer name/number (default: 0)")
    parser.add_argument("--typ", default="CIRCLE", help=f"Entity type: {', '.join(VALID_TYPES)} (default: CIRCLE)")
    parser.add_argument("--step", type=float, default=STEP, help=f"Grid step size (default: {STEP})")
    return parser.parse_args()


def validate_input(filename, entity_type):
    """Validate input parameters."""
    # Validate file exists
    if not Path(filename).exists():
        raise FileNotFoundError(f"DXF file not found: {filename}")
    
    # Validate entity type
    if entity_type not in VALID_TYPES:
        raise ValueError(f"Invalid entity type '{entity_type}'. Must be one of: {', '.join(VALID_TYPES)}")


def read_coordinates(doc, layer, entity_type):
    """Extract coordinates from DXF entities."""
    logger.info(f"Reading {entity_type} entities from layer '{layer}'...")
    msp = doc.modelspace()
    coords = []
    
    try:
        if entity_type == "CIRCLE":
            pts = msp.query(f'CIRCLE[layer=="{layer}"]')
            for p in pts:
                coords.append(p.dxf.center)
        elif entity_type == "POINT":
            pts = msp.query(f'POINT[layer=="{layer}"]')
            for p in pts:
                coords.append(p.dxf.location)
        
        if not coords:
            raise ValueError(f"No {entity_type} entities found on layer '{layer}'")
        
        logger.info(f"Found {len(coords)} coordinates")
        return coords
    except Exception as e:
        logger.error(f"Failed to read coordinates: {e}")
        raise


def interpolate_surface(coords, step):
    """Perform surface interpolation on coordinates."""
    logger.info("Performing surface interpolation...")
    
    try:
        coords = np.array(coords)
        if coords.shape[1] < 3:
            raise ValueError("Coordinates must have X, Y, Z values")
        
        points = coords[:, :2]
        values = coords[:, 2]
        
        min_x = np.min(coords[:, 0])
        max_x = np.max(coords[:, 0])
        min_y = np.min(coords[:, 1])
        max_y = np.max(coords[:, 1])
        
        delta_x = max_x - min_x
        delta_y = max_y - min_y
        
        delta_x = int(np.around(delta_x / step))
        delta_y = int(np.around(delta_y / step))
        
        grid_x = np.arange(0, delta_x) * step + min_x
        grid_y = np.arange(0, delta_y) * step + min_y
        
        X, Y = np.meshgrid(grid_x, grid_y)
        Z = griddata(points, values, (X, Y), method="linear")
        Z = Z.T
        
        logger.info(f"Grid created: {delta_x}x{delta_y} cells")
        return grid_x, grid_y, Z
    except Exception as e:
        logger.error(f"Interpolation failed: {e}")
        raise


def add_grid_to_dxf(msp, doc, grid_x, grid_y, Z, step):
    """Add interpolated grid to DXF document."""
    logger.info("Adding grid to DXF...")
    
    try:
        # Setup style and layer
        doc.header["$PDMODE"] = 32
        doc.header["$PDSIZE"] = 0.25
        doc.styles.new("myStandard", dxfattribs={"font": "Arial.ttf"})
        doc.layers.new(name="PY")
        
        num = 0
        icoords = []
        squares = []
        
        for i, x in enumerate(grid_x):
            for j, y in enumerate(grid_y):
                num += 1
                
                # Add text label
                msp.add_text(
                    f"{num}",
                    height=TEXT_HEIGHT,
                    dxfattribs={"layer": "PY", "color": TEXT_COLOR, "style": "myStandard"},
                ).set_placement((x + step / 2, y + step / 2), align=TextEntityAlignment.CENTER)
                
                z = Z[i, j]
                
                # Store square data
                try:
                    squares.append([num, Z[i, j], Z[i + 1, j], Z[i, j + 1], Z[i + 1, j + 1]])
                except IndexError:
                    pass
                
                # Add valid points
                if not np.isnan(z):
                    icoords.append((x, y, z))
                    msp.add_point((x, y, z), dxfattribs={"layer": "PY", "color": POINT_COLOR})
        
        logger.info(f"Added {num} grid cells")
        return squares, icoords
    except Exception as e:
        logger.error(f"Failed to add grid to DXF: {e}")
        raise


def save_outputs(doc, msp, filename, squares, icoords):
    """Save DXF and CSV output files."""
    try:
        # Save DXF
        output_dxf = Path(filename).stem + "_output.dxf"
        logger.info(f"Saving DXF to {output_dxf}...")
        zoom.extents(msp)
        doc.saveas(output_dxf)
        
        # Save CSV
        if len(squares) > 0:
            output_csv = Path(filename).stem + "_output.csv"
            logger.info(f"Saving CSV to {output_csv}...")
            squares_array = np.array(squares)
            np.savetxt(
                output_csv,
                squares_array,
                delimiter=DELIMITER,
                fmt=["%i", "%10.4f", "%10.4f", "%10.4f", "%10.4f"],
                encoding="utf-8",
            )
        
        return output_dxf, output_csv
    except Exception as e:
        logger.error(f"Failed to save outputs: {e}")
        raise


def plot_surface(icoords):
    """Plot 3D surface visualization."""
    try:
        if len(icoords) == 0:
            logger.warning("No valid coordinates to plot")
            return
        
        logger.info("Plotting surface...")
        icoords = np.array(icoords)
        x = icoords[:, 0]
        y = icoords[:, 1]
        z = icoords[:, 2]
        
        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")
        ax.plot_trisurf(x, y, z, cmap=cm.terrain)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title("Surface Reconstruction")
        plt.show()
    except Exception as e:
        logger.error(f"Failed to plot surface: {e}")


def main():
    """Main execution function."""
    try:
        args = parse_arguments()
        validate_input(args.filename, args.typ)
        
        # Read DXF
        logger.info(f"Reading DXF file: {args.filename}")
        doc = ezdxf.readfile(args.filename)
        msp = doc.modelspace()
        
        # Extract and interpolate
        coords = read_coordinates(doc, args.layer, args.typ)
        grid_x, grid_y, Z = interpolate_surface(coords, args.step)
        
        # Add to DXF
        squares, icoords = add_grid_to_dxf(msp, doc, grid_x, grid_y, Z, args.step)
        
        # Save outputs
        save_outputs(doc, msp, args.filename, squares, icoords)
        
        # Visualize
        plot_surface(icoords)
        
        logger.info("Process completed successfully")
        
    except Exception as e:
        logger.error(f"Process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
