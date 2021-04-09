global_server_registry: list = []


def add_server_instance(template: str, variables: dict) -> None:
    data = tuple([template, variables])
    if data not in global_server_registry:
        global_server_registry.append(data)


def get_server_instances() -> list:
    return global_server_registry
