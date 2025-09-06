"""增强型SQL解析器，支持DELETE、UPDATE、WHERE子句。

该模块提供了完整的SQL语句解析功能，支持：
- INSERT语句（支持多值组插入）
- SELECT语句（支持WHERE、列别名）
- UPDATE语句（支持WHERE子句）
- DELETE语句（支持WHERE子句）
- CREATE TABLE语句（支持列定义）
- DROP TABLE语句

主要特性：
1. 完整的SQL语法解析
2. 类型安全的值解析
3. WHERE条件支持（=, !=, >, <, >=, <=, LIKE, IS NULL, IS NOT NULL）
4. 列别名支持
5. 错误处理和语法验证
"""

import re
from enum import Enum
from typing import Optional, Tuple, List, Any, Dict
from .models import DataType  # 使用统一的数据类型
from .models import Row, PrepareResult
from .constants import USERNAME_SIZE, EMAIL_SIZE


class StatementType(Enum):
    """增强的语句类型枚举。
    
    定义了解析器支持的所有SQL语句类型。
    
    Attributes:
        INSERT: 插入语句
        SELECT: 查询语句
        UPDATE: 更新语句
        DELETE: 删除语句
        CREATE_TABLE: 创建表语句
        DROP_TABLE: 删除表语句
    """
    INSERT = "INSERT"
    SELECT = "SELECT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE_TABLE = "CREATE_TABLE"
    DROP_TABLE = "DROP_TABLE"


class WhereCondition:
    """增强的WHERE子句条件，支持更好的类型处理。
    
    表示SQL WHERE子句中的单个条件，支持多种操作符和类型转换。
    
    Attributes:
        column: 列名
        operator: 操作符（=, !=, >, <, >=, <=, LIKE, IS NULL, IS NOT NULL）
        value: 比较值
    
    Examples:
        >>> condition = WhereCondition("age", ">", 25)
        >>> condition.evaluate(row)
        True
    """
    
    def __init__(self, column: str, operator: str, value: Any):
        """初始化WHERE条件。
        
        Args:
            column: 列名
            operator: 操作符
            value: 比较值
        """
        self.column = column
        # 规范化操作符，但保留原始格式以避免混淆
        self.operator = operator
        self.value = value
        
    def __repr__(self):
        """字符串表示。
        
        Returns:
            str: 条件的字符串表示
        """
        return f"WhereCondition(column='{self.column}', operator='{self.operator}', value={self.value!r})"
    
    def evaluate(self, row: Row) -> bool:
        """根据行数据评估条件。

        支持类型安全的比较，包括NULL值处理和LIKE操作符。

        Args:
            row: 行数据
            
        Returns:
            bool: 条件满足返回True
        """
        # 获取行值 - 支持多种行数据格式
        row_value = None
        
        # 优先使用get_value方法（标准Row对象）
        if hasattr(row, 'get_value'):
            row_value = row.get_value(self.column)
        # 其次使用data字典（兼容旧格式）
        elif hasattr(row, 'data'):
            row_value = row.data.get(self.column)
        # 最后尝试直接属性访问
        else:
            try:
                row_value = getattr(row, self.column, None)
            except AttributeError:
                pass
        
        # 处理NULL值检查操作符
        if self.operator == "IS NULL":
            return row_value is None
        elif self.operator == "IS NOT NULL":
            return row_value is not None
        
        # 如果行值为None，其他操作符返回False（NULL不等于任何值）
        if row_value is None:
            return False
        
        # 处理LIKE操作符 - 不区分大小写的模糊匹配
        if self.operator.upper() == "LIKE":
            pattern = str(self.value).lower()
            text = str(row_value).lower()
            return pattern in text
        
        # 类型转换和比较 - 确保类型安全
        # 初始化变量以确保在所有代码路径中都已定义
        original_self_value = self.value
        
        try:
            # 保存原始值用于错误处理
            original_row_value = row_value
            
            # 尝试将两个值都转换为数值类型进行比较
            row_numeric = None
            self_numeric = None
            
            # 转换行值为数值
            if isinstance(row_value, (int, float)):
                row_numeric = float(row_value)
            elif isinstance(row_value, str):
                try:
                    row_numeric = float(row_value)
                except ValueError:
                    pass  # 保持为None，后续按字符串处理
            
            # 转换比较值为数值
            if isinstance(self.value, (int, float)):
                self_numeric = float(self.value)
            elif isinstance(self.value, str):
                try:
                    self_numeric = float(self.value)
                except ValueError:
                    pass  # 保持为None，后续按字符串处理
            
            # 如果两个值都能转换为数值，则按数值比较
            if row_numeric is not None and self_numeric is not None:
                row_value = row_numeric
                self.value = self_numeric
            # 如果其中一个值是数值，另一个是字符串，则按字符串处理
            # 但只在操作符不是比较运算符时才这样做
            elif self.operator in ["=", "!="]:
                # 对于相等性比较，按字符串处理是可以接受的
                row_value = str(row_value)
                self.value = str(self.value)
            else:
                # 对于比较运算符（>, <, >=, <=），如果类型不匹配则返回False
                # 或者抛出异常，因为我们不能合理地比较不兼容的类型
                if (row_numeric is not None) != (self_numeric is not None):
                    # 一个能转为数值，另一个不能，无法比较
                    return False
                elif row_numeric is None and self_numeric is None:
                    # 两个都不能转为数值，对于比较运算符，尝试字符串比较
                    row_value = str(row_value)
                    self.value = str(self.value)
            
            # 根据操作符执行相应的比较
            if self.operator == "=":
                return row_value == self.value
            elif self.operator == "!=":
                return row_value != self.value
            elif self.operator == ">":
                return row_value > self.value
            elif self.operator == "<":
                return row_value < self.value
            elif self.operator == ">=":
                return row_value >= self.value
            elif self.operator == "<=":
                return row_value <= self.value
            else:
                return False
        except (TypeError, ValueError):
            # 类型转换失败时返回False
            # 恢复原始值以便调试
            self.value = original_self_value
            return False


