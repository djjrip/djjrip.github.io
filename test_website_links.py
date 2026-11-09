"""
Test suite for djjrip.github.io static site.
Verifies internal links, JSON manifests, profile media hygiene,
Stripe Checkout pricing parity, and DJ portal phone privacy.
"""
import hashlib
import json
import os
import re
import struct
import sys

SITE_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

DJ_FUNNEL_FILES = (
    "dj.html",
    "dj-events.html",
    "dj-cancel.html",
    "booking.html",
    "dj-terms.html",
    "dj-confirmed.html",
    "vibe.html",
)

STRIPE_ONLY_CHECK_FILES = DJ_FUNNEL_FILES + (
    "hire-now.html",
    "index.html",
    "gaming-for-groceries/index.html",
)

EXPECTED_STRIPE_LINKS = (
    "https://buy.stripe.com/14A5kFfE8feF52H48U0Fi0o",
    "https://buy.stripe.com/cNi4gB2Rm7Md7aP0WI0Fi0c",
    "https://buy.stripe.com/9B6fZjgIcc2t1QvcFq0Fi0d",
    "https://buy.stripe.com/00w6oJdw02rTcv9bBm0Fi0e",
    "https://buy.stripe.com/aFa3cxgIceaBbr520M0Fi0f",
)

# SHA-256 of 10-digit private booking phone (kept hashed in public test suite)
PRIVATE_PHONE_SHA256 = "7066ef0d6158b8af8213a2f02485fc52a1810697bd74afad6419f1f8f3aa9ca2"

DEPRECATED_TERMS = (
    "due at show",
    "335.7k",
    "don toliver",
    "bookDateMirror",
    "preset-pill",
    "smsFallbackLink",
    "topBookBtn",
    "brandBtn",
    "tt-rhythm-dtx",
    "dj-jrip-headshot",
    "serif-accent",
    "ach invoice",
    "ach bank invoice",
    "mercury bank",
    "mercury business invoice",
    "bank transfer",
    "data-pay=\"ach\"",
    "zelle",
    "venmo",
)


def check_html_links():
    html_files = []
    for root, _, files in os.walk(SITE_DIR):
        if f"{os.sep}.git" in root or root.endswith(f"{os.sep}.git"):
            continue
        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root, f))

    print(f"Auditing {len(html_files)} HTML files in {SITE_DIR}...")
    errors = []
    checked_count = 0

    link_pattern = re.compile(r'(?:href|src)=["\']([^"\']+)["\']', re.IGNORECASE)

    for html_file in html_files:
        rel_html = os.path.relpath(html_file, SITE_DIR)
        with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        matches = link_pattern.findall(content)
        for target in matches:
            target = target.strip()
            if (target.startswith("http://") or target.startswith("https://") or
                target.startswith("#") or target.startswith("mailto:") or
                target.startswith("tel:") or target.startswith("sms:") or
                target.startswith("javascript:") or target.startswith("data:")):
                continue

            clean_target = target.split("#")[0].split("?")[0]
            if not clean_target:
                continue

            html_dir = os.path.dirname(html_file)
            resolved_path = os.path.normpath(os.path.join(html_dir, clean_target))

            checked_count += 1
            if not os.path.exists(resolved_path):
                errors.append(f"Broken link in {rel_html} -> '{target}' (resolved to {resolved_path})")

    print(f"Total internal links checked: {checked_count}")
    return errors


def check_json_manifests():
    errors = []
    catalog_path = os.path.join(SITE_DIR, "dj-catalog.json")
    layout_path = os.path.join(SITE_DIR, "dj-layout.json")

    if not os.path.exists(catalog_path):
        errors.append("Missing dj-catalog.json")
    else:
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                cat = json.load(f)
            if not isinstance(cat.get("vibes"), dict) or len(cat["vibes"]) < 4:
                errors.append("dj-catalog.json missing expected 'vibes' map")
            if not isinstance(cat.get("tracks"), list) or len(cat["tracks"]) < 1000:
                errors.append("dj-catalog.json 'tracks' list unexpectedly small or missing")
        except Exception as exc:
            errors.append(f"Invalid dj-catalog.json: {exc}")

    if not os.path.exists(layout_path):
        errors.append("Missing dj-layout.json")
    else:
        try:
            with open(layout_path, "r", encoding="utf-8") as f:
                lay = json.load(f)
            if not isinstance(lay.get("sectionOrder"), list) or "hero" not in lay["sectionOrder"]:
                errors.append("dj-layout.json missing valid 'sectionOrder'")
            if not isinstance(lay.get("profile"), dict):
                errors.append("dj-layout.json missing 'profile' object")
        except Exception as exc:
            errors.append(f"Invalid dj-layout.json: {exc}")

    return errors


