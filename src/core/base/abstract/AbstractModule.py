import abc


class AbstractModule(metaclass=abc.ABCMeta):

    async def module_shell(self) -> None:
        """
        Abstract Coroutine that will spawn a sub-shell for module

        :return:
        """

    async def execute(self) -> None:
        """
        Abstract Coroutine that will execute the module logic

        :return:
        """

    async def main(self) -> None:
        """
        Abstract Coroutine that bootstraps the module execution

        :return:
        """
