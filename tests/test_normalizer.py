from vin_collector.normalizer import NameNormalizer


def test_unit_variants_converge_to_same_canonical_form(tmp_path):
    normalizer = NameNormalizer(dictionary_path=tmp_path / "dict.json")

    # Variantes que difieren solo en cómo se escribe la unidad (sin perder información,
    # p.ej. la concentración "1.8 EC"), que es lo que la normalización por reglas +
    # similitud difusa puede resolver sin un diccionario de alias de negocio.
    canonical = normalizer.normalize("VERTIMEC 1.8 EC 1 LT")
    variant_l = normalizer.normalize("VERTIMEC 1.8 EC 1L")
    variant_litro = normalizer.normalize("VERTIMEC 1.8 EC 1 LITRO")

    assert canonical == "VERTIMEC 1.8 EC 1 LT"
    assert variant_l == canonical
    assert variant_litro == canonical


def test_unit_normalization_rules():
    normalizer = NameNormalizer(dictionary_path=None)
    normalizer._canonical_names = []  # evita interferencia de ejecuciones previas

    assert "1 LT" in normalizer._apply_rules("VERTIMEC 1 LITRO")
    assert "5 KG" in normalizer._apply_rules("UREA 5 KGS")
    assert "250 CC" in normalizer._apply_rules("ENGEO 250 ML")


def test_similar_color_variants_are_not_collapsed(tmp_path):
    normalizer = NameNormalizer(dictionary_path=tmp_path / "dict.json")

    red_blue = normalizer.normalize("Victorinox Evoke roja azul")
    red = normalizer.normalize("Victorinox Evoke roja")

    assert red_blue != red
    assert red.endswith("ROJA")
