from flask import Flask, render_template_string, request, redirect, url_for, session, flash, g
import sqlite3
import os
from datetime import datetime, timedelta
import pytz
import hashlib
import random

# 前置函数
def JD_tihuan(Str, th):
    res = Str
    for i in th:
        res = res.replace(i, th[i])
    return res

def minify_html(html):
    import re
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    html = re.sub(r'\n\s+', '\n', html)
    html = re.sub(r'\s+', ' ', html)
    return html

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'yoursecretkeyhere')

# 数据库配置：使用绝对路径，避免工作目录问题
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'messagewall.db')

MESSAGE_EXPIRE_DAYS = 5
static_add = os.environ.get('STATIC_ADD', '/static/')

# 敏感词配置
mgc_par = ['鸡巴', '几把', '极霸'
                          "阴茎", "精子", "77", 'nm', '亖',
           '精液', '子宫', '卵巢', '答辩', '大便']

class mgc:
    def __init__(self, str):
        self.str = str
        return

    def __bool__(self):
        t_str = self.str.lower()
        t_str = t_str.replace(" ", "").replace("\n", "").replace("\r\n", "").replace("\r", "").replace("_", "")
        for i in mgc_par:
            if i in t_str:
                return True
        return False

# HTML模板（保持原样，这里省略中间HTML以节省篇幅，实际使用时请保留你原有的完整HTML）
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
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--light-bg); line-height: 1.6; color: var(--text-color); }
        .container { max-width: 800px; margin: 20px auto; padding: 25px; }
        .header { background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); color: white; padding: 40px 20px; border-radius: 12px; margin-bottom: 30px; text-align: center; }
        h1 { color: white; text-align: center; }
        .message-card { background-color: white; border-radius: 10px; padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); border-left: 4px solid var(--primary-color); max-height: 500px; overflow: auto; }
        .message-header { display: flex; justify-content: space-between; margin-bottom: 10px; font-weight: 600; }
        .username { color: var(--primary-color); }
        .timestamp { color: #6B7280; font-size: 0.9rem; }
        .content { margin-top: 10px; word-wrap: break-word; white-space: pre-wrap; overflow-wrap: break-word; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 500; }
        input[type="text"], input[type="password"], textarea { width: 100%; padding: 12px; border: 1px solid #D1D5DB; border-radius: 8px; font-family: inherit; font-size: 1rem; }
        textarea { height: 120px; resize: vertical; }
        .btn, .red-button { background-color: var(--primary-color); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; font-size: 1rem; display: inline-flex; align-items: center; justify-content: center; min-width: 120px; min-height: 42px; padding: 0 16px; text-decoration: none; }
        .red-button { background-color: var(--accent-color); margin-top: 20px; width: 100%; }
        .auth-container { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 30px; }
        .auth-form { flex: 1; background-color: #81C5F9; padding: 25px; border-radius: 10px; }
        .tabs { display: flex; margin-bottom: 25px; border-bottom: 1px solid #E5E7EB; }
        .tab { padding: 12px 24px; cursor: pointer; background-color: #E5E7EB; border-radius: 8px 8px 0 0; margin-right: 5px; }
        .tab.active { background-color: var(--primary-color); color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .flash { padding: 15px; margin-bottom: 20px; border-radius: 8px; }
        .flash.success { background-color: rgba(16, 185, 129, 0.1); color: var(--success-color); }
        .flash.error { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-color); }
        .form-btn-wrapper { display: flex; justify-content: flex-end; margin-top: 15px; }
        .footer { text-align: center; margin-top: 40px; font-size: 0.9rem; color: #6B7280; }
    </style>
    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</head>
<body>
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
            <h2.5>欢迎, {{ current_user['username'] }}!</h2.5>
            <div class="form-group">
                <form method="post" action="{{ url_for('send_message') }}" id="messageForm">
                    <textarea id="message" name="message" placeholder="请发表留言，按 Ctrl+Enter 发送" required></textarea>
                    <div class="form-btn-wrapper"><button type="submit" class="btn">发送</button></div>
                </form>
            </div>
        </div>
        <div class="tabs">
            <div class="tab active" onclick="showTab('messages')">留言列表</div>
            <div class="tab" onclick="showTab('change-password')">修改密码</div>
        </div>
        <div id="messages" class="tab-content active">
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
            <form method="post" action="{{ url_for('change_password') }}">
                <div class="form-group"><label>当前密码:</label><input type="password" name="current_password" required></div>
                <div class="form-group"><label>新密码:</label><input type="password" name="new_password" required></div>
                <div class="form-group"><label>确认新密码:</label><input type="password" name="confirm_password" required></div>
                <div class="form-btn-wrapper"><button type="submit" class="btn">修改密码</button></div>
            </form>
        </div>
        <a href="{{ url_for('logout') }}" class="red-button">退出登录</a>
        <a href="{{ url_for('rules') }}" class="red-button">畅连消息墙公约</a>
        {% else %}
        <div class="header"><h1>留言墙</h1></div>
        <div class="auth-container">
            <div class="auth-form">
                <h2>登录</h2>
                <form method="post" action="{{ url_for('login') }}">
                    <div class="form-group"><label>用户名:</label><input type="text" name="username" required></div>
                    <div class="form-group"><label>密码:</label><input type="password" name="password" required></div>
                    <div class="form-btn-wrapper"><button type="submit" class="btn">登录</button></div>
                </form>
            </div>
            <div class="auth-form">
                <h2>注册</h2>
                <form method="post" action="{{ url_for('register') }}">
                    <div class="form-group"><label>用户名:</label><input type="text" name="username" required></div>
                    <div class="form-group"><label>密码:</label><input type="password" name="password" required></div>
                    <div class="form-btn-wrapper"><button type="submit" class="btn">注册</button></div>
                </form>
            </div>
        </div>
        <a href="{{ url_for('rules') }}" class="red-button">畅连消息墙公约</a>
        {% endif %}
        <div class="footer"><p>© 2025 畅连消息墙.余俊东 版权所有</p></div>
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

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# 初始化数据库
def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cursor = db.execute('SELECT id FROM users WHERE username = ?', ['admin'])
        if cursor.fetchone() is None:
            admin_password = hashlib.md5(
                os.environ.get('ADMIN_PASSWORD', 'admin123456').encode()
            ).hexdigest()
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', ['admin', admin_password])
        db.commit()

# 清理过期消息
def clean_expired_messages():
    db = get_db()
    expire_time = datetime.utcnow() - timedelta(days=MESSAGE_EXPIRE_DAYS)
    db.execute('DELETE FROM messages WHERE created_at < ?', [expire_time])
    db.commit()

@app.route('/')
def index():
    db = get_db()
    cursor = db.execute('''
        SELECT m.id, m.content, m.created_at, u.username 
        FROM messages m LEFT JOIN users u ON m.user_id = u.id
        ORDER BY m.created_at DESC
    ''')
    messages = cursor.fetchall()
    messages_list = []
    for message in messages:
        msg_dict = dict(message)
        try:
            utc_time = datetime.strptime(msg_dict['created_at'], '%Y-%m-%d %H:%M:%S')
            local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Shanghai'))
            msg_dict['created_at'] = local_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            pass
        messages_list.append(msg_dict)

    current_user = None
    if 'user_id' in session:
        cursor = db.execute('SELECT * FROM users WHERE id = ?', [session['user_id']])
        current_user = cursor.fetchone()
    return minify_html(render_template_string(INDEX_HTML, messages=messages_list, current_user=current_user))

@app.route('/send', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('index'))
    message = request.form['message']
    if not message or message[0] == ' ' or message[-1] == ' ':
        flash('消息内容不能为空，也不能在首尾有空格', 'error')
        return redirect(url_for('index'))
    if mgc(message):
        flash('你输入了什么！！', 'error')
        return redirect(url_for('index'))

    db = get_db()
    cursor = db.execute("SELECT username FROM users WHERE id = ?", [session['user_id']])
    resultyjd = cursor.fetchone()
    if '封禁用户' in resultyjd['username']:
        session.clear()
        flash('您的账号已被封禁', 'danger')
        return redirect(url_for('login'))

    db.execute('INSERT INTO messages (user_id, content) VALUES (?, ?)', [session['user_id'], message])
    db.commit()
    if random.random() < 0.1:
        clean_expired_messages()
    flash('消息发送成功', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    if not username or not password:
        flash('用户名和密码不能为空', 'error')
        return redirect(url_for('index'))
    db = get_db()
    cursor = db.execute('SELECT * FROM users WHERE username = ?', [username])
    if cursor.fetchone():
        flash('用户名已存在', 'error')
        return redirect(url_for('index'))
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    db.execute('INSERT INTO users (username, password) VALUES (?, ?)', [username, hashed_password])
    db.commit()
    flash('注册成功，请登录', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    cursor = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', [username, hashed_password])
    user = cursor.fetchone()
    if user:
        session['user_id'] = user['id']
        flash('登录成功', 'success')
    else:
        flash('用户名或密码错误', 'error')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('已退出登录', 'success')
    return redirect(url_for('index'))

@app.route('/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('index'))
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    if new_password != confirm_password:
        flash('新密码和确认密码不匹配', 'error')
        return redirect(url_for('index'))
    db = get_db()
    hashed_current = hashlib.md5(current_password.encode()).hexdigest()
    cursor = db.execute('SELECT * FROM users WHERE id = ? AND password = ?', [session['user_id'], hashed_current])
    if not cursor.fetchone():
        flash('当前密码不正确', 'error')
        return redirect(url_for('index'))
    hashed_new = hashlib.md5(new_password.encode()).hexdigest()
    db.execute('UPDATE users SET password = ? WHERE id = ?', [hashed_new, session['user_id']])
    db.commit()
    flash('密码修改成功', 'success')
    return redirect(url_for('index'))

cl_rules = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>畅连消息墙公约</title></head>
<body><h1>畅连™消息墙公约</h1><p>共建和谐社区，共享优质交流</p><a href="/">返回首页</a></body>
</html>
'''

@app.route('/rules')
def rules():
    return minify_html(cl_rules)

with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7891))
    app.run(debug=False, host='0.0.0.0', port=port)
