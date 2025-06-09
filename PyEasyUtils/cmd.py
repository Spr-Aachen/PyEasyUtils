import os
import sys
import platform
import io
import shlex
import subprocess
from pathlib import Path
from typing import Union, Optional, List

from .utils import toIterable
from .path import normPath, getFileInfo
from .text import rawString

#############################################################################################################

class subprocessManager:
    """
    Manage subprocess of commands
    """
    def __init__(self,
        shell: bool = False,
        encoding: Optional[str] = None,
    ):
        self.shell = shell

        self.subprocesses: List[subprocess.Popen] = []

        self.encoding = encoding or ('gbk' if platform.system() == 'Windows' else 'utf-8')

    def _create(self, arg: Union[List[str], str], merge: bool, env: Optional[os._Environ] = None):
        if self.shell == False:
            arg = shlex.split(arg) if isinstance(arg, str) else arg
            process = subprocess.Popen(
                args = arg,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                env = os.environ,
                creationflags = subprocess.CREATE_NO_WINDOW,
                text = False,
            )
        else:
            arg = shlex.join(arg) if isinstance(arg, list) else arg
            argBuffer = f'{rawString(arg)}\n'.encode(self.encoding, errors = 'replace')
            if platform.system() == 'Windows':
                shellArgs = ['cmd']
            if platform.system() == 'Linux':
                shellArgs = ['bash', '-s']
            process = subprocess.Popen(
                args = shellArgs,
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                env = env,
                creationflags = subprocess.CREATE_NO_WINDOW,
                text = False,
            ) if self.subprocesses.__len__() == 0 or not merge else self.subprocesses[-1]
            process.stdin.write(argBuffer)
            process.stdin.flush() #process.stdin.close() if not merge else None
        self.subprocesses.append(process)

    def create(self, args: Union[list[Union[list, str]], str], merge: bool = True, env: Optional[os._Environ] = None):
        for arg in toIterable(args):
            self._create(arg, merge, env)
        for process in self.subprocesses:
            process.stdin.close() if process.poll() is not None else None

    def _getOutputLines(self, subprocess: subprocess.Popen, logPath: Optional[str] = None):
        for line in io.TextIOWrapper(subprocess.stdout, encoding = self.encoding, errors = 'replace'):
            sys.stdout.write(line) if sys.stdout is not None else None
            if logPath is not None:
                with open(logPath, mode = 'a', encoding = 'utf-8') as log:
                    log.write(line)
            line = line.encode(self.encoding, errors = 'replace')
            yield line
            subprocess.stdout.flush()
            if subprocess.poll() is not None:
                break

    def monitor(self, logPath: Optional[str] = None):
        for process in self.subprocesses:
            if self.shell == False:
                for line in self._getOutputLines(process, logPath):
                    yield line, b''
            else:
                for line in self._getOutputLines(process, logPath):
                    yield line, b''
                if process.wait() != 0:
                    yield b'', b"error occurred, please check the logs for full command output."

    def result(self,
        decodeResult: Optional[bool] = None,
        logPath: Optional[str] = None
    ):
        output, error = (bytes(), bytes())
        for o, e in self.monitor(logPath):
            output += o
            error += e

        output, error = output.strip(), error.strip()
        output, error = output.decode(self.encoding, errors = 'ignore') if decodeResult else output, error.decode(self.encoding, errors = 'ignore') if decodeResult else error

        return None if output in ('', b'') else output, None if error in ('', b'') else error, self.subprocesses[-1].returncode


def runCMD(
    args: Union[list[Union[list, str]], str],
    merge: bool = True,
    shell: bool = False,
    env: Optional[os._Environ] = None,
    decodeResult: Optional[bool] = None,
    logPath: Optional[str] = None
):
    """
    Run command
    """
    manageSubprocess = subprocessManager(shell, env)
    manageSubprocess.create(args, merge)
    return manageSubprocess.result(decodeResult, logPath)

#############################################################################################################

def mkPyFileCommand(filePath: str, **kwargs):
    pythonExec = sys.executable or "python"
    args = " ".join([f"--{name} {value}" for name, value in kwargs.items()])
    return '"%s" "%s" %s' % (pythonExec, filePath, args)

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