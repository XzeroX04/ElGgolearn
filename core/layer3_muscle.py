"""
ElGgolearn | core/layer3_muscle.py
المحرك الثالث: العضلات - تحميل الفيديوهات وإدارة الملفات
"""
import os
import re
import threading
from typing import Callable


class AlgoMuscle:
    """مسؤول عن تحميل قوائم تشغيل YouTube وتنظيم الملفات"""

    DEFAULT_BASE = os.path.join(os.path.expanduser("~"), "Downloads", "ElGgolearn")

    def sanitize(self, name: str) -> str:
        return re.sub(r'[\\/*?:"<>|\n\r\t]', "", name).strip().replace(" ", "_")[:60]

    def download_playlist(
        self,
        url          : str,
        folder_name  : str,
        base_path    : str | None,
        progress_hook: Callable | None = None,
    ) -> None:
        """
        يحمّل قائمة تشغيل YouTube في thread منفصل.
        progress_hook: دالة تُستدعى مع dict من yt-dlp
        """
        try:
            import yt_dlp
        except ImportError:
            print("❌ yt-dlp غير مثبّت. شغّل: pip install yt-dlp")
            return

        base      = base_path or self.DEFAULT_BASE
        folder    = self.sanitize(folder_name)
        save_path = os.path.join(base, "Video_Lessons", folder)
        os.makedirs(save_path, exist_ok=True)

        ydl_opts = {
            "format"          : "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl"         : os.path.join(save_path, "%(playlist_index)02d - %(title)s.%(ext)s"),
            "noplaylist"      : False,
            "ignoreerrors"    : True,
            "retries"         : 3,
            "quiet"           : True,
            "no_warnings"     : True,
        }

        if progress_hook:
            ydl_opts["progress_hooks"] = [progress_hook]

        def _run():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                print(f"✅ Download complete: {folder}")
            except Exception as e:
                print(f"❌ Download error: {e}")

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def get_folder_size(self, path: str) -> str:
        """حجم مجلد بصيغة نصية (KB/MB/GB)"""
        try:
            total = sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, files in os.walk(path)
                for f in files
            )
            for unit in ("B", "KB", "MB", "GB"):
                if total < 1024:
                    return f"{total:.1f} {unit}"
                total /= 1024
            return f"{total:.1f} TB"
        except Exception:
            return "0 B"