class InsertStatement:
    """INSERT语句，支持多值组插入。
    
    表示SQL INSERT语句，支持插入多行数据。
    
    Attributes:
        table_name: 目标表名
        columns: 列名列表
        value_groups: 值组列表，每组对应一行数据
    
    Examples:
        >>> stmt = InsertStatement("users", ["id", "name"], [[1, "张三"], [2, "李四"]])
    """
    
    def __init__(self, table_name: str, columns: List[str], value_groups: List[List[Any]]):
        """初始化INSERT语句。
        
        Args:
            table_name: 表名
            columns: 列名列表
            value_groups: 值组列表
        """
        self.table_name = table_name
        self.columns = columns
        self.value_groups = value_groups
    
    def to_rows(self, schema=None) -> List[Row]:
        """将INSERT语句转换为行对象列表。

        根据提供的表模式验证列名，处理默认值，并确保数据完整性。
        支持主键自增、默认值应用、非空约束检查等高级功能。

        Args:
            schema: 表模式对象（可选），包含列定义和约束信息
            
        Returns:
            List[Row]: 转换后的行对象列表，每行包含所有列的值
            
        Raises:
            ValueError: 如果列验证失败、数据类型不匹配或违反约束
        """
        rows = []
        
        # 处理每个值组（支持批量插入）
        for values in self.value_groups:
            # 将提供的值与列名对应起来
            data = dict(zip(self.columns, values))
            
            # 初始化行数据字典
            row_data = {}
            
            # 如果提供了表模式，进行严格的模式验证
            if schema:
                # 第一步：验证所有提供的列名是否存在于表中
                for col in self.columns:
                    if col not in schema.columns:
                        raise ValueError(f"列 '{col}' 不存在于表 '{self.table_name}' 中")
                
                # 第二步：根据模式定义处理每一列
                for col_name, col_def in schema.columns.items():
                    # 情况1：用户提供了该列的值
                    if col_name in data:
                        row_data[col_name] = data[col_name]
                    # 情况2：列有默认值
                    elif col_def.default_value is not None:
                        row_data[col_name] = col_def.default_value
                    # 情况3：INTEGER主键（通常用于自增）
                    elif col_def.is_primary and col_def.data_type.name == 'INTEGER':
                        # 设置为None，让数据库处理自增
                        row_data[col_name] = None
                    # 情况4：自增列
                    elif col_def.is_primary and col_def.is_autoincrement:
                        # 设置为None，让数据库处理自增
                        row_data[col_name] = None
                    # 情况5：非空约束检查
                    elif not col_def.is_nullable:
                        raise ValueError(f"列 '{col_name}' 定义为NOT NULL且不能为NULL")
                    # 情况6：使用类型默认值
                    else:
                        # 根据数据类型提供合理的默认值
                        if col_def.data_type.name == 'INTEGER':
                            row_data[col_name] = 0
                        elif col_def.data_type.name == 'REAL':
                            row_data[col_name] = 0.0
                        elif col_def.data_type.name == 'TEXT':
                            row_data[col_name] = ''
                        elif col_def.data_type.name == 'BOOLEAN':
                            row_data[col_name] = False
                        else:
                            row_data[col_name] = None
            else:
                # 无模式时的向后兼容处理：直接使用提供的值
                for col, val in zip(self.columns, values):
                    row_data[col] = val
            
            # 创建Row对象并添加到结果列表
            rows.append(Row(**row_data))
        
        return rows
    
    def __repr__(self):
        """字符串表示。
        
        Returns:
            str: 语句的字符串表示
        """
        return f"InsertStatement(table_name='{self.table_name}', columns={self.columns}, value_groups={self.value_groups})"


class SelectStatement:
    """SELECT语句，支持WHERE子句。
    
    表示SQL SELECT查询语句。
    
    Attributes:
        table_name: 表名
        columns: 要查询的列列表
        where_clause: WHERE条件
        alias_mapping: 列别名映射
    """
    
    def __init__(self, table_name: str, columns: List[str] = None, where_clause: WhereCondition = None, alias_mapping: Dict[str, str] = None):
        """初始化SELECT语句。
        
        Args:
            table_name: 表名
            columns: 列名列表，None表示所有列
            where_clause: WHERE条件
            alias_mapping: 列别名映射
        """
        self.table_name = table_name
        self.columns = columns or ['*']
        self.where_clause = where_clause
        self.alias_mapping = alias_mapping or {}
    
    def __repr__(self):
        """字符串表示。
        
        Returns:
            str: 语句的字符串表示
        """
        return f"SelectStatement(table_name='{self.table_name}', columns={self.columns}, where_clause={self.where_clause})"


