# Global Codex Instructions

## Active Skills

Use skill: karpathy-guidelines

---

## System Environment
OS: Windows 11
Shell: Use PowerShell commands first
Encoding: UTF-8
Path style: Windows format (e.g. .\path\to\file)
---

## Language
默认使用中文回答说明
代码、变量名、方法名保持英文
---

## Working Style
先理解需求，再修改代码
Always plan before implementing
仅做必要修改（minimal diff）
禁止无关重构
优先局部修改而不是整体重写
优先提供可运行方案
---

## Coding Rules
避免新增重量级依赖
新增依赖必须说明原因
不要猜测 API
不要假设不存在的框架能力
---

## Verification
不要假装执行过命令
不要假装测试已经通过
修改前确认文件存在
修改后优先检查编译错误
---

## Safety
不要删除用户代码（除非明确要求）
不要修改数据库结构
不要修改 migration 文件
不要修改生产环境配置
不要输出密钥或凭据
---

## Change Policy
涉及以下操作必须先给计划：
数据库结构修改
跨模块修改
依赖升级
架构调整
