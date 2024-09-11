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
        self._setup_bake_settings()
        # check a mesh is selected
        if not any(obj.type == 'MESH' for obj in context.selected_objects):
            self.report({'ERROR'}, "No mesh objects selected.")
            return {'CANCELLED'}
        
        # create a new image to bake
        bake_image = bpy.data.images.new("BakeImage", width=1024, height=1024)
        
        # get the first material in the object being baked, create an image node with our new image and make it active
        obj = context.selected_objects[0]
        mat = obj.material_slots[0].material
        node_tree = mat.node_tree
        nodes = node_tree.nodes
        image_node = nodes.new(type='ShaderNodeTexImage')
        image_node.image = bake_image
        node_tree.nodes.active = image_node
        
        print("Baking started!")
        #bake object
        bpy.ops.object.bake('INVOKE_DEFAULT', type='DIFFUSE')
        
        print("Baking finished!")
        
        return {'FINISHED'}

    
        
        

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
