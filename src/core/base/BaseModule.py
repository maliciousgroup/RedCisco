from src.core.registry.ModuleRegistry import ModuleRegistry
from src.core.base.abstract.AbstractModule import AbstractModule


class BaseModule(AbstractModule):

    def __init_subclass__(cls, **kwargs):
        try:
            assert isinstance(cls, type(BaseModule))
            ModuleRegistry().register_module(cls)
            super().__init_subclass__(**kwargs)
        except AssertionError:
            pass

    async def module_shell(self) -> None:
        pass

    async def execute(self) -> None:
        pass

    async def main(self) -> None:
        pass
