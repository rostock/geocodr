import pytest

from .search import (
  SimpleField,
  NGramField,
  GermanNGramField,
  PrefixField,
  Only,
  is_exclusive,
)


@pytest.mark.parametrize('input,boost,output', [
  ['', None, None],
  ['st', None, None],
  ['str', None, "{!edismax qf=gramfield v='str' mm='2<-1 4<-2 6<-3 8<-4'}^1.0"],
  ['stral', None, "{!edismax qf=gramfield v='str tra ral' mm='2<-1 4<-2 6<-3 8<-4'}^0.33"],
  ['strals', None, "{!edismax qf=gramfield v='str tra ral als' mm='2<-1 4<-2 6<-3 8<-4'}^0.25"],
  ['strals', 2.0, "{!edismax qf=gramfield v='str tra ral als' mm='2<-1 4<-2 6<-3 8<-4'}^0.5"],
])
def test_ngram(input, boost, output):
  f = NGramField('gramfield') ^ (boost or 1.0)
  assert f.query(input) == output


@pytest.mark.parametrize('input,boost,output', [
  ['', None, None],
  ['aß', None, "{!edismax qf=gramfield v='ass' mm='2<-1 4<-2 6<-3 8<-4'}^1.0"],
  ['aßa', None, "{!edismax qf=gramfield v='ass ssa' mm='2<-1 4<-2 6<-3 8<-4'}^0.5"],
  ['laekoerue', None,
   "{!edismax qf=gramfield v='lak ako kor oru' mm='2<-1 4<-2 6<-3 8<-4'}^0.25"],
  ['quer', 2.0, "{!edismax qf=gramfield v='que uer' mm='2<-1 4<-2 6<-3 8<-4'}^1.0"],
])
def test_german_ngram(input, boost, output):
  f = GermanNGramField('gramfield') ^ (boost or 1.0)
  assert f.query(input) == output


@pytest.mark.parametrize('input,boost,output', [
  ['', None, None],
  ['str', None, "simplefield:str"],
  ['stra', None, "simplefield:stra"],
  ['stral', None, "simplefield:stral"],
  ['strals', 2.0, "simplefield:strals^2.0"],
])
def test_simple(input, boost, output):
  f = SimpleField('simplefield') ^ (boost or 1.0)
  assert f.query(input) == output


@pytest.mark.parametrize('input,min,boost,output', [
  ['', None, None, None],
  ['str', None, None, None],
  ['str', 4, None, None],
  ['str', 3, None, "prefixfield:str*"],
  ['stra', 4, None, "prefixfield:stra*"],
  ['stral', 4, None, "prefixfield:stral*"],
  ['strals', 4, 2.0, "prefixfield:strals*^2.0"],
])
def test_prefix(input, min, boost, output):
  if min:
    f = PrefixField('prefixfield', min)
  else:
    f = PrefixField('prefixfield')
  if boost:
    f ^ boost
  assert f.query(input) == output


@pytest.mark.parametrize('input,check,output', [
  ['', 'x', None],
  ['1234', r'^\d+$', 'field:1234'],
  ['12a4', r'^\d+$', None],
])
def test_only(input, check, output):
  f = Only(check, SimpleField('field'))
  q = f.query(input)
  assert q == output

  if output:
    assert is_exclusive(q)
  else:
    assert not is_exclusive(q)
