from setuptools import setup, find_packages

setup(name='lfilterpy',

      version='0.1.1',

      url='https://github.com/dcloud347/lfilter',

      license='MIT',

      author='dcloud347',

      author_email='17864201683@163.com',

      description='Manage website visit',

      packages=find_packages(exclude=['http','https']),

      long_description=open('README.md').read(),
      long_description_content_type="text/markdown",
      zip_safe=False)