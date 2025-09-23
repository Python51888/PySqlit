import sys
import os
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from pysqlit.enhanced_datafile import EnhancedDataFile


class Pysqlit_API:

    """
    Pysqlit_API类，用于封装数据库操作功能，提供对数据库的增删改查等基本操作接口。
    """
    def __init__(self,file_name):
        """
        初始化方法，创建一个EnhancedDataFile实例并保存为类属性。
        参数:
            file_name: 数据库文件名
        """
        self.db = EnhancedDataFile(file_name) #'chao.db'
        

    def get_db_info(self):
        """
        获取数据库信息的方法。
        返回:
            数据库信息
        """
        # 获取数据库信息
        return self.db.get_database_info()
        pass


    def create_tb(self,tablename,columnss:dict[str,str],pk=None,unique=None,check=None):    
        # 创建表，添加主键自增、唯一约束和检查约束
        re = self.db.create_table(              #'animals'
            tablename, 
            columnss,
            # {
            #     'id': 'INTEGER',
            #     'name': 'TEXT',
            #     'age': 'INTEGER',
            #     'gender': 'TEXT'
            # },
            # primary_key='id',
            # unique_columns=['name'],
            # not_null_columns=['name']
            primary_key=pk,
            unique_columns=unique,
            not_null_columns=check
        )
        if re:
            print('表创建成功')
        else:
            print('表创建失败')

    def drop_tb(self,tablename):
        # 删除表
        re = self.db.drop_table(tablename)
        if re:
            print('表删除成功')
        else:
            print('表删除失败')

    def get_tb_info(self,tablename):
        # 获取表信息
        return self.db.get_table_info(tablename)
        pass

    
    def insert_data(self,tablename,data:dict):
        # 插入数据
        re = self.db.insert(tablename,data)
        if re:
            print('数据'+ str(re) +'行插入成功')
        else:
            print('数据插入失败')
        pass
    

    def insert_datas(self,tablename,datas:list):
        # 批量插入数据
        re = self.db.batch_insert(tablename,datas)
        if re:
            print('数据'+ str(re) +'行插入成功')
        else:
            print('数据插入失败')
        pass
       

    def select_data(self,tablename,condition=None):
        # 查询数据
        re = self.db.select(tablename,condition)
        if re:
            print('查询成功')
            results = []
            for i in re:
                # 将字典转换为JSON格式并添加到结果列表中
                json_result = json.dumps(i, ensure_ascii=False)
                results.append(json_result)
            return results
        else:
            print('查询失败')
            return []
        pass
    

    def update_data(self,tablename,data:dict,condition=None):
        # 更新数据
        re = self.db.update(tablename,data,condition)
        if re:
            print('数据'+ str(re) +'行更新成功')
        else:
            print('数据更新失败')
        pass

    
    def delete_data(self,tablename,condition=None):
        # 删除数据
        re = self.db.delete(tablename,condition)
        if re:
            print('数据'+ str(re) +'行删除成功')
        else:
            print('数据删除失败')
        pass
    
    def executor(self,sql):
        # 执行SQL语句
        re = self.db.execute_sql(sql)
        if re:
            print('执行成功')
            # 如果是查询语句，返回结果
            if sql.strip().upper().startswith('SELECT'):
                results = []
                for i in re:
                    # 将字典转换为JSON格式并添加到结果列表中
                    json_result = json.dumps(i, ensure_ascii=False)
                    results.append(json_result)
                return results
            else:
                # 对于非查询语句，返回影响的行数
                return re
        else:
            print('执行失败')
            return None
        pass


    def backup_db(self,db_name):
        # 备份数据库
        re = self.db.create_backup(db_name)
        if re:
            print('备份成功')
        else:
            print('备份失败')
        
    def list_backup(self):
        # 列出备份文件
        re = self.db.list_backups()
        if re:
            print('备份文件列表：')
            for i in re:
                print(i)
        else:
            print('没有备份文件')
        pass

    def restore_db(self,backup_name):
        # 还原数据库
        re = self.db.restore_backup(backup_name)
        if re:
            print('还原成功')
        else:
            print('还原失败')
        pass
    

    def export_csv_file(self,table_name,file_name):
        # 导出CSV文件
        re = self.db.export_to_csv(table_name,file_name)
        if re:
            print('导出csv文件成功: %s' % file_name)
        else:
            print('导出csv文件失败')
        pass


    def import_csv_file(self,table_name,file_name):
        # 导入CSV文件
        re = self.db.import_from_csv(table_name,file_name)
        if re:
            print('导入csv文件成功: %s' % file_name)
        else:
            print('导入csv文件失败')
        pass


if __name__ == '__main__':
    # db = Pysqlit_API('chao58.db')

    # db.create_tb('animals', 
    # {'id': 'INTEGER', 'name': 'TEXT', 'age': 'INTEGER', 'gender': 'TEXT'},
    # 'id', 
    # ['name'],
    # ['name','age'])

    # db.drop_tb('animals')
    # dic = db.get_tb_info('animals')
    # print(dic)
    # db.insert_data('animals',{'name': 'AChao', 'age': 100, 'gender': '女'})
    # db.select_data('animals')
    # db.update_data('animals', {'age':10}, 'name=小猫')
    # db.delete_data('animals', 'name=Jerry')
    # db.delete_data('animals')
    # print(db.get_db_info())
    # db.backup_db('chao.db')
    # db.list_backup()
    # db.restore_db('chao.db')
    # db.insert_datas('animals', [{'name': 'Haa', 'gender': '女'}, {'name': 'YChao', 'age': 100, 'gender': '女'}])
    # db.export_csv_file('animals','demo.csv')
    # db.import_csv_file('animals','animals.csv')
    pass