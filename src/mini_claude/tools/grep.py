"""Grep tool for searching file contents."""

import re
from pathlib import Path
from typing import Any, List, Optional, Tuple

from mini_claude.tools.base import Tool, ToolResult


class GrepTool(Tool):
    """Tool for searching file contents with regular expressions."""

    name = "Grep"
    description = "Search file contents using regular expressions"

    async def execute(
        self,
        pattern: str,
        path: Optional[str] = None,
        glob: Optional[str] = None,
        output_mode: str = "content",
        context: int = 0,
        case_insensitive: bool = False,
        multiline: bool = False,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Search file contents using regular expressions.

        Args:
            pattern: Regular expression pattern to search for
            path: File or directory to search (defaults to current directory)
            glob: Glob pattern to filter files (e.g., "*.py")
            output_mode: Output mode - "content", "files_with_matches", or "count"
            context: Number of context lines to show around matches
            case_insensitive: Whether to perform case-insensitive search
            multiline: Whether to enable multiline matching
            **kwargs: Additional arguments (unused)

        Returns:
            ToolResult with search results
        """
        try:
            search_path = Path(path) if path else Path.cwd()
            search_path = search_path.resolve()

            if not search_path.exists():
                return ToolResult.err(f"Path not found: {search_path}")

            # Compile regex pattern
            flags = 0
            if case_insensitive:
                flags |= re.IGNORECASE
            if multiline:
                flags |= re.MULTILINE

            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return ToolResult.err(f"Invalid regex pattern: {e}")

            # Collect files to search
            files_to_search: List[Path] = []
            if search_path.is_file():
                files_to_search.append(search_path)
            else:
                glob_pattern = glob or "**/*"
                for p in search_path.glob(glob_pattern):
                    if p.is_file():
                        files_to_search.append(p)

            # Perform search
            matches_by_file: List[Tuple[Path, List[Tuple[int, str, List[str], List[str]]]]] = []
            files_with_matches: List[str] = []
            total_matches = 0

            for file_path in files_to_search:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    lines = content.splitlines(keepends=False)
                except (UnicodeDecodeError, PermissionError):
                    continue

                file_matches: List[Tuple[int, str, List[str], List[str]]] = []

                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        # Collect context lines
                        before_lines = lines[max(0, line_num - 1 - context): line_num - 1]
                        after_lines = lines[line_num: line_num + context]

                        file_matches.append((line_num, line, before_lines, after_lines))
                        total_matches += 1

                if file_matches:
                    matches_by_file.append((file_path, file_matches))
                    files_with_matches.append(str(file_path.relative_to(search_path)))

            # Format output based on mode
            if output_mode == "files_with_matches":
                result_content = "\n".join(files_with_matches) if files_with_matches else "No matches found"
            elif output_mode == "count":
                result_content = f"Found {total_matches} matches in {len(files_with_matches)} files"
            else:  # content mode
                result_lines: List[str] = []
                for file_path, matches in matches_by_file:
                    rel_path = file_path.relative_to(search_path)
                    result_lines.append(f"--- {rel_path} ---")
                    for line_num, line, before, after in matches:
                        for ctx_line in before:
                            result_lines.append(f"  {ctx_line}")
                        result_lines.append(f"{line_num}:{line}")
                        for ctx_line in after:
                            result_lines.append(f"  {ctx_line}")
                    result_lines.append("")
                result_content = "\n".join(result_lines) if result_lines else "No matches found"

            return ToolResult.ok(
                content=result_content,
                data={
                    "pattern": pattern,
                    "path": str(search_path),
                    "files_with_matches": files_with_matches,
                    "total_matches": total_matches,
                    "files_searched": len(files_to_search),
                },
            )
        except Exception as e:
            return ToolResult.err(f"Failed to search: {e}")
