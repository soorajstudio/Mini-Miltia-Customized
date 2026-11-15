# repack_sprites.py
import os, plistlib, zipfile, io, re, sys
from PIL import Image

APK_PATH = 'com.appsomniacs.mmc-0-14-4-arm64-v8a-android60.apk'
SEPARATED_DIR = 'separated_images'
OUTPUT_RAW_DIR = 'apk_images/raw_assets_for_apk'

# If user provided a decompiled folder path as argument (e.g. python repack_sprites.py my_decompiled_folder)
DECOMPILED_DIR = sys.argv[1] if len(sys.argv) > 1 else None

z = zipfile.ZipFile(APK_PATH)

def repack_plist_atlas(atlas_name, plist_rel_path, png_rel_path, individual_dir):
    print(f'[*] Repacking {atlas_name}...')
    img = Image.open(io.BytesIO(z.read(png_rel_path))).convert('RGBA')
    plist_data = plistlib.loads(z.read(plist_rel_path))
    frames = plist_data.get('frames', {})

    flat_dir = os.path.join(individual_dir, 'all')
    replaced_count = 0

    for name, frame in frames.items():
        src_path = None
        # Check flat dir first
        candidate = os.path.join(flat_dir, name)
        if os.path.exists(candidate):
            src_path = candidate
        else:
            # Check subdirs
            for sub in os.listdir(individual_dir):
                candidate_sub = os.path.join(individual_dir, sub, name)
                if os.path.isfile(candidate_sub):
                    src_path = candidate_sub
                    break
        
        if src_path and os.path.exists(src_path):
            sprite_img = Image.open(src_path).convert('RGBA')
            rect_str = frame['textureRect']
            nums = [int(n) for n in re.findall(r'\d+', rect_str)]
            x, y, w, h = nums

            # Resize to expected slot if needed
            if sprite_img.size != (w, h):
                sprite_img = sprite_img.resize((w, h), Image.Resampling.LANCZOS)
            
            # Clear old rect with transparency and paste new sprite
            img.paste((0, 0, 0, 0), (x, y, x + w, y + h))
            img.paste(sprite_img, (x, y), sprite_img)
            replaced_count += 1

    print(f'    Replaced {replaced_count} sprites into {atlas_name} (HDR: {img.size})')

    # Save HDR
    hdr_out = os.path.join(OUTPUT_RAW_DIR, png_rel_path)
    os.makedirs(os.path.dirname(hdr_out), exist_ok=True)
    img.save(hdr_out, format='PNG')

    # Also save downscaled HD (50%) and SD (25%)
    hd_rel = png_rel_path.replace('/hdr/', '/hd/')
    hd_out = os.path.join(OUTPUT_RAW_DIR, hd_rel)
    hd_img = img.resize((img.width // 2, img.height // 2), Image.Resampling.LANCZOS)
    hd_img.save(hd_out, format='PNG')

    sd_rel = png_rel_path.replace('/hdr/', '/sd/')
    sd_out = os.path.join(OUTPUT_RAW_DIR, sd_rel)
    sd_img = img.resize((img.width // 4, img.height // 4), Image.Resampling.LANCZOS)
    sd_img.save(sd_out, format='PNG')

    # If decompiled directory provided, copy there too
    if DECOMPILED_DIR and os.path.isdir(DECOMPILED_DIR):
        for rel_path, out_img in [(png_rel_path, img), (hd_rel, hd_img), (sd_rel, sd_img)]:
            dest = os.path.join(DECOMPILED_DIR, rel_path)
            if os.path.exists(os.path.dirname(dest)):
                out_img.save(dest, format='PNG')
                print(f'    Copied to {dest}')

def repack_map_tiles(tile_name, png_rel_path, individual_dir):
    print(f'[*] Repacking {tile_name}...')
    img = Image.open(io.BytesIO(z.read(png_rel_path))).convert('RGBA')
    replaced_count = 0

    if os.path.exists(individual_dir):
        for f in os.listdir(individual_dir):
            if f.endswith('.png'):
                # Extract tile id or row, col
                m = re.search(r'tile_(\d+)_r(\d+)_c(\d+)', f)
                if m:
                    tile_id, row, col = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    x = 8 + col * 264
                    y = 8 + row * 264
                    tile_img = Image.open(os.path.join(individual_dir, f)).convert('RGBA')
                    if tile_img.size != (256, 256):
                        tile_img = tile_img.resize((256, 256), Image.Resampling.LANCZOS)
                    img.paste((0, 0, 0, 0), (x, y, x + 256, y + 256))
                    img.paste(tile_img, (x, y), tile_img)
                    replaced_count += 1

    print(f'    Replaced {replaced_count} tiles into {tile_name} (HDR: {img.size})')

    hdr_out = os.path.join(OUTPUT_RAW_DIR, png_rel_path)
    os.makedirs(os.path.dirname(hdr_out), exist_ok=True)
    img.save(hdr_out, format='PNG')

    hd_rel = png_rel_path.replace('/hdr/', '/hd/')
    hd_out = os.path.join(OUTPUT_RAW_DIR, hd_rel)
    hd_img = img.resize((img.width // 2, img.height // 2), Image.Resampling.LANCZOS)
    hd_img.save(hd_out, format='PNG')

    sd_rel = png_rel_path.replace('/hdr/', '/sd/')
    sd_out = os.path.join(OUTPUT_RAW_DIR, sd_rel)
    sd_img = img.resize((img.width // 4, img.height // 4), Image.Resampling.LANCZOS)
    sd_img.save(sd_out, format='PNG')

    if DECOMPILED_DIR and os.path.isdir(DECOMPILED_DIR):
        for rel_path, out_img in [(png_rel_path, img), (hd_rel, hd_img), (sd_rel, sd_img)]:
            dest = os.path.join(DECOMPILED_DIR, rel_path)
            if os.path.exists(os.path.dirname(dest)):
                out_img.save(dest, format='PNG')
                print(f'    Copied to {dest}')

if __name__ == '__main__':
    repack_plist_atlas('partsTexture', 'assets/hdr/partsTexture.plist', 'assets/hdr/partsTexture.png', 'separated_images/characters_and_avatars')
    repack_plist_atlas('menuTexture', 'assets/hdr/menuTexture.plist', 'assets/hdr/menuTexture.png', 'separated_images/ui_and_menus')
    repack_map_tiles('tile64_new', 'assets/hdr/tile64_new.png', 'separated_images/map_tiles_default')
    repack_map_tiles('tile64Desert_new', 'assets/hdr/tile64Desert_new.png', 'separated_images/map_tiles_desert')
    repack_map_tiles('tile64Moon_new', 'assets/hdr/tile64Moon_new.png', 'separated_images/map_tiles_moon')
    repack_map_tiles('tile64Snow_new', 'assets/hdr/tile64Snow_new.png', 'separated_images/map_tiles_snow')
    print('\n[+] Repacking complete! Sprite sheets updated for HDR, HD, and SD.')
