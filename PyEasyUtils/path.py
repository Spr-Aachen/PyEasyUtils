import os
import sys
import platform
import stat
import re
import shutil
from pathlib import Path
from typing import Union, Optional

#############################################################################################################

def normPath(
    string: Union[str, Path],
    pathType: Optional[str] = None,
    trailingSlash: Optional[bool] = None
):
    """
    Normalize path string
    """
    try:
        if str(string).strip() == '':
            raise
        PathString = Path(string)#.resolve()

    except:
        return None

    else: #if re.search(r':[/\\\\]', str(string)) or re.search(r'\./', str(string)):
        if trailingSlash is None:
            trailingSlash = True if str(string).endswith(('/', '\\')) else False
        if platform.system() == 'Windows' or pathType == 'Win32':
            string = PathString.as_posix().replace(r'/', '\\')
            string += '\\' if trailingSlash else ''
        if platform.system() == 'Linux' or pathType == 'Posix':
            string = PathString.as_posix()
            string += '/' if trailingSlash else ''
        return string

#############################################################################################################

"""
def getPaths(
    directory,
    extensions
):
    matchedFiles = []

    for extension in extensions:
        matchedFiles.extend(Path(directory).glob(f'*{extension}'))

    return matchedFiles
"""


def getPaths(
    directory: str,
    name: str,
    searchKeyword: bool = True
):
    """
    Get all paths of files and folders in directory
    """
    results = []

    for dirPath, folderNames, fileNames in os.walk(directory):
        for folderName in folderNames:
            if name == folderName or (name in folderName and searchKeyword is True):
                results.append(Path(dirPath).joinpath(folderName))
            else:
                pass
        for fileName in fileNames:
            if name == fileName or (name in fileName and searchKeyword is True):
                results.append(Path(dirPath).joinpath(fileName))
            else:
                pass

    return [result.as_posix() for result in results] if len(results) > 0 else None

#############################################################################################################

def getBaseDir(
    filePath: Optional[str] = None,
    parentLevel: Optional[int] = None,
    searchMEIPASS: bool = False
):
    """
    Get the parent directory of file, or get the MEIPASS if file is compiled with pyinstaller
    """
    if filePath is not None:
        baseDir = normPath(Path(str(filePath)).absolute().parents[parentLevel if parentLevel is not None else 0])
    elif searchMEIPASS and getattr(sys, 'frozen', None):
        baseDir = normPath(sys._MEIPASS)
    else:
        baseDir = None

    return baseDir


def getCurrentPath():
    """
    Get the path of the current python file
    """
    return Path(sys.argv[0]).as_posix() #return __file__ if getFileInfo()[1] == False else sys.executable


def getFileInfo(
    file: Optional[str] = None
):
    """
    Check whether python file is compiled
    """
    if file is None:
        fileName = Path(getCurrentPath()).name
        if getattr(sys, 'frozen', None):
            isFileCompiled = True
        else:
            isFileCompiled = False if fileName.endswith('.py') or sys.executable.endswith('python.exe') else True
    else:
        fileName = Path(normPath(file)).name
        isFileCompiled = False if fileName.endswith('.py') else True

    return fileName, isFileCompiled

#############################################################################################################

def renameIfExists(
    pathStr: str
):
    """
    If pathStr already exists, rename it to pathStr(0), pathStr(1), etc.
    """
    parentPath, name = Path(pathStr).parent, Path(pathStr).name
    suffix = Path(name).suffix
    if len(suffix) > 0:
        while Path(pathStr).exists():
            pattern = r'(\d+)\)\.'
            if re.search(pattern, name) is None:
                name = name.replace('.', '(0).')
            else:
                CurrentNumber = int(re.findall(pattern, name)[-1])
                name = name.replace(f'({CurrentNumber}).', f'({CurrentNumber + 1}).')
            pathStr = parentPath.joinpath(name).as_posix()
    else:
        while Path(pathStr).exists():
            pattern = r'(\d+)\)'
            match = re.search(pattern, name)
            if match is None:
                name += '(0)'
            else:
                CurrentNumber = int(match.group(1))
                name = name[:match.start(1)] + f'({CurrentNumber + 1})'
            pathStr = parentPath.joinpath(name).as_posix()
    return pathStr


def rmtree(
    path: str
):
    """
    Remove file or directory tree including read-only files
    """
    shutil.rmtree(
        path,
        onerror = lambda func, path, execinfo: (
            os.chmod(path, stat.S_IWUSR),
            func(path)
        )
    )


def cleanDirectory(
    directory: str,
    whiteList: list
):
    """
    Remove all files and folders in directory except those in whiteList
    """
    if Path(directory).exists():
        for dirPath, folders, files in os.walk(directory, topdown = False):
            for file in files:
                filePath = Path(dirPath).joinpath(file).as_posix()
                try:
                    if not any(file in filePath for file in whiteList):
                        os.remove(filePath)
                except:
                    pass
            for folder in folders:
                FolderPath = Path(dirPath).joinpath(folder).as_posix()
                try:
                    if not any(folder in FolderPath for folder in whiteList):
                        rmtree(FolderPath)
                except:
                    pass


def moveFiles(
    directory: str,
    destination: str
):
    """
    Move all files and folders in directory to destination
    """
    for dirPath, folderNames, fileNames in os.walk(directory):
        for folderName in folderNames:
            if directory != destination:
                shutil.move(Path(dirPath).joinpath(folderName).as_posix(), destination)
        for fileName in fileNames:
            if directory != destination:
                shutil.move(Path(dirPath).joinpath(fileName).as_posix(), destination)

#############################################################################################################