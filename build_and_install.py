import os, sys, zipfile, io, re, plistlib, subprocess, struct, hashlib, zlib
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # mmg app\ (script lives here)
APP_DIR  = BASE_DIR                                      # same folder — no more sub-dir
ROOT_DIR = os.path.dirname(BASE_DIR)                    # mmcg\ parent — APK output goes here

SRC_APK    = os.path.join(APP_DIR,  "com.appsomniacs.mmc-0-14-4-arm64-v8a-android60.apk")
TARGET_APK = os.path.join(ROOT_DIR, "MiniMilitia_Modded.apk")   # output to mmcg\ root
UBER_SIGNER = os.path.join(APP_DIR, "uber-apk-signer.jar")
def _find_adb():
    """Auto-detect adb.exe from common Android SDK locations or PATH."""
    import shutil
    # 1. Check PATH first
    found = shutil.which("adb")
    if found:
        return found
    # 2. Search common per-user SDK installs
    for user_dir in os.listdir(r"C:\Users"):
        candidate = os.path.join(r"C:\Users", user_dir,
                                 "AppData", "Local", "Android", "Sdk",
                                 "platform-tools", "adb.exe")
        if os.path.isfile(candidate):
            return candidate
    return None

ADB_EXE = _find_adb() or r"adb"  # fallback to bare 'adb' (must be on PATH)

SEPARATED_DIR = os.path.join(APP_DIR, "separated_images")
ICON_SRC = os.path.join(APP_DIR, "apk_images", "app icon.png")

def generate_icons():
    """Generate all density icons from 'app icon.png'"""
    if not os.path.exists(ICON_SRC):
        print(f"[-] Icon source not found: {ICON_SRC}")
        return {}

    print(f"[*] Generating Android launcher icons from: {os.path.basename(ICON_SRC)}")
    src_img = Image.open(ICON_SRC).convert("RGBA")

    densities = {
        "mdpi": {"standard": 48, "fg": 108},
        "hdpi": {"standard": 72, "fg": 162},
        "xhdpi": {"standard": 96, "fg": 216},
        "xxhdpi": {"standard": 144, "fg": 324},
        "xxxhdpi": {"standard": 192, "fg": 432}
    }

    icon_files = {}
    for density, sizes in densities.items():
        std_size = sizes["standard"]
        fg_size = sizes["fg"]

        # Standard icon
        std_img = src_img.resize((std_size, std_size), Image.Resampling.LANCZOS)
        buf_std = io.BytesIO()
        std_img.save(buf_std, format="PNG")
        icon_files[f"res/mipmap-{density}-v4/mmc_ic_launcher.png"] = buf_std.getvalue()

        # Round icon (circle mask)
        mask = Image.new("L", (std_size, std_size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, std_size, std_size), fill=255)
        rnd_img = std_img.copy()
        rnd_img.putalpha(mask)
        buf_rnd = io.BytesIO()
        rnd_img.save(buf_rnd, format="PNG")
        icon_files[f"res/mipmap-{density}-v4/mmc_ic_launcher_round.png"] = buf_rnd.getvalue()

        # Foreground adaptive icon
        fg_img = Image.new("RGBA", (fg_size, fg_size), (0, 0, 0, 0))
        content_size = int(fg_size * 0.72)
        scaled_content = src_img.resize((content_size, content_size), Image.Resampling.LANCZOS)
        offset = (fg_size - content_size) // 2
        fg_img.paste(scaled_content, (offset, offset))
        buf_fg = io.BytesIO()
        fg_img.save(buf_fg, format="PNG")
        icon_files[f"res/mipmap-{density}-v4/mmc_ic_launcher_foreground.png"] = buf_fg.getvalue()

    print(f"[+] Generated {len(icon_files)} launcher icon assets.")
    return icon_files

# --- Custom Image Sources (in BASE_DIR / project root) ---
TITLE_RET_LOGO_SRC = os.path.join(APP_DIR, "apk_images", "title ret logo.png")  # intro centre icon
TITLE_RET_SRC      = os.path.join(APP_DIR, "apk_images", "title ret.png")       # intro / splash background
TITLE_RET2_SRC     = os.path.join(APP_DIR, "apk_images", "title ret 2.png")     # home page background

