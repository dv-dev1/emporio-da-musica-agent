"""Guards the link between the policy manual and the suite.

A clause declared in emporio.spec is a promise that the agent enforces it. This
fails the moment a promise stops being pinned by a test.
"""

import pytest

from emporio.spec import CLAUSES


def _marked_sections(session) -> set[str]:
    sections = set()
    for item in session.items:
        for mark in item.iter_markers(name="spec"):
            sections.update(mark.args)
    return sections


@pytest.fixture(scope="session")
def covered(request):
    return _marked_sections(request.session)


def test_every_declared_clause_has_a_test(covered):
    missing = sorted(clause.section for clause in CLAUSES if clause.section not in covered)
    assert not missing, f"cláusulas sem teste: {missing}"


def test_no_test_claims_a_clause_that_was_never_declared(covered):
    declared = {clause.section for clause in CLAUSES}
    unknown = sorted(covered - declared)
    assert not unknown, f"testes marcados com cláusula inexistente: {unknown}"
