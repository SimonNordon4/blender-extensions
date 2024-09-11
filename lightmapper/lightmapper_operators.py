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
    
    def __init__(self):
        self._timer = None
        self.progress = 0
        self.instance = None
        self.finished = False

    def _get_bake_name(self, bake_target):
        active_object = bpy.context.view_layer.objects.active

        if bake_target == 'ACTIVE_OBJECT':
            return active_object.name if active_object else "Unnamed"
        elif bake_target == 'COLLECTION':
            if active_object and active_object.users_collection:
                return active_object.users_collection[0].name
            else:
                return "Unnamed"
        else:
            return "Unnamed"
    
    def _check_mesh_objects(self, context, mesh_objects):
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
    
    def _correct_mesh_objects(self, context, mesh_objects):
        """ Change the state of the selected objects to work for baking."""
        
        self.report({'INFO'}, "Correcting UV Selections.")
        # Ensure that the first UVMap is set to render, and that "Lightmap" UV is selected.
        for obj in mesh_objects:
            # If the lightmap is renderable, set it to the first UVMap. Otherwise respect user choice.
            obj.data.uv_layers[0].active_render = True
            # Ensure the lightmap is selected, as that's the UV we're baking to.
            obj.data.uv_layers["Lightmap"].active = True
            
    def _combine_objects(self, context):
        """ Combine selected objects into one for baking. """
        
        print("Combining objects...")
        
        bpy.ops.object.duplicate()
        # set the active object to the first selected object
        bpy.context.view_layer.objects.active = context.selected_objects[0]
        # Join duplicated objects into one
        bpy.ops.object.join()
        
        # Store the combined object for later deletion
        combined_object = context.active_object
        # rename to temp_bake_name
        combined_object.name = "temp_bake_object"
        return combined_object
        
    def _create_lightmap_image(self, width=2048, height=2048):
        """ Create a new lightmap image for baking. """
        new_image = bpy.data.images.new("LightmapBake", width=width, height=height, float_buffer=True)
        # give the image a name like temp_diffuse_bake_noise
        new_image.name = "temp_lightmap_bake_image"
        return new_image
    
    def _assign_lightmap_image(self, context, combined_object, lightmap_image):
        # Ensure the object has an active material
        if not combined_object.data.materials:
            material = bpy.data.materials.new(name="TempBakeMaterial")
            combined_object.data.materials.append(material)
        
        # Get the active material
        material = combined_object.active_material

        # Ensure the material uses nodes
        if not material.use_nodes:
            material.use_nodes = True

        # Access the material's node tree
        nodes = material.node_tree.nodes
        texture_node = nodes.get('Image Texture')

        # If there's no existing Image Texture node, create one
        if texture_node is None:
            texture_node = nodes.new(type='ShaderNodeTexImage')

        # Assign the lightmap image to the texture node
        texture_node.image = lightmap_image

        # Set the texture node as active for baking
        material.node_tree.nodes.active = texture_node
    
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
        

        
        
    def _setup_compositor(self):
        """ Set up compositor nodes to denoise and save as HDR. """
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree
        tree.nodes.clear()

        render_layer_node = tree.nodes.new('CompositorNodeRLayers')
        denoise_node = tree.nodes.new('CompositorNodeDenoise')
        file_output_node = tree.nodes.new('CompositorNodeOutputFile')

        file_output_node.format.file_format = 'HDR'
        file_output_node.base_path = "//"
        file_output_node.file_slots[0].path = "LightmapResult"

        tree.links.new(render_layer_node.outputs['Image'], denoise_node.inputs['Image'])
        tree.links.new(denoise_node.outputs['Image'], file_output_node.inputs['Image'])
        
    def render_and_save(self):
        """ Render and save the denoised lightmap as an HDR. """
        bpy.ops.render.render(use_viewport=True, write_still=True)
        
        
    def _bake(self, context, bake_image):
        yield 1
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        # Trigger the bake and wait for it to finish
        bpy.ops.object.bake('INVOKE_DEFAULT', type='DIFFUSE')
        
        # Wait for the bake to complete by checking if the image is updated
        while not bake_image.is_dirty:
            yield 1
        
        yield 0
           
    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            try:
                result = next(self.instance)
            except StopIteration:
                self.finish(context)
                return {'FINISHED'}

            if result == -1:
                self.cancel(context)
                return {'CANCELLED'}
            if result == 0:
                self.finish(context)
                return {'FINISHED'}

            self.progress += 1
            context.area.tag_redraw()

        return {'RUNNING_MODAL'}

    def execute(self, context):
    
        print("Adding timer")
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)

        scene = context.scene
        lightmapper_props = scene.lightmapper_properties
        width = lightmapper_props.lightmap_width
        height = lightmapper_props.lightmap_height
        path = lightmapper_props.export_path
        bake_target = lightmapper_props.bake_target

        print(f"Lightmap width: {width}, height: {height}, path: {path}, bake_target: {bake_target}")

        # Setup and validate bake
        bake_name = self._get_bake_name(bake_target)
        print(f"Bake name: {bake_name}")
        bake_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        print(f"Bake objects: {bake_objects}")
        self._check_mesh_objects(context, bake_objects)
        self._correct_mesh_objects(context, bake_objects)

        # Combine objects for faster baking
        combined_object = self._combine_objects(context)
        print(f"Combined object: {combined_object}")

        # Create lightmap image for baking
        lightmap_image = self._create_lightmap_image(width, height)
        print(f"Lightmap image created: {lightmap_image}")
        self._assign_lightmap_image(context, combined_object, lightmap_image)

        # Start bake
        print("Setting up bake settings")
        self._setup_bake_settings()
        print("Setting up bake modal instance.")
        self.instance = self._bake(context, lightmap_image)
    
        print("Baking has started")

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        return {'CANCELLED'}

    def finish(self, context):
        if self.finished:
            return {'FINISHED'}  # If already finished, prevent re-entering the finish logic

        print("Finishing Model")
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)

        self.report({'INFO'}, "Bake finished successfully.")
        self.finished = True  # Set the flag to True once finished
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text=f"Baking Progress: {self.progress}%")
        
        

from bpy.utils import register_class, unregister_class
from .lightmapper_properties import LIGHTMAPPER_PT_properties

def register():
    print("Registering lightmapper_operators")
    bpy.utils.register_class(LIGHTMAPPER_OT_create_lightmap_uv)
    bpy.utils.register_class(LIGHTMAPPER_OT_bake_lightmap)

def unregister():
    bpy.utils.unregister_class(LIGHTMAPPER_OT_create_lightmap_uv)
    bpy.utils.unregister_class(LIGHTMAPPER_OT_bake_lightmap)

if __name__ == "__main__":
    register()
