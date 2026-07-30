from vin_collector.models import ImageCandidate
from vin_collector.ranking import rank_candidates


def test_higher_resolution_and_priority_domain_ranks_first():
    low_res_generic = ImageCandidate(
        url="https://example.com/a.jpg", source_domain="randomshop.com",
        width=150, height=150, priority_tier=5,
    )
    high_res_manufacturer = ImageCandidate(
        url="https://example.com/b.jpg", source_domain="syngenta.cl",
        width=1600, height=1600, priority_tier=1,
    )

    ranked = rank_candidates([low_res_generic, high_res_manufacturer])

    assert ranked[0].url == high_res_manufacturer.url
    assert ranked[0].score > ranked[1].score
