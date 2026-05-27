from app.deanonymizer import deanonymize
from app.models import DeanonymizeRequest


def test_deanonymize_simple():
    request = DeanonymizeRequest(
        text="Contact [PERSON_1] at [EMAIL_1].",
        mapping={
            "[PERSON_1]": "John Smith",
            "[EMAIL_1]": "john@example.com",
        },
    )
    result = deanonymize(request)
    assert result.restored_text == "Contact John Smith at john@example.com."
    assert result.replacements_made == 2
    assert result.unresolved_placeholders == []


def test_deanonymize_unresolved():
    request = DeanonymizeRequest(
        text="[PERSON_1] and [PERSON_2] work together.",
        mapping={"[PERSON_1]": "John Smith"},
    )
    result = deanonymize(request)
    assert "John Smith" in result.restored_text
    assert "[PERSON_2]" in result.restored_text
    assert result.replacements_made == 1
    assert "[PERSON_2]" in result.unresolved_placeholders


def test_deanonymize_empty_mapping():
    request = DeanonymizeRequest(
        text="No placeholders here.",
        mapping={},
    )
    result = deanonymize(request)
    assert result.restored_text == "No placeholders here."
    assert result.replacements_made == 0


def test_deanonymize_multiple_same_placeholder():
    request = DeanonymizeRequest(
        text="[PERSON_1] said that [PERSON_1] is coming.",
        mapping={"[PERSON_1]": "Anna"},
    )
    result = deanonymize(request)
    assert result.restored_text == "Anna said that Anna is coming."
    assert result.replacements_made == 2
