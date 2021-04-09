"""
import asyncio

from src.core.base.BaseCommand import BaseCommand
from src.core.registry.OptionRegistry import OptionRegistry


class RunCommand(BaseCommand):

    helper = {
        'name': 'run',
        'help': 'This command will start the connection process',
        'usage': 'run'
    }

    def __init__(self, command: str, print_queue: asyncio.Queue):
        super().__init__()
        self.command: str = command
        self.print_queue: asyncio.Queue = print_queue
        self.options: OptionRegistry = OptionRegistry()
        self.end_points: list = []

    async def main(self) -> None:

        await self.execute()

    async def execute(self) -> None:

        _options: dict = self.options.get_registry_pairs()
"""