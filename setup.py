from setuptools import find_packages, setup


with open("README.md", "r") as file:
    long_description = file.read()

setup(name="PyQtExtendedScene",
      version="1.0.16",
      description="Extended scene library",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/EPC-MSU/PyQtExtendedScene",
      author="EPC MSU",
      author_email="mihalin@physlab.ru",
      license="MIT",
      packages=find_packages(),
      python_requires=">=3.6",
      install_requires=[
            'PyQt5>=5.8.2, <=5.15.0; python_version=="3.6"',
            'PyQt5; python_version>"3.6"',
      ],
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
      ],
      zip_safe=False)
