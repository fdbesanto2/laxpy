import numpy as np
from numba import vectorize, bool_, float64

def ray_trace(x, y, poly):
    """
    A numba implementation of the ray tracing algorithm.
    :param x: A 1D numpy array of x coordinates.
    :param y: A 1D numpy array of y coordinates.
    :param poly: The coordinates of a polygon as a numpy array (i.e. from geo_json['coordinates']
    :return:
    """

    poly = np.stack((poly.exterior.coords.xy[0],
                            poly.exterior.coords.xy[1]), axis = 1)

    @vectorize([bool_(float64, float64)])
    def ray(x, y):
        # where xy is a coordinate
        n = len(poly)
        inside = False
        p2x = 0.0
        p2y = 0.0
        xints = 0.0
        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
    return(ray(x, y))
