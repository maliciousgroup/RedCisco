import asyncio

from aiohttp import web, http_exceptions
from src.core.base.BaseModule import BaseModule
from src.core.registry.ModuleRegistry import ModuleRegistry
from src.core.registry.OptionRegistry import OptionRegistry
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.styles import Style

prompt_style = Style.from_dict({"prompt": "ansired bold"})


class LocalFSModule(BaseModule):

    helper = {
        'name': 'local_fs',
        'help': 'This module will start a local HTTP file server',
        'usage': 'use local_fs'
    }

    options = {
        'module': {
            'host': [
                '10.10.10.1',
                'The IPv4 Address of the local interface you want to use',
                ''
            ],
            'port': [
                '8080',
                'The port number to use for the local HTTP server',
                ''
            ],
            'root': [
                'C:\\Users\\d3d\\PycharmProjects\\RedTeam\\RedCiscoDev\\src\\file',
                'The directory path containing files to serve via HTTP',
                ''
            ]
        }
    }

    def __init__(self, command: str, print_queue: asyncio.Queue, console: object):
        super().__init__()
        self.command: str = command
        self.console: object = console
        self.print_queue: asyncio.Queue = print_queue
        self.module_register: ModuleRegistry = ModuleRegistry()
        self.option_register: OptionRegistry = OptionRegistry()

    async def main(self) -> None:
        await self.register()
        await self.module_shell()

    async def register(self) -> None:
        self.option_register.register_options(options=self.options)

    async def module_shell(self) -> None:
        session = PromptSession()
        allowed_commands = ['set', 'options', 'run', 'back']
        tasks: list = []
        while True:
            try:
                prompt_text = self.option_register.get_register_value('prompt')
                sub_prompt = f"{prompt_text} [{self.helper['name']}]> "
                data: str = await session.prompt_async(sub_prompt, style=prompt_style)
                if not data or not data.startswith(tuple(allowed_commands)):
                    continue
                if data.startswith(tuple(['back', 'exit'])):
                    raise EOFError
                if data.startswith(tuple(['set', 'options'])):
                    # noinspection PyUnresolvedReferences
                    await self.console.command_interpreter(data)
                if data.startswith(tuple(['run', 'exploit'])):
                    tasks.append(asyncio.create_task(self.execute()))

            except (EOFError, KeyboardInterrupt):
                await self.unregister()
                break
            except http_exceptions.BadStatusLine as e:
                await self.print_queue.put(f"[Warning] - {e.__str__()}")
            except Exception as e:
                print("DERP " + e.__str__())
        [task.cancel() for task in tasks]

    async def unregister(self) -> None:
        options: dict = self.option_register.get_register_dict()
        if 'module' in options.keys():
            options.pop('module')
            self.option_register.register_options(options)

    async def execute(self) -> None:
        try:
            root: str = self.option_register.get_register_value('root')
            port: str = self.option_register.get_register_value('port')
            host: str = self.option_register.get_register_value('host')

            app = web.Application()
            app.router.add_static("/", root, show_index=True)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host=host, port=int(port))
            await site.start()
            await self.print_queue.put(f"[HTTP Server] - Started on IP {host} using port {port}\n")
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if "10048" in e.__str__():
                await self.print_queue.put(f"[HTTP Server] - Server already started on port {port}\n")
