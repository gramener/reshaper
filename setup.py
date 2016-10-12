#!/usr/bin/env python

from setuptools import setup
import reshaper

long_description = reshaper.__doc__.strip()

kwargs = {
    "name": "reshaper",
    "description": long_description.splitlines()[0],
    "long_description": long_description,
    "url": "https://github.com/gramener/reshaper",
    "author": "Gramener",
    "author_email": "s.anand@gramener.com",
    "version": "1.0.2",
    "py_modules": ["reshaper"],
    "install_requires": ["pandas", "scipy", "tqdm", "GDAL"],
    "entry_points": {
        "console_scripts": ["reshaper=reshaper:cmdline"]
    },
    "license": "MIT",
    "keywords": "reshaper",
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5"
    ]
}

setup(**kwargs)
