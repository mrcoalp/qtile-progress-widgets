from setuptools import find_packages, setup

setup(
    name="qtile-progress-widgets",
    version="0.0.1",
    packages=find_packages(),
    install_requires=["dbus-next", "psutil", "qtile", "requests", "validators"],
    description="Custom progress widgets for qtile window manager.",
    author="mrcoalp",
    url="https://github.com/mrcoalp/qtile-progress-widgets",
    license="MIT",
)
