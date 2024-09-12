import bpy
import bpy.utils
import bmesh
import bpy.ops
import os.path
import re



class LIGHTMAPPER_OT_create_lightmap_uv(bpy.types.Operator):
    bl_idname = "lightmapper.create_lightmap_uv"
    bl_label = "Create Lightmap UV"
    bl_description = "Create a second UV channel called 'Lightmap' and select it"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected.")
            return {'CANCELLED'}

        for obj in mesh_objects:
            uv_layers = obj.data.uv_layers
            if len(uv_layers) < 2:
                uv_layer = uv_layers.new(name="Lightmap")
                uv_layers.active = uv_layer
                self.report({'INFO'}, f"Lightmap UV created for {obj.name}.")
            else:
                self.report({'INFO'}, f"{obj.name} already has a Lightmap UV.")
            
            # Perform lightmap unwrap
            print(f"Performing lightmap unwrap for {obj.name}")
            bpy.context.view_layer.objects.active = obj
            bpy.ops.uv.lightmap_pack()

        return {'FINISHED'}

class SceneState():
    def __init__(self, bake_node_material_name="LIGHTMAPPER_TMP_EMPTY_MAT", bake_node_name="LIGHTMAPPER_TMP_IMAGE_NODE"):
        self.original_selection = None
        self.bake_node_material_name = bake_node_material_name
        self.bake_node_name = bake_node_name

        
    def save_original_materials(self):
        original_materials = {}
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                original_materials[obj] = [slot.material for slot in obj.material_slots]
        return original_materials
    
    def save_compositor_state(self):
        scene = bpy.context.scene
        if scene.use_nodes:
            self.original_compositor_nodes = [node.copy() for node in scene.node_tree.nodes]
            self.original_compositor_links = [link.copy() for link in scene.node_tree.links]

    def restore_compositor_state(self):
        scene = bpy.context.scene
        if scene.use_nodes and self.original_compositor_nodes and self.original_compositor_links:
            scene.node_tree.nodes.clear()
            scene.node_tree.links.clear()
            for node in self.original_compositor_nodes:
                scene.node_tree.nodes.new(type=node.bl_idname)
                for attr in dir(node):
                    if not attr.startswith("__") and not callable(getattr(node, attr)):
                        setattr(scene.node_tree.nodes[-1], attr, getattr(node, attr))
            for link in self.original_compositor_links:
                scene.node_tree.links.new(
                    scene.node_tree.nodes[link.from_node.name].outputs[link.from_socket.name],
                    scene.node_tree.nodes[link.to_node.name].inputs[link.to_socket.name]
                )
    
    def restore_empty_materials(self):
        """ Removes temporary bake material from selected objects, they will be applied if the material slot has an empty material """
        for obj in self.original_selection:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material and slot.material.name == self.bake_node_material_name:
                        obj.data.materials.pop(index=obj.material_slots.find(slot.material.name))
                        
    def restore_original_materials(self):
        """ Removes the bake image node that was created for the bake. """
        for obj, materials in self.original_materials.items():
            for material in materials:
                if material and material.node_tree:
                    nodes = material.node_tree.nodes
                    for node in nodes:
                        if node.name == self.bake_node_name:
                            nodes.remove(node)
                            
    def restore_selection(self):
        # deselect all
        bpy.ops.object.select_all(action='DESELECT')
        
        # select all original objects and make them renderable.
        for obj in self.original_selection:
            obj.select_set(True)
            obj.hide_render = False
            
        # set the original active object
        if self.original_active_object is not None:
            bpy.context.view_layer.objects.active = self.original_active_object
        
    def save(self, context):
        self.engine = bpy.context.scene.render.engine
        self.samples = bpy.context.scene.cycles.samples
        self.use_denoising = bpy.context.scene.cycles.use_denoising
        self.bake_type = bpy.context.scene.cycles.bake_type
        self.use_pass_direct = bpy.context.scene.render.bake.use_pass_direct
        self.use_pass_indirect = bpy.context.scene.render.bake.use_pass_indirect
        self.use_pass_color = bpy.context.scene.render.bake.use_pass_color
        self.use_selected_to_active = bpy.context.scene.render.bake.use_selected_to_active
        
        self.original_active_object = bpy.context.view_layer.objects.active
        self.original_selection = context.selected_objects
        self.active_object = context.active_object
        self.original_materials = self.save_original_materials()

        # self.save_compositor_state()
    
    def restore(self, context):
        bpy.context.scene.render.engine = self.engine
        bpy.context.scene.cycles.samples = self.samples
        bpy.context.scene.cycles.use_denoising = self.use_denoising

        bpy.context.scene.cycles.bake_type = self.bake_type
        bpy.context.scene.render.bake.use_pass_direct = self.use_pass_direct
        bpy.context.scene.render.bake.use_pass_indirect = self.use_pass_indirect
        bpy.context.scene.render.bake.use_pass_color = self.use_pass_color

        bpy.context.scene.render.bake.use_selected_to_active = self.use_selected_to_active

        self.restore_selection()
        self.restore_original_materials()
        self.restore_empty_materials()
        # self.restore_compositor_state()
        


