"""
Setup script for PC-Agent+
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

setup(
    name="pc-agent-plus",
    version="1.0.0",
    author="Ambreen Aslam",
    author_email="ambreengillanii@gmail.com",
    description="Enhanced Hierarchical Multi-Agent Collaboration Framework with Multi-Model Support and Automated Evaluation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/asalam-msit/PC-Agent-Plus",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pc-agent-plus=main:main",
            "pc-agent-simulate=simulate:compare_scenarios",
        ],
    },
    include_package_data=True,
    package_data={
        "pc_agent_plus": [
            "config/*.yaml",
            "config/*.yml",
        ],
    },
    keywords=[
        "ai",
        "automation",
        "multi-agent",
        "gui",
        "llm",
        "cost-optimization",
        "pc-automation"
    ],
    project_urls={
        "Bug Reports": "https://github.com/asalam-msit/PC-Agent-Plus/issues",
        "Source": "https://github.com/asalam-msit/PC-Agent-Plus",
        "Documentation": "https://github.com/asalam-msit/PC-Agent-Plus/wiki",
    },
)