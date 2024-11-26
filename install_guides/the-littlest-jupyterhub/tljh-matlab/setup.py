# Copyright 2024 The MathWorks, Inc.
from setuptools import setup, find_namespace_packages
from pathlib import Path

HERE = Path(__file__).parent.resolve()
long_description = (HERE / "README.md").read_text()

setup(
    name="tljh-matlab",
    entry_points={"tljh": ["matlab = tljh_matlab.tljh_matlab"]},
    version="0.1.0",
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    package_data={"tljh_matlab.bash_scripts": ["*.sh"]},
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mathworks/jupyter-matlab-proxy/tree/main/install_guides/the-littlest-jupyterhub/tljh-matlab",
    author="The MathWorks, Inc.",
    author_email="cloud@mathworks.com",
    license="MATHWORKS CLOUD REFERENCE ARCHITECTURE LICENSE",
    description="TLJH plugin for MATLAB",
)
