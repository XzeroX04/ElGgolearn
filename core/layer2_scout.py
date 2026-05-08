import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

class VideoScout:
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
        self._service = None
        if self.api_key:
            self._init_service()

    def _init_service(self):
        try:
            from googleapiclient.discovery import build
            self._service = build("youtube", "v3", developerKey=self.api_key)
        except Exception as e:
            print(f"⚠️ YouTube API init failed: {e}")

    def find_playlists(self, query: str) -> dict:
        if not self._service or not query: return {}
        try:
            req = self._service.search().list(q=query, part="snippet", maxResults=1, type="playlist", order="viewCount")
            res = req.execute()
            items = res.get("items", [])
            if items:
                pid = items[0]["id"]["playlistId"]
                return {"all_time": {"url": f"https://www.youtube.com/playlist?list={pid}", "title": items[0]["snippet"]["title"]}}
            return {}
        except Exception: return {}

    def get_playlist_details(self, playlist_url: str) -> list:
        if not self._service or "list=" not in playlist_url: return []
        try:
            playlist_id = playlist_url.split("list=")[1].split("&")[0]
            request = self._service.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=50)
            response = request.execute()
            videos = []
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                v_id = snippet.get("resourceId", {}).get("videoId")
                thumb = snippet.get("thumbnails", {}).get("medium", {}).get("url", "")
                if v_id: videos.append({"title": snippet.get("title", ""), "videoId": v_id, "thumb": thumb})
            return videos
        except Exception: return []

class AcademicScout:
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    def find_pdfs_info(self, eng_query: str) -> list:
        # تحسين الكويري للبحث عن ملفات جامعية
        search_query = f"{eng_query} university lecture notes filetype:pdf"
        print(f"🔍 Searching for: {search_query}")
        
        links = self._search_ddg(search_query)
        results = []
        for url in links[:5]:
            name = url.split("/")[-1].replace("%20", " ").replace("-", " ").replace("_", " ")
            if not name.lower().endswith(".pdf"): name += ".pdf"
            results.append({"title": name[:55], "url": url, "source": url.split("/")[2]})
        return results

    def _search_ddg(self, query: str) -> list:
        url = "https://html.duckduckgo.com/html/"
        try:
            resp = requests.post(url, data={"q": query}, headers=self.HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            return [a["href"] for a in soup.find_all("a", href=True) if ".pdf" in a["href"].lower() and "http" in a["href"]]
        except Exception: return []

    def download_selected_pdf(self, url, level_title, base_path, custom_name):
        save_path = os.path.join(base_path, "Academic_Library", re.sub(r'[\\/*?:"<>|]', "", level_title))
        os.makedirs(save_path, exist_ok=True)
        try:
            r = requests.get(url, headers=self.HEADERS, timeout=20)
            if r.status_code == 200 and len(r.content) > 10000:
                file_path = os.path.join(save_path, re.sub(r'[\\/*?:"<>|]', "", custom_name) + ".pdf")
                with open(file_path, "wb") as f: f.write(r.content)
                return file_path
        except Exception: return None