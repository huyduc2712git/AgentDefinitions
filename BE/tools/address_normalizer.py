"""
tools/address_normalizer.py
Công cụ chuẩn hóa địa chỉ giao hàng tiếng Việt sử dụng Vietnam Administrative Data (dvhcvn.json)
kết hợp với bộ quy tắc viết tắt tên đường.
Hỗ trợ địa chỉ thiếu cấp (2 cấp hành chính), tự động suy luận Quận/Tỉnh nếu duy nhất.
Tích hợp sơ đồ ánh xạ phường cũ/sáp nhập (Historical Wards) theo cải cách hành chính.
"""
import re
import json
import os

_db = None

def _load_db():
    global _db
    if _db is not None:
        return _db
    
    db_path = os.path.join(os.path.dirname(__file__), "dvhcvn.json")
    if not os.path.exists(db_path):
        _db = {"data": []}
        return _db
        
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            _db = json.load(f)
    except Exception as e:
        print(f"Error loading dvhcvn.json: {e}")
        _db = {"data": []}
    return _db


# Các từ viết tắt của tỉnh thành phổ biến để map sang tên chuẩn trong CSDL
PROVINCE_ALIASES = {
    "hcm": "Thành phố Hồ Chí Minh",
    "tp hcm": "Thành phố Hồ Chí Minh",
    "tphcm": "Thành phố Hồ Chí Minh",
    "sài gòn": "Thành phố Hồ Chí Minh",
    "sai gon": "Thành phố Hồ Chí Minh",
    "hồ chí minh": "Thành phố Hồ Chí Minh",
    "hn": "Thành phố Hà Nội",
    "hà nội": "Thành phố Hà Nội",
    "đn": "Thành phố Đà Nẵng",
    "đà nẵng": "Thành phố Đà Nẵng",
    "hp": "Thành phố Hải Phòng",
    "hải phòng": "Thành phố Hải Phòng",
}

# Các từ viết tắt quận huyện tại TP.HCM
DISTRICT_ALIASES_HCM = {
    "bt": "Quận Bình Thạnh",
    "bình thạnh": "Quận Bình Thạnh",
    "q bt": "Quận Bình Thạnh",
    "q.bt": "Quận Bình Thạnh",
    "gia định": "Quận Bình Thạnh",  # Ánh xạ lịch sử/dân gian về Quận Bình Thạnh
    "giađịnh": "Quận Bình Thạnh",
    "giá đình": "Quận Bình Thạnh",
    "tb": "Quận Tân Bình",
    "tân bình": "Quận Tân Bình",
    "q tb": "Quận Tân Bình",
    "q.tb": "Quận Tân Bình",
    "tp": "Quận Tân Phú",
    "tân phú": "Quận Tân Phú",
    "q tp": "Quận Tân Phú",
    "q.tp": "Quận Tân Phú",
    "gv": "Quận Gò Vấp",
    "gò vấp": "Quận Gò Vấp",
    "q gv": "Quận Gò Vấp",
    "q.gv": "Quận Gò Vấp",
    "pn": "Quận Phú Nhuận",
    "phú nhuận": "Quận Phú Nhuận",
    "q pn": "Quận Phú Nhuận",
    "q.pn": "Quận Phú Nhuận",
    "thủ đức": "Thành phố Thủ Đức",
    "tp thủ đức": "Thành phố Thủ Đức",
    "tp. thủ đức": "Thành phố Thủ Đức",
    "gia định": "Quận Bình Thạnh",  # Ánh xạ lịch sử/dân gian về Quận Bình Thạnh
}

# Ánh xạ phường cũ đã sáp nhập (theo dvhcvn.json hiện tại)
# Sử dụng key đã clean_name (loại bỏ tiền tố phường/xã/p. và chữ thường)
HISTORICAL_WARDS = {
    "quận bình thạnh": {
        "15": "Phường 2",  # Phường 15 đã được sáp nhập vào Phường 2 trong CSDL dvhcvn.json
        "gia định": "Phường 2",  # Phường Gia Định mới sáp nhập (chứa Phường 2 trong CSDL)
        "giađịnh": "Phường 2",
        "giá đình": "Phường 2",
    }
}


