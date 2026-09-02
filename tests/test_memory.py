import pytest

from emporio.memory import History


@pytest.fixture
def history(tmp_path):
    return History("alpha", db_path=tmp_path / "chat.db", max_turns=3)


def test_a_new_session_starts_empty(history):
    assert history.messages() == []


def test_messages_come_back_in_the_order_they_were_said(history):
    history.append("user", "oi")
    history.append("assistant", "opa")
    history.append("user", "tem violão?")
    assert [m["content"] for m in history.messages()] == ["oi", "opa", "tem violão?"]


def test_only_the_last_turns_are_replayed(history):
    for index in range(20):
        history.append("user", f"m{index}")
    replayed = history.messages()
    assert len(replayed) == history.max_turns * 2
    assert replayed[-1]["content"] == "m19"


def test_two_sessions_do_not_see_each_other(tmp_path):
    db = tmp_path / "chat.db"
    alpha, beta = History("alpha", db_path=db), History("beta", db_path=db)
    alpha.append("user", "segredo do alpha")
    assert beta.messages() == []
    assert alpha.messages()[0]["content"] == "segredo do alpha"


def test_clearing_one_session_leaves_the_other_alone(tmp_path):
    db = tmp_path / "chat.db"
    alpha, beta = History("alpha", db_path=db), History("beta", db_path=db)
    alpha.append("user", "a")
    beta.append("user", "b")
    alpha.clear()
    assert alpha.messages() == []
    assert len(beta.messages()) == 1
