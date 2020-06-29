#!/usr/bin/env python

# This file exists within 'nark':
#
#   https://github.com/tallybark/nark

# Boilerplate documentation build configuration file,
# (Originally) created by sphinx-quickstart on Tue Jul 9 22:26:36 2013
# (and since somewhat modified to a make more palatable boilerplate).
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import datetime
import os
import shlex
import sys
from pkg_resources import get_distribution

import sphinx_rtd_theme

# If extensions (or modules to document with autodoc) are in another
# directory, add these directories to sys.path here. If the directory is
# relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
#sys.path.insert(0, os.path.abspath('.'))

# Get the project root dir, which is the parent dir of this
cwd = os.getcwd()
project_root = os.path.dirname(cwd)

# Insert the project root dir as the first element in the PYTHONPATH.
# This lets us ensure that the source package is imported, and that its
# version is used.
sys.path.insert(0, project_root)

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                                                     ┃
# ┃ YOU/DEV: Customize this import and these strings for your project.  ┃

project_dist = 'nark'
package_name = 'nark'
project_ghuser = 'tallybark'
project_ghrepo = project_dist
project_texinfo = 'One line description of project.'
project_docinfo = '{} Documentation'.format(project_dist)
project_htmlhelp_basename = 'Narkdoc'
project_copy = '2018-2020 Landon Bouma, Tally Bark LLC, & contributors.'
project_auth = 'Landon Bouma'
project_orgn = 'Tally Bark LLC'

exclude_patterns = [
    'CODE-OF-CONDUCT.rst',
    'CONTRIBUTING.rst',
    'README.rst',
]

# ┃                                                                     ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

# -- General configuration ---------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
# Ref:
#   http://www.sphinx-doc.org/en/master/usage/extensions/index.html
extensions = [
    'sphinx.ext.autodoc',
    # For hyperlinks, e.g., :ref:`My Section Title`.
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.coverage',
    # Google style docstrings
    # https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
    # https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
    # https://google.github.io/styleguide/pyguide.html#383-functions-and-methods
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
]

# Prevent non local image warnings from showing.
suppress_warnings = ['image.nonlocal_uri']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = project_dist
copyright = project_copy
author = project_auth

# (lb): Using setuptools_scm magic, per
#   https://github.com/pypa/setuptools_scm#usage-from-sphinx
# we can call get_distribution, rather than hard coding herein.
#
# The version info for the project you're documenting, acts as replacement
# for |version| and |release|, also used in various other places throughout
# the built documents.
#
# The full version, including alpha/beta/rc tags.
release = get_distribution(project_dist).version
# The short X.Y version.
# - (lb): One place I see `release` used -- to name the browser page.
version = '.'.join(release.split('.')[:2])

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to
# some non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build']

# The reST default role (used for this markup: `text`) to use for all
# documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []

# If true, keep warnings as "system message" paragraphs in the built
# documents.
#keep_warnings = False

# -- Options for HTML output -------------------------------------------

# Ref:
#   http://www.sphinx-doc.org/en/master/usage/configuration.html#html-options
#   http://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# The theme to use for HTML and HTML Help pages.
# Ref:
#   https://sphinx-rtd-theme.readthedocs.io/en/latest/configuring.html
html_theme = 'sphinx_rtd_theme'

# 2020-03-29: There's a deprecation warning fixed upstream last year
# but the Sphinx package has not been released to PyPI since Feb, 2019.
# Here's the error:
#   writing additional pages...  search/<path>/.tox/docs/lib/python3.8/site-packages/
#       sphinx_rtd_theme/search.html:21: RemovedInSphinx30Warning: To modify script_files in
#       the theme is deprecated. Please insert a <script> tag directly in your theme instead.
html_theme_path = ["_themes", ]

# Theme options are theme-specific and customize the look and feel of a
# theme further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    # Table of contents options.
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
    # Miscellaneous options.
    # 'canonical_url': '',
    # 'analytics_id': 'UA-XXXXXXX-1',  #  Provided by Google in your dashboard
    'logo_only': False,
    'display_version': True,
    # prev_next_buttons_location: [bottom], top, both, or None.
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    # vcs_pageview_mode (upper-left navbar home button):
    #   With display_github: [blob], edit, or raw.
    #   #'vcs_pageview_mode': '',
    # style_nav_header_background: Default: '#2980B9'
    #   #'style_nav_header_background': '#2980B9',
}

# https://docs.readthedocs.io/en/latest/vcs.html?highlight=conf_py_path
html_context = {
    # Enable the "Edit in GitHub" link within the header of each page.
    'display_github': True,
    # Set the following variables to generate the resulting github URL for each page.
    # Format Template: https://{{ github_host|default("github.com") }}
    #   /{{ github_user }}/{{ github_repo }}/blob
    #   /{{ github_version }}{{ conf_py_path }}{{ pagename }}{{ suffix }}
    'github_user': project_ghuser,
    'github_repo': project_ghrepo,
    # Branch name.
    'github_version': 'proving/',
    # Path in the checkout to the docs root.
    'conf_py_path': 'docs/',
}

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as
# html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the
# top of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon
# of the docs.  This file should be a Windows icon file (.ico) being
# 16x16 or 32x32 pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets)
# here, relative to this directory. They are copied after the builtin
# static files, so a file named "default.css" will overwrite the builtin
# "default.css".
# (lb): include docs/_static/images/*.png
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page
# bottom, using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# (lb): These work with alabaster, but are ignored by sphinx_rtd_theme.
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html',
        'donate.html',
    ]
}

# Additional templates that should be rendered to pages, maps page names
# to template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer.
# Default is True.
#html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer.
# Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages
# will contain a <link> tag referring to it.  The value of this option
# must be the base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = project_htmlhelp_basename

# -- Options for LaTeX output ------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto/manual]).
latex_documents = [(
    'index',
    '{}.tex'.format(package_name),
    project_docinfo,
    project_orgn,
    'manual',
), ]

# The name of an image file (relative to this directory) to place at
# the top of the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings
# are parts, not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


# -- Options for manual page output ------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(
    'index',
    package_name,
    project_docinfo,
    [project_orgn],
    1,
), ]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output ----------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [(
    'index',
    package_name,
    project_docinfo,
    project_orgn,
    package_name,
    project_texinfo,
    'Miscellaneous',
), ]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu.
#texinfo_no_detailmenu = False

# https://www.sphinx-doc.org/en/master/_modules/sphinx/builders/linkcheck.html
linkcheck_anchors_ignore = [
    # Default ignore entry is leading bang.
    "^!",
    # FIXME/2019-02-19: (lb): I'm having issues with `linkcheck`
    # not liking my anchors, which I swear are working for me!
    "get-started",
]

