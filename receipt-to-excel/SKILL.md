---
name: receipt-to-excel
description: Turns a pile of receipt photos or PDFs (tens to hundreds) into one tidy Excel file - date, store, category, payment, items, tax and total for each receipt, monthly and category totals, and a "to check" sheet for blurry or duplicate receipts. Resumable, so large batches can be done over several sittings.
---

# Receipt Photos to Excel

The user drops receipt photos (phone shots, scans, screenshots, PDFs) into one folder.
You read every receipt yourself, write one line per receipt to `receipts.jsonl`, and a script builds the workbook.
Nothing is sent to an outside OCR service; the reading is done by you in this conversation.

Reply to the user in their language. Use their language for categories and sheet names (`--lang ko` for Korean, `--lang en` otherwise).

## What you need
- Python 3.9+ with `pip install pillow openpyxl`
- Optional: `pip install pillow-heif` (iPhone HEIC photos), `pip install pypdfium2` (PDF receipts)

Check these first. If something is missing, give the exact install command.

## Workflow

1. **Ask only what is missing** (otherwise use defaults):
   - Folder with the receipts. Output goes to a new work folder next to it (`<folder>_excel`), never inside the originals.
   - Categories: default list in `references/schema.md`, or the user's own (e.g. their accounting codes).
   - Anything to skip (e.g. personal purchases) - default: include everything.

2. **Prepare** (never edit the original files):
   ```
   python <skill>/scripts/prepare.py "<receipt folder>" "<work folder>"
   ```
   This fixes rotation, shrinks big photos, splits PDFs into pages, drops exact duplicate files, and writes
   `pages/0001.jpg ...` plus `manifest.csv`. Tell the user how many pages and anything in `skipped.csv`.

3. **Read the receipts in batches of 5 to 10 pages.**
   - Open each `pages/NNNN.jpg` with your image reading tool and fill the fields in `references/schema.md`.
   - Append to `<work>/receipts.jsonl` right after each batch (one JSON object per line). Do not hold hundreds in memory.
   - Read what is printed. Never invent a date, store, card number or amount. If a value is unreadable, use null,
     set `confidence` to `low` and say why in `note`.
   - The total is the amount actually paid, after discounts.
   - One photo with several receipts: one line each, same `page_id`.
   - After every few batches run `python <skill>/scripts/build_xlsx.py "<work>" --status` and tell the user the progress
     (e.g. "120 / 340 pages read"). With hundreds of pages, offer to stop and continue later; `--status` shows where to resume.

4. **Build the workbook**
   ```
   python <skill>/scripts/build_xlsx.py "<work>" --lang ko
   ```
   Sheets: receipt list (with a totals row and a link to each page image), line items, summary by month / category / payment,
   and **to check** (low confidence, missing date or total, items not adding up, net + tax not equal to total, possible duplicates).

5. **Before handing over**
   - Open the "to check" rows' page images again and fix what you can in `receipts.jsonl`, then rebuild.
   - Spot-check at least 5 random receipts against their images.
   - Report: file path, number of receipts, grand total per currency, how many are left in "to check" and why.
   - Say plainly that the numbers were read from photos and the user should confirm the flagged rows before using them for tax or expense claims.

## Notes
- Keep the work folder: re-running step 4 after edits is instant, and new receipts can be added later
  (run prepare again into a new work folder, or ask the user if they want them merged).
- Mixed currencies are kept as they are. Do not convert unless the user gives a rate.
- Card numbers, business numbers and addresses stay in the user's own files only.

---
만든이: sphereai.work (https://sphereai.work)
