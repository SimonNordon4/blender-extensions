import bpy
import mathutils
import math
import os


# Multi-user datablocks are preserved here. Unique copies are made for applying the rotation.
# Eventually multi-user datablocks become single-user and gets processed.
# Therefore restoring the multi-user data assigns a shared but already processed datablock.
shared_data = dict()

# All objects and collections in this view layer must be visible while being processed.
# apply_rotation and matrix changes don't have effect otherwise.
# Visibility will be restored right before saving the FBX.
hidden_collections = []
hidden_objects = []
disabled_collections = []
disabled_objects = []


def unhide_collections(col):
	global hidden_collections
	global disabled_collections

	# No need to unhide excluded collections. Their objects aren't included in current view layer.
	if col.exclude:
		return

	# Find hidden child collections and unhide them
	hidden = [item for item in col.children if not item.exclude and item.hide_viewport]
	for item in hidden:
		item.hide_viewport = False

	# Add them to the list so they could be restored later
	hidden_collections.extend(hidden)

	# Same with the disabled collections
	disabled = [item for item in col.children if not item.exclude and item.collection.hide_viewport]
	for item in disabled:
		item.collection.hide_viewport = False

	disabled_collections.extend(disabled)

	# Recursively unhide child collections
	for item in col.children:
		unhide_collections(item)


def unhide_objects():
	global hidden_objects
	global disabled_objects

	view_layer_objects = [ob for ob in bpy.data.objects if ob.name in bpy.context.view_layer.objects]

	for ob in view_layer_objects:
		if ob.hide_get():
			hidden_objects.append(ob)
			ob.hide_set(False)
		if ob.hide_viewport:
			disabled_objects.append(ob)
			ob.hide_viewport = False


def make_single_user_data():
	global shared_data

	for ob in bpy.data.objects:
		if ob.data and ob.data.users > 1:
			# Figure out actual users of this datablock (not counting fake users)
			users = [user for user in bpy.data.objects if user.data == ob.data]
			if len(users) > 1:
				# Store shared mesh data (MESH objects only).
				# Other shared datablocks (CURVE, FONT, etc) are always exported as separate meshes
				# by the built-in FBX exporter.
				if ob.type == 'MESH':
					# Shared mesh data will be restored if users have no active modifiers
					modifiers = 0
					for user in users:
						modifiers += len([mod for mod in user.modifiers if mod.show_viewport])
					if modifiers == 0:
						shared_data[ob.name] = ob.data

				# Single-user data is mandatory in all object types, otherwise we can't apply the rotation.
				ob.data = ob.data.copy()


def apply_object_modifiers():
	# Select objects in current view layer not using an armature modifier
	bpy.ops.object.select_all(action='DESELECT')
	for ob in bpy.data.objects:
		if ob.name in bpy.context.view_layer.objects:
			bypass_modifiers = False
			for mod in ob.modifiers:
				if mod.type == 'ARMATURE':
					bypass_modifiers = True
			if not bypass_modifiers:
				ob.select_set(True)

	# Conversion to mesh may not be available depending on the remaining objects
	if bpy.ops.object.convert.poll():
		print("Converting to meshes:", bpy.context.selected_objects)
		bpy.ops.object.convert(target='MESH')


def reset_parent_inverse(ob):
	if (ob.parent):
		mat_world = ob.matrix_world.copy()
		ob.matrix_parent_inverse.identity()
		ob.matrix_basis = ob.parent.matrix_world.inverted() @ mat_world


def apply_rotation(ob):
	bpy.ops.object.select_all(action='DESELECT')
	ob.select_set(True)
	bpy.ops.object.transform_apply(location = False, rotation = True, scale = False)


