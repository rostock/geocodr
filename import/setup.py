from setuptools import setup, find_packages

setup(
    name='geocodr_import',
    description="Import tools for geocodr",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'geocodr-post=geocodr_import.post:main',
            'geocodr-zk=geocodr_import.zk:main',
        ],
    },
    install_requires=[
        'requests',
        'kazoo',
    ],
)
