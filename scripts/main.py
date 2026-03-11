#!/usr/bin/env python3
"""
OpenClaw 团队协作服务器 - 入口文件
"""

import os
import json
import hashlib
import base64
import secrets
import socket
from datetime import datetime
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ====== 配置 ======
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://127.0.0.1:18789")
GATEWAY_TOKEN = os.environ.get("GATEWAY_TOKEN", "")
PORT = int(os.environ.get("PORT", "8888"))
DATA_DIR = os.path.expanduser("~/Desktop/alldata")
CREDENTIAL_FILE = "credential.enc"
INVITE_CODE = os.environ.get("INVITE_CODE", "OPENCLAW2026")  # 邀请码，可通过环境变量自定义
BRAND_NAME = os.environ.get("BRAND_NAME", "OPENCLAW-TEAM")  # 品牌名称，可通过环境变量自定义
# ==================

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()
print(f"📡 本地IP: {LOCAL_IP}")

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app, origins=[f"http://{LOCAL_IP}:{PORT}", f"http://127.0.0.1:{PORT}"], supports_credentials=True)

# 导入并注册上传路由
from upload import register_upload_routes
register_upload_routes(app, DATA_DIR, CREDENTIAL_FILE, LOCAL_IP, PORT)

# ====== 工具函数 =====
def encrypt_data(data: str, password: str) -> str:
    key = hashlib.sha256(password.encode()).digest()
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted: str, password: str) -> str:
    key = hashlib.sha256(password.encode()).digest()
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.decrypt(encrypted.encode()).decode()

