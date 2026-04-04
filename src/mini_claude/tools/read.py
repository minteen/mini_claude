"""Read tool for reading file contents."""

from pathlib import Path
from typing import Any, Optional

from mini_claude.tools.base import Tool, ToolResult


class ReadTool(Tool):
    """Tool for reading file contents."""

    name = "Read"
    description = "Read contents from a file"

    async def execute(
        self,
        file_path: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Read contents from a file.

        Args:
            file_path: Path to the file to read
            offset: Line number to start reading from (1-indexed)
            limit: Maximum number of lines to read
            **kwargs: Additional arguments (unused)

        Returns:
            ToolResult with file content or error
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return ToolResult.err(f"File not found: {file_path}")
            if not path.is_file():
                return ToolResult.err(f"Path is not a file: {file_path}")

            with path.open("r", encoding="utf-8") as f:
                lines = f.readlines()

            # Apply offset and limit if specified
            start = (offset - 1) if (offset and offset > 0) else 0
            end = (start + limit) if limit else None
            selected_lines = lines[start:end]

            content = "".join(selected_lines)
            return ToolResult.ok(
                content=content,
                data={
                    "file_path": str(path.resolve()),
                    "total_lines": len(lines),
                    "returned_lines": len(selected_lines),
                    "offset": offset,
                    "limit": limit,
                },
            )
        except UnicodeDecodeError:
            return ToolResult.err(f"File is not valid UTF-8: {file_path}")
        except PermissionError:
            return ToolResult.err(f"Permission denied: {file_path}")
        except Exception as e:
            return ToolResult.err(f"Failed to read file: {e}")
