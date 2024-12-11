import os
import configparser
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
        self.configPath = normPath(Path(os.getenv('SystemDrive')).joinpath('Config.ini')) if configPath == None else configPath
        os.makedirs(Path(self.configPath).parent, exist_ok = True)

        self.configParser = configparser.ConfigParser()
        try:
            self.configParser.read(self.configPath, encoding = 'utf-8')
        except:
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
                pass #raise Exception("Need initial value")
        return value

#############################################################################################################