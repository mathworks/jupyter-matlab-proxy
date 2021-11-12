# Copyright 2020-2021 The MathWorks, Inc.
from setuptools.command.install import install
import setuptools
from pathlib import Path
from jupyter_matlab_proxy.jupyter_config import config


tests_require = [
    "pytest",
    "pytest-cov",
]

HERE = Path(__file__).parent.resolve()
long_description = (HERE / "README.md").read_text()

setuptools.setup(
    name="jupyter-matlab-proxy",
    version="0.4.0",
    url=config["doc_url"],
    author="The MathWorks, Inc.",
    author_email="jupyter-support@mathworks.com",
    license="MATHWORKS CLOUD REFERENCE ARCHITECTURE LICENSE",
    description="Jupyter Server Proxy for MATLAB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=["tests", "anaconda"]),
    keywords=[
        "Jupyter",
        "Jupyter Proxy",
        "Jupyter Server Proxy",
        "MATLAB Integration for Jupyter",
        "MATLAB",
        "MATLAB Proxy",
        "MATLAB Web Desktop",
        "Remote MATLAB Web Access",
    ],
    classifiers=[
        "Framework :: Jupyter",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires="~=3.6",
    install_requires=[
        "jupyter-server-proxy",
        "jupyter_contrib_nbextensions",
        "matlab-proxy",
    ],
    tests_require=tests_require,
    extras_require={"dev": ["black", "ruamel.yaml"] + tests_require},
    entry_points={
        # jupyter-server-proxy uses this entrypoint
        "jupyter_serverproxy_servers": ["matlab = jupyter_matlab_proxy:setup_matlab"],
        # matlab-proxy uses this entrypoint
        "matlab_proxy_configs": [
            f"{config['extension_name']} = jupyter_matlab_proxy.jupyter_config:config"
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
