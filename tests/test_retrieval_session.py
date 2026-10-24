import io
import tempfile
import unittest
from unittest.mock import patch

from research_finder.document_chunks import chunk_document
from research_finder.interactive_session import ResearchSession
from research_finder.models import Paper, SearchResult
from research_finder.paper_retrieval import PaperRetriever, RetrievedPaper

class RecordingAnalyzer:
    def __init__(self):
        self.calls = []
    def analyze(self, papers, question, evidence_text=None):
        self.calls.append((papers, question, evidence_text))
        from research_finder.analysis import Analysis
        return Analysis("grounded answer", tuple(p.title for p in papers))

class Response:
    def __init__(self, data, content_type="text/html"):
        self.data, self.headers = data, {"Content-Type": content_type}
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return self.data

class RetrievalSessionTests(unittest.TestCase):
    def _session(self, commands, output, results=None, analyzer=None):
        results = results or tuple(
            SearchResult(Paper(id=f"W{i}", title=f"Paper {i}", abstract=f"Evidence {i}"), 1.0)
            for i in range(1, 4)
        )
        command_iter = iter(commands)
        return ResearchSession(
            results,
            PaperRetriever(
                tempfile.mkdtemp(),
                opener=lambda *a, **k: (_ for _ in ()).throw(OSError("offline")),
            ),
            "local" if analyzer else "online",
            analyzer=analyzer,
            input_fn=lambda _: next(command_iter),
            output_fn=lambda text: output.write(str(text) + "\n"),
        )

    def test_select_paper_two_then_follow_up_uses_paper_two(self):
        output = io.StringIO()
        session = self._session(["2", "summary", "what evidence is available?", "quit"], output)
        session.run()
        self.assertEqual(session.selected, 1)
        self.assertEqual(session.document(1).paper.id, "W2")
        text = output.getvalue()
        self.assertIn("Selected paper 2: Paper 2", text)
        self.assertIn("Evidence 2", text)
        self.assertNotIn("Evidence 1", text)

    def test_switch_without_number_returns_to_list_and_replaces_context(self):
        output = io.StringIO()
        session = self._session(["2", "switch", "3", "what is this paper about?", "quit"], output)
        session.run()
        self.assertEqual(session.selected, 2)
        text = output.getvalue()
        self.assertIn("Available papers:", text)
        self.assertIn("Selected paper 3: Paper 3", text)
        self.assertIn("Evidence 3", text)

    def test_numeric_selection_uses_exact_paper_and_content(self):
        papers = tuple(
            SearchResult(Paper(id=f"W{i}", title=f"Paper {i}", abstract=f"Evidence {i}"), 1.0)
            for i in range(1, 4)
        )
        output = io.StringIO()
        commands = iter(["3", "summary", "quit"])
        session = ResearchSession(
            papers,
            PaperRetriever(tempfile.mkdtemp(), opener=lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))),
            "online", input_fn=lambda _: next(commands),
            output_fn=lambda text: output.write(str(text) + "\n"),
        )
        session.run()
        self.assertEqual(session.selected, 2)
        self.assertEqual(session.document(2).paper.id, "W3")
        self.assertIn("Paper 3", output.getvalue())
        self.assertIn("Evidence 3", output.getvalue())
        self.assertNotIn("Evidence 1", output.getvalue())

    def test_switch_replaces_active_evidence_and_context(self):
        papers = tuple(
            SearchResult(Paper(id=f"W{i}", title=f"Paper {i}", abstract=f"Evidence {i}"), 1.0)
            for i in range(1, 4)
        )
        output = io.StringIO()
        commands = iter(["1", "summary", "switch 3", "summary", "quit"])
        session = ResearchSession(
            papers,
            PaperRetriever(tempfile.mkdtemp(), opener=lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))),
            "online", input_fn=lambda _: next(commands),
            output_fn=lambda text: output.write(str(text) + "\n"),
        )
        session.run()
        self.assertEqual(session.selected, 2)
        self.assertEqual(len(session.history), 1)
        switched_output = output.getvalue().split("Selected paper 3:", 1)[1]
        self.assertIn("Evidence 3", switched_output)
        self.assertNotIn("Evidence 1", switched_output)

    def test_local_answer_receives_only_active_paper_context(self):
        analyzer = RecordingAnalyzer()
        output = io.StringIO()
        session = self._session(["3", "what is the method?", "quit"], output, analyzer=analyzer)
        session.run()
        self.assertEqual(len(analyzer.calls), 1)
        papers, _, evidence = analyzer.calls[0]
        self.assertEqual([paper.id for paper in papers], ["W3"])
        self.assertIn("Active paper: Paper 3", evidence)
        self.assertIn("Evidence 3", evidence)
        self.assertNotIn("Evidence 1", evidence)

    def test_html_retrieval_and_abstract_fallback(self):
        paper = Paper(id="W1", title="Study", url="https://example.org/paper")
        with tempfile.TemporaryDirectory() as cache:
            result = PaperRetriever(cache, opener=lambda *a, **k: Response(b"<h1>Methods</h1><p>Evidence.</p>")).retrieve(paper)
            self.assertTrue(result.full_text_available)
            self.assertIn("Evidence", result.text)
        unavailable = PaperRetriever(tempfile.mkdtemp(), opener=lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))).retrieve(
            Paper(id="W2", title="Abstract study", abstract="Abstract evidence"))
        self.assertEqual(unavailable.status, "abstract-only")
        self.assertEqual(unavailable.text, "Abstract evidence")
        no_evidence = PaperRetriever(tempfile.mkdtemp(), opener=lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))).retrieve(
            Paper(id="W3", title="No evidence"))
        self.assertEqual(no_evidence.status, "unavailable")

    def test_long_documents_are_overlapping(self):
        paper = Paper(id="W1", title="Study")
        document = RetrievedPaper(paper, None, "abc " * 5000, "full-text", "test")
        chunks = chunk_document(document, size=100, overlap=20)
        self.assertGreater(len(chunks), 2)
        self.assertTrue(set(chunks[0].text[-20:]) & set(chunks[1].text[:20]))

    def test_session_keeps_question_context(self):
        paper = Paper(id="W1", title="Study", abstract="Evidence")
        result = SearchResult(paper, 1.0)
        output = io.StringIO()
        with patch("builtins.input", side_effect=["1", "summary", "quit"]):
            commands = iter(["1", "summary", "quit"])
            session = ResearchSession((result,), PaperRetriever(tempfile.mkdtemp(), opener=lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))), "online", input_fn=lambda _: next(commands), output_fn=lambda text: output.write(str(text) + "\n"))
            session.run()
        self.assertEqual(len(session.history), 1)
        self.assertIn("Evidence", output.getvalue())

if __name__ == "__main__":
    unittest.main()
