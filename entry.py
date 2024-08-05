import importlib
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
__package__ = os.path.basename(script_dir)

import template.__init__

importlib.reload(template.__init__)
    
template.__init__.register()