def fix_object(ob):
	# Only fix objects in current view layer
	if ob.name in bpy.context.view_layer.objects:

		# Reset parent's inverse so we can work with local transform directly
		reset_parent_inverse(ob)

		# Create a copy of the local matrix and set a pure X-90 matrix
		mat_original = ob.matrix_local.copy()
		ob.matrix_local = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'X')

		# Apply the rotation to the object
		apply_rotation(ob)

		# Reapply the previous local transform with an X+90 rotation
		ob.matrix_local = mat_original @ mathutils.Matrix.Rotation(math.radians(90.0), 4, 'X')

	# Recursively fix child objects in current view layer.
	# Children may be in the current view layer even if their parent isn't.
	# for child in ob.children:
	# 	fix_object(child)

def export_fbx(filepath, objects):
    # # Object mode
	# if bpy.ops.object.mode_set.poll():
	# 	bpy.ops.object.mode_set(mode="OBJECT")
	print(f"Exporting {len(objects)} objects to {filepath}")
	# Create a single copy in multi-user datablocks. Will be restored after fixing rotations.
 	
	make_single_user_data()
 
	for o in objects:
		print("Fixing object:", o)
		fix_object(o)
  
  	# Recompute the transforms out of the changed matrices
	bpy.context.view_layer.update()
 
 	# select the original objects
	bpy.ops.object.select_all(action='DESELECT')
	for o in objects:
		o.select_set(True)
 
 	# Export FBX file
  
	bpy.ops.export_scene.fbx(
     			filepath=filepath,
                apply_scale_options='FBX_SCALE_UNITS',
                object_types={'EMPTY', 'MESH', 'ARMATURE'},
                use_active_collection=False,
                use_selection=True, 
                use_armature_deform_only=False,
                add_leaf_bones=False,
                primary_bone_axis="Y",
                secondary_bone_axis="X",
                use_tspace=False,
                use_triangles=False)

def export_unity_fbx(context, filepath):
	global shared_data
	global hidden_collections
	global hidden_objects
	global disabled_collections
	global disabled_objects

	print("Preparing 3D model for Unity...")

	# Root objects: Empty, Mesh, Curve, Surface, Font or Armature without parent
	root_objects = [item for item in bpy.data.objects if (item.type == "EMPTY" or item.type == "MESH" or item.type == "ARMATURE" or item.type == "FONT" or item.type == "CURVE" or item.type == "SURFACE") and not item.parent]

	# Preserve current scene
	# undo_push examples, including exporters' execute:
	# https://programtalk.com/python-examples/bpy.ops.ed.undo_push  (Examples 4, 5 and 6)
	# https://sourcecodequery.com/example-method/bpy.ops.ed.undo  (Examples 1 and 2)

	bpy.ops.ed.undo_push(message="Prepare Unity FBX")

	shared_data = dict()
	hidden_collections = []
	hidden_objects = []
	disabled_collections = []
	disabled_objects = []

	selection = bpy.context.selected_objects

	# Object mode
	if bpy.ops.object.mode_set.poll():
		bpy.ops.object.mode_set(mode="OBJECT")

	# Ensure all the collections and objects in this view layer are visible
	unhide_collections(bpy.context.view_layer.layer_collection)
	unhide_objects()

	# Create a single copy in multi-user datablocks. Will be restored after fixing rotations.
	make_single_user_data()

	# Apply modifiers to objects (except those affected by an armature)
	apply_object_modifiers()

	try:
		# Fix rotations
		for ob in root_objects:
			print(ob.name, ob.type)
			fix_object(ob)

		# Restore multi-user meshes
		for item in shared_data:
			bpy.data.objects[item].data = shared_data[item]

		# Recompute the transforms out of the changed matrices
		bpy.context.view_layer.update()

		# Restore hidden and disabled objects
		for ob in hidden_objects:
			ob.hide_set(True)
		for ob in disabled_objects:
			ob.hide_viewport = True

		# Restore hidden and disabled collections
		for col in hidden_collections:
			col.hide_viewport = True
		for col in disabled_collections:
			col.collection.hide_viewport = True

		# Restore selection
		bpy.ops.object.select_all(action='DESELECT')
		for ob in selection:
			ob.select_set(True)

		# Export FBX file
		params = dict(filepath=filepath,
                apply_scale_options='FBX_SCALE_UNITS',
                object_types={'EMPTY', 'MESH', 'ARMATURE'},
                use_active_collection=False,
                use_selection=True, 
                use_armature_deform_only=False,
                add_leaf_bones=False,
                primary_bone_axis="Y",
                secondary_bone_axis="X",
                use_tspace=False,
                use_triangles=False)

		print("Invoking default FBX Exporter:", params)
		bpy.ops.export_scene.fbx(**params)

	except Exception as e:
		bpy.ops.ed.undo_push(message="")
		bpy.ops.ed.undo()
		bpy.ops.ed.undo_push(message="Export Unity FBX")
		print(e)
		print("File not saved.")
		# Always finish with 'FINISHED' so Undo is handled properly
		return {'FINISHED'}

	# Restore scene and finish

	bpy.ops.ed.undo_push(message="")
	bpy.ops.ed.undo()
	bpy.ops.ed.undo_push(message="Export Unity FBX")
	print("FBX file for Unity saved.")
	return {'FINISHED'}

class ExportPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_export_panel"
    bl_label = "Export Panel"
    bl_description = "This is an export panel, for exporting the addon."
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Ripper"
    bl_order = 3
    
    @classmethod
    def poll(cls, context):
        return context.object is not None
    
    def draw_header(self, context):
        layout = self.layout
        
    
    def draw(self, context):
        layout = self.layout 
        layout.prop(context.scene, "directory_path")
        layout.operator("ripper.export_images")
        layout.operator("unity_exporter.export_selected")
        layout.operator("unity_exporter.export_each")
        
class ExportImagesOperator(bpy.types.Operator):
    bl_idname = "ripper.export_images"
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
    bl_description = "Export selected objects to Unity as a single fbx."
    
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
                export_fbx(fbx_file_path, selected_objects)
                self.report({'INFO'}, f"Exported selected objects to {fbx_file_path}")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to export FBX: {str(e)}")
                return {'CANCELLED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"An unexpected error occurred: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class UnityExporterExportEach(bpy.types.Operator):
    bl_idname = "unity_exporter.export_each"
    bl_label = "Export Each"
    bl_description = "Export selected objects to Unity each as its own fbx."
    
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
            
            # Ensure the directory path is writable
            if not os.access(directory_path, os.W_OK):
                self.report({'ERROR'}, 'The specified directory path is not writable.')
                return {'CANCELLED'}
            
            for obj in selected_objects:
                # Deselect all objects
                bpy.ops.object.select_all(action='DESELECT')
                
                # Select the current object
                obj.select_set(True)
                
                # Make the object the active object
                bpy.context.view_layer.objects.active = obj
                
                # Get the name of the object
                object_name = obj.name
                fbx_file_path = os.path.join(directory_path, f"{object_name}.fbx")
                
                # Perform the export
                try:
                    print(f"Exporting {object_name} to {fbx_file_path}")
                    
                    export_fbx(fbx_file_path, [obj])
                    self.report({'INFO'}, f"Exported {object_name} to {fbx_file_path}")
                except Exception as e:
                    self.report({'ERROR'}, f"Failed to export {object_name}: {str(e)}")
                    return {'CANCELLED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"An unexpected error occurred: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
        
def register():
    bpy.utils.register_class(ExportPanel)
    bpy.utils.register_class(ExportImagesOperator)
    bpy.utils.register_class(UnityExporterExportSelected)
    bpy.utils.register_class(UnityExporterExportEach)
    bpy.types.Scene.directory_path = bpy.props.StringProperty(
        name="Directory Path",
        description="Choose a directory",
        subtype='DIR_PATH',
        default=r"E:\repos\alchemancer\Assets\Content"
    )
        
def unregister():
    bpy.utils.unregister_class(ExportPanel)
    bpy.utils.unregister_class(ExportImagesOperator)
    bpy.utils.unregister_class(UnityExporterExportSelected)
    bpy.utils.unregister_class(UnityExporterExportEach)
    del bpy.types.Scene.directory_path
