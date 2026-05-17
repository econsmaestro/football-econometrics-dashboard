"""
WhatsApp Bulk Messenger
-----------------------
Sends the same message to multiple contacts by opening pre-filled
WhatsApp Web links in your browser.

HOW TO USE:
1. Make sure you are already logged into WhatsApp Web in your browser
   (go to web.whatsapp.com and scan the QR code once — it stays logged in)
2. Edit the PHONE_NUMBERS list below with all 27 numbers (include country code, no + or spaces)
3. Edit the MESSAGE below with your message
4. Run:  python whatsapp_bulk_send.py
5. For each contact a browser tab will open — click "Send" (the arrow button), then come back
   The script waits for you between each one
"""

import webbrowser
import urllib.parse
import time

# ── EDIT THESE ──────────────────────────────────────────────────────────────

# Phone numbers with country code, digits only (no +, spaces, or dashes)
# Example: "447911123456" for a UK number +44 7911 123456
PHONE_NUMBERS = [
    "447911000001",
    "447911000002",
    "447911000003",
    "447911000004",
    "447911000005",
    "447911000006",
    "447911000007",
    "447911000008",
    "447911000009",
    "447911000010",
    "447911000011",
    "447911000012",
    "447911000013",
    "447911000014",
    "447911000015",
    "447911000016",
    "447911000017",
    "447911000018",
    "447911000019",
    "447911000020",
    "447911000021",
    "447911000022",
    "447911000023",
    "447911000024",
    "447911000025",
    "447911000026",
    "447911000027",
]

MESSAGE = """Hello! Please replace this with your actual message.

You can use multiple lines.
"""

# Seconds to wait between opening each tab (gives you time to click Send)
DELAY_SECONDS = 15

# ── DO NOT EDIT BELOW THIS LINE ─────────────────────────────────────────────

def build_url(phone: str, message: str) -> str:
    encoded = urllib.parse.quote(message)
    return f"https://web.whatsapp.com/send?phone={phone}&text={encoded}"


def main():
    total = len(PHONE_NUMBERS)
    print(f"WhatsApp Bulk Sender — {total} contacts")
    print("Make sure you are logged into WhatsApp Web in your browser first!\n")
    input("Press Enter when ready to start...")

    for i, number in enumerate(PHONE_NUMBERS, start=1):
        url = build_url(number, MESSAGE)
        print(f"[{i}/{total}] Opening chat for {number} ...")
        webbrowser.open(url)

        if i < total:
            print(f"         -> Click Send in the browser tab, then wait.")
            print(f"         -> Next contact opens in {DELAY_SECONDS} seconds...\n")
            time.sleep(DELAY_SECONDS)

    print("\nAll done! All contacts have been opened.")


if __name__ == "__main__":
    main()
