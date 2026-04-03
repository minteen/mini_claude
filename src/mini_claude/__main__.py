"""MiniClaude CLI entry point."""

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from mini_claude import __version__
from mini_claude.commands import (
    HelpCommand,
    ConfigCommandGroup,
    AuthCommandGroup,
    ChatCommand,
    ToolCommandGroup,
)

# Initialize Typer app
app = typer.Typer(
    name="mini-claude",
    help="A lightweight Claude Code CLI implementation in Python",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"MiniClaude version: [bold cyan]{__version__}[/bold cyan]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """MiniClaude - A lightweight Claude Code CLI implementation."""
    pass


# Register commands manually (for reliable discovery)
HelpCommand().register(app)
ConfigCommandGroup().register(app)
AuthCommandGroup().register(app)
ChatCommand().register(app)
ToolCommandGroup().register(app)


@app.command(name="hello")
def hello(name: Optional[str] = typer.Argument(None, help="Name to greet")) -> None:
    """Say hello!"""
    if name:
        message = f"Hello, [bold green]{name}[/bold green]!"
    else:
        message = "Hello from MiniClaude!"

    console.print(
        Panel(
            message,
            title="[bold cyan]MiniClaude[/bold cyan]",
            border_style="cyan",
        )
    )


@app.command(name="info")
def info() -> None:
    """Show MiniClaude information."""
    from mini_claude.config.settings import settings

    console.print(f"[bold]Version:[/bold] {__version__}")
    console.print(f"[bold]Config directory:[/bold] {settings.config_dir}")
    console.print(f"[bold]Data directory:[/bold] {settings.data_dir}")
    console.print(f"[bold]Default model:[/bold] {settings.model}")


@app.command(name="test-tools")
def test_tools() -> None:
    """Test the basic tools."""
    import asyncio
    from pathlib import Path
    from rich.panel import Panel

    from mini_claude.tools import (
        ReadTool,
        WriteTool,
        EditTool,
        GlobTool,
        GrepTool,
        BashTool,
    )

    async def run_tests() -> None:
        test_file = Path("test_temp.txt")

        console.print("\n[bold cyan]=== Testing Tools ===[/bold cyan]\n")

        # Test 1: Write
        console.print("[bold]1. Testing WriteTool...[/bold]")
        write_tool = WriteTool()
        result = await write_tool.execute(
            file_path=str(test_file),
            content="Hello World!\nLine 2\nLine 3\nLine 4\nLine 5\n",
        )
        if result.success:
            console.print(f"  [green]✓[/green] {result.content}")
        else:
            console.print(f"  [red]✗[/red] {result.error}")
            return

        # Test 2: Read
        console.print("\n[bold]2. Testing ReadTool...[/bold]")
        read_tool = ReadTool()
        result = await read_tool.execute(file_path=str(test_file), offset=2, limit=3)
        if result.success:
            console.print(f"  [green]✓[/green] Read successful:")
            console.print(Panel(result.content.strip(), border_style="dim"))
        else:
            console.print(f"  [red]✗[/red] {result.error}")

        # Test 3: Edit
        console.print("\n[bold]3. Testing EditTool...[/bold]")
        edit_tool = EditTool()
        result = await edit_tool.execute(
            file_path=str(test_file),
            old_string="Hello World!",
            new_string="Hello MiniClaude!",
        )
        if result.success:
            console.print(f"  [green]✓[/green] {result.content}")
        else:
            console.print(f"  [red]✗[/red] {result.error}")

        # Test 4: Glob
        console.print("\n[bold]4. Testing GlobTool...[/bold]")
        glob_tool = GlobTool()
        result = await glob_tool.execute(pattern="*.md")
        if result.success:
            console.print(f"  [green]✓[/green] Found {result.data['count'] if result.data else 0} files:")
            for f in result.content.splitlines()[:5]:
                console.print(f"    - {f}")
            if len(result.content.splitlines()) > 5:
                console.print(f"    ... and {len(result.content.splitlines()) - 5} more")
        else:
            console.print(f"  [red]✗[/red] {result.error}")

        # Test 5: Grep
        console.print("\n[bold]5. Testing GrepTool...[/bold]")
        grep_tool = GrepTool()
        result = await grep_tool.execute(pattern="class.*Tool", glob="**/*.py", output_mode="count")
        if result.success:
            console.print(f"  [green]✓[/green] {result.content}")
        else:
            console.print(f"  [red]✗[/red] {result.error}")

        # Test 6: Bash
        console.print("\n[bold]6. Testing BashTool...[/bold]")
        bash_tool = BashTool()
        cmd = "echo Hello from Shell"
        result = await bash_tool.execute(command=cmd, description="Test shell command")
        if result.success:
            console.print(f"  [green]✓[/green] Command output:")
            console.print(Panel(result.content.strip(), border_style="dim"))
        else:
            console.print(f"  [red]✗[/red] {result.error}")

        # Cleanup
        test_file.unlink(missing_ok=True)
        console.print("\n[bold green]✓ All tests completed! [/bold green]\n")

    asyncio.run(run_tests())


def run() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    run()
