from . import unity_exporter_panel

def register():
    print("Registering  unity_exporter/__init__")
    unity_exporter_panel.register()

def unregister():
    unity_exporter_panel.unregister()
    