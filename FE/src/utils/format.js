export function formatVND(value) {
  const number = Number(value || 0);
  return number.toLocaleString('vi-VN') + 'đ';
}

export function calculateOriginalPrice(price) {
  const numPrice = Number(price || 0);
  return Math.round(numPrice * 1.5);
}
