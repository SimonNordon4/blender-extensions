import importlib
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
__package__ = os.path.basename(script_dir)

import unity_exporter.__init__
import unity_exporter.unity_fbx_exporter
import unity_exporter.unity_exporter_panel

# TODO: Make this autoload everything.
importlib.reload(unity_exporter.__init__)
importlib.reload(unity_exporter.unity_fbx_exporter)
importlib.reload(unity_exporter.unity_exporter_panel)

unity_exporter.__init__.register()