class UpdateStatement:
    """UPDATE语句。
    
    表示SQL UPDATE更新语句。
    
    Attributes:
        table_name: 表名
        updates: 更新字典（列名 -> 新值）
        where_clause: WHERE条件
    """
    
    def __init__(self, table_name: str, updates: Dict[str, Any], where_clause: WhereCondition = None):
        """初始化UPDATE语句。
        
        Args:
            table_name: 表名
            updates: 更新字典
            where_clause: WHERE条件
        """
        self.table_name = table_name
        self.updates = updates
        self.where_clause = where_clause
    
    def __repr__(self):
        """字符串表示。
        
        Returns:
            str: 语句的字符串表示
        """
        return f"UpdateStatement(table_name='{self.table_name}', updates={self.updates}, where_clause={self.where_clause})"


class DeleteStatement:
    """DELETE语句。
    
    表示SQL DELETE删除语句。
    
    Attributes:
        table_name: 表名
        where_clause: WHERE条件
    """
    
    def __init__(self, table_name: str, where_clause: WhereCondition = None):
        """初始化DELETE语句。
        
        Args:
            table_name: 表名
            where_clause: WHERE条件
        """
        self.table_name = table_name
        self.where_clause = where_clause
    
    def __repr__(self):
        """字符串表示。
        
        Returns:
            str: 语句的字符串表示
        """
        return f"DeleteStatement(table_name='{self.table_name}', where_clause={self.where_clause})"


class CreateTableStatement:
    """CREATE TABLE语句。
    
    表示SQL CREATE TABLE创建表语句。
    
    Attributes:
        table_name: 表名
        columns: 列定义字典（列名 -> (数据类型, 是否主键, 是否自增, 是否唯一, 是否非空)）
    """
    
    def __init__(self, table_name: str, columns: Dict[str, Tuple[DataType, bool, bool, bool, bool]]):
        """初始化CREATE TABLE语句。
        
        Args:
            table_name: 表名
            columns: 列定义字典
        """
        self.table_name = table_name
        self.columns = columns  # Dict[str, (DataType, is_primary, is_autoincrement, is_unique, is_not_null)]
    
    def __repr__(self):
        """字符串表示。
        
        Returns:
            str: 语句的字符串表示
        """
        return f"CreateTableStatement(table_name='{self.table_name}', columns={list(self.columns.keys())})"


class DropTableStatement:
    """DROP TABLE语句。
    
    表示SQL DROP TABLE删除表语句。
    
    Attributes:
        table_name: 表名
    """
    
    def __init__(self, table_name: str):
        """初始化DROP TABLE语句。
        
        Args:
            table_name: 表名
        """
        self.table_name = table_name
    
    def __repr__(self):
        """字符串表示。
        
        Returns:
            str: 语句的字符串表示
        """
        return f"DropTableStatement(table_name='{self.table_name}')"


