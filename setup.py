from setuptools import setup, find_packages
import os
import re

# Read version from gitswitch.py
with open(os.path.join('gitswitch', 'gitswitch.py'), 'r') as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")

# Read long description from README.md
with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name="gitswap",
    version=version,
    author="Utkarsh Umang",
    author_email="luciferutkarsh@gmail.com",
    description="Manage multiple GitHub accounts on a single machine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gitswitch",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyyaml>=5.1",
    ],
    entry_points={
        "console_scripts": [
            "gitswap=gitswitch.gitswitch:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    keywords="git, github, ssh, multiple accounts, identity, profile",
)