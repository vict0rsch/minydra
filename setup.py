import setuptools

import minydra

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="minydra",
    version=minydra.__version__,
    author="Victor Schmidt",
    author_email="not.an.address@yes.com",
    description=(
        "Easily parse arbitrary arguments from the command line without dependencies"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vict0rsch/minydra",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    install_requires=[],
    extras_require={"yaml": ["PyYaml"]},
)
