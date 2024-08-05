https://simonnordon4.github.io/blender-extensions/index.json



blender --command extension server-generate --repo-dir=E:\repos\blender-extensions\ --html

Compress-Archive -Path ".\hello-world" -DestinationPath "hello-world.zip" -Force

1. Create a new directory for the extension.
2. Compres the directory into a zip file.
3. Run blender extension command.
4. Upload the zip file to the server.
5. Ensure repo is public and a website page.

References:
    https://docs.blender.org/manual/en/latest/advanced/extensions/creating_repository/static_repository.html