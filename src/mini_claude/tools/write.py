"""Write tool for writing file contents."""

from pathlib import Path
from typing import Any

from mini_claude.core.tool import Tool, ToolResult


class WriteTool(Tool):
    """Tool for writing file contents."""

    name = "Write"
    description = "Write content to a file (creates or overwrites)"

    async def execute(
        self,
        file_path: str,
        content: str,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Write content to a file.

        Args:
            file_path: Path to the file to write
            content: Content to write to the file
            **kwargs: Additional arguments (unused)

        Returns:
            ToolResult with success status or error
        """
        try:
            path = Path(file_path)

            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write the content
            path.write_text(content, encoding="utf-8", newline="\n")

            return ToolResult.ok(
                content=f"Successfully wrote to {path}",
                data={
                    "file_path": str(path.resolve()),
                    "bytes_written": len(content.encode("utf-8")),
                },
            )
        except PermissionError:
            return ToolResult.err(f"Permission denied: {file_path}")
        except Exception as e:
            return ToolResult.err(f"Failed to write file: {e}")
