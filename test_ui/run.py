import os
import threading
import time
import webbrowser

from extractor import parts_for_ui
from ui        import build_html
from server    import start

KNOX_URL = "http://localhost:8080"
PORT     = 5001
DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "geno_knox_dutch", "genocad.db")


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        print("Run genocad/convert_to_db.py first")
        exit(1)

    parts = parts_for_ui(DB_PATH)
    print(f"Loaded {sum(len(v) for v in parts.values())} parts from {len(parts)} categories")

    html = build_html(parts)

    def open_browser():
        time.sleep(0.8)
        webbrowser.open(f"http://localhost:{PORT}")

    threading.Thread(target=open_browser, daemon=True).start()
    print(f"Open http://localhost:{PORT} (opening automatically...)")
    print("Press Ctrl+C to stop.\n")
    start(html, knox_url=KNOX_URL, port=PORT)