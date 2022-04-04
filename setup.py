import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="clusterprocess_ss_abp",
    version="0.0.7",
    author="Sam Cameron",
    author_email="samuel.j.m.cameron@gmail.com",
    description="package to process LAMMPS data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/samueljmcameron/clusterprocess_ss_abp",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License "
        "v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.3',
    install_requires=['numpy','lammpstools']
)
