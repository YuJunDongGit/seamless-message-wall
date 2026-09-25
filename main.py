from flask import Flask, render_template_string, request, redirect, url_for, session, flash, g
import sqlite3
import os
from datetime import datetime, timedelta
import pytz
import hashlib
import random
import socket
import subprocess

from ybc_commons.util.predicates import false


# 前置函数
def JD_tihuan(Str, th):
    res = Str
    for i in th:
        res = res.replace(i, th[i])
    return res

def search_after(text, pattern):
    index = text.find(pattern)
    Strstr = text[index + len(pattern):] if index != -1 else None
    resulStr = ""
    for i in Strstr:
        if i == '\n':
            break
        else:
            resulStr += i
    return resulStr

def get_flask_IPv6_address():
    return search_after(subprocess.run("ipconfig", shell=True, capture_output=True).stdout.decode('gbk'), "IPv4 地址 . . . . . . . . . . . . : ")


def minify_html(html):
    import re
    # 去除注释、空行、多余空格
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)  # 去除注释
    html = re.sub(r'\n\s+', '\n', html)  # 去除行前多余空格
    html = re.sub(r'\s+', ' ', html)  # 多个空格替换为单个空格
    return html


# 前置函数

app = Flask(__name__)
app.secret_key = 'yoursecretkeyhere'

# 数据库配置
DATABASE = 'messagewall.db'
MESSAGE_EXPIRE_DAYS = 5  # 留言过期时间设为5天

# IP配置
IPv6interfaces = socket.getaddrinfo(socket.gethostname(), None)
IPv6DZ ='http://' + get_flask_IPv6_address()
IP_PORT = 7891
static_add = str(IPv6DZ) + ":" + str(IP_PORT) + "/static/"

# 敏感词配置
mgc_par = ['鸡巴','几把','极霸'
                    "阴茎","精子","77",'nm','亖',
                    '精液','子宫','卵巢','答辩','大便']
class mgc:
    def __init__(self, str):
        self.str = str
        return
    def __bool__(self):# 判断是否敏感
        flag = False
        t_str = self.str.lower()
        t_str = t_str.replace(" ", "")
        t_str = t_str.replace("\n", "")
        t_str = t_str.replace("\r\n", "")
        t_str = t_str.replace("\r", "")
        t_str = t_str.replace("_", "")
        for i in mgc_par:
            if i in t_str:
                return False
        return False

