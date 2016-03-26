from setuptools import setup, find_packages
import recon.release

version = recon.release.get_info()
recon.release.write_template(version, 'recon/')

setup(
    name='recon',
    version=version.pep386,
    author='Joseph Hunkeler',
    author_email='jhunkeler@gmail.com',
    url='https://github.com/jhunkeler/recon',
    license='LICENSE.txt',
    packages=find_packages(),
    package_data={'': ['README.md', 'LICENSE.txt']}
)
