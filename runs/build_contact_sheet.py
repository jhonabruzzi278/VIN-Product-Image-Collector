import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    source = Path(sys.argv[1])
    category = sys.argv[2].casefold()
    output = Path(sys.argv[3])
    offset = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 20

    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    rows = payload.get("products", payload) if isinstance(payload, dict) else payload
    if category == "all":
        pass
    elif rows and "categoria" in rows[0]:
        rows = [row for row in rows if category in row["categoria"].casefold()]
    else:
        rows = [row for row in rows if category in row.get("decision", "").casefold()]
    rows = rows[offset : offset + limit]
    cell_w, cell_h, cols = 360, 360, 4
    rows_n = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGB", (cell_w * cols, cell_h * rows_n), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=15)

    for index, row in enumerate(rows):
        x = (index % cols) * cell_w
        y = (index // cols) * cell_h
        image_path = Path(row.get("local_path") or row["candidate"])
        if image_path.exists():
            image = Image.open(image_path).convert("RGB")
            image.thumbnail((cell_w - 20, cell_h - 88))
            sheet.paste(image, (x + (cell_w - image.width) // 2, y + 58))
        else:
            draw.text((x + 8, y + 72), "ARCHIVO NO DISPONIBLE", fill="red", font=font)
        name = row.get("nombre_original") or row.get("name", "")
        label = f'{offset + index + 1}. {row["sku"]}\n{name[:42]}'
        draw.multiline_text((x + 8, y + 6), label, fill="black", font=font, spacing=4)

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=90)


if __name__ == "__main__":
    main()
