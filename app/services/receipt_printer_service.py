# reference commands https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/tmu220.html

from escpos.printer import Usb
import datetime

VENDOR_ID = 0x04b8
PRODUCT_ID = 0x0202

p = Usb(VENDOR_ID, PRODUCT_ID)

def wrap_text(text, width=32):
    words = text.split()
    lines = []
    current_line = ""
    g = 0

    for word in words:
        if len(current_line) + len(word) + (1 if current_line else 0) <=width:
            if current_line:
                current_line += " "
            current_line += word
        else:
            g += 1
            print(current_line + str(g))
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    print(current_line)
    return "\n\n".join(lines)

def print_chore(chore_name: str):
    try:
        p.set(align="center", bold=False, double_height=True)
    except: 
        p.close()
        p = Usb(VENDOR_ID, PRODUCT_ID)

    now = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")

    p.set(align="center", bold=False, double_height=True)
    p.text("================================\n")
    p.text("=========")
    p.set(align="center", bold=True, double_height=True)
    p.text("CHORE REMINDER")
    p.set(align="center", bold=False, double_height=True)
    p.text("=========\n")
    p.text("================================\n\n")
    p.set(align="center", bold=False, double_height=False)
    p.text(f"Time: {now}\n\n")
    p.text("--------------------------------\n\n")
    p.set(align="center", bold=True, double_height=False)
    wrapped = wrap_text(f'Chore: {chore_name}', width=32)
    for line in wrapped.split("\n"):
        p.text(line + "\n")
    p.set(align="center", bold=False, double_height=False)
    p.text("\n--------------------------------\n\n")
    p.text("The Devil hates slackers.\n\n\n\n\n")
    p.cut()