# PySQLit 高级主题指南

## 🎯 概述

本文档涵盖 PySQLit 的高级使用场景、性能调优、扩展开发和生产部署等主题，适合有经验的开发者和架构师。

## 📊 性能调优深度指南

### 1. 内存优化策略

#### 1.1 内存使用分析
```python
import tracemalloc
from pysqlit.database import EnhancedDatabase

# 启动内存跟踪
tracemalloc.start()

# 创建数据库并执行操作
db = EnhancedDatabase("large_dataset.db")

# 分析内存使用
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("内存使用TOP 10:")
for stat in top_stats[:10]:
    print(stat)
```

#### 1.2 缓存调优
```python
from pysqlit.config import DatabaseConfig

# 根据数据量调整缓存
config = DatabaseConfig(
    cache_size=1000,  # 大数据集使用更大缓存
    page_size=8192,   # 大页减少I/O次数
    max_memory_usage="512MB"  # 限制内存使用
)

db = EnhancedDatabase("bigdata.db", config=config)
```

#### 1.3 批量操作优化
```python
# 最优批量大小测试
def find_optimal_batch_size(db, data_size=10000):
    batch_sizes = [100, 500, 1000, 2000, 5000]
    results = {}
    
    for batch_size in batch_sizes:
        start = time.time()
        
        for i in range(0, data_size, batch_size):
            batch = data[i:i+batch_size]
            db.executemany(
                "INSERT INTO test VALUES (?, ?, ?)",
                batch
            )
        
        elapsed = time.time() - start
        results[batch_size] = elapsed
    
    return min(results, key=results.get)
```

### 2. 并发性能优化

#### 2.1 连接池高级配置
```python
from pysqlit.pool import ConnectionPool, PoolConfig

# 高级连接池配置
config = PoolConfig(
    max_connections=50,
    min_connections=5,
    connection_timeout=30,
    idle_timeout=300,
    max_lifetime=3600,
    health_check_interval=60
)

pool = ConnectionPool(
    database_path="production.db",
    config=config
)

# 监控连接池状态
def monitor_pool(pool):
    stats = pool.get_stats()
    print(f"""
    活跃连接: {stats['active_connections']}
    空闲连接: {stats['idle_connections']}
    等待连接: {stats['waiting_connections']}
    总连接数: {stats['total_connections']}
    """)
```

#### 2.2 读写分离策略
```python
class ReadWriteRouter:
    """读写分离路由器"""
    
    def __init__(self, master_db, replica_dbs):
        self.master = master_db
        self.replicas = replica_dbs
        self.current_replica = 0
    
    def get_read_db(self):
        """获取读数据库"""
        replica = self.replicas[self.current_replica]
        self.current_replica = (self.current_replica + 1) % len(self.replicas)
        return replica
    
    def get_write_db(self):
        """获取写数据库"""
        return self.master
    
    def execute_read(self, sql, params=()):
        return self.get_read_db().execute(sql, params)
    
    def execute_write(self, sql, params=()):
        return self.master.execute(sql, params)
```

### 3. 查询优化高级技巧

#### 3.1 索引策略设计
```python
class IndexOptimizer:
    """索引优化器"""
    
    def analyze_query_patterns(self, queries):
        """分析查询模式"""
        patterns = {}
        for query in queries:
            # 提取WHERE条件
            where_conditions = self.extract_where_conditions(query)
            # 提取JOIN条件
            join_conditions = self.extract_join_conditions(query)
            # 提取ORDER BY
            order_columns = self.extract_order_columns(query)
            
            patterns[query] = {
                'where': where_conditions,
                'join': join_conditions,
                'order': order_columns
            }
        return patterns
    
    def recommend_indexes(self, patterns):
        """推荐索引"""
        recommendations = []
        
        for query, pattern in patterns.items():
            # 基于查询频率和选择性推荐索引
            if pattern['where']:
                for col, op in pattern['where']:
                    if self.is_selective(col):
                        recommendations.append({
                            'table': self.get_table_from_query(query),
                            'columns': [col],
                            'type': 'btree',
                            'reason': f'WHERE {col} {op}'
                        })
        
        return recommendations
```

