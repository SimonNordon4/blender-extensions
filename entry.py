import importlib
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
__package__ = os.path.basename(script_dir)

import template.__init__

# TODO: Make this autoload everything.
importlib.reload(template.__init__)
importlib.reload(template.template_panel)

template.__init__.register()
