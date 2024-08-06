import bpy
import os
import bpy.utils

from . import unity_fbx_exporter

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
        
        row = layout.row()
        row.operator("unity_exporter.clean_image_names")
        row.operator("unity_exporter.clean_mesh_names")
        
        layout.operator("unity_exporter.export_images")
        layout.operator("unity_exporter.export_selected")

class UnityExporterCleanMeshNames(bpy.types.Operator):
    bl_idname = "unity_exporter.clean_mesh_names"
    bl_label = "Clean Mesh Names"
    bl_description = "Match mesh to object name"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):

        selected_objects = bpy.context.selected_objects
            
        if not selected_objects:
            self.report({'WARNING'}, 'No objects selected.')
            return {'CANCELLED'}

        # Make sure each mesh data has the same name as the object it belongs to
        for obj in selected_objects:
            if obj.type == 'MESH':
                obj.data.name = obj.name
        return {'FINISHED'}
    
class UnityExporterCleanImageNames(bpy.types.Operator):
    bl_idname = "unity_exporter.clean_image_names"
    bl_label = "Clean Image Names"
    bl_description = "Match image to material name"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Ensure each image has the same name as the material it belongs to
        for mat in bpy.data.materials:
            if mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        node.image.name = mat.name
        return {'FINISHED'}
    
class UnityExporterExportImages(bpy.types.Operator):
    bl_idname = "unity_exporter.export_images"
    bl_label = "Export Images"
    bl_description = "Export all images in the blend file to the selected directory"
    
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

class UnityExporterExportSelected(bpy.types.Operator):
    bl_idname = "unity_exporter.export_selected"
    bl_label = "Export Selected"
    bl_description = "Export selected objects to Unity as an fbx."
    
    def execute(self, context):
        try:
            # Get the directory path from the user
            directory_path = context.scene.directory_path
            if not directory_path:
                self.report({'WARNING'}, 'Please specify a directory path.')
                return {'CANCELLED'}
            
            if not os.path.exists(directory_path):
                self.report({'WARNING'}, 'The specified directory path does not exist.')
                return {'CANCELLED'}
            
            # Get selected objects
            selected_objects = bpy.context.selected_objects
            if not selected_objects:
                self.report({'WARNING'}, 'No objects selected.')
                return {'CANCELLED'}
            
            # Get the name of the active object
            if not bpy.context.active_object:
                self.report({'WARNING'}, 'No active object found.')
                return {'CANCELLED'}
            
            name_of_active_object = bpy.context.active_object.name
            fbx_file_path = os.path.join(directory_path, f"{name_of_active_object}.fbx")
            
            # Ensure the directory path is writable
            if not os.access(directory_path, os.W_OK):
                self.report({'ERROR'}, 'The specified directory path is not writable.')
                return {'CANCELLED'}
            
            # Perform the export
            try:
                bpy.ops.export_scene.fbx(filepath=fbx_file_path, use_selection=True)
                self.report({'INFO'}, f"Exported selected objects to {fbx_file_path}")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to export FBX: {str(e)}")
                return {'CANCELLED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"An unexpected error occurred: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

def register():
    print("Registering unity_exporter_panel")
    bpy.utils.register_class(UnityExporterPanel)
    bpy.utils.register_class(UnityExporterCleanMeshNames)
    bpy.utils.register_class(UnityExporterCleanImageNames)
    bpy.utils.register_class(UnityExporterExportImages)
    bpy.utils.register_class(UnityExporterExportSelected)
    bpy.types.Scene.directory_path = bpy.props.StringProperty(
        name="Directory Path",
        description="Choose a directory",
        subtype='DIR_PATH'
    )
    
    bpy.app.handlers.load_post.append(load_directory_path_handler)
    bpy.app.handlers.save_pre.append(save_directory_path_handler)
    
def unregister():
    bpy.utils.unregister_class(UnityExporterPanel)
    bpy.utils.unregister_class(UnityExporterCleanMeshNames)
    bpy.utils.unregister_class(UnityExporterCleanImageNames)
    bpy.utils.unregister_class(UnityExporterExportImages)
    bpy.utils.unregister_class(UnityExporterExportSelected)
    del bpy.types.Scene.directory_path
    bpy.app.handlers.load_post.remove(load_directory_path_handler)
    bpy.app.handlers.save_pre.remove(save_directory_path_handler)

    
