"""Generates an MP3 for every Arabic text in tts/texts.json using Microsoft neural Levantine voices (edge-tts).
Runs on GitHub Actions; existing files are skipped. Writes audio/manifest.json with the available keys."""
import asyncio, json, os, sys
import edge_tts

VOICE = os.environ.get("TTS_VOICE", "ar-JO-SanaNeural")
RATE = os.environ.get("TTS_RATE", "-10%")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
items = json.load(open(os.path.join(ROOT, "tts", "texts.json"), encoding="utf-8"))
outdir = os.path.join(ROOT, "audio")
os.makedirs(outdir, exist_ok=True)

async def one(it, sem):
    path = os.path.join(outdir, it["k"] + ".mp3")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return True
    async with sem:
        for attempt in range(3):
            try:
                await edge_tts.Communicate(it["t"], VOICE, rate=RATE).save(path)
                return True
            except Exception as e:
                print("retry", it["k"], e, file=sys.stderr)
                await asyncio.sleep(2 + attempt * 3)
    return False

async def main():
    sem = asyncio.Semaphore(4)
    res = await asyncio.gather(*(one(it, sem) for it in items))
    keys = sorted(it["k"] for it, ok in zip(items, res) if ok)
    json.dump({"voice": VOICE, "keys": keys}, open(os.path.join(outdir, "manifest.json"), "w"))
    print(f"{len(keys)}/{len(items)} audio files ready")

asyncio.run(main())
