from .utils import toIterable, itemReplacer, findKey, getNamesFromMethod, getClassFromMethod, runEvents
from .overload import singledispatchmethod
from .math import getDecimalPlaces
from .text import evalString, rawString, findURL, makeSafeForURL, isURL, isJson, generateRandomString, toMarkdown, richTextManager, setRichText
from .path import normPath, getPaths, getBaseDir, getCurrentPath, getFileInfo, renameIfExists, cleanDirectory, moveFiles
from .process import taskAccelerationManager, processTerminator, occupationTerminator
from .cmd import subprocessManager, runCMD, runScript, bootWithScript
from .env import isVersionSatisfied, isSystemSatisfied, setEnvVar
from .config import configManager
from .database import sqliteManager
from .web import requestManager, isConnected, simpleRequest, responseParser, downloadFile, checkUpdateFromGithub