def generate_background_images():
    """
    Injects all three custom title/background images:
      - title ret logo.png  -> assets/{density}/title_ret_logo.png  (intro centre PNG icon)
      - title ret.png       -> assets/{density}/title_ret_new.png   (intro/splash background)
      - title ret 2.png     -> assets/{density}/bg_new.png          (home page background, BEHIND buttons)
      - title_ret2_new.png  -> 1x1 transparent                      (home overlay CLEARED so buttons show)
    """
    bg_files = {}

    # ── 1. Intro centre logo (title_ret_logo.png) ──────────────────────────
    if not os.path.exists(TITLE_RET_LOGO_SRC):
        print(f"[-] title ret logo.png not found: {TITLE_RET_LOGO_SRC}")
    else:
        print(f"[*] Setting intro logo from: {os.path.basename(TITLE_RET_LOGO_SRC)}")
        logo_img = Image.open(TITLE_RET_LOGO_SRC).convert("RGBA")
        # Original dimensions: HDR 1261x1287, HD 631x644, SD 315x322
        logo_resolutions = {
            "assets/hdr/title_ret_logo.png": (1261, 1287),
            "assets/hd/title_ret_logo.png":  (631,  644),
            "assets/sd/title_ret_logo.png":  (315,  322),
        }
        for path, (w, h) in logo_resolutions.items():
            resized = logo_img.resize((w, h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            resized.save(buf, format="PNG")
            bg_files[path] = buf.getvalue()
        print(f"    [+] Injected title_ret_logo.png at 3 densities.")

    # ── 2. Intro / splash background (title_ret_new.png) ───────────────────
    if not os.path.exists(TITLE_RET_SRC):
        print(f"[-] title ret.png not found: {TITLE_RET_SRC}")
    else:
        print(f"[*] Setting intro background from: {os.path.basename(TITLE_RET_SRC)}")
        intro_img = Image.open(TITLE_RET_SRC).convert("RGBA")
        splash_resolutions = {
            "assets/hdr/title_ret_new.png": (2272, 1536),
            "assets/hd/title_ret_new.png":  (1136, 768),
            "assets/sd/title_ret_new.png":  (568,  384),
        }
        for path, (w, h) in splash_resolutions.items():
            resized = intro_img.resize((w, h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            resized.save(buf, format="PNG")
            bg_files[path] = buf.getvalue()
        print(f"    [+] Injected title_ret_new.png at 3 densities.")

    # ── 3 & 4. Home page background ─────────────────────────────────────────
    # title_ret2_new.png is the ACTUAL rendered background of the home menu.
    # bg_new.png is a secondary layer that may or may not show.
    # So we inject the custom background into BOTH to ensure it always shows.
    if not os.path.exists(TITLE_RET2_SRC):
        print(f"[-] title ret 2.png not found: {TITLE_RET2_SRC}")
    else:
        print(f"[*] Setting home page background from: {os.path.basename(TITLE_RET2_SRC)}")
        home_img = Image.open(TITLE_RET2_SRC).convert("RGBA")

        # Inject into title_ret2_new.png (the main home background layer)
        title_ret2_resolutions = {
            "assets/hdr/title_ret2_new.png": (2048, 1536),
            "assets/hd/title_ret2_new.png":  (1136, 768),
            "assets/sd/title_ret2_new.png":  (480,  320),
        }
        for path, (w, h) in title_ret2_resolutions.items():
            resized = home_img.resize((w, h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            resized.save(buf, format="PNG")
            bg_files[path] = buf.getvalue()
        print(f"    [+] Injected title_ret2_new.png at 3 densities (main home bg).")

        # Also inject into bg_new.png (secondary background layer)
        bg_resolutions = {
            "assets/hdr/bg_new.png": (2020, 1338),
            "assets/hd/bg_new.png":  (1010, 669),
            "assets/sd/bg_new.png":  (505,  337),
        }
        for path, (w, h) in bg_resolutions.items():
            resized = home_img.resize((w, h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            resized.save(buf, format="PNG")
            bg_files[path] = buf.getvalue()
        print(f"    [+] Injected bg_new.png at 3 densities (secondary home bg).")

    print("[+] Home background injected — buttons remain visible on top.")

    print(f"[+] Generated {len(bg_files)} total background/logo assets.")
    return bg_files


def patch_terms_and_conditions_json():
    """Bypasses Terms and Conditions / Privacy Policy consent popups"""
    print("[*] Patching Terms & Conditions consent flow JSONs...")
    files = {}

    # Bypass terms of service & privacy alert
    tos_bypass = """{
  "states": [{
    "id": 12,
    "is_initial_state": true,
    "type": "event",
    "name": "tos_ok",
    "destination_state_id": 99
  }, {
    "id": 99,
    "type": "reinit"
  }]
}"""
    files["res/raw/applovin_consent_flow_terms_of_service_and_privacy_policy.json"] = tos_bypass.encode("utf-8")
    files["res/raw/applovin_consent_flow_privacy_policy.json"] = tos_bypass.encode("utf-8")

    # Bypass unified CMP
    cmp_bypass = """{
  "states": [{
    "id": 99,
    "is_initial_state": true,
    "type": "reinit"
  }]
}"""
    files["res/raw/applovin_consent_flow_unified_cmp.json"] = cmp_bypass.encode("utf-8")
    return files

def patch_libcocos2dcpp(z):
    """
    1. Removes in-game compliance/terms popup
    2. Replaces top line buttons: QUICK PLAY -> SETTINGS (with cog.png gear icon), PLAY ONLINE -> AVATARS
    3. Reroutes button handlers to open Settings and Avatars
    4. Disables top ad banner, Pro Pass, C++ ad triggers (banner, interstitial, rewarded)
    5. Cleanly hides Login, Armory, duplicate Avatars, Friends, Officers, Tokens & Coin
    6. Removes rank title, progress bar, numeric XP, tokens string, spin.png string
    7. Removes STATS and SCORES buttons from MenuLayer
    8. Removes bottom-left green VersionLabel (*BETA* v0.14.4 (88))
    9. Restricts engine map registration to Outpost only
    """
    print("[*] Patching libcocos2dcpp.so for menu buttons, ad blocking, and UI clean-up...")
    so = bytearray(z.read("lib/arm64-v8a/libcocos2dcpp.so"))

    # 1. String replacements:
    # "QUICK PLAY\0quick.png\0" (21 bytes) -> "SETTINGS\0\0\0cog.png\0\0\0" (21 bytes)
    str_offset1 = 0x108792F
    orig1 = so[str_offset1 : str_offset1 + 21]
    if orig1.startswith(b"QUICK PLAY\x00") or orig1.startswith(b"SETTINGS\x00"):
        new1 = b"SETTINGS\x00\x00\x00cog.png\x00\x00\x00"
        so[str_offset1 : str_offset1 + 21] = new1
        print("[+] Replaced 'QUICK PLAY' -> 'SETTINGS' (with cog.png gear icon)")

    # "PLAY ONLINE\0online.png\0" (23 bytes) -> "AVATARS\0\0\0\0\0avatar.png\0" (23 bytes)
    str_offset2 = str_offset1 + 21
    orig2 = so[str_offset2 : str_offset2 + 23]
    if orig2.startswith(b"PLAY ONLINE\x00") or orig2.startswith(b"AVATARS\x00"):
        new2 = b"AVATARS\x00\x00\x00\x00\x00avatar.png\x00"
        so[str_offset2 : str_offset2 + 23] = new2
        print("[+] Replaced 'PLAY ONLINE' -> 'AVATARS' (with avatar.png icon)")

    # 2. Function Redirections:
    # onQuick (0x6E4EA0) -> Jump to onSettings (0x6E6394)
    so[0x6E4EA0 : 0x6E4EA0 + 4] = bytes([0x3D, 0x05, 0x00, 0x14])
    print("[+] Rerouted Button 1 (formerly onQuick) -> onSettings")

    # onMultiplayer (0x6E5284) -> Jump to onAvatars (0x6E5A0C)
    so[0x6E5284 : 0x6E5284 + 4] = bytes([0xE2, 0x01, 0x00, 0x14])
    print("[+] Rerouted Button 2 (formerly onMultiplayer) -> onAvatars")

    # 3. ComplianceGuardian (Disable terms/privacy prompt in C++)
    so[0xBEAD48 : 0xBEAD48 + 8] = bytes([0x00, 0x00, 0x80, 0x52, 0xC0, 0x03, 0x5F, 0xD6])
    so[0xBEAD80 : 0xBEAD80 + 4] = bytes([0xC0, 0x03, 0x5F, 0xD6])
    print("[+] Disabled in-game ComplianceGuardian terms popup.")

    # 4. AdBannerNode & C++ Ad API Disabling (Banner, Interstitial, Rewarded)
    so[0x0055AEDC : 0x0055AEDC + 4] = bytes([0xC0, 0x03, 0x5F, 0xD6]) # AdBannerNode::initNode -> ret
    so[0x0055BEE0 : 0x0055BEE0 + 4] = bytes([0xC0, 0x03, 0x5F, 0xD6]) # AdBannerNode::attachToScene -> ret
    so[0x0055C1B0 : 0x0055C1B0 + 4] = bytes([0xC0, 0x03, 0x5F, 0xD6]) # AdBannerNode::show -> ret
    so[0x009A5330 : 0x009A5334] = bytes([0xC0, 0x03, 0x5F, 0xD6])     # ApplicationInterface::showAdBanner -> ret
    so[0x00989528 : 0x0098952C] = bytes([0xC0, 0x03, 0x5F, 0xD6])     # ApplicationInterface::showWrappedAdBanner -> ret
    so[0x009896D8 : 0x009896DC] = bytes([0xC0, 0x03, 0x5F, 0xD6])     # ApplicationInterface::scheduledCreateAddBanner -> ret
    so[0x009A54C8 : 0x009A54CC] = bytes([0xC0, 0x03, 0x5F, 0xD6])     # ApplicationInterface::showInterstitial -> ret
    so[0x009A5440 : 0x009A5444] = bytes([0xC0, 0x03, 0x5F, 0xD6])     # ApplicationInterface::prepareInterstitial -> ret
    so[0x009A6DCC : 0x009A6DD0] = bytes([0xC0, 0x03, 0x5F, 0xD6])     # ApplicationInterface::showRewardedAd -> ret
    so[0x009A6C38 : 0x009A6C3C] = bytes([0xC0, 0x03, 0x5F, 0xD6])     # ApplicationInterface::prepareRewardedAd -> ret
    print("[+] Disabled all C++ ad banner, interstitial, and rewarded ad triggers.")

    # 5. Hide Login button/status, Armory, duplicate Avatars, Friends, Officers, Badges, Tokens & Coin
    # Build clean-up stub at 0x006E6BA0 (unused updateLoginStatus space)
    def gen_hide_block(offset, has_enabled=True):
        imm12 = offset // 8
        ldr_insn = 0xF9400000 | (imm12 << 10) | (0 << 5) | 1 # ldr x1, [x0, #offset]
        res = [ldr_insn]
        if has_enabled:
            cbz_insn = 0xB4000000 | (3 << 5) | 1 # cbz x1, #+12
            strb1 = 0x39000000 | (0x104 << 10) | (1 << 5) | 31 # strb wzr, [x1, #0x104]
            strb2 = 0x39000000 | (0x133 << 10) | (1 << 5) | 31 # strb wzr, [x1, #0x133]
            res += [cbz_insn, strb1, strb2]
        else:
            cbz_insn = 0xB4000000 | (2 << 5) | 1 # cbz x1, #+8
            strb1 = 0x39000000 | (0x104 << 10) | (1 << 5) | 31 # strb wzr, [x1, #0x104]
            res += [cbz_insn, strb1]
        return res

    blocks = []
    blocks += gen_hide_block(0x188, True)  # m_loginBtn
    blocks += gen_hide_block(0x1b8, True)  # m_armoryBtn
    blocks += gen_hide_block(0x190, True)  # left m_avatarsBtn
    blocks += gen_hide_block(0x1c8, True)  # m_friendsBtn
    blocks += gen_hide_block(0x1c0, True)  # m_officersBtn
    blocks += gen_hide_block(0x1e0, False) # m_friendsBadge
    blocks += gen_hide_block(0x1e8, False) # m_officersBadge
    blocks += gen_hide_block(0x220, False) # m_loginStatusLabel
    blocks += gen_hide_block(0x1f8, False) # m_coinIcon (TOKENS coin)
    blocks += gen_hide_block(0x200, False) # m_tokensLabel ("TOKENS: 0")

    jump_imm = len(blocks) + 1
    stub_insns = [0xB4000000 | (jump_imm << 5) | 0] + blocks + [0xD65F03C0] # ret
    stub_bytes = b"".join(struct.pack("<I", x) for x in stub_insns)
    so[0x006E6BA0 : 0x006E6BA0 + len(stub_bytes)] = stub_bytes
    print("[+] Patched updateLoginStatus to cleanly hide Login, Armory, Friends, Officers, Tokens & Coin.")

    # 6. Rank strings blanking (keep name, erase rank title, progress bar text & numeric XP)
    # "[%d] %s\0" -> "\0"
    so[0x01089CAC : 0x01089CAC + 8] = b"\x00" * 8
    # "RANK PROGRESS:\0" -> "\0"
    so[0x01089CB4 : 0x01089CB4 + 15] = b"\x00" * 15
    # Blank out numeric XP format "%d/%d" at 0x7af950 by pointing x0 to empty string at 0x1089CB4
    # 0x7af950: adrp x0, #0x1089000 (C0 46 00 D0)
    # 0x7af954: add x0, x0, #0xcb4  (00 D0 32 91)
    so[0x007AF950 : 0x007AF958] = bytes([0xC0, 0x46, 0x00, 0xD0, 0x00, 0xD0, 0x32, 0x91])
    # Blank out "TOKENS: " string at 0x01081401
    so[0x01081401 : 0x01081409] = b"\x00" * 8
    print("[+] Erased rank title, progress bar text, numeric XP, and tokens string.")

    # 7. Remove STATS and SCORES from MenuLayer
    so[0x006E38A0 : 0x006E38A4] = bytes([0x1F, 0x20, 0x03, 0xD5]) # nop (skip menu->addChild(statsBtn))
    so[0x006E3A44 : 0x006E3A48] = bytes([0x1F, 0x20, 0x03, 0xD5]) # nop (skip menu->addChild(scoresBtn))
    so[0x010879A9 : 0x010879AF] = b"\x00" * 6                     # "STATS\0" -> "\0"
    so[0x010879B9 : 0x010879C0] = b"\x00" * 7                     # "SCORES\0" -> "\0"
    print("[+] Removed STATS and SCORES buttons from MenuLayer.")

    # 8. Remove bottom-left green VersionLabel (*BETA* v0.14.4 (88))
    so[0x00C3B170 : 0x00C3B174] = bytes([0xC0, 0x03, 0x5F, 0xD6]) # CCDirector::updateVersionLabel -> ret
    so[0x010A918B : 0x010A9193] = b"\x00" * 8                     # " *BETA*\0" -> "\0"
    so[0x0108F23A : 0x0108F244] = b"\x00" * 10                    # " *BETA* v\0" -> "\0"
    print("[+] Removed bottom-left green version label.")

    # 9. Outpost map ONLY
    so[0x009D0150 : 0x009D0150 + 4] = bytes([0x9D, 0x07, 0x00, 0x14]) # b 0x9D1FC4
    print("[+] Restricted engine map registration to Outpost only.")

    # 10. Set menu background opacity to 100% (255) instead of 35 (0x23)
    so[0x6E4130 : 0x6E4134] = bytes([0xE2, 0x1F, 0x80, 0x52]) # mov w2, #0xff
    print("[+] Set menu background opacity to 100% (255).")

    # 11. Add title_ret2 background behind buttons with zOrder = -1
    # Originally called: this->addChild(sprite) [zOrder=0, which overlays buttons]
    # Now calls: this->addChild(sprite, -1) [zOrder=-1, safely behind all UI buttons and avatar]
    bg_zorder_patch = bytes([
        0x02, 0x00, 0x80, 0x12, # 0x6e4158: mov  w2, #-1 (zOrder = -1)
        0xe9, 0xe3, 0x42, 0xf9, # 0x6e415c: ldr  x9, [sp, #0x5c0]
        0x20, 0x01, 0x40, 0xf9, # 0x6e4160: ldr  x0, [x9]
        0x00, 0xcc, 0x40, 0xf9, # 0x6e4164: ldr  x0, [x0, #0x198] (CCNode::addChild(CCNode*, int))
        0x3e, 0xed, 0x40, 0xf9, # 0x6e4168: ldr  x30, [x9, #0x1d8]
        0xe0, 0x7f, 0x00, 0xf9, # 0x6e416c: str  x0, [sp, #0xf8]
        0xe0, 0x03, 0x09, 0xaa, # 0x6e4170: mov  x0, x9 (this)
        0xe1, 0x03, 0x1e, 0xaa, # 0x6e4174: mov  x1, x30 (sprite)
        0xe8, 0x7f, 0x40, 0xf9, # 0x6e4178: ldr  x8, [sp, #0xf8]
        0x00, 0x01, 0x3f, 0xd6  # 0x6e417c: blr  x8
    ])
    so[0x6E4158 : 0x6E4158 + len(bg_zorder_patch)] = bg_zorder_patch
    print("[+] Patched title_ret2 background to render at zOrder=-1 (behind all menu buttons).")

    # 12. Remove the duplicate top-right standalone gear SETTINGS button
    # In MenuLayer::init at 0x6e3c0c: blr x10 calls this->addChild(settingsBtn)
    # NOPing out this call prevents the top-right button from ever being added to the scene,
    # leaving ONLY the side menu 'SETTINGS' button with text.
    so[0x6E3C0C : 0x6E3C10] = bytes([0x1F, 0x20, 0x03, 0xD5]) # nop
    print("[+] Removed duplicate top-right standalone gear SETTINGS button.")

    return {"lib/arm64-v8a/libcocos2dcpp.so": bytes(so)}

def repack_atlas(z, atlas_name, plist_path, png_path, individual_dir):
    """Repack sprite sheet from individual sprites"""
    print(f"[*] Repacking {atlas_name} from {os.path.basename(individual_dir)}...")
    img = Image.open(io.BytesIO(z.read(png_path))).convert("RGBA")
    plist_data = plistlib.loads(z.read(plist_path))
    frames = plist_data.get("frames", {})

    flat_dir = os.path.join(individual_dir, "all")
    replaced = 0

    for name, frame in frames.items():
        src_path = None
        if os.path.exists(flat_dir):
            candidate = os.path.join(flat_dir, name)
            if os.path.isfile(candidate):
                src_path = candidate

        if not src_path:
            for sub in os.listdir(individual_dir):
                sub_dir = os.path.join(individual_dir, sub)
                if os.path.isdir(sub_dir):
                    candidate = os.path.join(sub_dir, name)
                    if os.path.isfile(candidate):
                        src_path = candidate
                        break

        if src_path and os.path.exists(src_path):
            sprite_img = Image.open(src_path).convert("RGBA")
            rect_str = frame["textureRect"]
            nums = [int(n) for n in re.findall(r"\d+", rect_str)]
            x, y, w, h = nums
            if sprite_img.size != (w, h):
                sprite_img = sprite_img.resize((w, h), Image.Resampling.LANCZOS)

            img.paste((0, 0, 0, 0), (x, y, x + w, y + h))
            img.paste(sprite_img, (x, y), sprite_img)
            replaced += 1

    print(f"    Replaced {replaced} sprites in {atlas_name}.")

    results = {}
    buf_hdr = io.BytesIO()
    img.save(buf_hdr, format="PNG")
    results[png_path] = buf_hdr.getvalue()

    hd_path = png_path.replace("/hdr/", "/hd/")
    hd_img = img.resize((img.width // 2, img.height // 2), Image.Resampling.LANCZOS)
    buf_hd = io.BytesIO()
    hd_img.save(buf_hd, format="PNG")
    results[hd_path] = buf_hd.getvalue()

    sd_path = png_path.replace("/hdr/", "/sd/")
    sd_img = img.resize((img.width // 4, img.height // 4), Image.Resampling.LANCZOS)
    buf_sd = io.BytesIO()
    sd_img.save(buf_sd, format="PNG")
    results[sd_path] = buf_sd.getvalue()

    return results

def repack_map_tiles(z, tile_name, png_path, individual_dir):
    """Repack map tile atlas"""
    print(f"[*] Repacking {tile_name} from {os.path.basename(individual_dir)}...")
    img = Image.open(io.BytesIO(z.read(png_path))).convert("RGBA")
    replaced = 0

    if os.path.exists(individual_dir):
        for f in os.listdir(individual_dir):
            if f.endswith(".png"):
                m = re.search(r"tile_(\d+)_r(\d+)_c(\d+)", f)
                if m:
                    _, row, col = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    x = 8 + col * 264
                    y = 8 + row * 264
                    tile_img = Image.open(os.path.join(individual_dir, f)).convert("RGBA")
                    if tile_img.size != (256, 256):
                        tile_img = tile_img.resize((256, 256), Image.Resampling.LANCZOS)
                    img.paste((0, 0, 0, 0), (x, y, x + 256, y + 256))
                    img.paste(tile_img, (x, y), tile_img)
                    replaced += 1

    print(f"    Replaced {replaced} tiles in {tile_name}.")
    results = {}
    buf_hdr = io.BytesIO()
    img.save(buf_hdr, format="PNG")
    results[png_path] = buf_hdr.getvalue()

    hd_path = png_path.replace("/hdr/", "/hd/")
    hd_img = img.resize((img.width // 2, img.height // 2), Image.Resampling.LANCZOS)
    buf_hd = io.BytesIO()
    hd_img.save(buf_hd, format="PNG")
    results[hd_path] = buf_hd.getvalue()

    sd_path = png_path.replace("/hdr/", "/sd/")
    sd_img = img.resize((img.width // 4, img.height // 4), Image.Resampling.LANCZOS)
    buf_sd = io.BytesIO()
    sd_img.save(buf_sd, format="PNG")
    results[sd_path] = buf_sd.getvalue()

    return results

def build_apk():
    """Builds MiniMilitia_Modded.apk with all modifications"""
    if not os.path.exists(SRC_APK):
        print(f"[-] Source APK not found: {SRC_APK}")
        return False

    temp_apk = os.path.join(APP_DIR, "temp_unsigned.apk")
    print(f"\n[1/4] Reading source APK: {os.path.basename(SRC_APK)}")

    with zipfile.ZipFile(SRC_APK, "r") as zin:
        files_to_update = {}

        # 1. Launcher icons
        icon_files = generate_icons()
        files_to_update.update(icon_files)

        # 1b. Custom Home Page & Splash Background
        bg_files = generate_background_images()
        files_to_update.update(bg_files)

        # 2. Terms & Conditions popup removal JSONs
        terms_files = patch_terms_and_conditions_json()
        files_to_update.update(terms_files)

        # 3. Patch libcocos2dcpp.so for menu buttons and popup bypass
        so_files = patch_libcocos2dcpp(zin)
        files_to_update.update(so_files)

        # 4. Character & Weapon Sprite Sheet (partsTexture)
        parts = repack_atlas(
            zin, "partsTexture",
            "assets/hdr/partsTexture.plist", "assets/hdr/partsTexture.png",
            os.path.join(SEPARATED_DIR, "characters_and_avatars")
        )
        files_to_update.update(parts)

        # 5. UI and Menus Sprite Sheet (menuTexture)
        menu = repack_atlas(
            zin, "menuTexture",
            "assets/hdr/menuTexture.plist", "assets/hdr/menuTexture.png",
            os.path.join(SEPARATED_DIR, "ui_and_menus")
        )
        files_to_update.update(menu)

        # 6. Map Tile Sheets (Outpost uses default tile64_new)
        tiles = repack_map_tiles(zin, "tile64_new", "assets/hdr/tile64_new.png", os.path.join(SEPARATED_DIR, "map_tiles_default"))
        files_to_update.update(tiles)

        # Blank 1x1 image for unused map tiles and backgrounds
        blank_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        buf_blank = io.BytesIO()
        blank_img.save(buf_blank, format="PNG")
        blank_bytes = buf_blank.getvalue()

        for unused_tile in [
            "assets/hdr/tile64Desert_new.png", "assets/hd/tile64Desert_new.png", "assets/sd/tile64Desert_new.png",
            "assets/hdr/tile64Moon_new.png", "assets/hd/tile64Moon_new.png", "assets/sd/tile64Moon_new.png",
            "assets/hdr/tile64Snow_new.png", "assets/hd/tile64Snow_new.png", "assets/sd/tile64Snow_new.png",
            "assets/hdr/bgDesert_new.png", "assets/hd/bgDesert_new.png", "assets/sd/bgDesert_new.png",
            "assets/hdr/bgMoon_new.png", "assets/hd/bgMoon_new.png", "assets/sd/bgMoon_new.png",
            "assets/hdr/bgSnow_new.png", "assets/hd/bgSnow_new.png", "assets/sd/bgSnow_new.png",
        ]:
            files_to_update[unused_tile] = blank_bytes

        # Write to temp APK
        print(f"\n[2/4] Packaging {len(files_to_update)} updated assets into APK...")
        with zipfile.ZipFile(temp_apk, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename.startswith("META-INF/"):
                    continue
                # Exclude all non-Outpost .tmx map files
                if item.filename.endswith(".tmx") and not item.filename.endswith("1outpost_new.tmx"):
                    continue
                if item.filename in files_to_update:
                    zout.writestr(item.filename, files_to_update[item.filename])
                else:
                    zout.writestr(item, zin.read(item.filename))

            for fname, content in files_to_update.items():
                if fname not in zin.namelist():
                    zout.writestr(fname, content)

    # 7. Sign the APK with uber-apk-signer
    print(f"\n[3/4] Signing APK with uber-apk-signer...")
    if os.path.exists(TARGET_APK):
        try: os.remove(TARGET_APK)
        except: pass

    cmd_sign = [
        "java", "-Xmx128m", "-Xms32m", "-jar", UBER_SIGNER,
        "-a", temp_apk,
        "-o", ROOT_DIR,       # signed APK goes to mmcg\ root
        "--allowResign"
    ]
    res = subprocess.run(cmd_sign, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[-] Signer failed: {res.stderr}")
        return False

    signed_candidate = os.path.join(ROOT_DIR, "temp_unsigned-aligned-debugSigned.apk")
    if os.path.exists(signed_candidate):
        if os.path.exists(TARGET_APK):
            os.remove(TARGET_APK)
        os.rename(signed_candidate, TARGET_APK)
        print(f"[+] Output ready: {TARGET_APK} ({os.path.getsize(TARGET_APK)/(1024*1024):.2f} MB)")
    else:
        print(f"[-] Could not locate signed APK output")
        return False

    if os.path.exists(temp_apk):
        try: os.remove(temp_apk)
        except: pass

    return True

def install_and_launch_phone():
    """Installs MiniMilitia_Modded.apk to the connected phone and launches it"""
    print(f"\n[4/4] Checking connected phone via ADB...")

    # Verify adb is actually reachable before attempting anything
    import shutil
    adb_resolved = ADB_EXE if (ADB_EXE != "adb" or shutil.which("adb")) else None
    if not adb_resolved or not os.path.isfile(adb_resolved) and shutil.which(adb_resolved) is None:
        print("[-] ADB not found. Skipping phone install step.")
        print(f"    APK is ready at: {TARGET_APK}")
        print("    Transfer it manually to your device, or install Android SDK platform-tools.")
        return False

    res_devices = subprocess.run([ADB_EXE, "devices"], capture_output=True, text=True)
    lines = [l.strip() for l in res_devices.stdout.strip().split("\n")[1:] if l.strip()]

    device_id = None
    for l in lines:
        parts = l.split()
        if len(parts) >= 2 and parts[1] == "device":
            device_id = parts[0]
            break

    if not device_id:
        print("[-] No authorized device connected via ADB.")
        return False

    print(f"[+] Found connected device: {device_id}")
    print(f"[*] Installing {os.path.basename(TARGET_APK)} to {device_id}...")
    res_install = subprocess.run([ADB_EXE, "-s", device_id, "install", "-r", "-g", TARGET_APK], capture_output=True, text=True)
    print(res_install.stdout)
    if "Success" not in res_install.stdout:
        print(f"[-] Installation failed: {res_install.stderr}")
        return False

    print(f"[+] Installation successful! Ensuring user profile 0 has package installed...")
    subprocess.run([ADB_EXE, "-s", device_id, "shell", "cmd", "package", "install-existing", "--user", "0", "com.appsomniacs.mmc"], capture_output=True)
    print(f"[*] Launching Mini Militia on phone...")
    import time
    subprocess.run([ADB_EXE, "-s", device_id, "shell", "input", "keyevent", "224"])
    subprocess.run([ADB_EXE, "-s", device_id, "shell", "input", "keyevent", "82"])
    subprocess.run([ADB_EXE, "-s", device_id, "shell", "input", "swipe", "500", "1500", "500", "500"])
    time.sleep(0.5)
    subprocess.run([ADB_EXE, "-s", device_id, "shell", "am", "start", "-n", "com.appsomniacs.mmc/com.appsomniacs.mmc.MmcActivity"])
    print("[*] Waiting for splash screen, then tapping 'Touch to start'...")
    time.sleep(5)
    subprocess.run([ADB_EXE, "-s", device_id, "shell", "input", "tap", "1200", "540"])
    print("[+] Game launched and entered main menu on phone screen!")
    return True

if __name__ == "__main__":
    success = build_apk()
    if success:
        install_and_launch_phone()
