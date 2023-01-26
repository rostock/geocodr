import re

from collections import namedtuple


flst = namedtuple('flst', [
  'gemarkung',  # 6
  'flur',  # 3
  'zaehler',  # 5
  'nenner',  # 4
  'gemarkung_name',
])

flst_re = re.compile(r'''
    ^\s*
    (
        ((?P<gemarkung>\d{6})[-/ ]?) # 6 digit gemarkung
        |
        (?P<gemarkung_name>[^0-9]+?)   # or gemarkung name
    )
    [-/, ]*                            # optional delimiters
    ((flur\s*)?(?P<flur>\d{1,3}))?     # 'flur' with number or just a number
    [-/, ]*                            # optional delimiters
    (?P<zaehler>\d{,5})                # zaehler (up to 5 digits)
    [-/, ]*                            # optional delimiters
    (?P<nenner>\d{,4})                  # nenner (up to 4 digits))
    \s*$
''',
                     re.VERBOSE | re.IGNORECASE
                     )

flst_short_re = re.compile(r'''
    ^\s*
    (
      (
        ((?P<gemarkung>\d{4,6})[-/ ]?) # 4 or 6 digit gemarkung
        |
        (?P<gemarkung_name>[^0-9]+?)   # or gemarkung name
      )[-/, ]+                         # required delimiter
    )?                                 # gemarkung/gemarkung_name are both optional

    (
        (?P<zaehler>\d{2,5})           # either 2-5 digit zaehler with required nenner
        ([-/, ]+(?P<nenner>\d{1,4}))   # separator required for short format
        |
        (?P<zaehler2>\d{2,3})          # or 2-3 digits zaehler with optional nenner
        ([-/, ]+(?P<nenner2>\d{1,4}))? # separat required for short format
    )
    \s*$
''',
                           re.VERBOSE | re.IGNORECASE
                           )


