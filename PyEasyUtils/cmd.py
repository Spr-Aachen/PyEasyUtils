import os
import sys
import platform
import shlex
import subprocess
import asyncio
from pathlib import Path
from typing import Union, Optional, List

from .utils import toIterable
from .path import normPath, getFileInfo
from .text import getSystemEncoding

#############################################################################################################

class asyncSubprocessManager:
    """
    Manage subprocess of commands (async version)
    """
    def __init__(self,
        shell: bool = False,
        encoding: Optional[str] = None,
    ):
        self.shell = shell
        self.encoding = encoding or getSystemEncoding()

        self.subprocesses: List[asyncio.subprocess.Process] = []

        self.isWindowsSystem = platform.system() == 'Windows'
        #asyncio.set_event_loop(asyncio.ProactorEventLoop()) if self.isWindowsSystem and isinstance(asyncio.get_event_loop(), asyncio.SelectorEventLoop) else None

    async def _create(self, arg: Union[List[str], str], merge: bool, env: Optional[os._Environ] = None):
        if self.shell == False:
            arg = shlex.split(arg) if isinstance(arg, str) else arg
            process = await asyncio.create_subprocess_exec(
                *arg,
                stdout = asyncio.subprocess.PIPE,
                stderr = asyncio.subprocess.STDOUT,
                env = os.environ,
                creationflags = subprocess.CREATE_NO_WINDOW if self.isWindowsSystem else 0,
                text = False,
            )
        else:
            arg = shlex.join(arg) if isinstance(arg, list) else arg
            argBuffer = (f'{arg}\n' if not arg.endswith('\n') else arg).encode(self.encoding)
            if platform.system() == 'Windows':
                shellArgs = ['cmd']
            if platform.system() == 'Linux':
                shellArgs = ['bash', '-s']
            process = await asyncio.create_subprocess_exec(
                *shellArgs,
                stdin = asyncio.subprocess.PIPE,
                stdout = asyncio.subprocess.PIPE,
                stderr = asyncio.subprocess.STDOUT,
                env = env,
                creationflags = subprocess.CREATE_NO_WINDOW if self.isWindowsSystem else 0,
                text = False,
            ) if self.subprocesses.__len__() == 0 or not merge else self.subprocesses[-1]
            process.stdin.write(argBuffer)
            await process.stdin.drain()
        self.subprocesses.append(process)

    async def create(self, args: Union[list[Union[list, str]], str], merge: bool = True, env: Optional[os._Environ] = None):
        for arg in toIterable(args):
            await self._create(arg, merge, env)
            process = self.subprocesses[-1]
            if self.shell == False:
                pass
            else:
                process.stdin.close() if (merge and self.subprocesses.__len__() == toIterable(args).__len__()) or not merge else None

    async def _getOutputLines(self, process: asyncio.subprocess.Process, showProgress: bool = True, logPath: Optional[str] = None):
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            yield line
            lineString = line.decode(self.encoding, errors = 'replace')
            sys.stdout.write(lineString) if showProgress and sys.stdout is not None else None
            if logPath is not None:
                with open(logPath, mode = 'a', encoding = 'utf-8') as log:
                    log.write(lineString)
            if process.returncode is not None:
                break

    async def monitor(self, showProgress: bool = True, logPath: Optional[str] = None):
        for process in self.subprocesses:
            async for line in self._getOutputLines(process, showProgress, logPath):
                yield line, b''
            await process.wait()
            if process.returncode != 0:
                yield b'', b"error occurred, please check the logs for full command output."

    async def close(self):
        for process in self.subprocesses:
            try:
                if process.returncode is None:
                    process.terminate()
                    await asyncio.sleep(0.1)
                    if process.returncode is None:
                        process.kill()
                await process.wait()
                if hasattr(process, '_transport') and process._transport:
                    process._transport.close()
            except:
                pass
        self.subprocesses.clear()


