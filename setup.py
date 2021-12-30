from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='album-detector',
    version='0.1.0',
    description='Organizes music library.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/hchsiao/album-detector',
    author='hchsiao',

    packages=find_packages(where='.'),
    python_requires='>=3.5',
    install_requires=[],
    entry_points={
        'console_scripts': [
            'album-detector=album_detector:main',
        ],
    },
)
