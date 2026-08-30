"""Tests for Dynamic Context-Aware Website Generation (No Default Shopping Assumptions)."""
import os
import shutil
from fastapi.testclient import TestClient
from apps.desktop.server import app
from core.planner.code_synthesizer import detect_web_domain, synthesize_project_artifacts


def test_detect_web_domain_differentiates_contexts():
    # Explicit shopping only
    assert detect_web_domain("Create an ecommerce shopping website with cart") == "shopping"
    assert detect_web_domain("Build an online clothing store") == "shopping"

    # Diverse domains must NOT be classified as shopping
    assert detect_web_domain("Create a modern portfolio website for a photographer") == "portfolio"
    assert detect_web_domain("Build a restaurant website with food menu and table booking") == "restaurant"
    assert detect_web_domain("Create a crypto price tracking dashboard website") == "crypto"
    assert detect_web_domain("Build a doctor clinic appointment website") == "doctor"
    assert detect_web_domain("Build a gym fitness website with BMI calculator") == "gym"
    assert detect_web_domain("Build a tech blog website with articles") == "blog"


def test_portfolio_synthesizes_portfolio_elements_not_shopping():
    artifacts, cmd = synthesize_project_artifacts("Create a portfolio website for a software engineer", "K:\\test_portfolio")
    html = artifacts["index.html"]

    # Must contain portfolio sections
    assert "Portfolio" in html or "Featured Work" in html or "About Me" in html
    assert "Projects" in html
    assert "Skills" in html
    # Must NOT contain shopping cart elements
    assert "cartDrawer" not in html
    assert "Cart Total" not in html


def test_restaurant_synthesizes_restaurant_menu_and_reservations():
    artifacts, cmd = synthesize_project_artifacts("Build a fine dining restaurant website with food menu", "K:\\test_rest")
    html = artifacts["index.html"]
    js = artifacts["app.js"]

    # Must contain restaurant features
    assert "Menu" in html
    assert "Reserve Table" in html or "Book a Table" in html
    assert "resModal" in html
    assert "Truffle Arancini" in js or "starters" in js


def test_end_to_end_portfolio_execution():
    test_dir = os.path.join(os.getcwd(), "scratch_test_portfolio_site")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    client = TestClient(app)
    try:
        res = client.post(
            "/api/kritimode/execute",
            json={
                "goal": f"Create a portfolio website for a designer in {test_dir}",
                "power_mode": "autonomous"
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["status"] == "completed"

        # Verify files on disk
        index_file = os.path.join(test_dir, "index.html")
        assert os.path.isfile(index_file)
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Portfolio" in content or "About" in content
        assert "cartDrawer" not in content

    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
