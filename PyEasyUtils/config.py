import os
import configparser
from datetime import datetime
from pathlib import Path
from typing import Optional

from .path import normPath

#############################################################################################################

class configManager:
    """
    Manage config through ConfigParser
    """
    def __init__(self,
        configPath: Optional[str] = None
    ):
        self.configParser = configparser.ConfigParser()
        self.configPath = normPath(Path(os.getcwd()).joinpath('config_%s.ini' % datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))) if configPath == None else configPath
        if Path(self.configPath).exists():
            self.configParser.read(self.configPath, encoding = 'utf-8')
        else:
            configDir = Path(self.configPath).parent.as_posix()
            os.makedirs(configDir, exist_ok = True) if Path(configDir).exists() == False else None
            with open(self.configPath, 'w'):
                pass
            self.configParser.clear()

    def parser(self):
        return self.configParser

    def editConfig(self,
        section: str = ...,
        option: str = ...,
        value: str = ...,
        configParser: Optional[configparser.ConfigParser] = None
    ):
        configParser = self.parser() if configParser == None else configParser
        try:
            configParser.add_section(section)
        except:
            pass
        configParser.set(section, option, value)
        with open(self.configPath, 'w', encoding = 'utf-8') as Config:
            configParser.write(Config)

    def remove(self,
        section: str = ...,
        option: Optional[str] = None,
        configParser: Optional[configparser.ConfigParser] = None
    ):
        configParser = self.parser() if configParser == None else configParser
        try:
            configParser.remove_option(section, option) if option is not None else configParser.remove_section(section)
        except:
            pass
        with open(self.configPath, 'w', encoding = 'utf-8') as Config:
            configParser.write(Config)

    def getValue(self,
        section: str = ...,
        option: str = ...,
        initValue: Optional[str] = None,
        configParser: Optional[configparser.ConfigParser] = None
    ):
        configParser = self.parser() if configParser == None else configParser
        try:
            value = configParser.get(section, option)
        except:
            if initValue != None:
                self.editConfig(section, option, initValue, configParser)
                return initValue
            else:
                return None #raise Exception("Need initial value")
        else:
            return value

#############################################################################################################