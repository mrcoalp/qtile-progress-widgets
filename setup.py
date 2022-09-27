from setuptools import find_packages, setup

setup(
    name="qtile-awesome-widgets",
    version="0.0.1",
    packages=find_packages(),
    install_requires=["qtile>=0.21.0", "psutil"],
    description="Awesome custom widgets for qtile window manager.",
    author="mrcoalp",
    url="https://github.com/mrcoalp/qtile-awesome-widgets",
    license="MIT",
)
