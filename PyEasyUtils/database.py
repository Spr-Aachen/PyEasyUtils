import hashlib
import polars
import sqlalchemy
from datetime import datetime

#############################################################################################################

class sqliteManager:
    """
    Manage sqlite database
    """
    historydbName = "history"
    historydbTableName = "historyTable"

    filedbName = None

    colName_fileHash = "fileHash"
    colName_filedbName = "filedbName"

    def writeDataToFiledb(self, df: polars.DataFrame, new: bool = True):
        '''
        将DataFrame导入文件数据库
        '''
        self.filedbName = f"DB_{datetime.now().strftime('%Y%m%d%H%M%S')}" if new else self.filedbName
        filedb_engine = sqlalchemy.create_engine(f'sqlite:///{self.filedbName}.db')
        df.write_database(
            table_name = self.filedbName,
            connection = filedb_engine,
            if_table_exists = 'replace'
        )

    def readDataFromFiledb(self):
        '''
        从文件数据库中导出DataFrame
        '''
        filedb_engine = sqlalchemy.create_engine(f'sqlite:///{self.filedbName}.db') # 与文件数据库建立连接
        df = polars.read_database(
            f"SELECT * FROM {self.filedbName}",
            connection = filedb_engine
        )
        df.fill_nan("")
        return df

    def createHistorydb(self):
        '''
        创建历史记录数据库并初始化历史记录Table
        '''
        self.historyEngine = sqlalchemy.create_engine(f'sqlite:///{self.historydbName}.db')
        if not sqlalchemy.inspect(self.historyEngine).has_table(self.historydbTableName):
            df = polars.DataFrame({
                self.colName_fileHash: [],
                self.colName_filedbName: []
            })
            df.write_database(
                table_name = self.historydbTableName,
                connection = self.historyEngine,
                if_table_exists = 'replace'
            )

    def toHistorydb(self, file_path):
        '''
        将[表格哈希值,表格数据库名]写入历史记录数据库
        '''
        fileHash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
        df = polars.DataFrame({
            self.colName_fileHash: [fileHash],
            self.colName_filedbName: [self.filedbName]
        })
        df.write_database(
            table_name = self.historydbTableName,
            connection = self.historyEngine,
            if_table_exists = 'append'
        )
        # TODO 通过redis建立旁路缓存模式

    def chkHistorydb(self, file_path):
        '''
        检查文件哈希值在历史记录数据库中的对应值
        '''
        fileHash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
        df = polars.read_database(
            f"SELECT * FROM {self.historydbTableName} WHERE {self.colName_fileHash} = '{fileHash}'",
            connection = self.historyEngine
        )
        filedbName = df.row(0, named = True)[self.colName_filedbName] if len(df) > 0 else None
        return filedbName

##############################################################################################################################