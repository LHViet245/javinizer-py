"""GUI command module"""

import click

from javinizer.cli_common import console


@click.command()
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to")
@click.option("--port", "-p", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def gui(host: str, port: int, reload: bool) -> None:
    """Start the web GUI server (Web Station)
    
    Examples:
    
        javinizer gui
        
        javinizer gui --port 8080
        
        javinizer gui --host 0.0.0.0 --port 8000
    """
    try:
        from javinizer.web.server import run_server
    except ImportError:
        console.print(
            "[red]GUI dependencies not installed.[/]\n"
            "Install with: [cyan]pip install javinizer[gui][/]"
        )
        return

    console.print("[dim]Press Ctrl+C to stop[/]")
    console.print()

    run_server(host=host, port=port, reload=reload)

