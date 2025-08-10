from setuptools import setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

setup(
    name="py_ri_ufsc",
    version="0.9",
    description="Program designed to handle searches in metadata stored in UFSC Institutional Repository",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Igor Caetano de Souza",
    author_email="igorcaetanods@gmail.com",
    project_urls={
        "GitHub Repository": "https://github.com/IgorCaetano/py_ri_ufsc",
    },
    packages=[
        "py_ri_ufsc",
        "py_ri_ufsc.common",
        "py_ri_ufsc.etl",
        "py_ri_ufsc.etl.extraction",
        "py_ri_ufsc.etl.extraction.courses_info",
        "py_ri_ufsc.etl.transform_and_load",
        "py_ri_ufsc.get_metadata",
        "py_ri_ufsc.src_files"
    ],
    package_dir={"": "src"},
    package_data={"py_ri_ufsc.src_files": ["*.parquet"]},
    include_package_data=True,
    install_requires=install_requires,
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
