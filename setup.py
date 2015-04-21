from setuptools import setup, find_packages
import simsogui

setup(
    name='simsogui',
    version=simsogui.__version__,
    description='Graphical User Interface for SimSo',
    author='Maxime Cheramy',
    author_email='maxime.cheramy@laas.fr',
    url='http://homepages.laas.fr/mcheramy/simso/',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering',
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: Qt'
    ],
    packages=find_packages(),
    install_requires=[
        'simso>=0.7',
    ],
    entry_points={
        'gui_scripts': ['simso = simsogui:run_gui']
    },
    long_description="""\
This package provides a Graphical User Interface for SimSo. SimSo is a
scheduling simulator for real-time multiprocessor architectures that takes
into account some scheduling overheads (scheduling decisions, context-switches)
and the impact of caches through statistical models. Based on a Discrete-Event
Simulator, it allows quick simulations and a fast prototyping of scheduling
policies using Python."""
)
