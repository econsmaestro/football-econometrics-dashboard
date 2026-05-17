"""
WhatsApp Bulk Messenger
-----------------------
Opens a pre-filled WhatsApp Web chat for each number in the list.
Works in both Jupyter and the terminal.

HOW TO USE:
1. Log into WhatsApp Web in your browser (web.whatsapp.com) and keep it open
2. Fill in PHONE_NUMBERS and MESSAGE below
3. Run all cells (in Jupyter) or: python whatsapp_bulk_send.py (in terminal)
4. Click Send for each tab that opens — the next one opens automatically
"""

import urllib.parse
import time

# ── EDIT THESE ──────────────────────────────────────────────────────────────

# Singapore numbers — 8 digits, no country code needed
# The script adds +65 automatically
PHONE_NUMBERS = [
    "91234567",
    "81234567",
    # ... add all 27 numbers here, one per line, in quotes with a comma
]

MESSAGE = """Hello! Replace this with your actual message.

You can use multiple lines.
"""

# Seconds between tabs — time for you to click Send before the next one opens
DELAY_SECONDS = 15

# ── DO NOT EDIT BELOW THIS LINE ─────────────────────────────────────────────

COUNTRY_CODE = "65"


def build_url(phone):
    full_number = COUNTRY_CODE + phone.strip()
    encoded = urllib.parse.quote(MESSAGE)
    return f"https://web.whatsapp.com/send?phone={full_number}&text={encoded}"


def is_jupyter():
    try:
        from IPython import get_ipython
        return get_ipython() is not None
    except ImportError:
        return False


def send_all():
    total = len(PHONE_NUMBERS)
    if total == 0:
        print("ERROR: PHONE_NUMBERS list is empty. Add your numbers first.")
        return

    print(f"WhatsApp Bulk Sender — {total} contacts")
    print("Preview:")
    for n in PHONE_NUMBERS[:5]:
        print(f"  +{COUNTRY_CODE}{n.strip()}")
    if total > 5:
        print(f"  ... and {total - 5} more")
    print()

    if is_jupyter():
        _send_jupyter(total)
    else:
        _send_terminal(total)


def _send_jupyter(total):
    from IPython.display import display, Javascript
    input("Press Enter when WhatsApp Web is open in your browser...")
    for i, number in enumerate(PHONE_NUMBERS, start=1):
        url = build_url(number)
        print(f"[{i}/{total}] Opening +{COUNTRY_CODE}{number.strip()} ...")
        display(Javascript(f'window.open("{url}", "_blank");'))
        if i < total:
            print(f"         -> Click Send, then wait {DELAY_SECONDS}s.\n")
            time.sleep(DELAY_SECONDS)
    print("\nAll done!")


def _send_terminal(total):
    import webbrowser
    input("Press Enter when WhatsApp Web is open in your browser...")
    for i, number in enumerate(PHONE_NUMBERS, start=1):
        url = build_url(number)
        print(f"[{i}/{total}] Opening +{COUNTRY_CODE}{number.strip()} ...")
        webbrowser.open(url)
        if i < total:
            print(f"         -> Click Send, then wait {DELAY_SECONDS}s.\n")
            time.sleep(DELAY_SECONDS)
    print("\nAll done!")


if __name__ == "__main__":
    send_all()
