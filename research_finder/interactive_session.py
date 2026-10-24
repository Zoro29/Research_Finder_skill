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
        self.selected: int | None = None
        self.documents: dict[str, RetrievedPaper] = {}
        self.history: list[tuple[str, str]] = []

    def document(self, index: int) -> RetrievedPaper:
        paper = self.results[index].paper
        return self.documents.setdefault(paper.id, self.retriever.retrieve(paper))

    def run(self) -> None:
        self.output("paper> Select a paper number, or type switch, help, back, or quit.")
        while True:
            try: command = self.input("paper> ").strip()
            except EOFError: return
            if not command: continue
            lower = command.casefold()
            if lower in {"quit", "q", "exit"}: return
            if lower == "back":
                self.output("Returning to the search results.")
                return
            if lower == "switch":
                self._choose_paper()
                continue
            if lower == "help":
                self.output("Commands: summary, paper, section, compare N, switch N, back, quit; natural-language questions are supported.")
                continue
            if lower.isdigit():
                self._switch(command)
                continue
            if lower == "paper":
                if self.selected is None:
                    self.output("Select a paper first.")
                else:
                    self.output(self.results[self.selected].paper)
                continue
            if lower == "section":
                if self.selected is None:
                    self.output("Select a paper first.")
                    continue
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

    def _choose_paper(self):
        self.output("Available papers:")
        for number, result in enumerate(self.results, 1):
            self.output(f"[{number}] {result.paper.title}")
        try:
            value = self.input("Select a paper number (or back): ").strip()
        except EOFError:
            return
        if value.casefold() in {"back", "q", "quit"}:
            return
        self._switch(value)

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
            if self.selected is None:
                raise ValueError
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
            "method": "Explain the methodology, setup, datasets, baselines, and metrics. Say when unavailable.",
            "methodology": "Explain the methodology, setup, datasets, baselines, and metrics. Say when unavailable.",
            "findings": "Summarize only the findings actually supported by the evidence, including numbers only when present.",
            "limitations": "List author-stated limitations separately from limitations inferred from the available evidence.",
        }
        question = commands.get(question.casefold(), question)
        if self.selected is None:
            self.output("Select a paper first.")
            return
        doc = self.document(self.selected)
        documents = documents or (doc,)
        if doc.status != "full-text":
            available = "abstract and metadata" if doc.status == "abstract-only" else "metadata only"
            self.output(f"Full text unavailable. Available evidence: {available}. "
                        "Analysis is limited to the available material.")
        context = "\n\n".join(
            f"[Active paper: {item.paper.title}; OpenAlex ID: {item.paper.id}; "
            f"DOI: {item.paper.doi or 'unavailable'}; status={item.status}; "
            f"source={item.source_url or 'metadata'}]\n"
            + "\n".join(
                f"[section={chunk.section or 'unidentified'}] {chunk.text}"
                for chunk in relevant_chunks(item, question)
            )
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
