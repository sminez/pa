import os
from setuptools import setup, find_packages


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='pa',
    version='0.2.1',
    description="My presonal ADHD assistant.",
    url="https://github.com/sminez/pa",
    author="Innes Anderson-Morrison",
    author_email='innesdmorrison@gmail.com',
    install_requires=[
        'docopt',
        'keyring',
        'peewee',
        'requests',
        'toml',
    ],
    setup_requires=[
        'pytest-cov',
        'pytest-runner',
    ],
    tests_require=['pytest'],
    extras_require={'test': ['pytest']},
    packages=find_packages(),
    package_dir={'pa': 'pa'},
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta'
    ],
    entry_points={
        'console_scripts': [
            'pa = pa.cli:main',
        ]
    },
    test_suite="tests",
)
