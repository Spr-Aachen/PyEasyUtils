import os
import sys
import platform
import io
import shlex
import subprocess
from pathlib import Path
from typing import Union, Optional

from .utils import toIterable
from .path import normPath, getFileInfo
from .text import rawString

#############################################################################################################

class subprocessManager:
    """
    Manage subprocess of commands
    """
    def __init__(self,
        communicateThroughConsole: bool = False
    ):
        self.communicateThroughConsole = communicateThroughConsole

        self.encoding = 'gbk' if platform.system() == 'Windows' else 'utf-8'

    def create(self,
        args: Union[list[Union[list, str]], str],
    ):
        if not self.communicateThroughConsole:
            for arg in toIterable(args):
                arg = shlex.split(arg) if isinstance(arg, str) else arg
                self.subprocess = subprocess.Popen(
                    args = arg,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE,
                    env = os.environ,
                    creationflags = subprocess.CREATE_NO_WINDOW
                )

        else:
            totalInput = str()
            for arg in toIterable(args):
                arg = shlex.join(arg) if isinstance(arg, list) else arg
                totalInput += f'{rawString(arg)}\n'
            self.totalInput = totalInput.encode(self.encoding, errors = 'replace')
            if platform.system() == 'Windows':
                shellArgs = ['cmd']
            if platform.system() == 'Linux':
                shellArgs = ['bash', '-c']
            self.subprocess = subprocess.Popen(
                args = shellArgs,
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                env = os.environ,
                creationflags = subprocess.CREATE_NO_WINDOW
            )

        return self.subprocess

    def monitor(self,
        showProgress: bool = False,
        decodeResult: Optional[bool] = None,
        logPath: Optional[str] = None
    ):
        if not self.communicateThroughConsole:
            totalOutput, totalError = (bytes(), bytes())
            if showProgress:
                output, error = (bytes(), bytes())
                for line in io.TextIOWrapper(self.subprocess.stdout, encoding = self.encoding, errors = 'replace'):
                    output += line.encode(self.encoding, errors = 'replace')
                    sys.stdout.write(line) if sys.stdout is not None else None
                    if logPath is not None:
                        with open(logPath, mode = 'a', encoding = 'utf-8') as Log:
                            Log.write(line)
                    self.subprocess.stdout.flush()
                    if self.subprocess.poll() is not None:
                        break
                for line in io.TextIOWrapper(self.subprocess.stderr, encoding = self.encoding, errors = 'replace'):
                    error += line.encode(self.encoding, errors = 'replace')
                    sys.stderr.write(line) if sys.stderr is not None else None
                    if logPath is not None:
                        with open(logPath, mode = 'a', encoding = 'utf-8') as Log:
                            Log.write(line)
            else:
                output, error = self.subprocess.communicate()
                output, error = b'' if output is None else output, b'' if error is None else error
            totalOutput, totalError = totalOutput + output, totalError + error

        else:
            if showProgress:
                totalOutput, totalError = (bytes(), bytes())
                self.subprocess.stdin.write(self.totalInput)
                self.subprocess.stdin.close()
                for line in io.TextIOWrapper(self.subprocess.stdout, encoding = self.encoding, errors = 'replace'):
                    totalOutput += line.encode(self.encoding, errors = 'replace')
                    sys.stdout.write(line) if sys.stdout is not None else None
                    if logPath is not None:
                        with open(logPath, mode = 'a', encoding = 'utf-8') as Log:
                            Log.write(line)
                    self.subprocess.stdout.flush()
                    if self.subprocess.poll() is not None:
                        break
                if self.subprocess.wait() != 0:
                    totalError = b"error occurred, please check the logs for full command output."
            else:
                totalOutput, totalError = self.subprocess.communicate(self.totalInput)
                totalOutput, totalError = b'' if totalOutput is None else totalOutput, b'' if totalError is None else totalError

        totalOutput, totalError = totalOutput.strip(), totalError.strip()
        totalOutput, totalError = totalOutput.decode(self.encoding, errors = 'ignore') if decodeResult else totalOutput, totalError.decode(self.encoding, errors = 'ignore') if decodeResult else totalError

        return None if totalOutput in ('', b'') else totalOutput, None if totalError in ('', b'') else totalError, self.subprocess.returncode


def runCMD(
    args: Union[list[Union[list, str]], str],
    showProgress: bool = False,
    communicateThroughConsole: bool = False,
    decodeResult: Optional[bool] = None,
    logPath: Optional[str] = None
):
    """
    Run command
    """
    manageSubprocess = subprocessManager(communicateThroughConsole)
    manageSubprocess.create(args)
    return manageSubprocess.monitor(showProgress, decodeResult, logPath)

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