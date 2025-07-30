import requests
import os
import pytest


def test_healthz():
    """Тест health check энд-поинта"""
    url = f"http://localhost:{os.getenv('PORT_HEALTH', '8080')}/healthz"
    r = requests.get(url, timeout=2)
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_metrics():
    """Тест Prometheus метрик"""
    url = f"http://localhost:{os.getenv('PORT_HEALTH', '8080')}/metrics"
    r = requests.get(url, timeout=2)
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "") 