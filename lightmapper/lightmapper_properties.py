import bpy
from bpy.props import EnumProperty, StringProperty  # type: ignore

class LIGHTMAPPER_PT_properties(bpy.types.PropertyGroup):
    lightmap_width: bpy.props.IntProperty(
        name="Lightmap Width",
        description="Width of the lightmap in pixels",
        default=1024,
        min=4,
        max=8192
    )  # type: ignore

    lightmap_height: bpy.props.IntProperty(
        name="Lightmap Height",
        description="Height of the lightmap in pixels",
        default=1024,
        min=4,
        max=8192
    )  # type: ignore

    export_path: StringProperty(
        name="Export Path",
        description="Path to export the lightmap",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
    )  # type: ignore
    
    bake_name: EnumProperty(
        name="Bake Name",
        description="Choose the bake target",
        items=[
            ('ACTIVE_OBJECT', "Active Object", "Bake the active object"),
            ('COLLECTION', "Collection", "Bake the collection"),
        ],
        default='ACTIVE_OBJECT'
    )  # type: ignore
    
    num_samples: bpy.props.IntProperty(
            name="Number of Samples",
            description="Number of samples for baking",
            default=64,
            min=8,
            max=256
        )  # type: ignore

    

def register():
    print("Registering lightmapper_properties")
    bpy.utils.register_class(LIGHTMAPPER_PT_properties)
    bpy.types.Scene.lightmapper_properties = bpy.props.PointerProperty(type=LIGHTMAPPER_PT_properties)

def unregister():
    del bpy.types.Scene.lightmapper_properties
    bpy.utils.unregister_class(LIGHTMAPPER_PT_properties)
