import asyncio

from src.core.utility.colors import colors
from src.core.utility.tables import create_table

from src.core.base.BaseCommand import BaseCommand
from src.core.registry.OptionRegistry import OptionRegistry

_colors: dict = colors()
red = _colors['red']
reset = _colors['reset']


class OptionsCommand(BaseCommand):

    helper = {
        'name': 'options',
        'help': 'This command prints all available options',
        'usage': 'options'
    }

    def __init__(self, command: str, print_queue: asyncio.Queue):
        """
        Class "initializer"

        :param command: User-supplied input
        :param print_queue: Asynchronous print queue
        """
        super().__init__()
        self.command: str = command
        self.pq: asyncio.Queue = print_queue
        self.registry: OptionRegistry = OptionRegistry()

    async def main(self) -> None:
        """
        Coroutine that starts command logic

        :returns: None
        """
        await self.execute()

    async def execute(self) -> None:
        approved_keys = ['module', 'console']
        options: dict = self.registry.get_register_dict()
        for x in options.keys():
            if x not in approved_keys:
                continue
            if 'module' in options.keys():
                await self.pq.put('')
                await self.pq.put(f"Module Options")
                await self.pq.put(f"==============\n")
                field_names: list = [
                    f"{'Option':<25}",
                    f"{'Setting':<20}",
                    f"{'Description':<30}"
                ]
                field_values: list = []
                for item in options['module'].items():
                    field_values.append([item[0], item[1][0], item[1][1]])
                output: str = create_table(field_names, field_values)
                await self.pq.put(output)
                await self.pq.put('')
                return

            if 'console' in options.keys():
                await self.pq.put('')
                await self.pq.put(f"Console Options")
                await self.pq.put(f"===============\n")
                field_names: list = [
                    f"{'Option':<25}",
                    f"{'Setting':<20}",
                    f"{'Description':<30}"
                ]
                field_values: list = []
                for item in options['console'].items():
                    field_values.append([item[0], item[1][0], item[1][1]])
                output: str = create_table(field_names, field_values)
                await self.pq.put(output)
                await self.pq.put('')
