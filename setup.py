from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='potemkin-decorator',
    version=open('version.txt','r').read(),
    packages=find_packages(),

    install_requires=[
      'boto3==1.12.26'
    ],

    author='Eric Kascic',
    author_email='eric.kascic@stelligent.com',
    description='Decorator to help for AWS/boto integration testing in pytest',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/stelligent/potemkin-decorator',
    license='MIT',
    python_requires='>=3.6'
)