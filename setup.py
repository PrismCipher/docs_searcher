from setuptools import setup, find_packages
from docs_cli.utils import VERSION

setup(
    name='docs-cli',
    version=VERSION,
    packages=find_packages(),
    install_requires=[
        'typer',
        'rich',
        'requests',
        'requests-cache',
        'beautifulsoup4',
        'lxml',
        'markdownify',
    ],
    entry_points={
        'console_scripts': [
            'docs=docs_cli.main:run',
        ],
    },
    python_requires='>=3.10',
    author='CS50 Final Project',
    description='Search programming documentation from the command line',
)