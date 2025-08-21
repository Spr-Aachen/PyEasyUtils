import os
import platform
import socket
import requests
import urllib
import hashlib
import json
from tqdm import tqdm
from packaging import version
from github import Github
from pathlib import Path
from enum import Enum
from typing import Union, Optional, Tuple, Any

from .utils import toIterable
from .path import normPath
from .text import getSystemEncoding
from .cmd import runCMD

#############################################################################################################

def isPortAvailable(port: int, host: str = '127.0.0.1', protocol: str = 'tcp'):
    """
    Check whether port is available
    """
    if protocol == 'tcp':
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    elif protocol == 'udp':
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    else:
        raise ValueError("Protocol must be 'tcp' or 'udp'")
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
        sock.close()
        return True
    except (socket.error, OSError):
        return False


def findAvailablePorts(port_range: tuple, host: str = '127.0.0.1', protocol: str = 'tcp'):
    """
    Find available ports
    """
    available_ports = []
    port_range = (port_range, port_range + 1) if isinstance(port_range, int) else (port_range[0], port_range[1] + 1)
    for port in range(*port_range):
        if isPortAvailable(port, host, protocol):
                available_ports.append(port)
    return available_ports


def freePort(port: int):
    """
    Free port
    """
    if isPortAvailable(port):
        return
    netStat = runCMD('netstat -aon|findstr "%s"' % port)
    for line in str(netStat).splitlines():
        line = line.strip()
        runCMD(f'taskkill /T /F /PID {line.split(" ")[-1]}') if line.startswith("TCP") else None

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
        data: Any = None,
        stream: bool = False,
        **kwargs
    ):
        pathParams = "/".join([str(pathParam) for pathParam in toIterable(pathParams)] if pathParams else [])
        queryParams = "&".join([str(queryParam) for queryParam in toIterable(queryParams)] if queryParams else [])
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
            data = data if isinstance(data, str) else (json.dumps(data) if data is not None else None),
            stream = stream,
            **kwargs
        )
        #assert response.status_code == 200
        return response


def simpleRequest(
    reqMethod: requestManager,
    protocol: str,
    host: str,
    port: int,
    pathParams: Union[str, list[str], None] = None,
    queryParams: Union[str, list[str], None] = None,
    headers: Optional[dict] = None,
    data: Any = None,
    stream: bool = False,
    *keys
):
    with reqMethod.request(protocol, host, port, pathParams, queryParams, headers, data, stream) as response:
        encodedResponse = response.json()
        result = tuple([encodedResponse.get(key, {}) for key in keys]) if keys else encodedResponse
        return result


def responseParser(
    response: requests.Response,
    stream: bool = False,
    decodeUnicode: bool = False,
    encoding: Optional[str] = None,
    #isJSON: bool = False,
):
    if response.status_code != 200:
        print("Warning: status code is not 200")
    for chunk in response.iter_content(chunk_size = 1024 if stream else None, decode_unicode = False):
        if chunk:
            content = chunk.decode(encoding or getSystemEncoding(), errors = 'replace') if decodeUnicode and isinstance(chunk, bytes) else chunk
            '''
            try:
                parsed_content = json_repair.loads(content) if isJSON else content
                yield parsed_content, response.status_code
            except:
                print("Broken content:", content)
                continue
            '''
            yield content, response.status_code

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