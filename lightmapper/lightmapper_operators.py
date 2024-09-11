import bpy
import bpy.utils
import bmesh



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


class LIGHTMAPPER_OT_bake_lightmap(bpy.types.Operator):
    bl_idname = "lightmapper.bake_lightmap"
    bl_label = "Bake Lightmap"
    bl_description = "Bake lightmap for selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    bake_image = None
    
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
       
    def _create_bakeable_object(self, mesh_objects):
        """ Create a combined mesh from the selected objects, including UVs from the 'Lightmap' UV map. """
        # Create a new mesh
        new_mesh = bpy.data.meshes.new(name="BakeableMesh")

        # Create a new object with the new mesh
        new_object = bpy.data.objects.new(name="BakeableObject", object_data=new_mesh)

        # Link the new object to the current collection
        bpy.context.collection.objects.link(new_object)

        # Create a bmesh to combine all selected meshes
        bm = bmesh.new()

        # Create a new UV layer in the combined mesh
        uv_layer = bm.loops.layers.uv.new("Lightmap")

        # A dictionary to map temporary vertices to the combined bmesh vertices
        vertex_map = {}

        for obj in mesh_objects:
            # Ensure the object is in object mode
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='OBJECT')

            # Get the mesh data
            mesh = obj.data

            # Find the "Lightmap" UV map on the current object
            if "Lightmap" in mesh.uv_layers:
                temp_bm = bmesh.new()
                temp_bm.from_mesh(mesh)

                # Get the UV layer from the "Lightmap" UV map
                temp_uv_layer = temp_bm.loops.layers.uv.get("Lightmap")

                if temp_uv_layer:
                    # Transform the temporary bmesh to the object's world space
                    temp_bm.transform(obj.matrix_world)

                    # Loop over each face in the temporary bmesh
                    for face in temp_bm.faces:
                        # Create a list of the corresponding vertices in the combined bmesh
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

                        # Copy the UV coordinates from the "Lightmap" UV layer
                        for loop_dest, loop_src in zip(bm_face.loops, face.loops):
                            loop_dest[uv_layer].uv = loop_src[temp_uv_layer].uv

                # Free the temporary bmesh
                temp_bm.free()

        # Write the combined bmesh to the new mesh
        bm.to_mesh(new_mesh)
        bm.free()

        # Ensure the new object does not have any materials
        new_object.data.materials.clear()

        # Update the mesh
        new_mesh.update()

        return new_object
    
    def _prepare_objects_for_baking(self, mesh_objects, bake_object):
        # Ensure the bakeable mesh isn't visible in the render.
        bake_object.hide_render = True
        
        bake_object.select_set(True)
        # Select all mesh_objects and make the bake_object active so "Selected ot Active" baking works.
        bpy.ops.object.select_all(action='DESELECT')
        for obj in mesh_objects:
            obj.select_set(True)
            
        bpy.context.view_layer.objects.active = bake_object
    
    def _create_bake_material(self, bake_object):
        # Create a new material
        bake_material_name = "PreviewBakeMaterial"
        
        # check if the material already exists
        
        existing_material = bpy.data.materials.get(bake_material_name)
        if existing_material:
            bake_material = existing_material
        else:
            bake_material = bpy.data.materials.new(name=bake_material_name)
        
        bake_object.data.materials.append(bake_material)
        
        bake_material.use_nodes = True
        node_tree = bake_material.node_tree
        nodes = node_tree.nodes
        image_node = nodes.new(type='ShaderNodeTexImage')
        image_node.image = self.bake_image
        node_tree.nodes.active = image_node

    def _setup_bake_settings(self):
        """ Set up bake settings for diffuse lightmap baking. """
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = 128
        bpy.context.scene.cycles.use_denoising = False

        bpy.context.scene.cycles.bake_type = 'DIFFUSE'
        bpy.context.scene.render.bake.use_pass_direct = True
        bpy.context.scene.render.bake.use_pass_indirect = True
        bpy.context.scene.render.bake.use_pass_color = False
        
        bpy.context.scene.render.bake.use_selected_to_active = True

    def execute(self, context):
        # 1. Validate that the selected objects are suitable for lightmapping.
        print("Validating mesh objects...")
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not self._validate_mesh_objects(context, mesh_objects):
            return {'CANCELLED'}
        
        self._select_correct_uv(mesh_objects)
        
        # 2. Create an image to bake to, and a new bake object to be baked to.
        self.bake_image = bpy.data.images.new("BakeImage", width=1024, height=1024)
        bake_object = self._create_bakeable_object(mesh_objects)
        self._create_bake_material(bake_object)
        self._prepare_objects_for_baking(mesh_objects, bake_object)
        
        self._setup_bake_settings()
        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)  # Check every 0.5 seconds
        context.window_manager.modal_handler_add(self)
        bpy.ops.object.bake('INVOKE_DEFAULT', type='DIFFUSE') # 'INVOKE_DEFAULT' will give us the progress bar.

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            # Check if the image has been modified (baking should make the image 'dirty')
            if self.bake_image.is_dirty:
                print("Baking finished!")
                context.window_manager.event_timer_remove(self._timer)
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        return {'CANCELLED'}

def register():
    print("Registering lightmapper_operators")
    bpy.utils.register_class(LIGHTMAPPER_OT_create_lightmap_uv)
    bpy.utils.register_class(LIGHTMAPPER_OT_bake_lightmap)

def unregister():
    bpy.utils.unregister_class(LIGHTMAPPER_OT_create_lightmap_uv)
    bpy.utils.unregister_class(LIGHTMAPPER_OT_bake_lightmap)

if __name__ == "__main__":
    register()
