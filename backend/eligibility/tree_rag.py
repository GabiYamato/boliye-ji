from __future__ import annotations

import hashlib
import importlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import config


@dataclass
class TreeNode:
    id: str
    name: str
    description: str
    attributes: dict[str, Any]
    children: list["TreeNode"]


@dataclass
class SchemeLeaf:
    id: str
    name: str
    description: str
    attributes: dict[str, Any]
    category_path: list[str]


_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "schemes_tree.json"
_vector_collection = None
_leaf_cache: list[SchemeLeaf] | None = None


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _term_overlap_score(query: str, text: str) -> float:
    q_tokens = set(_tokenize(query))
    t_tokens = set(_tokenize(text))
    if not q_tokens or not t_tokens:
        return 0.0
    return len(q_tokens.intersection(t_tokens)) / max(1, len(q_tokens))


def _hash_embedding(text: str, dim: int = 256) -> list[float]:
    vec = [0.0] * dim
    for token in _tokenize(text):
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _parse_node(raw: dict[str, Any]) -> TreeNode:
    return TreeNode(
        id=str(raw.get("id", "")),
        name=str(raw.get("name", "")),
        description=str(raw.get("description", "")),
        attributes=raw.get("attributes", {}) or {},
        children=[_parse_node(c) for c in (raw.get("children") or [])],
    )


def load_tree_root() -> TreeNode:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return _parse_node(payload["root"])


def _collect_leaves(node: TreeNode, path: list[str], out: list[SchemeLeaf]) -> None:
    next_path = path + [node.name]
    if not node.children and node.attributes:
        out.append(
            SchemeLeaf(
                id=node.id,
                name=node.name,
                description=node.description,
                attributes=node.attributes,
                category_path=next_path,
            )
        )
        return
    for child in node.children:
        _collect_leaves(child, next_path, out)


def get_scheme_leaves() -> list[SchemeLeaf]:
    global _leaf_cache
    if _leaf_cache is not None:
        return _leaf_cache
    root = load_tree_root()
    leaves: list[SchemeLeaf] = []
    _collect_leaves(root, [], leaves)
    _leaf_cache = leaves
    return leaves


def _ensure_chroma() -> None:
    global _vector_collection
    if _vector_collection is not None:
        return
    try:
        chromadb = importlib.import_module("chromadb")

        persist_dir = config.CHROMA_PERSIST_DIR
        client = chromadb.PersistentClient(path=persist_dir)
        _vector_collection = client.get_or_create_collection(name="boliye_tree_rag")

        leaves = get_scheme_leaves()
        docs = [
            f"{leaf.name}. {leaf.description}. Categories: {' > '.join(leaf.category_path)}"
            for leaf in leaves
        ]
        ids = [leaf.id for leaf in leaves]
        embeddings = [_hash_embedding(d) for d in docs]

        existing = _vector_collection.get(include=[])
        if not existing.get("ids"):
            _vector_collection.add(ids=ids, documents=docs, embeddings=embeddings)
    except Exception:
        _vector_collection = None


def bootstrap_tree_rag() -> None:
    # Warm caches and vector store at startup.
    get_scheme_leaves()
    _ensure_chroma()


def _profile_leaf_match(leaf: SchemeLeaf, profile: dict[str, Any]) -> bool:
    attrs = leaf.attributes or {}

    age = profile.get("age")
    min_age = attrs.get("min_age")
    max_age = attrs.get("max_age")
    if isinstance(age, int):
        if isinstance(min_age, int) and age < min_age:
            return False
        if isinstance(max_age, int) and age > max_age:
            return False

    income = profile.get("income")
    max_income = attrs.get("max_income")
    if isinstance(income, int) and isinstance(max_income, int) and income > max_income:
        return False

    location = str(profile.get("location") or "").strip().lower()
    allowed_locations = [str(x).strip().lower() for x in (attrs.get("location") or [])]
    if allowed_locations and location:
        if not any(loc in location or location in loc for loc in allowed_locations):
            return False

    category = str(profile.get("category") or "").strip().lower()
    allowed_categories = [str(x).strip().lower() for x in (attrs.get("category") or [])]
    if allowed_categories and category:
        if not any(cat == category or cat in category or category in cat for cat in allowed_categories):
            return False

    return True


def _node_relevance(query: str, node: TreeNode) -> float:
    text = f"{node.name}. {node.description}"
    return 0.7 * _cosine(_hash_embedding(query), _hash_embedding(text)) + 0.3 * _term_overlap_score(query, text)


def _collect_node_leaves(node: TreeNode, path: list[str], out: list[SchemeLeaf]) -> None:
    _collect_leaves(node, path, out)


def tree_top_down_retrieve(query: str, k: int = 4, profile: dict[str, Any] | None = None) -> list[SchemeLeaf]:
    root = load_tree_root()
    all_leaves = get_scheme_leaves()
    if not all_leaves:
        return []

    # Top-down traversal: choose best categories, then best subcategories.
    category_scores = sorted(
        ((_node_relevance(query, node), node) for node in root.children),
        key=lambda x: x[0],
        reverse=True,
    )
    top_categories = [n for _, n in category_scores[: max(1, min(3, len(category_scores)))]]

    candidate_leaves: list[SchemeLeaf] = []
    for cat in top_categories:
        sub_nodes = cat.children or []
        if not sub_nodes:
            _collect_node_leaves(cat, [root.name], candidate_leaves)
            continue

        sub_scores = sorted(
            ((_node_relevance(query, sub), sub) for sub in sub_nodes),
            key=lambda x: x[0],
            reverse=True,
        )
        top_subs = [n for _, n in sub_scores[: max(1, min(2, len(sub_scores)))]]
        for sub in top_subs:
            _collect_node_leaves(sub, [root.name, cat.name], candidate_leaves)

    if not candidate_leaves:
        candidate_leaves = list(all_leaves)

    # Hybrid retrieval: optional rule-based hard filter before semantic ranking.
    if profile:
        filtered = [leaf for leaf in candidate_leaves if _profile_leaf_match(leaf, profile)]
        if filtered:
            candidate_leaves = filtered

    q_vec = _hash_embedding(query)
    scored: list[tuple[float, SchemeLeaf]] = []
    for leaf in candidate_leaves:
        txt = f"{' '.join(leaf.category_path)} {leaf.name} {leaf.description}"
        score = 0.8 * _cosine(q_vec, _hash_embedding(txt)) + 0.2 * _term_overlap_score(query, txt)
        scored.append((score, leaf))
    scored.sort(key=lambda x: x[0], reverse=True)

    winners = [leaf for _, leaf in scored[:k]]
    if winners:
        return winners

    # Final fallback to all leaves to avoid empty retrieval.
    fallback_scored: list[tuple[float, SchemeLeaf]] = []
    for leaf in all_leaves:
        txt = f"{' '.join(leaf.category_path)} {leaf.name} {leaf.description}"
        score = _cosine(q_vec, _hash_embedding(txt))
        fallback_scored.append((score, leaf))
    fallback_scored.sort(key=lambda x: x[0], reverse=True)
    return [leaf for _, leaf in fallback_scored[:k]]
