# TESVFontForge
A tool that converts and processes your preferred font files (TTF/OTF) into the format (SWF) usable within the Skyrim game.

## Requirements
Please install the following tools beforehand.

* **[UV](https://docs.astral.sh/uv/)**  
A tool that automatically manages the Python runtime environment. Simply launch PowerShell and run the command below to complete the installation.

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Usage
The basic workflow is described below. For more details, refer to the [User Manual](/docs/user/README.md).

### 1. Download the Tool
Download the latest version from [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/174143) or [GitHub](https://github.com/SkyLaptor/TESVFontForge/releases).

### 2. Prepare Your Font
Have the font you want to use ready.

> [!TIP]
> OTF format is also supported, but if you want to speed up conversion, it is recommended to convert to TTF in advance using the following command:
> `uv run otf2ttf [font file]`

### 3. [Optional] Process the Font
If you want to adjust weight or width, launch the GUI by running `run.cmd` in the top folder.
Use the `Individual: Font Processing` tab to adjust while previewing.

![TESVFontForge-Font Processing](https://github.com/user-attachments/assets/281af337-622f-4e6f-89df-f13e74602689)

### 4. Embed into SWF
To have the game recognize the font, convert it to SWF format.
In the GUI's `Individual: SWF Embed` tab, specify the output destination and internal font name, then execute.

![TESVFontForge-SWF Embed](https://github.com/user-attachments/assets/3f6662ba-a8ef-4102-af41-fa74067901e5)

### 5. Install into the Game
To have the game load the generated SWF, you would normally need to go through very cumbersome steps such as editing `fontconfig.txt` and creating definition files.

To automate these tedious tasks and install fonts in the most reliable and straightforward way, we strongly recommend using the companion tool [TESVFontPresetBuilder](https://github.com/SkyLaptor/TESVFontPresetBuilder).

Please refer to the linked page for usage instructions and how to apply changes to the game.


## Tips / Troubleshooting
### The tool won't launch / launches slowly
On the first run, the tool automatically sets up the Python environment and downloads external tools, which may take several minutes. If the screen appears frozen, please wait a moment.
*If it exits with an error, please check your internet connection.*

### Processing never finishes
Font processing (such as changing weight) consumes a large amount of PC resources (CPU/memory). If the operation is noticeably slow, try closing other applications before running it.

### I want to perform batch processing
For batch processing, you need to prepare and load a recipe file for the corresponding operation. Recipe templates with explanations are available in the `docs/user/templates` folder.

* **[Font Processing]**: `recipe_template_for_font_processing.yml`
* **[SWF Embed]**: `recipe_template_for_swf_embed.yml`


## Credits / Usage
* When publishing fonts created with this tool as a mod, no notification is required, but mentioning the tool name would be greatly appreciated and encourages further development.
