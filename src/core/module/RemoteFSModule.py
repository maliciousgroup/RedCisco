import asyncio
import re

from src.core.base.BaseModule import BaseModule
from src.core.registry.ModuleRegistry import ModuleRegistry
from src.core.registry.OptionRegistry import OptionRegistry
from src.core.registry.ServerRegistry import add_server_instance
from src.core.utility.manage import create_resources
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.styles import Style

prompt_style = Style.from_dict({"prompt": "ansired bold"})


class RemoteFSModule(BaseModule):

    helper = {
        'name': 'remote_fs',
        'help': 'This module will start a remote HTTP file server on DigitalOcean',
        'usage': 'use remote_fs'
    }

    options = {
        'module': {
            'api_token': [
                '',
                'The DigitalOcean API token associated with your account',
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
                    await self.print_queue.put("[Building remote HTTP file server (may take a few minutes)]")
                    await asyncio.sleep(0.1)  # Added to print before processing due to Print task time delay (.002)
                    tasks.append(asyncio.create_task(self.execute()))
                    [await task for task in tasks]
            except (EOFError, KeyboardInterrupt):
                await self.unregister()
                break
            except Exception as e:
                await self.print_queue.put(f"[Uncaught Exception] - {e.__str__()}")
        [task.cancel() for task in tasks]

    async def unregister(self) -> None:
        options: dict = self.option_register.get_register_dict()
        if 'module' in options.keys():
            options.pop('module')
            self.option_register.register_options(options)

    async def execute(self) -> None:
        try:
            api_token: str = self.option_register.get_register_value('api_token')
            template: str = 'src/config/templates'
            var: dict = {'do_api_token': api_token}

            output = create_resources(template, var)
            ip_address = ''.join(re.findall(r'ip_address = ([\w-]\S+)', str(output)))
            if not ip_address:
                raise Exception(f"[Error] - Remote FS failed to launch.  Check API key and DigitalOcean dashboard")

            await self.print_queue.put(f"[HTTP Server] - Started on IP {ip_address} using port 80\n")
            # await asyncio.Event().wait()

        except Exception as e:
            await self.print_queue.put(f"[Uncaught Exception] - {e.__str__()}")
        finally:
            add_server_instance(template, var)
