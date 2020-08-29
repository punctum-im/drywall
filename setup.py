import io

from setuptools import find_packages
from setuptools import setup

with io.open("README.md", "rt", encoding="utf8") as f:
    readme = f.read()

with io.open("requirements.txt", "rt", encoding="utf8") as f:
    require = f.readlines()
require = [x.strip() for x in require]

setup(
    name="drywall",
    version="0.0.1",
    url="https://rosetta.im",
    license="BSD",
    maintainer="rosetta.im team",
    maintainer_email="none@...",
    description="The refference implementation of a rosetta.im server.",
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=require,
    extras_require={"test": ["pytest", "coverage"]},
)
