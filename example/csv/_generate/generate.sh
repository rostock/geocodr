set -e
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $HERE/..

curl -O -fsSL https://geo.sv.rostock.de/download/opendata/statistische_bezirke/statistische_bezirke.json
curl -O -fsSL https://geo.sv.rostock.de/download/opendata/strassen/strassen.json
python $HERE/tocsv.py
rm *.json
