import os
import platform
import hashlib
import urllib
import requests
from tqdm import tqdm
from packaging import version
from github import Github
from pathlib import Path
from typing import Union, Optional, Tuple

from .path import normPath
from .cmd import runCMD

#############################################################################################################

def isConnected(
    host: str,
    port: int,
):
    """
    Check connection
    """
    try:
        response = requests.get(
            url = f"http://{host}:{port}/"
        )
        return True
    except Exception as e:
        print(e)
        return False

#############################################################################################################

def downloadFile(
    downloadURL: str,
    downloadDir: str,
    fileName: str,
    fileFormat: str,
    sha: Optional[str],
    createNewConsole: bool = False
) -> Tuple[Union[bytes, str], str]:
    """
    Downloads a file from a given URL and saves it to a specified directory
    """
    os.makedirs(downloadDir, exist_ok = True)

    downloadName = fileName + (fileFormat if '.' in fileFormat else f'.{fileFormat}')
    downloadPath = normPath(Path(downloadDir).joinpath(downloadName).absolute())

    def Download():
        try:
            runCMD(
                args = [
                    'aria2c',
                    f'''
                    {('cmd.exe /c start ' if platform.system() == 'Windows' else 'x-terminal-emulator -e ') if createNewConsole else ''}
                    aria2c "{downloadURL}" --dir="{Path(downloadPath).parent.as_posix()}" --out="{Path(downloadPath).name}" -x6 -s6 --file-allocation=none --force-save=false
                    '''
                ]
            )
        except:
            with urllib.request.urlopen(downloadURL) as source, open(downloadPath, "wb") as output:
                with tqdm(total = int(source.info().get("content-Length")), ncols = 80, unit = 'iB', unit_scale = True, unit_divisor = 1024) as loop:
                    while True:
                        buffer = source.read(8192)
                        if not buffer:
                            break
                        output.write(buffer)
                        loop.update(len(buffer))
        finally:
            return open(downloadPath, "rb").read() if Path(downloadPath).exists() else None

    if os.path.exists(downloadPath):
        if os.path.isfile(downloadPath) == False:
            raise RuntimeError(f"{downloadPath} exists and is not a regular file")
        elif sha is not None:
            with open(downloadPath, "rb") as f:
                FileBytes = f.read()
            if len(sha) == 40:
                SHA_Current = hashlib.sha1(FileBytes).hexdigest()
            if len(sha) == 64:
                SHA_Current = hashlib.sha256(FileBytes).hexdigest()
            FileBytes = Download() if SHA_Current != sha else FileBytes #Download() if SHA_Current != sha else None
        else:
            os.remove(downloadPath)
            FileBytes = Download()
    else:
        FileBytes = Download()

    if FileBytes is None:
        raise Exception('Download Failed!')

    return FileBytes, downloadPath

#############################################################################################################

def checkUpdateFromGithub(
    repoOwner: str = ...,
    repoName: str = ...,
    fileName: str = ...,
    fileFormat: str = ...,
    currentVersion: str = ...,
    accessToken: Optional[str] = None,
):
    """
    Check if there is an update available on Github
    """
    try:
        PersonalGit = Github(accessToken)
        Repo = PersonalGit.get_repo(f"{repoOwner}/{repoName}")
        latestVersion = Repo.get_tags()[0].name
        latestRelease = Repo.get_latest_release() #latestRelease = Repo.get_release(latestVersion)
        for Index, Asset in enumerate(latestRelease.assets):
            if Asset.name == f"{fileName}.{fileFormat}":
                IsUpdateNeeded = True if version.parse(currentVersion) < version.parse(latestVersion) else False
                downloadURL = Asset.browser_download_url #downloadURL = f"https://github.com/{repoOwner}/{repoName}/releases/download/{latestVersion}/{fileName}.{fileFormat}"
                VersionInfo = latestRelease.body
                return IsUpdateNeeded, downloadURL, VersionInfo
            elif Index + 1 == len(latestRelease.assets):
                raise Exception(f"No file found with name {fileName}.{fileFormat} in the latest release")

    except Exception as e:
        print(f"Error occurred while checking for updates: \n{e}")

#############################################################################################################