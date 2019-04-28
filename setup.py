import os
import sys
from setuptools import find_packages, setup
from subprocess import check_output

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')) as requirements_file:
    requirements = []
    for line in requirements_file:
        requirement_spec = line.strip().split(';', 1)
        if len(requirement_spec) == 1 or eval(requirement_spec[1]):
            requirements.append(requirement_spec[0])

setup(
    name='PyEssent',
    version=0.1,
    install_requires=requirements,
    description="A wrapper around Essent's API",
    author='Sylvia van Os',
    author_email='sylvia@hackerchick.me',
    license='Apache2',
    packages=find_packages()
)
