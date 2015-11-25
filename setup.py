from setuptools import setup, find_packages


setup(
    name='eris',
    version='0.1',
    author='William Palmer',
    author_email='will@steelhive.com',
    url='https://www.steelhive.com',
    description='A chaos monkey for ldap3.',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'ldap3',
        'fake-factory'
    ],
    entry_points={
        'console_scripts': [
            'eris = eris.bin.chaos:main'
        ]
    }
)