class subprocessManager:
    """
    Manage subprocess of commands (synchronous wrapper)
    """
    def __init__(self, shell: bool = False, encoding: Optional[str] = None):
        self._asyncManager = asyncSubprocessManager(shell, encoding)

        self._hasLoop = False

    @property
    def subprocesses(self):
        return self._asyncManager.subprocesses

    @property
    def encoding(self):
        return self._asyncManager.encoding

    def _run_async(self, coro):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._hasLoop = True
        return loop.run_until_complete(coro)

    def create(self, args: Union[List[Union[List, str]], str], merge: bool = True, env: Optional[os._Environ] = None):
        return self._run_async(self._asyncManager.create(args, merge, env))

    def monitor(self, showProgress: bool = True, logPath: Optional[str] = None, realTime: bool = True):
        while realTime:
            try:
                yield self._run_async(self._asyncManager.monitor(showProgress, logPath).__anext__())
            except StopAsyncIteration:
                break
        else:
            async def collect():
                results = []
                async for o, e in self._asyncManager.monitor(showProgress, logPath):
                    results.append((o, e))
                return results
            for o, e in self._run_async(collect()):
                yield o, e

    def close(self):
        self._run_async(self._asyncManager.close()) if self._asyncManager.subprocesses else None
        asyncio.get_event_loop().close() if self._hasLoop else None

    def result(self, decodeResult: Optional[bool] = None, showProgress: bool = True, logPath: Optional[str] = None):
        try:
            output, error = (bytes(), bytes())
            for o, e in self.monitor(showProgress, logPath, realTime = False):
                output += o
                error += e
        finally:
            output, error = output.strip(), error.strip()
            output, error = output.decode(self.encoding, errors = 'ignore') if decodeResult else output, error.decode(self.encoding, errors = 'ignore') if decodeResult else error
            returncode = self.subprocesses[-1].returncode
            self.close()
            return None if output in ('', b'') else output, None if error in ('', b'') else error, returncode


def runCMD(
    args: Union[list[Union[list, str]], str],
    merge: bool = True,
    shell: bool = False,
    env: Optional[os._Environ] = None,
    decodeResult: Optional[bool] = None,
    showProgress: bool = True,
    logPath: Optional[str] = None
):
    """
    Run command
    """
    manageSubprocess = subprocessManager(shell)
    manageSubprocess.create(args, merge, env)
    return manageSubprocess.result(decodeResult, showProgress, logPath)

#############################################################################################################

def mkPyFileCommand(filePath: str, **kwargs):
    args = " ".join([f"--{name} {value}" for name, value in kwargs.items()])
    command = 'python "%s" %s' % (filePath, args)
    return command

#############################################################################################################

def runScript(
    *commands: str,
    scriptPath: Optional[str]
):
    """
    Run a script with bash or bat
    """
    if platform.system() == 'Linux':
        scriptPath = Path.cwd().joinpath('Bash.sh') if scriptPath is None else normPath(scriptPath)
        with open(scriptPath, 'w') as bashFile:
            commands = "\n".join(toIterable(commands))
            bashFile.write(commands)
        os.chmod(scriptPath, 0o755) # 给予可执行权限
        subprocess.Popen(['bash', scriptPath])
    if platform.system() == 'Windows':
        scriptPath = Path.cwd().joinpath('Bat.bat') if scriptPath is None else normPath(scriptPath)
        with open(scriptPath, 'w') as BatFile:
            commands = "\n".join(toIterable(commands))
            BatFile.write(commands)
        subprocess.Popen([scriptPath], creationflags = subprocess.CREATE_NEW_CONSOLE)


def bootWithScript(
    programPath: str = ...,
    delayTime: int = 3,
    scriptPath: Optional[str] = None
):
    """
    Boot the program with a script
    """
    if platform.system() == 'Linux':
        _, isFileCompiled = getFileInfo(programPath)
        runScript(
            '#!/bin/bash',
            f'sleep {delayTime}',
            f'./"{programPath}"' if isFileCompiled else f'python3 "{programPath}"',
            'rm -- "$0"',
            scriptPath = scriptPath
        )
    if platform.system() == 'Windows':
        _, isFileCompiled = getFileInfo(programPath)
        runScript(
            '@echo off',
            f'ping 127.0.0.1 -n {delayTime + 1} > nul',
            f'start "Programm Running" "{programPath}"' if isFileCompiled else f'python "{programPath}"',
            'del "%~f0"',
            scriptPath = scriptPath
        )

#############################################################################################################