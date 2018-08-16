from setuptools import setup, find_packages
import os

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='advk',
    description="My presonal ADHD assistant.",
    url="https://github.com/sminez/aard",
    author="Innes Anderson-Morrison",
    author_email='innesdmorrison@gmail.com',
    install_requires=[],
    # setup_requires=[
    #     'pytest-cov',
    #     'pytest-runner',
    # ],
    # tests_require=['pytest'],
    # extras_require={'test': ['pytest']},
    packages=find_packages(),
    package_dir={'advk': 'advk'},
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta'
    ],
    entry_points={
        'console_scripts': [
            'advk = advk.cli:main',
        ]
    },
    test_suite="tests",
)
