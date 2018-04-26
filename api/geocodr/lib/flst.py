import re
from collections import namedtuple

flst = namedtuple('flst', [
    'gemarkung', # 6
    'flur',  # 3
    'zaehler', # 5
    'nenner', # 4
    'gemarkung_name',
])

flst_re = re.compile(r'''
    ^\s*
    (
        ((?P<gemarkung>\d{6,6})[-/ ]?)
        |
        (?P<gemarkung_name>[^0-9]+?)
    )[-/, ]*
    ((flur\s*)?(?P<flur>\d{1,3}))?[-/, ]*
    (?P<zaehler>\d{,5})[-/, ]*
    (?P<nenner>\d{,4})[-/, ]*
    \s*$
''',
    re.VERBOSE | re.IGNORECASE
)

def parse_flst(token):
    """
    >>> parse_flst("123456")
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

    >>> parse_flst("132232 flur 1")
    flst(gemarkung='132232', flur='001', zaehler='', nenner='', gemarkung_name='')
    >>> parse_flst("flurbezirk ii flur 1")
    flst(gemarkung='', flur='001', zaehler='', nenner='', gemarkung_name='flurbezirk ii')
    >>> parse_flst("123232 1, 157")
    flst(gemarkung='123232', flur='001', zaehler='00157', nenner='', gemarkung_name='')
    >>> parse_flst("123232 1, 157/1")
    flst(gemarkung='123232', flur='001', zaehler='00157', nenner='0001', gemarkung_name='')
    >>> parse_flst("Krummendorf 1 157")
    flst(gemarkung='', flur='001', zaehler='00157', nenner='', gemarkung_name='Krummendorf')
    """
    match = flst_re.match(token)
    if match:
        g = match.groupdict()
        return flst(
            gemarkung_name=(g['gemarkung_name'] or '').strip(),
            gemarkung=g['gemarkung'] or '',
            flur='%03d' % int(g['flur']) if g['flur'] else '',
            zaehler='%05d' % int(g['zaehler']) if g['zaehler'] else '',
            nenner='%04d' % int(g['nenner']) if g['nenner'] else '',
        )
        return flst(match.groupdict())
