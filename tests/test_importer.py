from vin_collector.importer import import_products


def test_imports_products_from_csv(tmp_path):
    csv_path = tmp_path / "productos.csv"
    csv_path.write_text(
        "SKU,Nombre,Marca\nVTX-001,VERTIMEC 1.8 EC 1 LT,\nABM-010,ABAMITE 1 LT,ANASAC\n",
        encoding="utf-8",
    )

    products = import_products(csv_path)

    assert len(products) == 2
    assert products[0].sku == "VTX-001"
    assert products[0].nombre_original == "VERTIMEC 1.8 EC 1 LT"
    assert products[1].marca == "ANASAC"


def test_raises_for_missing_file(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        import_products(tmp_path / "no_existe.csv")
