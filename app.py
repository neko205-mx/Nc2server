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
        # result = subprocess.run(command, shell=True, capture_output=True, text=True)
        # output = result.stdout if result.returncode == 0 else result.stderr
        return jsonify({'output': output})  # 确保返回的是 JSON
    except Exception as e:
        return jsonify({'error': f'执行命令时出错: {str(e)}'}), 500


if __name__ == '__main__':
    app.run()
