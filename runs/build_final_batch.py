import json
from pathlib import Path

ROOT = Path(r"C:\Trabajos\agrofarias\agrofarias-astro")
PHOTOS = ROOT / "material-productos" / "03-APROBADOS" / "fotos"
SNAPSHOT = ROOT / "material-productos" / "05-EXPORTACIONES" / "woocommerce-catalog-snapshot.json"
OUTPUT = ROOT / "material-productos" / "05-EXPORTACIONES" / "lote-imagenes-completo.json"

products = json.loads(SNAPSHOT.read_text(encoding="utf-8-sig"))["products"]
files = [path for path in PHOTOS.iterdir() if path.is_file() and not path.name.startswith("PLACEHOLDER_")]
rows = []
missing = []
for product in products:
    if product.get("images"):
        continue
    prefix = product["sku"].upper() + "_"
    choices = [path for path in files if path.name.upper().startswith(prefix)]
    if not choices:
        missing.append(product["sku"])
        continue
    # Prefer a real/approved image over the explicit temporary placeholder.
    choices.sort(key=lambda path: ("IMAGEN_EN_ACTUALIZACION" in path.name, path.name))
    path = choices[0]
    rows.append(
        {
            "id": product["id"],
            "sku": product["sku"],
            "name": product["name"],
            "image_path": str(path),
            "image_status": "temporary-placeholder" if "IMAGEN_EN_ACTUALIZACION" in path.name else "verified-or-approved",
        }
    )

payload = {
    "generated_at": "2026-08-12T23:30:00-04:00",
    "mode": "reviewed-not-applied",
    "summary": {
        "total_missing_in_snapshot": len(rows) + len(missing),
        "verified_or_approved": sum(x["image_status"] == "verified-or-approved" for x in rows),
        "temporary_placeholders": sum(x["image_status"] == "temporary-placeholder" for x in rows),
        "without_local_asset": len(missing),
    },
    "products": rows,
    "missing": missing,
}
OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(payload["summary"], ensure_ascii=False))
