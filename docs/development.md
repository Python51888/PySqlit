# PySQLit 开发指南

## 🎯 开发环境设置

### 1. 系统要求

#### 1.1 必需工具
- **Python**: 3.8+ (推荐 3.9+)
- **Git**: 2.20+
- **Make**: 用于构建任务 (Windows 可用 `make` 替代)

#### 1.2 推荐工具
- **IDE**: VS Code + Python 扩展
- **虚拟环境**: venv 或 conda
- **代码格式化**: black + isort
- **类型检查**: mypy
- **测试框架**: pytest
- **代码质量**: flake8 + pylint

### 2. 环境搭建

#### 2.1 快速开始
```bash
# 克隆项目
git clone https://gitee.com/Python51888/PySqlit.git
cd py-sqlit

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 验证安装
python -c "import pysqlit; print(pysqlit.__version__)"
```

#### 2.2 开发依赖
```bash
# 安装所有开发工具
pip install -r requirements-dev.txt

# 可选：安装额外工具
pip install pre-commit tox sphinx
```

#### 2.3 VS Code 配置
创建 `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestPath": "pytest",
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true
    }
}
```

## 🏗️ 项目结构

```
py-sqlit/
├── pysqlit/                    # 核心库
│   ├── __init__.py            # 包初始化
│   ├── database.py            # 主数据库类
│   ├── transaction.py         # 事务管理
│   ├── backup.py             # 备份恢复
│   ├── ddl.py                # DDL操作
│   ├── parser.py             # SQL解析器
│   ├── btree.py              # B树索引
│   ├── storage.py            # 存储引擎
│   ├── concurrent_storage.py # 并发存储
│   ├── models.py             # 数据模型
│   ├── exceptions.py         # 异常定义
│   ├── constants.py          # 常量定义
│   ├── integrity.py          # 完整性检查
│   ├── art.py               # ASCII艺术
│   └── repl.py              # 交互式界面
├── tests/                    # 测试套件
│   ├── __init__.py
│   ├── conftest.py          # pytest配置
│   ├── test_database.py     # 数据库测试
│   ├── test_transaction.py  # 事务测试
│   ├── test_backup.py       # 备份测试
│   ├── test_ddl.py         # DDL测试
│   ├── test_parser.py      # 解析器测试
│   ├── test_btree.py       # B树测试
│   ├── test_storage.py     # 存储测试
│   ├── test_integration.py # 集成测试
│   └── fixtures/           # 测试数据
├── docs/                   # 文档
├── examples/              # 示例代码
├── scripts/              # 构建脚本
├── .gitee/              # Gitee工作流
├── Makefile             # 构建任务
├── pyproject.toml       # 项目配置
├── pytest.ini          # 测试配置
├── tox.ini            # 多环境测试
└── requirements*.txt  # 依赖文件
```

## 🛠️ 开发工作流

