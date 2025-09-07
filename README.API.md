## 📦 快速开始

### 安装
```
pip install pysqlit
```
### 快速入门
```
from pysqlit.pysqlit_api import Pysqlit_API

# 创建数据库连接
db = Pysqlit_API('test.db')

# 创建表
 db.create_tb('animals', 
    {'id': 'INTEGER', 'name': 'TEXT', 'age': 'INTEGER', 'gender': 'TEXT'},
    'id', 
    ['name'],
    ['name','age'])

# 插入数据
db.insert_data('animals',{'name': 'AChao', 'age': 100, 'gender': '女'})

# 批量插入数据
db.insert_datas('animals', 
[{'name': 'Haa', 'age': 100, 'gender': '男'},
 {'name': 'YChao', 'age': 10, 'gender': '女'}]
 )

# 查询数据
db.select_data('animals')

# 更新数据
db.update_data('animals', {'age':10}, 'name=小猫')

# 删除数据
db.delete_data('animals', 'name=Jerry')
db.delete_data('animals')

# 执行SQL语句
db.executor('SELECT * FROM animals')

# 备份数据库
db.backup_db('test.db')

# 列出备份文件
db.list_backup()

# 还原数据库
db.restore_db('test.db')

# 导出CSV文件
db.export_csv_file('animals','animals.csv')

# 导入CSV文件
db.import_csv_file('animals','animals.csv')

```