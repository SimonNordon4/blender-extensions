import bpy
import os

import bpy.utils

# Handler to load the directory path when a Blender file is loaded
def load_directory_path_handler(dummy):
    bpy.context.scene.directory_path = bpy.context.scene.get("last_directory_path", "")

# Handler to save the directory path when a Blender file is saved
def save_directory_path_handler(dummy):
    bpy.context.scene["last_directory_path"] = bpy.context.scene.directory_path

class UnityExporterPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_unity_exporter_panel"
    bl_label = "Unity Exporter"
    bl_description = "This is a unity_exporter panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "UnityExporter"
    bl_order = 0
    
    @classmethod
    def poll(cls, context):
        return context.object is not None
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="OBJECT_DATA")
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.prop(scene, "directory_path")
        layout.operator("unity_exporter.export_images")

    
class UnityExporterExportImages(bpy.types.Operator):
    bl_idname = "unity_exporter.export_images"
    bl_label = "Export Images to Unity"
    
    def execute(self, context):
        # Get the directory path from the user
        directory_path = context.scene.directory_path
        if not directory_path:
            self.report({'WARNING'}, 'Please specify a directory path.')
            return {'CANCELLED'}
        
        if not os.path.exists(directory_path):
            self.report({'WARNING'}, 'The specified directory path does not exist.')
            return {'CANCELLED'}
        
        # Check if there are any images to export
        if not bpy.data.images:
            self.report({'WARNING'}, 'There are no images to export.')
            return {'CANCELLED'}

        # Iterate over all images in the blend file
        for image in bpy.data.images:
            if image.type not in {'RENDER_RESULT', 'COMPOSITING'}:
                # Create a file path for the export image
                image_name = bpy.path.clean_name(image.name)
                export_image_path = os.path.join(directory_path, f"{image_name}.png")

                # Save the image as a PNG file
                image.filepath_raw = export_image_path
                image.file_format = 'PNG'
                try:
                    image.save()
                    self.report({'INFO'}, f"Exported {image.name} to {export_image_path}")
                except Exception as e:
                    self.report({'ERROR'}, f"Failed to export {image.name}: {str(e)}")
                    return {'CANCELLED'}
        
        self.report({'INFO'}, 'Images exported successfully.')
        return {'FINISHED'}

def register():
    print("Registering unity_exporter_panel")
    bpy.utils.register_class(UnityExporterPanel)
    bpy.utils.register_class(UnityExporterExportImages)
    bpy.types.Scene.directory_path = bpy.props.StringProperty(
        name="Directory Path",
        description="Choose a directory",
        subtype='DIR_PATH'
    )
    
    bpy.app.handlers.load_post.append(load_directory_path_handler)
    bpy.app.handlers.save_pre.append(save_directory_path_handler)
    
def unregister():
    bpy.utils.unregister_class(UnityExporterPanel)
    bpy.utils.unregister_class(UnityExporterExportImages)
    del bpy.types.Scene.directory_path
    bpy.app.handlers.load_post.remove(load_directory_path_handler)
    bpy.app.handlers.save_pre.remove(save_directory_path_handler)

    
