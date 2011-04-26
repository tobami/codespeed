import os
from setuptools import setup, find_packages

f = open(os.path.join(os.path.dirname(__file__), 'README.md'))
readme = f.read()
f.close()

setup(
    author='Miquel Torres',
    author_email='tobami@gmail.com',
    name='codespeed',
    version='0.8.1',
    url='https://github.com/tobami/codespeed',
    license='GNU Lesser General Public License version 2.1',
    requires=['django', 'isodate'],
    packages=find_packages(exclude=['ez_setup', 'speedcenter']),
    description='A web application to monitor and analyze the performance of your code',
    long_description=readme,
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License version 2.1',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
)
