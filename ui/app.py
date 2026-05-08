import os
import sys
import json
import threading
import webview
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.layer1_brain import AlgoBrain
from core.layer2_scout import AcademicScout, VideoScout
from core.layer3_muscle import AlgoMuscle
from core.layer4_pdf import create_study_tracker
from core.database import DatabaseManager

class ElGgoAPI:
    def __init__(self):
        self._window = None
        self._brain = AlgoBrain()
        self._scout_ac = AcademicScout()
        self._scout_yt = VideoScout()
        self._muscle = AlgoMuscle()
        self._db = DatabaseManager()
        self._folder = os.path.join(os.path.expanduser("~"), "Downloads", "ElGgolearn")
        self._roadmap = None
        
    def set_window(self, window):
        self._window = window

    # ─── واجهات جلب البيانات للصفحات المنفصلة ───
    def get_saved_videos(self) -> dict:
        try:
            return {"ok": True, "data": self._db.get_library_by_type('video')}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_saved_books(self) -> dict:
        try:
            return {"ok": True, "data": self._db.get_library_by_type('pdf')}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_course_content(self, playlist_url: str, playlist_title: str = "Course") -> dict:
        try:
            self._db.log_library(playlist_title, playlist_url, 'video')
            videos = self._scout_yt.get_playlist_details(playlist_url)
            return {"ok": True, "videos": videos}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def download_single_pdf(self, url: str, level_title: str, custom_name: str) -> dict:
        try:
            self._emit(f"⬇️ جاري التحميل...")
            self._db.log_library(custom_name, url, 'pdf')
            path = self._scout_ac.download_selected_pdf(url, level_title, self._folder, custom_name)
            if path:
                self._emit("✅ تم التحميل بنجاح!")
                return {"ok": True, "path": path}
            return {"ok": False, "error": "عذراً، الملف محمي أو معطوب."}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ─── توليد وإدارة المسارات ───
    def generate_roadmap(self, topic: str, level: str, lang: str) -> dict:
        try:
            self._emit(f"🤖 جاري بناء المسار...")
            roadmap = self._brain.generate_roadmap(topic, level, lang)
            self._roadmap = roadmap
            roadmap_id = self._db.save_roadmap(topic, level, lang, roadmap)
            threading.Thread(target=self._fetch_yt_links, args=(roadmap,), daemon=True).start()
            return {"ok": True, "data": roadmap, "db_id": roadmap_id}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_history(self) -> dict:
        try:
            return {"ok": True, "data": self._db.get_all_roadmaps()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def load_saved_roadmap(self, roadmap_id: int) -> dict:
        try:
            data = self._db.get_roadmap_by_id(roadmap_id)
            if data:
                self._roadmap = data
                return {"ok": True, "data": data}
            return {"ok": False, "error": "المسار غير موجود"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ─── خدمات إضافية ───
    def get_pdf_suggestions(self, eng_query: str) -> dict:
        try:
            self._emit("🔍 جاري البحث عن مراجع...")
            results = self._scout_ac.find_pdfs_info(eng_query)
            return {"ok": True, "data": results} if results else {"ok": False, "error": "لم يتم العثور على مراجع."}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def download_playlist(self, url: str, folder_name: str) -> dict:
        try:
            def hook(d):
                if d.get("status") == "downloading":
                    self._emit(f"⬇️ جاري التحميل: {d.get('_percent_str', '?%')}")
                elif d.get("status") == "finished":
                    self._emit("✅ اكتمل التحميل!")
            self._muscle.download_playlist(url, folder_name, self._folder, hook)
            return {"ok": True, "message": "بدأ التحميل"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def export_pdf(self, roadmap: dict) -> dict:
        try:
            os.makedirs(self._folder, exist_ok=True)
            safe_name = re.sub(r'[\\/*?:"<>|]', "", roadmap.get("topic", "Study"))
            out = os.path.join(self._folder, f"Roadmap_{safe_name}.pdf")
            ok = create_study_tracker(roadmap, [], out)
            return {"ok": ok, "path": out if ok else ""}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def open_url(self, url: str) -> dict:
        import subprocess
        try:
            if sys.platform == "win32": os.startfile(url)
            elif sys.platform == "darwin": subprocess.Popen(["open", url])
            else: subprocess.Popen(["xdg-open", url])
            return {"ok": True}
        except: return {"ok": False}

    def clear_cache(self) -> dict:
        self._brain.clear_cache()
        return {"ok": True}

    def _fetch_yt_links(self, roadmap: dict):
        for level in roadmap.get("levels", []):
            try:
                result = self._scout_yt.find_playlists(level.get("yt_query", ""))
                if self._window:
                    safe = json.dumps(result, ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "")
                    self._window.evaluate_js(f"window.ElGgoAPI && window.ElGgoAPI.onYTLinks({level.get('id', 1)}, '{safe}')")
            except: pass

    def _emit(self, msg: str):
        if self._window:
            safe = msg.replace("'", "\\'").replace("\n", " ")
            try: self._window.evaluate_js(f"window.ElGgoAPI && window.ElGgoAPI.onStatusUpdate('{safe}')")
            except: pass