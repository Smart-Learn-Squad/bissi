
import sys
from pathlib import Path

# Ajout du dossier racine au PATH
sys.path.insert(0, str(Path(__file__).parent))

from manager import get_manager
import os

def run_diagnostic():
    manager = get_manager()
    results = []

    print("=== DIAGNOSTIC DES OUTILS BISSI ===\n")

    # 1. Test Word (Write/Read)
    try:
        print("[*] Test Word...")
        path = "diag_word.docx"
        res_w = manager._tool_write_word(path, "Diagnostic BISSI - Test Word")
        res_r = manager._tool_read_word(path)
        status = "OK" if res_w['success'] and res_r['success'] else "FAILED"
        results.append(f"Word: {status}")
        if status == "OK": os.remove(path)
    except Exception as e: results.append(f"Word: ERROR ({e})")

    # 2. Test Excel (Write/Read)
    try:
        print("[*] Test Excel...")
        path = "diag_excel.xlsx"
        data = [{"Test": "A", "Val": 1}, {"Test": "B", "Val": 2}]
        res_w = manager._tool_write_excel(path, data)
        res_r = manager._tool_read_excel(path)
        status = "OK" if res_w['success'] and res_r['success'] else "FAILED"
        results.append(f"Excel: {status}")
        if status == "OK": os.remove(path)
    except Exception as e: results.append(f"Excel: ERROR ({e})")

    # 3. Test PowerPoint (Write/Read)
    try:
        print("[*] Test PowerPoint...")
        path = "diag_ppt.pptx"
        slides = [{"title": "Diag Slide", "content": "Content Test"}]
        res_w = manager._tool_write_pptx(path, "Diag Title", slides)
        res_r = manager._tool_read_pptx(path)
        status = "OK" if res_w['success'] and res_r['success'] else "FAILED"
        results.append(f"PowerPoint: {status}")
        if status == "OK": os.remove(path)
    except Exception as e: results.append(f"PowerPoint: ERROR ({e})")

    # 4. Test Clipboard
    try:
        print("[*] Test Clipboard...")
        test_text = "BISSI_CLIPBOARD_TEST_2026"
        manager._tool_set_clipboard(test_text)
        res_g = manager._tool_get_clipboard()
        status = "OK" if res_g.get('content') == test_text else "FAILED (Clipboard may be blocked on this OS)"
        results.append(f"Clipboard: {status}")
    except Exception as e: results.append(f"Clipboard: ERROR ({e})")

    # 5. Test Python Runner
    try:
        print("[*] Test Python Runner...")
        res = manager._tool_python_runner("print(21 * 2)")
        status = "OK" if res['success'] and "42" in res['output'] else "FAILED"
        results.append(f"Python Runner: {status}")
    except Exception as e: results.append(f"Python Runner: ERROR ({e})")

    print("\n=== RÉSUMÉ DU DIAGNOSTIC ===")
    for r in results:
        print(r)

if __name__ == "__main__":
    run_diagnostic()
