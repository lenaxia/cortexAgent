from setuptools import setup, find_packages

setup(
    name="unified_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "mcp",
        "pydantic",
        "pytest",
        "pytest-mock",
    ],
    extras_require={
        "strands": ["strands-agents", "strands-agents-tools", "strands-agents-builder"],
    },
    entry_points={
        'console_scripts': [
            'unified-agent=unified_agent.main:main',
        ],
    },
)
