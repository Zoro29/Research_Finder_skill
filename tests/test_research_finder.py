import json
import unittest
from research_finder.query import parse_query, QueryParseError
from research_finder.openalex import OpenAlexClient, OpenAlexError

class Response:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return json.dumps(self.payload).encode()

class Tests(unittest.TestCase):
    def test_required_grammar(self):
        q = parse_query("RESEARCH - XD Robotics X Machine Learning XP Jane Doe XU MIT XY 2020-2023 XT Article")
        self.assertEqual(q.domains, ("Robotics", "Machine Learning"))
        self.assertEqual(q.professors, ("Jane Doe",))
        self.assertEqual(q.universities, ("MIT",))
        self.assertEqual(q.year_range, (2020, 2023))
        self.assertEqual(q.paper_types, ("article",))
        self.assertIn("RESEARCH -", q.original_query)

    def test_required_query_variants_and_case(self):
        for raw in (
            "RESEARCH - XD Robotics",
            "RESEARCH - XD Robotics X Machine Learning",
            "RESEARCH - XP Professor Name",
            "RESEARCH - XD Robotics XP Professor Name",
            "RESEARCH - XD Robotics XP Professor Name XU Tsinghua University",
            "RESEARCH - XD Robotics XT Survey",
            "RESEARCH - XD Robotics XY 2025",
            "research - xd robotics xu Tsinghua University xy 2024-2026",
        ):
            self.assertIsNotNone(parse_query(raw))
        self.assertEqual(parse_query("RESEARCH - XD Xylophone").domains, ("Xylophone",))

    def test_validation(self):
        for query in ("RESEARCH - XD", "RESEARCH - XT unicorn", "RESEARCH - XY 2023-2020",
                      "RESEARCH - XD Robotics X", "RESEARCH - XD Robotics XP"):
            with self.assertRaises(QueryParseError): parse_query(query)
        with self.assertRaises(QueryParseError): parse_query("RESEARCH - X biology")
        with self.assertRaises(QueryParseError): parse_query("RESEARCH - XD Robotics XP A XP B")

    def test_combined_local_filtering_and_dedup(self):
        item = {"id":"W1","title":"Machine Learning","type":"article",
                "authorships":[{"author":{"display_name":"Jane Doe"},
                "institutions":[{"display_name":"MIT"}]}],
                "publication_year":2022,"cited_by_count":100,"doi":"doi:X",
                "open_access":{"is_oa":True}}
        client = OpenAlexClient(opener=lambda *a, **k: Response({"results":[item, item]}))
        out = client.search(parse_query("RESEARCH - XD: machine - XP: Jane Doe - XU: MIT - XY: 2020-2023 - XT: article"))
        self.assertEqual(len(out), 1)

    def test_errors_are_explicit(self):
        with self.assertRaises(OpenAlexError):
            OpenAlexClient(opener=lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))).fetch(
                parse_query("RESEARCH - XD: biology"))

if __name__ == "__main__": unittest.main()
