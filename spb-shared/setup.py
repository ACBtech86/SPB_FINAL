"""Setup configuration for spb-shared package."""

from setuptools import find_packages, setup

setup(
    name="spb-shared",
    version="0.1.0",
    description="Shared database models for SPB (Brazilian Payment System) projects",
    author="Finvest DTVM",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.0",
        "asyncpg>=0.29.0",
        "aiosqlite>=0.19.0",
        "alembic>=1.13.0",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
