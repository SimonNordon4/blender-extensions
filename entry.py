import importlib
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
__package__ = os.path.basename(script_dir)

import unity_exporter.__init__

# TODO: Make this autoload everything.
importlib.reload(unity_exporter.__init__)
importlib.reload(unity_exporter.unity_exporter_panel)

unity_exporter.__init__.register()
