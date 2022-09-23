from setuptools import setup, find_packages

import AERzip

with open('README.md') as readme_file:
    README = readme_file.read()

'''with open('HISTORY.md') as history_file:
    HISTORY = history_file.read()'''

setup(
    name='AERzip',
    version=AERzip.__version__,
    description='Useful tools to compress and decompress AEDAT files in Python',
    # long_description_content_type="text/markdown",
    # long_description=README + '\n\n' + HISTORY,
    license='GPL-3.0',
    packages=find_packages(),
    author='Alvaro Ayuso Martinez',
    author_email='alv.correo@gmail.com',
    keywords=['AER', 'Events', 'Spikes', 'AEDAT', 'Compression', 'Decompression', 'Utils',
              'Neuroscience', 'Neuromorphic', 'Cochlea', 'Retina', 'jAER'],
    url='https://github.com/alvaroy96/AERzip',
    download_url='https://pypi.org/project/AERzip/',
    install_requires=[
        'pyNAVIS>=1.1.0',
        'matplotlib>=3.4.3',
        'numpy>=1.21.3',
        'lz4>=3.1.3',
        'zstandard>=0.16.0',
        'pylzma'
    ]
)
