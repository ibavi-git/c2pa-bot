#!/usr/bin/env python3
"""
c2pa_tool.py — Detect and remove C2PA Content Credentials from images.

Install deps:
    pip install c2pa-python Pillow

Usage:
    python c2pa_tool.py detect  image.jpg
    python c2pa_tool.py strip   image.jpg  out.jpg            # surgical (JPEG: keeps EXIF)
    python c2pa_tool.py strip   image.jpg  out.jpg --resave   # brute force (drops ALL metadata)

Note: C2PA is a voluntary transparency signal. Some jurisdictions (e.g. the EU AI
Act) place disclosure obligations on AI-generated media; removing the marker to
pass synthetic content off as human-made may run against those rules or a
platform's terms. Use on your own files and for legitimate reasons.
"""

import sys
import struct
import mimetypes

try:
    from c2pa import Reader
except ImportError:
    Reader = None


# ---------- DETECTION ----------

def detect(path):
    """Return a dict of C2PA info, or None if the file carries no manifest."""
    if Reader is None:
        raise RuntimeError("c2pa-python not installed: pip install c2pa-python")
    import json
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        reader = Reader.try_create(mime, f)   # returns None when no manifest
        if reader is None:
            return None
        store = json.loads(reader.json())
    active = store.get("active_manifest")
    m = store.get("manifests", {}).get(active, {})
    return {
        "claim_generator": m.get("claim_generator"),
        "title": m.get("title"),
        "is_embedded": reader.is_embedded(),
        "num_manifests": len(store.get("manifests", {})),
    }


# ---------- REMOVAL: surgical (JPEG only, preserves EXIF etc.) ----------

def strip_c2pa_jpeg(in_path, out_path):
    """Drop only APP11 segments that carry C2PA/JUMBF data. Keeps other metadata.
    Returns the number of segments removed."""
    with open(in_path, "rb") as f:
        data = f.read()
    if data[:2] != b"\xff\xd8":
        raise ValueError("Not a JPEG — use --resave for other formats")

    out = bytearray(b"\xff\xd8")
    i, n, removed = 2, len(data), 0
    while i < n:
        if data[i] != 0xFF:
            out.extend(data[i:]); break
        marker = data[i + 1]
        if marker == 0xDA:                       # start of scan: copy rest verbatim
            out.extend(data[i:]); break
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:   # standalone markers
            out.extend(data[i:i + 2]); i += 2; continue
        seg_len = struct.unpack(">H", data[i + 2:i + 4])[0]
        seg = data[i:i + 2 + seg_len]
        payload = data[i + 4:i + 2 + seg_len]
        if marker == 0xEB and (b"jumb" in payload[:60] or b"c2pa" in payload[:120]):
            removed += 1                          # this is the C2PA segment: skip it
        else:
            out.extend(seg)
        i += 2 + seg_len

    with open(out_path, "wb") as f:
        f.write(out)
    return removed


# ---------- REMOVAL: brute force (any format, drops ALL metadata) ----------

def strip_by_resave(in_path, out_path, quality=95):
    """Re-encode pixels into a fresh file. Removes C2PA and every other metadata."""
    from PIL import Image
    img = Image.open(in_path)
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))
    save_kwargs = {"quality": quality} if out_path.lower().endswith((".jpg", ".jpeg")) else {}
    clean.save(out_path, **save_kwargs)


# ---------- CLI ----------

def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("detect", "strip"):
        print(__doc__); sys.exit(1)

    if args[0] == "detect":
        info = detect(args[1])
        if info is None:
            print("No C2PA / Content Credentials found.")
        else:
            print("C2PA FOUND:")
            for k, v in info.items():
                print(f"  {k}: {v}")
        return

    # strip
    in_path, out_path = args[1], args[2]
    if "--resave" in args:
        strip_by_resave(in_path, out_path)
        print(f"Re-saved (all metadata dropped) -> {out_path}")
    else:
        removed = strip_c2pa_jpeg(in_path, out_path)
        print(f"Removed {removed} C2PA segment(s) -> {out_path}")

    # verify
    still = detect(out_path)
    print("Verification:", "C2PA still present!" if still else "clean, no C2PA.")


if __name__ == "__main__":
    main()