def clean_name(name: str) -> str:
    """
    Chuẩn hóa tên để đối chiếu so sánh.
    """
    if not name:
        return ""
    name = name.lower().strip()
    
    # Loại bỏ tiền tố hành chính chính thức
    prefixes = [
        "thành phố trung ương", "thành phố", "tỉnh",
        "quận", "huyện", "thị xã",
        "phường", "xã", "thị trấn"
    ]
    for prefix in prefixes:
        if name.startswith(prefix + " "):
            name = name[len(prefix) + 1:].strip()
            break
            
    # Bỏ dấu chấm và dấu gạch ngang
    name = name.replace(".", "").replace("-", " ")
    name = " ".join(name.split())
    
    # Loại bỏ tiền tố q, p viết tắt (ví dụ: q10 -> 10, p15 -> 15)
    if name.startswith("q ") or name.startswith("q."):
        name = name[2:].strip()
    elif name.startswith("q") and name[1:].isdigit():
        name = name[1:]
        
    if name.startswith("p ") or name.startswith("p."):
        name = name[2:].strip()
    elif name.startswith("p") and name[1:].isdigit():
        name = name[1:]
        
    return name


def is_ward_segment(seg: str) -> bool:
    """Kiểm tra xem segment có dấu hiệu rõ ràng là Phường/Xã/Thị trấn hay không."""
    s = seg.lower().strip()
    return s.startswith("p.") or s.startswith("p ") or s.startswith("phường") or s.startswith("xã") or s.startswith("thị trấn")


def is_district_segment(seg: str) -> bool:
    """Kiểm tra xem segment có dấu hiệu rõ ràng là Quận/Huyện/Thị xã hay không."""
    s = seg.lower().strip()
    return s.startswith("q.") or s.startswith("q ") or s.startswith("quận") or s.startswith("huyện") or s.startswith("thị xã") or s.startswith("thành phố")


