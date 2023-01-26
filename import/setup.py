from setuptools import find_packages, setup

setup(
  name='geocodr_import',
  description='Import tools for geocodr',
  version='1.0.0',
  python_requires='>=3',
  packages=find_packages(),
  include_package_data=True,
  entry_points={
    'console_scripts': [
      'geocodr-post=geocodr_import.post:main',
      'geocodr-zk=geocodr_import.zk:main',
    ],
  },
  install_requires=[
    'kazoo',
    'requests',
  ],
)