#### 3.2 查询重写优化
```python
class QueryRewriter:
    """查询重写器"""
    
    def rewrite_subquery_to_join(self, query):
        """将子查询重写为JOIN"""
        # 示例：将IN子查询重写为JOIN
        # 原查询: SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)
        # 重写后: SELECT DISTINCT u.* FROM users u JOIN orders o ON u.id = o.user_id
        pass
    
    def optimize_pagination(self, query, offset, limit):
        """优化分页查询"""
        # 使用键集分页替代OFFSET
        if offset > 1000:
            return self.keyset_pagination(query, offset, limit)
        return query
```

## 🏗️ 扩展开发指南

### 1. 自定义存储引擎

#### 1.1 存储引擎接口
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class StorageEngine(ABC):
    """存储引擎接口"""
    
    @abstractmethod
    def open(self, path: str, **kwargs) -> None:
        """打开存储"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭存储"""
        pass
    
    @abstractmethod
    def read_page(self, page_num: int) -> bytes:
        """读取页"""
        pass
    
    @abstractmethod
    def write_page(self, page_num: int, data: bytes) -> None:
        """写入页"""
        pass
    
    @abstractmethod
    def get_page_count(self) -> int:
        """获取页数"""
        pass

class RedisStorageEngine(StorageEngine):
    """Redis存储引擎实现"""
    
    def __init__(self, redis_url: str):
        import redis
        self.redis = redis.from_url(redis_url)
    
    def read_page(self, page_num: int) -> bytes:
        key = f"db:page:{page_num}"
        data = self.redis.get(key)
        return data or b''
    
    def write_page(self, page_num: int, data: bytes) -> None:
        key = f"db:page:{page_num}"
        self.redis.set(key, data)
```

#### 1.2 注册自定义引擎
```python
from pysqlit.storage import register_storage_engine

# 注册Redis存储引擎
register_storage_engine('redis', RedisStorageEngine)

# 使用自定义引擎
db = EnhancedDatabase("redis://localhost:6379/0", engine='redis')
```

### 2. 自定义索引类型

#### 2.1 索引接口设计
```python
from pysqlit.index import IndexInterface

class HashIndex(IndexInterface):
    """哈希索引实现"""
    
    def __init__(self, storage):
        self.storage = storage
        self.hash_table = {}
    
    def insert(self, key: Any, value: int) -> None:
        """插入键值对"""
        if key not in self.hash_table:
            self.hash_table[key] = []
        self.hash_table[key].append(value)
    
    def search(self, key: Any) -> Optional[List[int]]:
        """精确查找"""
        return self.hash_table.get(key)
    
    def range_search(self, start: Any, end: Any) -> List[int]:
        """范围查找（哈希索引不支持）"""
        raise NotImplementedError("Hash index does not support range queries")

class FullTextIndex(IndexInterface):
    """全文索引实现"""
    
    def __init__(self, storage):
        self.storage = storage
        self.inverted_index = {}
    
    def insert(self, document: str, doc_id: int) -> None:
        """插入文档"""
        words = self.tokenize(document)
        for word in words:
            if word not in self.inverted_index:
                self.inverted_index[word] = set()
            self.inverted_index[word].add(doc_id)
    
    def search(self, query: str) -> List[int]:
        """全文搜索"""
        terms = self.tokenize(query)
        results = set()
        for term in terms:
            if term in self.inverted_index:
                if not results:
                    results = self.inverted_index[term]
                else:
                    results &= self.inverted_index[term]
        return list(results)
```

### 3. 插件系统开发

#### 3.1 插件架构设计
```python
from typing import Protocol
from dataclasses import dataclass

@dataclass
class PluginContext:
    """插件上下文"""
    database: EnhancedDatabase
    config: Dict[str, Any]
    logger: Any

class Plugin(Protocol):
    """插件协议"""
    
    def initialize(self, context: PluginContext) -> None:
        """初始化插件"""
        ...
    
    def before_query(self, sql: str, params: tuple) -> None:
        """查询前钩子"""
        ...
    
    def after_query(self, sql: str, params: tuple, result: Any, duration: float) -> None:
        """查询后钩子"""
        ...
    
    def shutdown(self) -> None:
        """关闭插件"""
        ...

