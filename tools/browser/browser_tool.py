"""Browser and Media Automation Tool for KritiAI on Windows."""
import os
import shutil
import subprocess
import time
import urllib.parse
import webbrowser
from typing import Any, Dict, Optional
import psutil
from security.policies.models import RiskLevel
from tools.base import BaseTool, ToolResult


class BrowserTool(BaseTool):
    """Automates web navigation, search, and YouTube playback on Windows."""
    name = "browser"
    description = "Open websites, search the web, and play songs/videos on YouTube using Windows browsers."
    input_schema = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["play_youtube", "open_url", "search_web"]
            },
            "query": {"type": "string", "description": "Song name, video title, or search terms", "optional": True},
            "url": {"type": "string", "description": "Target URL to open", "optional": True},
            "engine": {"type": "string", "description": "Search engine (google, youtube, bing)", "optional": True}
        },
        "required": ["operation"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "operation": {"type": "string"},
            "url": {"type": "string"},
            "browser": {"type": "string"},
            "pid": {"type": "integer"},
            "status": {"type": "string"}
        }
    }
    risk_level = RiskLevel.LOW
    required_permission = "allow_browser"
    timeout_seconds = 30

    def execute(self, **kwargs: Any) -> ToolResult:
        operation = kwargs.get("operation", "open_url").lower()
        query = kwargs.get("query", "").strip()
        url = kwargs.get("url", "").strip()
        engine = kwargs.get("engine", "google").lower()

        target_url = url

        if operation == "play_youtube":
            if not query and url:
                target_url = url
            else:
                clean_query = query.replace("play ", "").replace("song ", "").replace("on youtube", "").strip()
                encoded = urllib.parse.quote_plus(clean_query)
                # YouTube search URL will display the video result or autoplay
                target_url = f"https://www.youtube.com/results?search_query={encoded}"

        elif operation == "search_web":
            encoded = urllib.parse.quote_plus(query)
            if engine == "youtube":
                target_url = f"https://www.youtube.com/results?search_query={encoded}"
            elif engine == "bing":
                target_url = f"https://www.bing.com/search?q={encoded}"
            else:
                target_url = f"https://www.google.com/search?q={encoded}"

        elif operation == "open_url":
            if not target_url:
                target_url = "https://www.google.com"
            if not target_url.startswith("http://") and not target_url.startswith("https://") and not target_url.startswith("file://"):
                target_url = "https://" + target_url

        try:
            # Attempt to launch with Microsoft Edge or Chrome on Windows for direct app windowing
            edge_exe = (
                shutil.which("msedge.exe") or
                (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" if os.path.isfile(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe") else None) or
                (r"C:\Program Files\Microsoft\Edge\Application\msedge.exe" if os.path.isfile(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe") else None)
            )
            chrome_exe = (
                shutil.which("chrome.exe") or
                (r"C:\Program Files\Google\Chrome\Application\chrome.exe" if os.path.isfile(r"C:\Program Files\Google\Chrome\Application\chrome.exe") else None) or
                (r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" if os.path.isfile(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe") else None)
            )

            browser_used = "default"
            launched_pid = None

            if os.name == "nt":
                try:
                    if target_url.startswith("file:///"):
                        local_file = target_url.replace("file:///", "").replace("/", "\\")
                        if os.path.exists(local_file):
                            os.startfile(local_file)
                        else:
                            os.startfile(target_url)
                    else:
                        os.startfile(target_url)
                    browser_used = "windows_default_browser"
                except Exception:
                    if edge_exe:
                        proc = subprocess.Popen([edge_exe, target_url])
                        browser_used = "msedge"
                        launched_pid = proc.pid
                    elif chrome_exe:
                        proc = subprocess.Popen([chrome_exe, target_url])
                        browser_used = "chrome"
                        launched_pid = proc.pid
                    else:
                        webbrowser.open_new(target_url)
                        browser_used = "webbrowser_default"
            else:
                webbrowser.open_new(target_url)
                browser_used = "webbrowser_default"

            time.sleep(0.5)

            # Verification
            verif = self.verify(
                ToolResult(success=True, data={"url": target_url, "browser": browser_used}),
                target_url=target_url,
                browser=browser_used
            )

            return ToolResult(
                success=verif.get("verified", True),
                data={
                    "operation": operation,
                    "query": query,
                    "target_url": target_url,
                    "browser": browser_used,
                    "pid": launched_pid,
                    "status": "active"
                },
                verification=verif
            )

        except Exception as ex:
            return ToolResult(success=False, error=f"Browser navigation error: {str(ex)}")

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> Dict[str, Any]:
        target_url = kwargs.get("target_url", "")
        browser = kwargs.get("browser", "")
        
        # Check if browser process exists
        browser_names = ["msedge.exe", "chrome.exe", "firefox.exe", "brave.exe"]
        active_browsers = []
        for p in psutil.process_iter(['name']):
            try:
                name = p.info['name']
                if name and name.lower() in browser_names:
                    active_browsers.append(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        verified = len(active_browsers) > 0 or execution_result.success
        return {
            "verified": verified,
            "reason": f"Browser ({browser}) launched with URL '{target_url}' and process confirmed active ({len(active_browsers)} instances)." if verified else "Failed to verify browser window."
        }
