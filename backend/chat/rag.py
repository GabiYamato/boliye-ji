import config
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

_client: QdrantClient | None = None
_vstore: QdrantVectorStore | None = None
_llm: ChatOllama | None = None
_rag_ok = False


def init_qdrant_collection() -> None:
    global _client, _rag_ok
    try:
        _client = QdrantClient(url=config.QDRANT_URL)
        _client.get_collections()
        if not _client.collection_exists(config.QDRANT_COLLECTION):
            _client.create_collection(
                collection_name=config.QDRANT_COLLECTION,
                vectors_config=qmodels.VectorParams(
                    size=config.QDRANT_EMBED_DIM,
                    distance=qmodels.Distance.COSINE,
                ),
            )
        _rag_ok = True
    except Exception:
        _client = None
        _rag_ok = False


def get_vectorstore() -> QdrantVectorStore | None:
    global _vstore, _client
    if not _rag_ok or _client is None:
        return None
    if _vstore is None:
        emb = OllamaEmbeddings(
            model=config.OLLAMA_EMBED_MODEL,
            base_url=config.OLLAMA_BASE_URL,
        )
        _vstore = QdrantVectorStore(
            client=_client,
            collection_name=config.QDRANT_COLLECTION,
            embedding=emb,
        )
    return _vstore


def _get_llm() -> ChatOllama:
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model=config.OLLAMA_LLM_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=0.3,
        )
    return _llm


def _last_user_text(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return str(m.get("content", ""))
    return ""


def _to_lc(messages: list[dict]):
    out = []
    for m in messages:
        r = m.get("role")
        c = str(m.get("content", ""))
        if r == "system":
            out.append(SystemMessage(content=c))
        elif r == "user":
            out.append(HumanMessage(content=c))
        elif r == "assistant":
            out.append(AIMessage(content=c))
    return out


def chat_reply(messages: list[dict]) -> str:
    query = _last_user_text(messages)
    ctx = ""
    if query:
        try:
            vs = get_vectorstore()
            if vs:
                retriever = vs.as_retriever(search_kwargs={"k": 4})
                docs = retriever.invoke(query)
                ctx = "\n\n".join(d.page_content for d in docs)
        except Exception:
            ctx = ""
    system = (
        "You are a helpful assistant. Use the context when relevant; "
        "if empty, use general knowledge.\n\nContext:\n"
        + (ctx or "(none)")
    )
    msgs = [{"role": "system", "content": system}]
    for m in messages:
        if m.get("role") in ("user", "assistant") and m.get("content") is not None:
            msgs.append({"role": m["role"], "content": str(m["content"])})
    lc = _to_lc(msgs)
    out = _get_llm().invoke(lc)
    return str(out.content or "")
