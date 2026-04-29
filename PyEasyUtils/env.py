import os
import sys
import platform
import re
import winreg
import ctypes
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


def getAdminPrivileges():
    """
    Ensure the script runs with administrator privileges on Windows
    """
    if not platform.system() == 'Windows':
        return
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                " ".join(sys.argv),
                None,
                1
            )
            sys.exit()
    except Exception:
        print("Failed to elevate privileges. Please run as administrator.")
        sys.exit(1)


def setEnvVar(
    variable: str,
    value: str,
    type: envType = envType.Temp,
    affectOS: bool = True
):
    """
    Set environment variable using winreg on Windows for System/User variables
    """
    value = rawString(value)

    if platform.system() == 'Windows':
        if type == envType.System:
            try:
                getAdminPrivileges()
                # Open registry key for environment variables
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                    0,
                    winreg.KEY_ALL_ACCESS
                )
                # Determine new value
                try:
                    current_value, reg_type = winreg.QueryValueEx(key, variable)
                    if current_value:
                        new_value = f"{value}{os.pathsep}{current_value}"
                    else:
                        new_value = value
                except FileNotFoundError:
                    new_value = value
                # Set new value
                winreg.SetValueEx(key, variable, 0, winreg.REG_EXPAND_SZ if '%' in value else winreg.REG_SZ, new_value)
                winreg.CloseKey(key)
                # Broadcast change to all applications
                ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")
            except Exception as e:
                print(f"Error setting system environment variable '{variable}': {e}")
                return

        elif type == envType.User:
            try:
                # Open registry key for environment variables
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Environment",
                    0,
                    winreg.KEY_ALL_ACCESS
                )
                # Determine new value
                try:
                    current_value, reg_type = winreg.QueryValueEx(key, variable)
                    if current_value:
                        new_value = f"{value}{os.pathsep}{current_value}"
                    else:
                        new_value = value
                except FileNotFoundError:
                    new_value = value
                # Set new value
                winreg.SetValueEx(key, variable, 0, winreg.REG_EXPAND_SZ if '%' in value else winreg.REG_SZ, new_value)
                winreg.CloseKey(key)
                # Broadcast change to all applications
                ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")
            except Exception as e:
                print(f"Error setting user environment variable '{variable}': {e}")
                return

    elif platform.system() == 'Linux':
        if type == envType.System:
            with open('/etc/environment', 'a') as f:
                f.write(f'\n{variable}="{value}"\n')

        if type == envType.User:
            shell = os.environ.get('SHELL', '/bin/bash')
            if 'bash' in shell:
                config_file = os.path.expanduser('~/.bashrc')
            elif 'zsh' in shell:
                config_file = os.path.expanduser('~/.zshrc')
            else:
                config_file = os.path.expanduser('~/.profile')
            with open(config_file, 'a') as f:
                f.write(f'\nexport {variable}="{value}"\n')

    # For temporary variables or when affectOS is True
    if type == envType.Temp or affectOS:
        EnvValue = os.environ.get(variable)
        if EnvValue is not None:
            if value not in EnvValue.split(os.pathsep):
                val_new = f'{value}{os.pathsep}{EnvValue}'
                os.environ[variable] = val_new
        else:
            os.environ[variable] = value

#############################################################################################################