import abc


class AbstractCommand(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def execute(self) -> None:
        """
        Abstract Coroutine that executes the Command logic

        :return: None
        """

    @abc.abstractmethod
    async def main(self) -> None:
        """
        Abstract Coroutine that starts the Command logic chain

        :return: None
        """
