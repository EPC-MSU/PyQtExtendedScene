from setuptools import setup

setup(name='PyQtExtendedScene',
      version='0.1',
      description='Little library for working with scene: drag, zoom, add\\remove elements, etc',
      url='https://github.com/EPC-MSU/PyQtExtendedScene',
      author='EPC MSU',
      author_email='mihalin@physlab.ru',
      license='MIT',
      packages=['extendedscene'],
      install_requires=[
            'PyQt5>=5.8.2, <=5.14.0',
      ],
      zip_safe=False)
