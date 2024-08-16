import bpy
import os
import zipfile

# Define the global property
bpy.types.Scene.zip_file_path = bpy.props.StringProperty(
    name="File Path",
    description="Select a .zip file",
    default=r"D:\Ripped\Sketchfab",
    subtype='FILE_PATH'
)

class ImportPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_ripper_import_panel"
    bl_label = "Import"
    bl_description = "This is a template panel, for starting a new addon."
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Ripper"
    bl_order = 0
    
    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.label(text="Import Panel")
        layout.prop(context.scene, "zip_file_path", text="Select .zip File")
        
        # Add a button to trigger the import operator
        layout.operator("ripper.import_zip", text="Import")

class ImportZipOperator(bpy.types.Operator):
    bl_idname = "ripper.import_zip"
    bl_label = "Import"
    
    def execute(self, context):
        
        current_file_path = bpy.data.filepath
        
        
        # save the current file only if there is a current filepath
        if current_file_path:
            bpy.ops.wm.save_mainfile()
        # remove all mesh, material and image data in the blender scene
        # Remove all objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # Remove all meshes
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        # Remove all materials
        for material in bpy.data.materials:
            bpy.data.materials.remove(material)

        # Remove all images
        for image in bpy.data.images:
            bpy.data.images.remove(image)


        
        file_path = context.scene.zip_file_path
        if not file_path.endswith(".zip"):
            self.report({'ERROR'}, "Please select a .zip file")
            return {'CANCELLED'}
        
        # Unzip the file
        unzip_dir = os.path.splitext(file_path)[0]
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(unzip_dir)
        
                # Try to import an FBX file
        fbx_file = None
        obj_files = []
        for root, dirs, files in os.walk(unzip_dir):
            for file in files:
                if file.endswith(".fbx") and fbx_file is None:
                    fbx_file = os.path.join(root, file)
                    bpy.ops.import_scene.fbx(filepath=fbx_file)
                    break
                elif file.endswith(".obj"):
                    obj_files.append(os.path.join(root, file))

            if fbx_file:
                break

        # If no FBX file was found, import all OBJ files
        if not fbx_file and obj_files:
            for obj_file in obj_files:
                bpy.ops.wm.obj_import(filepath=obj_file)
        elif not fbx_file and not obj_files:
            self.report({'ERROR'}, "No FBX or OBJ file found in the zip")
            return {'CANCELLED'}
        
        # Save the blend file
        blend_file_path = os.path.join(unzip_dir, os.path.basename(unzip_dir) + ".blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend_file_path)

        self.report({'INFO'}, f"Imported and saved blend file: {blend_file_path}")
        return {'FINISHED'}

def register():
    print("Registering ImportPanel")
    bpy.utils.register_class(ImportPanel)
    bpy.utils.register_class(ImportZipOperator)

def unregister():
    bpy.utils.unregister_class(ImportPanel)
    bpy.utils.unregister_class(ImportZipOperator)
    del bpy.types.Scene.zip_file_path

if __name__ == "__main__":
    register()
