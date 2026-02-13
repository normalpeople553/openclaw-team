# OpenClaw Team - 零知识团队协作服务器

一个安全的零知识团队协作 Web 界面，多用户可通过局域网 WiFi 访问 OpenClaw。

## 背景

适用于部署一个 OpenClaw 实例，但可以多人共同使用——每个用户拥有独立的加密存储空间，实现真正的数据隔离。

## 特性

- 🔐 **零知识架构**：服务器不存储任何密码数据，用户数据只能用正确密码解密
- 👥 **多用户数据隔离**：每个用户独立文件夹，AES-256 加密，密码即密钥
- 📱 **跨设备访问**：支持电脑和手机通过局域网 IP 访问
- 🛡️ **端到端加密**：所有用户数据（历史、记忆、灵魂）在传输和存储全程加密
- 🔑 **设备绑定登录**：无需会话 Token，登录状态保存在浏览器 localStorage
- ⚡ **轻量部署**：无需数据库，一个 Python 脚本即可运行

## 适用场景

- **家庭共享**：一家人共用一个 OpenClaw 实例，各自拥有独立对话历史
- **团队协作**：小团队共享 AI 助手，每个人的数据和配置完全隔离
- **隐私敏感**：对数据安全有要求，不想让管理员或服务器运营方看到任何用户数据

## 技术亮点

### 1. 零知识认证（Zero-Knowledge）

传统方案：服务器存储密码 hash，登录时比对。

**本方案**：
- 服务器**不存储**任何密码相关数据
- 注册时：用密码加密生成 `credential.enc`（包含用户身份证明）
- 登录时：服务器尝试用提交的密码解密 `credential.enc`
- 解开 → 证明密码正确；解不开 → 登录失败

即使服务器被攻破、数据库被拖走，攻击者也无法恢复任何用户密码或解密数据。

### 2. 密码即密钥

用户的密码同时用于：
- 身份验证（解密 credential.enc）
- 数据加密（加密 history.enc、memory.enc、soul.enc）

密码丢失 = 数据永久丢失。这是特性，不是 bug——确保了**只有用户自己**能访问自己的数据。

### 3. 数据隔离

```
~/Desktop/alldata/
├── .protected          # 保护标记，防止误删
├── alice/             # Alice 的数据
│   ├── credential.enc
│   ├── config.json
│   ├── soul.enc
│   ├── memory.enc
│   └── history.enc
└── bob/               # Bob 的数据
    ├── credential.enc
    ├── config.json
    ├── soul.enc
    ├── memory.enc
    └── history.enc
```

每个文件夹只能被对应密码解密，Bob 无法读取 Alice 的任何文件。

### 4. 第一原则约束

代码中内置安全注释：
```python
# ⚠️ 安全原则：禁止删除 alldata 目录下任何非用户自己的文件夹
```

AI 助手不会执行任何删除他人数据的指令。

## 快速开始

```bash
# 1. 安装依赖
pip install flask flask-cors cryptography requests gunicorn

# 2. 启动服务器
gunicorn -w 4 -b 0.0.0.0:8888 team_chat_server:app
```

访问: `http://<你的IP>:8888`

默认邀请码: `OPENCLAW2026`

## 自定义邀请码

```bash
# 方式1: 环境变量
INVITE_CODE=你的邀请码 gunicorn -w 4 -b 0.0.0.0:8888 team_chat_server:app

# 方式2: 直接修改代码中的 INVITE_CODE 常量
```

## 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| PORT | 8888 | 服务器端口 |
| INVITE_CODE | OPENCLAW2026 | 注册邀请码 |
| DATA_DIR | ~/Desktop/alldata | 数据存储目录 |
| GATEWAY_URL | http://127.0.0.1:18789 | OpenClaw Gateway API |
| GATEWAY_TOKEN | (配置中获取) | Gateway 认证令牌 |

## API 接口

- `POST /api/check_invite` - 验证邀请码
- `POST /api/register` - 注册新用户
- `POST /api/login` - 登录（通过解密凭证验证）
- `POST /api/chat` - 发送消息到 OpenClaw

## 故障排除

**无法从其他设备访问？**
- 确保防火墙允许该端口
- 使用电脑的局域网 IP（不是 localhost）

**注册失败？**
- 检查邀请码是否正确
- 用户名必须 1-15 个字符
- 密码至少 4 个字符

**提示登录过期？**
- 这是正常的 - 登录是基于设备的，刷新页面重新验证

## 与传统方案对比

| 特性 | 传统方案 | OpenClaw Team |
|------|----------|---------------|
| 密码存储 | 服务器存 hash | 服务器不存任何密码数据 |
| 数据隔离 | 管理员可查看 | 只有用户自己能解密 |
| 会话管理 | Token 有过期时间 | 设备绑定，永不过期 |
| 数据恢复 | 管理员可重置 | 密码丢失 = 数据丢失 |

## 技术栈

- Flask + Gunicorn
- Cryptography (Fernet/AES-256)
- 零知识认证架构
- PBKDF2 密钥派生

## 许可证

Apache License 2.0
