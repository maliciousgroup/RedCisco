import abc


class AbstractConsole(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def interactive_shell(self) -> None:
        """
        Abstract Coroutine that will handle user-supplied commands

        :return: None
        """

    @abc.abstractmethod
    async def print_processor(self) -> None:
        """
        Abstract Coroutine that will handle the print queue

        :return: None
        """

    @staticmethod
    @abc.abstractmethod
    async def shutdown(_loop) -> None:
        """
        Abstract Coroutine that gracefully shuts down application

        :param _loop: Main Event Loop
        :return: None
        """

    @abc.abstractmethod
    async def main(self) -> None:
        """
        Abstract Coroutine that starts the event loops

        :return: None
        """
