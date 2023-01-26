import pytest

from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from .keys import APIKeys


@pytest.fixture()
def key_file(tmpdir):
  key_file = tmpdir.join("keys.csv")
  key_file.write(
    'key,domains\n'
    'wildcard,\n'
    '# comment,with,commas,\n'
    'multi,example.org;example.com\n'
    'single,test.local'
  )
  yield key_file.strpath


@pytest.mark.parametrize("key,referrer,permitted", [
  ["single", None, True],
  ["single", "", True],
  ["single", "--", True],
  ["single", "http", True],
  ["single", "http://", True],
  ["single", "test.local", True],
  ["single", "http://test.local", True],
  ["single", "https://test.local", True],
  ["single", "http://sub.test.local/path?arg=1", True],
  ["single", "http://sub.test.local", True],
  ["single", "https://subtest.local", False],
  ["single", "http://sub.test.local.com", False],
  ["single", "https://1.2.3.4", False],
  ["multi", "https://example.org", True],
  ["multi", "https://example.com", True],
  ["multi", "https://example.net", False],
  ["wildcard", "https://example.net", True],
  ["wildcard", "https://1.2.3.4", True],

])
def test_api_key(key_file, key, referrer, permitted):
  a = APIKeys(key_file)
  headers = []
  if referrer:
    headers.append(('Referer', referrer))
  builder = EnvironBuilder(method='GET', query_string={'key': key}, headers=headers)
  req = Request(builder.get_environ())
  assert a.is_permitted(req) == permitted
