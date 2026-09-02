import pytest

from emporio import policies


@pytest.fixture(scope="module")
def index():
    return policies.load()


def test_every_manual_section_is_extracted(index):
    numbers = {section.number.rstrip(".") for section in index.sections}
    assert {"1", "2", "3", "4", "7", "9", "10"} <= numbers
    assert {"3.1", "4.1", "4.4", "5.2", "6.2", "7.3", "8.3"} <= numbers


def test_the_numbered_list_inside_7_2_is_not_read_as_a_heading(index):
    flow = next(s for s in index.sections if s.number == "7.2")
    assert "Saudação" in flow.text
    assert "Entendimento" in flow.text


def test_orphan_headings_keep_their_parent(index):
    shipping = next(s for s in index.sections if s.number == "5.1")
    assert shipping.parent == "5. Política de Frete e Entregas"


# The agent always receives three chunks, so that is what the test asserts on.
# Demanding the top spot would be testing a tie break: "cordas e palhetas" is
# genuinely ambiguous between the catalogue scope and the warranty exclusions.
@pytest.mark.parametrize(
    "question, expected_section",
    [
        ("me arrependi da compra, posso devolver?", "4.1"),
        ("chegou quebrado, e a garantia?", "8.1"),
        ("que horas abre no sábado?", "2."),
        ("dá pra parcelar no cartão?", "3.1"),
        ("vocês vendem cordas e palhetas?", "1."),
        ("posso pagar metade no pix e metade no cartão?", "3.1"),
        ("meu pedido some no rastreio", "5.3"),
    ],
)
def test_questions_land_on_the_right_section(index, question, expected_section):
    found = [hit["section"] for hit in index.search(question, limit=3)]
    assert any(section.startswith(expected_section) for section in found), found


def test_an_empty_question_returns_nothing(index):
    assert index.search("???") == []
