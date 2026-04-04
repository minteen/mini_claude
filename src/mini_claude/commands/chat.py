"""Chat command for MiniClaude - interactive AI assistant."""

import asyncio
import json
import sys
import traceback
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

from mini_claude.commands.base import Command
from mini_claude.config.settings import settings
from mini_claude.services import (
    Conversation,
    OpenAIClient,
    OpenAIAuthError,
    OpenAIRateLimitError,
    OpenAIServerError,
    OpenAIAPIError,
    get_conversation_manager,
    get_api_key,
)
from mini_claude.services.execution_loop import ExecutionLoop, get_execution_loop
from mini_claude.services.tool_schema_generator import generate_all_tool_schemas

console = Console()


class ChatCommand(Command):
    """Interactive chat with AI assistant."""

    name = "chat"
    help = "Interactive chat with AI assistant"
    aliases = ["c"]
    group = "interactive"

    def register(self, app: typer.Typer) -> None:
        @app.command(name=self.name, help=self.help)
        def chat_command(
            message: Optional[str] = typer.Argument(None, help="Single message to send (one-shot mode)"),
            conversation_id: Optional[str] = typer.Option(None, "--id", "-i", help="Load existing conversation by ID"),
            model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
            system_prompt: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
            stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream responses"),
            tools: bool = typer.Option(True, "--tools/--no-tools", help="Enable/disable tool usage"),
        ) -> None:
            self._run(message, conversation_id, model, system_prompt, stream, tools)

    def _run(
        self,
        message: Optional[str],
        conversation_id: Optional[str],
        model: Optional[str],
        system_prompt: Optional[str],
        stream: bool,
        tools: bool,
    ) -> None:
        """Main chat entry point."""
        # Check API key
        api_key = get_api_key()
        if not api_key:
            console.print()
            console.print(Panel(
                "[red]No API key configured![/red]\n\n"
                "Please run:\n"
                "  [cyan]mini-claude auth login[/cyan]\n"
                "or\n"
                "  [cyan]mini-claude config set api_key <your-key>[/cyan]",
                border_style="red",
            ))
            console.print()
            raise typer.Exit(1)

        # Load or create conversation
        conv: Conversation
        manager = get_conversation_manager()

        if conversation_id:
            conv = manager.load(conversation_id)
            if not conv:
                console.print()
                console.print(f"[red]Conversation not found: {conversation_id}[/red]")
                console.print()
                raise typer.Exit(1)
            console.print()
            console.print(f"[dim]Loaded conversation: {conversation_id}[/dim]")
            console.print()
        else:
            # Create new conversation
            conv = Conversation(
                model=model or settings.model,
                system_prompt=system_prompt or settings.system_prompt,
            )
            # Add system prompt if provided
            if conv.system_prompt:
                conv.add_system_message(conv.system_prompt)

        # Determine mode
        if message:
            # One-shot mode
            asyncio.run(self._one_shot(conv, message, model, stream, tools))
        else:
            # Interactive REPL mode
            asyncio.run(self._repl(conv, model, stream, tools))

    async def _one_shot(
        self,
        conv: Conversation,
        user_message: str,
        model: Optional[str],
        stream: bool,
        tools: bool,
    ) -> None:
        """One-shot chat mode - single question and answer."""
        # Add user message
        conv.add_user_message(user_message)

        # Send to LLM with tools
        if tools:
            await self._response_with_tools(conv, model)
        else:
            if stream:
                await self._stream_response(conv, model)
            else:
                await self._non_stream_response(conv, model)

        # Save conversation
        manager = get_conversation_manager()
        manager.save(conv)
        console.print()
        console.print(f"[dim]Conversation saved: {conv.id}[/dim]")
        console.print()

    async def _repl(
        self,
        conv: Conversation,
        model: Optional[str],
        stream: bool,
        tools: bool,
    ) -> None:
        """Interactive REPL chat mode."""
        console.print()
        console.print(Panel(
            "[bold cyan]MiniClaude Chat[/bold cyan]\n\n"
            f"Type your message and press Enter.\n"
            f"Tools: [{'green' if tools else 'yellow'}]{'ENABLED' if tools else 'DISABLED'}[/{'green' if tools else 'yellow'}]\n"
            "Type [yellow]/help[/yellow] for available commands.\n"
            "Type [yellow]/exit[/yellow] or press [yellow]Ctrl+C[/yellow] to quit.",
            border_style="cyan",
        ))
        console.print()

        # Show existing conversation if any
        if len(conv.messages) > 0:
            self._show_conversation_history(conv)

        manager = get_conversation_manager()

        try:
            while True:
                # Get user input
                try:
                    user_input = Prompt.ask(
                        "[bold cyan]You[/bold cyan]",
                        console=console,
                    )
                except EOFError:
                    console.print()
                    break
                except KeyboardInterrupt:
                    console.print()
                    console.print("[dim]Exiting...[/dim]")
                    break

                if not user_input.strip():
                    continue

                # Check for slash commands
                if user_input.startswith("/"):
                    if await self._handle_slash_command(user_input, conv):
                        continue
                    else:
                        break

                # Add user message
                conv.add_user_message(user_input)

                # Send to LLM
                if tools:
                    await self._response_with_tools(conv, model)
                else:
                    if stream:
                        await self._stream_response(conv, model)
                    else:
                        await self._non_stream_response(conv, model)

                # Save conversation
                manager.save(conv)

        except KeyboardInterrupt:
            console.print()
            console.print("[dim]Exiting...[/dim]")

        console.print()
        console.print(f"[dim]Conversation saved: {conv.id}[/dim]")
        console.print()

    async def _handle_slash_command(self, command: str, conv: Conversation) -> bool:
        """Handle slash commands. Return True to continue, False to exit."""
        cmd = command.lower().strip()

        if cmd in ["/exit", "/quit", "/q"]:
            console.print("[dim]Exiting...[/dim]")
            return False

        elif cmd == "/help":
            self._show_help()
            return True

        elif cmd == "/clear":
            conv.clear()
            console.print("[green]Conversation cleared![/green]")
            console.print()
            return True

        elif cmd.startswith("/load "):
            conv_id = cmd[6:].strip()
            manager = get_conversation_manager()
            loaded_conv = manager.load(conv_id)
            if loaded_conv:
                # Replace current conversation
                conv.messages = loaded_conv.messages
                conv.model = loaded_conv.model
                conv.system_prompt = loaded_conv.system_prompt
                conv.metadata = loaded_conv.metadata
                console.print(f"[green]Loaded conversation: {conv_id}[/green]")
                self._show_conversation_history(conv)
            else:
                console.print(f"[red]Conversation not found: {conv_id}[/red]")
            return True

        elif cmd in ["/save", "/id"]:
            console.print(f"[dim]Conversation ID: {conv.id}[/dim]")
            return True

        elif cmd == "/list":
            self._list_conversations()
            return True

        elif cmd == "/model":
            console.print(f"[dim]Current model: {conv.model or settings.model}[/dim]")
            return True

        elif cmd.startswith("/model "):
            new_model = cmd[7:].strip()
            conv.model = new_model
            console.print(f"[green]Model set to: {new_model}[/green]")
            return True

        else:
            console.print(f"[yellow]Unknown command: {command}[/yellow]")
            console.print("[dim]Type /help for available commands[/dim]")
            console.print()
            return True

    def _show_help(self) -> None:
        """Show help for slash commands."""
        console.print()
        console.print("[bold]Available commands:[/bold]")
        console.print()
        console.print("  [cyan]/help[/cyan]    - Show this help")
        console.print("  [cyan]/clear[/cyan]   - Clear conversation history")
        console.print("  [cyan]/list[/cyan]    - List saved conversations")
        console.print("  [cyan]/load <id>[/cyan] - Load conversation by ID")
        console.print("  [cyan]/save|/id[/cyan] - Show current conversation ID")
        console.print("  [cyan]/model[/cyan]   - Show current model")
        console.print("  [cyan]/model <name>[/cyan] - Change model")
        console.print("  [cyan]/exit|/quit[/cyan] - Exit chat")
        console.print()

    def _list_conversations(self) -> None:
        """List saved conversations."""
        manager = get_conversation_manager()
        conversations = manager.list()

        console.print()
        if not conversations:
            console.print("[yellow]No saved conversations[/yellow]")
            console.print()
            return

        console.print("[bold]Saved conversations:[/bold]")
        console.print()
        for conv in conversations[:10]:
            snippet = conv.get("snippet", "")
            created = conv.get("created_at", "")
            console.print(f"  [cyan]{conv['id'][:16]}...[/cyan] - {snippet} [dim]({created})[/dim]")
        if len(conversations) > 10:
            console.print(f"  [dim]... and {len(conversations) - 10} more[/dim]")
        console.print()

    def _show_conversation_history(self, conv: Conversation) -> None:
        """Show existing conversation history."""
        console.print()
        console.print("[dim]Conversation history:[/dim]")
        console.print()

        for msg in conv.messages:
            if msg.role == "system":
                continue  # Skip system messages
            elif msg.role == "user":
                content = msg.content if isinstance(msg.content, str) else ""
                console.print(f"[bold cyan]You:[/bold cyan] {content}")
            elif msg.role == "assistant":
                content = msg.content if isinstance(msg.content, str) else ""
                md = Markdown(content)
                console.print(Panel(md, title="[bold green]Assistant[/bold green]", border_style="green"))
            elif msg.role == "tool":
                # Show tool result
                content = msg.content if isinstance(msg.content, str) else ""
                console.print(Panel(
                    content,
                    title="[bold yellow]Tool Result[/bold yellow]",
                    border_style="yellow",
                ))
            console.print()

    def _show_error(self, e: Exception) -> None:
        """Show detailed error information."""
        console.print()

        if isinstance(e, OpenAIAuthError):
            console.print(Panel(
                "[red]Authentication Error[/red]\n\n"
                f"{str(e)}\n\n"
                "Please check your API key:\n"
                "  [cyan]mini-claude auth status[/cyan]\n"
                "  [cyan]mini-claude auth login[/cyan]",
                border_style="red",
            ))
        elif isinstance(e, OpenAIRateLimitError):
            console.print(Panel(
                "[yellow]Rate Limit Exceeded[/yellow]\n\n"
                f"{str(e)}\n\n"
                "Please try again later.",
                border_style="yellow",
            ))
        elif isinstance(e, OpenAIServerError):
            console.print(Panel(
                "[red]Server Error[/red]\n\n"
                f"{str(e)}\n\n"
                "The API server is experiencing issues. Please try again later.",
                border_style="red",
            ))
        else:
            console.print(Panel(
                "[red]Error[/red]\n\n"
                f"{str(e)}\n\n"
                "[dim]Stack trace:[/dim]\n"
                f"{traceback.format_exc()}",
                border_style="red",
            ))

        console.print()

    async def _response_with_tools(self, conv: Conversation, model: Optional[str]) -> None:
        """Get response with tool calling support."""
        try:
            # Get available tools
            tools = generate_all_tool_schemas()

            if tools:
                console.print(f"[dim]Available tools: {', '.join([t.function.name for t in tools])}[/dim]")
                console.print()

            # Get execution loop
            loop = get_execution_loop()

            # Track message counts to detect new messages
            initial_message_count = len(conv.messages)

            # Current iteration for display
            current_iteration = 0

            # Setup callbacks for real-time display with structured output
            def on_loop_start() -> None:
                """Called when execution loop starts."""
                console.print()
                console.print(Panel(
                    "[bold cyan]🧠 Starting Agent Reasoning Loop[/bold cyan]",
                    border_style="cyan",
                ))
                console.print()

            def on_thinking(iteration: int) -> None:
                """Called when LLM is thinking (waiting for response)."""
                nonlocal current_iteration
                current_iteration = iteration

                # Show a nice thinking header with iteration count
                console.print()
                console.print(f"[bold magenta]{'='*60}[/bold magenta]")
                console.print(f"[bold magenta]🔄 Step {iteration} - Processing[/bold magenta]")
                console.print(f"[bold magenta]{'='*60}[/bold magenta]")
                console.print()

            def on_thought_content(content: str, has_tool_calls: bool) -> None:
                """Called when LLM's thought content is received."""
                status_text = " (will use tools)" if has_tool_calls else " (final answer)"

                if content and content.strip():
                    # Show the thinking content
                    console.print(Panel(
                        Markdown(content),
                        title=f"[bold magenta]💭 Thought{status_text}[/bold magenta]",
                        border_style="magenta",
                        padding=(1, 1),
                    ))
                    console.print()
                elif has_tool_calls:
                    # When content is empty but there are tool calls, show a decision message
                    console.print(Panel(
                        "The LLM decided to call tools to gather more information.",
                        title=f"[bold magenta]💭 Decision{status_text}[/bold magenta]",
                        border_style="magenta",
                        padding=(1, 1),
                    ))
                    console.print()

            def on_tool_call(tool_calls: list) -> None:
                """Called when LLM decides to call tools."""
                console.print()
                console.print(f"[bold blue]✨ Decision: Calling {len(tool_calls)} tool(s)[/bold blue]")
                console.print()

                for tc_idx, tc in enumerate(tool_calls, 1):
                    tool_name = tc.function.name
                    tool_call_id = tc.id
                    args_str = tc.function.arguments

                    try:
                        # Try to pretty print JSON args
                        args_obj = json.loads(args_str)
                        args_str = json.dumps(args_obj, indent=2, ensure_ascii=False)
                    except (json.JSONDecodeError, Exception):
                        # If parsing fails, just use the original string
                        pass

                    # Show tool call with nice formatting
                    console.print(Panel(
                        args_str,
                        title=f"[bold blue]🔧 Tool {tc_idx}: [cyan]{tool_name}[/cyan][/bold blue]",
                        subtitle=f"[dim]ID: {tool_call_id[:12]}...[/dim]",
                        border_style="blue",
                        padding=(1, 1),
                    ))
                    console.print()

            def on_tool_result(tool_name: str, content: str, is_error: bool, tool_call_id: str) -> None:
                """Called when a tool completes."""
                status_emoji = "❌" if is_error else "✅"
                status_text = "[red]Error[/red]" if is_error else "[green]Success[/green]"
                border_color = "red" if is_error else "green"

                # Truncate long content for display
                display_content = content
                if len(display_content) > 2000:
                    display_content = display_content[:2000] + "\n... [content truncated]"

                console.print(Panel(
                    display_content,
                    title=f"[bold {border_color}]{status_emoji} Result: [cyan]{tool_name}[/cyan] - {status_text}[/bold {border_color}]",
                    subtitle=f"[dim]ID: {tool_call_id[:12]}...[/dim]",
                    border_style=border_color,
                    padding=(1, 1),
                ))
                console.print()

            def on_assistant_message(content: str) -> None:
                """Called when assistant sends a message."""
                pass  # We'll show this at the end

            def on_loop_end(total_tool_calls: int) -> None:
                """Called when execution loop ends."""
                console.print()
                console.print(Panel(
                    f"[bold cyan]✅ Agent Reasoning Complete[/bold cyan]\n\n"
                    f"Total tool calls: [bold]{total_tool_calls}[/bold]\n"
                    f"Total steps: [bold]{current_iteration}[/bold]",
                    border_style="cyan",
                ))
                console.print()

            # Register callbacks
            loop.on_loop_start = on_loop_start
            loop.on_thinking = on_thinking
            loop.on_thought_content = on_thought_content
            loop.on_tool_call = on_tool_call
            loop.on_tool_result = on_tool_result
            loop.on_assistant_message = on_assistant_message
            loop.on_loop_end = on_loop_end

            # Show thinking indicator and run conversation
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("Agent is working...", total=None)

                # Run conversation with tools
                final_conv = await loop.run_conversation(
                    conversation=conv,
                    tools=tools,
                    stream=False,
                )

                progress.update(task, description="Done!")

            # Update our conversation reference
            conv.messages = final_conv.messages

            # Show final answer if it was not already shown (no tool calls case)
            # Find the last message to check if it's a final answer without tools
            has_tool_calls_in_conversation = False
            last_assistant_content = None

            for msg in conv.messages[initial_message_count:]:
                if msg.role == "assistant":
                    last_assistant_content = msg.content if isinstance(msg.content, str) else ""

            # Check if any tool calls were made
            for msg in conv.messages:
                if msg.role == "tool":
                    has_tool_calls_in_conversation = True
                    break

            # If no tool calls were made and we have a final answer, show it with the final answer header
            if not has_tool_calls_in_conversation and last_assistant_content and not last_assistant_content.startswith("[System]"):
                console.print()
                console.print(Panel(
                    "[bold green]🎯 Final Answer[/bold green]",
                    border_style="green",
                ))
                console.print()
                md = Markdown(last_assistant_content)
                console.print(Panel(
                    md,
                    title="[bold green]🤖 Assistant[/bold green]",
                    border_style="green",
                ))
                console.print()

        except Exception as e:
            self._show_error(e)

    async def _stream_response(self, conv: Conversation, model: Optional[str]) -> None:
        """Stream response from LLM with live updates."""
        try:
            async with OpenAIClient() as client:
                console.print()
                console.print("[bold green]Assistant:[/bold green] ", end="")

                full_response = ""
                with Live("", console=console, refresh_per_second=10) as live:
                    async for chunk in client.create_chat_completion_stream(
                        model=model or conv.model or settings.model,
                        messages=conv.get_messages_for_api(),
                        max_completion_tokens=1024,
                    ):
                        if chunk.choices and len(chunk.choices) > 0:
                            delta = chunk.choices[0].delta
                            if delta.content:
                                full_response += delta.content
                                live.update(full_response)

            # Add assistant response to conversation
            if full_response:
                conv.add_assistant_message(full_response)
            console.print()

        except Exception as e:
            self._show_error(e)

    async def _non_stream_response(self, conv: Conversation, model: Optional[str]) -> None:
        """Get non-streamed response from LLM."""
        try:
            with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                async with OpenAIClient() as client:
                    response = await client.create_chat_completion(
                        model=model or conv.model or settings.model,
                        messages=conv.get_messages_for_api(),
                        max_completion_tokens=1024,
                    )

            message = response.choices[0].message
            content = message.content or ""

            # Show response
            console.print()
            md = Markdown(content)
            console.print(Panel(md, title="[bold green]Assistant[/bold green]", border_style="green"))
            console.print()

            # Add assistant response to conversation
            conv.add_assistant_message(content)

        except Exception as e:
            self._show_error(e)
