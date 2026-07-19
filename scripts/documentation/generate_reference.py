"""Generate configuration and transport references from authoritative code."""

import argparse
import json
from pathlib import Path
from typing import Any

from fastapi.routing import APIRoute, APIWebSocketRoute
from pydantic import BaseModel, SecretStr
from pydantic_core import PydanticUndefined

from bluebubbles.client.configuration.settings import ClientSettings
from bluebubbles.server.application import create_application
from bluebubbles.server.configuration.settings import ServerSettings


def _transport_routes(routes: list[Any]) -> list[Any]:
    """Flatten FastAPI's lazy included-router wrappers without starting the app."""
    flattened: list[Any] = []
    for route in routes:
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            flattened.extend(_transport_routes(list(original_router.routes)))
        else:
            flattened.append(route)
    return flattened


def _type_name(annotation: object) -> str:
    name = getattr(annotation, "__name__", None)
    rendered = name if isinstance(name, str) else str(annotation)
    return (
        rendered.replace("<class '", "")
        .replace("<enum '", "")
        .replace("'>", "")
        .replace("|", "\\|")
    )


def _default_text(value: object) -> str:
    if value is PydanticUndefined:
        return "required"
    if isinstance(value, SecretStr):
        return "`<redacted>`"
    if value is None:
        return "`null`"
    if isinstance(value, Path):
        return f"`{value}`"
    if isinstance(value, set):
        value = sorted(value)
    rendered = json.dumps(value, default=str, sort_keys=True)
    return f"`{rendered}`"


def _configuration_rows(model: type[BaseModel], prefix: str = "") -> list[str]:
    rows: list[str] = []
    for name, field in model.model_fields.items():
        path = f"{prefix}.{name}" if prefix else name
        annotation = field.annotation
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            rows.extend(_configuration_rows(annotation, path))
            continue
        constraints = ", ".join(str(item) for item in field.metadata) or "-"
        default = _default_text(field.get_default(call_default_factory=True))
        rows.append(
            f"| `{path}` | `{_type_name(annotation)}` | " f"{default} | {constraints} |"
        )
    return rows


def configuration_reference() -> str:
    """Return a complete field/default/constraint reference."""
    sections = [
        "# Configuration reference",
        "",
        "Generated from the strict Pydantic settings models. Unknown keys fail. "
        "Secret defaults are redacted. Environment variables use `__` between "
        "nested names.",
        "",
    ]
    for title, model in (
        ("Server", ServerSettings),
        ("Windows client", ClientSettings),
    ):
        sections.extend(
            [
                f"## {title}",
                "",
                "| Setting | Type | Default | Constraints |",
                "|---|---|---|---|",
                *_configuration_rows(model),
                "",
            ]
        )
    return "\n".join(sections) + "\n"


def _response_name(value: Any) -> str:
    return getattr(value, "__name__", str(value)) if value is not None else "Response"


def api_reference() -> str:
    """Return the current HTTP and WebSocket route catalogue."""
    rows: list[str] = []
    for route in _transport_routes(list(create_application().routes)):
        if isinstance(route, APIRoute):
            methods = ", ".join(sorted(route.methods or ()))
            rows.append(
                f"| `{methods}` | `{route.path}` | {route.summary or route.name} | "
                f"`{_response_name(route.response_model)}` |"
            )
        elif isinstance(route, APIWebSocketRoute):
            rows.append(
                f"| `WSS` | `{route.path}` | Authenticated event stream | `events` |"
            )
    return "\n".join(
        [
            "# API and WebSocket reference",
            "",
            "Generated from the FastAPI route table. Production disables interactive "
            "API documentation. Protected HTTP routes require a bearer access token; "
            "the WebSocket authenticates with its first validated client envelope.",
            "",
            "| Method | Path | Purpose | Response |",
            "|---|---|---|---|",
            *sorted(rows),
            "",
        ]
    )


def generate(output_root: Path) -> tuple[Path, Path]:
    """Write both generated references below the selected documentation root."""
    output_root.mkdir(parents=True, exist_ok=True)
    configuration_path = output_root / "configuration-reference.md"
    api_path = output_root / "api-and-websocket-reference.md"
    configuration_path.write_text(configuration_reference(), encoding="utf-8")
    api_path.write_text(api_reference(), encoding="utf-8")
    return configuration_path, api_path


def main() -> int:
    """Parse output selection and regenerate deterministic references."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("documentation/reference"),
    )
    arguments = parser.parse_args()
    for path in generate(arguments.output_root):
        print(f"Generated: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
