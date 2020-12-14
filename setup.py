# Copyright 2020 The MathWorks, Inc.

import json
import os
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist
from setuptools.command.install import install
import setuptools
from pathlib import Path
from shutil import which

npm_install = ["npm", "--prefix", "gui", "install", "gui"]
npm_build = ["npm", "run", "--prefix", "gui", "build"]


class InstallNpm(install):
    def run(self):

        # Ensure npm is present
        if which("npm") is None:
            raise Exception(
                "npm must be installed and on the path during package install!"
            )

        self.spawn(npm_install)
        self.spawn(npm_build)
        target_dir = Path(self.build_lib) / self.distribution.packages[0] / "gui"
        self.mkpath(str(target_dir))
        self.copy_tree("gui/build", str(target_dir))

        # In order to be accessible in the package, turn the built gui into modules
        (Path(target_dir) / "__init__.py").touch(exist_ok=True)
        for (path, directories, filenames) in os.walk(target_dir):
            for directory in directories:
                (Path(path) / directory / "__init__.py").touch(exist_ok=True)

        super().run()


tests_require = [
    "pytest",
    "pytest-env",
    "pytest-cov",
    "pytest-mock",
    "pytest-dependency",
]

setuptools.setup(
    name="jupyter-matlab-proxy",
    version="0.1.0",
    url="https://github.com/mathworks/jupyter-matlab-proxy",
    author="The MathWorks, Inc.",
    description="Jupyter extension to proxy MATLAB JavaScript Desktop",
    packages=setuptools.find_packages(exclude=["devel", "tests"]),
    keywords=["Jupyter"],
    classifiers=["Framework :: Jupyter"],
    python_requires="~=3.6",
    install_requires=["jupyter-server-proxy", "aiohttp~=3.6.2"],
    setup_requires=["pytest-runner"],
    tests_require=tests_require,
    extras_require={"dev": ["aiohttp-devtools"] + tests_require},
    entry_points={
        "jupyter_serverproxy_servers": [
            "matlab = jupyter_matlab_proxy:setup_matlab"
        ],
        "console_scripts": [
            "matlab-jupyter-app = jupyter_matlab_proxy.app:main"
        ],
    },
    include_package_data=True,
    zip_safe=False,
    cmdclass={"install": InstallNpm},
)
