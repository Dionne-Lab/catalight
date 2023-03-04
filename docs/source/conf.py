import os
import sys
import tomli
with open("../../pyproject.toml", "rb") as f:
    toml = tomli.load(f)

sys.path.insert(0, os.path.abspath(os.path.join('..', '..')))


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = toml['project']["name"]
version = toml['project']["version"]
release = toml['project']["version"]
author = ', '.join([entry['name'] for entry in toml['project']["authors"]])
copyright = '2022, Briley Bourgeois, Claire Carlin'
# These are grabbed from toml now.
#project = 'catalight'
#author = 'Briley Bourgeois, Claire Carlin'
#release = '0.1.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    "sphinx.ext.intersphinx",
    'sphinx.ext.mathjax'
    ]

autosummary_generate = True
autodoc_default_options = {'inherited-members': False}

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
exclude_patterns = ['catalight/data_analysis/IntegrationTesting.rst']

napoleon_google_docstring = False
napoleon_numpy_docstring = True
todo_include_todos = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = '_static/images/catalight_header_g_whitetext.png'
html_favicon = '_static/images/catalight_logo1_thick.svg'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    "python": ("http://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "PyQt5": ("https://www.riverbankcomputing.com/static/Docs/PyQt5/", None)
}

autodoc_mock_imports = [
    'alicat',
    'matplotlib',
    'mcculw',
    'numpy',
    'pandas',
    'psutil',
    'pycaw',
    'pyqtgraph',
    'scipy',
    'pyserial',
    'pyttsx3',
    'comtypes',
    'pythonnet',
    'pywin32',
    'pywatlow',
    'win32com',
    'PyQt5',
    'clr',
    'serial',
    'Peaksimple',
    'win32gui'
]
