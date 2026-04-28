"""Pydantic schemas for ClaimGuard API payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_DATE_FORMAT = "%Y-%m-%d"


class ClaimInput(BaseModel):
    """Validated single-claim payload for the prototype scoring API."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    claim_id: str = Field(min_length=3)
    member_id: str = Field(min_length=3)
    provider_id: str = Field(min_length=3)
    provider_name: str = Field(min_length=3)
    provider_type: str = Field(min_length=2)
    claim_date: str = Field(min_length=10)
    admission_date: str | None = None
    discharge_date: str | None = None
    diagnosis_code: str = Field(min_length=2)
    diagnosis_description: str = Field(min_length=3)
    procedure_code: str = Field(min_length=2)
    procedure_description: str = Field(min_length=3)
    drug_code: str | None = None
    claim_amount: float = Field(ge=0)
    approved_amount: float = Field(ge=0)
    document_count: int = Field(ge=0)
    has_invoice: bool
    has_discharge_summary: bool
    has_lab_report: bool
    previous_claim_count_90d: int = Field(ge=0)
    same_provider_claim_count_30d: int = Field(ge=0)
    claim_channel: str = Field(min_length=2)
    claim_status: str = Field(min_length=2)

    @field_validator("claim_date", "admission_date", "discharge_date", mode="before")
    @classmethod
    def validate_date_strings(cls, value: object) -> str | None:
        """Validate simple ISO-style date strings while keeping them as strings."""

        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("Date values must be provided as strings in YYYY-MM-DD format.")

        stripped_value = value.strip()
        if stripped_value == "":
            return None

        try:
            datetime.strptime(stripped_value, _DATE_FORMAT)
        except ValueError as exc:
            raise ValueError("Dates must use the YYYY-MM-DD format.") from exc

        return stripped_value

    @model_validator(mode="after")
    def validate_logical_date_order(self) -> "ClaimInput":
        """Ensure admission and discharge dates remain logically ordered."""

        if self.admission_date and self.discharge_date:
            admission_date = datetime.strptime(self.admission_date, _DATE_FORMAT)
            discharge_date = datetime.strptime(self.discharge_date, _DATE_FORMAT)
            if discharge_date < admission_date:
                raise ValueError("discharge_date cannot be earlier than admission_date.")
        return self


# Backward-compatible alias for earlier API imports.
ClaimSchema = ClaimInput
