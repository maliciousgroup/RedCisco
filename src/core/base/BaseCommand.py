from src.core.base.abstract.AbstractCommand import AbstractCommand
from src.core.registry.CommandRegistry import CommandRegistry


class BaseCommand(AbstractCommand):

    def __init_subclass__(cls, **kwargs) -> None:
        try:
            assert isinstance(cls, type(BaseCommand))
            CommandRegistry(cls)
            super().__init_subclass__(**kwargs)
        except AssertionError:
            pass

    async def execute(self) -> None:
        """
        Base Coroutine that executes the Command logic

        :return: None
        """

    async def main(self) -> None:
        """
        Base Coroutine that starts the Command chain

        :return: None
        """
