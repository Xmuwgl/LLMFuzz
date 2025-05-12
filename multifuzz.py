'''
作为接口启动 MultiFuzz
'''

import subprocess
import signal
import os

# 全局变量，存储当前运行的 fuzzer 进程
current_fuzzer_process = None

def run_fuzzer(target, asynchronous=False):
    """
    启动 Fuzzer 进程
    参数:
        target: 目标固件路径
        asynchronous: 是否异步运行
    返回:
        进程对象(异步模式)或执行结果(同步模式)
    """
    global current_fuzzer_process
    
    # 设置环境变量
    env = os.environ.copy()
    env["RESUME"] = "true"
    env["RUN_FOR"] = "24h"
    env["WORKDIR"] = f"{target}/workdir"
    
    # 构建命令
    cmd = ["cargo", "run", "--release", "--", target]
    
    print(f"Starting fuzzer with command: {' '.join(cmd)}")
    
    try:
        # 启动进程
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 存储当前进程
        current_fuzzer_process = process
        
        if asynchronous:
            # 异步模式直接返回进程
            return process
        else:
            # 同步模式等待进程完成
            output, _ = process.communicate()
            return {
                "returncode": process.returncode,
                "output": output
            }
            
    except Exception as e:
        print(f"Failed to start fuzzer: {e}")
        return None

def stop_fuzzer(process=None):
    """
    停止当前正在运行的 fuzzer 进程
    参数:
        process: 可选的进程对象，如果未提供，则使用全局存储的进程
    """
    global current_fuzzer_process
    
    # 如果未提供进程，使用全局存储的进程
    if process is None:
        process = current_fuzzer_process
    
    if process is None:
        print("No running fuzzer process to stop")
        return False
    
    try:
        print("Stopping fuzzer process...")
        
        # 首先尝试发送 SIGINT (Ctrl+C)，给进程优雅退出的机会
        process.send_signal(signal.SIGINT)
        
        # 等待进程退出
        try:
            process.wait(timeout=30)  # 等待 30 秒
            print(f"Fuzzer process stopped with return code {process.returncode}")
            current_fuzzer_process = None
            return True
        except subprocess.TimeoutExpired:
            # 如果 30 秒后仍未退出，发送 SIGKILL 强制终止
            print("Fuzzer did not stop gracefully, sending SIGKILL")
            process.kill()
            process.wait()  # 确保进程已终止
            print(f"Fuzzer process killed with return code {process.returncode}")
            current_fuzzer_process = None
            return True
            
    except Exception as e:
        print(f"Error stopping fuzzer process: {e}")
        return False
