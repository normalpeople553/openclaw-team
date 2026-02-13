# OpenClaw Team - Zero-Knowledge Team Collaboration Server

A secure zero-knowledge team collaboration web interface for OpenClaw. Multiple users can access OpenClaw via local WiFi network.

## Background

Designed for deploying a single OpenClaw instance that multiple users can share—each user gets isolated encrypted storage, achieving true data separation.

## Features

- 🔐 **Zero-knowledge**: Server never stores any password data; user data can only be decrypted with correct password
- 👥 **Data isolation**: Each user has independent folder with AES-256 encryption, password is the key
- 📱 **Cross-device**: Access via LAN IP from desktop or mobile
- 🛡️ **End-to-end encrypted**: All user data (history, memory, soul) encrypted in transit and at rest
- 🔑 **Device-based login**: No session tokens; login state stored in browser localStorage
- ⚡ **Lightweight**: No database needed; runs with a single Python script

## Use Cases

- **Family sharing**: Family shares one OpenClaw instance, each with independent conversation history
- **Team collaboration**: Small teams share AI assistant with complete data isolation per user
- **Privacy-sensitive**: High security requirements—neither admins nor server operators can see any user data

## Technical Highlights

### 1. Zero-Knowledge Architecture

Traditional approach: Server stores password hash, compares on login.

**This solution**:
- Server stores **nothing** password-related
- Registration: Encrypt `credential.enc` (contains user identity proof) using password
- Login: Server attempts to decrypt `credential.enc` with provided password
- Decrypt success → password verified; decrypt fail → login failed

Even if server is compromised and database stolen, attackers cannot recover any passwords or decrypt user data.

### 2. Password is the Key

User's password is used for:
- Authentication (decrypt credential.enc)
- Data encryption (encrypt history.enc, memory.enc, soul.enc)

Password lost = data permanently lost. This is a feature, not a bug—ensures **only the user** can access their own data.

### 3. Data Isolation

```
~/Desktop/alldata/
├── .protected          # Protection flag, prevents accidental deletion
├── alice/             # Alice's data
│   ├── credential.enc
│   ├── config.json
│   ├── soul.enc
│   ├── memory.enc
│   └── history.enc
└── bob/               # Bob's data
    ├── credential.enc
    ├── config.json
    ├── soul.enc
    ├── memory.enc
    └── history.enc
```

Each folder can only be decrypted with corresponding password—Bob cannot read any of Alice's files.

### 4. First Principle Restriction

Security comment embedded in code:
```python
# ⚠️ Security principle: Never delete any folder in alldata except user's own folder
```

AI assistant will not execute any command to delete other users' data.

## Quick Start

```bash
# 1. Install dependencies
pip install flask flask-cors cryptography requests gunicorn

# 2. Start server
gunicorn -w 4 -b 0.0.0.0:8888 team_chat_server:app
```

Access at: `http://<your-ip>:8888`

Default invite code: `OPENCLAW2026`

## Custom Invite Code

```bash
# Option 1: Environment variable
INVITE_CODE=your_code gunicorn -w 4 -b 0.0.0.0:8888 team_chat_server:app

# Option 2: Edit INVITE_CODE constant in the script
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 8888 | Server port |
| INVITE_CODE | OPENCLAW2026 | Invite code for registration |
| DATA_DIR | ~/Desktop/alldata | Data storage directory |
| GATEWAY_URL | http://127.0.0.1:18789 | OpenClaw Gateway API |
| GATEWAY_TOKEN | (from config) | Gateway auth token |

## API Endpoints

- `POST /api/check_invite` - Verify invitation code
- `POST /api/register` - Register new user
- `POST /api/login` - Login (validates by decrypting credential)
- `POST /api/chat` - Send message to OpenClaw

## Troubleshooting

**Can't access from other device?**
- Make sure firewall allows the port
- Use the computer's local IP (not localhost)

**Registration fails?**
- Check invitation code matches
- Username must be 1-15 characters
- Password must be at least 4 characters

**Login keeps expiring?**
- This is expected - login is device-based, refresh page to re-authenticate

## Comparison with Traditional Solutions

| Feature | Traditional | OpenClaw Team |
|---------|-------------|---------------|
| Password storage | Server stores hash | Server stores nothing password-related |
| Data isolation | Admins can view | Only user can decrypt |
| Session management | Token expires | Device-based, never expires |
| Data recovery | Admin can reset | Password lost = data lost |

## Tech Stack

- Flask + Gunicorn
- Cryptography (Fernet/AES-256)
- Zero-knowledge architecture
- PBKDF2 key derivation

## License

Apache License 2.0
