import pytest

from emporio import text


@pytest.mark.parametrize(
    "word, expected",
    [
        ("violões", "violao"), ("violao", "violao"),
        ("pães", "pao"), ("papéis", "papel"),
        ("bons", "bom"), ("cores", "cor"),
        ("guitarras", "guitarra"), ("ukulele", "ukulele"),
    ],
)
def test_plurals_collapse_onto_the_singular(word, expected):
    assert text.singular(text.normalize(word)) == expected


@pytest.mark.parametrize(
    "raw, expected", [("Violão", "violao"), ("SAXOFONE", "saxofone"), ("Ukulelê", "ukulele")]
)
def test_accents_and_case_fold_away(raw, expected):
    assert text.normalize(raw) == expected


def test_amounts_are_not_searched_as_words():
    assert text.search_terms("violões até 1000 reais") == ["violao"]


def test_a_model_code_keeps_its_short_fragments():
    assert text.search_terms("Giannini GF-3D") == ["giannini", "gf", "3d"]


def test_the_policy_stemmer_bridges_inflection():
    assert set(text.stem("me arrependi")) & set(text.stem("direito de arrependimento"))


def test_a_product_name_reduces_to_the_shape_of_a_query():
    assert text.searchable("Violões Yamaha C40") == "violao yamaha c40"
