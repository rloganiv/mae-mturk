from setuptools import setup

setup(
    name='mae-mturk',
    packages=['app'],
    include_package_data=True,
    install_requires=[
        'flask',
        'boto3'
    ],
)
