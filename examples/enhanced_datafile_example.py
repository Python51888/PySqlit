"""增强版数据文件操作接口使用示例。

这个示例展示了如何使用EnhancedDataFile类对数据文件执行完整的数据库操作。
"""

import os
import json
import csv
import xml.etree.ElementTree as ET
from pysqlit.enhanced_datafile import EnhancedDataFile
from pysqlit.exceptions import DatabaseError


def create_sample_data():
    """创建示例数据文件。"""
    # 创建JSON示例数据
    users_data = [
        {"id": 1, "name": "张三", "email": "zhangsan@example.com", "age": 25},
        {"id": 2, "name": "李四", "email": "lisi@example.com", "age": 30}
    ]
    
    with open("sample_users.json", "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)
    
    # 创建CSV示例数据
    with open("sample_users.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "email", "age"])
        writer.writerow([3, "王五", "wangwu@example.com", 28])
        writer.writerow([4, "赵六", "zhaoliu@example.com", 35])
    
    # 创建XML示例数据
    root = ET.Element("data")
    row1 = ET.SubElement(root, "row")
    ET.SubElement(row1, "id").text = "5"
    ET.SubElement(row1, "name").text = "钱七"
    ET.SubElement(row1, "email").text = "qianqi@example.com"
    ET.SubElement(row1, "age").text = "22"
    
    row2 = ET.SubElement(root, "row")
    ET.SubElement(row2, "id").text = "6"
    ET.SubElement(row2, "name").text = "孙八"
    ET.SubElement(row2, "email").text = "sunba@example.com"
    ET.SubElement(row2, "age").text = "27"
    
    tree = ET.ElementTree(root)
    tree.write("sample_users.xml", encoding="utf-8", xml_declaration=True)


def main():
    # 数据库文件名
    db_file = "enhanced_datafile_example.db"
    schema_file = f"{db_file}.schema"
    
    # 如果数据库文件存在，先删除它以确保干净的环境
    if os.path.exists(db_file):
        os.remove(db_file)
    
    # 删除模式文件
    if os.path.exists(schema_file):
        os.remove(schema_file)
    
    # 创建示例数据文件
    create_sample_data()
    
    # 使用上下文管理器创建增强版数据文件操作对象
    with EnhancedDataFile(db_file) as edf:
        # 创建表
        print("创建表...")
        edf.create_table(
            table_name="users",
            columns={
                "id": "INTEGER",
                "name": "TEXT",
                "email": "TEXT",
                "age": "INTEGER"
            },
            primary_key="id",
            unique_columns=["email"],
            not_null_columns=["name"]
        )
        print("表创建成功！")
        
        # 插入单行数据
        print("\n插入单行数据...")
        edf.insert("users", {"id": 7, "name": "周九", "email": "zhoujiu@example.com", "age": 31})
        print("单行数据插入成功！")
        
        # 插入多行数据
        print("\n插入多行数据...")
        edf.insert("users", [
            {"id": 8, "name": "吴十", "email": "wushi@example.com", "age": 26},
            {"id": 9, "name": "郑十一", "email": "zhengshiyi@example.com", "age": 29}
        ])
        print("多行数据插入成功！")
        
        # 批量插入数据
        print("\n批量插入数据...")
        batch_data = [
            {"id": 10, "name": "王十二", "email": "wangshier@example.com", "age": 33},
            {"id": 11, "name": "冯十三", "email": "fengsanshi@example.com", "age": 24},
            {"id": 12, "name": "陈十四", "email": "chensishi@example.com", "age": 36}
        ]
        inserted_count = edf.batch_insert("users", batch_data)
        print(f"批量插入了 {inserted_count} 行数据")
        
        # 从JSON文件导入数据
        print("\n从JSON文件导入数据...")
        imported_count = edf.import_from_json("users", "sample_users.json")
        print(f"从JSON文件导入了 {imported_count} 行数据")
        
        # 从CSV文件导入数据
        print("\n从CSV文件导入数据...")
        imported_count = edf.import_from_csv("users", "sample_users.csv")
        print(f"从CSV文件导入了 {imported_count} 行数据")
        
        # 从XML文件导入数据
        print("\n从XML文件导入数据...")
        imported_count = edf.import_from_xml("users", "sample_users.xml")
        print(f"从XML文件导入了 {imported_count} 行数据")
        
        # 查询所有数据
        print("\n查询所有用户...")
        users = edf.select("users")
        for user in users:
            print(f"  ID: {user['id']}, 姓名: {user['name']}, 邮箱: {user['email']}, 年龄: {user['age']}")
        
        # 条件查询
        print("\n查询年龄大于25的用户...")
        older_users = edf.select("users", where="age > 25")
        for user in older_users:
            print(f"  ID: {user['id']}, 姓名: {user['name']}, 年龄: {user['age']}")
        
        # 排序和限制查询（注释掉因为当前实现不支持）
        # print("\n按年龄排序并限制结果数量...")
        # sorted_users = edf.select("users", order_by="age DESC", limit=5)
        # for user in sorted_users:
        #     print(f"  ID: {user['id']}, 姓名: {user['name']}, 年龄: {user['age']}")
        
        # 创建部门表...
        # edf.create_table(
        #     table_name="departments",
        #     columns={
        #         "id": "INTEGER",
        #         "name": "TEXT"
        #     },
        #     primary_key="id"
        # )
        
        # 插入部门数据
        # edf.insert("departments", [
        #     {"id": 1, "name": "技术部"},
        #     {"id": 2, "name": "销售部"},
        #     {"id": 3, "name": "人事部"}
        # ])
        
        # 添加外键列到用户表
        # print("\n修改用户表，添加部门ID列...")
        # edf.alter_table("users", "ADD", "department_id", "INTEGER")
        
        # 更新用户数据，添加部门ID（注释掉因为IN操作符不被支持）
        # edf.update("users", {"department_id": 1}, where="id IN (1, 2, 7, 8)")
        # edf.update("users", {"department_id": 2}, where="id IN (3, 4, 9, 10)")
        # edf.update("users", {"department_id": 3}, where="id IN (5, 6, 11, 12)")
        
        # 多表连接查询（注释掉因为当前实现可能不支持）
        # print("\n多表连接查询（用户和部门信息）...")
        # joined_data = edf.select_with_join(
        #     tables=["users", "departments"],
        #     columns=["users.id", "users.name", "users.email", "departments.name as department"],
        #     join_conditions=["INNER JOIN departments ON users.department_id = departments.id"],
        #     where="users.age > 25",
        #     order_by="users.age DESC",
        #     limit=5
        # )
        # for row in joined_data:
        #     print(f"  ID: {row['id']}, 姓名: {row['name']}, 邮箱: {row['email']}, 部门: {row['department']}")
        # 更新数据
        print("\n更新用户信息...")
        updated_count = edf.update("users", {"age": 27}, where="id = 1")
        print(f"更新了 {updated_count} 条记录")
        
        # 验证更新
        updated_user = edf.select("users", where="id = 1")
        print(f"更新后的用户: {updated_user[0]}")
        
        # 删除数据
        print("\n删除用户...")
        deleted_count = edf.delete("users", where="id = 3")
        print(f"删除了 {deleted_count} 条记录")
        
        # 验证删除
        remaining_users = edf.select("users")
        print("剩余用户:")
        for user in remaining_users:
            print(f"  ID: {user['id']}, 姓名: {user['name']}")
        
        # 创建索引
        print("\n创建索引...")
        edf.create_index("users", "idx_users_age", ["age"])
        edf.create_index("users", "idx_users_email", ["email"], unique=True)
        print("索引创建成功！")
        
        # 获取表信息
        print("\n表信息:")
        table_info = edf.get_table_info("users")
        print(f"  表名: {table_info['table_name']}")
        print(f"  主键: {table_info['primary_key']}")
        print("  列信息:")
        for col_name, col_info in table_info['columns'].items():
            print(f"    {col_name}: {col_info['data_type']} "
                  f"(主键: {col_info['is_primary']}, 可空: {col_info['is_nullable']}, "
                  f"唯一: {col_info['is_unique']}, 自增: {col_info['is_autoincrement']})")
        
        # 列出所有表
        print("\n所有表:")
        tables = edf.list_tables()
        for table in tables:
            print(f"  {table}")
        
        # 获取数据库信息
        print("\n数据库信息:")
        db_info = edf.get_database_info()
        print(f"  文件名: {db_info['filename']}")
        print(f"  文件大小: {db_info['file_size']} 字节")
        print(f"  表数量: {len(db_info['tables'])}")
        for table_name, row_count in db_info['tables'].items():
            print(f"    {table_name}: {row_count} 行")
        
        # 导出数据到JSON文件
        print("\n导出数据到JSON文件...")
        exported_count = edf.export_to_json("users", "exported_users.json")
        print(f"导出了 {exported_count} 行数据到 exported_users.json")
        
        # 导出数据到CSV文件
        print("\n导出数据到CSV文件...")
        exported_count = edf.export_to_csv("users", "exported_users.csv")
        print(f"导出了 {exported_count} 行数据到 exported_users.csv")
        
        # 导出数据到XML文件
        print("\n导出数据到XML文件...")
        exported_count = edf.export_to_xml("users", "exported_users.xml")
        print(f"导出了 {exported_count} 行数据到 exported_users.xml")
        
        # 执行原始SQL查询
        print("\n执行原始SQL查询...")
        result, data = edf.execute_sql("SELECT COUNT(*) as count FROM users")
        rows, col_names = data
        print(f"用户总数: {rows[0].get_value('count')}")
        
        # 事务操作示例
        print("\n事务操作示例...")
        try:
            # 开始事务
            edf.begin_transaction()
            
            # 在事务中执行多个操作
            edf.insert("users", {"id": 20, "name": "事务用户1", "email": "trans1@example.com", "age": 20})
            edf.insert("users", {"id": 21, "name": "事务用户2", "email": "trans2@example.com", "age": 21})
            
            # 查询验证（注释掉因为OR操作符不被支持）
            # trans_users = edf.select("users", where="id = 20 OR id = 21")
            # print(f"事务中插入的用户数量: {len(trans_users)}")
            
            # 提交事务
            edf.commit_transaction()
            print("事务提交成功")
            
        except Exception as e:
            # 回滚事务
            edf.rollback_transaction()
            print(f"事务回滚: {e}")
        
        # 验证事务结果（注释掉因为OR操作符不被支持）
        # trans_users = edf.select("users", where="id = 20 OR id = 21")
        # print(f"事务提交后用户数量: {len(trans_users)}")
        
        # 创建备份
        print("\n创建数据库备份...")
        backup_path = edf.create_backup("enhanced_example_backup")
        print(f"备份创建成功: {backup_path}")
        
        # 列出备份
        print("\n所有备份:")
        backups = edf.list_backups()
        for backup in backups:
            print(f"  {backup['name']}: {backup['path']}")
        
        # 数据库整理
        print("\n数据库整理...")
        if edf.vacuum():
            print("数据库整理成功")
        else:
            print("数据库整理失败")


if __name__ == "__main__":
    main()
    
    # 清理示例文件
    cleanup_files = [
        "sample_users.json",
        "sample_users.csv",
        "sample_users.xml",
        "exported_users.json",
        "exported_users.csv",
        "exported_users.xml",
        "enhanced_datafile_example.db",
        "enhanced_datafile_example.db.schema"
    ]
    
    for file in cleanup_files:
        if os.path.exists(file):
            os.remove(file)
    
    # 清理备份文件（如果存在）
    import glob
    backup_files = glob.glob("backups/*.db.backup")
    for file in backup_files:
        if os.path.exists(file):
            os.remove(file)
    
    print("\n示例运行完成，临时文件已清理。")