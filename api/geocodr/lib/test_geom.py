from shapely.geometry import (
    Point,
    Polygon,
    LineString,
    MultiPoint,
    MultiPolygon,
    MultiLineString,
)

from .geom import point_on_geom


def test_point():
    p = Point(5, 5)
    assert point_on_geom(p) == Point(5, 5)


def test_multipoint():
    mp = MultiPoint([(0, 0), (5, 5), (10, 0)])
    assert point_on_geom(mp) == Point(5, 5)


def test_linestring():
    l = LineString([(0, 0), (10, 10)])
    assert point_on_geom(l) == Point(5, 5)

    l = LineString([(0, 0), (10, 0), (10, 10)])
    assert point_on_geom(l) == Point(10, 0),  point_on_geom(l).wkt

    l = LineString([(0, 0), (10, 0), (10, 10), (0, 10)])
    assert point_on_geom(l) == Point(10, 5),  point_on_geom(l).wkt


def test_multilinestring():
    ml = MultiLineString([
        LineString([(0, 0), (10, 0), (10, 10), (0, 10)]),
        LineString([(0, 20), (10, 20)]),
    ])
    assert point_on_geom(ml) == Point(10, 5),  point_on_geom(ml).wkt


def test_polygon():
    p = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    assert point_on_geom(p) == Point(5, 5)

    # L-shape, point in center of stem
    p = Polygon([(0, 0), (100, 0), (100, 10), (10, 10), (10, 100), (0, 100)])
    assert point_on_geom(p) == Point(5, 50), point_on_geom(p).wkt

    # U-shape, point in center of right stem, which is wider
    p = Polygon([(0, 0), (100, 0), (100, 100), (80, 100),
                 (80, 10), (10, 10), (10, 100), (0, 100)])
    assert point_on_geom(p) == Point(90, 50), point_on_geom(p).wkt


def test_multipolygon():
    # In center of largest
    p = MultiPolygon([
        Polygon([(20, 0), (20, 0), (20, 8), (20, 10)]),
        Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]),
        Polygon([(30, 0), (30, 0), (30, 5), (30, 10)]),
    ])
    assert point_on_geom(p) == Point(5, 5), point_on_geom(p).wkt
