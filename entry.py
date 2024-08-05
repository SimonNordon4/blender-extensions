import importlib
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
__package__ = os.path.basename(script_dir)

import hello_world.__init__

if "auto_load" in locals():
    importlib.reload(hello_world.__init__)
    
hello_world.__init__.register()
