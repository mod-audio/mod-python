from setuptools import setup, find_packages
import os

setup(name = 'mod-common',
      version = '1.0',
      description = 'MOD common libraries, used by both device and cloud',
      author = "Luis Fagundes",
      author_email = "lhfagundes@hacklab.com.br",
      license = "GPL",
      packages = find_packages(),
      install_requires = ['rdflib', 'whoosh', 'pymongo'],
      classifiers = [
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
        ],
      url = 'http://dev.portalmod.com.br/mod-common',
      
)
