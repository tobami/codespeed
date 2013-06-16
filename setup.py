from setuptools import setup, find_packages

setup(
    author='Miquel Torres',
    author_email='tobami@gmail.com',
    name='codespeed',
    version='0.9.1',
    url='https://github.com/tobami/codespeed',
    license='GNU Lesser General Public License version 2.1',
    install_requires=['django==1.4', 'isodate', 'south<=2.0', 'django-tastypie'],
    packages=find_packages(exclude=['ez_setup', 'sample_project']),
    description='A web application to monitor and analyze the performance of your code',
    include_package_data=True,
    zip_safe=False,
)
