# SafeFlow 文档中心

## 📚 文档索引

### 核心文档

| 文档 | 描述 | 适用人群 |
|------|------|----------|
| [PRD.md](PRD.md) | 产品需求文档，详细的技术方案和架构设计 | 产品经理、架构师 |
| [DEV_PLAN.md](DEV_PLAN.md) | 开发计划，分阶段实施路线图 | 开发团队 |
| [mcp_protocol_spec.md](mcp_protocol_spec.md) | MCP 协议规范，数据格式和接口定义 | 开发者 |

### 使用指南

| 文档 | 描述 | 适用场景 |
|------|------|----------|
| [INSTALLATION.md](INSTALLATION.md) | 安装指南，环境配置和依赖管理 | 新用户、运维 |
| [MCP_COMPLETE_GUIDE.md](MCP_COMPLETE_GUIDE.md) | MCP 完整指南，从入门到高级使用 | 所有用户 |

---

## 🎯 快速导航

### 我是新用户

1. **了解项目** → [PRD.md](PRD.md) - 了解 SafeFlow 是什么
2. **安装环境** → [INSTALLATION.md](INSTALLATION.md) - 配置开发环境
3. **开始使用** → [MCP_COMPLETE_GUIDE.md](MCP_COMPLETE_GUIDE.md) - 快速开始

### 我是开发者

1. **技术架构** → [PRD.md](PRD.md) - 了解技术方案
2. **开发计划** → [DEV_PLAN.md](DEV_PLAN.md) - 了解开发路线
3. **协议规范** → [mcp_protocol_spec.md](mcp_protocol_spec.md) - 了解 MCP 协议
4. **MCP 使用** → [MCP_COMPLETE_GUIDE.md](MCP_COMPLETE_GUIDE.md) - 开发指南

### 我要集成 MCP

1. **协议规范** → [mcp_protocol_spec.md](mcp_protocol_spec.md) - 了解数据格式
2. **完整指南** → [MCP_COMPLETE_GUIDE.md](MCP_COMPLETE_GUIDE.md) - 集成方法
3. **故障排查** → [MCP_COMPLETE_GUIDE.md](MCP_COMPLETE_GUIDE.md#故障排查) - 解决问题

### 我要部署生产

1. **安装指南** → [INSTALLATION.md](INSTALLATION.md) - 环境配置
2. **安全考虑** → [MCP_COMPLETE_GUIDE.md](MCP_COMPLETE_GUIDE.md#安全考虑) - 生产部署
3. **性能指标** → [MCP_COMPLETE_GUIDE.md](MCP_COMPLETE_GUIDE.md#性能指标) - 性能参考

---

## 📖 文档结构

```
docs/
├── README.md              # 本文档（文档索引）
├── PRD.md                 # 产品需求文档（67KB，227行）
├── DEV_PLAN.md            # 开发计划（4.8KB，56行）
├── mcp_protocol_spec.md   # MCP 协议规范（11KB，383行）
├── INSTALLATION.md        # 安装指南（6.2KB，349行）
└── MCP_COMPLETE_GUIDE.md  # MCP 完整指南（合并精简版）
```

---

## 🔄 文档更新

### 最近更新

- **2025-01-15**: 合并精简 MCP 相关文档，删除重复内容
- **2025-01-15**: 创建统一的 MCP 完整指南
- **2025-01-15**: 更新文档索引和导航

### 维护原则

1. **避免重复**：相同内容只在一个地方维护
2. **结构清晰**：按用户角色和使用场景组织
3. **及时更新**：代码变更时同步更新文档
4. **易于查找**：提供清晰的导航和索引

---

## 💡 使用建议

### 阅读顺序

1. **首次接触**：PRD.md → INSTALLATION.md → MCP_COMPLETE_GUIDE.md
2. **开发集成**：mcp_protocol_spec.md → MCP_COMPLETE_GUIDE.md
3. **问题排查**：MCP_COMPLETE_GUIDE.md → INSTALLATION.md

### 文档特点

- **PRD.md**: 详细但较长，适合深入了解
- **DEV_PLAN.md**: 简洁明了，适合快速了解
- **mcp_protocol_spec.md**: 技术规范，适合开发者
- **INSTALLATION.md**: 实用指南，适合运维
- **MCP_COMPLETE_GUIDE.md**: 综合指南，适合所有用户

---

## 📞 获取帮助

如果文档中没有找到你需要的信息：

1. 查看 [GitHub Issues](https://github.com/your-org/SafeFlow/issues)
2. 加入社区讨论
3. 提交文档改进建议

---

**文档版本**: v1.0  
**最后更新**: 2025-01-15  
**维护者**: SafeFlow 开发团队
