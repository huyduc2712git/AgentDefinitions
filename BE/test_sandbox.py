import sys
import os

# Add BE folder to path so imports work
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from agents.miko import run_miko_turn
from session import store

if __name__ == "__main__":
    session_id = "simulation_session_999"
    store.clear_session(session_id)
    
    # Simulation steps
    conversation = [
        "hiện tại shop mình có sản phẩm gì",
        "cho mình xem áo thun với",
    ]
    
    for user_msg in conversation:
        print("="*60)
        print(f"User: {user_msg}")
        
        def mock_status(step, desc):
            print(f"  [Status] {step}: {desc}")

        final_reply, products = run_miko_turn(user_msg, session_id, on_status=mock_status)
        
        print(f"\nMiko Final Reply:\n{final_reply}\n")
