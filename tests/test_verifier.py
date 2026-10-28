from vin_collector.models import ImageCandidate, Product
from vin_collector.verifier import HeuristicVerifier


def test_query_text_alone_cannot_verify_an_unrelated_image(tmp_path):
    product = Product(nombre_original="Karate Zeon 1 L", nombre_normalizado="KARATE ZEON 1 LT")
    candidate = ImageCandidate(
        url="https://example.com/fertilizante-generico.jpg",
        title="Fertilizante genÃ©rico",
        source_url="https://example.com/catalogo/fertilizante",
        source_domain="example.com",
        query_used="KARATE ZEON 1 LT",
    )

    matches, confidence = HeuristicVerifier().verify(product, tmp_path / "unused.jpg", candidate)

    assert matches is False
    assert confidence == 0
