import asyncio

from src.core.Console import Console
from src.core.utility.colors import colors

_colors: dict = colors()
red = _colors['red']
reset = _colors['reset']

_prompt: str = 'RedCisco> '
_config: str = 'src/config/config.json'


def heading():
    print(f"""
{red}██████╗ ███████╗██████╗ {reset} ██████╗██╗███████╗ ██████╗ ██████╗ 
{red}██╔══██╗██╔════╝██╔══██╗{reset}██╔════╝██║██╔════╝██╔════╝██╔═══██╗
{red}██████╔╝█████╗  ██║  ██║{reset}██║     ██║███████╗██║     ██║   ██║
{red}██╔══██╗██╔══╝  ██║  ██║{reset}██║     ██║╚════██║██║     ██║   ██║
{red}██║  ██║███████╗██████╔╝{reset}╚██████╗██║███████║╚██████╗╚██████╔╝
{red}╚═╝  ╚═╝╚══════╝╚═════╝ {reset} ╚═════╝╚═╝╚══════╝ ╚═════╝ ╚═════╝ \n
This tool was created to assist offensive operators in compromising
Cisco IOS devices in order to infiltrate their internal networks{reset}

Author:  d3d (@MCoetus)
""")


if __name__ == '__main__':
    import sys

    if sys.platform == 'win32':
        """ Attempting to fix ANSI/VT100 """
        from ctypes import *
        kernel32 = windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    heading()
    console = Console(_config, _prompt)
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(console.main())
    except KeyboardInterrupt:
        pass
    except asyncio.CancelledError:
        pass
