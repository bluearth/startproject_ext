from django.core.management.base import copy_helper, CommandError, LabelCommand
from django.utils.importlib import import_module
import os
import re
from random import choice


PREPEND_SETTINGS = \
"""
##################################################################
# Changing settings here is not recomended!!
#
# You can provide setting overrides in one of the provided settings 
# file in config/settings. Or you can create your own using one of 
# those files as starting point.
#
# Django will check for the value of DJANGO_ENV[_<project_name>][_<site_id>]
# to choose which setting to load at runtime. 
#
# default.py will always be used as fallback override
#
###################################################################

import os
import sys
PROJECT_ROOT = os.path.dirname(__file__)
PROJECT_NAME = os.path.basename(PROJECT_ROOT)
"""
APPEND_SETTINGS = \
"""
###################################################################
import os
import sys
from django.core.exceptions import ImproperlyConfigured

# Add project specific 3rd party lib to PYTHONPATH
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'lib'))

#
# Load settings override based on DJANGO_ENV[_<proj_name>] 
#

# First asserts that default.py exists
try:
    assert os.path.exists(os.path.join('config','settings','default.py'))
except AssertionError:
    raise ImproperlyConfigured("Something wen't very wrong. There should be a config/settings/default.py")

# Use 'default' as fallback 
settings_name = 'default'

# Probe DJANGO_ENV then DJANGO_ENV_<PROJECT_NAME> for settings override name
if os.environ.get('DJANGO_ENV', False):
    settings_name = os.environ.get('DJANGO_ENV', False)
elif os.environ.get('%s_ENV' % (PROJECT_NAME.upper()), False):
    settings_name =  os.environ.get('%s_ENV' % (PROJECT_NAME.upper()), False)

# Finally, load settings override
try:
    exec 'from config.settings.%s import *' % (settings_name)
except ImportError, e:
    raise ImproperlyConfigured(u'%s'% e.message)
"""


class Command(LabelCommand):
    help = "Creates a Django project directory structure for the given project name in the current directory."
    args = "[projectname]"
    label = 'project name'

    requires_model_validation = False
    # Can't import settings during this command, because they haven't
    # necessarily been created.
    can_import_settings = False

    def handle_label(self, project_name, **options):
        # Determine the project_name a bit naively -- by looking at the name of
        # the parent directory.
        directory = os.getcwd()

        # Check that the project_name cannot be imported.
        try:
            import_module(project_name)
        except ImportError:
            pass
        else:
            raise CommandError("%r conflicts with the name of an existing Python module and cannot be used as a project name. Please try another name." % project_name)

        copy_helper(self.style, 'project', project_name, directory)

        # Create a random SECRET_KEY hash, and put it in the main settings.
        main_settings_file = os.path.join(directory, project_name, 'settings.py')
        settings_contents = open(main_settings_file, 'r').read()
        fp = open(main_settings_file, 'w')
        secret_key = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
        settings_contents = re.sub(r"(?<=SECRET_KEY = ')'", secret_key + "'", settings_contents)
#       fp.write(settings_contents)
        fp.write(PREPEND_SETTINGS + settings_contents + APPEND_SETTINGS)
        fp.close()
        
        # Create directory structure and make it pyton module
        os.mkdir(os.path.join(directory, project_name, 'config'))
        open(os.path.join(directory, project_name, 'config', '__init__.py'), 'w').close()
        os.mkdir(os.path.join(directory, project_name, 'config', 'settings'))
        open(os.path.join(directory, project_name, 'config', 'settings', '__init__.py'), 'w').close()
        os.mkdir(os.path.join(directory, project_name, 'config', 'wsgi'))
        os.mkdir(os.path.join(directory, project_name, 'db'))
        os.mkdir(os.path.join(directory, project_name, 'lib'))
        # Default settings override
        fp = open(os.path.join(directory, project_name, 'config', 'settings','default.py'), 'w')
        fp.write(settings_contents)
        fp.close()
        # Create environtment spesific settings at <project_name>/config/settings/      
        open(os.path.join(directory, project_name, 'config', 'settings','development.py'), 'w').close()
        open(os.path.join(directory, project_name, 'config', 'settings','test.py'), 'w').close()
        open(os.path.join(directory, project_name, 'config', 'settings','production.py'), 'w').close()

