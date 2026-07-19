"""Render the checked-in Nginx template without expanding Nginx variables."""

import argparse
from pathlib import Path

from bluebubbles.deployment import DeploymentTemplateRenderer


def render_nginx(template_path: Path, output_path: Path, hostname: str) -> None:
    """Render one validated hostname and refuse to overwrite an existing file."""
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_path}")
    template = template_path.read_text(encoding="utf-8")
    rendered = DeploymentTemplateRenderer(
        template, required_values=frozenset({"server_hostname"})
    ).render({"server_hostname": hostname})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")


def main() -> int:
    """Parse safe paths and render a deployment Nginx configuration."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hostname", required=True)
    arguments = parser.parse_args()
    render_nginx(arguments.template, arguments.output, arguments.hostname)
    print(f"Rendered Nginx configuration: {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
