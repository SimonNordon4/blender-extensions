import bpy
import auto_load

class TemplateDevPanel(bpy.types.Panel):
    bl_idname = "DEV_PT_template_dev_panel"
    bl_label = "Template Dev Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Template"
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Template Panel", icon="MODIFIER")
        layout.operator("dev_panel.reload_addon")
        layout.operator("dev_panel.uninstall_addon")
        
class ReloadAddonOperator(bpy.types.Operator):
    bl_idname = "dev_panel.reload_addon"
    bl_label = "Reload Addon"
    
    def execute(self, context):
        auto_load.unregister()
        auto_load.init()
        auto_load.register()
        return {"FINISHED"}
    
class UninstallAddonOperator(bpy.types.Operator):
    bl_idname = "dev_panel.uninstall_addon"
    bl_label = "Uninstall Addon"
    
    def execute(self, context):
        auto_load.unregister()
        return {"FINISHED"}
