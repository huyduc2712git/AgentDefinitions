import subprocess
import sys
import os
import time

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    be_dir = os.path.join(base_dir, "BE")
    fe_dir = os.path.join(base_dir, "FE")

    # Windows node command is npm.cmd
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"

    # Detect local IP for dynamic multi-device demo link
    import socket
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    print("=== Khởi động Miko AI Agent (BE + FE) ===")
    
    # Run BE via Python module to ensure clean process control
    print("-> Đang khởi động Backend (port 8000 on 0.0.0.0)...")
    be_args = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    be_process = subprocess.Popen(
        be_args,
        cwd=be_dir,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    # Wait a bit for BE to initialize ports
    time.sleep(1.5)

    # Run FE via npm run dev
    print("-> Đang khởi động Frontend (Vite with --host)...")
    fe_args = [npm_cmd, "run", "dev", "--", "--host"]
    fe_process = subprocess.Popen(
        fe_args,
        cwd=fe_dir,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    print("\n[OK] Cả 2 server đang chạy đồng thời trên Local Network!")
    print(f"- Local PC: http://localhost:5173")
    print(f"- Demo thiết bị khác (Mobile/Tablet): http://{local_ip}:5173")
    print(f"- Backend API: http://{local_ip}:8000")
    print("👉 Nhấn Ctrl+C để TẮT cả 2 server cùng lúc.\n")

    try:
        while True:
            time.sleep(1)
            # Check if any process exited unexpectedly
            if be_process.poll() is not None:
                print("Backend terminated.")
                break
            if fe_process.poll() is not None:
                print("Frontend terminated.")
                break
    except KeyboardInterrupt:
        print("\n[Hệ thống] Đang dừng cả 2 server...")
    finally:
        # Graceful terminate
        try:
            be_process.terminate()
        except:
            pass
        try:
            fe_process.terminate()
        except:
            pass
        
        # Give processes a moment to shutdown, otherwise force kill
        time.sleep(0.5)
        try:
            be_process.kill()
        except:
            pass
        try:
            fe_process.kill()
        except:
            pass
        print("=== Đã tắt toàn bộ server ===")

if __name__ == "__main__":
    main()
