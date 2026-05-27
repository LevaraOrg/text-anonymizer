from __future__ import annotations

from pydantic import BaseModel, Field

EXAMPLE_TEXT = (
    "Dear Mr. Johnson, this is Sarah Miller from Levara. "
    "We are writing regarding the contract between Levara and Acme Corp "
    "for the OrcaEngine migration project. "
    "Please contact Sarah at sarah.miller@levara.cloud or +1 555-0198. "
    "The meeting is scheduled at 742 Evergreen Terrace, Springfield, IL 62704 on 06/15/2025. "
    "Your account reference is ACC-2025-88421."
)

ANONYMIZE_EXAMPLE_PROTECTED = {
    "summary": "Protected terms — force-anonymize business secrets",
    "description": (
        "The company names 'Levara' and 'Acme Corp' and the project name 'OrcaEngine' "
        "are NOT standard PII — the model would not detect them. "
        "By listing them under protected_terms, they are always anonymized with custom categories "
        "like [COMPANY_1], [CUSTOMER_1], [PROJECT_1]. "
        "This prevents business secrets from leaking to AI services."
    ),
    "value": {
        "text": EXAMPLE_TEXT,
        "protected_terms": {
            "COMPANY": ["Levara"],
            "CUSTOMER": ["Acme Corp"],
            "PROJECT": ["OrcaEngine"],
        },
    },
}

ANONYMIZE_EXAMPLE_COMBINED = {
    "summary": "Combined — protected terms + exclusions",
    "description": (
        "'Levara' and 'OrcaEngine' are force-anonymized via protected_terms. "
        "'Springfield' is excluded from anonymization via exclusions (it stays visible). "
        "Standard PII (persons, emails, phones) is detected by the model as usual."
    ),
    "value": {
        "text": EXAMPLE_TEXT,
        "protected_terms": {
            "COMPANY": ["Levara"],
            "CUSTOMER": ["Acme Corp"],
            "PROJECT": ["OrcaEngine"],
        },
        "exclusions": ["Springfield"],
    },
}

ANONYMIZE_EXAMPLE_PLAIN = {
    "summary": "Plain — PII model only, no custom terms",
    "description": (
        "No protected_terms and no exclusions. Only standard PII detected by the model "
        "(person names, emails, phones, addresses, dates) is anonymized. "
        "Business terms like 'Levara', 'Acme Corp', 'OrcaEngine' pass through unchanged."
    ),
    "value": {
        "text": EXAMPLE_TEXT,
    },
}

DEANONYMIZE_EXAMPLE = {
    "summary": "Restore AI-processed text",
    "description": (
        "An AI has summarized the anonymized text. The placeholders are still intact. "
        "Pass the AI output together with the original mapping table to restore all values — "
        "both PII and business terms."
    ),
    "value": {
        "text": (
            "Summary: [PERSON_1] from [COMPANY_1] confirmed the contract with [CUSTOMER_1] "
            "for the [PROJECT_1] migration. "
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
            "[COMPANY_1]": "Levara",
            "[CUSTOMER_1]": "Acme Corp",
            "[PROJECT_1]": "OrcaEngine",
        },
    },
}


class AnonymizeRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                ANONYMIZE_EXAMPLE_PROTECTED["value"],
                ANONYMIZE_EXAMPLE_COMBINED["value"],
                ANONYMIZE_EXAMPLE_PLAIN["value"],
            ]
        }
    }

    text: str = Field(..., description="The text to anonymize")
    protected_terms: dict[str, list[str]] = Field(
        default_factory=dict,
        description=(
            "Terms to ALWAYS anonymize, mapped by custom category. "
            "Use this for business secrets, company names, customer names, project codes, "
            "or domain-specific terms the PII model would not detect. "
            "Example: {\"COMPANY\": [\"Levara\"], \"CUSTOMER\": [\"Acme Corp\"], \"PROJECT\": [\"OrcaEngine\"]}"
        ),
    )
    exclusions: list[str] = Field(
        default_factory=list,
        description="Terms to NEVER anonymize — they stay visible even if the model detects them as PII",
    )
    categories: list[str] | None = Field(
        default=None,
        description=(
            "PII categories to detect (model-based). None = all. "
            "Options: person, email_address, phone_number, private_address, url, date, account_number, secret"
        ),
    )


class DetectedEntity(BaseModel):
    placeholder: str = Field(..., description="The placeholder used in anonymized text, e.g. [PERSON_1] or [COMPANY_1]")
    original: str = Field(..., description="The original text that was replaced")
    category: str = Field(..., description="Category — either a PII type (person, email) or a custom category (company, customer)")
    start: int = Field(..., description="Start character offset in original text")
    end: int = Field(..., description="End character offset in original text")


class AnonymizeResponse(BaseModel):
    anonymized_text: str = Field(..., description="Text with PII and protected terms replaced by numbered placeholders")
    mapping: dict[str, str] = Field(
        ...,
        description="Mapping from placeholder to original value — keep this to restore the text later",
    )
    entities: list[DetectedEntity] = Field(..., description="All detected and protected entities with details")
    exclusions_applied: list[str] = Field(default_factory=list, description="Terms that were protected from anonymization")
    protected_terms_applied: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Custom terms that were force-anonymized, grouped by category",
    )


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
