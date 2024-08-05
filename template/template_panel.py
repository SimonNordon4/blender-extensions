import bpy

class TemplatePanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_template_panel"
    bl_label = "Template Panel"
    bl_description = "This is a template panel, for starting a new addon."
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Template"
    bl_order = 0
    
    @classmethod
    def poll(cls, context):
        return context.object is not None
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="OBJECT_DATA")
    
    def draw(self, context):
        layout = self.layout
        layout.operator("template.test_operator")
        
class TemplateTestOperator(bpy.types.Operator):
    bl_idname = "template.test_operator"
    bl_label = "Testing 1, 2, 3"
    
    def execute(self, context):
        self.report({'INFO'}, 'Hello from template panel.')
        return {"FINISHED"}
    
def register():
    bpy.utils.register_class(TemplatePanel)
    bpy.utils.register_class(TemplateTestOperator)
    
def unregister():
    bpy.utils.unregister_class(TemplatePanel)
    bpy.utils.unregister_class(TemplateTestOperator)

    
