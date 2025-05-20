from setuptools import setup, find_packages

# Read requirements
with open("requirements.txt") as f:
    requirements = [line.strip() for line in f.readlines()]

setup(
    name="neurodock",
    version="0.1.0",
    description="A memory and task execution system for AI agents",
    author="NeuroDock Team",
    author_email="info@neurodock.ai",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=requirements,
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "neurodock=neurodock.cli:main",
        ],
    },
)