### 1. 分支策略
- **main**: 生产分支，稳定版本
- **develop**: 开发分支，集成测试
- **feature/**: 功能分支，新功能开发
- **bugfix/**: 修复分支，bug修复
- **hotfix/**: 紧急修复分支

### 2. 开发流程

#### 2.1 功能开发
```bash
# 1. 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/add-full-text-search

# 2. 开发功能
# ... 编写代码 ...

# 3. 运行测试
pytest tests/ -v

# 4. 代码检查
black pysqlit/ tests/
isort pysqlit/ tests/
mypy pysqlit/
flake8 pysqlit/ tests/

# 5. 提交代码
git add .
git commit -m "feat: add full-text search support"

# 6. 推送分支
git push origin feature/add-full-text-search

# 7. 创建Pull Request
```

#### 2.2 代码提交规范
使用 [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

**类型说明**:
- `feat`: 新功能
- `fix`: bug修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具

**示例**:
```bash
git commit -m "feat(parser): add support for UPDATE statements"
git commit -m "fix(storage): resolve page cache memory leak"
git commit -m "docs(api): update transaction documentation"
```

## 🧪 测试策略

### 1. 测试金字塔

```
         /\
        /  \    少量集成测试
       /----\
      /      \  中等数量服务测试
     /--------\
    /          \ 大量单元测试
   /____________\
```

### 2. 测试类型

#### 2.1 单元测试
```python
# tests/test_database.py
import pytest
from pysqlit.database import EnhancedDatabase

class TestDatabaseOperations:
    def setup_method(self):
        self.db = EnhancedDatabase(":memory:")
        self.db.execute("""
            CREATE TABLE test_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE
            )
        """)
    
    def teardown_method(self):
        self.db.close()
    
    def test_insert_and_retrieve(self):
        """测试插入和查询"""
        user_id = self.db.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("Alice", "alice@example.com"),
            return_id=True
        )
        
        user = self.db.execute(
            "SELECT * FROM test_users WHERE id = ?",
            (user_id,)
        )[0]
        
        assert user['name'] == "Alice"
        assert user['email'] == "alice@example.com"
    
    def test_unique_constraint(self):
        """测试唯一约束"""
        self.db.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("Bob", "bob@example.com")
        )
        
        with pytest.raises(Exception) as exc_info:
            self.db.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                ("Charlie", "bob@example.com")
            )
        
        assert "UNIQUE constraint failed" in str(exc_info.value)
```

#### 2.2 集成测试
```python
# tests/test_integration.py
import tempfile
import os
from pysqlit.database import EnhancedDatabase

class TestIntegration:
    def test_backup_restore(self):
        """测试备份恢复功能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试数据库
            db_path = os.path.join(tmpdir, "test.db")
            db = EnhancedDatabase(db_path)
            
            # 添加测试数据
            db.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            db.execute("INSERT INTO test VALUES (1, 'Alice')")
            
            # 创建备份
            backup_path = db.create_backup("test_backup")
            assert os.path.exists(backup_path)
            
            # 修改数据
            db.execute("INSERT INTO test VALUES (2, 'Bob')")
            
            # 恢复备份
            db.restore_backup("test_backup")
            
            # 验证数据
            rows = db.execute("SELECT * FROM test")
            assert len(rows) == 1
            assert rows[0]['name'] == "Alice"
            
            db.close()
```

#### 2.3 性能测试
```python
# tests/test_performance.py
import time
import pytest
from pysqlit.database import EnhancedDatabase

class TestPerformance:
    @pytest.mark.performance
    def test_bulk_insert_performance(self):
        """测试批量插入性能"""
        db = EnhancedDatabase(":memory:")
        db.execute("CREATE TABLE test (id INTEGER, name TEXT, age INTEGER)")
        
        # 准备测试数据
        data = [(i, f"User{i}", i % 100) for i in range(10000)]
        
        start_time = time.time()
        db.executemany(
            "INSERT INTO test VALUES (?, ?, ?)",
            data
        )
        elapsed = time.time() - start_time
        
        # 断言性能要求
        assert elapsed < 5.0  # 10,000条记录应在5秒内完成
        
        # 验证数据完整性
        count = db.execute("SELECT COUNT(*) FROM test")[0][0]
        assert count == 10000
        
        db.close()
```

### 3. 测试配置

#### 3.1 pytest配置 (pytest.ini)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=pysqlit
    --cov-report=html
    --cov-report=term-missing
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
```

#### 3.2 测试数据生成
```python
# tests/fixtures/data_generator.py
import random
from datetime import datetime, timedelta

class TestDataGenerator:
    @staticmethod
    def generate_users(count=100):
        """生成测试用户数据"""
        users = []
        for i in range(count):
            users.append({
                'username': f'user{i:03d}',
                'email': f'user{i:03d}@example.com',
                'age': random.randint(18, 80),
                'created_at': datetime.now() - timedelta(days=random.randint(0, 365))
            })
        return users
    
    @staticmethod
    def generate_orders(users, count=500):
        """生成测试订单数据"""
        orders = []
        for i in range(count):
            user = random.choice(users)
            orders.append({
                'user_id': user['id'],
                'total_amount': round(random.uniform(10, 1000), 2),
                'status': random.choice(['pending', 'paid', 'shipped', 'delivered']),
                'created_at': datetime.now() - timedelta(days=random.randint(0, 30))
            })
        return orders
```

## 🔧 代码规范

### 1. Python代码规范

#### 1.1 代码风格
遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 和 [PEP 257](https://www.python.org/dev/peps/pep-0257/):

```python
# ✅ 好的示例
class DatabaseManager:
    """数据库管理器，提供高级数据库操作接口。
    
    该类封装了底层存储和索引操作，提供简洁的SQL执行接口。
    
    Attributes:
        filename: 数据库文件名
        storage: 存储引擎实例
        index: 索引管理器实例
        
    Examples:
        >>> db = DatabaseManager("test.db")
        >>> db.execute("CREATE TABLE users (id INTEGER, name TEXT)")
        >>> db.execute("INSERT INTO users VALUES (1, 'Alice')")
        >>> results = db.execute("SELECT * FROM users")
    """
    
    def __init__(self, filename: str) -> None:
        """初始化数据库管理器。
        
        Args:
            filename: 数据库文件路径
            
        Raises:
            StorageError: 如果无法创建或打开数据库文件
        """
        self.filename: str = filename
        self._storage: Optional[StorageInterface] = None
        self._initialize_storage()

    def execute(self, sql: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        """执行SQL语句并返回结果。
        
        Args:
            sql: SQL语句
            params: 参数元组
            
        Returns:
            查询结果列表
            
        Raises:
            ParseError: SQL语法错误
            ExecutionError: 执行错误
        """
        # 实现代码...
```

#### 1.2 类型提示
```python
from typing import List, Dict, Optional, Any, Tuple, Union

class EnhancedDatabase:
    def __init__(
        self,
        filename: str,
        page_size: int = 4096,
        cache_size: int = 100,
        timeout: float = 5.0
    ) -> None:
        self.filename: str = filename
        self.page_size: int = page_size
        self._cache: Dict[int, bytearray] = {}
    
    def execute(
        self,
        sql: str,
        params: Union[Tuple[Any, ...], List[Any], Dict[str, Any]] = ()
    ) -> List[Dict[str, Any]]:
        """执行SQL语句。"""
        pass
    
    def create_backup(
        self,
        name: str,
        *,
        compress: bool = False,
        description: Optional[str] = None
    ) -> str:
        """创建数据库备份。"""
        pass
```

### 2. 命名规范

#### 2.1 命名约定
| 类型 | 命名风格 | 示例 |
|------|----------|------|
| 类名 | PascalCase | `DatabaseManager`, `BTreeIndex` |
| 函数/方法 | snake_case | `execute_sql()`, `create_backup()` |
| 变量 | snake_case | `user_name`, `total_count` |
| 常量 | UPPER_CASE | `MAX_PAGE_SIZE`, `DEFAULT_TIMEOUT` |
| 私有方法 | _snake_case | `_internal_method()`, `_validate_input()` |

#### 2.2 文件命名
- 模块文件: `snake_case.py`
- 测试文件: `test_*.py`
- 配置文件: `*.ini`, `*.toml`, `*.yaml`

### 3. 代码质量工具

#### 3.1 配置文件

**.pre-commit-config.yaml**:
```yaml
repos:
  - repo: https://gitee.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      
  - repo: https://gitee.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.9
        
  - repo: https://gitee.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
        
  - repo: https://gitee.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
        
  - repo: https://gitee.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

#### 3.2 代码检查命令
```bash
# 格式化代码
black pysqlit/ tests/
isort pysqlit/ tests/

# 类型检查
mypy pysqlit/

# 代码质量检查
flake8 pysqlit/ tests/
pylint pysqlit/

# 安全检查
bandit -r pysqlit/

# 复杂度检查
radon cc pysqlit/ -a -nb
```

## 🚀 构建和发布

### 1. 构建系统

#### 1.1 Makefile
```makefile
.PHONY: install dev test lint format clean build upload

# 安装
install:
	pip install -e .

# 开发环境
dev:
	pip install -e ".[dev]"
	pre-commit install

# 运行测试
test:
	pytest tests/ -v --cov=pysqlit --cov-report=html

# 代码检查
lint:
	flake8 pysqlit/ tests/
	mypy pysqlit/
	pylint pysqlit/

# 格式化
format:
	black pysqlit/ tests/
	isort pysqlit/ tests/

# 清理
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/ dist/ *.egg-info/

# 构建
build:
	python -m build

# 上传到测试PyPI
upload-test:
	python -m twine upload --repository testpypi dist/*

# 上传到PyPI
upload:
	python -m twine upload dist/*
```

#### 1.2 构建配置 (pyproject.toml)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "py-sqlit"
version = "1.0.0"
description = "Enterprise-grade SQLite database engine in Python"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
keywords = ["database", "sqlite", "sql", "storage"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Database",
    "Topic :: Database :: Database Engines/Servers",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.0.0",
    "flake8>=6.0.0",
    "pylint>=2.17.0",
    "pre-commit>=3.0.0",
    "tox>=4.0.0",
    "sphinx>=6.0.0",
    "sphinx-rtd-theme>=1.2.0",
]

[project.urls]
Homepage = "https://gitee.com/Python51888/PySqlit"
Documentation = "https://py-sqlit.readthedocs.io/"
Repository = "https://gitee.com/Python51888/PySqlit.git"
Issues = "https://gitee.com/Python51888/PySqlit/issues"

[tool.setuptools.packages.find]
where = ["."]
include = ["pysqlit*"]

[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "performance: marks tests as performance tests",
]

[tool.coverage.run]
source = ["pysqlit"]
omit = ["*/tests/*", "*/test_*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

