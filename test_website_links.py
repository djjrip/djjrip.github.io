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
    "booking.html",
    "dj-terms.html",
    "dj-confirmed.html",
    "vibe.html",
)

EXPECTED_STRIPE_LINKS = (
    "https://buy.stripe.com/cNi4gB2Rm7Md7aP0WI0Fi0c",
    "https://buy.stripe.com/9B6fZjgIcc2t1QvcFq0Fi0d",
    "https://buy.stripe.com/00w6oJdw02rTcv9bBm0Fi0e",
    "https://buy.stripe.com/aFa3cxgIceaBbr520M0Fi0f",
)

# SHA-256 of 10-digit private booking phone (kept hashed in public test suite)
PRIVATE_PHONE_SHA256 = "7066ef0d6158b8af8213a2f02485fc52a1810697bd74afad6419f1f8f3aa9ca2"

DEPRECATED_TERMS = (
    "due at show",
    "bookDateMirror",
    "preset-pill",
    "smsFallbackLink",
    "topBookBtn",
    "brandBtn",
    "tt-rhythm-dtx",
    "dj-jrip-headshot",
    "serif-accent",
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
    size = os.path.getsize(portrait_path)
    if size < 10_000:
        errors.append(f"Portrait assets/dj-jrip-profile.jpg unexpectedly small ({size} bytes)")
    with open(portrait_path, "rb") as f:
        raw = f.read()
    if _jpeg_has_exif_marker(raw):
        errors.append("Portrait assets/dj-jrip-profile.jpg contains EXIF metadata (strip EXIF before publishing)")
    try:
        from PIL import Image
        with Image.open(portrait_path) as im:
            if len(im.getexif()) > 0:
                errors.append("Portrait assets/dj-jrip-profile.jpg has non-empty PIL EXIF tags")
            w, h = im.size
            if w < 400 or h < 400:
                errors.append(f"Portrait resolution too small: {w}x{h} (expected >= 400x400)")
    except ImportError:
        pass
    return errors


def check_dj_funnel_consistency_and_privacy():
    errors = []
    phone_cand_re = re.compile(r'(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b')

    for fname in DJ_FUNNEL_FILES:
        fpath = os.path.join(SITE_DIR, fname)
        if not os.path.exists(fpath):
            errors.append(f"Missing expected DJ funnel file: {fname}")
            continue
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()

        # Check phone privacy: never expose raw digits in public DJ HTML
        for match in phone_cand_re.findall(txt):
            digits = re.sub(r"\D", "", match)
            if len(digits) == 11 and digits.startswith("1"):
                digits = digits[1:]
            if len(digits) == 10 and hashlib.sha256(digits.encode("utf-8")).hexdigest() == PRIVATE_PHONE_SHA256:
                errors.append(f"Phone privacy breach in {fname}: raw booking number exposed ({match})")

        # Check deprecated/removed UI copy or elements
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

    for dead_asset in ("dj-jrip-headshot.jpg", "tt-rhythm-dtx.jpg"):
        if os.path.exists(os.path.join(SITE_DIR, "assets", dead_asset)):
            errors.append(f"Redundant/dead asset still present on disk: assets/{dead_asset}")

    return errors


def main():
    errors = []
    errors.extend(check_html_links())
    errors.extend(check_json_manifests())
    errors.extend(check_profile_portrait())
    errors.extend(check_dj_funnel_consistency_and_privacy())

    if errors:
        print(f"FAILED: Found {len(errors)} issue(s):")
        for err in errors:
            print(f"  - {err}")
        return False

    print("ALL STATIC SITE LINKS, MANIFESTS, MEDIA & DJ PRIVACY CHECKS PASSED!")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
