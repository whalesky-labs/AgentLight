# AgentLight 代码规范

## 总原则

AgentLight 按清晰分层项目维护。任何代码变更都应保持边界清楚、可测试、可扩展、可追踪。

## 文件头规范

所有源代码文件必须包含项目文件头。内容固定如下，注释语法按语言选择：

```text
This file is part of AgentLight.

@link     https://github.com/whalesky-labs/AgentLight
@document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
@contact  root@imoi.cn
@license  https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE
```

适用范围：

- C/C++: `.cpp`, `.h`
- Python: `.py` 和无扩展 Python 入口脚本
- Shell: `.sh` 和无扩展 Bash 入口脚本
- PowerShell: `.ps1`

不适用范围：

- Markdown 文档
- JSON/YAML/INI 配置
- CI 配置文件
- 生成物

## 开源协议规范

- 项目使用 MIT License 开源，SPDX 标识为 `MIT`。
- 正式协议原文维护在根目录 [LICENSE](../LICENSE)。
- 源码文件头中的 `@license` 必须指向 `https://github.com/whalesky-labs/AgentLight/blob/main/LICENSE`。

## 架构边界

### 固件端

```text
src/domain              命令、灯光状态、灯效等纯领域模型
src/application         状态灯用例和业务语义
src/infrastructure      GPIO、USB、BLE、Wi-Fi 等外部适配
src/main.cpp            对象装配和主循环调度
```

约束：

- `domain` 不访问 Arduino 硬件 IO、网络、串口、BLE。
- `application` 不直接操作 GPIO、Wi-Fi、BLE、USB。
- `infrastructure` 负责外部系统接入，但不承载业务策略。
- `main.cpp` 只做装配，不写业务规则。

### 桌面 Agent

```text
agentlight_agent/domain          监听器、规则、运行模式、配置模型
agentlight_agent/application     平台选择、监听编排、服务运行用例
agentlight_agent/infrastructure  JSON、路径、文件监听、子进程、事件发送
agentlight_agent/interfaces      CLI 参数和输出
scripts/                         向后兼容入口
```

约束：

- `scripts/agentlight-agent` 和 `scripts/multi-agent-monitor` 必须保持薄入口。
- 平台切换策略固定从 `activePlatform` 读取。
- 多会话策略固定为 `latest-event-wins`，不得引入聚合或轮播逻辑。
- 新增平台时优先更新 `config/agent-platforms.json`、兼容性文档和验证脚本。

## 命名规范

- 项目名统一使用 `AgentLight`。
- 服务、日志目录、配置目录统一使用 `whalesky-labs-AgentLight` 前缀。
- Python 类型使用 `PascalCase`，函数和变量使用 `snake_case`。
- C++ 类型使用 `PascalCase`，函数使用 `camelCase`，私有字段使用尾部 `_`。
- Shell 变量使用小写加下划线，环境变量使用大写加下划线。

## 配置规范

- JSON 配置必须通过显式类型校验后才能进入应用层。
- 布尔值必须是真正的 JSON boolean，不允许 `"true"` 或 `"false"` 字符串。
- 路径必须在基础设施层解析，不允许应用层拼接运行时路径。
- 示例配置必须能被 `scripts/verify-agent-bridge` 验证。

## 测试规范

必须覆盖：

- 配置解析和类型校验
- 平台选择
- 多会话策略入口
- 监听规则匹配
- CLI 入口兼容
- CI 发布脚本关键路径

优先使用标准库测试工具，避免为简单项目引入不必要依赖。

## 验证命令

常规变更至少运行：

```bash
python3 -m py_compile $(find agentlight_agent tests -name '*.py' -print) scripts/agentlight-agent scripts/multi-agent-monitor scripts/codex-session-monitor scripts/ci/resolve-firmware-version scripts/ci/prepare-firmware-release scripts/ci/package-firmware
python3 -m unittest discover -s tests -p 'test_*.py'
scripts/verify-agent-bridge
scripts/ci/verify-firmware-ci
git diff --check
```

固件或 CI 相关变更还需要运行：

```bash
pio run -e esp32-c3-supermini
```

## Markdown 文档规范

- 除 [README.en.md](../README.en.md) 外，所有 Markdown 文档正文必须使用中文。
- 技术专有名词、命令、文件名、路径、协议名和配置键可以保留英文原文。
- CI 生成的 `release-body.md` 也必须是中文发布说明。
