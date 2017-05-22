from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='yann',
    version='1.0rc1',
    description='Toolbox for building and learning convolutional neural networks',
    long_description=long_description,
    url='https://github.com/ragavvenkatesan/yann',
    author='Ragav Venkatesan',
    author_email='support@yann.network',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Students, Researchers and Developers',
        'Topic :: Scientific/Engineering :: Computer Vision :: Deep Learning'
        'License :: MIT License',
        'Programming Language :: Python :: 2.7 :: Python 3.x',
    ],
    keywords='convolutional neural networks deep learning',
    packages=find_packages(exclude=['docs', 'tests', 'pantry']),
    install_requires=['theano','numpy','scipy','skdata','progressbar','pillow','matplotlib',
                            'networkx'],
    extras_require={
        'dev': ['sphinx', 'sphinx_rtd_theme', 'pydot',
                'pydot-ng','graphviz'],
        'test': ['mock','pytest-cov','pytest-pep8','pytest'],
    },
    # data_files=['_datasets/'],
    setup_requires=[],
    tests_require=['pytest', 'pytest-runner','pytest', 'pytest-runner', 'coverage', 'codecov'],    
)