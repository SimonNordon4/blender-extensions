import bpy
from bpy.props import EnumProperty, StringProperty  # type: ignore

class LIGHTMAPPER_PT_properties(bpy.types.PropertyGroup):
    lightmap_resolution: EnumProperty(
        name="Lightmap Resolution",
        description="Choose the resolution for the lightmap",
        items=[
            ('512', "512", "512x512 pixels"),
            ('1024', "1k", "1024x1024 pixels"),
            ('2048', "2k", "2048x2048 pixels"),
            ('4096', "4k", "4096x4096 pixels"),
            ('8192', "8k", "8192x8192 pixels"),
        ],
        default='2048'
    )  # type: ignore

    export_path: StringProperty(
        name="Export Path",
        description="Path to export the lightmap",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
    )  # type: ignore

def register():
    print("Registering lightmapper_properties")
    bpy.utils.register_class(LIGHTMAPPER_PT_properties)
    bpy.types.Scene.lightmapper_properties = bpy.props.PointerProperty(type=LIGHTMAPPER_PT_properties)

def unregister():
    del bpy.types.Scene.lightmapper_properties
    bpy.utils.unregister_class(LIGHTMAPPER_PT_properties)
