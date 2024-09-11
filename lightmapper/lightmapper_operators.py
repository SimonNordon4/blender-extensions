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
    
    def check_context(self, context):
        """ Ensure the object is in a state that supports baking. """
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
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
    
    def correct_context(self, context):
        """ Change the state of the selected objects to work for baking."""
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        self.report({'INFO'}, "Correcting UV Selections.")
        # Ensure that the first UVMap is set to render, and that "Lightmap" UV is selected.
        for obj in mesh_objects:
            # If the lightmap is renderable, set it to the first UVMap. Otherwise respect user choice.
            obj.data.uv_layers[0].active_render = True
            # Ensure the lightmap is selected, as that's the UV we're baking to.
            obj.data.uv_layers["Lightmap"].active = True
            
    def execute(self, context):
        if not self.check_context(context):
            return {'CANCELLED'}
        
        self.correct_context(context)
        
        self.report({'INFO'}, "Lightmap baking started.")
        return {'FINISHED'}
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                # Set up lightmap UV if not present
                if len(obj.data.uv_layers) < 2:
                    obj.data.uv_layers.new(name="Lightmap")
                
                # Set up image for baking
                image = bpy.data.images.new(name=f"{obj.name}_Lightmap", width=1024, height=1024)
                
                # Set up material for baking
                material = obj.active_material
                if not material:
                    material = bpy.data.materials.new(name=f"{obj.name}_Lightmap_Material")
                    obj.data.materials.append(material)
                
                # Set up node for baking
                material.use_nodes = True
                node_tree = material.node_tree
                texture_node = node_tree.nodes.new('ShaderNodeTexImage')
                texture_node.image = image
                
                # Perform bake
                bpy.ops.object.bake(type='COMBINED')
                
        self.report({'INFO'}, "Lightmap baking completed")
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
