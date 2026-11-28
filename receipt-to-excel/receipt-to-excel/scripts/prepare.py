"""Prepare receipt files for reading.

Walks an input folder, fixes phone rotation, shrinks big photos, splits PDFs into pages
(if pypdfium2 is installed), converts HEIC (if pillow-heif is installed), skips exact
duplicate files, and writes everything to <work>/pages/ plus a manifest.csv.

    python prepare.py <input_folder> <work_folder> [--max 1600]
"""
import argparse, csv, hashlib, os, sys
from PIL import Image, ImageOps

IMG = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif"}


def heic_ok():
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        return True
    except ImportError:
        return False


def pdf_pages(path):
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return None
    doc = pdfium.PdfDocument(path)
    return [doc[i].render(scale=2).to_pil() for i in range(len(doc))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("work")
    ap.add_argument("--max", type=int, default=1600, help="longest side in pixels")
    a = ap.parse_args()
    has_heic = heic_ok()
    out_dir = os.path.join(a.work, "pages"); os.makedirs(out_dir, exist_ok=True)
    files = sorted(os.path.join(r, f) for r, _, fs in os.walk(a.src) for f in fs)
    seen, rows, skipped = {}, [], []
    n = 0
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext not in IMG and ext != ".pdf":
            continue
        h = hashlib.md5(open(f, "rb").read()).hexdigest()
        rel = os.path.relpath(f, a.src)
        if h in seen:
            skipped.append((rel, "same file as " + seen[h])); continue
        seen[h] = rel
        if ext in (".heic", ".heif") and not has_heic:
            skipped.append((rel, "HEIC needs: pip install pillow-heif")); continue
        if ext == ".pdf":
            pages = pdf_pages(f)
            if pages is None:
                skipped.append((rel, "PDF needs: pip install pypdfium2")); continue
        else:
            try:
                pages = [ImageOps.exif_transpose(Image.open(f))]
            except Exception as e:
                skipped.append((rel, f"cannot open: {e}")); continue
        for pi, im in enumerate(pages, 1):
            n += 1
            im = im.convert("RGB")
            im.thumbnail((a.max, a.max))
            page_id = f"{n:04d}"
            name = f"{page_id}.jpg"
            im.save(os.path.join(out_dir, name), quality=88)
            rows.append({"page_id": page_id, "page_file": "pages/" + name, "source": rel,
                         "pdf_page": pi if ext == ".pdf" else ""})
    with open(os.path.join(a.work, "manifest.csv"), "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.DictWriter(fp, fieldnames=["page_id", "page_file", "source", "pdf_page"])
        w.writeheader(); w.writerows(rows)
    with open(os.path.join(a.work, "skipped.csv"), "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.writer(fp); w.writerow(["source", "reason"]); w.writerows(skipped)
    print(f"pages ready: {len(rows)}  skipped: {len(skipped)}  -> {out_dir}")
    for s in skipped[:20]:
        print("  skipped:", s[0], "|", s[1])


if __name__ == "__main__":
    sys.exit(main())
