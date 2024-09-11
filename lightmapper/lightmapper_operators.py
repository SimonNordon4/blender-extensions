import bpy

import bpy.utils



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
            
    def _create_bake_material(self, bake_object):
        # Create a new material
        bake_material = bpy.data.materials.new(name="BakeMaterial")
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
        
        bpy.context.scene.render.bake.use_selected_to_active = False

    def execute(self, context):
 
        
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not self._validate_mesh_objects(context, mesh_objects):
            return {'CANCELLED'}
        
        self._select_correct_uv(mesh_objects)
        
        # Create a new image to bake
        self.bake_image = bpy.data.images.new("BakeImage", width=1024, height=1024)

        # bake object is current selection
        bake_object = context.active_object
        
        self._create_bake_material(bake_object)

        print("Baking started!")
        
        self._setup_bake_settings()
        
        # Start modal timer to check for bake completion
        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)  # Check every 0.5 seconds
        context.window_manager.modal_handler_add(self)
        bpy.ops.object.bake('INVOKE_DEFAULT', type='DIFFUSE')

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
