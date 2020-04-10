from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='PyQtExtendedScene',
      version='0.1.3',
      description='Extended scene library',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/EPC-MSU/PyQtExtendedScene',
      author='EPC MSU',
      author_email='mihalin@physlab.ru',
      license='MIT',
      packages=['extendedscene'],
      install_requires=[
            'PyQt5>=5.8.2, <=5.14.0',
      ],
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
      ],
      python_requires='>=3.6',
      zip_safe=False)
