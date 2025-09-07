import os
import sys
import csv
import traceback

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from pysqlit.enhanced_datafile import EnhancedDataFile

def test_csv_import():
    # 创建测试数据库
    db = EnhancedDataFile('test_import.db')
    
    # 如果表已存在，先删除它
    try:
        db.drop_table('animals')
        print("已删除已存在的animals表")
    except:
        pass  # 表不存在，忽略错误
    
    # 创建表，使用自动生成的整数主键，name作为唯一约束
    db.create_table('animals', {
        'id': 'INTEGER',
        'name': 'TEXT',
        'age': 'INTEGER',
        'gender': 'TEXT'
    }, primary_key='id', unique_columns=['name'])  # 使用id作为主键，name作为唯一约束
    
    # 导入CSV数据
    print("\n导入CSV文件...")
    try:
        result = db.import_from_csv('animals', 'demo.csv')
        print(f"导入结果: {result}")
    except Exception as e:
        print(f"导入失败: {e}")
        traceback.print_exc()
    
    # 查询所有数据
    print("\n查询所有数据...")
    try:
        data = db.select('animals')
        print(f"查询到 {len(data)} 行数据:")
        for i, row in enumerate(data):
            print(f"  行 {i+1}: {row}")
    except Exception as e:
        print(f"查询失败: {e}")
        traceback.print_exc()
    
    # 清理测试文件
    db.close()
    if os.path.exists('test_import.db'):
        os.remove('test_import.db')
    if os.path.exists('test_import.db.schema'):
        os.remove('test_import.db.schema')

if __name__ == '__main__':
    test_csv_import()