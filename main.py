import sys
import os
import webview
import io

# ── 1. قتل أي محاولة للطباعة فوراً لمنع الانهيار ──
def silence_all():
    if getattr(sys, 'frozen', False):
        # توجيه كل المخارج إلى "الثقب الأسود" (devnull)
        f = open(os.devnull, 'w', encoding='utf-8')
        sys.stdout = f
        sys.stderr = f
        # منع أي مكتبة من فتح Terminal داخلي
        sys.__stdout__ = f
        sys.__stderr__ = f

silence_all()

# استيراد باقي المكونات بعد الصمت
from ui.app import ElGgoAPI

def resource_path(relative_path):
    """ الحصول على الملفات المدمجة داخل الـ EXE """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    api = ElGgoAPI()
    html_path = resource_path(os.path.join("ui", "index.html"))

    window = webview.create_window(
        title    = "ElGgolearn | Academic AI Pro",
        url      = html_path,
        js_api   = api,
        width    = 1100,
        height   = 750,
        background_color = "#07090f"
    )

    api.set_window(window)
    webview.start()

if __name__ == "__main__":
    main()