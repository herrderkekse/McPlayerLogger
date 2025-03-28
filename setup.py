from setuptools import setup, find_packages

setup(
    name="minecraft_log_checker",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "paramiko",
        "matplotlib",
        "numpy",
    ],
    extras_require={
        "dev": ["pytest"],
    },
)
