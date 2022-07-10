from setuptools import find_packages, setup

setup(
    name="qtile-widgets",
    version="0.0.1",
    packages=find_packages(),
    install_requires=["qtile>=0.21.0"],
    description="Custom widgets for qtile window manager.",
    author="mrcoalp",
    url="https://github.com/mrcoalp/qtile-widgets",
    license="MIT",
)