# HTML模板（修改后的版本）
INDEX_HTML = '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>留言墙</title>
    <style>
        :root {
            --primary-color: #3B82F6;
            --secondary-color: #6366F1;
            --accent-color: #EF4444;
            --text-color: #1F2937;
            --light-bg: #F3F4F6;
            --success-color: #10B981;
            --heading-font: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--light-bg);
            line-height: 1.6;
            color: var(--text-color);
        }

        .container {
            max-width: 800px;
            margin: 20px auto;
            background-color: transparent;
            padding: 25px;
            border-radius: 12px;
        }

        .header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 40px 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .header:hover {
            border-left-color: var(--secondary-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        h1 {
            color: white;
            text-align: center;
            
        }

        .message-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border-left: 4px solid var(--primary-color);
            transition: all 0.3s ease;
            /* 新增：限制最大高度和溢出处理 */
            max-height: 500px;
            overflow: auto;
        }

        .message-card:hover {
            border-left-color: var(--secondary-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        .message-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-weight: 600;
        }

        .username {
            color: var(--primary-color);
        }

        .timestamp {
            color: #6B7280;
            font-size: 0.9rem;
        }

        .content {
            margin-top: 10px;
            line-height: 1.6;
            /* 新增：文本自动换行处理 */
            word-wrap: break-word;
            white-space: pre-wrap;
            overflow-wrap: break-word;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: var(--text-color);
        }

        input[type="text"],
        input[type="password"],
        textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #D1D5DB;
            border-radius: 8px;
            box-sizing: border-box;
            font-family: inherit;
            font-size: 1rem;
            transition: border-color 0.3s;
        }

        textarea {
            height: 120px;
            resize: vertical;
            /* 新增：文本自动换行处理 */
            word-wrap: break-word;
            white-space: pre-wrap;
            overflow-wrap: break-word;
        }

        input:focus, textarea:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        }

        /* 统一按钮基础样式 */
        .btn, .red-button {
            position: relative;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            font-size: 1rem;
            transition: all 0.3s ease;
            overflow: hidden;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 120px; /* 添加最小宽度 */
            min-height: 42px; /* 添加最小高度 */
            padding: 0 16px; /* 添加水平内边距 */
        }

        .btn:hover, .red-button:hover {
            background-color: #2563EB;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
        }

        .red-button {
            background-color: var(--accent-color);
            margin-top: 20px;
            width: 100%;
        }

        .red-button:hover {
            background-color: #DC2626;
        }

        /* 关键修复：让链接填满整个按钮并保持合适尺寸 */
        .btn a, .red-button a {
            display: block;
            width: 100%;
            height: 100%;
            color: white;
            text-decoration: none;
            box-sizing: border-box;
        }

        /* 修复表单按钮的特殊样式 */
        .form-btn-container {
            display: flex;
            justify-content: flex-end;
            margin-top: 10px;
        }

        .auth-container {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 30px;
        }

        .auth-form {
            flex: 1;
            background-color: #81C5F9;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        
        .auth-form:hover {
            border-left-color: var(--secondary-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        }
        
        .tabs {
            display: flex;
            margin-bottom: 25px;
            border-bottom: 1px solid #E5E7EB;
        }

        .tab {
            padding: 12px 24px;
            cursor: pointer;
            background-color: #E5E7EB;
            border-radius: 8px 8px 0 0;
            margin-right: 5px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .tab.active {
            background-color: var(--primary-color);
            color: white;
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.5s;
        }

        .tab-content.active {
            display: block;
        }

        .flash {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            font-weight: 500;
        }

        .flash.success {
            background-color: rgba(16, 185, 129, 0.1);
            border-left: 4px solid var(--success-color);
            color: var(--success-color);
        }

        .flash.error {
            background-color: rgba(239, 68, 68, 0.1);
            border-left: 4px solid var(--accent-color);
            color: var(--accent-color);
        }

        textarea::placeholder {
            color: #9CA3AF;
            font-style: italic;
        }

        /* 为表单按钮添加特殊容器 */
        .form-btn-wrapper {
            display: flex;
            justify-content: flex-end;
            margin-top: 15px;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @media (max-width: 768px) {
            .auth-container {
                flex-direction: column;
            }

            .container {
                padding: 15px;
                margin: 10px;
            }

            /* 移动端按钮内边距调整 */
            .btn, .red-button {
                min-width: 100%;
                min-height: 40px;
                padding: 10px;
            }

            .form-btn-wrapper {
                justify-content: flex-start;
            }

            /* 移动端消息卡片调整 */
            .message-card {
                padding: 15px;
            }
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            font-size: 0.9rem;
            color: #6B7280;
        }

        /* 新增：滚动条样式 */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
        
        h2\.5 {
            font-family: var(--heading-font);
            font-size: calc(1.33em + 0.17vw); /* 约21.36px，响应式调整 */
            font-weight: 600; /* 介于h2(600)和h3(400)之间 */
            line-height: 1.3;
            margin: 0.85em 0; /* 接近h2(0.83em)和h3(1em)的间距 */
        }
    </style>
    
    <script> 
        let keys = {
            ctrl: false,
            q: false,
            enter: false
        };
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Control') keys.ctrl = true;
            if (e.key.toLowerCase() === 'q') keys.q = true;
            if (e.key === 'Enter') keys.enter = true;
        
            if (keys.ctrl && keys.q && keys.enter) {
                window.prompt('请问您要对谁发呢？','all');
                keys.ctrl = false;
                keys.q = false;
                keys.enter = false;
                e.preventDefault();
            }
        });
        
        document.addEventListener('keyup', (e) => {
            if (e.key === 'Control') keys.ctrl = false;
            if (e.key.toLowerCase() === 'q') keys.q = false;
            if (e.key === 'Enter') keys.enter = false;
        });
    </script>
</head>
<body>
    <div>
        <div class="container">
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash {{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            {% if session['user_id'] %}
            <div class="header">
                <h1>留言墙</h1>
                <br>
                <h2.5>欢迎, {{ current_user['username'] }}!</h2.5>
                <br><br>
                <div class="form-group">
                    <form method="post" action="{{ url_for('send_message') }}" id="messageForm">
                        <textarea id="message" name="message" placeholder="请发表留言，按 Ctrl+Enter 发送" required></textarea>

                        <!-- 使用专用容器包裹按钮 -->
                        <div class="form-btn-wrapper">
                            <button type="submit" class="btn">
                                <span>发送</span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
                <div class="tabs">
                    <div class="tab active" onclick="showTab('messages')">留言列表</div>
                    <div class="tab" onclick="showTab('change-password')">修改密码</div>
                </div>

                <div id="messages" class="tab-content active">
                    <h2>留言列表</h2>
                    <br>
                    {% if messages %}
                        {% for message in messages %}
                            <div class="message-card">
                                <div class="message-header">
                                    <span class="username">{{ message['username'] }}</span>
                                    <span class="timestamp">{{ message['created_at'] }}</span>
                                </div>
                                <div class="content">{{ message['content'] }}</div>
                            </div>
                        {% endfor %}
                    {% else %}
                        <p>暂无留言</p>
                    {% endif %}
                </div>

                <div id="change-password" class="tab-content">
                    <h2>修改密码</h2>
                    <form method="post" action="{{ url_for('change_password') }}">
                        <div class="form-group">
                            <label for="current_password">当前密码:</label>
                            <input type="password" id="current_password" name="current_password" required>
                        </div>
                        <div class="form-group">
                            <label for="new_password">新密码:</label>
                            <input type="password" id="new_password" name="new_password" required>
                        </div>
                        <div class="form-group">
                            <label for="confirm_password">确认新密码:</label>
                            <input type="password" id="confirm_password" name="confirm_password" required>
                        </div>

                        <!-- 使用专用容器包裹按钮 -->
                        <div class="form-btn-wrapper">
                            <button type="submit" class="btn">
                                <span>修改密码</span>
                            </button>
                        </div>
                    </form>
                </div>
                
                <button class="red-button">
                    <a href="{{ url_for('logout') }}">
                        <span>退出登录</span>
                    </a>
                </button>

                <button class="red-button">
                    <a href="{{ url_for('rules') }}">
                        <span>畅连消息墙公约</span>
                    </a>
                </button>
                
            {% else %}
                <div class="header">
                    <h1>留言墙</h1>
                </div>
                <div class="auth-container">
                    <div class="auth-form">
                        <h2>登录</h2>
                        <form method="post" action="{{ url_for('login') }}">
                            <div class="form-group">
                                <label for="login_username">用户名:</label>
                                <input type="text" id="login_username" name="username" required>
                            </div>
                            <div class="form-group">
                                <label for="login_password">密码:</label>
                                <input type="password" id="login_password" name="password" required>
                            </div>

                            <!-- 使用专用容器包裹按钮 -->
                            <div class="form-btn-wrapper">
                                <button type="submit" class="btn">
                                    <span>登录</span>
                                </button>
                            </div>
                        </form>
                    </div>

                    <div class="auth-form">
                        <h2>注册</h2>
                        <form method="post" action="{{ url_for('register') }}">
                            <div class="form-group">
                                <label for="register_username">用户名:</label>
                                <input type="text" id="register_username" name="username" required>
                            </div>
                            <div class="form-group">
                                <label for="register_password">密码:</label>
                                <input type="password" id="register_password" name="password" required>
                            </div>

                            <!-- 使用专用容器包裹按钮 -->
                            <div class="form-btn-wrapper">
                                <button type="submit" class="btn">
                                    <span>注册</span>
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
                
                <button class="red-button">
                    <a href="{{ url_for('rules') }}">
                        <span>畅连消息墙公约</span>
                    </a>
                </button>
            {% endif %}
        </div>

        <script>
            function showTab(tabName) {
                // 隐藏所有标签内容
                const tabContents = document.querySelectorAll('.tab-content');
                tabContents.forEach(content => {
                    content.classList.remove('active');
                });

                // 移除所有标签的活动状态
                const tabs = document.querySelectorAll('.tab');
                tabs.forEach(tab => {
                    tab.classList.remove('active');
                });

                // 显示选中的标签内容
                document.getElementById(tabName).classList.add('active');

                // 添加活动状态到选中的标签
                event.target.classList.add('active');
            }

            // 添加Ctrl+Enter监听功能
            document.addEventListener('DOMContentLoaded', function() {
                const messageTextarea = document.getElementById('message');

                if (messageTextarea) {
                    messageTextarea.addEventListener('keydown', function(event) {
                        // 检查是否同时按下了Ctrl键和Enter键
                        if (event.ctrlKey && event.key === 'Enter') {
                            // 阻止默认行为（防止换行）
                            event.preventDefault();

                            // 获取表单并提交
                            const form = document.getElementById('messageForm');
                            if (form) {
                                form.submit();
                            }
                        }
                    });
                }
            });
        </script>
        <div class="footer">
            <p>© 2025 畅连消息墙.余俊东 版权所有</p>
            <p>未经许可，不得复制、传播或用于商业用途</p>
        </div>
        <br>
    </div>
</body>
</html>
'''

# 数据库连接函数
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


# 关闭数据库连接
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# 初始化数据库
def init_db():
    # 如果数据库文件存在，先删除它
    if os.path.exists(DATABASE):
        os.remove(DATABASE)

    with app.app_context():
        db = get_db()
        # 创建用户表
        db.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # 创建消息表
        db.execute('''
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        # 创建默认管理员账号
        admin_password = hashlib.md5('admin'.encode()).hexdigest()
        db.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                   ['admin', admin_password])
        db.commit()


# 清理过期消息函数
def clean_expired_messages():
    db = get_db()
    # 计算过期时间点（当前时间减去5天）
    expire_time = datetime.utcnow() - timedelta(days=MESSAGE_EXPIRE_DAYS)
    # 删除早于过期时间点的消息
    db.execute('DELETE FROM messages WHERE created_at < ?', [expire_time])
    db.commit()


# 首页
@app.route('/')
def index():
    db = get_db()

    # 获取所有消息，包括用户名
    cursor = db.execute('''
        SELECT m.id, m.content, m.created_at, u.username 
        FROM messages m
        LEFT JOIN users u ON m.user_id = u.id
        ORDER BY m.created_at DESC
    ''')
    messages = cursor.fetchall()

    # 转换为字典列表并处理时间
    messages_list = []
    for message in messages:
        msg_dict = dict(message)
        # 处理时间显示
        try:
            # 解析时间字符串
            utc_time = datetime.strptime(msg_dict['created_at'], '%Y-%m-%d %H:%M:%S')
            # 转换为本地时间
            local_tz = pytz.timezone('Asia/Shanghai')
            local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
            # 格式化时间
            msg_dict['created_at'] = local_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"时间转换错误: {e}")
            # 如果转换失败，保留原始时间
            pass
        messages_list.append(msg_dict)

    # 获取当前用户信息
    current_user = None
    if 'user_id' in session:
        cursor = db.execute('SELECT * FROM users WHERE id = ?', [session['user_id']])
        current_user = cursor.fetchone()

    return minify_html(render_template_string(INDEX_HTML, messages=messages_list, current_user=current_user))


# 发送消息
@app.route(rule='/send', methods=['POST'])
def send_message():
    db = get_db()

    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('index'))

    message = request.form['message']

    if not message or message[0] == ' ' or message[-1] == ' ' or message[0] == '\n' or message[-1] == '\n':
        flash('消息内容不能为空，也不能在首尾有空格或换行', 'error')
        return redirect(url_for('index'))

    mess = mgc(message)
    if mess:
        flash('你输入了什么！！', 'error')
        return redirect(url_for('index'))

    cursor = db.execute(
        "SELECT username FROM users WHERE id = ?",
        [session['user_id']]
    )
    resultyjd = cursor.fetchone()
    usernameyjd = resultyjd['username']

    # 如果用户名为空或None，拒绝发送消息
    if  '封禁用户' in usernameyjd:
        session.clear()  # 清除会话
        flash('您的账号已被封禁，无法发送消息', 'danger')
        return redirect(url_for('login'))

    db = get_db()
    db.execute('INSERT INTO messages (user_id, content) VALUES (?, ?)',
               [session['user_id'], message])
    db.commit()

    # 有10%的概率清理过期消息
    if random.random() < 0.1:
        clean_expired_messages()
        print("已清理过期消息")  # 可选：在控制台输出清理信息

    flash('消息发送成功', 'success')
    return redirect(url_for('index'))


# 用户注册
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    # return redirect(url_for('index'))
    if not username or not password:
        flash('用户名和密码不能为空', 'error')
        return redirect(url_for('index'))

    db = get_db()

    # 检查用户名是否已存在
    cursor = db.execute('SELECT * FROM users WHERE username = ?', [username])
    # if cursor.fetchone():
    #     flash('用户名已存在', 'error')
    #     return redirect(url_for('index'))
    #
    # if username.lower() == 'longint':
    #     flash('盗号是吧？', 'error')
    #     return redirect(url_for('index'))
    #
    # if username.lower() == 'lwt':
    #     flash('盗号是吧？', 'error')
    #     return redirect(url_for('index'))
    # if username.lower() == 'ae8633':
    #     flash('盗号是吧？', 'error')
    #     return redirect(url_for('index'))
    # 密码加密
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    # 插入新用户
    db.execute('INSERT INTO users (username, password) VALUES (?, ?)',
               [username, hashed_password])
    db.commit()

    flash('注册成功，请登录', 'success')
    return redirect(url_for('index'))


# 用户登录
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        flash('用户名和密码不能为空', 'error')
        return redirect(url_for('index'))

    db = get_db()

    # 密码加密
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    # 查询用户
    cursor = db.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                        [username, hashed_password])
    user = cursor.fetchone()

    if user:
        session['user_id'] = user['id']
        flash('登录成功', 'success')
    else:
        flash('用户名或密码错误', 'error')

    return redirect(url_for('index'))


