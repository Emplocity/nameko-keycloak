#!/usr/bin/env python

from glob import glob
from os.path import basename, splitext

from setuptools import find_packages, setup

with open("README.rst", "r") as f:
    long_description = f.read()


setup(
    name="nameko-keycloak",
    version="0.1.1",
    license="Apache-2.0",
    description="Helpers to integrate Single Sign-On in nameko-based applications using Keycloak.",
    long_description=long_description,
    author="Emplocity",
    author_email="zbigniew.siciarz@emplocity.pl",
    url="https://github.com/emplocity/nameko-keycloak",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Utilities",
    ],
    project_urls={
        "Issue Tracker": "https://github.com/emplocity/nameko-keycloak/issues",
    },
    python_requires=">=3.8.*",
    install_requires=[
        "nameko>=2,<3",
        "python-keycloak>=0.25.0,<1.0",
        "python-jose>=3.0,<4.0",
        "cryptography>=3.0,<4.0",
        "werkzeug>=1.0,<2.0",
    ],
)
