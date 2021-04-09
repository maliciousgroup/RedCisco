global_command_registry: dict = {}


class CommandRegistry(object):

    def __init__(self, cls):
        """
        Class 'Constructor-Like' Initializer

        :param cls: Command
        """
        if cls.__name__ not in global_command_registry:
            global_command_registry[cls.__name__] = cls
