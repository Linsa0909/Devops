"""AI Factory Runtime — CLI 网关"""
from setuptools import setup, find_packages

setup(
    name="ai-factory-runtime",
    version="1.0.0",
    description="AI Factory CLI — 端到端软件需求 Agent 平台网关",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.1",
        "pyyaml>=6.0",
        "httpx>=0.27",
    ],
    entry_points={
        "console_scripts": [
            "ai-factory=cli:main",
        ],
    },
    python_requires=">=3.10",
)
