from . import auto_load

print("Loading template")

def register():
    print("Registering template")
    auto_load.test()


def unregister():
    auto_load.unregister()
    


    
