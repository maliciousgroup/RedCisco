import asyncio

from src.core.base.BaseCommand import BaseCommand
from src.core.registry.OptionRegistry import OptionRegistry


class SetCommand(BaseCommand):

    helper = {
        'name': 'set',
        'help': 'This command will set an option value',
        'usage': 'set'
    }

    def __init__(self, command: str, print_queue: asyncio.Queue):
        """
        Class "initializer"

        :param command: User-supplied input
        :param print_queue: None
        """
        super().__init__()
        self.command: str = command
        self.pq: asyncio.Queue = print_queue
        self.options: OptionRegistry = OptionRegistry()

    async def main(self) -> None:
        """
        Coroutine that starts command logic

        :returns: None
        """
        await self.execute()

    async def execute(self) -> None:
        """
        Coroutine that handles any execution logic

        :returns: None
        """
        if len(self.command.split()) < 3:
            return

        _parts: list = self.command.split()

        # Fix user input styles when setting option values
        if _parts[2] == '=':
            _parts.remove('=')
        if _parts[2] == '\"\"':
            _parts[2] = ''
        _, key, *value = tuple(_parts)

        if key in self.options.get_registry_pairs().keys():
            await self.pq.put(self.options.set_register_value(key, ' '.join(value)))
