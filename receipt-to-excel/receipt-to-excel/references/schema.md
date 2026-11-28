# receipts.jsonl format

One line = one receipt. Append each receipt as soon as you have read it, so the work survives an interruption.

```json
{"page_id": "0007", "date": "2026-11-03", "time": "12:41", "store": "Daily Mart Gangnam", "business_no": "123-45-67890",
 "category": "Food", "payment": "card", "card_last4": "1234",
 "items": [{"name": "Americano", "qty": 2, "unit_price": 4500, "amount": 9000}],
 "supply": 8182, "vat": 818, "total": 9000, "currency": "KRW", "confidence": "high", "note": ""}
```

| field | rule |
|---|---|
| page_id | the 4-digit id from manifest.csv (file name in pages/ without .jpg). Several receipts on one photo share the same page_id, one line each. |
| date | YYYY-MM-DD. Two-digit years: assume 20xx. If not printed, null. |
| time | HH:MM or null |
| store | name as printed (branch included). No guessing from a logo alone. |
| business_no | as printed, else null |
| category | one of the user's categories. Default set: Food, Cafe, Groceries, Transport, Fuel, Parking, Office, Shopping, Medical, Lodging, Utilities, Other. Use the user's language for the names if they want (식비, 카페, 장보기, 교통, 주유, 주차, 사무용품, 쇼핑, 의료, 숙박, 공과금, 기타). |
| payment | card, cash, transfer, other, or null |
| card_last4 | last 4 digits if printed, else null. Never more digits than printed. |
| items | line items as printed. Leave [] if the receipt has no item lines or they are unreadable. Discounts are items with a negative amount. |
| supply, vat | net amount and tax if printed, else null. Do not calculate them yourself. |
| total | the amount actually paid (after discounts). Number only, no commas or currency signs. |
| currency | ISO code. KRW, USD, JPY, EUR ... |
| confidence | high = everything clearly readable; medium = one field unsure; low = blurry, cut off or handwritten |
| note | short reason when something is unsure, e.g. "total blurred, read as 12,000?" |

A page that is not a receipt (blank, a menu, the back side): `{"page_id": "0012", "skip": true, "note": "back of receipt"}`.

Card slips and the matching receipt for the same purchase are two pieces of paper but one expense. Record the itemized receipt, and add `"note": "card slip duplicate of 0013"` to a skip line for the slip.
