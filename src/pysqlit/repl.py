"""增强型REPL（交互式命令行界面），支持完整SQL语法、事务管理和备份功能。

该模块提供了一个功能丰富的交互式命令行界面，支持：
- 完整的SQL语法解析和执行
- 事务管理（BEGIN、COMMIT、ROLLBACK）
- 多数据库管理
- 数据库备份和恢复
- 表结构查看
- 错误处理和用户友好的提示

主要特性：
1. 完整的ACID事务支持
2. 多数据库连接管理
3. 数据库备份和恢复功能
4. 交互式命令行界面
5. 丰富的元命令支持
"""

import sys
import os
import glob
from typing import Optional, List, Any, Dict
from .database import EnhancedDatabase, SQLExecutor
from .parser import EnhancedSQLParser
from .models import PrepareResult
from .transaction import IsolationLevel
from .transaction import TransactionManager


class EnhancedInputBuffer:
    """增强型输入缓冲区，用于读取用户输入。
    
    提供用户输入的读取和预处理功能，支持EOF处理和基本的输入验证。
    
    Attributes:
        buffer: 输入缓冲区内容
    """
    
    def __init__(self) -> None:
        """初始化输入缓冲区。"""
        self.buffer = ""
    
    def read_input(self) -> str:
        """从用户读取输入。
        
        Returns:
            str: 用户输入的字符串，EOF时返回".exit"
        """
        try:
            return input("SQLite> ").strip()
        except EOFError:
            return ".exit"
    
    def close(self) -> None:
        """关闭输入缓冲区。"""
        pass


