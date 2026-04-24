import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from eligibility.models import UserProfile
from eligibility.service import run_eligibility_pipeline


if __name__ == "__main__":
    sample_query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "I am a 22 year old student from India with income three lakh. Which schemes can I apply for?"
    )
    profile = UserProfile(
        age=int(sys.argv[2]) if len(sys.argv) > 2 else 22,
        income=int(sys.argv[3]) if len(sys.argv) > 3 else 300000,
        location=sys.argv[4] if len(sys.argv) > 4 else "India",
        category=sys.argv[5] if len(sys.argv) > 5 else "student",
    )
    out = run_eligibility_pipeline(raw_text=sample_query, profile=profile, confidence=0.95)

    print("--- Structured ---")
    print(f"raw: {out.raw_transcript}")
    print(f"cleaned: {out.cleaned_query}")
    print(f"confidence: {out.confidence:.2f}")
    print("\n--- Eligible schemes ---")
    if not out.eligibility.eligible_schemes:
        print("No eligible schemes found.")
    for s in out.eligibility.eligible_schemes:
        print(f"- {s.name} (score={s.final_score})")
        for reason in s.reasons:
            print(f"  reason: {reason}")
        for idx, step in enumerate(s.next_steps[:3], start=1):
            print(f"  next step {idx}: {step}")
    print("\n--- Retrieved context ---")
    for node in out.retrieved_context:
        print(f"- {node.name} :: {' > '.join(node.category_path)}")
    print("\n--- TTS text ---")
    print(out.tts_text)
