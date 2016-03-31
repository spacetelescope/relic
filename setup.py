from setuptools import setup, find_packages
import relic.release

version = relic.release.get_info()
relic.release.write_template(version, 'relic/')

setup(
    name='relic',
    version=version.pep386,
    author='Joseph Hunkeler',
    author_email='jhunkeler@gmail.com',
    url='https://github.com/jhunkeler/relic',
    license='LICENSE.txt',
    packages=find_packages(),
    package_data={'': ['README.md', 'LICENSE.txt']}
)