class EnhancedREPL:
    """增强型REPL，支持完整SQL语法、事务和多数据库管理。
    
    提供功能丰富的交互式数据库操作界面，支持：
    - 完整的SQL语法执行
    - 事务管理
    - 多数据库切换
    - 备份和恢复
    - 表结构查看
    
    Attributes:
        databases: 数据库连接字典（数据库名 -> EnhancedDatabase）
        current_database_name: 当前数据库名称
        current_database: 当前数据库实例
        active_database: 活动数据库标识
        executor: SQL执行器
        transaction_manager: 事务管理器
        current_transaction: 当前事务ID
        input_buffer: 输入缓冲区
    
    Examples:
        >>> repl = EnhancedREPL("test.db")
        >>> repl.run()  # 启动交互式界面
    """
    
    def __init__(self, database_file: str = ":memory:") -> None:
        """初始化增强型REPL。
        
        Args:
            database_file: 数据库文件路径，默认为内存数据库
        """
        # 确保数据库文件在项目根目录
        if database_file != ":memory:" and not os.path.isabs(database_file):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            database_file = os.path.join(project_root, database_file)
            
        self.databases: Dict[str, EnhancedDatabase] = {}
        self.current_database_name: str = "main"
        self.current_database: Optional[EnhancedDatabase] = None
        self.active_database: Optional[str] = None  # 跟踪当前使用的数据库
        
        # 初始化默认数据库
        self._initialize_database(database_file)
        
        # 注意：不要在这里重新设置为None，因为_initialize_database已经正确设置了这些属性
        # self.executor: SQLExecutor = None
        # self.transaction_manager: TransactionManager = None
        self.current_transaction: Optional[int] = None
        self.input_buffer = EnhancedInputBuffer()
        
    def _initialize_database(self, database_file: str) -> None:
        """初始化数据库连接。
        
        Args:
            database_file: 数据库文件路径
        """
        try:
            # 确保文件路径是绝对路径，以保证日志文件在正确的目录中创建
            if database_file != ":memory:":
                abs_database_file = os.path.abspath(database_file)
            else:
                abs_database_file = database_file
            self.current_database = EnhancedDatabase(abs_database_file)
            self.databases[self.current_database_name] = self.current_database
            self.executor = SQLExecutor(self.current_database)
            self.transaction_manager = self.current_database.transaction_manager
        except Exception as e:
            print(f"初始化数据库失败: {e}")
            # 回退到内存数据库
            self.current_database = EnhancedDatabase(":memory:")
            self.databases[self.current_database_name] = self.current_database
            self.executor = SQLExecutor(self.current_database)
            self.transaction_manager = self.current_database.transaction_manager
    
    def _switch_database(self, database_name: str) -> bool:
        """切换到不同的数据库。
        
        在切换数据库前会回滚当前活动的事务，确保数据一致性。
        
        Args:
            database_name: 目标数据库名称
            
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        if database_name in self.databases:
            # 切换前关闭当前事务
            if self.current_transaction:
                self.transaction_manager.rollback_transaction(self.current_transaction)
                self.current_transaction = None
                print("已回滚活动事务")
                
            self.current_database_name = database_name
            self.current_database = self.databases[database_name]
            self.executor = SQLExecutor(self.current_database)
            self.transaction_manager = self.current_database.transaction_manager
            self.active_database = database_name  # 标记此数据库为活动
            return True
        else:
            # 尝试打开现有数据库文件
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, f"{database_name}.db")
            
            if os.path.exists(db_path):
                try:
                    # 确保文件路径是绝对路径，以保证日志文件在正确的目录中创建
                    abs_db_path = os.path.abspath(db_path)
                    new_db = EnhancedDatabase(abs_db_path)
                    self.databases[database_name] = new_db
                    
                    # 切换前关闭当前事务
                    if self.current_transaction:
                        self.transaction_manager.rollback_transaction(self.current_transaction)
                        self.current_transaction = None
                        print("已回滚活动事务")
                    
                    self.current_database_name = database_name
                    self.current_database = new_db
                    self.executor = SQLExecutor(new_db)
                    self.transaction_manager = new_db.transaction_manager
                    self.active_database = database_name  # 标记此数据库为活动
                    return True
                except Exception as e:
                    print(f"无法打开数据库 '{database_name}': {e}")
                    return False
            else:
                print(f"数据库 '{database_name}' 不存在")
                return False
    
    def run(self) -> None:
        """运行REPL主循环。
        
        提供交互式命令行界面，持续读取用户输入并执行相应的操作。
        """
        print("增强版SQLite数据库 - 支持完整SQL语法和ACID事务")
        print("功能特性:")
        print("- 完整的ACID事务支持")
        print("- 多线程/多进程安全")
        print("- 数据库备份/恢复功能")
        print("- DDL操作(CREATE/DROP/ALTER)")
        print("- 支持并发访问和文件锁")
        print("- 多数据库管理")
        print("=" * 60)
        print("输入'.help'获取帮助，'.exit'退出程序")
        
        while True:
            try:
                # 更新提示符显示当前数据库
                prompt = f"SQLite [{self.current_database_name}]> "
                try:
                    input_line = input(prompt).strip()
                except EOFError:
                    input_line = ".exit"
                
                if not input_line:
                    continue
                
                if input_line.startswith('.'):
                    if not self.process_meta_command(input_line):
                        break
                    continue
                
                # 检查USE命令
                upper_line = input_line.upper().strip()
                if upper_line.startswith('USE '):
                    db_name = input_line[4:].strip().strip('"').strip("'")
                    if self._switch_database(db_name):
                        print(f"已切换到数据库: {db_name}")
                    continue
                
                # 处理SQL语句
                self.process_statement(input_line)
                
            except KeyboardInterrupt:
                print("\n请使用'.exit'退出程序")
            except Exception as e:
                print(f"Error: {e}")
    
    def process_meta_command(self, command: str) -> bool:
        """处理元命令（以.开头的命令）。
        
        Args:
            command: 元命令字符串
            
        Returns:
            bool: 返回False表示退出程序，True表示继续运行
        """
        command = command.lower()
        
        if command == '.exit':
            self.close()
            return False
        elif command == '.help':
            self.print_help()
        elif command == '.tables':
            self.print_tables()
        elif command == '.schema':
            self.print_schema()
        elif command == '.backup':
            self.create_backup()
        elif command == '.list-backups':
            self.list_backups()
        elif command == '.begin':
            self.begin_transaction()
        elif command == '.commit':
            self.commit_transaction()
        elif command == '.rollback':
            self.rollback_transaction()
        elif command == '.status':
            self.print_status()
        elif command == '.databases':
            self.print_databases()
        else:
            print(f"无法识别的命令'{command}'，请输入'.help'获取帮助")
        return True
    
    def process_statement(self, statement: str) -> None:
        """处理SQL语句。
        
        解析并执行SQL语句，提供详细的错误处理和结果展示。
        
        Args:
            statement: SQL语句字符串
        """
        try:
            # 预解析以提供更好的错误信息
            parsed_result = EnhancedSQLParser.parse_statement(statement.strip())
            if parsed_result[0] != PrepareResult.SUCCESS:
                print(f"错误: {parsed_result[1] or '语法错误'}")
                return
            
            if self.current_transaction:
                result, data = self.executor.execute(statement, self.current_transaction)
            else:
                # 单条语句自动事务
                transaction_id = self.transaction_manager.begin_transaction()
                try:
                    result, data = self.executor.execute(statement, transaction_id)
                    self.transaction_manager.commit_transaction(transaction_id)
                except Exception as e:
                    self.transaction_manager.rollback_transaction(transaction_id)
                    raise e
            
            if result == PrepareResult.SUCCESS:
                # 检查是否是SELECT结果（字典列表格式）
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    # SELECT结果是字典列表（包含别名信息）
                    if data:
                        # 从字典键中提取列名
                        columns = list(data[0].keys()) if data else []
                        self.print_select_results_with_columns(data, columns)
                    else:
                        print("(0 行)")
                elif isinstance(data, tuple) and len(data) == 2:
                    # SELECT结果包含列信息
                    rows, columns = data
                    if rows:
                        self.print_select_results_with_columns(rows, columns)
                    else:
                        print("(0 行)")
                elif isinstance(data, list):
                    # SELECT结果不包含列信息（遗留）
                    if data:
                        # 遗留结果也使用适当的列处理
                        columns = self._infer_columns_from_rows(data)
                        self.print_select_results_with_columns(data, columns)
                    else:
                        print("(0 rows)")
                elif isinstance(data, int):
                    # INSERT/UPDATE/DELETE计数
                    if data == 0:
                        print("查询成功，0 行受影响。(未找到匹配行)")
                    else:
                        print(f"查询成功，{data} 行受影响。")
                elif isinstance(data, bool):
                    # DDL操作
                    print("查询成功。")
                else:
                    print("Query OK.")
            elif result.value == 4:  # TABLE_NOT_FOUND
                print("错误: 表不存在")
            else:
                print(f"错误: {data}")
                
        except Exception as e:
            # 提供更友好的错误信息
            error_msg = str(e)
            if "WHERE" in statement.upper() and "WHERE" not in statement.upper().replace("WHERE", "").strip():
                print("错误: WHERE子句语法无效")
            elif "DELETE" in statement.upper() and "WHERE" not in statement.upper():
                print("警告: DELETE语句没有WHERE子句将影响所有行")
                print(f"错误: {error_msg}")
            elif "UPDATE" in statement.upper() and "WHERE" not in statement.upper():
                print("警告: UPDATE语句没有WHERE子句将影响所有行")
                print(f"错误: {error_msg}")
            elif "表" in error_msg and "不存在" in error_msg:
                print(f"错误: {error_msg}")
            elif "无法删除包含数据的表" in error_msg:
                print(f"错误: {error_msg}")
            else:
                print(f"错误: {error_msg}")
    
    def _infer_columns_from_rows(self, rows: List[Any]) -> List[str]:
        """从行数据中推断列名（用于遗留结果）。
        
        Args:
            rows: 行数据列表
            
        Returns:
            List[str]: 推断出的列名列表
        """
        if not rows:
            return []
        
        # 尝试从第一行获取列名
        first_row = rows[0]
        # 使用getattr安全地访问data属性
        row_data = getattr(first_row, 'data', None)
        if row_data is not None:
            # 确保row_data是字典类型
            if isinstance(row_data, dict):
                return list(row_data.keys())
        
        # 如果没有数据结构，回退到通用列名
        return ['id', 'name']  # 通用回退

    def print_select_results_with_columns(self, rows: List[Any], columns: List[str]):
        """以表格形式打印SELECT查询结果。
        
        Args:
            rows: 查询结果行列表
            columns: 列名列表
        """
        if not rows:
            print("(0 行)")
            return
            
        # 打印表头
        header = " | ".join(columns)
        print(header)
        print("-" * len(header))
        
        # 打印数据行
        for row in rows:
            values = []
            for col in columns:
                # 处理Row对象和字典对象
                value = 'NULL'
                # 使用getattr安全地访问data属性
                row_data = getattr(row, 'data', None)
                if row_data is not None:
                    # Row对象包含数据字典
                    if isinstance(row_data, dict) and col in row_data:
                        val = row_data.get(col)
                        value = 'NULL' if val is None else str(val)
                elif isinstance(row, dict):
                    # 字典对象（来自execute_select）
                    val = row.get(col)
                    value = 'NULL' if val is None else str(val)
                else:
                    # 尝试从行属性获取
                    try:
                        val = getattr(row, col)
                        value = 'NULL' if val is None else str(val)
                    except (AttributeError, KeyError):
                        value = 'NULL'
                values.append(value)
            print(" | ".join(values))
    
    def _get_table_name_from_rows(self, rows: List[Any]) -> Optional[str]:
        """从行对象中推断表名。
        
        Args:
            rows: 行数据列表
            
        Returns:
            Optional[str]: 表名，如果无法推断返回None
        """
        if not rows:
            return None
        if hasattr(rows[0], '__table__'):
            return rows[0].__table__
        if hasattr(rows[0], 'table_name'):
            return rows[0].table_name
        return None
        
        print(f"\n({len(rows)} 行)")
    
    def print_help(self) -> None:
        """打印帮助信息。"""
        print("""增强版SQLite数据库帮助文档:
        