def parse_flst(token, gemarkung_prefix=None):
  """
  Parse German parcel identifications (Flurstücksnummern).
  gemarkung_prefix is the state-wide prefix used to convert 4-digit
  Gemarkungsnummern to 6-digit.

  Suports long-form with gemarkung name or number, flur number, zaehler and nenner.
  Identification can be truncated from right (e.g. only gemarkung and flur number.

  Also supports short-form with zaehler and optional nenner.

  Numerical identifications (long-form):
  >>> parse_flst("123456")
  flst(gemarkung='123456', flur='', zaehler='', nenner='', gemarkung_name='')

  >>> parse_flst("3456", gemarkung_prefix='12')
  flst(gemarkung='123456', flur='', zaehler='', nenner='', gemarkung_name='')
  >>> parse_flst("123456-56-1/2")
  flst(gemarkung='123456', flur='056', zaehler='00001', nenner='0002', gemarkung_name='')

  >>> parse_flst("123456-123-1234-1")
  flst(gemarkung='123456', flur='123', zaehler='01234', nenner='0001', gemarkung_name='')
  >>> parse_flst("132232001001230001")
  flst(gemarkung='132232', flur='001', zaehler='00123', nenner='0001', gemarkung_name='')
  >>> parse_flst("1322320010012301")
  flst(gemarkung='132232', flur='001', zaehler='00123', nenner='0001', gemarkung_name='')
  >>> parse_flst("13223200100123")
  flst(gemarkung='132232', flur='001', zaehler='00123', nenner='', gemarkung_name='')
  >>> parse_flst("223200100123", gemarkung_prefix='13')
  flst(gemarkung='132232', flur='001', zaehler='00123', nenner='', gemarkung_name='')

  Long-form with named flur and gemarkung names:
  >>> parse_flst("132232 flur 1")
  flst(gemarkung='132232', flur='001', zaehler='', nenner='', gemarkung_name='')
  >>> parse_flst("flurbezirk ii flur 1")
  flst(gemarkung='', flur='001', zaehler='', nenner='', gemarkung_name='flurbezirk ii')
  >>> parse_flst("123232 1, 157")
  flst(gemarkung='123232', flur='001', zaehler='00157', nenner='', gemarkung_name='')
  >>> parse_flst("3232 1, 157", gemarkung_prefix='12')
  flst(gemarkung='123232', flur='001', zaehler='00157', nenner='', gemarkung_name='')
  >>> parse_flst("123232 1, 157/1")
  flst(gemarkung='123232', flur='001', zaehler='00157', nenner='0001', gemarkung_name='')
  >>> parse_flst("Krummendorf 1 157")
  flst(gemarkung='', flur='001', zaehler='00157', nenner='', gemarkung_name='Krummendorf')

  Test short-form:
  >>> parse_flst("15", gemarkung_prefix='12')
  flst(gemarkung='', flur='', zaehler='00015', nenner='', gemarkung_name='')
  >>> parse_flst("157", gemarkung_prefix='12')
  flst(gemarkung='', flur='', zaehler='00157', nenner='', gemarkung_name='')

  >=4-digit numbers are parsed as long-format again:
  >>> parse_flst("1573", gemarkung_prefix='12')
  flst(gemarkung='121573', flur='', zaehler='', nenner='', gemarkung_name='')
  >>> parse_flst("15731", gemarkung_prefix='12')
  flst(gemarkung='121573', flur='001', zaehler='', nenner='', gemarkung_name='')

  Short-form requires /-separator for >=4-digit numbers:
  >>> parse_flst("15/1", gemarkung_prefix='12')
  flst(gemarkung='', flur='', zaehler='00015', nenner='0001', gemarkung_name='')
  >>> parse_flst("157/1", gemarkung_prefix='12')
  flst(gemarkung='', flur='', zaehler='00157', nenner='0001', gemarkung_name='')
  >>> parse_flst("1573/1", gemarkung_prefix='12')
  flst(gemarkung='', flur='', zaehler='01573', nenner='0001', gemarkung_name='')
  >>> parse_flst("15731/1", gemarkung_prefix='12')
  flst(gemarkung='', flur='', zaehler='15731', nenner='0001', gemarkung_name='')

  Short-form combined with gemarkung(name):
  >>> parse_flst("1234,157/1", gemarkung_prefix='13')
  flst(gemarkung='131234', flur='', zaehler='00157', nenner='0001', gemarkung_name='')
  >>> parse_flst("Krummendorf, 157/12")
  flst(gemarkung='', flur='', zaehler='00157', nenner='0012', gemarkung_name='Krummendorf')

  """

  # Add state prefix for Gemarkungen if token starts with numbers but not
  # with our prefix.

  def check(curr_token, r):
    match = r.match(curr_token)
    # print(token, match and match.groupdict())
    if not match:
      return None
    g = match.groupdict()

    # print(g)
    gemarkung_name = (g['gemarkung_name'] or '').strip()
    gemarkung = g.get('gemarkung') or ''
    flur = '%03d' % int(g['flur']) if g.get('flur') else ''

    zaehler = ''
    if g['zaehler']:
      zaehler = '%05d' % int(g['zaehler'])
    elif g.get('zaehler2'):
      zaehler = '%05d' % int(g['zaehler2'])

    nenner = ''
    if g['nenner']:
      nenner = '%04d' % int(g['nenner'])
    elif g.get('nenner2'):
      nenner = '%04d' % int(g['nenner2'])

    return flst(
      gemarkung_name=gemarkung_name,
      gemarkung=gemarkung,
      flur=flur,
      zaehler=zaehler,
      nenner=nenner,
    )

  f = check(token, flst_short_re)
  if f:
    if len(f.gemarkung) == 4 and gemarkung_prefix:
      f = flst(
        gemarkung=gemarkung_prefix + f.gemarkung,
        gemarkung_name='',
        flur='',
        zaehler=f.zaehler,
        nenner=f.nenner,
      )
    return f

  # extend with gemarkung_prefix
  if gemarkung_prefix and re.match(r'^\d{4}', token) and not token.startswith(gemarkung_prefix):
    token = gemarkung_prefix + token

  # check long format
  return check(token, flst_re)
