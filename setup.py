from setuptools import setup
from setuptools import find_packages
from curses_builder import VERSION, AUTHOR

setup(
    name="curses_builder",
    version=VERSION,
    description="curses_builder",
    author=AUTHOR,
    install_requires=["windows-curses", "Levenshtein"],
    packages=find_packages(exclude=("tests*", "testing*")),
    entry_points={},
)
