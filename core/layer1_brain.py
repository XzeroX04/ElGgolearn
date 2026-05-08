"""
ElGgolearn | core/layer1_brain.py
المحرك الأول: الذكاء الاصطناعي - توليد خارطة الطريق المخصصة
الإصلاحات:
  - Flash أول في القائمة لتوفير الكوتا
  - نظام تخزين مؤقت (Caching) محلي لتفادي استدعاء API مكرر
"""
import os
import sys
import json
import hashlib
from google import genai
from dotenv import load_dotenv

# ── البحث عن api.env بجانب ملف الـ EXE ──
if getattr(sys, 'frozen', False):
    # الفولدر اللي فيه ملف ElGgolearn_Pro.exe
    dir_path = os.path.dirname(sys.executable)
    env_path = os.path.join(dir_path, 'api.env')
else:
    # فولدر التطوير العادي
    env_path = os.path.join(os.path.dirname(__file__), '..', 'api.env')

load_dotenv(env_path)
# مسار ملف الـ Cache محلياً
CACHE_FILE = os.path.join(os.path.expanduser("~"), "Downloads", "ElGgolearn", ".cache.json")


class AlgoBrain:
    # Flash أولاً لتوفير الكوتا، Pro كاحتياط فقط
    MODELS = [
        "gemini-2.5-flash",      # ✅ سريع ورخيص - الافتراضي
        "gemini-2.0-flash",      # ✅ احتياط أول
        "gemini-2.0-flash-lite", # ✅ احتياط ثانٍ
        "gemini-2.5-pro",        # ⚠️ غالي - آخر ملجأ
    ]

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY غير موجود في ملف api.env")
        self.client = genai.Client(api_key=api_key)
        self._cache: dict = self._load_cache()

    # ── الـ Cache ──────────────────────────────────────────────────────
    def _load_cache(self) -> dict:
        """تحميل ملف الـ Cache من الجهاز"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_cache(self):
        """حفظ الـ Cache على الجهاز"""
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Cache save failed: {e}")

    def _cache_key(self, topic: str, level: str, lang: str) -> str:
        """إنشاء مفتاح فريد للـ Cache"""
        raw = f"{topic.strip().lower()}|{level}|{lang}"
        return hashlib.md5(raw.encode()).hexdigest()

    # ── توليد خارطة الطريق ────────────────────────────────────────────
    def generate_roadmap(self, topic: str, level: str, lang: str) -> dict:
        """
        يولّد خارطة طريق JSON لمستوى محدد.
        يتحقق من الـ Cache أولاً، ثم يستدعي Gemini إذا لزم.
        """
        if not topic or not topic.strip():
            raise ValueError("الرجاء إدخال موضوع للبحث.")

        # ── فحص الـ Cache أولاً (صفر كوتا) ──────────────────────────
        key = self._cache_key(topic, level, lang)
        if key in self._cache:
            print(f"⚡ Brain → Cache HIT for [{topic} | {level}]")
            return self._cache[key]

        # ── استدعاء Gemini إذا لم يوجد في الـ Cache ──────────────────
        prompt = f"""
        Act as a Senior AI Academic Architect.
        Task: Create a highly detailed learning roadmap for: {topic}.
        Target Level: {level}
        Response Language: {lang}

        Create exactly 3 structured modules for this specific level.
        For each module, provide:
        - id: (1, 2, or 3)
        - title: Professional title in {lang}
        - eng_query: Precise search query for academic PDFs (e.g., 'machine learning introduction lecture notes filetype:pdf')
        - yt_query: VERY SHORT and SIMPLE YouTube search query in {lang} targeting a full course playlist (e.g., '{topic} {level} course tutorial'). DO NOT use complex words or OR/AND operators.
        - summary: 2-sentence summary of the module goals in {lang}.

        Return ONLY raw JSON, no markdown, no explanations.
        Format: {{ "topic": "{topic}", "level": "{level}", "levels": [...] }}
        """
        last_error = None

        for model in self.MODELS:
            try:
                print(f"🤖 Brain → {model}...")

                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                )

                text = response.text.strip()
                text = self._clean_json(text)
                data = json.loads(text)

                self._validate(data)
                print(f"✅ Brain → Roadmap ready via {model}")

                # ── حفظ في الـ Cache ────────────────────────────────
                self._cache[key] = data
                self._save_cache()

                return data

            except json.JSONDecodeError as e:
                print(f"⚠️ {model} → JSON parse error: {e}")
                last_error = "فشل في تحليل رد الذكاء الاصطناعي. حاول مجدداً."
                continue

            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    print(f"⚠️ {model} → Quota (429), trying next...")
                    last_error = "حصة API ممتلئة. انتظر 60 ثانية."
                elif "404" in err or "NOT_FOUND" in err:
                    print(f"⚠️ {model} → Not found, trying next...")
                    last_error = "الموديل غير متاح."
                elif "401" in err or "UNAUTHORIZED" in err:
                    raise Exception("❌ API Key خاطئ. تحقق من ملف api.env")
                else:
                    print(f"⚠️ {model} → {err[:100]}")
                    last_error = err[:120]
                continue

        raise Exception(
            f"❌ جميع موديلات Gemini غير متاحة حالياً.\n"
            f"السبب: {last_error}\n"
            f"انتظر 60 ثانية وأعد المحاولة."
        )

    def clear_cache(self):
        """مسح الـ Cache بالكامل"""
        self._cache = {}
        try:
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
            print("🗑️ Cache cleared.")
        except Exception as e:
            print(f"⚠️ Cache clear failed: {e}")

    @staticmethod
    def _clean_json(text: str) -> str:
        """إزالة أي markdown أو نص زائد حول JSON"""
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]
        return text.strip()

    @staticmethod
    def _validate(data: dict):
        """التحقق من صحة بنية البيانات"""
        assert "topic" in data, "المفتاح 'topic' مفقود"
        assert "levels" in data, "المفتاح 'levels' مفقود"
        assert len(data["levels"]) == 3, "يجب أن تكون هناك 3 وحدات"
        for lvl in data["levels"]:
            for key in ("id", "title", "eng_query", "yt_query", "summary"):
                assert key in lvl, f"المفتاح '{key}' مفقود في الوحدة {lvl.get('id')}"