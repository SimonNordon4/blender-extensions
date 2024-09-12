import bpy

import bpy.utils

class LIGHTMAPPER_PT_main_panel(bpy.types.Panel):
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
        props = scene.lightmapper_properties

        # Create UV Lightmap
        box = layout.box()
        box.label(text="Lightmap UV", icon='UV')
        box.operator("lightmapper.create_lightmap_uv", icon='ADD')

        # Lightmap Resolution
        box = layout.box()
        box.label(text="Lightmap Resolution", icon='TEXTURE')
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(props, "lightmap_width", text="Width")
        row.prop(props, "lightmap_height", text="Height")

        # Resolution Presets
        row = col.row(align=True)
        row.operator("lightmapper.set_resolution", text="1K").resolution = 1024
        row.operator("lightmapper.set_resolution", text="2K").resolution = 2048
        row.operator("lightmapper.set_resolution", text="4K").resolution = 4096
        row.operator("lightmapper.set_resolution", text="8K").resolution = 8192

        # Export Settings
        box = layout.box()
        box.label(text="Export Settings", icon='EXPORT')
        box.prop(props, "export_path")
        box.label(text="Bake Name", icon='TEXTURE')
        export_row = box.row(align=True)
        export_row.prop(props, "bake_name", expand=True)

        # Bake Button
        layout.separator()
        row = layout.row()
        row.scale_y = 2
        row.operator("lightmapper.bake_lightmap", text="Bake Lightmap", icon='RENDER_STILL')
    
class LIGHTMAPPER_OT_set_resolution(bpy.types.Operator):
    bl_idname = "lightmapper.set_resolution"
    bl_label = "Set Resolution"
    bl_description = "Set the resolution for the lightmap"
    
    resolution: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        scene.lightmapper_properties.lightmap_width = self.resolution
        scene.lightmapper_properties.lightmap_height = self.resolution
        self.report({'INFO'}, f"Resolution set to {self.resolution}x{self.resolution}")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(LIGHTMAPPER_OT_set_resolution)
    bpy.utils.register_class(LIGHTMAPPER_PT_main_panel)
    
def unregister():
    bpy.utils.unregister_class(LIGHTMAPPER_PT_main_panel)
    bpy.utils.unregister_class(LIGHTMAPPER_OT_set_resolution)

    