class LIGHTMAPPER_OT_bake_lightmap(bpy.types.Operator):
    bl_idname = "lightmapper.bake_lightmap"
    bl_label = "Bake Lightmap"
    bl_description = "Bake lightmap for selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.TMP_EMPTY_MAT_NAME = "BAKELAB_TMP_EMPTY_MAT"
        self.TMP_IMAGE_NODE_NAME = "BAKELAB_TMP_IMAGE_NODE"
        
        self._timer = None
        self.bake_iterator = None
        
        self.bake_object = None
        self.bake_name = None
        self.bake_image = None
        
        self.scene_state = SceneState()

        self.lightmapper_props = bpy.context.scene.lightmapper_properties
        
    def _validate_export_path(self, context):
        export_path = self.lightmapper_props.export_path
        if not export_path:
            self.report({'ERROR'}, "Export path not set.")
            return False
        
        if not os.path.exists(export_path):
            self.report({'ERROR'}, "Export path does not exist.")
            return False

        if not os.path.isdir(export_path):
            self.report({'ERROR'}, "Export path is not a directory.")
            return False

        return True

    def _validate_bake_objects(self, context):
        """ Ensure the object is in a state that supports baking. """
        if not self.bake_object:
            self.report({'ERROR'}, "No mesh objects selected.")
            return False

        # Ensure we're in object mode.
        if context.mode != 'OBJECT':
            self.report({'ERROR'}, "Lightmap baking requires object mode.")
            return False
        pass
            

    def _validate_mesh_objects(self, context, mesh_objects):
            """ Ensure the object is in a state that supports baking. """
            if not mesh_objects:
                self.report({'ERROR'}, "No mesh objects selected.")
                return False
            
            # Ensure we're in object mode.
            if context.mode != 'OBJECT':
                self.report({'ERROR'}, "Lightmap baking requires object mode.")
                return False

            # Ensure we have at least one object selected.
            if not mesh_objects:
                self.report({'ERROR'}, "No mesh objects selected.")
                return False
            
            # Ensure there are no disabled for rendering.
            for obj in mesh_objects:
                if obj.hide_render or obj.hide_viewport:
                    self.report({'ERROR'}, f"Object {obj.name} is disabled for rendering or hidden in viewport.")
                    return False
                
            # Ensure each mesh has 2 uv channels.
            for obj in mesh_objects:
                if len(obj.data.uv_layers) < 2:
                    self.report({'ERROR'}, f"Object {obj.name} does not have a Lightmap channel.")
                    return False

            return True
        
    def _select_correct_uv(self, mesh_objects):
        """ Change the state of the selected objects to work for baking."""
        self.report({'INFO'}, "Correcting UV Selections.")
        # Ensure that the first UVMap is set to render, and that "Lightmap" UV is selected.
        for obj in mesh_objects:
            # If the lightmap is renderable, set it to the first UVMap. Otherwise respect user choice.
            obj.data.uv_layers[0].active_render = True
            # Ensure the lightmap is selected, as that's the UV we're baking to.
            obj.data.uv_layers["Lightmap"].active = True
       
    def _create_bake_image(self, context):
        # get the resolution from the props
        width = self.lightmapper_props.lightmap_width
        height = self.lightmapper_props.lightmap_height
        new_image = bpy.data.images.new(name="BakeImage", width=width, height=height)
        
        # set the float depth
        new_image.use_generated_float = True
        # EXR for high dynamic range.
        new_image.file_format = 'OPEN_EXR'
        
        # color space
        # new_image.color_space = 'sRGB' # Don't need to set for now.
        return new_image
        
        
       
    def _create_bakeable_object(self, mesh_objects):
        """ Create a combined mesh from the selected objects, including UVs and materials. """
        # Create a new mesh
        new_mesh = bpy.data.meshes.new(name="BakeableMesh")

        # Create a new object with the new mesh
        new_object = bpy.data.objects.new(name="BakeableObject", object_data=new_mesh)

        # Link the new object to the current collection
        bpy.context.collection.objects.link(new_object)

        # Create a bmesh to combine all selected meshes
        bm = bmesh.new()

        # Dictionary to map temporary vertices to the combined bmesh vertices
        vertex_map = {}
        
        # Create a dictionary to hold the UV layer mappings for each UV map
        uv_map_layers = {}

        # List to keep track of all materials across objects
        material_map = {}

        for obj in mesh_objects:
            # Ensure the object is in object mode
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='OBJECT')

            # Get the mesh data
            mesh = obj.data

            # Add all UV maps from the original object
            for uv_layer in mesh.uv_layers:
                # Create a new UV layer in the combined mesh if it doesn't already exist
                if uv_layer.name not in uv_map_layers:
                    uv_map_layers[uv_layer.name] = bm.loops.layers.uv.new(uv_layer.name)

            # Create a temporary bmesh from the current object's mesh data
            temp_bm = bmesh.new()
            temp_bm.from_mesh(mesh)

            # Transform the temporary bmesh to the object's world space
            temp_bm.transform(obj.matrix_world)

            # Ensure the materials are copied over correctly
            for mat_slot in obj.material_slots:
                if mat_slot.material not in material_map:
                    # Append the material to the new object if it doesn't exist yet
                    new_object.data.materials.append(mat_slot.material)
                    material_map[mat_slot.material] = len(new_object.data.materials) - 1

            # Loop over each face in the temporary bmesh
            for face in temp_bm.faces:
                # Create a list of corresponding vertices in the combined bmesh
                new_face_verts = []
                for loop in face.loops:
                    vert = loop.vert
                    # Check if the vertex is already in the main bmesh
                    if vert not in vertex_map:
                        # Add the vertex to the main bmesh and store the mapping
                        new_vert = bm.verts.new(vert.co)
                        vertex_map[vert] = new_vert
                    new_face_verts.append(vertex_map[vert])

                # Create the face in the combined bmesh
                bm_face = bm.faces.new(new_face_verts)

                # Copy UV coordinates for all UV layers
                for uv_layer_name, uv_layer in uv_map_layers.items():
                    temp_uv_layer = temp_bm.loops.layers.uv.get(uv_layer_name)
                    if temp_uv_layer:
                        for loop_dest, loop_src in zip(bm_face.loops, face.loops):
                            loop_dest[uv_layer].uv = loop_src[temp_uv_layer].uv

                # Assign the correct material index to the face
                mat_index = face.material_index
                if mat_index < len(obj.material_slots):
                    mat = obj.material_slots[mat_index].material
                    bm_face.material_index = material_map[mat]

            # Free the temporary bmesh
            temp_bm.free()

        # Write the combined bmesh to the new mesh
        bm.to_mesh(new_mesh)
        bm.free()

        # Ensure the new object has all materials correctly assigned
        new_object.data.update()
        return new_object
    
    def _get_empty_material(self):
        """ Creates a bake compatible material for the bake object. """
        mat = bpy.data.materials.new(self.TMP_EMPTY_MAT_NAME)
        mat.use_nodes = True
        img_node = mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
        img_node.name = self.TMP_IMAGE_NODE_NAME
        return mat
    
    def _apply_bake_image(self, bake_object):
        """ Apply the bake image to all materials in the bake_object"""
        if len(bake_object.material_slots) == 0:
            bpy.ops.object.material_slot_add()
        for slot in bake_object.material_slots:
            if slot.material is None:
                slot.material = self._get_empty_material()
            mat = slot.material
            mat.use_nodes = True
            if self.TMP_IMAGE_NODE_NAME in mat.node_tree.nodes:
                img_node = mat.node_tree.nodes[self.TMP_IMAGE_NODE_NAME]
            else:
                img_node = mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                img_node.name = self.TMP_IMAGE_NODE_NAME
            mat.node_tree.nodes.active = img_node
            img_node.image = self.bake_image
            
    def _prepare_object_for_bake(self, mesh_objects, bake_object):
        """ Get object context ready for baking, disabling the original objects and setting the bake object as the active object. """
        # Ensure the original objects are hidden and unselected
        for obj in mesh_objects:
            obj.select_set(False)
            obj.hide_render = True
        
        # Ensure the bake object is selected and active, with correct UVs
        bake_object.select_set(True)
        bpy.context.view_layer.objects.active = bake_object
        
        # Ensure the lightmap is selected, as that's the UV we're baking to.
        bake_object.data.uv_layers[0].active_render = True
        bake_object.data.uv_layers["Lightmap"].active = True
    
    
    def _setup_bake_settings(self):
        """ Set up bake settings for diffuse lightmap baking. """
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = self.lightmapper_props.num_samples
        bpy.context.scene.cycles.use_denoising = False

        bpy.context.scene.cycles.bake_type = 'DIFFUSE'
        bpy.context.scene.render.bake.use_pass_direct = True
        bpy.context.scene.render.bake.use_pass_indirect = True
        bpy.context.scene.render.bake.use_pass_color = False
        
        bpy.context.scene.render.bake.use_selected_to_active = False
        
    def _setup_compositor_for_denoising(self):
        # Enable use_nodes for the current scene
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree

        # Clear default nodes
        for node in tree.nodes:
            tree.nodes.remove(node)

        # Create input image node
        input_node = tree.nodes.new(type='CompositorNodeImage')
        input_node.image = self.bake_image

        # Create denoise node
        denoise_node = tree.nodes.new(type='CompositorNodeDenoise')

        # Create output node
        output_node = tree.nodes.new(type='CompositorNodeOutputFile')
        output_node.format.file_format = 'HDR'
        output_node.format.color_depth = '32'
        output_node.format.exr_codec = 'ZIP'
        
        
        output_node.base_path = bpy.context.scene.lightmapper_properties.export_path
        output_node.file_slots[0].path = self.bake_name

        # Link nodes
        tree.links.new(input_node.outputs[0], denoise_node.inputs[0])
        tree.links.new(denoise_node.outputs[0], output_node.inputs[0])
        
    def _render_denoised_image(self):
        # Run the compositor
        bpy.ops.render.render(write_still=True)
        
    def _clean_up_exported_name(self):
        export_path = bpy.context.scene.lightmapper_properties.export_path
        exported_file = None
        cleaned_file = os.path.join(export_path, f"{self.bake_name}.hdr")

        print(f"Export path: {export_path}")
        print(f"Expected cleaned file: {cleaned_file}")

        for file in os.listdir(export_path):
            print(f"Checking file: {file}")
            if file.startswith(self.bake_name) and file.endswith(".hdr"):
                if re.match(rf"{re.escape(self.bake_name)}\d{{4}}\.hdr$", file):
                    exported_file = os.path.join(export_path, file)
                    print(f"Found exported file: {exported_file}")
                    break

        if exported_file is None:
            print("Exported file not found.")
            return

        if os.path.exists(cleaned_file):
            print(f"Removing existing cleaned file: {cleaned_file}")
            os.remove(cleaned_file)

        print(f"Renaming {exported_file} to {cleaned_file}")
        os.rename(exported_file, cleaned_file)
        
    def save_state(self, context):
        self.scene_state.save(context)
        
    def restore_state(self, context):
        self.scene_state.restore(context)
        
        # remove the bake object
        if self.bake_object is not None:
            if self.bake_object.data is not None:
                bpy.data.meshes.remove(self.bake_object.data, do_unlink=True)
        
        # remove the bake_image
        if self.bake_image is not None:
            bpy.data.images.remove(self.bake_image, do_unlink=True)

    def execute(self, context):
        # Run the update loop as an iterator.
        self.save_state(context)
        self.bake_iterator = self.bake(context)
        # We'll update every 0.5 seconds.
        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)  # Check every 0.5 seconds
        context.window_manager.modal_handler_add(self)
        
        bake_name_target = bpy.context.scene.lightmapper_properties.bake_name
        if bake_name_target is 'ACTIVE_OBJECT':
            self.bake_name = context.active_object.name
        else:
            self.bake_name = context.view_layer.active_layer_collection.collection.name
        

        return {'RUNNING_MODAL'}
    
    def bake(self, context):
       
        
        yield 1
        # 1. Validate that the selected objects are suitable for lightmapping.
        
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        # deselect everything so we're not baking lights and empties.
        bpy.ops.object.select_all(action='DESELECT')
        
        if not self._validate_export_path(context):
            yield -1
        
        if not self._validate_mesh_objects(context, mesh_objects):
            yield -1
        
        self._select_correct_uv(mesh_objects)
        
        yield 1
        

        # 2. Create an image to bake to, and a new bake object to be baked to.
        self.bake_image = self._create_bake_image(context)
        self.bake_object = self._create_bakeable_object(mesh_objects)
        yield 1
        self._apply_bake_image(self.bake_object)
        yield 1
        self._prepare_object_for_bake(mesh_objects, self.bake_object)
        yield 1
        self._setup_bake_settings()
        

        while bpy.ops.object.bake('INVOKE_DEFAULT', type='DIFFUSE') != {'RUNNING_MODAL'}:
            yield 1 # 'INVOKE_DEFAULT' will give us the progress bar.
        while not self.bake_image.is_dirty:
            yield 1
            
        self._setup_compositor_for_denoising()
        yield 1
        
        self._render_denoised_image()
        while bpy.ops.render.render() == {'RUNNING_MODAL'}:
            yield 1

        self._clean_up_exported_name()
            
        yield 0

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}
        
        if event.type == 'TIMER':
            result = next(self.bake_iterator)
            if result == 1:
                return {"RUNNING_MODAL"}
            if result == -1:
                self.cancel(context)
                return  {'CANCELLED'}
            if result == 0:
                self.finish(context)
                return {'FINISHED'}
        
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        print("Modal cancelled")
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        self.restore_state(context)
    
    def finish(self, context):
        print("Modal Finished")
        if self.bake_iterator.gi_running:
            self.bake_iterator.close()
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        self.restore_state(context)

def register():
    print("Registering lightmapper_operators")
    bpy.utils.register_class(LIGHTMAPPER_OT_create_lightmap_uv)
    bpy.utils.register_class(LIGHTMAPPER_OT_bake_lightmap)

def unregister():
    bpy.utils.unregister_class(LIGHTMAPPER_OT_create_lightmap_uv)
    bpy.utils.unregister_class(LIGHTMAPPER_OT_bake_lightmap)

if __name__ == "__main__":
    register()

