from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="slate-nlp",
    version="1.0.0",
    author="Jonathan K. Kummerfeld",
    author_email="jkk@berkeley.edu",
    description="A terminal-based text annotation tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://jkk.name/slate/",
    packages=find_packages(),
    keywords="nlp annotation labeling natural-language-processing text-annotation",
    python_requires='>=2.6, !=3.0.*, !=3.1.*, !=3.2.*, <4',
    entry_points={
        'console_scripts': [
            'slate = slate.annotate:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
