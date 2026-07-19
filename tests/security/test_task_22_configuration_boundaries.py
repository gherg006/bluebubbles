"""Generated at-boundary and out-of-bounds tests for every constrained setting."""

import math
from collections.abc import Iterator
from typing import Any

import pytest
from annotated_types import Ge, Gt, Le, Lt, MaxLen, MinLen
from pydantic import BaseModel, TypeAdapter, ValidationError

from bluebubbles.client.configuration.settings import ClientSettings
from bluebubbles.server.configuration.settings import ServerSettings


def _nested_model(annotation: object) -> type[BaseModel] | None:
    """Return a direct nested Pydantic model annotation when present."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return None


def _constraint_cases(model: type[BaseModel], prefix: str) -> Iterator[object]:
    """Yield accepted edge and rejected outside values for every field constraint."""
    for name, field in model.model_fields.items():
        path = f"{prefix}.{name}"
        nested = _nested_model(field.annotation)
        if nested is not None:
            yield from _constraint_cases(nested, path)
            continue
        if not field.metadata:
            continue
        constrained = field.rebuild_annotation()
        adapter = TypeAdapter(constrained)
        integer_field = field.annotation is int
        for constraint in field.metadata:
            case: tuple[object, object, str] | None = None
            if isinstance(constraint, Gt):
                edge = _numeric(constraint.gt)
                accepted = edge + 1 if integer_field else math.nextafter(edge, math.inf)
                case = (accepted, edge, "exclusive-minimum")
            elif isinstance(constraint, Ge):
                edge = _numeric(constraint.ge)
                rejected = (
                    edge - 1 if integer_field else math.nextafter(edge, -math.inf)
                )
                case = (edge, rejected, "minimum")
            elif isinstance(constraint, Lt):
                edge = _numeric(constraint.lt)
                accepted = (
                    edge - 1 if integer_field else math.nextafter(edge, -math.inf)
                )
                case = (accepted, edge, "exclusive-maximum")
            elif isinstance(constraint, Le):
                edge = _numeric(constraint.le)
                rejected = edge + 1 if integer_field else math.nextafter(edge, math.inf)
                case = (edge, rejected, "maximum")
            elif isinstance(constraint, MinLen):
                case = (
                    "x" * constraint.min_length,
                    "x" * max(0, constraint.min_length - 1),
                    "minimum-length",
                )
            elif isinstance(constraint, MaxLen):
                case = (
                    "x" * constraint.max_length,
                    "x" * (constraint.max_length + 1),
                    "maximum-length",
                )
            if case is not None:
                accepted_value, rejected_value, label = case
                yield pytest.param(
                    adapter,
                    accepted_value,
                    rejected_value,
                    id=f"{path}-{label}",
                )


def _numeric(value: object) -> int | float:
    """Narrow annotated-types numeric protocol values for boundary arithmetic."""
    if not isinstance(value, int | float):
        raise TypeError("configuration numeric constraint must use int or float")
    return value


BOUNDARY_CASES: tuple[Any, ...] = tuple(
    _constraint_cases(ServerSettings, "server")
) + tuple(_constraint_cases(ClientSettings, "client"))


@pytest.mark.parametrize(("adapter", "accepted", "rejected"), BOUNDARY_CASES)
def test_every_constrained_setting_accepts_edge_and_rejects_outside(
    adapter: TypeAdapter[object], accepted: object, rejected: object
) -> None:
    assert adapter.validate_python(accepted) is not None
    with pytest.raises(ValidationError):
        adapter.validate_python(rejected)
