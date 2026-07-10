"""
agents/miko.py
Miko — nhân viên tư vấn bán hàng UPOS.

Hàm chính: run_miko_turn(user_message, session_id)
  - Nếu ENABLE_INTENT_ROUTER=true: gọi Intent Router trước
    → auto_search / auto_order / free_chat / fallback
  - Load history từ session store
  - Gọi LLM → nếu ra JSON action, chạy tool-loop
  - Lưu history, trả về reply cuối cùng cho FE
"""
import re
import config
from models.ollama import call_ollama_api
from models.minimax import call_minimax_api
from tools.tool_executor import parse_intent, execute
from tools.address_normalizer import normalize_address
from session import store
from agents.prompts import MIKO_SYSTEM_PROMPT
from agents.intent_router import classify_and_route


def _call_llm(messages: list, stream: bool = False, temperature: float = 0.7) -> str:
    """Gọi LLM dựa trên cấu hình LLM_PROVIDER."""
    if config.LLM_PROVIDER == "nvidia":
        return call_minimax_api(messages=messages, stream=stream, temperature=temperature)
    else:
        return call_ollama_api(messages=messages, stream=stream, temperature=temperature)


def _build_response_from_products(products: list, tool_result: str, user_message: str) -> str:
    """
    Khi auto_search tìm được sản phẩm, gọi LLM 1 lần để viết câu trả lời tự nhiên.
    Fallback: trả thẳng kết quả thô nếu LLM fail.
    """
    if not products:
        return "Dạ hiện tại shop chưa có sản phẩm phù hợp với yêu cầu của anh/chị ạ. Anh/chị muốn tìm mặt hàng khác không ạ? 🥺"

    # Gọi LLM viết câu trả lời tự nhiên từ tool_result
    messages = [
        {"role": "system", "content": MIKO_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": '{"action": "search_product", "params": {"query": "..."}}'},
        {"role": "user", "content": f"[Kết quả từ hệ thống]\n{tool_result}\n\nHãy dùng thông tin trên để trả lời khách ngắn gọn, dễ thương."},
    ]
    try:
        raw = _call_llm(messages, stream=False, temperature=0.7)
        # Loại bỏ nhãn chế độ nếu LLM lỡ viết
        clean = re.sub(r'\(?(?:Chế độ|Định dạng|Mode)\s*\d+\)?\s*:?', '', raw, flags=re.IGNORECASE)
        return clean.strip()
    except Exception as e:
        print(f"[miko] LLM build response fail: {e}")
        return f"Dạ Miko tìm thấy {len(products)} sản phẩm phù hợp cho anh/chị nè! 🌸"


def _build_response_from_order(tool_result: str) -> str:
    """
    Khi auto_order được gọi, tạo response từ tool_result.
    Luôn nhúng tool_result nguyên vẹn để đảm bảo mã đơn hàng được hiển thị.
    """
    if "THÀNH CÔNG" in tool_result:
        return (
            f"Dạ đơn hàng đã được tạo thành công rồi ạ! 🎉\n\n"
            f"{tool_result}\n\n"
            f"Anh/chị kiểm tra lại thông tin giúp Miko nha! Nếu cần hỗ trợ gì thêm em luôn sẵn sàng ạ 🌸"
        )
    else:
        return f"Dạ Miko chưa thể tạo đơn ngay ạ.\n{tool_result}\nAnh/chị bổ sung thêm thông tin để Miko hoàn tất nha! 🥺"


def _post_process_address_in_reply(reply: str) -> str:
    """
    Tìm dòng địa chỉ trong form xác nhận đơn hàng mà LLM vừa tạo ra
    và chuẩn hóa nó bằng normalize_address().
    Áp dụng cho cả định dạng markdown **in đậm** lẫn plaintext.
    Ví dụ dòng khớp:
      - **Địa chỉ giao hàng**: 199 DBP, Gia định, hcm
      - Địa chỉ giao hàng: 199 DBP, Gia định, hcm
    """
    # Tìm dòng chứa "Địa chỉ giao hàng:" hoặc "Địa chỉ:" với các bullet point phổ biến (-, •, *)
    pattern = re.compile(
        r"(- \*\*Địa chỉ giao hàng\*\*:?\s*|[-•\*]\s*Địa chỉ giao hàng:?\s*)(.*?)(?=\n|$)",
        re.IGNORECASE
    )
    def _replace_addr(m: re.Match) -> str:
        prefix = m.group(1)
        raw_addr = m.group(2).strip()
        # Bỏ qua nếu là placeholder hoặc rỗng
        if not raw_addr or "(Chưa có)" in raw_addr or "chưa có" in raw_addr.lower():
            return m.group(0)
        normalized = normalize_address(raw_addr)
        if normalized != raw_addr:
            print(f"[miko] Normalized address in reply: '{raw_addr}' → '{normalized}'")
        return prefix + normalized

    return pattern.sub(_replace_addr, reply)


def is_generic_query(query: str) -> bool:
    """
    Kiểm tra xem câu truy vấn có mang tính chất chung chung, đại từ thay thế không.
    Ví dụ: '', 'sản phẩm', 'nó', 'này', 'đó', 'chi tiết', 'thông tin',...
    """
    q = query.strip().lower()
    # Loại bỏ dấu câu và khoảng trắng thừa
    q = re.sub(r'[^\w\s]', '', q)
    
    # Loại bỏ các từ đệm, từ chỉ xưng hô hoặc hạt từ cuối câu tiếng Việt
    filler_words = {
        "đi", "ạ", "nha", "nhé", "giùm", "hộ", "với", "cho", "mình", "tôi", 
        "em", "shop", "ad", "admin", "bạn", "nhỉ", "dạ", "vâng", "thêm", "chút", "nào",
        "xin", "hãy", "cơ", "thế", "vậy", "nhỉ", "hơn", "hon"
    }
    words = [w for w in q.split() if w not in filler_words]
    
    # Tạo lại chuỗi sạch sau khi lọc từ đệm
    clean_q = " ".join(words)
    
    # Danh sách các cụm từ chung chung thường gặp
    generic_phrases = {
        "", "sản phẩm", "san pham", "sản phẩm này", "san pham nay", 
        "sản phẩm đó", "san pham do", "sản phẩm ấy", "san pham ay",
        "nó", "no", "đó", "do", "ấy", "ay", "này", "nay",
        "chi tiết", "chi tiet", "thông tin", "thong tin",
        "chi tiết hơn", "chi tiet hon", "thông tin chi tiết", "thong tin chi tiet",
        "chi tiết sản phẩm", "chi tiet san pham", "chi tiết về sản phẩm", "chi tiet ve san pham",
        "thông tin sản phẩm", "thong tin san pham", "mẫu này", "mau nay",
        "mẫu đó", "mau do", "mẫu ấy", "mau ay", "cái này", "cai nay",
        "cái đó", "cai do", "cái ấy", "cai ay"
    }
    if clean_q in generic_phrases:
        return True
        
    single_generics = {"sản", "phẩm", "san", "pham", "này", "nay", "đó", "do", "ấy", "ay", "nó", "no", "chi", "tiết", "tiet", "thông", "tin", "thong", "hơn", "hon", "về", "ve"}
    if words and all(w in single_generics for w in words):
        return True
    return False


def detect_product_number(message: str) -> int | None:
    """
    Nhận diện số thứ tự từ 1-5 mà khách hàng chọn.
    Các mẫu tin nhắn được nhận diện: 'chốt 1', 'lấy cái số 2', 'mẫu 3', 'số 4', hoặc chỉ nhắn đúng chữ số '2'.
    Cũng hỗ trợ các dạng tự nhiên khác như: 'cái thứ 3', 'dòng 2', 'mục 1', 'cho cái 3',...
    """
    message_lower = message.lower().strip()
    
    # 1. Tìm các cụm từ chỉ lựa chọn rõ ràng: mẫu/số/cái/thứ/mục/dòng/sản phẩm [1-5]
    # Ví dụ: "cái thứ 3", "thứ 2", "số 1", "mẫu 3", "mục 4", "dòng 5", "cái 2"
    selection_pattern = r"\b(?:mẫu|số|cái|thứ|mục|dòng|sản\s*phẩm)\s*(?:cái|mẫu|số|sản\s*phẩm|thứ)?\s*([1-5])\b"
    match = re.search(selection_pattern, message_lower)
    if match:
        return int(match.group(1))
        
    # 2. Tìm các cụm từ hành động: chốt/lấy/chọn/mua/order [1-5]
    # Nhưng phải loại trừ trường hợp số đó biểu thị số lượng (vd: "lấy 3 cái", "mua 2 hộp")
    action_pattern = r"\b(?:chốt|lấy|chọn|mua|order)\s+([1-5])\b"
    match = re.search(action_pattern, message_lower)
    if match:
        num = int(match.group(1))
        # Loại trừ nếu ngay sau chữ số là đơn vị đo số lượng (vd: cái, chiếc, bộ, hộp, gói, ly, chai, lọ, sp, sản phẩm)
        quantity_classifier_pattern = rf"\b{num}\s*(?:cái|chiếc|bộ|hộp|gói|ly|chai|lọ|món|phần|đôi|cặp|sp|sản\s*phẩm)\b"
        if not re.search(quantity_classifier_pattern, message_lower):
            return num
    
    # 3. Hoặc nếu tin nhắn chỉ chứa đúng một chữ số từ 1 đến 5
    if re.match(r"^[1-5]$", message_lower):
        return int(message_lower)
        
    return None


def detect_product_by_text(message: str, last_products: list) -> dict | None:
    """
    Tìm sản phẩm khớp từ tên trong danh sách sản phẩm gần nhất.
    """
    if not last_products:
        return None
    msg_lower = message.lower()
    
    # Sắp xếp tên dài lên trước để tránh so trùng substring ngắn
    sorted_prods = sorted(last_products, key=lambda x: len(x.get("product_name") or x.get("name") or ""), reverse=True)
    
    for prod in sorted_prods:
        p_name = prod.get("product_name") or prod.get("name")
        if not p_name:
            continue
        p_name_lower = p_name.lower().strip()
        # Chuẩn hóa khoảng trắng để so khớp
        clean_p_name = re.sub(r"\s+", " ", p_name_lower)
        clean_msg = re.sub(r"\s+", " ", msg_lower)
        if clean_p_name in clean_msg:
            return prod
    return None


def run_miko_turn(user_message: str, session_id: str, stream: bool = False, on_status=None) -> tuple[str, list]:
    """
    Xử lý một lượt hội thoại của Miko.

    Flow:
      1. Nếu ENABLE_INTENT_ROUTER=true: gọi classify_and_route()
         - auto_search → gọi search_product, build response, return
         - auto_order  → gọi create_order, build response, return
         - free_chat   → tiếp tục Miko loop
         - None (fail) → fallback Miko loop
      2. Miko loop: gọi LLM, parse intent JSON, chạy tool, lưu history
    """
    found_products: list = []
    intent: str | None = None
    action_type: str | None = None

    # ── Step 0: Intent Routing (Hybrid 2.5 lớp) ──
    if config.ENABLE_INTENT_ROUTER:
        try:
            history = store.get_history(session_id)
            intent, action_type = classify_and_route(user_message, history=history)
            print(f"[miko] Router → intent={intent}, action={action_type}")

            # Nếu là tin nhắn chọn số hoặc câu hỏi chung chung về sản phẩm đang chọn, bypass auto_search để chạy Miko loop
            is_selection = detect_product_number(user_message) is not None
            is_generic_followup = is_generic_query(user_message) and bool(store.get_current_product(session_id))
            
            if action_type == "auto_search" and (is_selection or is_generic_followup):
                print(f"[miko] Tin nhắn chọn số hoặc câu hỏi chung chung về sản phẩm hiện tại, bypass auto_search.")
                action_type = None

            if action_type == "auto_search":
                # Xóa sản phẩm đang chọn vì đây là tìm kiếm mới
                store.save_current_product(session_id, {})
                if on_status:
                    on_status("searching", "Đang kết nối API và kiểm tra kho hàng...")
                # Tự động gọi search_product với raw user message làm query
                tool_result, current_products = execute({
                    "action": "search_product",
                    "params": {"query": user_message},
                })
                if current_products:
                    found_products = current_products
                if on_status:
                    on_status("answering", "Miko đang đối chiếu sản phẩm và soạn câu trả lời...")
                final_reply = _build_response_from_products(found_products, tool_result, user_message)
                # Lưu history
                store.append_turn(session_id, user_message, final_reply)
                # Lưu danh sách sản phẩm gần nhất
                if found_products:
                    store.save_last_products(session_id, found_products)
                return final_reply, found_products

            elif action_type == "auto_order":
                if on_status:
                    on_status("creating_order", "Đang chốt đơn hàng...")
                # Gọi create_order với raw user message — service sẽ extract info
                # Lưu ý: create_order hiện cần params riêng, ta tạm fallback về Miko loop
                # để LLM tự extract name/phone/address từ message (giống logic cũ).
                # Phase sau sẽ thêm regex extract tự động.
                # → Fall through to Miko loop bên dưới
                pass

            elif action_type == "free_chat":
                # GREETING / CHITCHAT → Miko loop bình thường
                pass

            # Nếu router fail (intent=None) → fall through to Miko loop

        except Exception as e:
            print(f"[miko] Router lỗi: {e}, fallback về Miko loop cũ")

    # ── Original Miko loop (with number selection mapping) ──
    history = store.get_history(session_id)
    messages = [{"role": "system", "content": MIKO_SYSTEM_PROMPT}]
    messages.extend(history)

    # Nhận diện lựa chọn sản phẩm của khách và lưu vào cache sản phẩm đang chọn
    num = detect_product_number(user_message)
    last_products = store.get_last_products(session_id)
    if num:
        if last_products and 1 <= num <= len(last_products):
            prod = last_products[num - 1]
            store.save_current_product(session_id, prod)
    else:
        # Thử nhận diện bằng tên sản phẩm trực tiếp từ message
        prod_by_text = detect_product_by_text(user_message, last_products)
        if prod_by_text:
            store.save_current_product(session_id, prod_by_text)

    # Lấy sản phẩm đang chọn từ cache (có thể được lưu từ lượt trước)
    current_prod = store.get_current_product(session_id)

    user_msg_for_llm = user_message
    if current_prod:
        prod_name = current_prod.get("name") or current_prod.get("product_name", "sản phẩm")
        prod_price = current_prod.get("price") or current_prod.get("sell_price", "")
        prod_sku = current_prod.get("sku", "")
        prod_color = current_prod.get("color") or current_prod.get("colors", "")
        prod_size = current_prod.get("size") or current_prod.get("sizes", "")
        
        system_injection = (
            f"\n\n[Hệ thống: Khách hàng đang chọn sản phẩm: \"{prod_name}\".\n"
            f"- Tên sản phẩm: {prod_name}\n"
            f"- Giá: {prod_price}\n"
            f"- SKU: {prod_sku}\n"
            f"- Màu sắc: {prod_color}\n"
            f"- Kích thước: {prod_size}\n"
        )
        # ── Kiểm tra trạng thái chốt đơn ──
        # Python tự đọc lịch sử để biết đã thu thập được thông tin nào
        is_checking_out = (
            intent == "CREATE_ORDER" or
            action_type == "auto_order" or
            any("địa chỉ" in h.get("content", "").lower() or
                "sđt" in h.get("content", "").lower() or
                "số điện thoại" in h.get("content", "").lower() or
                "họ tên" in h.get("content", "").lower() or
                "họ và tên" in h.get("content", "").lower()
                for h in history[-6:])
        )

        # Phát hiện khách vừa xác nhận (ok, đúng, đúng rồi, chuẩn, vâng, yes, ...)
        CONFIRM_WORDS = {
            "ok", "oke", "okay", "okey", "oki", "đúng", "đúng rồi", "chuẩn",
            "chuẩn rồi", "xác nhận", "chốt", "vâng", "dạ", "yes", "yep",
            "đồng ý", "đúng vậy", "đúng đó", "ừ", "ừ nhỉ", "uh", "uh huh",
        }
        msg_stripped = user_message.strip().lower().rstrip("!.,")
        is_customer_confirming = msg_stripped in CONFIRM_WORDS

        if is_checking_out:
            # Trích xuất thông tin đã thu thập từ lịch sử hội thoại
            collected_name = ""
            collected_phone = ""
            collected_address = ""

            # Quét toàn bộ history để tìm tên/sđt/địa chỉ (ưu tiên mới nhất)
            all_msgs = history + [{"role": "user", "content": user_message}]
            for h in reversed(all_msgs):
                content = h.get("content", "")
                # Tìm SĐT (10 số, bắt đầu 0[3-9])
                if not collected_phone:
                    m = re.search(r'\b0[3-9]\d{8}\b', content)
                    if m:
                        collected_phone = m.group(0)
                # Tìm địa chỉ từ nhãn "Địa chỉ giao hàng:" trong assistant reply
                if not collected_address and h.get("role") == "assistant":
                    m = re.search(
                        r'(?:\*\*)?Địa chỉ giao hàng(?:\*\*)?:?\s*(.+?)(?:\n|$)',
                        content, re.IGNORECASE
                    )
                    if m:
                        val = m.group(1).strip()
                        if val and "(chưa có)" not in val.lower():
                            collected_address = normalize_address(val)
                # Tìm tên từ nhãn "Họ và tên:" / "Họ tên:" trong assistant reply
                if not collected_name and h.get("role") == "assistant":
                    m = re.search(
                        r'(?:\*\*)?Họ (?:và )?tên(?:\*\*)?:?\s*(.+?)(?:\n|$)',
                        content, re.IGNORECASE
                    )
                    if m:
                        val = m.group(1).strip()
                        if val and "(chưa có)" not in val.lower():
                            collected_name = val

            if not collected_name:
                # Tên thường là chuỗi chữ cái tiếng Việt không chứa số, dài 2-5 từ
                # Tìm ngược từ tin nhắn mới nhất
                NAME_PATTERN = r'([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴÝỶỸ][a-zàáâãèéêìíòóôõùúăđĩũơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵýỷỹ]+(?:\s[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴÝỶỸ][a-zàáâãèéêìíòóôõùúăđĩũơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵýỷỹ]+){1,4})'
                for h in reversed(all_msgs):
                    if h.get("role") != "user":
                        continue
                    content = h.get("content", "")
                    
                    # Cách 1: Bắt theo prefix "tên (là)", "anh", "chị", "gọi là"
                    m1 = re.search(rf'(?i)\b(?:tên(?: là)?|gọi(?: là)?|anh|chị|em|mình(?: là)?)\s+{NAME_PATTERN}\b', content)
                    if m1:
                        collected_name = m1.group(1).strip()
                        break
                        
                    # Cách 2: Nếu tin nhắn rất ngắn (thường khách nhắn mỗi tên)
                    text_no_phone = re.sub(r'\b0[3-9]\d{8}\b', '', content).strip(".,! ")
                    if 1 <= len(text_no_phone.split()) <= 6:
                        m2 = re.match(rf'^{NAME_PATTERN}$', text_no_phone)
                        if m2:
                            collected_name = m2.group(1).strip()
                            break

            if not collected_address:
                # Tìm địa chỉ trong user messages (có chứa quận/phường/đường)
                for h in all_msgs:
                    if h.get("role") != "user":
                        continue
                    content = h.get("content", "")
                    if any(kw in content.lower() for kw in ["quận", "phường", "huyện", "đường", "tp", "hcm", "hà nội", "dbp", "đbp"]):
                        # Thử normalize toàn bộ đoạn text sau khi bỏ SĐT và tên
                        text = re.sub(r'\b0[3-9]\d{8}\b', '', content).strip()
                        if collected_name:
                            # Xóa tên đã thu thập khỏi text địa chỉ (cả chữ thường và HOA)
                            text = re.sub(re.escape(collected_name), '', text, flags=re.IGNORECASE)
                        # Xóa các từ khóa rác
                        text = re.sub(r'(?i)\b(tên(?: là)?|sđt|số điện thoại)\b', '', text).strip()
                        # Xóa các dấu phẩy thừa do xóa text
                        text = re.sub(r',\s*,', ',', text).strip(', ')
                        
                        candidate = normalize_address(text)
                        if len(candidate) >= 10:
                            collected_address = candidate
                            break

            has_all_3 = bool(collected_name and collected_phone and collected_address)

            if has_all_3 and is_customer_confirming:
                # ── CASE 3: Đủ 3 thông tin + khách vừa confirm → inject create_order JSON trực tiếp ──
                print(f"[miko] Auto-inject create_order: name={collected_name}, phone={collected_phone}, addr={collected_address}")
                import json as _json
                create_order_json = _json.dumps({
                    "action": "create_order",
                    "params": {
                        "customer_name": collected_name,
                        "phone": collected_phone,
                        "address": collected_address,
                        "product_name": prod_name,
                        "quantity": 1,
                    }
                }, ensure_ascii=False)
                # Bỏ qua LLM loop, set intent trực tiếp
                intent_obj = parse_intent(create_order_json)
                tool_result, _ = execute(intent_obj)
                final_reply = _build_response_from_order(tool_result)
                if "THÀNH CÔNG" in tool_result:
                    store.save_current_product(session_id, {})
                store.append_turn(session_id, user_message, final_reply)
                return final_reply, found_products

            elif has_all_3:
                # ── CASE 2: Đủ 3 thông tin, chờ khách confirm ──
                system_injection += (
                    f"\n\nKhách đang chốt đơn '{prod_name}'. Đã thu thập đủ thông tin:\n"
                    f"- Họ tên: {collected_name}\n"
                    f"- SĐT: {collected_phone}\n"
                    f"- Địa chỉ: {collected_address}\n\n"
                    f"Hãy hiển thị lại form xác nhận bên dưới, sau đó hỏi khách nhắn 'OK' để chốt đơn:\n\n"
                    f"Dạ, thông tin đơn hàng của mình hiện tại là:\n"
                    f"- **Họ và tên**: {collected_name}\n"
                    f"- **Số điện thoại**: {collected_phone}\n"
                    f"- **Địa chỉ giao hàng**: {collected_address}\n\n"
                    f"Anh/chị kiểm tra lại thông tin trên, nếu chính xác vui lòng nhắn OK để em chốt đơn nha!]"
                )
            else:
                # ── CASE 1: Còn thiếu thông tin → hỏi phần thiếu ──
                missing = []
                if not collected_name:
                    missing.append("Họ và tên")
                if not collected_phone:
                    missing.append("Số điện thoại")
                if not collected_address:
                    missing.append("Địa chỉ giao hàng")

                filled_summary = (
                    f"- Họ và tên: {collected_name or '(Chưa có)'}\n"
                    f"- Số điện thoại: {collected_phone or '(Chưa có)'}\n"
                    f"- Địa chỉ giao hàng: {collected_address or '(Chưa có)'}"
                )
                system_injection += (
                    f"\n\nKhách đang chốt đơn '{prod_name}'.\n"
                    f"Thông tin hiện có:\n{filled_summary}\n\n"
                    f"CÒN THIẾU: {', '.join(missing)}.\n"
                    f"Hãy hiển thị form tóm tắt trên (thay 'Chưa có' bằng giá trị thật nếu có), "
                    f"sau đó lịch sự hỏi khách cung cấp: {', '.join(missing)}.]\n"
                    f"Không hỏi về màu sắc hay kích thước — tên sản phẩm '{prod_name}' đã đủ."
                )
        else:
            system_injection += (
                f"Hãy dùng thông tin trên để tư vấn hoặc hướng dẫn khách hàng cách chốt đơn sản phẩm này.]"
            )
        user_msg_for_llm = f"{user_message}{system_injection}"

    messages.append({"role": "user", "content": user_msg_for_llm})

    final_reply = ""
    tool_calls = 0

    if on_status:
        on_status("thinking", "Miko đang suy nghĩ...")

    while tool_calls <= config.TOOL_LOOP_MAX:
        reply = _call_llm(messages, stream=stream)
        intent = parse_intent(reply)

        if intent is None:
            # Miko trả lời tự do — đây là reply cuối
            # Loại bỏ các nhãn chế độ (Chế độ 1, Định dạng 1, (Chế độ 1), v.v.)
            clean_reply = re.sub(r'\(?(?:Chế độ|Định dạng|Mode)\s*\d+\)?\s*:?', '', reply, flags=re.IGNORECASE)
            # Chuẩn hóa địa chỉ trong form xác nhận đơn hàng (nếu có)
            clean_reply = _post_process_address_in_reply(clean_reply)
            final_reply = clean_reply.strip()
            break

        # Miko ra JSON → chạy tool
        tool_calls += 1
        if on_status:
            on_status("searching", "Đang kết nối API và kiểm tra kho hàng...")

        # Chuyển hướng các câu truy vấn tìm kiếm sản phẩm chung chung sang sản phẩm đang chọn
        if intent.get("action") == "search_product":
            params = intent.get("params", {})
            query = params.get("query", "")
            if is_generic_query(query) and current_prod:
                prod_name = current_prod.get("name") or current_prod.get("product_name", "")
                if prod_name:
                    print(f"[miko] Redirecting generic search query '{query}' to current selected product: '{prod_name}'")
                    params["query"] = prod_name

        # Nếu action là create_order nhưng thiếu product_name, ta lấy từ current_prod cache
        if intent.get("action") == "create_order":
            params = intent.setdefault("params", {})
            if not params.get("product_name") and not params.get("product") and not params.get("name"):
                current_prod = store.get_current_product(session_id)
                if current_prod:
                    prod_name = current_prod.get("name") or current_prod.get("product_name")
                    if prod_name:
                        params["product_name"] = prod_name

        tool_result, current_products = execute(intent)
        if current_products:
            found_products = current_products
        print(f"[miko] Tool call #{tool_calls}: {intent.get('action')} → {tool_result[:100]}...")

        if on_status:
            on_status("answering", "Miko đang đối chiếu sản phẩm và soạn câu trả lời...")

        # Nếu là create_order: nhúng tool_result trực tiếp vào reply thay vì để LLM viết lại
        # Điều này đảm bảo mã đơn hàng luôn được hiển thị chính xác
        if intent and intent.get("action") == "create_order":
            final_reply = _build_response_from_order(tool_result)
            # Xóa current_product sau khi tạo đơn thành công
            if "THÀNH CÔNG" in tool_result:
                store.save_current_product(session_id, {})
            break

        # Inject tool result vào messages như một system message
        messages.append({"role": "assistant", "content": reply})
        messages.append({
            "role": "user",
            "content": f"[Kết quả từ hệ thống]\n{tool_result}\n\nHãy dùng thông tin trên để trả lời khách."
        })

        if tool_calls > config.TOOL_LOOP_MAX:
            final_reply = "Dạ hệ thống đang xử lý, anh/chị chờ mình một chút nhé ạ! 🙏"
            break

    # ── Lưu history (chỉ lưu lượt user gốc + reply cuối) ──
    store.append_turn(session_id, user_message, final_reply)

    # Lưu danh sách sản phẩm gần nhất
    if found_products:
        store.save_last_products(session_id, found_products)

    return final_reply, found_products


# ── Backward compat cho main.py cũ ──
def call_miko(user_message: str, history: list = None, stream: bool = False) -> str:
    """Legacy helper — dùng session_id tạm thời."""
    session_id = "legacy_main"
    if history:
        # Nạp history từ caller (không dùng session store)
        messages = [{"role": "system", "content": MIKO_SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return _call_llm(messages, stream=stream)
    reply, _ = run_miko_turn(user_message, session_id, stream=stream)
    return reply
