import sys
import os
import re

# Add BE folder to path so imports work
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from agents.miko import run_miko_turn, detect_product_number
from session import store


def test_detect_product_number():
    print("\n--- Testing detect_product_number ---")
    test_cases = [
        ("chốt 1", 1),
        ("lấy cái số 2", 2),
        ("mẫu 3 nha shop", 3),
        ("chốt sản phẩm 4", 4),
        ("lấy số 5", 5),
        ("5", 5),
        ("chốt cái 2", 2),
        ("cho tôi cái thứ 3 đi", 3),
        ("lấy 3 cái", None),
        ("chào shop", None),
        ("áo hoodie màu đỏ", None),
    ]

    all_pass = True
    for text, expected in test_cases:
        actual = detect_product_number(text)
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        print(f"  {status} | Text: '{text}' -> Expected: {expected}, Actual: {actual}")
        if actual != expected:
            all_pass = False
    return all_pass


def test_product_selection_flow():
    print("\n--- Testing product selection flow ---")
    session_id = "test_selection_session_123"
    store.clear_session(session_id)

    # 1. Mock a product list search result
    mock_products = [
        {"name": "Áo thun đen basic", "price": 150000, "sku": "AT-DEN-B", "color": "Đen", "size": "M"},
        {"name": "Áo thun trắng basic", "price": 150000, "sku": "AT-TRG-B", "color": "Trắng", "size": "L"},
        {"name": "Áo khoác gió bomber", "price": 280000, "sku": "AK-BOMBER", "color": "Xanh rêu", "size": "XL"},
    ]
    store.save_last_products(session_id, mock_products)

    # 2. Simulate user selection: "lấy cái số 2"
    user_msg = "mình lấy cái số 2 nha"
    print(f"User: {user_msg}")
    
    reply, products = run_miko_turn(user_msg, session_id)
    print(f"Miko Reply:\n{reply}\n")

    # The reply should contain "trắng" or refer to the correct product because we resolved product #2
    # Let's inspect history to see if history was updated correctly
    history = store.get_history(session_id)
    print("History:")
    for msg in history:
        print(f"  [{msg['role'].upper()}]: {msg['content']}")

    # 2b. Simulate user asking: "chi tiết hơn về sản phẩm đi ạ" (generic query)
    generic_msg = "chi tiết hơn về sản phẩm đi ạ"
    print(f"\nUser: {generic_msg}")
    reply, products = run_miko_turn(generic_msg, session_id)
    print(f"Miko Reply:\n{reply}\n")
    
    # Check if it still details Áo thun trắng basic
    generic_ok = "trắng" in reply.lower() or "basic" in reply.lower() or "at-trg-b" in reply.lower()
    if not generic_ok:
        print("❌ FAILED: Redirect of generic query to selected product failed.")
        return False

    # 3. Simulate ordering with name, SĐT and address
    order_msg = "chốt nha, mình tên Huy, SĐT 0912345678, địa chỉ 123 Nguyễn Trãi, Quận 1"
    print(f"\nUser: {order_msg}")
    
    reply, products = run_miko_turn(order_msg, session_id)
    print(f"Miko Reply:\n{reply}\n")

    # Check if order was successfully mocked/created for the correct product ("Áo thun trắng basic")
    success = "Áo thun trắng basic" in reply or "AT-TRG-B" in reply
    if success:
        print("✅ SUCCESS: Order created for correct product!")
    else:
        print("❌ FAILED: Correct product was not used for ordering.")
    return success


if __name__ == "__main__":
    detect_ok = test_detect_product_number()
    flow_ok = test_product_selection_flow()
    
    if detect_ok and flow_ok:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED.")
        sys.exit(1)
