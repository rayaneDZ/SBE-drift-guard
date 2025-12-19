#include "trade_parser.h"
#include <cstring>

namespace {

inline bool need(size_t pos, size_t len, size_t n) {
  return pos + n <= len;
}

inline uint32_t read_u32_le(const uint8_t* p) {
  return (uint32_t)p[0]
       | ((uint32_t)p[1] << 8)
       | ((uint32_t)p[2] << 16)
       | ((uint32_t)p[3] << 24);
}

inline uint64_t read_u64_le(const uint8_t* p) {
  return (uint64_t)p[0]
       | ((uint64_t)p[1] << 8)
       | ((uint64_t)p[2] << 16)
       | ((uint64_t)p[3] << 24)
       | ((uint64_t)p[4] << 32)
       | ((uint64_t)p[5] << 40)
       | ((uint64_t)p[6] << 48)
       | ((uint64_t)p[7] << 56);
}

inline int64_t read_i64_le(const uint8_t* p) {
  return (int64_t)read_u64_le(p);
}

} // namespace

bool parse_trade_update(const uint8_t* buf, size_t len, TradeUpdate& out) {
  size_t pos = 0;
  (void)len;  // silence -Wunused-parameter if generator emits no length checks    // Field: ts    if (!need(pos, len, 8)) return false;
    out.ts = read_u64_le(buf + pos);
    pos += 8;    // Field: symbol    if (!need(pos, len, 12)) return false;
    // raw bytes (not necessarily null-terminated)
    std::memcpy(out.symbol.data(), buf + pos, 12);
    pos += 12;    // Field: price    if (!need(pos, len, 8)) return false;
    out.price = read_i64_le(buf + pos);
    pos += 8;    // Field: qty    if (!need(pos, len, 8)) return false;
    out.qty = read_u64_le(buf + pos);
    pos += 8;    // Field: venue    if (!need(pos, len, 4)) return false;
    // raw bytes (not necessarily null-terminated)
    std::memcpy(out.venue.data(), buf + pos, 4);
    pos += 4;
  return true;
}