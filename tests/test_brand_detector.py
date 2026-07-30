from vin_collector.brand_detector import BrandDetector


def test_detects_known_brand_by_substring(tmp_path):
    brands_path = tmp_path / "marcas.json"
    brands_path.write_text('{"VERTIMEC": "SYNGENTA"}', encoding="utf-8")
    detector = BrandDetector(brands_path=brands_path)

    brand, manufacturer = detector.detect("VERTIMEC 1.8 EC 1 LT")

    assert brand == "VERTIMEC"
    assert manufacturer == "SYNGENTA"


def test_returns_none_for_unknown_brand(tmp_path):
    brands_path = tmp_path / "marcas.json"
    brands_path.write_text('{"VERTIMEC": "SYNGENTA"}', encoding="utf-8")
    detector = BrandDetector(brands_path=brands_path)

    brand, manufacturer = detector.detect("PRODUCTO TOTALMENTE DESCONOCIDO XYZ")

    assert brand is None
    assert manufacturer is None
