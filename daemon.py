'''
守护进程, 用于在 fuzzer 和 llm 之间进行数据交换
'''

import generator
import time
import os
import subprocess
import multifuzz
import shutil
import logging
from datetime import datetime

'''
执行 generator
'''
def run_generator():
    generator.main()


def realign():
    """ 当新生成器运行失败时执行回滚操作，恢复到 `generator_backup` 版本 """
    logger = logging.getLogger(__name__)
    workdir = os.environ.get("WORKDIR", "workdir")
    generator_path = os.path.join(workdir, "generator.py")
    backup_path = os.path.join(workdir, "generator_backup.py")
    
    try:
        # 检查是否存在备份文件
        if not os.path.exists(backup_path):
            logger.error("回滚失败：未找到生成器备份文件")
            return False
        
        # 创建时间戳目录保存失败的生成器
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        failed_dir = os.path.join(workdir, "failed_generators", timestamp)
        os.makedirs(failed_dir, exist_ok=True)
        
        # 保存失败的生成器版本
        if os.path.exists(generator_path):
            shutil.copy2(generator_path, os.path.join(failed_dir, "generator_failed.py"))
            logger.info(f"保存失败的生成器版本到: {failed_dir}")
        
        # 从备份恢复
        shutil.copy2(backup_path, generator_path)
        logger.info("已成功回滚到上次工作的生成器版本")
        
        # 记录回滚事件
        with open(os.path.join(workdir, "rollback_log.txt"), "a") as f:
            f.write(f"{timestamp}: 因生成器失败回滚\n")
        
        return True
        
    except Exception as e:
        logger.error(f"执行回滚操作时出错: {str(e)}")
        return False


last_coverage_change_time = time.time() # 初始化上一次覆盖率变化时间
last_coverage = 0 # 初始化上一次的覆盖率
def collect_feedback(target):
    '''收集 MultiFuzz 的反馈信息'''
    workdir = os.path.join(target, "workdir")  # 假设工作目录为 workdir
    coverage_file = os.path.join(workdir, "coverage.txt")  # 假设覆盖率信息保存在 coverage.txt 文件中
    if os.path.exists(coverage_file):
        with open(coverage_file, "r") as f:
            try:
                coverage = float(f.read().strip())
                return coverage
            except ValueError:
                return 0
    return 0


def monitor_coverage(target):
    global last_coverage_change_time, last_coverage
    while True:
        current_coverage = collect_feedback()
        if current_coverage != last_coverage:
            last_coverage = current_coverage
            last_coverage_change_time = time.time()
            print(f"Coverage changed to {current_coverage}%")
        else:
            elapsed_time = time.time() - last_coverage_change_time
            if elapsed_time >= 30 * 60:  # 30 分钟无变化
                print("Coverage has not changed for 30 minutes. Restarting fuzz...")
                # 重启 fuzz
                multifuzz.run_fuzzer(target)
                last_coverage_change_time = time.time()
        time.sleep(60)  # 每分钟检查一次覆盖率