def normalize_address(address: str) -> str:
    """
    Chuẩn hóa địa chỉ sử dụng CSDL hành chính chuẩn và quy tắc viết tắt.
    """
    if not address:
        return address

    # Tách số và chữ liền nhau để dễ chuẩn hóa (ví dụ: 199dbp -> 199 dbp, p15 -> p 15, q1 -> q 1)
    result = re.sub(r"(\d+)([a-zA-ZÀ-ỹ])", r"\1 \2", address)
    result = re.sub(r"([a-zA-ZÀ-ỹ])(\d+)", r"\1 \2", result)

    # ── BƯỚC 1: Thay thế các tên đường phố viết tắt bằng Regex ──
    streets = {
        r"dbp": "Điện Biên Phủ",
        r"đbp": "Điện Biên Phủ",
        r"dpb": "Điện Biên Phủ",
        r"đpb": "Điện Biên Phủ",
        r"hbt": "Hai Bà Trưng",
        r"cmt8": "Cách Mạng Tháng Tám",
        r"cmt\s*8": "Cách Mạng Tháng Tám",
        r"lhp": "Lê Hồng Phong",
        r"vvk": "Võ Văn Kiệt",
        r"vvt": "Võ Văn Tần",
        r"ntmk": "Nguyễn Thị Minh Khai",
        r"ltt": "Lý Tự Trọng",
        r"tdt": "Tôn Đức Thắng",
        r"nvl": "Nguyễn Văn Linh",
        r"nkkn": "Nam Kỳ Khởi Nghĩa",
        r"htp": "Huỳnh Tấn Phát",
        r"pxl": "Phan Xích Long",
        r"3/2": "Ba Tháng Hai",
        r"3-2": "Ba Tháng Hai",
        r"2/9": "Hai Tháng Chín",
        r"2-9": "Hai Tháng Chín",
        r"30/4": "Ba Mươi Tháng Tư",
        r"19/5": "Mười Chín Tháng Năm",
    }
    for pattern, replacement in streets.items():
        regex = re.compile(rf"(?<![a-zA-Z0-9À-ỹ]){pattern}(?![a-zA-Z0-9À-ỹ])", re.IGNORECASE)
        result = regex.sub(replacement, result)

    # ── BƯỚC 2: Đối chiếu CSDL hành chính ──
    db = _load_db()
    provinces_data = db.get("data", [])
    
    segments = [s.strip() for s in result.split(",")]
    
    matched_province = None
    matched_district = None
    matched_ward = None
    
    province_idx = -1
    district_idx = -1
    ward_idx = -1

    # 2A. Tìm Tỉnh/Thành phố
    for idx in reversed(range(len(segments))):
        seg_clean = clean_name(segments[idx])
        alias_match = PROVINCE_ALIASES.get(seg_clean)
        
        if alias_match:
            for p in provinces_data:
                if p["name"] == alias_match:
                    matched_province = p
                    province_idx = idx
                    break
            if matched_province:
                break
        
        for p in provinces_data:
            p_clean = clean_name(p["name"])
            if p_clean == seg_clean or p_clean.replace("thành phố ", "") == seg_clean:
                matched_province = p
                province_idx = idx
                break
        if matched_province:
            break

    # 2B. Tìm Quận/Huyện
    if matched_province:
        remaining_indices = [i for i in range(len(segments)) if i != province_idx]
        for idx in reversed(remaining_indices):
            if is_ward_segment(segments[idx]):
                continue
                
            seg_clean = clean_name(segments[idx])
            
            if matched_province["name"] == "Thành phố Hồ Chí Minh":
                alias_match = DISTRICT_ALIASES_HCM.get(seg_clean)
                if alias_match:
                    for d in matched_province.get("level2s", []):
                        if d["name"] == alias_match:
                            matched_district = d
                            district_idx = idx
                            break
                    if matched_district:
                        break
            
            for d in matched_province.get("level2s", []):
                d_clean = clean_name(d["name"])
                if d_clean == seg_clean or d_clean.replace("quận ", "").replace("huyện ", "") == seg_clean:
                    matched_district = d
                    district_idx = idx
                    break
            if matched_district:
                break
    else:
        # Tìm kiếm toàn quốc để tự động suy luận Tỉnh nếu Quận là duy nhất
        candidates = []
        for idx in reversed(range(len(segments))):
            if is_ward_segment(segments[idx]):
                continue
                
            seg_clean = clean_name(segments[idx])
            for p in provinces_data:
                if p["name"] == "Thành phố Hồ Chí Minh":
                    alias_match = DISTRICT_ALIASES_HCM.get(seg_clean)
                    if alias_match:
                        for d in p.get("level2s", []):
                            if d["name"] == alias_match:
                                candidates.append((p, d, idx))
                                break
                for d in p.get("level2s", []):
                    d_clean = clean_name(d["name"])
                    if d_clean == seg_clean or d_clean.replace("quận ", "").replace("huyện ", "") == seg_clean:
                        candidates.append((p, d, idx))
                        break
                        
        if candidates:
            unique_dists = {(c[0]["name"], c[1]["name"]): c for c in candidates}
            if len(unique_dists) == 1:
                p, d, idx = list(unique_dists.values())[0]
                matched_province = p
                matched_district = d
                district_idx = idx

    # 2C. Tìm Phường/Xã
    if matched_province:
        remaining_indices = [i for i in range(len(segments)) if i not in (province_idx, district_idx)]
        for idx in reversed(remaining_indices):
            if is_district_segment(segments[idx]):
                continue
                
            seg_clean = clean_name(segments[idx])
            
            if matched_district:
                # Kiểm tra danh sách phường cũ/sáp nhập trước
                d_name_clean = matched_district["name"].lower()
                hist_map = HISTORICAL_WARDS.get(d_name_clean, {})
                if seg_clean in hist_map:
                    active_w_name = hist_map[seg_clean]
                    for w in matched_district.get("level3s", []):
                        if w["name"] == active_w_name:
                            matched_ward = w
                            ward_idx = idx
                            break
                            
                if not matched_ward:
                    for w in matched_district.get("level3s", []):
                        w_clean = clean_name(w["name"])
                        if w_clean == seg_clean or w_clean.replace("phường ", "").replace("xã ", "") == seg_clean:
                            matched_ward = w
                            ward_idx = idx
                            break
                if matched_ward:
                    break
            else:
                candidates = []
                for d in matched_province.get("level2s", []):
                    # Check historical wards cho từng district
                    d_name_clean = d["name"].lower()
                    hist_map = HISTORICAL_WARDS.get(d_name_clean, {})
                    if seg_clean in hist_map:
                        active_w_name = hist_map[seg_clean]
                        for w in d.get("level3s", []):
                            if w["name"] == active_w_name:
                                candidates.append((d, w, idx))
                                break
                    # Tìm kiếm chuẩn thông thường
                    for w in d.get("level3s", []):
                        w_clean = clean_name(w["name"])
                        if w_clean == seg_clean or w_clean.replace("phường ", "").replace("xã ", "") == seg_clean:
                            candidates.append((d, w, idx))
                            
                if candidates:
                    unique_wards = {(c[0]["name"], c[1]["name"]): c for c in candidates}
                    if len(unique_wards) == 1:
                        d, w, idx = list(unique_wards.values())[0]
                        matched_district = d
                        matched_ward = w
                        ward_idx = idx
                        break

    # ── BƯỚC 3: Tái cấu trúc địa chỉ phân cấp chuẩn ──
    matched_indices = {province_idx, district_idx, ward_idx}
    street_segments = [segments[i] for i in range(len(segments)) if i not in matched_indices]
    
    output_segments = list(street_segments)
    
    if matched_ward:
        output_segments.append(matched_ward["name"])
    if matched_district:
        output_segments.append(matched_district["name"])
    if matched_province:
        output_segments.append(matched_province["name"])
        
    normalized_result = ", ".join(output_segments)

    # ── BƯỚC 4: Regex dự phòng cho các phần chưa chuẩn hóa ──
    if not matched_province:
        cities = {
            r"tp\.?\s*hcm": "TP. Hồ Chí Minh",
            r"tphcm": "TP. Hồ Chí Minh",
            r"hcm": "TP. Hồ Chí Minh",
            r"hn": "Hà Nội",
            r"dn": "Đà Nẵng",
            r"đn": "Đà Nẵng",
            r"hp": "Hải Phòng",
        }
        for pattern, replacement in cities.items():
            regex = re.compile(rf"(?<![a-zA-Z0-9À-ỹ]){pattern}(?![a-zA-Z0-9À-ỹ])", re.IGNORECASE)
            normalized_result = regex.sub(replacement, normalized_result)

    if not matched_district:
        normalized_result = re.compile(r"(?<![a-zA-Z0-9À-ỹ])[qQ]\.?\s*(\d+)(?![a-zA-Z0-9À-ỹ])").sub(r"Quận \1", normalized_result)
        districts_regex = {
            r"q\.?\s*bt": "Quận Bình Thạnh",
            r"q\.?\s*tb": "Quận Tân Bình",
            r"q\.?\s*tp": "Quận Tân Phú",
            r"q\.?\s*gv": "Quận Gò Vấp",
            r"q\.?\s*pn": "Quận Phú Nhuận",
        }
        for pattern, replacement in districts_regex.items():
            regex = re.compile(rf"(?<![a-zA-Z0-9À-ỹ]){pattern}(?![a-zA-Z0-9À-ỹ])", re.IGNORECASE)
            normalized_result = regex.sub(replacement, normalized_result)

    if not matched_ward:
        normalized_result = re.compile(r"(?<![a-zA-Z0-9À-ỹ])[pP]\.?\s*(\d+)(?![a-zA-Z0-9À-ỹ])").sub(r"Phường \1", normalized_result)

    normalized_result = re.compile(r"(?<![a-zA-Z0-9À-ỹ])[qQ]\.\s*(?=[A-ZÀ-ỹ])").sub("Quận ", normalized_result)
    normalized_result = re.compile(r"(?<![a-zA-Z0-9À-ỹ])[pP]\.\s*(?=[A-ZÀ-ỹ])").sub("Phường ", normalized_result)
    normalized_result = re.compile(r"(?<![a-zA-Z0-9À-ỹ])[hH]\.\s*(?=[A-ZÀ-ỹ])").sub("Huyện ", normalized_result)
    normalized_result = re.compile(r"(?<![a-zA-Z0-9À-ỹ])[tT]\.\s*(?=[A-ZÀ-ỹ])").sub("Tỉnh ", normalized_result)
    normalized_result = re.compile(r"(?<![a-zA-Z0-9À-ỹ])tp\.\s*(?=[A-ZÀ-ỹ])").sub("Thành phố ", normalized_result)

    normalized_result = re.compile(r"\s+").sub(" ", normalized_result)
    return normalized_result.strip()


