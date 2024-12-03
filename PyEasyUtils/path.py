import os
import sys
import platform
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

def getPaths(
    directory: str,
    name: str,
    searchKeyword: bool = True
):
    """
    Get all paths of files and folders in directory
    """
    Result = []

    for DirPath, FolderNames, fileNames in os.walk(directory):
        for FolderName in FolderNames:
            if name == FolderName or (name in FolderName and searchKeyword is True):
                Result.append(os.path.join(DirPath, FolderName))
            else:
                pass
        for fileName in fileNames:
            if name == fileName or (name in fileName and searchKeyword is True):
                Result.append(os.path.join(DirPath, fileName))
            else:
                pass

    return Result if len(Result) > 0 else None

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
        BaseDir = normPath(Path(str(filePath)).absolute().parents[parentLevel if parentLevel is not None else 0])
    elif searchMEIPASS and getattr(sys, 'frozen', None):
        BaseDir = normPath(sys._MEIPASS)
    else:
        BaseDir = None

    return BaseDir


def getFileInfo(
    file: Optional[str] = None
):
    """
    Check whether python file is compiled
    """
    if file is None:
        fileName = Path(sys.argv[0]).name
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
    ParentDirectory, name = os.path.split(pathStr)
    suffix = Path(name).suffix
    if len(suffix) > 0:
        while Path(pathStr).exists():
            pattern = r'(\d+)\)\.'
            if re.search(pattern, name) is None:
                name = name.replace('.', '(0).')
            else:
                CurrentNumber = int(re.findall(pattern, name)[-1])
                name = name.replace(f'({CurrentNumber}).', f'({CurrentNumber + 1}).')
            pathStr = Path(ParentDirectory).joinpath(name).as_posix()
    else:
        while Path(pathStr).exists():
            pattern = r'(\d+)\)'
            match = re.search(pattern, name)
            if match is None:
                name += '(0)'
            else:
                CurrentNumber = int(match.group(1))
                name = name[:match.start(1)] + f'({CurrentNumber + 1})'
            pathStr = Path(ParentDirectory).joinpath(name).as_posix()
    return pathStr


def cleanDirectory(
    directory: str,
    whiteList: list
):
    """
    Remove all files and folders in directory except those in whiteList
    """
    if os.path.exists(directory):
        for DirPath, Folders, Files in os.walk(directory, topdown = False):
            for file in Files:
                filePath = os.path.join(DirPath, file)
                try:
                    if not any(file in filePath for file in whiteList):
                        os.remove(filePath)
                except:
                    pass
            for Folder in Folders:
                FolderPath = os.path.join(DirPath, Folder)
                try:
                    if not any(Folder in FolderPath for Folder in whiteList):
                        shutil.rmtree(FolderPath)
                except:
                    pass


def moveFiles(
    directory: str,
    destination: str
):
    """
    Move all files and folders in directory to destination
    """
    for DirPath, FolderNames, fileNames in os.walk(directory):
        for FolderName in FolderNames:
            if directory != destination:
                shutil.move(os.path.join(DirPath, FolderName), destination)
        for fileName in fileNames:
            if directory != destination:
                shutil.move(os.path.join(DirPath, fileName), destination)

#############################################################################################################