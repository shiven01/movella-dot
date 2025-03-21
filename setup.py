from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="movella-dot",
    version="0.1.0",
    author="Shiven Shekar",
    author_email="shivenshekar01@gmail.com",
    description="Python package for interfacing with Movella DOT sensors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shiven01/movella-dot",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "bleak>=0.14.0",
        "numpy>=1.20.0",
    ],
)