# setup module for BloomFilter

from distutils.core import  setup, Extension

BloomFilter_module = Extension(name='_BloomFilter',
                               sources=['BloomFilter.cpp', 'BloomFilter_wrap.cxx'])

setup(name='BloomFilter',
      version='1.0',
      author='lixinye',
      description='BloomFilter Extension for Python',
      ext_modules=[BloomFilter_module],
      py_modules=['BloomFilter'])
