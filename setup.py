from setuptools import setup, find_packages
import os

setup(name = 'mod-common',
      version = '0.9',
      description = 'MOD common libraries, used by both device, SDK and cloud',
      author = "Luis Fagundes",
      author_email = "lhfagundes@hacklab.com.br",
      license = "GPLv3",
      packages = find_packages(),
      install_requires = ['rdflib', 'whoosh', 'pymongo'],
      classifiers = [
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
        ],
      url = 'http://github.com/portalmod/mod-python',
      
)
