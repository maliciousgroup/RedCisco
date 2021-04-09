from src.core.utility.colors import colors

global_option_registry: dict = {}

_colors: dict = colors()
red = _colors['red']
bold = _colors['bold']
reset = _colors['reset']


class OptionRegistry(object):

    @staticmethod
    def register_options(options: dict) -> None:
        """
        Class method that registers provided options dict

        :param options: options dict
        :return: None
        """
        for a in options:
            options[a] = dict((k.lower(), v) for k, v in options[a].items() for a in options)
            global_option_registry.update(options)

    @staticmethod
    def get_register_dict() -> dict:
        """
        Class function that returns the current global registry as a dict

        :return: dict
        """
        return global_option_registry

    @staticmethod
    def get_registry_pairs() -> dict:
        """
        Class function that returns the current global registry key value pairs

        :return: dict
        """
        pairs: dict = {}
        for ns in global_option_registry:
            pairs.update(global_option_registry[ns])
        return pairs

    @staticmethod
    def get_register_value(key: str) -> str:
        """
        Class method that retrieves the value from provided key

        :param key: dict key
        :return: str
        """
        for a in global_option_registry:
            if key in global_option_registry[a]:
                return global_option_registry[a][key][0]

    @staticmethod
    def set_register_value(key: str, value: str) -> str:
        """
        Class method that sets the value located at provided key

        :param key: dict key
        :param value: new value
        :return: str
        """
        try:
            for a in global_option_registry:
                if key.lower() not in str(global_option_registry[a]).lower():
                    continue
                _required: str = global_option_registry[a][key.lower()][2]
                if not _required:
                    global_option_registry[a][key.lower()][0] = value
                    return f"{key} => {value}\n"
                elif value in _required.replace(' ', '').split(','):
                    global_option_registry[a][key.lower()][0] = value
                    return f"{key} => {value}\n"
                else:
                    _possible = _required.replace(' ', '').split(',')
                    return f"{value} is not in the list of allowed values: {_possible}\n"
        except KeyError:
            pass
