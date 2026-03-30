from setuptools import find_packages, setup


setup(name="PyQtExtendedScene",
      version="1.0.18",
      description="Extended scene library",
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
