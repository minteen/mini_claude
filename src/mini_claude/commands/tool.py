"""Tool command group for MiniClaude."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from mini_claude.commands.base import Command, CommandGroup
from mini_claude.tools import (
    ReadTool,
    WriteTool,
    EditTool,
    GlobTool,
    GrepTool,
    BashTool,
)

console = Console()


class ToolCommandGroup(CommandGroup):
    """Tool command group for direct tool invocation."""

    name = "tool"
    help = "Directly invoke MiniClaude tools"
    aliases = ["t"]
    group = "tools"

    def __init__(self):
        super().__init__(
            name=self.name,
            help=self.help,
            aliases=self.aliases,
            group=self.group,
        )
        self.add_command(ToolReadCommand())
        self.add_command(ToolWriteCommand())
        self.add_command(ToolEditCommand())
        self.add_command(ToolGlobCommand())
        self.add_command(ToolGrepCommand())
        self.add_command(ToolBashCommand())


class ToolReadCommand(Command):
    """Read a file using ReadTool."""

    name = "read"
    help = "Read a file"
    group = "tools"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def read_file(
            file_path: str = typer.Argument(..., help="Path to the file to read"),
            offset: Optional[int] = typer.Option(None, "--offset", "-o", help="Start reading from this line (1-indexed)"),
            limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Maximum number of lines to read"),
        ) -> None:
            asyncio.run(self._run(file_path, offset, limit))

    async def _run(self, file_path: str, offset: Optional[int], limit: Optional[int]) -> None:
        tool = ReadTool()
        result = await tool.execute(file_path=file_path, offset=offset, limit=limit)

        if result.success:
            console.print()
            console.print(Panel(result.content, title=f"[cyan]{Path(file_path).name}[/cyan]", border_style="cyan"))
            console.print()
        else:
            console.print(f"[red]Error:[/red] {result.error}")
            console.print()
            raise typer.Exit(1)


class ToolWriteCommand(Command):
    """Write content to a file using WriteTool."""

    name = "write"
    help = "Write content to a file"
    group = "tools"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def write_file(
            file_path: str = typer.Argument(..., help="Path to the file to write"),
            content: str = typer.Argument(..., help="Content to write to the file"),
        ) -> None:
            asyncio.run(self._run(file_path, content))

    async def _run(self, file_path: str, content: str) -> None:
        tool = WriteTool()
        result = await tool.execute(file_path=file_path, content=content)

        if result.success:
            console.print()
            console.print(f"[green]✓[/green] {result.content}")
            console.print()
        else:
            console.print(f"[red]Error:[/red] {result.error}")
            console.print()
            raise typer.Exit(1)


class ToolEditCommand(Command):
    """Edit a file using EditTool."""

    name = "edit"
    help = "Edit a file by replacing strings"
    group = "tools"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def edit_file(
            file_path: str = typer.Argument(..., help="Path to the file to edit"),
            old_string: str = typer.Argument(..., help="String to search for"),
            new_string: str = typer.Argument(..., help="String to replace with"),
            replace_all: bool = typer.Option(False, "--all", "-a", help="Replace all occurrences"),
        ) -> None:
            asyncio.run(self._run(file_path, old_string, new_string, replace_all))

    async def _run(self, file_path: str, old_string: str, new_string: str, replace_all: bool) -> None:
        tool = EditTool()
        result = await tool.execute(
            file_path=file_path,
            old_string=old_string,
            new_string=new_string,
            replace_all=replace_all,
        )

        if result.success:
            console.print()
            console.print(f"[green]✓[/green] {result.content}")
            console.print()
        else:
            console.print(f"[red]Error:[/red] {result.error}")
            console.print()
            raise typer.Exit(1)


class ToolGlobCommand(Command):
    """Search for files using GlobTool."""

    name = "glob"
    help = "Search for files matching a pattern"
    group = "tools"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def glob_files(
            pattern: str = typer.Argument(..., help="Glob pattern to match (e.g., '**/*.py')"),
            path: Optional[str] = typer.Option(None, "--path", "-p", help="Base directory to search in"),
            include_hidden: bool = typer.Option(False, "--hidden", help="Include hidden files/directories"),
        ) -> None:
            asyncio.run(self._run(pattern, path, include_hidden))

    async def _run(self, pattern: str, path: Optional[str], include_hidden: bool) -> None:
        tool = GlobTool()
        result = await tool.execute(pattern=pattern, path=path, include_hidden=include_hidden)

        if result.success:
            console.print()
            count = result.data.get("count", 0) if result.data else 0
            console.print(f"[bold]Found {count} file(s):[/bold]")
            console.print()
            if result.content:
                for line in result.content.splitlines():
                    console.print(f"  - [cyan]{line}[/cyan]")
            console.print()
        else:
            console.print(f"[red]Error:[/red] {result.error}")
            console.print()
            raise typer.Exit(1)


class ToolGrepCommand(Command):
    """Search file contents using GrepTool."""

    name = "grep"
    help = "Search file contents using regular expressions"
    group = "tools"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def grep_files(
            pattern: str = typer.Argument(..., help="Regular expression pattern to search for"),
            path: Optional[str] = typer.Option(None, "--path", "-p", help="File or directory to search"),
            glob: Optional[str] = typer.Option(None, "--glob", "-g", help="Glob pattern to filter files (e.g., '*.py')"),
            output_mode: str = typer.Option("content", "--output", "-o", help="Output mode: content, files_with_matches, or count"),
            context: int = typer.Option(0, "--context", "-C", help="Number of context lines to show"),
            case_insensitive: bool = typer.Option(False, "--ignore-case", "-i", help="Case-insensitive search"),
            multiline: bool = typer.Option(False, "--multiline", "-m", help="Enable multiline matching"),
        ) -> None:
            asyncio.run(self._run(pattern, path, glob, output_mode, context, case_insensitive, multiline))

    async def _run(self, pattern: str, path: Optional[str], glob: Optional[str], output_mode: str, context: int, case_insensitive: bool, multiline: bool) -> None:
        tool = GrepTool()
        result = await tool.execute(
            pattern=pattern,
            path=path,
            glob=glob,
            output_mode=output_mode,
            context=context,
            case_insensitive=case_insensitive,
            multiline=multiline,
        )

        if result.success:
            console.print()
            console.print(result.content)
            console.print()
        else:
            console.print(f"[red]Error:[/red] {result.error}")
            console.print()
            raise typer.Exit(1)


class ToolBashCommand(Command):
    """Execute a shell command using BashTool."""

    name = "bash"
    help = "Execute a shell command"
    aliases = ["sh"]
    group = "tools"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def bash_command(
            command: str = typer.Argument(..., help="Shell command to execute"),
            description: Optional[str] = typer.Option(None, "--description", "-d", help="Description of what the command does"),
            timeout: Optional[int] = typer.Option(120000, "--timeout", "-t", help="Timeout in milliseconds"),
            working_dir: Optional[str] = typer.Option(None, "--cwd", help="Working directory for the command"),
        ) -> None:
            asyncio.run(self._run(command, description, timeout, working_dir))

    async def _run(self, command: str, description: Optional[str], timeout: Optional[int], working_dir: Optional[str]) -> None:
        tool = BashTool()
        result = await tool.execute(
            command=command,
            description=description,
            timeout=timeout,
            working_dir=working_dir,
        )

        if result.success:
            console.print()
            if result.content:
                console.print(Panel(result.content, border_style="green"))
                console.print()
        else:
            console.print(f"[red]Error:[/red] {result.error}")
            console.print()
            raise typer.Exit(1)
