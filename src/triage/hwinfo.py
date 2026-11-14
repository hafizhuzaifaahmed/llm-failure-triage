"""Host readings for feasibility and session checks (Windows host)."""
from __future__ import annotations

import ctypes
import csv
import io
import subprocess


def ram() -> dict:
    class MEMSTAT(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = MEMSTAT()
    m.dwLength = ctypes.sizeof(MEMSTAT)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return {"total_gib": m.ullTotalPhys / 2**30, "free_gib": m.ullAvailPhys / 2**30}


# Windows: run helper programs without flashing a console window
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def ollama_working_set_gib() -> float:
    out = subprocess.run(["tasklist", "/fi", "imagename eq ollama.exe", "/fo", "csv", "/nh"],
                         capture_output=True, text=True, creationflags=NO_WINDOW).stdout
    total_kb = 0
    for row in csv.reader(io.StringIO(out)):
        if len(row) >= 5 and row[0].lower() == "ollama.exe":
            total_kb += int(row[4].replace("K", "").replace(",", "").replace(".", "").strip() or 0)
    return total_kb / 2**20


def gpu() -> dict:
    q = "name,memory.total,memory.used,memory.free,temperature.gpu,driver_version,power.draw"
    out = subprocess.run(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, creationflags=NO_WINDOW).stdout.strip().split(",")
    if len(out) < 7:
        return {}
    keys = ["name", "mem_total_mib", "mem_used_mib", "mem_free_mib", "temp_c", "driver", "power_w"]
    vals = [x.strip() for x in out]
    d = dict(zip(keys, vals))
    for k in ("mem_total_mib", "mem_used_mib", "mem_free_mib", "temp_c", "power_w"):
        try:
            d[k] = float(d[k])
        except ValueError:
            pass
    smi = subprocess.run(["nvidia-smi"], capture_output=True, text=True, creationflags=NO_WINDOW).stdout
    import re
    m = re.search(r"CUDA Version:\s*([\d.]+)", smi)
    d["cuda"] = m.group(1) if m else None
    return d
