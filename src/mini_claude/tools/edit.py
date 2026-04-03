"""Edit tool for precise string replacement in files."""

import re
from pathlib import Path
from typing import Any, Optional

from mini_claude.core.tool import Tool, ToolResult


def _normalize_newlines(text: str) -> str:
    """Normalize all newlines to LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _detect_newline_style(text: str) -> str:
    """Detect the dominant newline style in text."""
    if "\r\n" in text:
        return "\r\n"
    return "\n"


class EditTool(Tool):
    """Tool for precise string replacement in files."""

    name = "Edit"
    description = "Perform precise string replacement in a file"

    async def execute(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Perform string replacement in a file.

        Args:
            file_path: Path to the file to edit
            old_string: String to search for
            new_string: String to replace with
            replace_all: Whether to replace all occurrences or just the first
            **kwargs: Additional arguments (unused)

        Returns:
            ToolResult with success status or error
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return ToolResult.err(f"File not found: {file_path}")
            if not path.is_file():
                return ToolResult.err(f"Path is not a file: {file_path}")

            # Read and normalize content
            content = path.read_text(encoding="utf-8")
            normalized_content = _normalize_newlines(content)
            normalized_old = _normalize_newlines(old_string)

            # Check if old_string exists
            if normalized_old not in normalized_content:
                return ToolResult.err(
                    f"String not found in file: {repr(old_string)}"
                )

            # Count occurrences
            count = normalized_content.count(normalized_old)

            # Perform replacement
            if replace_all:
                normalized_new_content = normalized_content.replace(
                    normalized_old, _normalize_newlines(new_string)
                )
            else:
                normalized_new_content = normalized_content.replace(
                    normalized_old, _normalize_newlines(new_string), 1
                )

            # Restore original newline style
            newline_style = _detect_newline_style(content)
            new_content = normalized_new_content.replace("\n", newline_style)

            # Write back
            path.write_text(new_content, encoding="utf-8", newline="")

            replaced_count = count if replace_all else 1
            return ToolResult.ok(
                content=f"Replaced {replaced_count} occurrence(s) in {path}",
                data={
                    "file_path": str(path.resolve()),
                    "occurrences_found": count,
                    "occurrences_replaced": replaced_count,
                },
            )
        except UnicodeDecodeError:
            return ToolResult.err(f"File is not valid UTF-8: {file_path}")
        except PermissionError:
            return ToolResult.err(f"Permission denied: {file_path}")
        except Exception as e:
            return ToolResult.err(f"Failed to edit file: {e}")
