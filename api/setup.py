from setuptools import setup, find_packages

setup(
    name='geocodr',
    description="Geocoder API for Solr",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    extras_require={
        ':python_version == "2.7"': ['futures']
    },
    install_requires=[
        'Werkzeug',
        'requests',
        'pyproj',
        'shapely',
    ],
)
