import sys
import llm_agent
import daemon
import multifuzz

# python main.py ../MultiFuzz/firmware/P2IM/CNC
if __name__ == '__main__':
    target = sys.argv[1]
    while True:
        if daemon.run_generator():
            print(f"generating new seeds...\n")
        else:
            daemon.realign()
        multifuzz.run_fuzzer(target)
        feedback = daemon.collect_feedback()
        llm_agent.fix_prompt(feedback)
        llm_agent.update_generator()
