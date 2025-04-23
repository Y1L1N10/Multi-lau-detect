from setuptools import setup, find_packages

setup(
    name="web_lau_detect",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'selenium',
        'pytest',
        'allure-pytest',
    ],
)