class MetricsPlugin:
    """指标收集插件"""
    
    def __init__(self):
        self.query_count = 0
        self.total_duration = 0.0
    
    def initialize(self, context: PluginContext):
        self.logger = context.logger
    
    def before_query(self, sql: str, params: tuple):
        self.start_time = time.time()
    
    def after_query(self, sql: str, params: tuple, result: Any, duration: float):
        self.query_count += 1
        self.total_duration += duration
        
        if duration > 1.0:  # 慢查询
            self.logger.warning(f"Slow query: {duration:.3f}s - {sql}")
```

#### 3.2 插件注册和使用
```python
from pysqlit.plugin import PluginManager

# 创建插件管理器
plugin_manager = PluginManager()

# 注册插件
plugin_manager.register_plugin('metrics', MetricsPlugin())
plugin_manager.register_plugin('cache', CachePlugin())

# 使用插件
db = EnhancedDatabase("app.db", plugins=['metrics', 'cache'])
```

## 🚀 生产部署指南

### 1. 容器化部署

#### 1.1 Docker配置
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/backups

# 设置权限
RUN chmod 755 /app/data /app/backups

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from pysqlit.database import EnhancedDatabase; db = EnhancedDatabase('/app/data/health.db'); db.execute('SELECT 1'); db.close()"

# 运行应用
CMD ["python", "-m", "pysqlit.server", "--host", "0.0.0.0", "--port", "8080"]
```

#### 1.2 Docker Compose配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  py-sqlit:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
    environment:
      - DATABASE_PATH=/app/data/app.db
      - BACKUP_PATH=/app/backups
      - LOG_LEVEL=INFO
    restart: unless-stopped
    
  backup:
    image: py-sqlit:latest
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
    command: ["python", "-m", "pysqlit.backup", "--schedule", "daily"]
    depends_on:
      - py-sqlit
```

### 2. Kubernetes部署

#### 2.1 StatefulSet配置
```yaml
# k8s/statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: py-sqlit
spec:
  serviceName: py-sqlit
  replicas: 1
  selector:
    matchLabels:
      app: py-sqlit
  template:
    metadata:
      labels:
        app: py-sqlit
    spec:
      containers:
      - name: py-sqlit
        image: py-sqlit:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_PATH
          value: "/data/app.db"
        volumeMounts:
        - name: data
          mountPath: /data
        - name: backups
          mountPath: /backups
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
  - metadata:
      name: backups
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 5Gi
```

#### 2.2 配置映射
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: py-sqlit-config
data:
  config.yaml: |
    database:
      page_size: 4096
      cache_size: 1000
      max_connections: 50
    
    performance:
      query_timeout: 30
      slow_query_threshold: 1.0
    
    backup:
      enabled: true
      schedule: "0 2 * * *"
      retention_days: 30
```

### 3. 监控和告警

#### 3.1 Prometheus指标
```python
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
query_counter = Counter('pysqlit_queries_total', 'Total queries', ['operation'])
query_duration = Histogram('pysqlit_query_duration_seconds', 'Query duration')
active_connections = Gauge('pysqlit_active_connections', 'Active connections')
database_size = Gauge('pysqlit_database_size_bytes', 'Database size')

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, db):
        self.db = db
    
    def collect_metrics(self):
        """收集指标"""
        # 查询计数
        query_counter.labels(operation='select').inc()
        
        # 数据库大小
        size = self.db.get_database_size()
        database_size.set(size)
        
        # 活跃连接
        connections = self.db.get_active_connections()
        active_connections.set(connections)
```

#### 3.2 Grafana仪表板
```json
{
  "dashboard": {
    "title": "PySQLit Monitoring",
    "panels": [
      {
        "title": "Query Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(pysqlit_queries_total[5m])",
            "legendFormat": "{{operation}}"
          }
        ]
      },
      {
        "title": "Database Size",
        "type": "stat",
        "targets": [
          {
            "expr": "pysqlit_database_size_bytes",
            "legendFormat": "Size"
          }
        ]
      }
    ]
  }
}
```

## 🔍 故障排除

### 1. 常见问题诊断

