"""
Tool: Architecture diagram generator (Mermaid / draw.io XML)
"""


def generate_mermaid(services: list[str], connections: list[tuple[str, str]]) -> str:
    """Generate a Mermaid flowchart string from services and connections."""
    lines = ["graph TD"]
    for src, dst in connections:
        lines.append(f"    {src} --> {dst}")
    return "\n".join(lines)
