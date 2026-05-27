from __future__ import annotations

from pydantic import BaseModel, Field


class AnonymizeRequest(BaseModel):
    text: str = Field(..., description="The text to anonymize")
    exclusions: list[str] = Field(
        default_factory=list,
        description="Terms to exclude from anonymization (company names, technical terms, etc.)",
    )
    categories: list[str] | None = Field(
        default=None,
        description="PII categories to detect. None = all. Options: person, email, phone, address, url, date, account_number, secret",
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
        description="Mapping from placeholder to original value, e.g. {'[PERSON_1]': 'Max Mustermann'}",
    )
    entities: list[DetectedEntity] = Field(..., description="All detected entities with details")
    exclusions_applied: list[str] = Field(..., description="Terms that were protected from anonymization")


class DeanonymizeRequest(BaseModel):
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
