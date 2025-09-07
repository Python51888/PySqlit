"""增强版数据文件操作接口测试。

这个测试文件验证EnhancedDataFile类的正确性和功能。
"""

import os
import json
import csv
import xml.etree.ElementTree as ET
import unittest
import tempfile
from pysqlit.enhanced_datafile import EnhancedDataFile
from pysqlit.exceptions import DatabaseError


class TestEnhancedDataFile(unittest.TestCase):
    """增强版数据文件操作接口测试类。"""

    def setUp(self):
        """测试前准备。"""
        # 创建临时目录和文件
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.temp_dir, "test_enhanced_datafile.db")
        self.schema_file = f"{self.db_file}.schema"
        
        # 清理可能存在的旧文件
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
        if os.path.exists(self.schema_file):
            os.remove(self.schema_file)

    def tearDown(self):
        """测试后清理。"""
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
        if os.path.exists(self.schema_file):
            os.remove(self.schema_file)
        
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_table(self):
        """测试创建表功能。"""
        with EnhancedDataFile(self.db_file) as edf:
            # 创建表
            result = edf.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT",
                    "email": "TEXT"
                },
                primary_key="id",
                unique_columns=["email"],
                not_null_columns=["name"]
            )
            self.assertTrue(result)
            
            # 验证表已创建
            tables = edf.list_tables()
            self.assertIn("users", tables)

    def test_insert_and_select(self):
        """测试插入和查询功能。"""
        with EnhancedDataFile(self.db_file) as edf:
            # 创建表
            edf.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT",
                    "email": "TEXT"
                },
                primary_key="id",
                unique_columns=["email"],
                not_null_columns=["name"]
            )
            
            # 插入单行数据
            count = edf.insert("users", {"id": 1, "name": "张三", "email": "zhangsan@example.com"})
            self.assertEqual(count, 1)
            
            # 插入多行数据
            count = edf.insert("users", [
                {"id": 2, "name": "李四", "email": "lisi@example.com"},
                {"id": 3, "name": "王五", "email": "wangwu@example.com"}
            ])
            self.assertEqual(count, 2)
            
            # 查询所有数据
            users = edf.select("users")
            self.assertEqual(len(users), 3)
            
            # 条件查询
            user = edf.select("users", where="id = 1")
            self.assertEqual(len(user), 1)
            self.assertEqual(user[0]["id"], 1)
            self.assertEqual(user[0]["name"], "张三")
            self.assertEqual(user[0]["email"], "zhangsan@example.com")

    def test_batch_insert(self):
        """测试批量插入功能。"""
        with EnhancedDataFile(self.db_file) as edf:
            # 创建表
            edf.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT"
                },
                primary_key="id"
            )
            
            # 批量插入数据
            data = [{"id": i, "name": f"用户{i}"} for i in range(1, 101)]
            count = edf.batch_insert("users", data, batch_size=20)
            self.assertEqual(count, 100)
            
            # 验证插入的数据
            users = edf.select("users")
            self.assertEqual(len(users), 100)

    def test_update_and_delete(self):
        """测试更新和删除功能。"""
        with EnhancedDataFile(self.db_file) as edf:
            # 创建表
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
            
            # 插入数据
            edf.insert("users", [
                {"id": 1, "name": "张三", "email": "zhangsan@example.com", "age": 25},
                {"id": 2, "name": "李四", "email": "lisi@example.com", "age": 30}
            ])
            
            # 更新数据
            count = edf.update("users", {"age": 26}, where="id = 1")
            self.assertEqual(count, 1)
            
            # 验证更新
            user = edf.select("users", where="id = 1")
            self.assertEqual(user[0]["age"], 26)
            
            # 删除数据
            count = edf.delete("users", where="id = 2")
            self.assertEqual(count, 1)
            
            # 验证删除
            users = edf.select("users")
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0]["id"], 1)

    def test_alter_table(self):
        """测试修改表结构功能。"""
        with EnhancedDataFile(self.db_file) as edf:
            # 创建表
            edf.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT"
                },
                primary_key="id"
            )
            
            # 添加列
            result = edf.alter_table("users", "ADD", "email", "TEXT")
            self.assertTrue(result)
            
            # 验证列已添加
            info = edf.get_table_info("users")
            self.assertIn("email", info["columns"])

    def test_get_table_info(self):
        """测试获取表信息功能。"""
        with EnhancedDataFile(self.db_file) as edf:
            # 创建表
            edf.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT",
                    "email": "TEXT"
                },
                primary_key="id",
                unique_columns=["email"],
                not_null_columns=["name"]
            )
            
            # 获取表信息
            info = edf.get_table_info("users")
            self.assertEqual(info["table_name"], "users")
            self.assertEqual(info["primary_key"], "id")
            self.assertIn("id", info["columns"])
            self.assertIn("name", info["columns"])
            self.assertIn("email", info["columns"])
            
            # 验证列信息
            id_col = info["columns"]["id"]
            self.assertEqual(id_col["data_type"], "INTEGER")
            self.assertTrue(id_col["is_primary"])
            self.assertFalse(id_col["is_nullable"])

    def test_import_export_json(self):
        """测试JSON导入导出功能。"""
        # 创建示例JSON文件
        json_file = os.path.join(self.temp_dir, "test_data.json")
        test_data = [
            {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
            {"id": 2, "name": "李四", "email": "lisi@example.com"}
        ]
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False)
        
        with EnhancedDataFile(self.db_file) as edf:
            # 创建表
            edf.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT",
                    "email": "TEXT"
                },
                primary_key="id",
                unique_columns=["email"],
                not_null_columns=["name"]
            )
            
            # 从JSON导入数据
            imported_count = edf.import_from_json("users", json_file)
            self.assertEqual(imported_count, 2)
            
            # 验证导入的数据
            users = edf.select("users")
            self.assertEqual(len(users), 2)
            
            # 导出数据到JSON
            export_file = os.path.join(self.temp_dir, "exported_data.json")
            exported_count = edf.export_to_json("users", export_file)
            self.assertEqual(exported_count, 2)
            
            # 验证导出的数据
            with open(export_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            self.assertEqual(len(exported_data), 2)

    def test_import_export_csv(self):
        """测试CSV导入导出功能。"""
        # 创建示例CSV文件
        csv_file = os.path.join(self.temp_dir, "test_data.csv")
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "email"])
            writer.writerow([1, "张三", "zhangsan@example.com"])
            writer.writerow([2, "李四", "lisi@example.com"])
        
        with EnhancedDataFile(self.db_file) as edf:
            # 创建表
            edf.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT",
                    "email": "TEXT"
                },
                primary_key="id",
                unique_columns=["email"],
                not_null_columns=["name"]
            )
            
            # 从CSV导入数据
            imported_count = edf.import_from_csv("users", csv_file)
            self.assertEqual(imported_count, 2)
            
            # 验证导入的数据
            users = edf.select("users")
            self.assertEqual(len(users), 2)
            
            # 导出数据到CSV
            export_file = os.path.join(self.temp_dir, "exported_data.csv")
            exported_count = edf.export_to_csv("users", export_file)
            self.assertEqual(exported_count, 2)
            
            # 验证导出的数据
            with open(export_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 3)  # 包含标题行

    def test_import_export_xml(self):
        """测试XML导入导出功能。"""
        # 创建示例XML文件
        xml_file = os.path.join(self.temp_dir, "test_data.xml")
        root = ET.Element("data")
        row1 = ET.SubElement(root, "row")
        ET.SubElement(row1, "id").text = "1"
        ET.SubElement(row1, "name").text = "张三"
        ET.SubElement(row1, "email").text = "zhangsan@example.com"
        
        row2 = ET.SubElement(root, "row")
        ET.SubElement(row2, "id").text = "2"
        ET.SubElement(row2, "name").text = "李四"
        ET.SubElement(row2, "email").text = "lisi@example.com"
        
        tree = ET.ElementTree(root)
        tree.write(xml_file, encoding="utf-8", xml_declaration=True)
        
        with EnhancedDataFile(self.db_file) as edf:
            # 创建表
            edf.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT",
                    "email": "TEXT"
                },
                primary_key="id",
                unique_columns=["email"],
                not_null_columns=["name"]
            )
            
            # 从XML导入数据
            imported_count = edf.import_from_xml("users", xml_file)
            self.assertEqual(imported_count, 2)
            
            # 验证导入的数据
            users = edf.select("users")
            self.assertEqual(len(users), 2)
            
            # 导出数据到XML
            export_file = os.path.join(self.temp_dir, "exported_data.xml")
            exported_count = edf.export_to_xml("users", export_file)
            self.assertEqual(exported_count, 2)
            
            # 验证导出的数据
            tree = ET.parse(export_file)
            root = tree.getroot()
            rows = root.findall("row")
            self.assertEqual(len(rows), 2)

    def test_index_management(self):
        """测试索引管理功能。"""
        with EnhancedDataFile(self.db_file) as edf:
            # 创建表
            edf.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT",
                    "email": "TEXT"
                },
                primary_key="id"
            )
            
            # 创建索引
            result = edf.create_index("users", "idx_users_name", ["name"])
            self.assertTrue(result)
            
            # 创建唯一索引
            result = edf.create_index("users", "idx_users_email", ["email"], unique=True)
            self.assertTrue(result)
            
            # 删除索引
            result = edf.drop_index("idx_users_name")
            self.assertTrue(result)

    def test_transaction_management(self):
        """测试事务管理功能。"""
        with EnhancedDataFile(self.db_file) as edf:
            # 创建表
            edf.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT"
                },
                primary_key="id"
            )
            
            # 开始事务
            transaction_id = edf.begin_transaction()
            self.assertIsNotNone(transaction_id)
            
            # 在事务中插入数据
            edf.insert("users", {"id": 1, "name": "张三"})
            
            # 验证数据已插入但未提交
            users = edf.select("users")
            self.assertEqual(len(users), 1)
            
            # 提交事务
            edf.commit_transaction()
            
            # 验证数据已提交
            users = edf.select("users")
            self.assertEqual(len(users), 1)

    def test_error_handling(self):
        """测试错误处理。"""
        with EnhancedDataFile(self.db_file) as edf:
            # 尝试操作不存在的表
            with self.assertRaises(DatabaseError):
                edf.select("nonexistent_table")
            
            # 尝试插入重复主键
            edf.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT"
                },
                primary_key="id"
            )
            
            edf.insert("users", {"id": 1, "name": "张三"})
            
            # 这应该会抛出DatabaseError异常
            with self.assertRaises(DatabaseError):
                edf.insert("users", {"id": 1, "name": "李四"})


if __name__ == "__main__":
    unittest.main()