from . import template_panel

print("Running template/__init__.py")

def register():
    template_panel.register()

def unregister():
    template_panel.unregister()
    