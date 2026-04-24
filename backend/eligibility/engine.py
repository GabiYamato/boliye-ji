from __future__ import annotations

from eligibility.models import EligibilityResult, SchemeCandidate, UserProfile
from eligibility.tree_rag import SchemeLeaf, tree_top_down_retrieve


def _norm(s: str) -> str:
    return s.strip().lower()


def _match_location(profile_location: str, allowed: list[str]) -> bool:
    p = _norm(profile_location)
    allowed_norm = {_norm(x) for x in allowed}
    if "india" in allowed_norm and "india" in p:
        return True
    return any(a in p for a in allowed_norm)


def _match_category(profile_category: str, allowed: list[str]) -> bool:
    p = _norm(profile_category)
    allowed_norm = {_norm(x) for x in allowed}
    return p in allowed_norm or any(a in p for a in allowed_norm)


def _rule_score(profile: UserProfile, leaf: SchemeLeaf) -> tuple[float, list[str]]:
    attrs = leaf.attributes or {}
    reasons: list[str] = []
    score = 0.0

    age = profile.age
    if age is not None:
        min_age = attrs.get("min_age")
        max_age = attrs.get("max_age")
        if min_age is not None and age < int(min_age):
            return 0.0, [f"Age is below minimum required age of {min_age}."]
        if max_age is not None and age > int(max_age):
            return 0.0, [f"Age is above maximum allowed age of {max_age}."]
        score += 0.25
        reasons.append("Age requirement is satisfied.")

    income = profile.income
    if income is not None:
        max_income = attrs.get("max_income")
        if max_income is not None and income > int(max_income):
            return 0.0, [f"Income exceeds limit of {max_income} rupees."]
        score += 0.30
        reasons.append("Income requirement is satisfied.")

    allowed_locations = attrs.get("location") or []
    if allowed_locations:
        if not _match_location(profile.location, allowed_locations):
            return 0.0, ["Location does not match this scheme."]
        score += 0.2
        reasons.append("Location requirement is satisfied.")

    allowed_categories = attrs.get("category") or []
    if allowed_categories:
        if not _match_category(profile.category, allowed_categories):
            return 0.0, ["Category requirement does not match this scheme."]
        score += 0.25
        reasons.append("Category requirement is satisfied.")

    return min(score, 1.0), reasons


def evaluate_eligibility(profile: UserProfile, cleaned_query: str, top_k: int = 5) -> EligibilityResult:
    retrieved = tree_top_down_retrieve(
        cleaned_query,
        k=max(8, top_k),
        profile=profile.model_dump(),
    )

    candidates: list[SchemeCandidate] = []
    for idx, leaf in enumerate(retrieved):
        rule_score, reasons = _rule_score(profile, leaf)
        if rule_score <= 0:
            continue
        semantic_score = max(0.0, 1.0 - (idx * 0.12))
        final_score = 0.65 * rule_score + 0.35 * semantic_score
        candidates.append(
            SchemeCandidate(
                id=leaf.id,
                name=leaf.name,
                description=leaf.description,
                category_path=leaf.category_path,
                rule_match_score=round(rule_score, 4),
                semantic_relevance_score=round(semantic_score, 4),
                final_score=round(final_score, 4),
                reasons=reasons,
                next_steps=list((leaf.attributes or {}).get("next_steps") or []),
            )
        )

    candidates.sort(key=lambda x: x.final_score, reverse=True)
    winners = candidates[:top_k]
    return EligibilityResult(
        eligible_schemes=winners,
        scores=[c.final_score for c in winners],
    )
