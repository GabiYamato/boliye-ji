from __future__ import annotations

import re

from eligibility.models import UserProfile


def infer_profile_from_query(text: str) -> UserProfile:
    t = text.lower()

    age: int | None = None
    income: int | None = None

    age_match = re.search(r"\b(?:age\s*(?:is|:)?\s*)?(\d{2})\s*(?:years?|yrs?)?\b", t)
    if age_match:
        age = int(age_match.group(1))

    income_match = re.search(r"\b(?:income|salary|annual)\s*(?:is|:)?\s*(\d{5,7})\b", t)
    if income_match:
        income = int(income_match.group(1))

    location = "india"
    if "rural" in t or "village" in t:
        location = "rural india"

    category = "general"
    for c in ("student", "worker", "entrepreneur", "household", "female-student", "rural"):
        if c in t:
            category = c
            break

    return UserProfile(age=age, income=income, location=location, category=category)