def verify_address_realism(address: str) -> tuple[bool, str]:
    """
    Xác thực offline địa chỉ hành chính (Phường -> Quận -> Tỉnh) sử dụng dvhcvn.json.
    Không gọi LLM để tối ưu hiệu năng, độ trễ và tránh lỗi kết nối/tự bịa.
    """
    db = _load_db()
    provinces_data = db.get("data", [])
    
    segments = [s.strip() for s in address.split(",")]
    
    # 1. Tìm Province segment
    matched_p = None
    for seg in segments:
        clean_seg = clean_name(seg)
        for p in provinces_data:
            if clean_name(p["name"]) == clean_seg:
                matched_p = p
                break
        if matched_p:
            break
            
    if not matched_p:
        # Chấp nhận nếu không tìm thấy Tỉnh chuẩn (ví dụ không điền tỉnh)
        return True, ""
        
    # 2. Tìm District segment và Ward segment
    matched_d = None
    matched_w = None
    
    remaining_segs = [s for s in segments if clean_name(s) != clean_name(matched_p["name"])]
    
    # Tìm District
    for seg in remaining_segs:
        if is_ward_segment(seg):
            continue
        clean_seg = clean_name(seg)
        for d in matched_p.get("level2s", []):
            if clean_name(d["name"]) == clean_seg:
                matched_d = d
                break
        if matched_d:
            break
            
    # Tìm Ward
    for seg in remaining_segs:
        if is_district_segment(seg):
            continue
        clean_seg = clean_name(seg)
        if matched_d:
            # Check historical mapping đầu tiên
            d_name_clean = matched_d["name"].lower()
            hist_map = HISTORICAL_WARDS.get(d_name_clean, {})
            if clean_seg in hist_map:
                active_w_name = hist_map[clean_seg]
                for w in matched_d.get("level3s", []):
                    if w["name"] == active_w_name:
                        matched_w = w
                        break
            
            if not matched_w:
                for w in matched_d.get("level3s", []):
                    if clean_name(w["name"]) == clean_seg:
                        matched_w = w
                        break
        else:
            # Tìm trên toàn bộ các district của province
            for d in matched_p.get("level2s", []):
                # Check historical map cho d
                d_name_clean = d["name"].lower()
                hist_map = HISTORICAL_WARDS.get(d_name_clean, {})
                if clean_seg in hist_map:
                    active_w_name = hist_map[clean_seg]
                    for w in d.get("level3s", []):
                        if w["name"] == active_w_name:
                            matched_w = w
                            matched_d = d
                            break
                            
                if not matched_w:
                    for w in d.get("level3s", []):
                        if clean_name(w["name"]) == clean_seg:
                            matched_w = w
                            matched_d = d
                            break
                if matched_w:
                    break
        if matched_w:
            break
            
    # 3. Kiểm tra mâu thuẫn hành chính trong các segment người dùng ghi
    for seg in remaining_segs:
        # Nếu người dùng ghi rõ Phường X nhưng không tìm thấy Phường nào khớp
        if is_ward_segment(seg) and not matched_w:
            return False, f"Không tìm thấy Phường/Xã có tên '{seg}' hợp lệ."
        # Nếu người dùng ghi rõ Quận Y nhưng không tìm thấy Quận nào khớp
        if is_district_segment(seg) and not matched_d:
            return False, f"Không tìm thấy Quận/Huyện có tên '{seg}' hợp lệ."
            
    # Nếu khớp cả hai, kiểm tra xem Phường có thuộc Quận đó không
    if matched_w and matched_d:
        w_ids = {w["level3_id"] for w in matched_d.get("level3s", [])}
        if matched_w["level3_id"] not in w_ids:
            return False, f"Phường/Xã '{matched_w['name']}' không thuộc '{matched_d['name']}'."
            
    return True, ""
