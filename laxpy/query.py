# will hold functions for querying cell indices from a .las/x pair
from laspy.file import File
import os.path
import ntpath
from laxpy import file, tree
from numpy.lib.recfunctions import append_fields
from laxpy import file, tree, clip
from shapely.geometry import Point, Polygon
import numpy as np
import copy

class IndexedLAS(File):
    """
    The main interface for interacting with indexed `.las` files. An `IndexedLAS` wraps a `laspy.file.File`
    and thereby has all of its functionality. When this class is initialized it checks if an existing `.lax` file that
    matches the name of the input `.las` file exists in the same directory. If not such file exists please use `lasindex`
    to create a matching `.lax` file.

    :param path: The path of a `.las` file to index.
    """
    def __init__(self, path):
        super().__init__(path)

        # Copy original points memory map
        self.original_points = copy.copy(self.reader.data_provider._pmap)

        # Check if matching `.lax` file is present.
        parent_dir = os.path.join(os.path.abspath(os.path.join(self.filename, os.pardir)))
        las_name = os.path.splitext(ntpath.basename(self.filename))[0]
        self.lax_path = os.path.join(parent_dir, las_name + '.lax')

        if not os.path.isfile(self.lax_path):
            raise FileNotFoundError('A matching .lax file was not found.')

        # Parse the lax file and generate the tree
        self.parser = file.LAXParser(self.lax_path)
        self.tree = tree.LAXTree(self.parser)

    def _query_cell(self, cell_index):
        """
        Returns the point indices of a given cell index. This is generally used internally.

        :param cell_index:
        :return:
        """

        point_indices = self.parser.create_point_indices(cell_index)
        return point_indices

    #@profile
    def map_polygon(self, q_polygon):
        """
        Sets the point mapping to the query polygon. Subsequent laspy-esque calls will therefore return only points
        within the polygon. E.g. `my_las.x` will return only the x-values for points within the polygon, etc. This
        modifies the object's reader point mapping in place. See `self.original_points` for a copy of the original
        point mapping.

        :param q_polygon: A shapely polygon to query.
        """
        point_indices = []
        for cell_index, polygon in self.tree.cell_polygons.items():
            if q_polygon.intersects(polygon):
                point_indices.append(self.parser.create_point_indices(cell_index))


        point_indices = np.unique(np.concatenate(point_indices))

        x_scale, y_scale, z_scale = self.header.scale
        x_off, y_off, z_off = self.header.offset

        x = (x_scale * self.original_points[point_indices]['point']['X']) + x_off
        y = (y_scale * self.original_points[point_indices]['point']['Y']) + y_off

        keep = clip.ray_trace(x, y, q_polygon)

        self.reader.data_provider._pmap = self.original_points[np.where(keep)[0]]
