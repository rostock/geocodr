from setuptools import find_packages, setup

setup(
  name='geocodr',
  description='geocoder API for Apache Solr',
  version='1.0.2',
  python_requires='>=3',
  packages=find_packages(),
  include_package_data=True,
  entry_points={
    'console_scripts': [
      'geocodr=geocodr.cli:main',
      'geocodr-api=geocodr.api:main',
    ],
  },
  install_requires=[
    'pyproj',
    'requests',
    'Shapely',
    'waitress',
    'Werkzeug',
  ],
)
