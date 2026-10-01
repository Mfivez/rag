"""Cœur testable de l'assistant helpdesk, indépendant de Streamlit."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.tools import tool
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import InMemorySaver


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS_DIR = ROOT / "documents"
OUTPUTS_DIR = ROOT / "outputs"
SOURCE_PATTERN = re.compile(r"\[Source : ([^\]]+)\]")


def stable_chunk_id(chunk) -> str:
    raw = (
        f"{chunk.metadata.get('source', '')}|"
        f"{chunk.metadata.get('page', '')}|"
        f"{chunk.page_content}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_chunks():
    loaded = []
    for path in sorted(DOCUMENTS_DIR.glob("*.md")):
        if path.name == "README.md":
            continue
        docs = TextLoader(str(path), encoding="utf-8").load()
        for doc in docs:
            doc.metadata["source"] = path.name
        loaded.extend(docs)

    pdf_path = DOCUMENTS_DIR / "guide_escalade_p1.pdf"
    pdf_docs = PyPDFLoader(str(pdf_path)).load()
    for doc in pdf_docs:
        doc.metadata["source"] = pdf_path.name
    loaded.extend(pdf_docs)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=450,
        chunk_overlap=80,
        separators=["\n## ", "\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(loaded)


def build_store() -> Chroma:
    OUTPUTS_DIR.mkdir(exist_ok=True)
    embeddings = OllamaEmbeddings(model="bge-m3")
    store = Chroma(
        collection_name="helpdesk_app",
        embedding_function=embeddings,
        persist_directory=str(OUTPUTS_DIR / "chroma_app"),
    )
    if len(store.get()["ids"]) == 0:
        chunks = load_chunks()
        store.add_documents(chunks, ids=[stable_chunk_id(chunk) for chunk in chunks])
    return store


def build_agent():
    store = build_store()
    model = ChatOllama(model="qwen2.5:3b", temperature=0)

    @tool
    def chercher_procedure(question: str) -> str:
        """Recherche une information dans les procédures helpdesk et retourne les passages sourcés."""
        docs = store.similarity_search(question, k=3)
        return "\n\n".join(
            f"[Source : {doc.metadata.get('source')}]\n{doc.page_content}"
            for doc in docs
        )

    @tool
    def calculer_sla(priorite: str, utilisateurs_impactes: int) -> str:
        """Calcule le SLA d'un ticket avec sa priorité et le nombre d'utilisateurs impactés."""
        priorite = priorite.strip().upper()
        if utilisateurs_impactes < 0:
            return "Nombre d'utilisateurs invalide."
        if priorite == "CRITIQUE" or utilisateurs_impactes >= 250:
            return "SLA : 1 heure · escalade DSI requise"
        if priorite == "HAUTE":
            return "SLA : 4 heures"
        if priorite == "NORMALE":
            return "SLA : 1 jour ouvré"
        return "Priorité inconnue : validation humaine requise"

    return create_agent(
        model=model,
        tools=[chercher_procedure, calculer_sla],
        system_prompt=(
            "Tu es un assistant helpdesk interne. Utilise les tools pour les procédures "
            "et les SLA. N'invente ni fait, ni source, ni délai. Si les observations ne "
            "suffisent pas, dis-le clairement. Réponds en français et reste concis."
        ),
        checkpointer=InMemorySaver(),
    )


def ask_agent(agent, question: str, thread_id: str) -> dict:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 8,
        },
    )
    messages = result["messages"]
    last_human = max(
        index for index, message in enumerate(messages) if message.type == "human"
    )
    current_turn = messages[last_human:]

    tool_calls = []
    sources = set()
    for message in current_turn:
        for call in getattr(message, "tool_calls", []):
            tool_calls.append({"name": call["name"], "args": call["args"]})
        if message.type == "tool":
            sources.update(SOURCE_PATTERN.findall(str(message.content)))

    return {
        "answer": messages[-1].content,
        "sources": sorted(sources),
        "tool_calls": tool_calls,
    }


__all__ = ["ask_agent", "build_agent", "build_store", "load_chunks"]
