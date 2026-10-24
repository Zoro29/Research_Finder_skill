import io
import os
import unittest
from unittest.mock import patch

from research_finder.cli import _interactive, main
from research_finder.models import Paper, SearchResult

class AnalysisModeTests(unittest.TestCase):
    def test_interactive_selection_displays_stable_identifier_and_evidence(self):
        paper = Paper(
            id="https://openalex.org/W1",
            title="Robotics Study",
            authors=("Researcher",),
            abstract="Accessible abstract.",
            publication_year=2025,
            url="https://doi.org/10/example",
        )
        output = io.StringIO()
        with patch("builtins.input", side_effect=["1", "q"]), patch("sys.stdout", output):
            _interactive([SearchResult(paper, 1.0, ("robotics",))])
        text = output.getvalue()
        self.assertIn("OpenAlex ID: https://openalex.org/W1", text)
        self.assertIn("Accessible abstract.", text)

    def test_online_analyze_does_not_invoke_ollama(self):
        paper = Paper(id="W1", title="Robotics Study", abstract="Evidence.")
        result = SearchResult(paper, 1.0)
        with patch.dict(os.environ, {"RESEARCH_ANALYSIS_MODE": "online"}, clear=True), \
             patch("research_finder.cli.OpenAlexClient") as client_class, \
             patch("research_finder.cli.OllamaAnalyzer") as ollama_class, \
             patch("sys.stdout", io.StringIO()):
            client_class.return_value.search.return_value = [result]
            self.assertEqual(main(["analyze", "RESEARCH - XD Robotics"]), 0)
            ollama_class.assert_not_called()

if __name__ == "__main__":
    unittest.main()
