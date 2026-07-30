from vin_collector.classifier import Classifier


def test_classifies_agrochemical_product(tmp_path):
    categories_path = tmp_path / "categorias.json"
    categories_path.write_text(
        '{"Fitosanitario": ["VERTIMEC", " EC"], "EPP": ["BOTIN"], "Otros": []}',
        encoding="utf-8",
    )
    classifier = Classifier(categories_path=categories_path)

    assert classifier.classify("VERTIMEC 1.8 EC 1 LT") == "Fitosanitario"
    assert classifier.classify("BOTIN BATA TALLA 42") == "EPP"
    assert classifier.classify("PRODUCTO SIN PALABRAS CLAVE") == "Otros"