# 用户退出
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('已退出登录', 'success')
    return redirect(url_for('index'))


# 修改密码
@app.route('/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('index'))

    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if not current_password or not new_password or not confirm_password:
        flash('所有字段都必须填写', 'error')
        return redirect(url_for('index'))

    if new_password != confirm_password:
        flash('新密码和确认密码不匹配', 'error')
        return redirect(url_for('index'))

    db = get_db()

    # 验证当前密码
    hashed_current_password = hashlib.md5(current_password.encode()).hexdigest()
    cursor = db.execute('SELECT * FROM users WHERE id = ? AND password = ?',
                        [session['user_id'], hashed_current_password])
    user = cursor.fetchone()

    if not user:
        flash('当前密码不正确', 'error')
        return redirect(url_for('index'))

    # 更新密码
    hashed_new_password = hashlib.md5(new_password.encode()).hexdigest()
    db.execute('UPDATE users SET password = ? WHERE id = ?',
               [hashed_new_password, session['user_id']])
    db.commit()

    flash('密码修改成功', 'success')
    return redirect(url_for('index'))


cl_rules = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>畅连消息墙公约</title>
    <script type="text/javascript" src="{{{{{{{static_add}}}}}}}}js/love.js"></script>
    <script type="text/javascript" src="{{{{{{{static_add}}}}}}}}js/snow.js"></script>
    
    <style>
        :root {
            --primary-color: #3B82F6;
            --secondary-color: #6366F1;
            --accent-color: #EF4444;
            --text-color: #1F2937;
            --light-bg: #E0E0E0;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--light-bg);
            margin: 0;
            padding: 0;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 40px 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .header:hover {
            border-left-color: var(--secondary-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }

        .header p {
            margin: 10px 0 0;
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .section {
            background-color: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border-left: 4px solid var(--primary-color);
            transition: all 0.3s ease;
        }

        .section:hover {
            border-left-color: var(--secondary-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        .section-title {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            font-size: 1.3rem;
            font-weight: 600;
            color: var(--secondary-color);
        }

        .section-title::before {
            content: "✓";
            margin-right: 10px;
            color: var(--primary-color);
            font-size: 1.5rem;
        }

        .section-content p {
            margin: 10px 0;
        }

        .highlight {
            background-color: #FFF3E0;
            padding: 10px 15px;
            border-radius: 6px;
            border-left: 4px solid var(--accent-color);
            font-weight: 500;
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            font-size: 0.9rem;
            color: #6B7280;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }

            .container {
                padding: 15px;
            }
        }
        .eleju {
           margin-top: 10px;    /* 上边距 */
           margin-bottom:10px
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/"><img src="{{{{{{{{{{{{{{{{{%{{{{{{{{{[image_back_png]}}}}}}}}}%}}}}}}}}}}}}}}}}}" height="39" width="37" class="eleju"></a>
        <div class="header">
            <h1>畅连™消息墙公约</h1>
            <p>共建和谐社区，共享优质交流</p>
        </div>

        <div class="section">
            <div class="section-title">序言</div>
            <div class="section-content">
                <p>畅连作为一个开放活跃的网站，需要大家共同维护秩序。</p>
                <p>为维护网站风气，净化网站环境，使得所有人都能享受到畅连网站的良好氛围，畅连站管理者制定本规则。</p>
                <p>本规则从整体层面对用户的行为作出了规范。</p>
            </div>
        </div>

        <div class="section">
            <div class="section-title">基本规则</div>
            <div class="section-content">
                <p>作为畅连网站的成员，用户在畅连网站内的活动应该遵守如下几条基本规则：</p>
                <p>1. 遵守法律与相关法规。一切违反法律法规的行为在畅连网站都是绝对禁止的。</p>
                <p>2. 尊重他人，待人友善。友善的氛围是畅连网站维持活力与亲和力的重要因素。请在参与网站的各个项目中保持开放与包容的态度，避免人身攻击等不友善的行为。</p>
            </div>
        </div>

        <div class="section">
            <div class="section-title">处罚类型</div>
            <div class="section-content">
                <p>违反网站规则的用户，视违规类型和情节严重性，可能受到如下类型的处罚：</p>
                <p>违反网站规则的用户在受到处罚后屡教不改，持续实施违反网站规则的行为时，可对其处以封禁账户的处罚。对多次违反网站规则，情节严重的用户，可永久封禁账户。</p>
            </div>
        </div>

        <div class="section">
            <div class="section-title">处罚细则</div>
            <div class="section-content">
                <div class="highlight">
                    用户在网站内有如下违反畅连网站规范，扰乱网站秩序的行为，视情节严重性，可处以警告、禁言或封禁账户的处罚：
                </div>
                <p>1. 在网站内提交（或发表）较多无意义内容;</p>
                <p>2. 使用夺人眼球、哗众取宠、或不知所谓的内容；</p>
                <p>3. 出现对其他用户的辱骂、歧视、人身攻击等不友善内容；</p>
                <p>4. 出现泄露其他用户个人隐私的内容；</p>
                <p>5. 出现未经许可的广告；</p>
                <p>6. 出现未经许可宣传非公开的比赛、团队、私题、题单、主题等；</p>
                <p>7. 出现轻微涉政、自残、低俗擦边球等敏感话题；</p>
                <p>8. 出现违反法律法规或严重违反社会公德的内容；</p>
                <p>9. 出现政治梗或反动言论，或讨论、影射国家机关或相关人物；</p>

                <div class="highlight mt-4">
                    用户有如下扰乱畅连用户管理秩序的行为，可处以封禁账户的处罚：
                </div>
                <p>1. 注册大量账户；</p>
                <p>2. 在受到规则处罚后，注册多个账户绕过处罚措施，继续违反规则；</p>
                <p>3. 盗用他人账户造成恶劣影响，或多次盗用他人账户；</p>
                <p>4. 其他严重损害畅连消息墙网站和其他用户的利益，造成恶劣影响的行为。</p>
            </div>
        </div>

        <div class="section">
            <div class="section-title">规则解释与执行</div>
            <div class="section-content">
                <p>1. 规则解释权归畅连消息墙网站;</p>
                <p>2. 规则由发布之日起执行。</p>
            </div>
        </div>

        <div class="footer">
            <p>© 2025 畅连消息墙.余俊东 版权所有</p>
            <p>未经许可，不得复制、传播或用于商业用途</p>
        </div>
    </div>
</body>
</html>
'''

# 社区公约
@app.route('/rules')
def rules():
    send = {
        '{{{{{{{{{{{{{{{{{%{{{{{{{{{[image_back_png]}}}}}}}}}%}}}}}}}}}}}}}}}}}': static_add + "image/back.png",
        '{{{{{{{static_add}}}}}}}}' : static_add
    }
    return minify_html(JD_tihuan(cl_rules, send))


# 初始化数据库命令
@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('数据库已初始化')


if __name__ == '__main__':
    # 确保数据库存在
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True, host='0.0.0.0', port=IP_PORT)