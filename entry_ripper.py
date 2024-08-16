import importlib
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
__package__ = os.path.basename(script_dir)

import ripper.__init__
import ripper.import_panel
import ripper.fix_panel
import ripper.export_panel

# TODO: Make this autoload everything.
importlib.reload(ripper.__init__)
importlib.reload(ripper.import_panel)
importlib.reload(ripper.fix_panel)
importlib.reload(ripper.export_panel)

ripper.__init__.register()
