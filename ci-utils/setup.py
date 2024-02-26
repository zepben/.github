from setuptools import setup, find_packages

setup(
    name='ci-utils',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'gitpython',
        'jinja2',
        'slack_sdk'
    ],
    entry_points={
        'console_scripts': [
            'ci = src.cli:cli',
        ],
    },
)