def _jpeg_has_exif_marker(jpeg_bytes):
    # Check JPEG APP1 (0xFFE1) Exif header without requiring third-party libs
    if not jpeg_bytes.startswith(b"\xff\xd8"):
        return True
    idx = 2
    n = len(jpeg_bytes)
    while idx + 4 <= n:
        if jpeg_bytes[idx] != 0xFF:
            break
        marker = jpeg_bytes[idx + 1]
        if marker == 0xDA or marker == 0xD9:  # SOS or EOI
            break
        seg_len = struct.unpack(">H", jpeg_bytes[idx + 2:idx + 4])[0]
        if marker == 0xE1:
            payload = jpeg_bytes[idx + 4:idx + 2 + seg_len]
            if payload.startswith(b"Exif\x00\x00"):
                return True
        idx += 2 + seg_len
    return False


def check_profile_portrait():
    errors = []
    portrait_path = os.path.join(SITE_DIR, "assets", "dj-jrip-profile.jpg")
    if not os.path.exists(portrait_path):
        return ["Missing required portrait asset: assets/dj-jrip-profile.jpg"]
    try:
        from PIL import Image
        with Image.open(portrait_path) as im:
            w, h = im.size
            if w < 400 or h < 400:
                errors.append(f"Portrait resolution too small: {w}x{h} (expected >= 400x400)")
    except ImportError:
        pass

    # Verify all published JPEGs are >= 10KB and 100% EXIF-clean (GPS/timestamp privacy)
    assets_dir = os.path.join(SITE_DIR, "assets")
    jpgs = [f for f in sorted(os.listdir(assets_dir)) if f.lower().endswith(".jpg")]
    for fname in jpgs:
        fpath = os.path.join(assets_dir, fname)
        size = os.path.getsize(fpath)
        if size < 10_000:
            errors.append(f"JPEG assets/{fname} unexpectedly small ({size} bytes)")
        with open(fpath, "rb") as f:
            raw = f.read()
        if _jpeg_has_exif_marker(raw):
            errors.append(f"JPEG assets/{fname} contains EXIF metadata (strip EXIF before publishing)")
        try:
            from PIL import Image
            with Image.open(fpath) as im:
                if len(im.getexif()) > 0:
                    errors.append(f"JPEG assets/{fname} has non-empty PIL EXIF tags")
        except ImportError:
            pass

    # Verify all DJ live performance MP4 assets exist, play-ready size, and within GitHub file bounds
    expected_videos = (
        "dj-jrip-homegrown-live.mp4",
        "dj-jrip-crowd-floor-2024.mp4",
        "dj-jrip-love-flip-reel.mp4",
        "dj-jrip-reel.mp4",
        "tiktok-clip.mp4",
    )
    for vname in expected_videos:
        vpath = os.path.join(assets_dir, vname)
        if not os.path.exists(vpath):
            errors.append(f"Missing live video asset: assets/{vname}")
            continue
        vsize = os.path.getsize(vpath)
        if vsize < 100_000:
            errors.append(f"Video assets/{vname} unexpectedly small ({vsize} bytes)")
        if vsize > 50 * 1024 * 1024:
            errors.append(f"Video assets/{vname} exceeds 50MB repo safety budget ({vsize / (1024*1024):.1f} MB)")

    return errors


