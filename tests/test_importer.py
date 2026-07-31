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


def test_imports_products_from_csv_with_utf8_bom(tmp_path):
    """Regresión: exportar 'CSV UTF-8' desde Excel antepone un BOM al encabezado
    ("\\ufeffPRODUCTO"), lo que antes hacía que no matcheara contra COLUMN_ALIASES
    y todas las filas se descartaran silenciosamente (0 productos importados,
    catálogo sin cambios pese a subir un archivo distinto)."""
    csv_path = tmp_path / "productos_bom.csv"
    csv_path.write_bytes(
        "﻿PRODUCTO\r\nAbamite 1.8 Ec X5lts\r\nAcaban 050 Sc X 1 Lt\r\n".encode("utf-8")
    )

    products = import_products(csv_path)

    assert len(products) == 2
    assert products[0].nombre_original == "Abamite 1.8 Ec X5lts"


def test_imports_single_column_csv_without_mis_sniffing_delimiter(tmp_path):
    """Regresión: con sep=None, el csv.Sniffer de pandas podía "inventar" un
    delimitador a partir de letras repetidas en un encabezado de una sola
    columna (ej. partió "PRODUCTO" en "PR"/"DUCT" usando la "O" como
    separador), perdiendo la columna de nombre por completo."""
    csv_path = tmp_path / "productos_una_columna.csv"
    csv_path.write_text(
        "PRODUCTO\nAbamite 1.8 Ec X5lts\nAcaban 050 Sc X 1 Lt\nAceite 2 T X 100 Cc\n",
        encoding="utf-8",
    )

    products = import_products(csv_path)

    assert len(products) == 3
    assert [p.nombre_original for p in products] == [
        "Abamite 1.8 Ec X5lts",
        "Acaban 050 Sc X 1 Lt",
        "Aceite 2 T X 100 Cc",
    ]


def test_single_column_csv_strips_quotes_from_fields_with_commas(tmp_path):
    """Un campo entrecomillado por el exportador (porque contiene una coma)
    no debe conservar las comillas literales en el nombre del producto — eso
    degradaría la calidad de las búsquedas de imagen."""
    csv_path = tmp_path / "productos_comillas.csv"
    csv_path.write_text(
        'PRODUCTO\n"Aceite Para Multitool, 10ml, Blister 10 ml"\nAcaban 050 Sc X 1 Lt\n',
        encoding="utf-8",
    )

    products = import_products(csv_path)

    assert len(products) == 2
    assert products[0].nombre_original == "Aceite Para Multitool, 10ml, Blister 10 ml"


def test_imports_semicolon_delimited_csv(tmp_path):
    """Excel en configuración regional (ej. es-CL) suele exportar CSV con ';'
    como delimitador en vez de ',' — debe seguir funcionando."""
    csv_path = tmp_path / "productos_semicolon.csv"
    csv_path.write_text(
        "SKU;Nombre;Marca\nVTX-001;VERTIMEC 1.8 EC 1 LT;\n",
        encoding="utf-8",
    )

    products = import_products(csv_path)

    assert len(products) == 1
    assert products[0].sku == "VTX-001"
    assert products[0].nombre_original == "VERTIMEC 1.8 EC 1 LT"


def test_imports_plain_txt_list_without_header(tmp_path):
    """Un .txt de una sola columna sin encabezado (una línea = un producto)
    debe seguir tratando TODAS las líneas como datos, no como encabezado."""
    txt_path = tmp_path / "productos.txt"
    txt_path.write_text("VERTIMEC 1.8 EC 1 LT\nABAMITE 1 LT\n", encoding="utf-8")

    products = import_products(txt_path)

    assert len(products) == 2
    assert products[0].nombre_original == "VERTIMEC 1.8 EC 1 LT"
