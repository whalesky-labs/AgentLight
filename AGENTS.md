# AgentLight 工程规则

本文件是 AgentLight 仓库级工程规则，适用于本仓库后续所有代码变更。

## 项目标识

- 项目名称：`AgentLight`
- 组织名称：`whalesky-labs`
- 硬件目标：ESP32-C3 SuperMini
- 对外服务名前缀：`whalesky-labs-AgentLight`

## 文件头规范

所有源代码文件必须在文件顶部附近包含 AgentLight 项目文件头。

文件头内容固定如下，注释语法按语言选择：

```text
This file is part of AgentLight.

@link     https://github.com/whalesky-labs/AgentLight
@document https://github.com/whalesky-labs/AgentLight/blob/main/README.md
@contact  root@imoi.cn
@license  https://github.com/whalesky-labs/AgentLight
```

规则：

- C/C++ 文件使用 `/** ... */` 块注释，并放在 `#include` 之前。
- Python 文件如果有 shebang，必须保留 shebang 在第一行，然后使用 `#` 行注释文件头。
- Shell 文件保留 shebang 在第一行，然后使用 `#` 行注释文件头。
- PowerShell 文件使用 `<# ... #>` 块注释，并放在可执行代码之前。
- Markdown、JSON、YAML、INI 和生成文件不添加源代码文件头。

## 架构边界

- 固件代码按 `domain`、`application`、`infrastructure` 和 `main.cpp` 分层。
- 桌面 Agent 代码按 `agentlight_agent/domain`、`application`、`infrastructure` 和 `interfaces` 分层。
- `domain` 不允许读取文件、启动进程、访问硬件或调用网络 API。
- `application` 负责用例编排和业务策略，不承载传输协议解析细节。
- `infrastructure` 负责硬件 IO、文件系统、子进程、JSON 配置加载和外部命令执行。
- `interfaces` 只负责 CLI 参数解析和输出。
- `scripts/agentlight-agent` 和 `scripts/multi-agent-monitor` 必须保持向后兼容的薄入口。

## 实现标准

- 不添加隐藏根因的兜底行为、临时补丁或兼容胶水。
- 结构化数据优先使用类型模型和显式校验，避免松散字典贯穿业务层。
- 函数保持小而明确，每个函数只承担一个清晰职责。
- 除非需求明确要求破坏性变更，否则保持既有 CLI 名称、服务名称和文档化命令行为。
- 生成物不进入 Git。
- 中英双语内容并存时，中文内容优先展示。

## 代码风格

- C/C++：沿用 Arduino 兼容 C++ 风格，2 空格缩进，类型使用 `PascalCase`，函数使用 `camelCase`，私有字段使用尾部 `_`。
- Python：使用类型注解，结构化领域数据使用 dataclass/enum，4 空格缩进，导入路径不产生隐藏全局副作用。
- Shell：使用 `set -euo pipefail`，变量必须加引号，仓库相对路径必须显式解析。
- PowerShell：使用 `$ErrorActionPreference = "Stop"`，服务名必须带 `whalesky-labs-AgentLight` 前缀。
- Markdown：中英双语内容并存时，中文在前。

## 验证要求

常规变更完成前至少运行：

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

## 提交和推送规则

- 提交信息必须使用 conventional commit 风格。
- 提交正文必须包含 `Summary:` 和 `Details:`。
- 从这台 Mac 推送 GitHub 必须使用本机 VPN 代理：

```bash
git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push origin main
```