def generate_key(password: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def get_user_dir(username: str) -> str:
    safe_name = username.replace(" ", "_")
    return os.path.join(DATA_DIR, safe_name)

def load_encrypted_json(file_path: str, password: str, default):
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        if not content:
            return default
        return json.loads(decrypt_data(content, password))
    except Exception:
        return default


def save_encrypted_json(file_path: str, password: str, data):
    with open(file_path, 'w') as f:
        f.write(encrypt_data(json.dumps(data, ensure_ascii=False, indent=2), password))


def build_memory_system_prompt(memory_items):
    if not memory_items:
        return None
    lines = ["以下是当前用户的长期记忆，只供你在本次回复时参考："]
    for item in memory_items:
        if isinstance(item, dict) and item.get('content'):
            tag = item.get('type', 'memory')
            lines.append(f"- [{tag}] {item['content']}")
    return "\n".join(lines)


def extract_memory_items(user_message: str, assistant_message: str):
    items = []
    text = (user_message or '').strip()
    if not text:
        return items

    explicit_markers = ["记住", "记一下", "帮我记住", "请记住", "记在心里"]
    if any(marker in text for marker in explicit_markers):
        cleaned = text
        for marker in explicit_markers:
            cleaned = cleaned.replace(marker, '')
        cleaned = cleaned.strip('：:，,。；; ')
        if cleaned:
            items.append({"type": "explicit", "content": cleaned, "created": datetime.now().isoformat()})

    auto_prefixes = ["我是", "我叫", "我负责", "我喜欢", "我不喜欢", "我的偏好是", "以后回复我", "以后叫我"]
    if any(text.startswith(prefix) for prefix in auto_prefixes):
        items.append({"type": "auto", "content": text, "created": datetime.now().isoformat()})

    return items


def merge_memory(memory_items, new_items, limit=200):
    existing = {item.get('content') for item in memory_items if isinstance(item, dict)}
    for item in new_items:
        content = item.get('content') if isinstance(item, dict) else None
        if content and content not in existing:
            memory_items.append(item)
            existing.add(content)
    return memory_items[-limit:]

# ====== 路由 =====
@app.route('/')
def index():
    # 读取HTML文件
    html_path = os.path.join(os.path.dirname(__file__), 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取前端配置"""
    return jsonify({
        "brand_name": BRAND_NAME
    })

@app.route('/api/check_invite', methods=['POST'])
def check_invite():
    data = request.get_json()
    code = data.get('code', '')
    return jsonify({"valid": code == INVITE_CODE})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    invite_code = data.get('invite_code', '')
    
    if invite_code != INVITE_CODE:
        return jsonify({"success": False, "error": "邀请码错误"}), 400
    if len(username) > 15 or not username:
        return jsonify({"success": False, "error": "用户名需要1-15字符"}), 400
    if len(password) < 4:
        return jsonify({"success": False, "error": "密码至少4个字符"}), 400
    
    user_dir = get_user_dir(username)
    if os.path.exists(os.path.join(user_dir, CREDENTIAL_FILE)):
        return jsonify({"success": False, "error": "用户已存在"}), 400
    
    os.makedirs(user_dir, exist_ok=True)
    
    # 创建加密凭证
    encrypted = encrypt_data(f"OPENCLAW_USER:{username}", password)
    with open(os.path.join(user_dir, CREDENTIAL_FILE), 'w') as f:
        f.write(encrypted)
    
    # 保存配置
    config = {"username": username, "created": datetime.now().isoformat()}
    with open(os.path.join(user_dir, "config.json"), 'w') as f:
        json.dump(config, f, indent=2)
    
    # 创建用户文件
    save_encrypted_json(os.path.join(user_dir, "memory.enc"), password, [])
    save_encrypted_json(os.path.join(user_dir, "history.enc"), password, [])
    
    print(f"✅ 新用户注册: {username}")
    return jsonify({"success": True, "username": username})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    user_dir = get_user_dir(username)
    cred_file = os.path.join(user_dir, CREDENTIAL_FILE)
    
    if not os.path.exists(cred_file):
        return jsonify({"success": False, "error": "用户不存在"}), 401
    
    try:
        with open(cred_file, 'r') as f:
            encrypted = f.read()
        cipher = Fernet(generate_key(password))
        decrypted = cipher.decrypt(encrypted.encode())
        if decrypted.decode() == f"OPENCLAW_USER:{username}":
            print(f"✅ 用户登录: {username}")
            return jsonify({"success": True, "username": username})
    except:
        pass
    
    return jsonify({"success": False, "error": "密码错误"}), 401

@app.route('/api/history', methods=['POST'])
def get_history():
    """获取聊天历史"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username:
        return jsonify({"error": "用户名为空"}), 400
    
    # 验证用户
    user_dir = os.path.join(DATA_DIR, username)
    cred_file = os.path.join(user_dir, CREDENTIAL_FILE)
    
    if not os.path.exists(cred_file):
        return jsonify({"error": "用户不存在"}), 401
    
    try:
        with open(cred_file, 'r') as f:
            encrypted = f.read()
        cipher = Fernet(generate_key(password))
        decrypted = cipher.decrypt(encrypted.encode())
        if not decrypted.decode().startswith("OPENCLAW_USER:" + username):
            return jsonify({"error": "验证失败"}), 401
    except:
        return jsonify({"error": "验证失败"}), 401
    
    # 获取历史
    history_file = os.path.join(user_dir, "history.enc")
    history = load_encrypted_json(history_file, password, [])
    
    return jsonify({"success": True, "history": history})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not user_message or not username:
        return jsonify({"error": "消息或用户名为空"}), 400
    
    # 验证用户
    user_dir = os.path.join(DATA_DIR, username)
    cred_file = os.path.join(user_dir, CREDENTIAL_FILE)
    
    if not os.path.exists(cred_file):
        return jsonify({"error": "用户不存在"}), 401
    
    try:
        with open(cred_file, 'r') as f:
            encrypted = f.read()
        cipher = Fernet(generate_key(password))
        decrypted = cipher.decrypt(encrypted.encode())
        if not decrypted.decode().startswith("OPENCLAW_USER:" + username):
            return jsonify({"error": "验证失败"}), 401
    except:
        return jsonify({"error": "验证失败"}), 401
    
    # 获取历史和长期记忆
    history_file = os.path.join(user_dir, "history.enc")
    memory_file = os.path.join(user_dir, "memory.enc")
    history = load_encrypted_json(history_file, password, [])
    memory_items = load_encrypted_json(memory_file, password, [])
    
    messages = []
    memory_prompt = build_memory_system_prompt(memory_items)
    if memory_prompt:
        messages.append({"role": "system", "content": memory_prompt})

    for msg in history:
        role = msg.get("role")
        content = msg.get("content")
        if role in ["user", "assistant", "system"] and isinstance(content, str):
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    payload = {"model": "openclaw:main", "messages": messages, "stream": False}
    print("=== gateway payload ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    
    # 调用 API
    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {GATEWAY_TOKEN}", "Content-Type": "application/json"},
            json=payload,
            timeout=120
        )
        print("=== gateway response ===")
        print(response.status_code)
        print(response.text)
        
        if response.status_code != 200:
            return jsonify({"error": f"API错误: {response.status_code}，详情: {response.text}"}), 500
        
        result = response.json()
        assistant_message = result['choices'][0]['message']['content']
        
        # 保存历史（最近 50 轮 = 100 条消息）
        now = datetime.now().isoformat()
        history.append({"role": "user", "content": user_message, "timestamp": now})
        history.append({"role": "assistant", "content": assistant_message, "timestamp": now})
        history = history[-100:]
        save_encrypted_json(history_file, password, history)

        # 更新长期记忆：用户明确要求记住 + 少量明显长期信息自动记
        new_memory_items = extract_memory_items(user_message, assistant_message)
        if new_memory_items:
            memory_items = merge_memory(memory_items, new_memory_items)
            save_encrypted_json(memory_file, password, memory_items)
        
        return jsonify({"response": assistant_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"🚀 OpenClaw 团队协作平台启动!")
    print(f"   访问: http://0.0.0.0:{PORT}")
    print(f"   数据目录: {DATA_DIR}")
    print(f"   邀请码: {INVITE_CODE}")
    print(f"   Gateway URL: {GATEWAY_URL}")
    print(f"   Gateway Token 已配置: {'是' if bool(GATEWAY_TOKEN) else '否'}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
