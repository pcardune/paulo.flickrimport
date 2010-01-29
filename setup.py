import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name='paulo.flickrimport',
    version = '0.0.1',
    author='Paul Carduner',
    description='Flickr Import Script',
    long_description='Script for downloading photos from flickr and uploading them to divvyshot',
    license = "proprietary",
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    namespace_packages = [],
    install_requires=[
        'setuptools',
        'flickrapi',
        'anyjson',
        'oauth',
        'httplib2',
        ],
    include_package_data = True,
    zip_safe = False,
    entry_points = """
    [console_scripts]
    flickrtodivvy = paulo.flickrimport.shell:main
    """,
    )
