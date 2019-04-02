import psutil
import json

process_info_list = []
all_process = psutil.process_iter()

for p in all_process:
    try:
        process_info_list.append({
            "id": p.pid,
            "name": p.name(),  # 进程名
            # "exe": p.exe(),
            # "cwd": p.cwd(),
            "status": p.status(),
            "create_time": p.create_time(),
            # "uids": p.uids(),
            # "gids": p.gids(),
            # "cpu_times": p.cpu_times(),
            # "cpu_affinity": p.cpu_affinity(),
            "memory_percent": p.memory_percent(),
            # "memory_info": p.memory_info(),
            # "io_counters": p.io_counters(),
            # "connectios": p.connectios(),
            "num_threads": p.num_threads(),
        })
    except:
        pass
    # print(p.send_signal())  # 发送信号
    # print(p.kill())  # 杀死程序
    # print(p.terminate())
print(json.dumps(process_info_list, sort_keys=True, indent=4, separators=(",", ":")))
