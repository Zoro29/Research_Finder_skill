import os
import unittest
from unittest.mock import patch

from research_finder.config import Settings
from research_finder.ollama import OllamaAnalyzer, OllamaError

class ProviderConfigTests(unittest.TestCase):
    def test_search_safe_default_has_no_model_requirement(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(Settings.from_env().provider, "none")

    def test_ollama_requires_explicit_model(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            with self.assertRaises(ValueError):
                Settings.from_env()

    def test_analysis_modes_are_validated(self):
        with patch.dict(os.environ, {"RESEARCH_ANALYSIS_MODE": "local",
                                     "LLM_PROVIDER": "ollama",
                                     "OLLAMA_MODEL": "gemma4:e2b"}, clear=True):
            settings = Settings.from_env()
            self.assertEqual(settings.analysis_mode, "local")
        with patch.dict(os.environ, {"RESEARCH_ANALYSIS_MODE": "online"}, clear=True):
            settings = Settings.from_env()
            self.assertEqual(settings.analysis_mode, "online")
        with patch.dict(os.environ, {"RESEARCH_ANALYSIS_MODE": "remote"}, clear=True):
            with self.assertRaises(ValueError):
                Settings.from_env()

    def test_ollama_uses_configured_tag(self):
        seen = {}
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'{"response":"ok"}'
        def opener(request, timeout):
            import json
            seen.update(json.loads(request.data))
            return Response()
        result = OllamaAnalyzer("gemma4:e2b", opener=opener).generate("hello")
        self.assertEqual(result, "ok")
        self.assertEqual(seen["model"], "gemma4:e2b")

if __name__ == "__main__":
    unittest.main()
