from setuptools import setup


with open("README.md", "r") as file:
    long_description = file.read()

setup(name="PyQtExtendedScene",
      version="2.0.0",
      description="Extended scene library",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/EPC-MSU/PyQtExtendedScene",
      author="EPC MSU",
      author_email="info@physlab.ru",
      license="MIT",
      packages=["PyQtExtendedScene"],
      install_requires=[
            "PyQt5>=5.8.2, <=5.15.0",
      ],
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
      ],
      python_requires=">=3.6, <=3.8",
      zip_safe=False)
