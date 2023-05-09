from setuptools import setup
from setuptools import find_packages
from curses_builder import VERSION, AUTHOR

setup(
    name ='curses_builder' ,
    version=VERSION,
    description='curses_builder',
    author=AUTHOR,
    install_requires=[],
    packages=find_packages(exclude=('tests*', 'testing*')),
    entry_points={
        'console_scripts': [
            'curses_builder = curses_builder.curses_builder:main',
],
}
)
