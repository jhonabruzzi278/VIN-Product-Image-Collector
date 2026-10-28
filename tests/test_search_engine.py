from vin_collector.models import Product
from vin_collector.search_engine import SearchEngine, SearchProvider


class EmptyProvider(SearchProvider):
    def search_images(self, query: str, max_results: int):
        return []


def test_victorinox_internal_sku_generates_official_model_query():
    engine = SearchEngine(provider=EmptyProvider())
    product = Product(
        sku="NAV9415DS23",
        nombre_original="Victorinox Evoke BS Alox",
        nombre_normalizado="VICTORINOX EVOKE BS ALOX",
        marca="Victorinox",
    )

    queries = engine.build_queries(product)

    assert queries[0] == 'Victorinox "0.9415.DS23"'
