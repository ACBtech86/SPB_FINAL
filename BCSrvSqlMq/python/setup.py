from setuptools import setup, find_packages

setup(
    name='bcsrvsqlmq',
    version='2.0.0',
    description='BCSrvSqlMq - Bacen/IF Message Broker Service (Python)',
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=[
        'pymqi>=1.12.0',
        'psycopg2-binary>=2.9.0',
        'cryptography>=41.0.0',
        'lxml>=4.9.0',
        'pywin32>=306',
    ],
    entry_points={
        'console_scripts': [
            'bcsrvsqlmq=bcsrvsqlmq.__main__:main',
        ],
    },
)
