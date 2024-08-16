import bpy

import bpy.utils

class RipperFixPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_ripper_fix_panel"
    bl_label = "Fix Panel"
    bl_description = "This is a fix panel, for fixing the addon."
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Ripper"
    bl_order = 2
    
    @classmethod
    def poll(cls, context):
        return context.object is not None
    
    def draw_header(self, context):
        layout = self.layout
    
    def draw(self, context):
        layout = self.layout
        layout.operator("ripper.fix_objects_operator", text="Fix Objects")
        layout.operator("ripper.clean_names_operator", text="Clean Names")
        
        box = layout.box()
        box.label(text="Rename Data")

        row = box.row()
        row.alignment = 'EXPAND'
        row.operator("ripper.rename_data_operator", text="Meshes").data_type = 'MESH'
        row.operator("ripper.rename_data_operator", text="Materials").data_type = 'MATERIAL'
        row.operator("ripper.rename_data_operator", text="Images").data_type = 'IMAGE'
        
class FixObjectsOperator(bpy.types.Operator):
    bl_idname = "ripper.fix_objects_operator"
    bl_label = "Fix Objects"
    
    def execute(self, context):
        # select all mesh objects and remove doubles
        view_layer_objects = bpy.context.view_layer.objects

        for obj in view_layer_objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.editmode_toggle()
        
        # select all object again
        for obj in view_layer_objects:
            obj.select_set(True)
        
        # apply rotation adn scale to all objects
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        
        return {"FINISHED"}
        
        
        
class CleanObjectNamesOperator(bpy.types.Operator):
    bl_idname = "ripper.clean_names_operator"
    bl_label = "Clean Names"
    
    def execute(self, context):

        for obj in bpy.context.selected_objects:
            obj.name = ''.join([' ' + char if char.isupper() and (i == 0 or not obj.name[i-1].isspace()) else char for i, char in enumerate(obj.name)])
            obj.name = obj.name.lower()    
            obj.name = obj.name.replace(" ", "_")
            obj.name = obj.name.replace("model", "")
            obj.name = obj.name.replace("level", "t")
            obj.name = obj.name.replace("lvl", "t")
            
            # Remove any leading non-alphanumeric characters (including _)
            while obj.name and not obj.name[0].isalnum():
                obj.name = obj.name[1:]
            # Ensure no consecutive underscores
            while '__' in obj.name:
                obj.name = obj.name.replace('__', '_')
        return {"FINISHED"}

    
class RenameDataOperator(bpy.types.Operator):
    bl_idname = "ripper.rename_data_operator"
    bl_label = "Rename Data"
    
    data_type: bpy.props.StringProperty(name="Data Type", default="MESH")
    
    def execute(self, context):
        
        
        data_type = self.data_type
        
        if data_type == 'MESH':
            self.report({'INFO'}, "Renaming Meshes")
            for obj in bpy.context.selected_objects:
                obj.data.name = obj.name
            
        elif data_type == 'MATERIAL':
            self.report({'INFO'}, "Renaming Materials")
            for obj in bpy.context.selected_objects:
                if obj.type == 'MESH':
                    for slot in obj.material_slots:
                        slot.material.name = obj.name
                    
        elif data_type == 'IMAGE':
            for obj in bpy.context.selected_objects:
                if obj.type == 'MESH':
                    for slot in obj.material_slots:
                        if slot.material.use_nodes:
                            for node in slot.material.node_tree.nodes:
                                if node.type == 'BSDF_PRINCIPLED':
                                    if node.inputs['Base Color'].is_linked:
                                        if node.inputs['Base Color'].links[0].from_node.type == 'TEX_IMAGE':
                                            node.inputs['Base Color'].links[0].from_node.image.name = obj.name
        return {"FINISHED"}
    

        
def register():
    bpy.utils.register_class(RipperFixPanel)
    bpy.utils.register_class(FixObjectsOperator)
    bpy.utils.register_class(CleanObjectNamesOperator)
    bpy.utils.register_class(RenameDataOperator)
    
def unregister():
    bpy.utils.unregister_class(RipperFixPanel)
    bpy.utils.unregister_class(FixObjectsOperator)
    bpy.utils.unregister_class(CleanObjectNamesOperator)
    bpy.utils.unregister_class(RenameDataOperator)
    