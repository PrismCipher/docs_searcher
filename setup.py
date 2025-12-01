from setuptools import setup, find_packages

setup(
    name='docs-cli',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'typer',
        'rich',
        'requests',
        'beautifulsoup4',
        'lxml',
    ],
    entry_points={
        'console_scripts': [
            'docs=docs_cli.main:app',
        ],
    },
)