def check_dj_funnel_consistency_and_privacy():
    errors = []
    phone_cand_re = re.compile(r'(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b')

    for fname in STRIPE_ONLY_CHECK_FILES:
        fpath = os.path.join(SITE_DIR, fname)
        if not os.path.exists(fpath):
            errors.append(f"Missing expected site file: {fname}")
            continue
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()

        # Check phone privacy only on gated DJ funnel pages (never expose raw digits in public DJ HTML)
        if fname in DJ_FUNNEL_FILES:
            for match in phone_cand_re.findall(txt):
                digits = re.sub(r"\D", "", match)
                if len(digits) == 11 and digits.startswith("1"):
                    digits = digits[1:]
                if len(digits) == 10 and hashlib.sha256(digits.encode("utf-8")).hexdigest() == PRIVATE_PHONE_SHA256:
                    errors.append(f"Phone privacy breach in {fname}: raw booking number exposed ({match})")

        # Check deprecated/removed UI copy or off-Stripe payment tokens
        for term in DEPRECATED_TERMS:
            if re.search(re.escape(term), txt, re.IGNORECASE):
                errors.append(f"Deprecated token '{term}' found in {fname}")

    dj_path = os.path.join(SITE_DIR, "dj.html")
    if os.path.exists(dj_path):
        with open(dj_path, "r", encoding="utf-8", errors="ignore") as f:
            dj_txt = f.read()
        for url in EXPECTED_STRIPE_LINKS:
            if url not in dj_txt:
                errors.append(f"Missing live Stripe payment link in dj.html: {url}")
        if "assets/dj-jrip-profile.jpg" not in dj_txt:
            errors.append("dj.html hero does not reference assets/dj-jrip-profile.jpg")
        if "headshot" in dj_txt.lower():
            errors.append("Deprecated placeholder image reference 'headshot' found in dj.html")
        if 'id="lockStepSection"' not in dj_txt:
            errors.append("dj.html missing Step 3 card container #lockStepSection")
        if 'id="directLineBox"' not in dj_txt:
            errors.append("dj.html missing #directLineBox gate")

    for dead_asset in (
        "dj-jrip-headshot.jpg",
        "tt-rhythm-dtx.jpg",
        "mix-serato-session-1.mp3",
        "mix-don-3track-blend.mp3",
        "mix-serato-session-4.mp3",
        "mix-frank-ocean-lost-afro.mp3",
        "mix-modern-jam-sexyback.mp3",
    ):
        if os.path.exists(os.path.join(SITE_DIR, "assets", dead_asset)):
            errors.append(f"Redundant/dead asset still present on disk: assets/{dead_asset}")

    for req_photo in (
        "dj-jrip-trunk-or-treat-2019.jpg",
        "dj-jrip-trunk-or-treat-night-2019.jpg",
        "dj-jrip-fort-worth-booth-2024.jpg",
    ):
        if not os.path.exists(os.path.join(SITE_DIR, "assets", req_photo)):
            errors.append(f"Missing live proof photo: assets/{req_photo}")

    # Verify GALLERY_ITEMS length matches lightbox trigger indices and block layout parity
    if os.path.exists(dj_path):
        m_gal = re.search(r"const\s+GALLERY_ITEMS\s*=\s*\[(.*?)\];", dj_txt, re.S)
        if not m_gal:
            errors.append("Could not locate GALLERY_ITEMS array in dj.html")
        else:
            gal_srcs = re.findall(r"src:\s*['\"]([^'\"]+)['\"]", m_gal.group(1))
            if len(gal_srcs) != 7:
                errors.append(f"Expected 7 GALLERY_ITEMS in dj.html, found {len(gal_srcs)}")
            for gsrc in gal_srcs:
                if not os.path.exists(os.path.normpath(os.path.join(SITE_DIR, gsrc))):
                    errors.append(f"Missing GALLERY_ITEMS file: {gsrc}")
            lb_indices = {int(x) for x in re.findall(r'data-lightbox-open="(\d+)"', dj_txt)}
            expected_indices = set(range(len(gal_srcs)))
            if lb_indices != expected_indices:
                errors.append(f"Gallery trigger index mismatch: {sorted(lb_indices)} vs {sorted(expected_indices)}")
        if "media-frame vertical" not in dj_txt:
            errors.append("dj.html missing .media-frame.vertical aspect-ratio container for portrait reels")
        for req_vid in (
            "assets/dj-jrip-homegrown-live.mp4",
            "assets/dj-jrip-crowd-floor-2024.mp4",
            "assets/dj-jrip-love-flip-reel.mp4",
        ):
            if req_vid not in dj_txt:
                errors.append(f"dj.html missing organizer video integration: {req_vid}")

    return errors


def check_vinyl_platter_tracks():
    errors = []
    dj_path = os.path.join(SITE_DIR, "dj.html")
    with open(dj_path, "r", encoding="utf-8", errors="ignore") as f:
        dj_txt = f.read()

    m_arr = re.search(r"const\s+DECK_TRACKS\s*=\s*\[(.*?)\];", dj_txt, re.S)
    if not m_arr:
        return ["Could not locate DECK_TRACKS array in dj.html"]

    srcs = re.findall(r"src:\s*['\"]([^'\"]+)['\"]", m_arr.group(1))
    if len(srcs) < 7:
        errors.append(f"Expected >= 7 organic tracks in DECK_TRACKS, found {len(srcs)}")
    if len(set(srcs)) != len(srcs):
        errors.append(f"Duplicate track src in DECK_TRACKS: {srcs}")

    chip_idxs = re.findall(r'class="deck-chip[^"]*"\s+data-track-idx="(\d+)"', dj_txt)
    if len(chip_idxs) != len(srcs):
        errors.append(f"Mismatch between #deckChipRow buttons ({len(chip_idxs)}) and DECK_TRACKS ({len(srcs)})")

    seen_hashes = {}
    for rel_src in srcs:
        full = os.path.normpath(os.path.join(SITE_DIR, rel_src))
        if not os.path.exists(full):
            errors.append(f"Missing DECK_TRACKS audio asset on disk: {rel_src}")
            continue
        if os.path.getsize(full) < 200_000:
            errors.append(f"Audio asset unexpectedly tiny (<200KB, likely preview stub): {rel_src}")
        digest = hashlib.sha256(open(full, "rb").read()).hexdigest()
        if digest in seen_hashes:
            errors.append(f"Duplicate audio bytes in DECK_TRACKS: {rel_src} matches {seen_hashes[digest]}")
        seen_hashes[digest] = rel_src

    return errors


def main():
    errors = []
    errors.extend(check_html_links())
    errors.extend(check_json_manifests())
    errors.extend(check_profile_portrait())
    errors.extend(check_dj_funnel_consistency_and_privacy())
    errors.extend(check_vinyl_platter_tracks())

    if errors:
        print(f"FAILED: Found {len(errors)} issue(s):")
        for err in errors:
            print(f"  - {err}")
        return False

    print("ALL STATIC SITE LINKS, MANIFESTS, MEDIA, VINYL DECK & DJ PRIVACY CHECKS PASSED!")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
