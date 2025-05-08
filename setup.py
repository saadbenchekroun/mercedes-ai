from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mercedes-ai",
    version="1.0.0",
    author="Mercedes-Benz AI Systems Team",
    author_email="ai-systems@mercedes-benz.com",
    description="Advanced conversational AI system for Mercedes-Benz S-Class",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mercedes-benz/mercedes-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mercedes-ai=main:main",
        ],
    },
) 