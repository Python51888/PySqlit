# PySQLit 文档导航

## 📋 文档总览

欢迎来到 PySQLit 完整文档体系！我们为您提供了从入门到精通的全面指南。

## 🗺️ 文档地图

### 🚀 [快速开始](index.md#快速开始)
- 5分钟上手教程
- 环境配置指南
- 第一个数据库应用

### 📖 [用户指南](usage-guide.md)
- **基础使用**: 连接管理、表操作、数据CRUD
- **事务管理**: ACID特性、隔离级别、最佳实践
- **备份恢复**: 自动备份、增量备份、灾难恢复
- **性能优化**: 索引优化、查询调优、批量操作

### 🏗️ [架构设计](architecture.md)
- **系统架构**: 分层设计、模块职责、扩展点
- **设计模式**: 工厂模式、策略模式、观察者模式
- **存储引擎**: 页管理、缓存策略、并发控制
- **性能架构**: 缓存设计、连接池、监控体系

### 🔧 [API参考](api-reference.md)
- **核心类**: EnhancedDatabase、EnhancedTable、TransactionManager
- **数据模型**: Row、TableSchema、WhereCondition
- **异常处理**: 完整异常层次、错误处理最佳实践
- **配置选项**: DatabaseConfig、所有配置参数

### ⚙️ [开发指南](development.md)
- **环境搭建**: 开发环境、工具链、VS Code配置
- **代码规范**: PEP 8、类型提示、提交规范
- **测试策略**: 单元测试、集成测试、性能测试
- **构建发布**: Makefile、CI/CD、版本管理

### ⚠️ [限制说明](limitations.md)
- **当前限制**: 并发控制、事务实现、查询优化
- **技术债务**: 代码质量、测试覆盖、文档完善
- **改进路线**: 短期、中期、长期规划
- **迁移建议**: 何时考虑其他数据库

### 🚀 [高级主题](advanced-topics.md)
- **性能调优**: 内存优化、并发优化、查询优化
- **扩展开发**: 自定义存储引擎、索引类型、插件系统
- **生产部署**: Docker、Kubernetes、监控告警
- **故障排除**: 常见问题、调试工具、诊断方法

## 📊 学习路径

### 👶 初学者路径 (1-2小时)
1. [快速开始](index.md#快速开始) - 5分钟上手
2. [基础使用](usage-guide.md#基础使用) - 核心操作
3. [简单示例](usage-guide.md#第一个数据库应用) - 实践练习

### 👨‍💻 开发者路径 (1-2天)
1. [用户指南](usage-guide.md) - 完整功能
2. [API参考](api-reference.md) - 接口文档
3. [开发指南](development.md) - 贡献代码

### 🏗️ 架构师路径 (1-2周)
1. [架构设计](architecture.md) - 系统设计
2. [高级主题](advanced-topics.md) - 深度优化
3. [生产部署](advanced-topics.md#生产部署指南) - 运维实践

## 🔗 快速导航

| 需求场景 | 推荐文档 |
|----------|----------|
| **快速试用** | [快速开始](index.md#快速开始) |
| **API文档** | [API参考](api-reference.md) |
| **性能问题** | [高级主题-性能调优](advanced-topics.md#性能调优深度指南) |
| **部署生产** | [高级主题-生产部署](advanced-topics.md#生产部署指南) |
| **贡献代码** | [开发指南](development.md) |
| **遇到问题** | [限制说明](limitations.md) + [高级主题-故障排除](advanced-topics.md#故障排除) |

## 📚 示例代码索引

### 基础示例
- [创建数据库](usage-guide.md#第一个数据库应用)
- [事务操作](usage-guide.md#事务管理)
- [备份恢复](usage-guide.md#备份恢复)

### 高级示例
- [实时数据管道](advanced-topics.md#实时数据管道)
- [分布式缓存层](advanced-topics.md#分布式缓存层)
- [自定义存储引擎](advanced-topics.md#自定义存储引擎)

### 生产示例
- [Docker部署](advanced-topics.md#容器化部署)
- [Kubernetes部署](advanced-topics.md#kubernetes部署)
- [监控配置](advanced-topics.md#监控和告警)

## 🆘 获取帮助

### 遇到问题？
1. 查看[限制说明](limitations.md)了解已知问题
2. 使用[故障排除指南](advanced-topics.md#故障排除)
3. 搜索[GitHub Issues](https://gitee.com/Python51888/PySqlit/issues)
4. 创建新问题报告

### 需要支持？
- 📧 **邮件支持**: support@py-sqlit.org
- 💬 **社区讨论**: [GitHub Discussions](https://gitee.com/Python51888/PySqlit/discussions)
- 🐦 **实时聊天**: [Discord](https://discord.gg/py-sqlit)

## 🔄 文档更新

本文档与代码同步更新，最新版本请查看：
- [GitHub仓库](https://gitee.com/Python51888/PySqlit)
- [在线文档](https://py-sqlit.readthedocs.io/)

---

**开始您的PySQLit之旅吧！** 从[快速开始](index.md#快速开始)开始，或根据您的需求选择相应的文档。