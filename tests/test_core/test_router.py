from core.router import route


def test_router_returns_gemma4_and_detects_domains():
    result = route("Analyse ce fichier xlsx puis génère un rapport docx")
    assert result.model == "gemma4:e2b"
    assert result.score > 0
    assert "data" in result.domains or "office" in result.domains