class EnhancedSQLParser:
    """增强型SQL解析器，提供完整的SQL语法解析功能。
    
    支持INSERT、SELECT、UPDATE、DELETE、CREATE TABLE、DROP TABLE等语句的解析，
    并提供详细的错误处理和语法验证。
    
    Examples:
        >>> result = EnhancedSQLParser.parse_statement("SELECT * FROM users WHERE age > 25")
        >>> if result[0] == PrepareResult.SUCCESS:
        ...     statement = result[1]
        ...     print(statement.table_name)  # users
    """
    
    @staticmethod
    def parse_statement(input_buffer: str) -> Tuple[PrepareResult, Optional[Any]]:
        """解析SQL语句。
        
        根据输入的SQL语句字符串，解析为相应的语句对象。
        
        Args:
            input_buffer: SQL语句字符串
            
        Returns:
            Tuple[PrepareResult, Optional[Any]]: (解析结果, 语句对象或错误信息)
        """
        input_buffer = input_buffer.strip()
        
        if not input_buffer:
            return PrepareResult.UNRECOGNIZED_STATEMENT, None
        
        # 转换为大写以便更容易解析
        upper_buffer = input_buffer.upper()
        
        if upper_buffer.startswith("INSERT"):
            return EnhancedSQLParser._parse_insert(input_buffer)
        elif upper_buffer.startswith("SELECT"):
            return EnhancedSQLParser._parse_select(input_buffer)
        elif upper_buffer.startswith("UPDATE"):
            return EnhancedSQLParser._parse_update(input_buffer)
        elif upper_buffer.startswith("DELETE"):
            return EnhancedSQLParser._parse_delete(input_buffer)
        elif upper_buffer.startswith("CREATE TABLE"):
            return EnhancedSQLParser._parse_create_table(input_buffer)
        elif upper_buffer.startswith("DROP TABLE"):
            return EnhancedSQLParser._parse_drop_table(input_buffer)
        else:
            return PrepareResult.UNRECOGNIZED_STATEMENT, None
    
    @staticmethod
    def _parse_insert(input_buffer: str) -> Tuple[PrepareResult, Optional[InsertStatement]]:
        """解析INSERT语句，支持多值组插入和复杂值解析。

        支持标准INSERT语法，包括：
        - INSERT INTO table_name (col1, col2) VALUES (val1, val2)
        - INSERT INTO table_name (col1, col2) VALUES (val1, val2), (val3, val4)
        - 支持字符串中的逗号和括号
        - 支持NULL值和空值处理

        Args:
            input_buffer: INSERT语句字符串
            
        Returns:
            Tuple[PrepareResult, Optional[InsertStatement]]: (解析结果, INSERT语句对象或错误信息)
        """
        # 使用正则表达式提取基本结构：表名、列名、值部分
        pattern = r'INSERT\s+INTO\s+(\w+)\s*(?:\(([^)]*)\))?\s*VALUES\s*(.*)'
        match = re.match(pattern, input_buffer, re.IGNORECASE)
        
        if not match:
            return PrepareResult.SYNTAX_ERROR, "Invalid INSERT syntax"
        
        # 提取匹配的组
        table_name = match.group(1)  # 表名
        columns_str = match.group(2).strip() if match.group(2) else ""  # 列名部分
        values_str = match.group(3).strip() if match.group(3) else ""  # 值部分
        
        # 初始化值组列表
        value_groups = []
        in_quotes = False  # 标记是否在引号内
        quote_char = None  # 记录当前引号字符
        current_group = ""  # 当前处理的值组
        paren_count = 0  # 括号计数器
        
        # 手动解析值组，正确处理引号和嵌套括号
        for char in values_str:
            if char in ["'", '"'] and not in_quotes:
                # 开始引号
                in_quotes = True
                quote_char = char
                current_group += char
            elif char == quote_char and in_quotes:
                # 结束引号
                in_quotes = False
                quote_char = None
                current_group += char
            elif char == '(' and not in_quotes:
                # 开始括号
                if paren_count == 0:
                    # 新的值组开始
                    current_group = ""
                else:
                    current_group += char
                paren_count += 1
            elif char == ')' and not in_quotes:
                # 结束括号
                paren_count -= 1
                if paren_count == 0:
                    # 值组结束
                    value_groups.append(current_group.strip())
                    current_group = ""
                else:
                    current_group += char
            elif char == ',' and not in_quotes and paren_count == 0:
                # 值组之间的逗号，忽略
                continue
            else:
                current_group += char
        
        # 处理最后一个值组（如果没有被括号捕获）
        if current_group.strip() and not value_groups:
            value_groups = [current_group.strip()]
        
        # 如果没有找到值组，尝试旧式解析
        if not value_groups:
            if values_str.startswith('(') and values_str.endswith(')'):
                value_groups = [values_str[1:-1].strip()]
            else:
                return PrepareResult.SYNTAX_ERROR, "Invalid VALUES syntax"
        
        # 解析每个值组为值列表
        all_values = []
        for group in value_groups:
            values = []
            if not group.strip():
                # 空值组
                values = []
            else:
                # 使用更智能的分割处理引号内的逗号
                current_value = ""
                in_quotes = False
                quote_char = None
                
                for char in group + ",":  # 添加结尾逗号确保处理最后一个值
                    if char in ["'", '"'] and not in_quotes:
                        in_quotes = True
                        quote_char = char
                        current_value += char
                    elif char == quote_char and in_quotes:
                        in_quotes = False
                        quote_char = None
                        current_value += char
                    elif char == ',' and not in_quotes:
                        # 值分隔符
                        stripped_val = current_value.strip()
                        if stripped_val == "":
                            values.append(None)  # 空值视为NULL
                        else:
                            values.append(EnhancedSQLParser._parse_value(stripped_val))
                        current_value = ""
                    else:
                        current_value += char
            
            all_values.append(values)
        
        try:
            # 解析列名列表
            columns = []
            if columns_str:
                columns = [col.strip() for col in columns_str.split(',') if col.strip()]
            
            # 验证列名格式（只允许字母数字和下划线）
            for col in columns:
                if not col.replace('_', '').isalnum():
                    return PrepareResult.SYNTAX_ERROR, f"Invalid column name: {col}"
            
            # 验证所有值组的长度一致性
            if columns:
                expected_length = len(columns)
                for i, values in enumerate(all_values):
                    if len(values) != expected_length:
                        return PrepareResult.SYNTAX_ERROR, \
                            f"值组 {i+1} 有 {len(values)} 个值，但期望 {expected_length} 个值（对应 {len(columns)} 列）"
            
            # 验证列名和值的对应关系
            if not columns and all_values and any(all_values):
                return PrepareResult.SYNTAX_ERROR, "提供值时必须指定列名"
            
            return PrepareResult.SUCCESS, InsertStatement(table_name, columns, all_values)
        except (ValueError, IndexError) as e:
            return PrepareResult.SYNTAX_ERROR, str(e)
    
    @staticmethod
    def _parse_select(input_buffer: str) -> Tuple[PrepareResult, Optional[SelectStatement]]:
        """解析SELECT语句，支持增强功能包括列别名和复杂WHERE条件。

        支持标准SELECT语法，包括：
        - SELECT * FROM table_name
        - SELECT col1, col2 FROM table_name WHERE condition
        - SELECT col1 AS alias1, col2 alias2 FROM table_name
        - 支持列别名（AS关键字或空格分隔）
        - 支持WHERE子句中的复杂条件

        Args:
            input_buffer: SELECT语句字符串
            
        Returns:
            Tuple[PrepareResult, Optional[SelectStatement]]: (解析结果, SELECT语句对象或错误信息)
        """
        # 使用正则表达式匹配SELECT语句的基本结构
        # (?is)标志：i=忽略大小写，s=点号匹配换行符
        pattern = re.compile(
            r'(?is)SELECT\s+(.*?)\s+FROM\s+(\w+)(?:\s+WHERE\s+(.*))?$'
        )
        match = pattern.match(input_buffer)
        
        if not match:
            # 处理简单的SELECT语句（无FROM子句）
            if input_buffer.upper().strip() == "SELECT":
                return PrepareResult.SUCCESS, SelectStatement(table_name="users")
            return PrepareResult.SYNTAX_ERROR, None
        
        # 提取匹配的组
        columns_str = match.group(1).strip()  # 列部分
        table_name = match.group(2).strip()   # 表名
        where_clause_str = match.group(3).strip() if match.group(3) else None  # WHERE条件
        
        # 初始化别名映射和列列表
        alias_mapping = {}  # 列名 -> 别名映射
        columns = []        # 实际列名列表
        
        # 分割列表达式（处理逗号分隔的列列表）
        column_exprs = [expr.strip() for expr in re.split(r',', columns_str) if expr.strip()]
        
        # 解析每个列表达式
        for expr in column_exprs:
            expr = expr.strip()
            
            # 情况1：使用AS关键字的显式别名
            if ' as ' in expr.lower():
                parts = re.split(r' as ', expr, flags=re.IGNORECASE)
                if len(parts) >= 2:
                    col_expr = parts[0].strip()
                    alias = parts[1].strip()
                    columns.append(col_expr)
                    alias_mapping[col_expr] = alias
            # 情况2：使用空格的隐式别名
            elif re.search(r'\s+', expr) and not expr.startswith("'") and not expr.startswith('"'):
                # 分割第一个空格作为分隔符
                parts = re.split(r'\s+', expr, 1)
                if len(parts) >= 2:
                    col_expr = parts[0].strip()
                    alias = parts[1].strip()
                    # 确保别名是有效的标识符
                    if alias.replace('_', '').isalnum():
                        columns.append(col_expr)
                        alias_mapping[col_expr] = alias
                    else:
                        columns.append(expr)
                else:
                    columns.append(expr)
            else:
                # 情况3：无别名，直接使用表达式
                columns.append(expr)
        
        # 处理通配符*
        if len(columns) == 1 and columns[0] == '*':
            columns = ['*']  # 保持通配符
            alias_mapping = {}
        
        # 解析WHERE子句（如果存在）
        where_clause = None
        if where_clause_str:
            try:
                where_clause = EnhancedSQLParser._parse_where(where_clause_str)
            except ValueError as e:
                return PrepareResult.SYNTAX_ERROR, f"Invalid WHERE clause: {str(e)}"
        
        return PrepareResult.SUCCESS, SelectStatement(
            table_name=table_name,
            columns=columns,
            where_clause=where_clause,
            alias_mapping=alias_mapping
        )
    
    @staticmethod
    def _parse_update(input_buffer: str) -> Tuple[PrepareResult, Optional[UpdateStatement]]:
        """解析UPDATE语句，支持复杂更新表达式和容错处理。

        支持标准UPDATE语法，包括：
        - UPDATE table_name SET col1=val1, col2=val2 WHERE condition
        - UPDATE table_name SET col1=val1, col2=val2 （无WHERE子句，更新所有行）
        - 支持常见拼写错误的容错处理（WHERE/WEHRE/WERE）
        - 支持引号内的等号

        Args:
            input_buffer: UPDATE语句字符串
            
        Returns:
            Tuple[PrepareResult, Optional[UpdateStatement]]: (解析结果, UPDATE语句对象或错误信息)
        """
        # 主模式：UPDATE table_name SET col1=val1, col2=val2 [WHERE condition]
        # 使用非贪婪匹配处理SET部分，支持WHERE子句的容错
        pattern = r'UPDATE\s+(\w+)\s+SET\s+(.+?)(?:\s+(?:WHERE|WEHRE|WERE)\s+(.+))?$'
        match = re.match(pattern, input_buffer, re.IGNORECASE)
        
        if not match:
            # 回退到手动解析，提供更好的错误处理
            parts = input_buffer.upper().split()
            if len(parts) >= 4 and parts[0] == 'UPDATE' and 'SET' in parts:
                # 找到SET关键字的位置
                set_start = input_buffer.upper().find('SET')
                if set_start == -1:
                    return PrepareResult.SYNTAX_ERROR, "缺少SET关键字"
                
                # 找到WHERE关键字的位置（支持拼写错误）
                where_start = -1
                where_keywords = ['WHERE', 'WEHRE', 'WERE']
                for keyword in where_keywords:
                    pos = input_buffer.upper().find(keyword)
                    if pos != -1 and pos > set_start:
                        where_start = pos
                        break
                
                # 提取SET部分和WHERE部分
                set_str = ""
                where_str = None
                
                if where_start != -1 and where_start > set_start:
                    # 有WHERE子句
                    set_str = input_buffer[set_start + 3:where_start].strip()
                    where_str = input_buffer[where_start + 5:].strip()
                else:
                    # 无WHERE子句
                    set_str = input_buffer[set_start + 3:].strip()
                
                try:
                    # 解析SET部分为键值对
                    updates = {}
                    # 使用更智能的分割处理引号内的逗号
                    assignments = EnhancedSQLParser._split_assignments(set_str)
                    
                    for assignment in assignments:
                        if '=' not in assignment:
                            return PrepareResult.SYNTAX_ERROR, f"无效的赋值表达式: {assignment}"
                        
                        # 分割第一个等号，保留其余部分作为值
                        parts = assignment.split('=', 1)
                        col = parts[0].strip()
                        val = parts[1].strip()
                        
                        # 验证列名格式
                        if not col.replace('_', '').isalnum():
                            return PrepareResult.SYNTAX_ERROR, f"无效的列名: {col}"
                        
                        updates[col] = EnhancedSQLParser._parse_value(val)
                    
                    # 解析WHERE子句（如果存在）
                    where_clause = None
                    if where_str:
                        try:
                            where_clause = EnhancedSQLParser._parse_where(where_str)
                        except ValueError as e:
                            return PrepareResult.SYNTAX_ERROR, str(e)
                    
                    # 提取表名（UPDATE关键字后的第一个单词）
                    update_pos = input_buffer.upper().find('UPDATE')
                    table_name = input_buffer[update_pos + 6:set_start].strip()
                    
                    return PrepareResult.SUCCESS, UpdateStatement(table_name, updates, where_clause)
                except ValueError as e:
                    return PrepareResult.SYNTAX_ERROR, str(e)
            
            return PrepareResult.SYNTAX_ERROR, "无效的UPDATE语法"
        
        # 正则表达式匹配成功，提取各部分
        table_name = match.group(1)
        set_str = match.group(2)
        where_str = match.group(3)
        
        try:
            # 解析SET部分
            updates = {}
            assignments = EnhancedSQLParser._split_assignments(set_str)
            
            for assignment in assignments:
                if '=' not in assignment:
                    return PrepareResult.SYNTAX_ERROR, f"无效的赋值表达式: {assignment}"
                
                col, val = assignment.split('=', 1)
                col = col.strip()
                val = val.strip()
                
                # 验证列名
                if not col.replace('_', '').isalnum():
                    return PrepareResult.SYNTAX_ERROR, f"无效的列名: {col}"
                
                updates[col] = EnhancedSQLParser._parse_value(val)
            
            # 解析WHERE子句
            where_clause = None
            if where_str:
                try:
                    where_clause = EnhancedSQLParser._parse_where(where_str)
                except ValueError as e:
                    return PrepareResult.SYNTAX_ERROR, str(e)
            
            return PrepareResult.SUCCESS, UpdateStatement(table_name, updates, where_clause)
        except ValueError as e:
            return PrepareResult.SYNTAX_ERROR, str(e)
    
    @staticmethod
    def _parse_delete(input_buffer: str) -> Tuple[PrepareResult, Optional[DeleteStatement]]:
        """解析DELETE语句。
        
        支持标准DELETE语法，包括：
        - DELETE FROM table_name WHERE condition
        - 支持常见拼写错误的容错处理
        
        Args:
            input_buffer: DELETE语句字符串
            
        Returns:
            Tuple[PrepareResult, Optional[DeleteStatement]]: (解析结果, DELETE语句对象或错误信息)
        """
        # Pattern: DELETE FROM table_name [WHERE condition]
        # More flexible pattern to handle common typos and variations
        pattern = r'DELETE\s+FROM\s+(\w+)(?:\s+(?:WHERE|WEHRE|WERE)\s+(.+))?'
        match = re.match(pattern, input_buffer, re.IGNORECASE)
        
        if not match:
            # Try simpler pattern for basic DELETE
            parts = input_buffer.upper().split()
            if len(parts) >= 3 and parts[0] == 'DELETE' and parts[1] == 'FROM':
                table_name = parts[2]
                # Check if there's more content after table name
                remaining = input_buffer[len('DELETE FROM ' + table_name):].strip()
                if remaining.upper().startswith('WHERE'):
                    where_str = remaining[5:].strip()  # Remove 'WHERE'
                    try:
                        where_clause = EnhancedSQLParser._parse_where(where_str)
                        return PrepareResult.SUCCESS, DeleteStatement(table_name, where_clause)
                    except ValueError:
                        return PrepareResult.SYNTAX_ERROR, f"Invalid WHERE clause: {where_str}"
                elif remaining:
                    # Handle common typos
                    where_match = re.search(r'(?:WHERE|WEHRE|WERE)\s+(.+)', remaining, re.IGNORECASE)
                    if where_match:
                        try:
                            where_clause = EnhancedSQLParser._parse_where(where_match.group(1))
                            return PrepareResult.SUCCESS, DeleteStatement(table_name, where_clause)
                        except ValueError:
                            return PrepareResult.SYNTAX_ERROR, f"Invalid WHERE clause: {where_match.group(1)}"
                    else:
                        return PrepareResult.SYNTAX_ERROR, f"Invalid syntax after table name: {remaining}"
                else:
                    return PrepareResult.SUCCESS, DeleteStatement(table_name, None)
            return PrepareResult.SYNTAX_ERROR, None
        
        table_name = match.group(1)
        where_str = match.group(2)
        where_clause = None
        
        if where_str:
            try:
                where_clause = EnhancedSQLParser._parse_where(where_str)
            except ValueError as e:
                return PrepareResult.SYNTAX_ERROR, str(e)
        
        return PrepareResult.SUCCESS, DeleteStatement(
            table_name=table_name,
            where_clause=where_clause
        )
    
    @staticmethod
    def _parse_create_table(input_buffer: str) -> Tuple[PrepareResult, Optional[CreateTableStatement]]:
        """解析CREATE TABLE语句，支持完整的列定义和约束。

        支持标准CREATE TABLE语法，包括：
        - CREATE TABLE table_name (col1 type1 constraints, col2 type2 constraints, ...)
        - 支持的数据类型：INTEGER, TEXT, REAL, BOOLEAN
        - 支持的约束：PRIMARY KEY, AUTOINCREMENT, UNIQUE, NOT NULL
        - 支持复合约束定义
        - 自动处理主键的非空约束

        Args:
            input_buffer: CREATE TABLE语句字符串
            
        Returns:
            Tuple[PrepareResult, Optional[CreateTableStatement]]: (解析结果, CREATE TABLE语句对象或错误信息)
        """
        # 正则表达式匹配CREATE TABLE语句
        # 支持多行和嵌套括号（虽然当前实现有限制）
        pattern = r'CREATE\s+TABLE\s+(\w+)\s*\(([^)]+)\)'
        match = re.match(pattern, input_buffer, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return PrepareResult.SYNTAX_ERROR, "无效的CREATE TABLE语法"
        
        table_name = match.group(1)
        columns_str = match.group(2)
        
        try:
            columns = {}
            
            # 使用正则分割列定义，避免括号内的逗号
            # 注意：这是一个简化实现，不处理复杂的嵌套结构
            col_definitions = re.split(r',\s*(?![^()]*\))', columns_str)
            
            for col_def in col_definitions:
                col_def = col_def.strip()
                if not col_def:
                    continue
                
                # 解析列定义格式：列名 类型 [约束...]
                col_parts = re.split(r'\s+', col_def.strip(), maxsplit=1)
                if len(col_parts) < 2:
                    return PrepareResult.SYNTAX_ERROR, f"无效的列定义: {col_def}"
                
                col_name = col_parts[0].strip()
                
                # 验证列名格式
                if not col_name.replace('_', '').isalnum():
                    return PrepareResult.SYNTAX_ERROR, f"无效的列名: {col_name}"
                
                rest = col_parts[1].strip()
                
                # 提取数据类型和约束部分
                type_match = re.match(r'(\w+)(?:\s*\((\d+)\))?\s*(.*)', rest, re.IGNORECASE)
                if not type_match:
                    return PrepareResult.SYNTAX_ERROR, f"无效的列类型: {rest}"
                
                col_type = type_match.group(1).upper()
                # type_size = type_match.group(2)  # 保留但不使用
                constraints = type_match.group(3).upper() if type_match.group(3) else ""
                
                # 映射字符串类型到DataType枚举
                try:
                    data_type = DataType.from_string(col_type)
                except KeyError:
                    return PrepareResult.SYNTAX_ERROR, f"不支持的数据类型: {col_type}"
                
                # 解析约束条件
                is_primary = "PRIMARY KEY" in constraints
                is_autoincrement = "AUTOINCREMENT" in constraints
                
                # 自动检测：INTEGER主键默认自增
                if is_primary and data_type == DataType.INTEGER and not is_autoincrement:
                    is_autoincrement = True
                
                is_unique = "UNIQUE" in constraints
                is_not_null = "NOT NULL" in constraints
                
                # 主键自动设置为NOT NULL
                if is_primary:
                    is_not_null = True
                
                # 存储列定义：(数据类型, 是否主键, 是否自增, 是否唯一, 是否非空)
                columns[col_name] = (data_type, is_primary, is_autoincrement, is_unique, is_not_null)
            
            # 验证至少有一列
            if not columns:
                return PrepareResult.SYNTAX_ERROR, "表必须至少包含一列"
                
            return PrepareResult.SUCCESS, CreateTableStatement(table_name, columns)
        except (ValueError, KeyError) as e:
            return PrepareResult.SYNTAX_ERROR, str(e)
    
    @staticmethod
    def _parse_drop_table(input_buffer: str) -> Tuple[PrepareResult, Optional[DropTableStatement]]:
        """解析DROP TABLE语句。
        
        支持标准DROP TABLE语法，包括大小写不敏感和额外空格处理。
        
        Args:
            input_buffer: DROP TABLE语句字符串
            
        Returns:
            Tuple[PrepareResult, Optional[DropTableStatement]]: (解析结果, DROP TABLE语句对象或错误信息)
        """
        # 更灵活的模式匹配，处理不同大小写和额外空格
        pattern = r'(?i)DROP\s+TABLE\s+(\w+)'
        match = re.match(pattern, input_buffer)
        
        if match:
            table_name = match.group(1)
            return PrepareResult.SUCCESS, DropTableStatement(table_name)
        else:
            # 尝试简单解析
            parts = input_buffer.upper().split()
            if len(parts) >= 3 and parts[0] == 'DROP' and parts[1] == 'TABLE':
                table_name = parts[2]
                return PrepareResult.SUCCESS, DropTableStatement(table_name)
            return PrepareResult.SYNTAX_ERROR, None
    
    @staticmethod
    def _parse_where(where_str: str) -> WhereCondition:
        """解析WHERE条件字符串为WhereCondition对象。
        
        支持多种操作符和条件格式，包括：
        - column = value
        - column != value
        - column > value
        - column LIKE 'pattern'
        - column IS NULL
        - column IS NOT NULL
        
        Args:
            where_str: WHERE条件字符串
            
        Returns:
            WhereCondition: WHERE条件对象
            
        Raises:
            ValueError: 如果条件格式无效
        """
        # Pattern: column operator value (supports newlines and extra whitespace)
        pattern = r'(\w+)\s*(=|!=|>|<|>=|<=|LIKE|IS\s+NULL|IS\s+NOT\s+NULL)\s*(.*)'
        match = re.match(pattern, where_str, re.IGNORECASE | re.DOTALL)
        if not match:
            # Fallback to simple operator splitting
            operators = ['>=', '<=', '!=', '=', '>', '<', 'LIKE']
            for op in operators:
                if op in where_str:
                    column, value = where_str.split(op, 1)
                    return WhereCondition(column.strip(), op.strip(), EnhancedSQLParser._parse_value(value.strip()))
            raise ValueError(f"Invalid WHERE condition: {where_str}")
        
        column = match.group(1)
        operator = match.group(2)  # 保持原始操作符格式
        value_str = match.group(3).strip()
        
        # Handle NULL conditions
        if operator.upper() == 'IS NULL':
            return WhereCondition(column, 'IS NULL', None)
        elif operator.upper() == 'IS NOT NULL':
            return WhereCondition(column, 'IS NOT NULL', None)
        
        # Parse value based on type
        value = EnhancedSQLParser._parse_value(value_str)
        return WhereCondition(column, operator, value)
    
    @staticmethod
    def _split_assignments(set_str: str) -> List[str]:
        """分割SET子句中的赋值表达式。
        
        Args:
            set_str: SET子句字符串
            
        Returns:
            赋值表达式列表
        """
        assignments = []
        current_assignment = ""
        in_quotes = False
        quote_char = None
        paren_count = 0
        
        for char in set_str:
            if char in ["'", '"'] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_assignment += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                current_assignment += char
            elif char == '(' and not in_quotes:
                paren_count += 1
                current_assignment += char
            elif char == ')' and not in_quotes:
                paren_count -= 1
                current_assignment += char
            elif char == ',' and not in_quotes and paren_count == 0:
                # 赋值表达式分隔符
                assignments.append(current_assignment.strip())
                current_assignment = ""
            else:
                current_assignment += char
        
        # 添加最后一个赋值表达式
        if current_assignment.strip():
            assignments.append(current_assignment.strip())
        
        return assignments

    @staticmethod
    def _parse_value(value_str: str) -> Any:
        """根据类型解析值。
        
        支持多种数据类型的解析，包括：
        - 字符串（单引号或双引号包裹）
        - 整数
        - 浮点数
        - 布尔值
        - NULL值
        
        Args:
            value_str: 值字符串
            
        Returns:
            Any: 解析后的值
        """
        value_str = value_str.strip()
        
        # Handle quoted values
        is_quoted = False
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            value_str = value_str[1:-1]
            is_quoted = True
        
        # Handle NULL
        if value_str.upper() == 'NULL':
            return None
        
        # Try integer - only attempt if quoted or contains only digits
        if is_quoted or value_str.isdigit():
            try:
                return int(value_str)
            except ValueError:
                pass
        
        # Try float - only attempt if quoted or contains digits and decimal point
        if is_quoted or (any(c.isdigit() for c in value_str) and '.' in value_str):
            try:
                return float(value_str)
            except ValueError:
                pass
        
        # Try boolean
        if value_str.upper() in ['TRUE', 'T', '1']:
            return True
        elif value_str.upper() in ['FALSE', 'F', '0']:
            return False
        
        # Return as string
        return value_str