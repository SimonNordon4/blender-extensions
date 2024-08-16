import bpy

class RipperPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_ripper_panel"
    bl_label = "Ripper Panel"
    bl_description = "This is a ripper panel, for starting a new addon."
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Ripper"
    bl_order = 0
    
    @classmethod
    def poll(cls, context):
        return context.object is not None
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="OBJECT_DATA")
    
    def draw(self, context):
        layout = self.layout
        layout.operator("ripper.test_operator")
        
class RipperTestOperator(bpy.types.Operator):
    bl_idname = "ripper.test_operator"
    bl_label = "Testing 1, 2, 3"
    
    def execute(self, context):
        self.report({'INFO'}, 'Hello from ripper panel.')
        return {"FINISHED"}
    
def register():
    bpy.utils.register_class(RipperPanel)
    bpy.utils.register_class(RipperTestOperator)
    
def unregister():
    bpy.utils.unregister_class(RipperPanel)
    bpy.utils.unregister_class(RipperTestOperator)

    
