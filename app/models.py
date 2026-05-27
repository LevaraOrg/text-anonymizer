from __future__ import annotations

from pydantic import BaseModel, Field

ANONYMIZE_EXAMPLE_WITH_EXCLUSIONS = {
    "summary": "With exclusions — company and customer names preserved",
    "description": (
        "The names 'Levara' and 'Acme Corp' appear in the text but are listed in exclusions. "
        "They will NOT be anonymized even if the model detects them as entities. "
        "All other PII (person names, emails, phones, addresses) will be replaced with placeholders."
    ),
    "value": {
        "text": (
            "Dear Mr. Johnson, this is Sarah Miller from Levara. "
            "We are writing regarding the contract between Levara and Acme Corp. "
            "Please contact Sarah at sarah.miller@levara.cloud or +1 555-0198. "
            "The meeting is scheduled at 742 Evergreen Terrace, Springfield, IL 62704 on 06/15/2025. "
            "Your account reference is ACC-2025-88421."
        ),
        "exclusions": ["Levara", "Acme Corp"],
    },
}

ANONYMIZE_EXAMPLE_WITHOUT_EXCLUSIONS = {
    "summary": "Without exclusions — everything anonymized",
    "description": (
        "Same text but NO exclusions. Now 'Levara' and 'Acme Corp' may also be "
        "detected and anonymized if the model classifies them as PII. "
        "Compare the result with the 'with exclusions' example to see the difference."
    ),
    "value": {
        "text": (
            "Dear Mr. Johnson, this is Sarah Miller from Levara. "
            "We are writing regarding the contract between Levara and Acme Corp. "
            "Please contact Sarah at sarah.miller@levara.cloud or +1 555-0198. "
            "The meeting is scheduled at 742 Evergreen Terrace, Springfield, IL 62704 on 06/15/2025. "
            "Your account reference is ACC-2025-88421."
        ),
        "exclusions": [],
    },
}

ANONYMIZE_EXAMPLE_CATEGORY_FILTER = {
    "summary": "Category filter — only detect persons and emails",
    "description": (
        "Same text but only person names and email addresses are anonymized. "
        "Phone numbers, addresses, dates, and account numbers are left untouched."
    ),
    "value": {
        "text": (
            "Dear Mr. Johnson, this is Sarah Miller from Levara. "
            "We are writing regarding the contract between Levara and Acme Corp. "
            "Please contact Sarah at sarah.miller@levara.cloud or +1 555-0198. "
            "The meeting is scheduled at 742 Evergreen Terrace, Springfield, IL 62704 on 06/15/2025. "
            "Your account reference is ACC-2025-88421."
        ),
        "exclusions": ["Levara", "Acme Corp"],
        "categories": ["person", "email_address"],
    },
}

DEANONYMIZE_EXAMPLE = {
    "summary": "Restore AI-processed text",
    "description": (
        "An AI has summarized an anonymized text. The placeholders are still intact. "
        "Pass the AI output together with the original mapping table to restore real names."
    ),
    "value": {
        "text": (
            "Summary: [PERSON_1] from Levara confirmed the contract with Acme Corp. "
            "[PERSON_2] will handle communications via [EMAIL_1]. "
            "Next meeting at [ADDRESS_1] on [DATE_1]."
        ),
        "mapping": {
            "[PERSON_1]": "Sarah Miller",
            "[PERSON_2]": "Mr. Johnson",
            "[EMAIL_1]": "sarah.miller@levara.cloud",
            "[PHONE_1]": "+1 555-0198",
            "[ADDRESS_1]": "742 Evergreen Terrace, Springfield, IL 62704",
            "[DATE_1]": "06/15/2025",
            "[ACCOUNT_1]": "ACC-2025-88421",
        },
    },
}


class AnonymizeRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                ANONYMIZE_EXAMPLE_WITH_EXCLUSIONS["value"],
                ANONYMIZE_EXAMPLE_WITHOUT_EXCLUSIONS["value"],
                ANONYMIZE_EXAMPLE_CATEGORY_FILTER["value"],
            ]
        }
    }

    text: str = Field(..., description="The text to anonymize")
    exclusions: list[str] = Field(
        default_factory=list,
        description="Terms to exclude from anonymization (company names, technical terms, etc.)",
    )
    categories: list[str] | None = Field(
        default=None,
        description="PII categories to detect. None = all. Options: person, email_address, phone_number, private_address, url, date, account_number, secret",
    )


class DetectedEntity(BaseModel):
    placeholder: str = Field(..., description="The placeholder used in anonymized text, e.g. [PERSON_1]")
    original: str = Field(..., description="The original text that was replaced")
    category: str = Field(..., description="PII category (person, email, phone, ...)")
    start: int = Field(..., description="Start character offset in original text")
    end: int = Field(..., description="End character offset in original text")


class AnonymizeResponse(BaseModel):
    anonymized_text: str = Field(..., description="Text with PII replaced by numbered placeholders")
    mapping: dict[str, str] = Field(
        ...,
        description="Mapping from placeholder to original value, e.g. {'[PERSON_1]': 'John Smith'}",
    )
    entities: list[DetectedEntity] = Field(..., description="All detected entities with details")
    exclusions_applied: list[str] = Field(..., description="Terms that were protected from anonymization")


class DeanonymizeRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [DEANONYMIZE_EXAMPLE["value"]]
        }
    }

    text: str = Field(..., description="The anonymized (and possibly AI-processed) text containing placeholders")
    mapping: dict[str, str] = Field(
        ...,
        description="The mapping table from the anonymize response",
    )


class DeanonymizeResponse(BaseModel):
    restored_text: str = Field(..., description="Text with placeholders replaced by original values")
    replacements_made: int = Field(..., description="Number of placeholders that were restored")
    unresolved_placeholders: list[str] = Field(
        default_factory=list,
        description="Placeholders found in text that had no mapping entry",
    )
