import pytest

from .solr import strip_special_chars


@pytest.mark.parametrize('input,output', [
  ['', ''],
  [' ', ''],
  ['  ', ''],
  [' -+! ? ', ''],
  [' -+x! ?x ', 'x x'],
  [' o-+|n!)l([]\\"y:?/\'  ', 'o n l y'],
])
def test_strip_special_chars(input, output):
  assert strip_special_chars(input) == output
