"""Strict rendering for checked-in deployment configuration templates."""

import re
from collections.abc import Mapping
from string import Template

_HOSTNAME_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)
_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9_./:@+-]{1,512}$")


class DeploymentTemplateRenderer:
    """Substitute an exact allowlist of safe operational values."""

    def __init__(self, template: str, *, required_values: frozenset[str]) -> None:
        """Create a renderer and reject undeclared template placeholders."""
        if not template:
            raise ValueError("deployment template cannot be empty")
        discovered = {
            match.group("named") or match.group("braced")
            for match in Template.pattern.finditer(template)
            if match.group("named") or match.group("braced")
        }
        if discovered != required_values:
            raise ValueError("template placeholders must exactly match required values")
        self._template = Template(template)
        self._required_values = required_values

    def render(self, values: Mapping[str, str]) -> str:
        """Render the template after exact-key and injection-safe validation."""
        if set(values) != self._required_values:
            raise ValueError("template values must exactly match required values")
        for key, value in values.items():
            pattern = _HOSTNAME_PATTERN if key.endswith("hostname") else _VALUE_PATTERN
            if not pattern.fullmatch(value):
                raise ValueError(f"unsafe deployment template value: {key}")
        return self._template.substitute(values)
