import io
from setuptools import setup

VERSION = '0.1.dev1'
DESCRIPTION = (
    'A few bits which are potentially useful to developers of Lektor plugins')

with io.open('README.md', 'rt', encoding="utf8") as f:
    README = f.read()

setup(
    author='Jeff Dairiki',
    author_email='dairiki@dairiki.org',
    description=DESCRIPTION,
    version=VERSION,
    keywords='Lektor utilities',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Framework :: Lektor',
        'Environment :: Plugins',
        'Topic :: Software Development :: Libraries',
        ],
    long_description=README,
    long_description_content_type='text/markdown',
    name='lektorlib',
    packages=['lektorlib'],
    url='https://github.com/dairiki/lektorlib',
    install_requires=[
        'six',
        'pathlib2 ; python_version < "3.4"',
        ],
    )
