import json

from guni import llm_analyzer


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps({"ok": True}).encode("utf-8")


def test_llm_request_uses_extended_default_timeout(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout, **kwargs):
        captured["timeout"] = timeout
        captured["kwargs"] = kwargs
        return _Response()

    monkeypatch.delenv("GUNI_LLM_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("GUNI_LLM_CA_BUNDLE", raising=False)
    monkeypatch.delenv("GUNI_LLM_TLS_VERIFY", raising=False)
    monkeypatch.setattr(llm_analyzer.urllib.request, "urlopen", fake_urlopen)

    assert llm_analyzer._post_json("https://example.com", {}, {}) == {"ok": True}
    assert captured["timeout"] == 60.0
    assert captured["kwargs"] == {}


def test_llm_request_timeout_can_be_configured(monkeypatch):
    monkeypatch.setenv("GUNI_LLM_TIMEOUT_SECONDS", "120")

    assert llm_analyzer._llm_timeout_seconds() == 120.0


def test_llm_request_can_disable_tls_verification(monkeypatch):
    captured = {}

    def fake_urlopen(request, **kwargs):
        captured.update(kwargs)
        return _Response()

    monkeypatch.setenv("GUNI_LLM_TLS_VERIFY", "false")
    monkeypatch.delenv("GUNI_LLM_CA_BUNDLE", raising=False)
    monkeypatch.setattr(llm_analyzer.urllib.request, "urlopen", fake_urlopen)

    assert llm_analyzer._post_json("https://example.com", {}, {}) == {"ok": True}
    assert captured["context"].check_hostname is False
