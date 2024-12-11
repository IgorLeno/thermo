from setuptools import setup, find_packages

setup(
    name="thermo",
    version="0.1",
    packages=find_packages(),
    package_data={
        'thermo': [
            'repository/*',
            'final_molecules/*',
            'programs/*'
        ]
    },
    install_requires=[
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "pubchempy>=1.0.4",
    ],
)