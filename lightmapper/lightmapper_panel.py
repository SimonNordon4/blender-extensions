import bpy

class LightmapperPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_lightmapper_panel"
    bl_label = "Lightmapper Panel"
    bl_description = "This is a lightmapper panel, for starting a new addon."
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lightmapper"
    bl_order = 0
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="OUTLINER_DATA_LIGHTPROBE")
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        lightmapper_props = scene.lightmapper_properties


        
        layout.operator("lightmapper.create_lightmap_uv")
        

        layout.prop(scene.lightmapper_properties, "lightmap_resolution")
        layout.prop(scene.lightmapper_properties, "export_path")
        layout.operator("lightmapper.bake_lightmap")
    
def register():
    bpy.utils.register_class(LightmapperPanel)
    
def unregister():
    bpy.utils.unregister_class(LightmapperPanel)

    
