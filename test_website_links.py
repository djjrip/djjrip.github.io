"""
Test suite for djjrip.github.io static site.
Verifies all internal href and src attributes point to existing files on disk.
"""
import os
import re
import sys

SITE_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

def check_html_links():
    html_files = []
    for root, dirs, files in os.walk(SITE_DIR):
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
            # Ignore absolute URLs, hashes, javascript, mailto, tel, sms
            if (target.startswith("http://") or target.startswith("https://") or 
                target.startswith("#") or target.startswith("mailto:") or 
                target.startswith("tel:") or target.startswith("sms:") or 
                target.startswith("javascript:") or target.startswith("data:")):
                continue
            
            # Strip anchor query parameters or hashes
            clean_target = target.split("#")[0].split("?")[0]
            if not clean_target:
                continue # was just a hash
            
            # Resolve relative to html file
            html_dir = os.path.dirname(html_file)
            resolved_path = os.path.normpath(os.path.join(html_dir, clean_target))
            
            checked_count += 1
            if not os.path.exists(resolved_path):
                errors.append(f"Broken link in {rel_html} -> '{target}' (resolved to {resolved_path})")

    print(f"Total internal links checked: {checked_count}")
    if errors:
        print(f"FAILED: Found {len(errors)} broken links:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("ALL INTERNAL LINKS VALID! (0 broken links)")
        return True

if __name__ == "__main__":
    success = check_html_links()
    if not success:
        sys.exit(1)
    sys.exit(0)
