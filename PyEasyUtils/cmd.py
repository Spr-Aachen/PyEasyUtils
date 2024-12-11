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

        self.Encoding = 'gbk' if platform.system() == 'Windows' else 'utf-8'

    def create(self,
        args: Union[list[Union[list, str]], str],
    ):
        if not self.communicateThroughConsole:
            for Arg in toIterable(args):
                Arg = shlex.split(Arg) if isinstance(Arg, str) else Arg
                self.Subprocess = subprocess.Popen(
                    args = Arg,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE,
                    env = os.environ,
                    creationflags = subprocess.CREATE_NO_WINDOW
                )

        else:
            TotalInput = str()
            for Arg in toIterable(args):
                Arg = shlex.join(Arg) if isinstance(Arg, list) else Arg
                TotalInput += f'{rawString(Arg)}\n'
            self.TotalInput = TotalInput.encode(self.Encoding, errors = 'replace')
            if platform.system() == 'Windows':
                ShellArgs = ['cmd']
            if platform.system() == 'Linux':
                ShellArgs = ['bash', '-c']
            self.Subprocess = subprocess.Popen(
                args = ShellArgs,
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                env = os.environ,
                creationflags = subprocess.CREATE_NO_WINDOW
            )

        return self.Subprocess

    def monitor(self,
        showProgress: bool = False,
        decodeResult: Optional[bool] = None,
        logPath: Optional[str] = None
    ):
        if not self.communicateThroughConsole:
            TotalOutput, TotalError = (bytes(), bytes())
            if showProgress:
                Output, Error = (bytes(), bytes())
                for Line in io.TextIOWrapper(self.Subprocess.stdout, encoding = self.Encoding, errors = 'replace'):
                    Output += Line.encode(self.Encoding, errors = 'replace')
                    sys.stdout.write(Line) if sys.stdout is not None else None
                    if logPath is not None:
                        with open(logPath, mode = 'a', encoding = 'utf-8') as Log:
                            Log.write(Line)
                    self.Subprocess.stdout.flush()
                    if self.Subprocess.poll() is not None:
                        break
                for Line in io.TextIOWrapper(self.Subprocess.stderr, encoding = self.Encoding, errors = 'replace'):
                    Error += Line.encode(self.Encoding, errors = 'replace')
                    sys.stderr.write(Line) if sys.stderr is not None else None
                    if logPath is not None:
                        with open(logPath, mode = 'a', encoding = 'utf-8') as Log:
                            Log.write(Line)
            else:
                Output, Error = self.Subprocess.communicate()
                Output, Error = b'' if Output is None else Output, b'' if Error is None else Error
            TotalOutput, TotalError = TotalOutput + Output, TotalError + Error

        else:
            if showProgress:
                TotalOutput, TotalError = (bytes(), bytes())
                self.Subprocess.stdin.write(self.TotalInput)
                self.Subprocess.stdin.close()
                for Line in io.TextIOWrapper(self.Subprocess.stdout, encoding = self.Encoding, errors = 'replace'):
                    TotalOutput += Line.encode(self.Encoding, errors = 'replace')
                    sys.stdout.write(Line) if sys.stdout is not None else None
                    if logPath is not None:
                        with open(logPath, mode = 'a', encoding = 'utf-8') as Log:
                            Log.write(Line)
                    self.Subprocess.stdout.flush()
                    if self.Subprocess.poll() is not None:
                        break
                if self.Subprocess.wait() != 0:
                    TotalError = b"Error occurred, please check the logs for full command output."
            else:
                TotalOutput, TotalError = self.Subprocess.communicate(self.TotalInput)
                TotalOutput, TotalError = b'' if TotalOutput is None else TotalOutput, b'' if TotalError is None else TotalError

        TotalOutput, TotalError = TotalOutput.strip(), TotalError.strip()
        TotalOutput, TotalError = TotalOutput.decode(self.Encoding, errors = 'ignore') if decodeResult else TotalOutput, TotalError.decode(self.Encoding, errors = 'ignore') if decodeResult else TotalError

        return None if TotalOutput in ('', b'') else TotalOutput, None if TotalError in ('', b'') else TotalError, self.Subprocess.returncode


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
    ManageSubprocess = subprocessManager(communicateThroughConsole)
    ManageSubprocess.create(args)
    return ManageSubprocess.monitor(showProgress, decodeResult, logPath)

#############################################################################################################

def runScript(
    commandList: list[str],
    scriptPath: Optional[str]
):
    """
    Run a script with bash or bat
    """
    if platform.system() == 'Linux':
        scriptPath = Path.cwd().joinpath('Bash.sh') if scriptPath is None else normPath(scriptPath)
        with open(scriptPath, 'w') as BashFile:
            Commands = "\n".join(commandList)
            BashFile.write(Commands)
        os.chmod(scriptPath, 0o755) # 给予可执行权限
        subprocess.Popen(['bash', scriptPath])
    if platform.system() == 'Windows':
        scriptPath = Path.cwd().joinpath('Bat.bat') if scriptPath is None else normPath(scriptPath)
        with open(scriptPath, 'w') as BatFile:
            Commands = "\n".join(commandList)
            BatFile.write(Commands)
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
            commandList = [
                '#!/bin/bash',
                f'sleep {delayTime}',
                f'./"{programPath}"' if isFileCompiled else f'python3 "{programPath}"',
                'rm -- "$0"'
            ],
            scriptPath = scriptPath
        )
    if platform.system() == 'Windows':
        _, isFileCompiled = getFileInfo(programPath)
        runScript(
            commandList = [
                '@echo off',
                f'ping 127.0.0.1 -n {delayTime + 1} > nul',
                f'start "Programm Running" "{programPath}"' if isFileCompiled else f'python "{programPath}"',
                'del "%~f0"'
            ],
            scriptPath = scriptPath
        )

#############################################################################################################