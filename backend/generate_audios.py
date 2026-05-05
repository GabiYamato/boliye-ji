import asyncio
import base64
from pathlib import Path
from voice.tts import synthesize_wav

FILLERS_DIR = Path("assets/fillers")
FILLERS_DIR.mkdir(parents=True, exist_ok=True)

async def main():
    # 1. Holding line
    text_hold = "Please hold on for one moment, I'll browse through the available schemes."
    print("Generating holding line...")
    audio_hold = synthesize_wav(text_hold)
    (FILLERS_DIR / "hold_on.wav").write_bytes(audio_hold)
    
    # 2. What can you do
    text_intro = "I am an AI assistant designed to help you discover and apply for government welfare schemes. I can check your eligibility based on your profile, explain scheme details, and guide you through the application process."
    print("Generating intro line...")
    audio_intro = synthesize_wav(text_intro)
    (FILLERS_DIR / "what_can_i_do.wav").write_bytes(audio_intro)
    
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
