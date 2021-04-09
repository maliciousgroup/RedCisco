from src.core.base.abstract.AbstractConsole import AbstractConsole
from src.core.registry.OptionRegistry import OptionRegistry


class BaseConsole(AbstractConsole):

    @staticmethod
    def __register(_config: str, _registry: OptionRegistry) -> None:
        """
        Class method that will register the Console options

        :return: None
        """

    async def interactive_shell(self) -> None:
        """
        Base Coroutine that will handle user-supplied commands

        :return: None
        """

    async def print_processor(self) -> None:
        """
        Base Coroutine that will handle the print queue

        :return: None
        """

    @staticmethod
    async def shutdown(_loop) -> None:
        """
        Base Coroutine that gracefully shuts down application

        :param _loop: Main Event Loop
        :return: None
        """

    async def main(self) -> None:
        """
        Base Coroutine that starts the event loops

        :return: None
        """
