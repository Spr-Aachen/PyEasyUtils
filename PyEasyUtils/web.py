import os
import platform
import requests
import urllib
import hashlib
import json
from tqdm import tqdm
from packaging import version
from github import Github
from pathlib import Path
from enum import Enum
from typing import Union, Optional, Tuple

from .utils import toIterable
from .path import normPath
from .cmd import runCMD

#############################################################################################################

class requestManager(Enum):
    """
    Manage request
    """
    Post = 0
    Get = 1
    #Head = 2

    def request(self,
        protocol: str = "http",
        host: str = "127.0.0.1",
        port: int = 8080,
        pathParams: Union[str, list[str], None] = None,
        queryParams: Union[str, list[str], None] = None,
        headers: Optional[dict] = None,
        data: Union[dict, json.JSONEncoder, None] = None,
        **kwargs
    ):
        pathParams = "/".join(toIterable(pathParams) if pathParams else [])
        queryParams = "&".join(toIterable(queryParams) if queryParams else [])
        if self == self.Post:
            reqMethod = 'POST'
        if self == self.Get:
            reqMethod = 'GET'
        response = requests.request(
            method = reqMethod,
            url = f"{protocol}://{host}:{port}"
            + (f"/{pathParams}" if len(pathParams) > 0 else "")
            + (f"?{queryParams}" if len(queryParams) > 0 else ""),
            headers = headers,
            data = data if isinstance(data, json.JSONDecoder) else (json.dumps(data) if data is not None else None),
            **kwargs
        )
        #assert response.status_code == 200
        return response


def isConnected(
    protocol: str,
    host: str,
    port: int,
):
    """
    Check connection
    """
    try:
        response = requestManager.Get.request(protocol, host, port)
        return True
    except requests.ConnectionError as e:
        print(f"Connection error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def simpleRequest(
    reqMethod: requestManager,
    protocol: str,
    host: str,
    port: int,
    pathParams: Union[str, list[str], None] = None,
    queryParams: Union[str, list[str], None] = None,
    headers: Optional[dict] = None,
    data: Union[dict, json.JSONEncoder, None] = None,
    *keys
):
    if not isConnected(protocol, host, port):
        return
    maxRetries = 3
    for attempt in range(maxRetries):
        try:
            response = reqMethod.request(protocol, host, port, pathParams, queryParams, headers, data)
            encodedResponse = response.json()
            result = (encodedResponse.get(key, {}) for key in keys) if keys else encodedResponse
            return result
        except requests.ConnectionError as e:
            print(f"Attempt {attempt + 1} failed. Retrying..." if attempt != maxRetries - 1 else f"Connection error after {maxRetries} attempts: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

#############################################################################################################

def _download(
    downloadURL: str,
    downloadPath: str,
):
    with urllib.request.urlopen(downloadURL) as source, open(downloadPath, mode = "wb") as output:
        totalLength = int(source.info().get("content-Length"))
        while True:
            buffer = source.read(8192)
            if not buffer:
                break
            output.write(buffer)
            yield len(buffer), totalLength


def _download_aria(
    downloadURL: str,
    downloadPath: str,
    createNewConsole: bool = False
):
    runCMD(
        args = [
            'aria2c',
            f'''
            {('cmd.exe /c start ' if platform.system() == 'Windows' else 'x-terminal-emulator -e ') if createNewConsole else ''}
            aria2c "{downloadURL}" --dir="{Path(downloadPath).parent.as_posix()}" --out="{Path(downloadPath).name}" -x6 -s6 --file-allocation=none --force-save=false
            '''
        ]
    )


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
    fileBytes = None
    isDownloadNeeded = True

    downloadName = fileName + (fileFormat if '.' in fileFormat else f'.{fileFormat}')
    downloadPath = normPath(Path(downloadDir).joinpath(downloadName).absolute())

    if Path(downloadPath).exists():
        if Path(downloadPath).is_file() and sha is not None:
            with open(downloadPath, mode = "rb") as f:
                fileBytes = f.read()
            if len(sha) == 40:
                SHA_Current = hashlib.sha1(fileBytes).hexdigest()
            if len(sha) == 64:
                SHA_Current = hashlib.sha256(fileBytes).hexdigest()
            isDownloadNeeded = True if SHA_Current != sha else False
        else:
            os.remove(downloadPath)
            os.makedirs(downloadDir, exist_ok = True)

    if isDownloadNeeded:
        try:
            _download_aria(downloadURL, downloadPath, createNewConsole)
        except:
            iter(_download(downloadURL, downloadPath))
        finally:
            fileBytes = open(downloadPath, mode = "rb").read() if Path(downloadPath).exists() else None

    if fileBytes is None:
        raise Exception('Download Failed!')

    return fileBytes, downloadPath

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