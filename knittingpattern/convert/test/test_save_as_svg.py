from test import *
from knittingpattern import load_from_relative_file
import untangle
from itertools import chain
import re

INKSCAPE_MESSAGE = "row is usable by inkscape"
TRANSFORM_REGEX = "^translate\(\s*(\S+?)\s*,\s*(\S+?)\s*\)\s*,"\
                  "\s*scale\(\s*(\S+?)\s*\)$"
ZOOM_MESSAGE = "zoom is computed from height"
DEFAULT_ZOOM = 25


def is_close_to(v1, v2, relative_epsilon=0.01):
    return v2 * (1 - relative_epsilon) < v1 < v2 * (1 + relative_epsilon)


@fixture(scope="module")
def patterns():
    return load_from_relative_file(__name__, "test_patterns/block4x4.json")


@fixture(scope="module")
def path(patterns):
    return patterns.to_svg(zoom=DEFAULT_ZOOM).temporary_path(".svg")


@fixture(scope="module")
def svg(path):
    return untangle.parse(path).svg


@fixture
def rows(svg):
    return [("row-{}".format(i), row) for i, row in enumerate(svg.g, 1)]


@fixture
def instructions(rows):
    return chain(*(row.g for _, row in rows))


def rows_test(function):
    def test(rows):
        for row_id, row in rows:
            function(row_id, row)
    return test


def instructions_test(function):
    def test(instructions):
        for instruction in instructions:
            function(instruction)
    return test


def test_svg_contains_four_rows(svg):
    assert len(svg.g) == 4


@rows_test
def test_rows_contain_four_instructions(row_id, row):
    assert len(row.g) == 4


@rows_test
def test_rows_are_labeled_for_inkscape(row_id, row):
    assert row["inkscape:label"] == row_id


@rows_test
def test_row_is_inkscape_layer(row_id, row):
    assert row["inkscape:groupmode"] == "layer"


@rows_test
def test_rows_have_class_for_styling(row_id, row):
    assert row["class"] == "row"


@rows_test
def test_rows_have_id_for_styling(row_id, row):
    assert row["id"] == row_id


@instructions_test
def test_instructions_have_class(instruction):
    assert instruction["class"] == "instruction"


@instructions_test
def test_instructions_have_id(instruction):
    # TODO all ids should be made up from the real ids
    assert instruction["id"].startswith("instruction-")


@instructions_test
def test_instructions_content_is_knit_svg_file(instruction):
    assert instruction.g.title == "knit"


@instructions_test
def test_instructions_have_transform(instruction):
    transform = instruction["transform"]
    x, y, zoom = map(float, re.match(TRANSFORM_REGEX, transform).groups())
    svg = instruction.g
    min_x, min_y, max_x, max_y = map(float, svg["viewBox"].split())
    min_zoom = zoom * 0.99  # rounding errors
    max_zoom = zoom * 1.01
    assert is_close_to(DEFAULT_ZOOM / (max_y - min_y), zoom), ZOOM_MESSAGE
