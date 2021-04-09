module_registry: dict = {}


class ModuleRegistry(object):

    @staticmethod
    def register_module(cls) -> None:
        if cls.__name__ not in module_registry:
            module_registry[cls.__name__] = cls

    @staticmethod
    def dump_register() -> dict:
        return module_registry
