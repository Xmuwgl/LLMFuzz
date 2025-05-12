'''
作为接口启动 MultiFuzz
'''
import os
import time
from pathlib import Path
import subprocess

def run_fuzzer(target) -> dict:
    """启动 MultiFuzz 并返回执行结果"""

    # 确保工作目录存在
    workdir_path = os.path.join(target, 'workdir')
    workdir = os.environ.get("WORKDIR", workdir_path)
    Path(workdir).mkdir(parents=True, exist_ok=True)

    # 设置环境变量
    env = os.environ.copy()
    env["RESUME"] = "true"
    env["RUN_FOR"] = "24h"
    env["WORKDIR"] = workdir

    # 构建命令
    cmd = ["cargo", "run", "--release", "--", target]

    print(f"Starting MultiFuzz with command: {' '.join(cmd)}")
    print(f"Environment variables:")
    print(f"  RESUME: {env['RESUME']}")
    print(f"  RUN_FOR: {env['RUN_FOR']}")
    print(f"  WORKDIR: {env['WORKDIR']}")

    # 启动进程
    try:
        start_time = time.time()
        
        # 启动命令并捕获输出
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 实时输出日志
        log_file = os.path.join(workdir, "multifuzz.log")
        with open(log_file, "w") as f:
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
                f.write(line)
        
        # 等待进程完成
        process.wait()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 检查返回码
        if process.returncode != 0:
            print(f"Failed to run MultiFuzz, Caused by: {process.returncode}")
        
        # 收集基本结果
        results = {
            "return_code": process.returncode,
            "duration_seconds": duration,
            "start_time": time.ctime(start_time),
            "end_time": time.ctime(end_time),
            "workdir": workdir,
            "log_file": log_file
        }
        
        # 尝试收集更多结果
        try:
            # 收集找到的崩溃数量
            crashes_dir = os.path.join(workdir, "crashes")
            if os.path.exists(crashes_dir):
                crashes = len([f for f in os.listdir(crashes_dir) if os.path.isfile(os.path.join(crashes_dir, f))])
                results["crashes"] = crashes
            
            # 收集找到的超时数量
            timeouts_dir = os.path.join(workdir, "timeouts")
            if os.path.exists(timeouts_dir):
                timeouts = len([f for f in os.listdir(timeouts_dir) if os.path.isfile(os.path.join(timeouts_dir, f))])
                results["timeouts"] = timeouts
            
            # 收集执行的总输入数量
            queue_dir = os.path.join(workdir, "queue")
            if os.path.exists(queue_dir):
                total_inputs = len([f for f in os.listdir(queue_dir) if os.path.isfile(os.path.join(queue_dir, f))])
                results["total_inputs"] = total_inputs
                
        except Exception as e:
            print(f"收集详细结果时出错: {e}")
        
        return results
        
    except Exception as e:
        print(f"启动MultiFuzz时出错: {e}")
        return {
            "error": str(e),
            "return_code": -1
        }
    

def stop_fuzzer():
    '''停止 MultiFuzz, 用于覆盖率长期无变化时'''
    pass
