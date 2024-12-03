import hashlib
import polars
import sqlalchemy
from datetime import datetime

#############################################################################################################

class sqlManager:
    """
    Manage SQL
    """
    historydbName = "history"
    historydbTableName = "historyTable"

    file_path = None
    filedb_name = None

    def exportDataToFiledb(self, df: polars.DataFrame, new: bool = True):
        '''
        将DataFrame导入文件数据库
        '''
        self.filedb_name = f"DB_{datetime.now().strftime('%Y%m%d%H%M%S')}" if new else self.filedb_name
        filedb_engine = sqlalchemy.create_engine(f'sqlite:///{self.filedb_name}.db')
        df.write_database(
            table_name = self.filedb_name,
            connection = filedb_engine,
            if_table_exists = 'replace'
        )

    def loadDataFromFiledb(self):
        '''
        从文件数据库中导出DataFrame
        '''
        filedb_engine = sqlalchemy.create_engine(f'sqlite:///{self.filedb_name}.db') # 与文件数据库建立连接
        df = polars.read_database(
            f"SELECT * FROM {self.filedb_name}",
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
                "file_hash": [],
                "filedb_name": []
            })
            df.write_database(
                table_name = self.historydbTableName,
                connection = self.historyEngine,
                if_table_exists = 'replace'
            )

    def toHistorydb(self):
        '''
        将[表格哈希值,表格数据库名]写入历史记录数据库
        '''
        file_hash = hashlib.md5(open(self.file_path, 'rb').read()).hexdigest()
        df = polars.DataFrame({
            "file_hash": [file_hash],
            "filedb_name": [self.filedb_name]
        })
        df.write_database(
            table_name = self.historydbTableName,
            connection = self.historyEngine,
            if_table_exists = 'append'
        )
        # TODO 通过redis建立旁路缓存模式

    def chkHistorydb(self):
        '''
        检查文件哈希值在历史记录数据库中的对应值
        '''
        file_hash = hashlib.md5(open(self.file_path, 'rb').read()).hexdigest()
        print(f'checking hash {file_hash} in {self.historydbName}.db')
        df = polars.read_database(
            f"SELECT * FROM {self.historydbTableName} WHERE file_hash = '{file_hash}'",
            connection = self.historyEngine
        )
        filedb_name = df.row(0, named = True)["filedb_name"] if len(df) > 0 else None
        print(f'filedb name found: {filedb_name}')
        return filedb_name

##############################################################################################################################