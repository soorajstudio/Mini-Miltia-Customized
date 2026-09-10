# Image Replacement Guide for Mini Militia Classic (MMC)

All images from the APK have been extracted into this directory:

## Folder Structure

1. categorized_preview_hdr/
   Organized by category using the highest quality (HDR) images for easy editing:
   - Maps_and_Tiles/ -> worldMap.png, tile64_new.png (default tiles), tile64Desert_new.png, tile64Moon_new.png, tile64Snow_new.png, grass.png, rock_new.png
   - UI_and_Menus/ -> menuTexture.png (main buttons & HUD), dialog.png (popup boxes), nameplate*.png (player tags), ammoText_new.png, font02_new.png
   - Backgrounds/ -> bg_new.png, bgDesert_new.png, bgMoon_new.png, bgSnow_new.png
   - Title_and_Logos/ -> title_ret_logo.png, title_ret_new.png, classic.png
   - Characters_and_Weapons/ -> partsTexture.png (skins, weapons, body parts), bullet_new.png, shell_new.png
   - VFX_and_Effects/ -> blast_new.png, smoke_new.png, streak_new.png (jetpack trail), blood_new.png

2. raw_assets_for_apk/
   Matches the exact internal APK file hierarchy:
   - assets/hdr/ (High-res screens - 1080p/1440p)
   - assets/hd/ (Standard screens - 720p)
   - assets/sd/ (Low-res screens)

3. app_icons/
   Contains the app launcher icons.

## Rules When Editing Textures
1. Do NOT change canvas dimensions: Keep image width and height identical to the original.
2. Preserve transparency: Save as 32-bit PNG with alpha channel intact.
3. Sprite alignment: For sprite sheets like menuTexture.png and tile64_new.png, keep your new graphics within the exact boundary of the original icons, or buttons will be misaligned in-game.

## How to Re-pack with Apktool
1. Decompile:
   apktool d com.appsomniacs.mmc-0-14-4-arm64-v8a-android60.apk -o decompiled_app
2. Replace:
   Copy your edited PNGs into decompiled_app/assets/hdr/ and decompiled_app/assets/hd/
3. Rebuild:
   apktool b decompiled_app -o my_modded_app.apk
4. Sign:
   java -jar uber-apk-signer.jar -a my_modded_app.apk
