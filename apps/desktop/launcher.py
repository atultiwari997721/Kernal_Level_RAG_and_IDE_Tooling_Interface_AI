"""Windows Desktop Launcher for KritiAI."""
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
import uvicorn

from config.settings import get_config


def start_server(host: str, port: int) -> None:
    """Run uvicorn server in worker thread."""
    uvicorn.run("apps.desktop.server:app", host=host, port=port, log_level="info")


def launch_native_window(url: str) -> None:
    """Launch application in a borderless native Windows desktop app window."""
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        shutil.which("msedge.exe") or ""
    ]
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("chrome.exe") or ""
    ]

    # Try Edge App Mode first (standard on Windows 10 & 11)
    for p in edge_paths:
        if p and os.path.isfile(p):
            try:
                subprocess.Popen([p, f"--app={url}", "--new-window"])
                return
            except Exception:
                pass

    # Try Chrome App Mode
    for p in chrome_paths:
        if p and os.path.isfile(p):
            try:
                subprocess.Popen([p, f"--app={url}", "--new-window"])
                return
            except Exception:
                pass

    # Fallback to system default browser
    webbrowser.open(url)


def main() -> None:
    config = get_config()
    host = config.host
    port = config.port
    url = f"http://{host}:{port}"

    print("=" * 60)
    print("  KritiAI: Windows Autonomous AI Execution Platform v0.1")
    print(f"  Local Desktop Server: {url}")
    print("  Power Mode: AUTONOMOUS (Zero user interaction by default)")
    print("  Local Model & Watchdog: ACTIVE")
    print("=" * 60)

    # Start FastAPI server in background thread
    server_thread = threading.Thread(target=start_server, args=(host, port), daemon=True)
    server_thread.start()

    # Wait for server startup
    time.sleep(1.2)

    # Launch desktop window unless --headless argument passed
    if "--headless" not in sys.argv:
        launch_native_window(url)

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping KritiAI Desktop...")


if __name__ == "__main__":
    main()
