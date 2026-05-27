from app.deanonymizer import deanonymize
from app.models import DeanonymizeRequest


def test_deanonymize_simple():
    request = DeanonymizeRequest(
        text="Kontaktieren Sie [PERSON_1] unter [EMAIL_1].",
        mapping={
            "[PERSON_1]": "Max Mustermann",
            "[EMAIL_1]": "max@example.com",
        },
    )
    result = deanonymize(request)
    assert result.restored_text == "Kontaktieren Sie Max Mustermann unter max@example.com."
    assert result.replacements_made == 2
    assert result.unresolved_placeholders == []


def test_deanonymize_unresolved():
    request = DeanonymizeRequest(
        text="[PERSON_1] und [PERSON_2] arbeiten zusammen.",
        mapping={"[PERSON_1]": "Max Mustermann"},
    )
    result = deanonymize(request)
    assert "Max Mustermann" in result.restored_text
    assert "[PERSON_2]" in result.restored_text
    assert result.replacements_made == 1
    assert "[PERSON_2]" in result.unresolved_placeholders


def test_deanonymize_empty_mapping():
    request = DeanonymizeRequest(
        text="Kein Platzhalter hier.",
        mapping={},
    )
    result = deanonymize(request)
    assert result.restored_text == "Kein Platzhalter hier."
    assert result.replacements_made == 0


def test_deanonymize_multiple_same_placeholder():
    request = DeanonymizeRequest(
        text="[PERSON_1] sagte, dass [PERSON_1] kommt.",
        mapping={"[PERSON_1]": "Anna"},
    )
    result = deanonymize(request)
    assert result.restored_text == "Anna sagte, dass Anna kommt."
    assert result.replacements_made == 2
