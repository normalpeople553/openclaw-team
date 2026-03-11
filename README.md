# OpenClaw Team

一个给 OpenClaw 做多人访问包装的轻量 Web 项目。

目标不是把 OpenClaw 改造成多租户平台，而是在一台机器上提供一个简单的团队入口：
- 多个用户可通过网页访问同一个统一助手人格
- 每个用户有自己的注册信息、聊天历史、长期记忆文件
- 前端支持登录、注册、聊天、上传文件
- 后端通过 OpenClaw Gateway 的兼容接口转发消息

注意：当前版本仍然是实验性方案，适合本地/局域网测试，不适合直接作为生产级多租户系统上线。

## 当前能力

- 邀请码注册
- 用户名 + 密码登录
- 每个用户独立数据目录
- `history.enc`：保存最近 50 轮对话（100 条消息）
- `memory.enc`：保存长期记忆
- 基于密码的本地加密存储
- 文件上传
- 聊天消息支持更好的文本展示：
  - 换行
  - 有序/无序列表
  - 行内代码
  - 代码块
  - 链接点击
- 后端支持从 `scripts/.env` 读取配置

## 当前数据模型

每个用户的数据默认保存在：

`~/Desktop/alldata/<username>/`

目录内容大致包括：

- `credential.enc`：登录验证数据
- `config.json`：用户配置
- `memory.enc`：长期记忆
- `history.enc`：近期对话历史

说明：
- 当前版本已不再要求新用户创建 `soul.enc`
- 统一助手人格由系统提示词和公共上下文维持，而不是每个用户单独一份 soul 文件

## 记忆与历史的当前行为

### history
- 每次回复后写回
- 仅保留最近 50 轮对话
- 用于短期上下文续聊

### memory
- 每个用户独立
- 当前会在以下场景写入：
  - 用户明确说“记住”“记一下”“帮我记住”
  - 少量明显长期信息自动记
- 在每次聊天时会读取并作为额外 system context 注入

## 重要限制

这个项目当前最大的限制是：

虽然文件层面已经做了“每用户独立 history / memory”，但 OpenClaw Gateway 兼容接口这一层，当前仍然可能存在会话上下文共享问题。

这意味着：
- 文件隔离 ≠ 后端会话彻底隔离
- 现阶段已经加入了“防跨用户泄露”的 system prompt 作为缓解措施
- 但这不是严格安全隔离

所以当前版本更准确的定位是：

“一个适合局域网/内测环境的多人访问原型”，
而不是“已经完成真正多租户隔离的正式产品”。

## 运行方式

### 方式 1：使用启动脚本

```bash
./start.sh
```

### 方式 2：手动运行

```bash
cd scripts
python3 main.py
```

## 配置方式

主程序会优先读取：

`scripts/.env`

示例：

```env
GATEWAY_URL=http://127.0.0.1:18789
GATEWAY_TOKEN=你的网关token
PORT=8888
INVITE_CODE=OPENCLAW2026
BRAND_NAME=OPENCLAW-TEAM
```

## 依赖安装

当前 Python 依赖位于：

`scripts/requirements.txt`

安装方式：

```bash
cd scripts
pip install -r requirements.txt
```

## 项目结构

```text
openclaw-team/
├── README.md
├── start.sh
├── scripts/
│   ├── main.py
│   ├── index.html
│   ├── upload.py
│   ├── requirements.txt
│   └── team_chat_server.py
├── .env.example
├── .gitignore
├── SKILL.md
└── license.txt
```

## 当前推荐用途

适合：
- 本地测试
- 局域网多人试用
- 团队内部原型验证
- 验证“统一人格 + 每用户独立文件存储”的交互模型

不适合：
- 公网直接暴露
- 高安全要求生产环境
- 对“强隔离、多租户安全边界”有严格要求的场景

## 最近更新

当前版本已补充：
- 网关配置改为优先从环境变量 / `scripts/.env` 读取
- 聊天调试日志
- 长期记忆读写入口
- 历史记录裁剪为最近 50 轮
- 前端更好的消息格式渲染
- 防跨用户泄露的 system prompt

## 后续建议方向

如果要继续演进，建议优先做这两件事：

1. 让每个网页用户绑定独立的 OpenClaw 后端 session
2. 进一步收紧用户名校验、路径安全、上传安全与凭证管理

## License

Apache License 2.0
