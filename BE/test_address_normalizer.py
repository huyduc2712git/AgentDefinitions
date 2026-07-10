"""
test_address_normalizer.py
Unit test cho công cụ chuẩn hóa địa chỉ.
Chạy: python test_address_normalizer.py
"""
import sys
import os

# Thêm thư mục BE vào path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from tools.address_normalizer import normalize_address

def test_normalization():
    test_cases = [
        ("199 DBP, Gia Định, TP.HCM", "199 Điện Biên Phủ, Quận Bình Thạnh, Thành phố Hồ Chí Minh"),
        ("199dbp, Gia Định, TP.HCM", "199 Điện Biên Phủ, Quận Bình Thạnh, Thành phố Hồ Chí Minh"),
        ("199 DPB, Phường 15, Gia Định, TP.HCM", "199 Điện Biên Phủ, Phường 2, Quận Bình Thạnh, Thành phố Hồ Chí Minh"),
        ("199 DPB, Phường Gia Định, Gia Định, TP.HCM", "199 Điện Biên Phủ, Phường 2, Quận Bình Thạnh, Thành phố Hồ Chí Minh"),
        ("12 HBT, Q.1", "12 Hai Bà Trưng, Quận 1, Thành phố Hồ Chí Minh"),
        ("Đường CMT8, P15, Q.10, HCM", "Đường Cách Mạng Tháng Tám, Phường 15, Quận 10, Thành phố Hồ Chí Minh"),
        ("35 VVK, Q.BT, TPHCM", "35 Võ Văn Kiệt, Quận Bình Thạnh, Thành phố Hồ Chí Minh"),
        ("10 LTT, P. Bến Nghé, Q.1", "10 Lý Tự Trọng, Phường Bến Nghé, Quận 1, Thành phố Hồ Chí Minh"),
        ("Đường 3/2, Q.10, TP.HCM", "Đường Ba Tháng Hai, Quận 10, Thành phố Hồ Chí Minh"),
        ("Số 15 NTMK, P. 6, Q. 3", "Số 15 Nguyễn Thị Minh Khai, Phường 6, Quận 3, Thành phố Hồ Chí Minh"),
        ("199 DBP, P. Đa Kao, TP.HCM", "199 Điện Biên Phủ, Phường Đa Kao, Quận 1, Thành phố Hồ Chí Minh"),
        ("12 HBT, Q. Bình Thạnh", "12 Hai Bà Trưng, Quận Bình Thạnh, Thành phố Hồ Chí Minh"),
        ("199 DBP, TP.HCM", "199 Điện Biên Phủ, Thành phố Hồ Chí Minh"),
    ]

    failed = 0
    for inp, expected in test_cases:
        actual = normalize_address(inp)
        if actual == expected:
            print(f"[PASS] '{inp}' -> '{actual}'")
        else:
            print(f"[FAIL] '{inp}'\n  Expected: '{expected}'\n  Got:      '{actual}'")
            failed += 1

    if failed == 0:
        print("\n🎉 Toàn bộ test cases đã PASS!")
    else:
        print(f"\n❌ Có {failed} test cases bị FAIL.")

    print("\n--- Bắt đầu test thực tế địa lý bằng CSDL Offline ---")
    from tools.address_normalizer import verify_address_realism
    realism_cases = [
        "15 Điện Biên Phủ, Phường Đa Kao, Quận 1, Thành phố Hồ Chí Minh", # Hợp lệ (Phường Đa Kao thuộc Quận 1)
        "199 Điện Biên Phủ, Phường Đa Kao, Quận Bình Thạnh, Thành phố Hồ Chí Minh" # Lỗi (Phường Đa Kao không thuộc Quận Bình Thạnh)
    ]
    for addr in realism_cases:
        is_valid, reason = verify_address_realism(addr)
        print(f"Địa chỉ: {addr}\n  Hợp lệ: {is_valid}\n  Lý do: {reason}\n")

if __name__ == "__main__":
    test_normalization()
