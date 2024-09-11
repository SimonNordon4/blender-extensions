from . import lightmapper_operators
from . import lightmapper_panel
from . import lightmapper_properties

print("Running lightmapper/__init__.py")

def register():
    lightmapper_properties.register()
    lightmapper_operators.register()
    lightmapper_panel.register()

def unregister():
    lightmapper_properties.unregister()
    lightmapper_operators.unregister()
    lightmapper_panel.unregister()
    