### 2. 发布流程

#### 2.1 版本管理
使用 [语义化版本](https://semver.org/lang/zh-CN/):

- **主版本号(MAJOR)**: 不兼容的API修改
- **次版本号(MINOR)**: 向下兼容的功能性新增
- **修订号(PATCH)**: 向下兼容的问题修正

#### 2.2 发布步骤
```bash
# 1. 更新版本号
# 编辑 pyproject.toml 中的 version

# 2. 更新CHANGELOG.md
# 添加新版本说明

# 3. 运行完整测试
make test
make lint

# 4. 构建发布包
make build

# 5. 上传到测试PyPI
make upload-test

# 6. 测试安装
pip install --index-url https://test.pypi.org/simple/ py-sqlit

# 7. 上传到正式PyPI
make upload

# 8. 创建Git标签
git tag v1.0.0
git push origin v1.0.0
```

## 📊 性能优化

### 1. 性能基准测试

#### 1.1 基准测试框架
```python
# benchmarks/benchmark.py
import time
import statistics
from typing import List, Callable
from pysqlit.database import EnhancedDatabase

class BenchmarkSuite:
    """性能基准测试套件"""
    
    def __init__(self, iterations: int = 5):
        self.iterations = iterations
        self.results = {}
    
    def benchmark(
        self,
        name: str,
        setup: Callable,
        test: Callable,
        teardown: Callable = None
    ) -> float:
        """运行基准测试"""
        times = []
        
        for _ in range(self.iterations):
            if setup:
                setup()
            
            start = time.perf_counter()
            test()
            elapsed = time.perf_counter() - start
            
            times.append(elapsed)
            
            if teardown:
                teardown()
        
        avg_time = statistics.mean(times)
        self.results[name] = {
            'mean': avg_time,
            'median': statistics.median(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'min': min(times),
            'max': max(times)
        }
        
        return avg_time
    
    def run_all(self):
        """运行所有基准测试"""
        # 插入性能测试
        self.benchmark_insert_performance()
        self.benchmark_query_performance()
        self.benchmark_transaction_performance()
        
        return self.results
    
    def benchmark_insert_performance(self):
        """测试插入性能"""
        def setup():
            self.db = EnhancedDatabase(":memory:")
            self.db.execute("CREATE TABLE test (id INTEGER, name TEXT, age INTEGER)")
        
        def test():
            data = [(i, f"User{i}", i % 100) for i in range(1000)]
            self.db.executemany("INSERT INTO test VALUES (?, ?, ?)", data)
        
        def teardown():
            self.db.close()
        
        self.benchmark("insert_1000_rows", setup, test, teardown)
```

#### 1.2 性能测试命令
```bash
# 运行性能测试
python benchmarks/benchmark.py

# 使用pytest-benchmark
pytest tests/test_performance.py --benchmark-only

# 生成性能报告
pytest tests/test_performance.py --benchmark-json=benchmark.json
```

### 2. 性能分析工具

#### 2.1 cProfile使用
```bash
# 性能分析
python -m cProfile -o profile.stats -m pysqlit.repl test.db

# 查看分析结果
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

#### 2.2 line_profiler使用
```python
# 在代码中添加装饰器
from line_profiler import LineProfiler

@profile
def complex_query(db):
    return db.execute("""
        SELECT u.username, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id
    """)

# 运行分析
kernprof -l -v script.py
```

## 🔍 调试技巧

### 1. 日志调试

#### 1.1 配置日志
```python
import logging
from pysqlit.debug import setup_debug_logging

# 设置调试日志
setup_debug_logging(level=logging.DEBUG)

# 使用日志
logger = logging.getLogger(__name__)

class DatabaseManager:
    def execute(self, sql: str, params: tuple = ()):
        logger.debug(f"Executing SQL: {sql} with params: {params}")
        # ... 执行逻辑 ...
```

#### 1.2 调试模式
```python
from pysqlit.debug import DebugDatabase

# 启用调试模式
db = DebugDatabase("test.db", debug=True)

# 查看执行计划
plan = db.explain("SELECT * FROM users WHERE age > 25")
print(plan)

# 查看锁信息
locks = db.get_lock_info()
print(locks)

# 查看缓存状态
cache_stats = db.get_cache_stats()
print(cache_stats)
```

### 2. 调试工具

#### 2.1 PDB调试
```python
import pdb

class BTreeIndex:
    def insert(self, key: int, value: bytes):
        # 设置断点
        if key == 42:  # 特定条件断点
            pdb.set_trace()
        
        # 正常插入逻辑
        # ...
```

#### 2.2 内存调试
```python
import tracemalloc

# 开始内存跟踪
tracemalloc.start()

# 执行操作
db = EnhancedDatabase("test.db")
# ... 大量操作 ...

# 获取内存快照
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("[ Top 10 memory consumers ]")
for stat in top_stats[:10]:
    print(stat)
```

## 🤝 贡献指南

### 1. 如何贡献

#### 1.1 报告问题
1. 搜索现有问题
2. 创建详细的问题报告
3. 提供最小复现示例
4. 包含环境信息

#### 1.2 提交代码
1. Fork 项目
2. 创建功能分支
3. 编写测试
4. 确保所有测试通过
5. 提交Pull Request

#### 1.3 代码审查清单
- [ ] 代码符合PEP 8规范
- [ ] 包含完整的类型提示
- [ ] 有清晰的文档字符串
- [ ] 包含单元测试
- [ ] 测试覆盖率>90%
- [ ] 性能没有退化
- [ ] 向后兼容
- [ ] 更新相关文档

### 2. 开发资源

#### 2.1 学习资源
- [SQLite官方文档](https://sqlite.org/docs.html)
- [数据库系统概念](https://www.db-book.com/)
- [Python数据库编程](https://docs.python.org/3/library/sqlite3.html)
- [B树算法](https://en.wikipedia.org/wiki/B-tree)

#### 2.2 开发工具
- **调试**: Python Debugger (pdb)
- **性能**: cProfile, line_profiler
- **内存**: tracemalloc, memory_profiler
- **测试**: pytest, hypothesis
- **文档**: Sphinx, MkDocs

#### 2.3 社区支持
- **GitHub Issues**: 技术讨论
- **Discussions**: 功能建议
- **Wiki**: 开发文档
- **Discord**: 实时交流

---

**准备好开始贡献了吗？** 查看 [GitHub Issues](https://gitee.com/Python51888/PySqlit/issues) 找到适合你的任务！