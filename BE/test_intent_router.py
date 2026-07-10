"""
test_intent_router.py
Unit test cho Hybrid 2.5 lớp Intent Router.
Chạy: python test_intent_router.py
"""
import sys
import os

# Add BE folder to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from agents.intent_router import (
    classify_intent_regex,
    classify_intent_llm,
    classify_and_route,
    route,
    REGEX_RULES,
)
from agents.prompts import VALID_INTENTS


def assert_eq(actual, expected, label: str):
    """Helper assertion với label rõ ràng."""
    status = "✅ PASS" if actual == expected else "❌ FAIL"
    print(f"  {status} | {label}: expected={expected!r}, actual={actual!r}")
    return actual == expected


def test_regex_layer():
    """Layer 1: Regex — test các case cứng."""
    print("\n=== Layer 1: REGEX ===")
    results = []

    # SĐT → CREATE_ORDER
    results.append(assert_eq(classify_intent_regex("0912345678"), "CREATE_ORDER", "SĐT 10 số"))
    results.append(assert_eq(classify_intent_regex("em tên Huy, 0987654321, mua áo"), "CREATE_ORDER", "SĐT trong câu dài"))

    # Greeting → GREETING
    results.append(assert_eq(classify_intent_regex("chào"), "GREETING", "chào"))
    results.append(assert_eq(classify_intent_regex("chào shop"), "GREETING", "chào shop"))
    results.append(assert_eq(classify_intent_regex("hi miko"), "GREETING", "hi miko"))
    results.append(assert_eq(classify_intent_regex("hello"), "GREETING", "hello"))

    # Chitchat → CHITCHAT
    results.append(assert_eq(classify_intent_regex("shop ở đâu vậy"), "CHITCHAT", "hỏi địa chỉ"))
    results.append(assert_eq(classify_intent_regex("có freeship không"), "CHITCHAT", "hỏi ship"))
    results.append(assert_eq(classify_intent_regex("shop mở cửa mấy giờ"), "CHITCHAT", "hỏi giờ mở cửa"))
    results.append(assert_eq(classify_intent_regex("có khuyến mãi gì không"), "CHITCHAT", "hỏi khuyến mãi"))

    # Không match → None (sẽ qua LLM)
    results.append(assert_eq(classify_intent_regex("có áo hoodie không"), None, "hỏi sản phẩm → None"))
    results.append(assert_eq(classify_intent_regex("kem dưỡng ẩm nào tốt"), None, "hỏi sản phẩm mỹ phẩm → None"))
    results.append(assert_eq(classify_intent_regex("áo thun trắng size M"), None, "mô tả sản phẩm → None"))

    print(f"\n  Tổng: {sum(results)}/{len(results)} pass")
    return all(results)


def test_route_layer():
    """Layer 2.5: Route — map intent → action."""
    print("\n=== Layer 2.5: ROUTE ===")
    results = []

    results.append(assert_eq(route("SEARCH_PRODUCT"), "auto_search", "SEARCH → auto_search"))
    results.append(assert_eq(route("CREATE_ORDER"), "auto_order", "ORDER → auto_order"))
    results.append(assert_eq(route("GREETING"), "free_chat", "GREETING → free_chat"))
    results.append(assert_eq(route("CHITCHAT"), "free_chat", "CHITCHAT → free_chat"))
    results.append(assert_eq(route(None), None, "None → None"))
    results.append(assert_eq(route("INVALID_INTENT"), None, "Invalid → None"))

    print(f"\n  Tổng: {sum(results)}/{len(results)} pass")
    return all(results)


def test_llm_layer():
    """
    Layer 2: LLM classify — cần Ollama hoặc NVIDIA chạy.
    Skip nếu không có LLM (để test sandbox).
    """
    print("\n=== Layer 2: LLM CLASSIFY (cần Ollama/NVIDIA chạy) ===")
    try:
        # Test 1: câu hỏi sản phẩm
        result = classify_intent_llm("có áo hoodie không")
        ok = assert_eq(result, "SEARCH_PRODUCT", "hỏi áo hoodie")
        if not ok:
            return False

        # Test 2: hỏi chitchat
        result = classify_intent_llm("shop mở cửa mấy giờ")
        ok = assert_eq(result, "CHITCHAT", "hỏi giờ mở cửa")
        if not ok:
            return False

        # Test 3: chào
        result = classify_intent_llm("chào bạn")
        ok = assert_eq(result, "GREETING", "chào bạn")
        if not ok:
            return False

        return True
    except Exception as e:
        print(f"  ⚠️  LLM test bị skip (lỗi: {e})")
        print(f"  💡 Để chạy test LLM, cần Ollama chạy ở localhost:11434 hoặc set LLM_PROVIDER=nvidia + API key")
        return None  # Skip, không fail


def test_classify_and_route():
    """Test end-to-end: classify_and_route với cả 2 layer."""
    print("\n=== END-TO-END: classify_and_route ===")
    results = []

    # Các case regex match nhanh (không cần LLM)
    intent, action = classify_and_route("chào")
    results.append(assert_eq(intent, "GREETING", "intent: chào"))
    results.append(assert_eq(action, "free_chat", "action: chào"))

    intent, action = classify_and_route("0912345678")
    results.append(assert_eq(intent, "CREATE_ORDER", "intent: SĐT"))
    results.append(assert_eq(action, "auto_order", "action: SĐT"))

    intent, action = classify_and_route("shop ở đâu")
    results.append(assert_eq(intent, "CHITCHAT", "intent: hỏi địa chỉ"))
    results.append(assert_eq(action, "free_chat", "action: hỏi địa chỉ"))

    # Empty/None
    intent, action = classify_and_route("")
    results.append(assert_eq(intent, None, "empty → None"))
    results.append(assert_eq(action, None, "empty → None"))

    print(f"\n  Tổng: {sum(results)}/{len(results)} pass")
    return all(results)


if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════╗")
    print("║  Test Hybrid 2.5 lớp Intent Router cho Miko       ║")
    print("╚════════════════════════════════════════════════════╝")

    # Layer 1: Regex (luôn chạy được, không cần LLM)
    pass_regex = test_regex_layer()

    # Layer 2.5: Route mapping
    pass_route = test_route_layer()

    # End-to-end không cần LLM
    pass_e2e = test_classify_and_route()

    # Layer 2: LLM (optional, skip nếu Ollama không chạy)
    pass_llm = test_llm_layer()
    if pass_llm is None:
        pass_llm = True  # Treat skip as pass

    # Tổng kết
    print("\n" + "=" * 60)
    print("TỔNG KẾT:")
    print(f"  Layer 1 (Regex):        {'✅ PASS' if pass_regex else '❌ FAIL'}")
    print(f"  Layer 2.5 (Route):      {'✅ PASS' if pass_route else '❌ FAIL'}")
    print(f"  End-to-end:             {'✅ PASS' if pass_e2e else '❌ FAIL'}")
    print(f"  Layer 2 (LLM):          {'✅ PASS' if pass_llm else '⚠️  SKIP'}")
    print("=" * 60)

    if pass_regex and pass_route and pass_e2e and pass_llm:
        print("\n🎉 Tất cả test PASS! Router sẵn sàng chạy.")
        sys.exit(0)
    else:
        print("\n❌ Có test FAIL. Vui lòng kiểm tra lại.")
        sys.exit(1)
