import json
import re
import unicodedata
from pathlib import Path

SNAPSHOT = Path(r"C:\Trabajos\agrofarias\agrofarias-astro\material-productos\05-EXPORTACIONES\woocommerce-catalog-snapshot.json")
AUDIT = Path(r"C:\Trabajos\VIN Product Image Collector\runs\auditoria-agrofarias.json")
APPROVED = Path(r"C:\Trabajos\agrofarias\agrofarias-astro\material-productos\03-APROBADOS\fotos")
OUTPUT = Path(r"C:\Trabajos\VIN Product Image Collector\runs\variant-mapping.json")


def plain(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def canonical(name: str, category: str) -> str:
    value = plain(name)
    category = plain(category)
    value = re.sub(r"\b(x|n|t|talla|tamano)\s*\d+(?:[.,]\d+)?\b", " ", value)
    value = re.sub(r"\b\d+(?:[.,]\d+)?\s*(ml|cc|lt|lts|l|kg|grs|gr|g|cm|mm|mts|mt|m|un|unid|unidades|pulg)\b", " ", value)
    if "seguridad" in category:
        value = re.sub(r"\b\d{2}\b", " ", value)
        value = re.sub(r"\b(xxl|xl|xxl|l|m|s|xs)\b", " ", value)
    elif "riego" in category:
        value = re.sub(r"\b\d+(?:[.,]\d+)?\b", " ", value)
        value = re.sub(r"\b(hi|he|pe|pvc|hdpe)\b", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8-sig"))["products"]
audit = json.loads(AUDIT.read_text(encoding="utf-8-sig"))
covered = set(audit["approved"] + audit.get("approved_local", []))
for batch in ("lote-vin-collector-01.json", "lote-vin-collector-02.json"):
    path = APPROVED.parent / batch
    if path.exists():
        covered.update(p["sku"] for p in json.loads(path.read_text(encoding="utf-8-sig"))["products"])

files = list(APPROVED.glob("*"))
file_by_sku = {sku: next((str(p) for p in files if p.name.upper().startswith(sku.upper() + "_")), "") for sku in covered}
groups: dict[tuple[str, str], dict[str, list[dict]]] = {}
for p in snapshot:
    if p.get("images"):
        continue
    category = p.get("categories", [{}])[0].get("name", "")
    key = (plain(category), canonical(p["name"], category))
    bucket = groups.setdefault(key, {"covered": [], "pending": []})
    item = {"sku": p["sku"], "name": p["name"], "file": file_by_sku.get(p["sku"], "")}
    bucket["covered" if p["sku"] in covered else "pending"].append(item)

rows = [
    {"category": key[0], "canonical": key[1], **value}
    for key, value in groups.items()
    if value["covered"] and value["pending"] and any(x["file"] for x in value["covered"])
]
OUTPUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"groups={len(rows)} pending={sum(len(row['pending']) for row in rows)}")
