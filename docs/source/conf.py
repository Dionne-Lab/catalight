import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join('..','..')))

print(sys.path)
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'photoreactor'
copyright = '2022, Briley Bourgeois, Claire Carlin'
author = 'Briley Bourgeois, Claire Carlin'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.napoleon', 
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary', 
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    "sphinx.ext.intersphinx"
    ]

autosummary_generate = True
autodoc_default_options = {'inherited-members': False}

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
exclude_patterns = ['photoreactor/data_analysis/IntegrationTesting.rst']

napoleon_google_docstring = False
napoleon_numpy_docstring = True
todo_include_todos = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    "python": ("http://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None)
}
