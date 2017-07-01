import numpy as np
from scipy.spatial import ConvexHull  # First thought this warning was caused by a pythonpath problem, but it seems more likely that the warning is caused by scipy import hackery. pylint: disable=no-name-in-module
from blmath.geometry import Polyline
from blmath.geometry.transform.rotation import estimate_normal, rotate_to_xz_plane
from blmath.geometry.transform.translation import translation

def convexify_planar_curve(polyline, flatten=False, want_vertices=False, normal=None):
    '''
    Take the convex hull of an almost planar 2-D curve in three-space.

    Params:
        - polyline:
            An instance of Polyline.
        - flatten:
            Boolean; if True, rotated curve will be flattened
            on the y-axis, thereby losing length. This loss
            may not be offset by the convex hull.
        - want_vertices:
            Boolean; do you want the indices to the convex hull vertices?
    '''
    if flatten:
        return convexify_and_flatten_planar_curve(polyline, want_vertices, normal)

    v = polyline.v
    if len(v) <= 1:
        return polyline

    if normal is None:
        normal = estimate_normal(v)

    # to call ConvexHull, the points must be projected to a plane.
    # with an eye toward numerical stability, this can be done by dropping 
    # whichever dimension is closest to the normal
    dim_to_drop = np.argmax(np.abs(normal))
    dims_to_keep = [i for i in range(3) if i != dim_to_drop]
    proj_v = v[:, dims_to_keep]

    hull_vertices = ConvexHull(proj_v).vertices
    result = Polyline(v=v[hull_vertices], closed=polyline.closed)

    if want_vertices:
        return result, hull_vertices
    else:
        return result

def convexify_and_flatten_planar_curve(polyline, want_vertices=False, normal=None):
    '''
    Take the convex hull of an almost planar 2-D curve in three-space.

    Params:
        - polyline:
            An instance of Polyline.
        - flatten:
            Boolean; if True, rotated curve will be flattened
            on the y-axis, thereby losing length. This loss
            may not be offset by the convex hull.
        - want_vertices:
            Boolean; do you want the indices to the convex hull vertices?
    '''
    if len(polyline.v) <= 1:
        return polyline

    rotated, R, p0 = rotate_to_xz_plane(polyline.v, normal=normal)

    if flatten:
        rotated[:, 1] = np.mean(rotated[:, 1])

    projected = rotated[:, [0, 2]]

    hull_vertices = ConvexHull(projected).vertices
    rotated_hull = rotated[hull_vertices]

    R_inv = np.array(np.mat(R.T).I)
    inv_rotated = np.dot(rotated_hull, R_inv)

    if p0 is not None:
        curve_hull = translation(np.array(inv_rotated), -p0)[0] # pylint: disable=invalid-unary-operand-type
    else:
        curve_hull = inv_rotated

    result = Polyline(v=curve_hull, closed=polyline.closed)

    if want_vertices:
        return result, hull_vertices
    else:
        return result
