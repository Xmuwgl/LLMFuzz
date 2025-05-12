'''
用于启动整个 fuzz 过程:
1. 初始时向大模型设定角色 (fuzzer 要求的输入格式和入口地址在 generator 中固化)
2. 执行 generator, 产生 1000 个测试用例, 放到执行指定位置
3. 执行 fuzzer, 在此期间 LLM 不做任何动作
4. 接收 fuzzer 的反馈, 如调用图和覆盖率等, 辅助 generator 改进
5. 每个项目循环 5 * 24 小时. 注意保留上下文信息.
'''
import sys
import llm_agent
import daemon
import multifuzz
import threading

# python main.py ../MultiFuzz/firmware/P2IM/CNC
if __name__ == '__main__':
    target = sys.argv[1]
     # 启动覆盖率监视
    monitor_thread = threading.Thread(target=daemon.monitor_coverage, args=(target,))
    monitor_thread.start()
    
    while True:
        if daemon.run_generator():
            print(f"generating new seeds...\n")
        else:
            daemon.realign()
        # 异步模式启动 MultiFuzz
        fuzzer_process = multifuzz.run_fuzzer(target, asynchronous=True)

        # 一段时间后需要停止 fuzzer
        if multifuzz.stop_fuzzer(fuzzer_process):
            print("Fuzzer stopped successfully\n")
        else:
            print("Failed to stop fuzzer\n")

        feedback = daemon.collect_feedback()
        llm_agent.fix_prompt(feedback)
        llm_agent.update_generator()
