"""Command Line Interface for Javinizer"""

import click
from javinizer import __version__

# Import commands from submodules
from javinizer.commands.find import find
from javinizer.commands.sort import sort, sort_dir
from javinizer.commands.update import update, update_dir
from javinizer.commands.config import config
from javinizer.commands.thumbs import thumbs
from javinizer.commands.info import info


@click.group()
@click.version_option(version=__version__)
def main():
    """Javinizer - JAV Metadata Scraper (Python Edition)

    A command-line tool to scrape and organize Japanese Adult Video metadata.

    Examples:

        javinizer find IPX-486

        javinizer find IPX-486 --source r18dev,dmm --aggregated

        javinizer find IPX-486 --proxy socks5://127.0.0.1:1080

        javinizer config --proxy socks5://127.0.0.1:1080
    """
    pass


# Register commands
main.add_command(find)
main.add_command(sort)
main.add_command(sort_dir)
main.add_command(update)
main.add_command(update_dir)
main.add_command(config)
main.add_command(thumbs)
main.add_command(info)


if __name__ == "__main__":
    main()
