"""Internal base classes for strict API-facing Pydantic contracts."""

from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Base model that rejects undocumented fields and validates assignment."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=False,
    )


class ImmutableContractModel(ContractModel):
    """Immutable variant for protocol and cryptographic value objects."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        use_enum_values=False,
    )
