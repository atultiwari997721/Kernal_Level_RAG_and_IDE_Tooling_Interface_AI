"""Tests for Browser and Media Automation Tool."""
from tools.browser.browser_tool import BrowserTool


def test_browser_play_youtube_url_construction():
    tool = BrowserTool()
    res = tool.execute(operation="play_youtube", query="Sita Ram song")
    assert res.success is True
    assert "youtube.com/results" in res.data["target_url"]
    assert "Sita+Ram+song" in res.data["target_url"] or "Sita" in res.data["target_url"]
    assert res.verification["verified"] is True


def test_browser_search_web():
    tool = BrowserTool()
    res = tool.execute(operation="search_web", query="best local llms", engine="google")
    assert res.success is True
    assert "google.com/search" in res.data["target_url"]
