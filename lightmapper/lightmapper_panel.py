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
            box.label(text="Lightmap Settings", icon='TEXTURE')
            col = box.column(align=True)
            row = col.row(align=True)
            row.prop(props, "lightmap_width", text="Width")
            row.prop(props, "lightmap_height", text="Height")
            col.prop(props, "num_samples", text="Samples")

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
    
def register():
        bpy.utils.register_class(LIGHTMAPPER_PT_main_panel)
    
def unregister():
        bpy.utils.unregister_class(LIGHTMAPPER_PT_main_panel)
