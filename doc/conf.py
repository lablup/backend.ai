import datetime
import os

import temporenc


#
# Project settings
#

project = 'Temporenc'
now = datetime.datetime.now()
if now.year > 2014:
    copyright = '2014-{0}, Wouter Bolsterlee'.format(now.year)
else:
    copyright = '2014, Wouter Bolsterlee'
version = temporenc.__version__
release = temporenc.__version__

#
# Extensions
#

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
]

autodoc_member_order = 'bysource'

#
# Files and paths
#

master_doc = 'index'
templates_path = ['_templates']
source_suffix = '.rst'
exclude_patterns = ['build']


#
# Output
#

pygments_style = 'sphinx'
html_theme = 'default'
html_static_path = ['_static']
html_domain_indices = False
html_use_index = False
html_show_sphinx = False
html_show_copyright = True


#
# These docs are intended for hosting by readthedocs.org. Override some
# settings for local use.
#

if not 'READTHEDOCS' in os.environ:
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
