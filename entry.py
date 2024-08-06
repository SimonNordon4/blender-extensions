import importlib
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
__package__ = os.path.basename(script_dir)

import test_addon.__init__

# TODO: Make this autoload everything.
importlib.reload(test_addon.__init__)
importlib.reload(test_addon.test_addon_panel)

test_addon.__init__.register()
