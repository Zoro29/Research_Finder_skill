"""Persistent paper exploration session for local analysis and host handoff."""
from __future__ import annotations
from collections.abc import Callable, Sequence
from .document_chunks import relevant_chunks
from .models import SearchResult
from .ollama import OllamaAnalyzer, OllamaError
from .paper_retrieval import PaperRetriever, RetrievedPaper

class ResearchSession:
    def __init__(self, results: Sequence[SearchResult], retriever: PaperRetriever,
                 mode: str = "online", analyzer: OllamaAnalyzer | None = None,
                 input_fn=input, output_fn=print):
        self.results = tuple(results)
        self.retriever, self.mode, self.analyzer = retriever, mode, analyzer
        self.input, self.output = input_fn, output_fn
        self.selected = 0
        self.documents: dict[str, RetrievedPaper] = {}
        self.history: list[tuple[str, str]] = []

    def document(self, index: int) -> RetrievedPaper:
        paper = self.results[index].paper
        return self.documents.setdefault(paper.id, self.retriever.retrieve(paper))

    def run(self) -> None:
        self.output("paper> Select a paper number, ask a question, or type help/back/quit.")
        while True:
            try: command = self.input("paper> ").strip()
            except EOFError: return
            if not command: continue
            lower = command.casefold()
            if lower in {"quit", "q", "exit"}: return
            if lower == "back":
                self.output("Returning to the search results.")
                return
            if lower == "help":
                self.output("Commands: summary, paper, section, compare N, switch N, back, quit; natural-language questions are supported.")
                continue
            if lower.isdigit():
                self._switch(command)
                continue
            if lower == "paper":
                self.output(self.results[self.selected].paper)
                continue
            if lower == "section":
                doc = self.document(self.selected)
                self.output("\n".join(h for h, _ in doc.sections) or "No section headings were extracted.")
                continue
            if lower.startswith("switch "):
                self._switch(command[7:])
                continue
            if lower.startswith("compare "):
                self._compare(command[8:])
                continue
            self._answer(command)

    def _switch(self, value):
        try:
            index = int(value) - 1
            if not 0 <= index < len(self.results): raise ValueError
            self.selected = index
            self.history.clear()
            self.output(f"Selected paper {index + 1}: {self.results[index].paper.title}")
            document = self.document(index)
            self.output(
                f"Evidence status: {document.status}; source: "
                f"{document.source_url or 'OpenAlex abstract/metadata'}"
            )
        except ValueError:
            self.output("Select a valid paper number.")

    def _compare(self, value):
        try:
            other = int(value) - 1
            if not 0 <= other < len(self.results): raise ValueError
            left, right = self.document(self.selected), self.document(other)
            self._answer(f"Compare paper {self.selected + 1} and paper {other + 1}, including objectives, methods, results, and limitations.",
                         documents=(left, right))
        except ValueError:
            self.output("Select a valid paper number.")

    def _answer(self, question, documents=None):
        commands = {
            "summary": "Provide a structured briefing: problem, motivation, contributions, method, findings, limitations, and future work.",
            "methodology": "Explain the methodology, setup, datasets, baselines, and metrics. Say when unavailable.",
            "findings": "Summarize only the findings actually supported by the evidence, including numbers only when present.",
            "limitations": "List author-stated limitations separately from limitations inferred from the available evidence.",
        }
        question = commands.get(question.casefold(), question)
        doc = self.document(self.selected)
        documents = documents or (doc,)
        if doc.status != "full-text":
            available = "abstract and metadata" if doc.status == "abstract-only" else "metadata only"
            self.output(f"Full text unavailable. Available evidence: {available}. "
                        "Analysis is limited to the available material.")
        context = "\n\n".join(
            f"[Paper {i + 1}; status={item.status}; source={item.source_url or 'metadata'}]\n"
            + "\n".join(chunk.text for chunk in relevant_chunks(item, question))
            for i, item in enumerate(documents)
        )
        if self.mode == "online":
            self.output("Online mode handoff: analyze the evidence below with the host agent; no Ollama call was made.")
            self.output(context[:12000])
            answer = "Host-agent analysis required."
        elif not self.analyzer:
            self.output("Local analysis unavailable: no Ollama analyzer is configured.")
            return
        else:
            try:
                answer = self.analyzer.analyze([item.paper for item in documents], question, context).summary
            except OllamaError as exc:
                self.output(f"Local analysis unavailable: {exc}")
                return
            self.output(answer)
        self.history.append((question, answer))
