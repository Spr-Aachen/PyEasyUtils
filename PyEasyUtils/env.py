import os
import sys
import platform
import re
from packaging import version
from enum import Enum

from .text import rawString
from .path import normPath
from .cmd import runCMD

#############################################################################################################

def isVersionSatisfied(
    currentVersion: str,
    versionReqs: str
):
    """
    Check if the version requirements are satisfied
    """
    if versionReqs is None:
        return True
    versionReqs = versionReqs.split(',') if isinstance(versionReqs, str) else list(versionReqs)
    results = []
    for versionReq in versionReqs:
        splitVersionReq = re.split('!|=|>|<', versionReq)
        requiredVersion = splitVersionReq[-1].strip()
        req = versionReq[:len(versionReq) - len(splitVersionReq[-1])].strip()
        if req == "":
            results.append(version.parse(currentVersion) == version.parse(requiredVersion))
        elif req == "==":
            results.append(version.parse(currentVersion) == version.parse(requiredVersion))
        elif req == "!=":
            results.append(version.parse(currentVersion) != version.parse(requiredVersion))
        elif req == ">=":
            results.append(version.parse(currentVersion) >= version.parse(requiredVersion))
        elif req == "<=":
            results.append(version.parse(currentVersion) <= version.parse(requiredVersion))
        elif req == ">":
            results.append(version.parse(currentVersion) > version.parse(requiredVersion))
        elif req == "<":
            results.append(version.parse(currentVersion) < version.parse(requiredVersion))
    return True if False not in results else False


def isSystemSatisfied(
    systemReqs: str
):
    """
    Check if the system requirements are satisfied
    """
    if systemReqs is None:
        return True
    systemReqs = systemReqs.split(';') if isinstance(systemReqs, str) else list(systemReqs)
    results = []
    for systemReq in systemReqs:
        splitSystemReq = re.split('!|=|>|<', systemReq)
        requiredSystem = splitSystemReq[-1].strip()
        req = systemReq[len(splitSystemReq[0]) : len(systemReq) - len(splitSystemReq[-1])].strip()
        if req == "==":
            results.append(sys.platform == eval(requiredSystem))
        if req == "!=":
            results.append(sys.platform != eval(requiredSystem))
        return True if False not in results else False

#############################################################################################################

class envType(Enum):
    System = "System"
    User = "User"
    Temp = "Temp"


def setEnvVar(
    variable: str,
    value: str,
    type: envType = envType.Temp,
    affectOS: bool = True
):
    """
    Set environment variable
    """
    value = rawString(value)

    if type == envType.System:
        if platform.system() == 'Windows':
            command = ";".join([
                f"`$current = [Environment]::GetEnvironmentVariable('{variable}', 'Machine')",
                f"`$new = '{value};' + `$current",
                f"[Environment]::SetEnvironmentVariable('{variable}', `$new, 'Machine')",
            ])
            runCMD(
                args = [
                    f'powershell.exe',
                    f'Start-Process powershell -ArgumentList "-Command {command}" -Verb RunAs -Wait',
                ],
                shell = True,
                env = os.environ,
            )
        if platform.system() == 'Linux':
            with open('/etc/environment', 'a') as f:
                f.write(f'\n{variable}="{value}"\n')

    if type == envType.User:
        if platform.system() == 'Windows':
            runCMD(
                args = [
                    f'for /f "usebackq tokens=2,*" %A in (`reg query "HKEY_CURRENT_USER\\Environment" /v "{variable}"`) do set userVAR=%B',
                    f'if defined userVAR (setx "{variable}" "{value}{os.pathsep}%userVAR%") else (setx "{variable}" "{value}")'
                ],
                shell = True,
                env = os.environ,
            )
        if platform.system() == 'Linux':
            shell = os.environ.get('SHELL', '/bin/bash')
            if 'bash' in shell:
                config_file = os.path.expanduser('~/.bashrc')
            elif 'zsh' in shell:
                config_file = os.path.expanduser('~/.zshrc')
            else:
                config_file = os.path.expanduser('~/.profile')
            with open(config_file, 'a') as f:
                f.write(f'\nexport {variable}="{value}"\n')

    if type == envType.Temp or affectOS:
        EnvValue = os.environ.get(variable)
        if EnvValue is not None and normPath(value, 'Posix') not in [normPath(value, 'Posix') for value in EnvValue.split(os.pathsep)]:
            EnvValue = f'{value}{os.pathsep}{EnvValue}' #EnvValue = f'{EnvValue}{os.pathsep}{value}'
        else:
            EnvValue = value
        os.environ[variable] = EnvValue

#############################################################################################################