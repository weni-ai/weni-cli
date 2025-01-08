from setuptools import setup, find_packages

setup(
    name="weni-cli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click",
        "requests",
        "flask",
        "waitress",
        "pyyaml",
        "python-slugify",
    ],
    entry_points={
        "console_scripts": [
            "weni = weni_cli.cli:cli",
        ],
    },
)
