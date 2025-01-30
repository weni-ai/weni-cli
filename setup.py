from setuptools import setup, find_packages

setup(
    name="weni-cli",
    version="0.3.0a2",
    packages=find_packages(where="weni_cli", include=["weni_cli", "weni_cli.*"]),
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
