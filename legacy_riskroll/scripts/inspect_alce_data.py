from pathlib import Path
import json


PROJECT = Path(__file__).resolve().parents[1]
ALCE_DIR = PROJECT / "external" / "ALCE"
DATA_DIR = ALCE_DIR / "data"

print("ALCE data dir:", DATA_DIR)
print("Exists:", DATA_DIR.exists())

files = sorted(DATA_DIR.rglob("*")) if DATA_DIR.exists() else []

print("\nFirst 100 files:")
for p in files[:100]:
    if p.is_file():
        print(p.relative_to(DATA_DIR), p.stat().st_size)

json_like = [
    p for p in files
    if p.is_file() and p.suffix.lower() in [".json", ".jsonl"]
]

print("\nJSON/JSONL files:")
for p in json_like[:80]:
    print(p.relative_to(DATA_DIR), p.stat().st_size)

print("\nSample records:")
for p in json_like[:20]:
    print("\n" + "=" * 100)
    print("FILE:", p.relative_to(DATA_DIR))
    try:
        if p.suffix.lower() == ".jsonl":
            line = p.read_text(encoding="utf-8").splitlines()[0]
            obj = json.loads(line)
        else:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(obj, list):
                obj = obj[0]
            elif isinstance(obj, dict):
                for key, val in obj.items():
                    if isinstance(val, list) and val:
                        obj = val[0]
                        break
        print("TYPE:", type(obj))
        if isinstance(obj, dict):
            print("KEYS:", list(obj.keys()))
            for k, v in list(obj.items())[:8]:
                s = str(v)
                if len(s) > 500:
                    s = s[:500] + "..."
                print(f"{k}: {s}")
    except Exception as e:
        print("Could not read sample:", repr(e))
