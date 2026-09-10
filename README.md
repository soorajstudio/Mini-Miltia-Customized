from pathlib import Path

readme = r"""# Mini Militia Customized

A personal customization project for the Android version of Mini Militia (Doodle Army 2), focused on redesigning the game's main-menu presentation, replacing visual assets, cleaning up selected UI elements, and automating the APK build/sign/install workflow.

> ⚠️ Disclaimer  
> This is an unofficial, personal customization project. It is not affiliated with, endorsed by, or sponsored by Miniclip, Appsomniacs, or the original Mini Militia developers. Mini Militia and its related assets remain the property of their respective owners. Do not redistribute copyrighted game files or modified APKs unless you have the necessary rights and permission.

## What this project does

The repository contains the source APK used as the customization base, visual assets, extracted/separated sprites, helper scripts, and the generated customized APK.

The current build script performs several modifications:

- Custom Android launcher icon generation for multiple screen densities.
- Custom home/menu background generation for HDR, HD, and SD resolutions.
- Custom splash-screen background generation.
- Removal of the extra title/menu overlay so the customized background can remain visible.
- Changes the former `QUICK PLAY` menu button to `SETTINGS`.
- Changes the former `PLAY ONLINE` menu button to `AVATARS`.
- Reroutes those menu buttons to their corresponding handlers.
- Hides selected UI elements such as login/status, armory, duplicate avatars, friends, officers, badges, tokens/coin, rank/progress information, and selected menu buttons.
- Disables selected in-game ad triggers.
- Removes selected compliance/terms popup flows from the customized build.
- Restricts map registration to the Outpost map in the patched native library.
- Rebuilds character/avatar sprite sheets from individually separated images.
- Rebuilds UI/menu sprite sheets from individually separated images.
- Rebuilds map tile sheets from individual tile images.
- Generates HDR, HD, and SD versions of rebuilt sprite sheets.
- Packages the modified assets into a new APK.
- Signs the resulting APK with `uber-apk-signer`.
- Uses ADB to install and launch the customized APK on a connected Android device.

The implementation can be found primarily in [`build_and_install.py`](./build_and_install.py), with additional sprite-repacking functionality in [`mmg app/repack_sprites.py`](./mmg%20app/repack_sprites.py).

## Repository structure

```text
Mini-Miltia-Customized/
│
├── build_and_install.py
├── README.md
│
├── mmg app/
│   ├── apk_images/
│   │   ├── README.txt
│   │   └── ...custom/extracted image assets
│   │
│   ├── separated_images/
│   │   ├── characters_and_avatars/
│   │   ├── ui_and_menus/
│   │   └── map tile assets
│   │
│   ├── com.appsomniacs.mmc-0-14-4-arm64-v8a-android60.apk
│   ├── MiniMilitia_Modded.apk
│   ├── presMix.mp3
│   ├── repack_sprites.py
│   └── uber-apk-signer.jar
│
├── current_phone_screen.png
├── phone_home_bg_verified.png
├── phone_home_menu_final.png
└── ...other visual reference/customization assets
