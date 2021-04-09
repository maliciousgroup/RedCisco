import asyncio

from src.core.base.BaseCommand import BaseCommand


class ExitCommand(BaseCommand):

    helper = {
        'name': 'exit',
        'help': 'This command will exit the application',
        'usage': 'exit'
    }

    def __init__(self, command: str, print_queue: asyncio.Queue):
        """
        Class 'Constructor-Like' Initializer

        :param command: User-input command
        :param print_queue: Print Queue
        :return None
        """
        super().__init__()
        self.command: str = command
        self.pq: asyncio.Queue = print_queue

    async def main(self) -> None:
        """
        Class Coroutine that starts command logic

        :return: None
        """
        await self.execute()

    async def execute(self) -> None:
        """
        Class Coroutine that starts command execution logic

        :return: None
        """
        raise EOFError
