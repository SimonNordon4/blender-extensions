# Use Github as a Blender Extension Repository

## Setting up the Repo.

1. Create a new repository on Github.
2. Turn it into a github page. Settings -> Pages -> Source -> Main

## Creating the Addon.

1. Create a new directory for the addon.
2. add a ```blender_manifest.toml``` file with this code:
```toml
schema_version = "1.0.0"
id = "id_of_your_addon"
version = "1.0.0"
name = "Name of your addon"
tagline = "This is a very cool Add On"
maintainer = "Your Name <email@address.com>"
type = "add-on"
tags = ["Object"]
blender_version_min = "4.2.0"
license = [
  "SPDX:GPL-2.0-or-later",
]
```
3. Add a ```__init__.py``` file with this code:
```python
def register():
    print("Hello World")
def unregister():
    print("Goodbye World")
```
4. Zip your addon subdirectory.
```bash
Compress-Archive -Path ".\id_of_your_addon" -DestinationPath "id_of_your_addon.zip" -Force
```
5. Use Blender command line to generate the extension.
```bash
blender --command extension server-generate --repo-dir={REPO_DIR} --html
```

6. Push your changes.

7. Get the github page url to your index.json, it will look something like this:
```html
https://{GITHUB_USER_NAME}.github.io/{REPO_NAME}/index.json
```

8. Add the url to the Blender preferences -> Get Extensions -> Repositories -> Add -> Paste the url.

## Theory

The new blender extensions allows you to create a static repository, allowing blender to download and update addons from a url.

https://docs.blender.org/manual/en/latest/advanced/extensions/creating_repository/static_repository.html

Github allows us to create a webpage from our repository, by doing this, we can give Blender the url our github page, and it will be able to download and update our addons as we push changes.

The index.json is a catalog of all addons in the repository (there can be multiple). It does this by pointing to the zip files of each of the addons.

In order for the zip files to be recognized as addons, they need to have a ```blender_manifest.toml``` file, which contains metadata about the addon, and a ```__init__.py``` file, which is the entry point of the addon.

I wont go into how addons work, all you need to know is that when an addon is enabled, the register function is called, and when it is disabled, the unregister function is called. This is the starting point for every addon.

## Using this repo to get started.

This repository contains additional files that make it easier to get started creating addons.

By running ```ui.py``` you will get a window that allows you to create a new addon, as well as building your extensions.

![Image of custom ui](/images/addon_manager.png)

```Create Addon from Template``` will create a new subdirectory with the necessary files to get started.

```Zip Addons``` will zip all valid subdirectories in a zip file.

```Build Blender Extensions``` Will run the blender command to generate the index.json

```entry.py``` is an optional script that allows you to run an addons code from an attached blender instance without installing the addon. This is useful when actively developing an addons and making changes quickly.