import importlib
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
__package__ = os.path.basename(script_dir)

import lightmapper.__init__
import lightmapper.lightmapper_properties
import lightmapper.lightmapper_operators
import lightmapper.lightmapper_panel

# TODO: Make this autoload everything.
importlib.reload(lightmapper.__init__)
importlib.reload(lightmapper.lightmapper_properties)
importlib.reload(lightmapper.lightmapper_operators)
importlib.reload(lightmapper.lightmapper_panel)

lightmapper.__init__.register()

 