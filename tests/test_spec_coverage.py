"""Guards the links SPEC.md is built from.

A clause declared in emporio.spec is a promise that the agent enforces it. Each
of its three columns is a claim that can rot on its own: the test may disappear,
a test may cite a clause nobody declared, or the code it names may be renamed
away. All three fail here.
"""

import importlib

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


def test_every_clause_points_at_code_that_exists():
    """The "Enforced in" column of SPEC.md, checked rather than trusted.

    It is the one column nothing else covers: a renamed function leaves the
    matrix pointing at a dead name while the whole suite still passes.
    """
    broken = []
    for clause in CLAUSES:
        for reference in (name.strip() for name in clause.implemented_in.split(",")):
            module_name, _, attribute = reference.partition(".")
            try:
                module = importlib.import_module(f"emporio.{module_name}")
            except ImportError:
                broken.append(f"§{clause.section} -> emporio.{module_name} (módulo)")
                continue
            if attribute and not hasattr(module, attribute):
                broken.append(f"§{clause.section} -> {reference}")
    assert not broken, f"cláusulas apontando para código inexistente: {broken}"