元命令:
  .exit                    退出程序
  .help                    显示本帮助信息
  .tables                  列出所有表
  .schema                  显示表结构
  .backup                  创建数据库备份
  .list-backups            列出可用备份
  .begin                   开始事务
  .commit                  提交当前事务
  .rollback                回滚当前事务
  .status                  显示数据库状态
  .databases               列出所有数据库

SQL命令示例:
CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT)
CREATE TABLE animal (id INTEGER PRIMARY KEY, name TEXT UNIQUE)
INSERT INTO users (id, username, email) VALUES (1, 'alice', 'alice@example.com')
INSERT INTO animal (name) VALUES ('Tom')
SELECT * FROM users
SELECT * FROM users WHERE id > 5
UPDATE users SET email = 'new@example.com' WHERE id = 1
DELETE FROM users WHERE id = 1
DROP TABLE users
DROP TABLE animal

数据库切换:
  USE database_name         切换到指定数据库
  .databases               查看所有数据库

事务示例:
  BEGIN;
  INSERT INTO users VALUES (1, 'user1', 'user1@example.com');
  UPDATE users SET email = 'updated@example.com' WHERE id = 1;
  COMMIT;

备份示例:
  .backup
  .list-backups
""")
    
    def print_tables(self) -> None:
        """打印所有表信息。
        
        显示当前数据库中的所有表及其列信息。
        """
        # 只有在通过USE命令显式选择数据库时才显示表
        if self.active_database is None:
            print("未选择任何数据库。请使用 'USE 数据库名' 命令选择数据库。")
            return
            
        if self.current_database is None:
            print("数据库未初始化。")
            return
            
        tables = self.current_database.list_tables()
        if tables:
            print("Tables:")
            for table in tables:
                schema = self.current_database.get_table_schema(table)
                if schema:
                    columns = ", ".join(schema.columns.keys())
                    print(f"  {table} ({columns})")
        else:
            print("未找到任何表。")

    def print_schema(self) -> None:
        """打印表结构信息。
        
        显示当前数据库中所有表的详细结构，包括列名、数据类型、约束等。
        """
        if self.current_database is None:
            print("数据库未初始化。")
            return
            
        tables = self.current_database.list_tables()
        for table in tables:
            schema = self.current_database.get_table_schema(table)
            if schema:
                print(f"\nTable: {table}")
                print("Columns:")
                for col_name, col_def in schema.columns.items():
                    primary = " PRIMARY KEY" if col_def.is_primary else ""
                    nullable = " NOT NULL" if not col_def.is_nullable else ""
                    print(f"  {col_name} {col_def.data_type.value}{primary}{nullable}")

    def print_databases(self) -> None:
        """打印所有可用数据库。
        
        列出项目目录中所有的数据库文件。
        """
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 列出所有.db文件
        db_files = glob.glob(os.path.join(project_root, "*.db"))
        
        if db_files:
            print("\n项目中的数据库文件:")
            for db_file in db_files:
                print(f"  {os.path.basename(db_file)}\t\t{db_file}")
        else:
            print("未找到数据库文件")
    
    def create_backup(self):
        """创建数据库备份。
        
        为当前数据库创建备份文件，包含时间戳信息。
        """
        if self.current_database is None:
            print("数据库未初始化。")
            return
            
        try:
            backup_path = self.current_database.create_backup()
            print(f"备份已创建: {backup_path}")
        except Exception as e:
            print(f"备份失败: {e}")

    def list_backups(self):
        """列出可用备份。
        
        显示当前数据库的所有备份文件及其详细信息。
        """
        if self.current_database is None:
            print("数据库未初始化。")
            return
            
        try:
            backups = self.current_database.list_backups()
            if backups:
                print("Available backups:")
                for backup in backups:
                    print(f"  {backup['name']} - {backup['created']} ({backup['size']} bytes)")
            else:
                print("未找到任何备份。")
        except Exception as e:
            print(f"列出备份失败: {e}")
    
    def begin_transaction(self):
        """开始新事务。
        
        如果当前已有活动事务，则提示用户。
        """
        if self.current_transaction:
            print("事务已处于活动状态")
            return
            
        self.current_transaction = self.transaction_manager.begin_transaction()
        print(f"事务 {self.current_transaction} 已开始")
    
    def commit_transaction(self):
        """提交当前事务。
        
        将当前事务的所有更改永久保存到数据库。
        """
        if not self.current_transaction:
            print("没有活动的事务")
            return
            
        try:
            self.transaction_manager.commit_transaction(self.current_transaction)
            print(f"事务 {self.current_transaction} 已提交")
            self.current_transaction = None
        except Exception as e:
            print(f"提交失败: {e}")
    
    def rollback_transaction(self):
        """回滚当前事务。
        
        撤销当前事务的所有更改，恢复到事务开始前的状态。
        """
        if not self.current_transaction:
            print("没有活动的事务")
            return
            
        try:
            self.transaction_manager.rollback_transaction(self.current_transaction)
            print(f"事务 {self.current_transaction} 已回滚")
            self.current_transaction = None
        except Exception as e:
            print(f"回滚失败: {e}")
    
    def print_status(self):
        """打印数据库状态信息。
        
        显示当前数据库的详细信息，包括文件大小、表数量、活动事务等。
        """
        if self.current_database is None:
            print("数据库未初始化。")
            return
            
        info = self.current_database.get_database_info()
        print("\n数据库状态:")
        print(f"  当前数据库: {self.current_database_name}")
        print(f"  文件: {info['filename']}")
        print(f"  大小: {info['file_size']} 字节")
        print(f"  页数: {info['num_pages']}")
        print(f"  表数量: {len(info['tables'])}")
        print(f"  活动事务: {info['active_transactions']}")
        print(f"  备份数量: {len(info['backups'])}")
    
    def close(self) -> None:
        """关闭数据库连接并退出程序。
        
        在退出前会回滚任何活动的事务，并关闭所有数据库连接。
        """
        if self.current_transaction:
            self.transaction_manager.rollback_transaction(self.current_transaction)
            print("已回滚活动事务")
        
        # 关闭所有数据库
        for db in self.databases.values():
            db.close()
        
        print("再见!")


def main():
    """主入口函数。
    
    处理命令行参数并启动REPL。
    """
    import sys
    
    if len(sys.argv) > 1:
        database_file = sys.argv[1]
    else:
        database_file = "test.db"
    
    repl = EnhancedREPL(database_file)
    repl.run()


# if __name__ == "__main__":
    # main()