#### 1.1 性能问题
```python
# 性能诊断工具
class PerformanceDiagnostics:
    def analyze_slow_queries(self, threshold=1.0):
        """分析慢查询"""
        slow_queries = []
        
        # 获取查询日志
        logs = self.db.get_query_logs()
        
        for log in logs:
            if log.duration > threshold:
                slow_queries.append({
                    'sql': log.sql,
                    'duration': log.duration,
                    'params': log.params,
                    'plan': self.explain_query(log.sql, log.params)
                })
        
        return slow_queries
    
    def check_index_usage(self, table):
        """检查索引使用情况"""
        stats = self.db.execute("""
            SELECT name, stat FROM sqlite_stat1 
            WHERE tbl = ?
        """, (table,))
        
        recommendations = []
        for name, stat in stats:
            if self.is_index_underused(name, stat):
                recommendations.append({
                    'index': name,
                    'reason': 'Underused index',
                    'action': 'Consider dropping'
                })
        
        return recommendations
```

#### 1.2 内存问题
```python
# 内存泄漏检测
import gc
import psutil

def check_memory_leaks():
    """检查内存泄漏"""
    process = psutil.Process()
    
    # 获取初始内存使用
    initial_memory = process.memory_info().rss
    
    # 执行大量操作
    db = EnhancedDatabase("test.db")
    for i in range(10000):
        db.execute("INSERT INTO test VALUES (?, ?)", (i, f"data{i}"))
    
    # 关闭数据库
    db.close()
    
    # 强制垃圾回收
    gc.collect()
    
    # 检查内存是否释放
    final_memory = process.memory_info().rss
    
    if final_memory > initial_memory * 1.1:
        print("Potential memory leak detected")
        return False
    
    return True
```

### 2. 调试工具

#### 2.1 调试模式
```python
# 启用调试模式
import logging
from pysqlit.debug import DebugDatabase

# 配置调试日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 创建调试数据库
db = DebugDatabase("app.db", debug=True)

# 启用查询日志
db.enable_query_logging()

# 设置断点
db.set_breakpoint("SELECT * FROM users WHERE id = 42")

# 执行查询
result = db.execute("SELECT * FROM users")
```

#### 2.2 性能分析
```python
# 使用cProfile进行性能分析
import cProfile
import pstats

def profile_database_operations():
    """分析数据库操作性能"""
    profiler = cProfile.Profile()
    
    profiler.enable()
    
    # 执行数据库操作
    db = EnhancedDatabase("profile.db")
    db.execute("CREATE TABLE test (id INTEGER, data TEXT)")
    
    for i in range(1000):
        db.execute("INSERT INTO test VALUES (?, ?)", (i, f"data{i}"))
    
    results = db.execute("SELECT * FROM test WHERE id > 500")
    
    profiler.disable()
    
    # 输出分析结果
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

## 📚 高级示例

### 1. 实时数据管道
```python
import asyncio
import aiohttp
from pysqlit.async_support import AsyncDatabase

class RealtimeDataPipeline:
    """实时数据管道"""
    
    def __init__(self, db_path: str):
        self.db = AsyncDatabase(db_path)
        self.buffer = asyncio.Queue(maxsize=1000)
    
    async def ingest_data(self, source_url: str):
        """数据摄取"""
        async with aiohttp.ClientSession() as session:
            async with session.get(source_url) as response:
                async for line in response.content:
                    await self.buffer.put(line)
    
    async def process_data(self):
        """数据处理"""
        while True:
            batch = []
            for _ in range(100):  # 批处理100条
                try:
                    item = await asyncio.wait_for(
                        self.buffer.get(), 
                        timeout=1.0
                    )
                    batch.append(item)
                except asyncio.TimeoutError:
                    break
            
            if batch:
                await self.db.executemany(
                    "INSERT INTO events (data, timestamp) VALUES (?, ?)",
                    [(item, datetime.now()) for item in batch]
                )
```

### 2. 分布式缓存层
```python
import redis
from functools import lru_cache

class CachedDatabase:
    """带缓存的数据库"""
    
    def __init__(self, db_path: str, redis_url: str):
        self.db = EnhancedDatabase(db_path)
        self.cache = redis.from_url(redis_url)
        self.cache_ttl = 300  # 5分钟
    
    @lru_cache(maxsize=1000)
    def get_user(self, user_id: int):
        """获取用户信息（带缓存）"""
        cache_key = f"user:{user_id}"
        
        # 尝试从缓存获取
        cached = self.cache.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 从数据库获取
        user = self.db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )[0]
        
        # 写入缓存
        self.cache.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps(user)
        )
        
        return user
```

---

**下一步**: 查看[故障排除指南](troubleshooting.md)或[贡献指南](development.md)获取更多信息！