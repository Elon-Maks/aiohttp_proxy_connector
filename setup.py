from setuptools import setup, find_packages

setup(
    name='aiohttp_proxy_connector',
    version='0.2',
    description='allow http/https requests through https and socks proxy for aiohttp library',
    long_description=open('README.md').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP',
    ],
    keywords='aiohttp proxy',
    url='https://github.com/Elon-Maks/aiohttp_proxy_connector',
    license='MIT',
    author='Maksym Sivolapov',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'yarl',
        'uvloop'
    ],
    platforms='linux',
    include_package_data=True,
    zip_safe=True,
)
