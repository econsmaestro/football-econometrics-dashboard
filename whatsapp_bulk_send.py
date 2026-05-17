"""
WhatsApp Bulk Messenger
-----------------------
Reads phone numbers from an Excel file and sends the same WhatsApp
message to each contact by opening pre-filled WhatsApp Web links.

SETUP (one time):
    pip install openpyxl

HOW TO USE:
1. Copy the Excel file from the ops support net laptop to a USB drive,
   then transfer it to your internet-connected laptop
2. Log into WhatsApp Web in your browser (web.whatsapp.com) and keep it open
3. Fill in the settings below (Excel file path, column, message)
4. Run:  python whatsapp_bulk_send.py
5. For each contact a browser tab opens with the message pre-typed
   — just click Send, come back, and the next one opens automatically
"""

import webbrowser
import urllib.parse
import time
import openpyxl

# ── EDIT THESE ──────────────────────────────────────────────────────────────

# Path to your Excel file — use the full path or put the file in the same
# folder as this script and just write the filename, e.g. "contacts.xlsx"
EXCEL_FILE = "contacts.xlsx"

# Which sheet tab contains the numbers (name or 1-based index)
SHEET = 1

# Which column has the phone numbers — "A", "B", etc.
NUMBER_COLUMN = "A"

# Does the first row have a header (column title)? True = skip row 1
HAS_HEADER = True

# Country code to add to every number (digits only, no + sign)
COUNTRY_CODE = "65"  # Singapore

# Your message — you can use multiple lines
MESSAGE = """Hello! Please replace this with your actual message.

You can use multiple lines here.
"""

# Seconds to wait between tabs — enough time for you to click Send
DELAY_SECONDS = 15

# ── DO NOT EDIT BELOW THIS LINE ─────────────────────────────────────────────

def load_numbers_from_excel(filepath, sheet, column, has_header, country_code):
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb[sheet] if isinstance(sheet, str) else wb.worksheets[sheet - 1]

    numbers = []
    col_letter = column.upper()
    start_row = 2 if has_header else 1

    for row in ws.iter_rows(min_row=start_row, min_col=openpyxl.utils.column_index_from_string(col_letter),
                             max_col=openpyxl.utils.column_index_from_string(col_letter)):
        cell_value = row[0].value
        if cell_value is None:
            continue
        # If Excel stored the number as a numeric type (int/float), cast to int
        # first to avoid "7911123456.0" becoming "79111234560" after digit filter
        if isinstance(cell_value, float):
            cell_value = int(cell_value)
        # Strip spaces, dashes, brackets — keep digits only
        digits = "".join(filter(str.isdigit, str(cell_value)))
        # Remove a leading zero (common in local numbers e.g. 07911...)
        if digits.startswith("0"):
            digits = digits[1:]
        if digits:
            numbers.append(country_code + digits)

    return numbers


def build_url(phone, message):
    encoded = urllib.parse.quote(message)
    return f"https://web.whatsapp.com/send?phone={phone}&text={encoded}"


def main():
    print("Reading numbers from Excel...")
    try:
        numbers = load_numbers_from_excel(EXCEL_FILE, SHEET, NUMBER_COLUMN, HAS_HEADER, COUNTRY_CODE)
    except FileNotFoundError:
        print(f"ERROR: Could not find '{EXCEL_FILE}'. Check the path and try again.")
        return

    if not numbers:
        print("ERROR: No numbers found. Check SHEET, NUMBER_COLUMN, and HAS_HEADER settings.")
        return

    total = len(numbers)
    print(f"Found {total} numbers.\n")
    print("Preview (first 5):")
    for n in numbers[:5]:
        print(f"  +{n}")
    print()

    input(f"Press Enter to start sending (make sure WhatsApp Web is open in your browser)...")

    for i, number in enumerate(numbers, start=1):
        url = build_url(number, MESSAGE)
        print(f"[{i}/{total}] Opening chat for +{number} ...")
        webbrowser.open(url)

        if i < total:
            print(f"         -> Click Send, then wait {DELAY_SECONDS}s for the next one.\n")
            time.sleep(DELAY_SECONDS)

    print("\nAll done!")


if __name__ == "__main__":
    main()
