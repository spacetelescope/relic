from setuptools import setup, find_packages
import relic.release

version = relic.release.get_info()
relic.release.write_template(version, 'relic/')

setup(
    name='relic',
    version=version.pep386,
    author='Joseph Hunkeler',
    author_email='jhunkeler@gmail.com',
    description='Maintains version information for git projects',
    url='https://github.com/jhunkeler/relic',
    license='BSD',
    classifiers = [
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=find_packages(),
    package_data={'': ['README.md', 'LICENSE.txt']}
)
