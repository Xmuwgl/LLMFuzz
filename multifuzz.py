import os
import time
from pathlib import Path
import subprocess

def run_fuzzer(target) -> dict:
    workdir_path = target + '/workdir'
    workdir = os.environ.get("WORKDIR", workdir_path)
    Path(workdir).mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["RESUME"] = "true"
    env["RUN_FOR"] = "24h"
    env["WORKDIR"] = workdir
  
    cmd = ["cargo", "run", "--release", "--", target]

    print(f"Starting MultiFuzz with command: {' '.join(cmd)}")
    print(f"Environment variables:")
    print(f"  RESUME: {env['RESUME']}")
    print(f"  RUN_FOR: {env['RUN_FOR']}")
    print(f"  WORKDIR: {env['WORKDIR']}")

      try:
        start_time = time.time()
        
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        log_file = os.path.join(workdir, "multifuzz.log")
        with open(log_file, "w") as f:
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
                f.write(line)
        
        process.wait()
        
        end_time = time.time()
        duration = end_time - start_time
        
        if process.returncode != 0:
            print(f"Failed to run MultiFuzz, Caused by: {process.returncode}")
        
        results = {
            "return_code": process.returncode,
            "duration_seconds": duration,
            "start_time": time.ctime(start_time),
            "end_time": time.ctime(end_time),
            "workdir": workdir,
            "log_file": log_file
        }
        
        try:
            crashes_dir = os.path.join(workdir, "crashes")
            if os.path.exists(crashes_dir):
                crashes = len([f for f in os.listdir(crashes_dir) if os.path.isfile(os.path.join(crashes_dir, f))])
                results["crashes"] = crashes
            
            timeouts_dir = os.path.join(workdir, "timeouts")
            if os.path.exists(timeouts_dir):
                timeouts = len([f for f in os.listdir(timeouts_dir) if os.path.isfile(os.path.join(timeouts_dir, f))])
                results["timeouts"] = timeouts
            
            queue_dir = os.path.join(workdir, "queue")
            if os.path.exists(queue_dir):
                total_inputs = len([f for f in os.listdir(queue_dir) if os.path.isfile(os.path.join(queue_dir, f))])
                results["total_inputs"] = total_inputs
                
        except Exception as e:
            print(f"ERROR: {e}")
        
        return results
        
    except Exception as e:
        print(f"ERROR: {e}")
        return {
            "error": str(e),
            "return_code": -1
        }
