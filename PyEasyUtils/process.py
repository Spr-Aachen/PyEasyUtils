import os
import psutil
import signal
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from enum import Enum
from typing import Union, Optional

from .path import normPath

#############################################################################################################

class taskAccelerationManager(Enum):
    """
    Manage task acceleration
    """
    ThreadPool = 0
    ProcessPool = 1

    def createPool(self, 
        funcDict: dict,
        asynchronous: bool = True,
        maxWorkers: Optional[int] = None
    ) -> Union[ThreadPoolExecutor, ProcessPoolExecutor]:
        if self == self.ThreadPool:
            executor = ThreadPoolExecutor(maxWorkers)
        if self == self.ProcessPool:
            executor = ProcessPoolExecutor(maxWorkers)
        futures = []
        for func, args in funcDict.items():
            try:
                future = executor.submit(func, *args)
                isLastFuture = len(futures) == len(funcDict) - 1
                futures.append(future) if asynchronous or isLastFuture else future.result()
            except Exception as e:
                executor.shutdown(wait = False, cancel_futures = True)
                raise e
        return executor

#############################################################################################################

def processTerminator(
    program: Union[str, int],
    selfIgnored: bool = True,
    searchKeyword: bool = False
):
    """
    Kill a process by its PID or name
    """
    if isinstance(program, int):
        PID = program
        try:
            Process = psutil.Process(PID)
        except psutil.NoSuchProcess: # Process already terminated
            return

        ProcessList =  Process.children(recursive = True) + [Process]
        for Process in ProcessList:
            try:
                if Process.pid == os.getpid() and selfIgnored:
                    continue
                os.kill(Process.pid, signal.SIGTERM)
            except:
                pass

    if isinstance(program, str):
        name = program
        programPath = normPath(name) if normPath(name) is not None else name
        for Process in psutil.process_iter():
            ProcessList =  Process.children(recursive = True) + [Process]
            try:
                for Process in ProcessList:
                    if Process.pid == os.getpid() and selfIgnored:
                        continue
                    ProcessPath = Process.exe()
                    if programPath == ProcessPath or (programPath.lower() in ProcessPath.lower() and searchKeyword):
                        Process.send_signal(signal.SIGTERM) #Process.kill()
            except:
                pass


def occupationTerminator(
    file: str,
    searchKeyword: bool = False
):
    """
    Terminate all processes that are currently using the file
    """
    filePath = normPath(file) if normPath(file) is not None else file
    for Process in psutil.process_iter():
        try:
            PopenFiles = Process.open_files()
            for PopenFile in PopenFiles:
                PopenFilePath = PopenFile.path
                if filePath == PopenFilePath or (filePath.lower() in PopenFilePath.lower() and searchKeyword):
                    Process.send_signal(signal.SIGTERM) #Process.kill()
        except:
            pass

#############################################################################################################