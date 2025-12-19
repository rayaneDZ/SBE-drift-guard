#pragma once
#include <array>
#include <cstddef>
#include <cstdint>

#ifndef TRADEUPDATE_PARSER_H
#define TRADEUPDATE_PARSER_H

struct TradeUpdate {  uint64_t ts;  std::array<char, 12> symbol;  int64_t price;  uint64_t qty;  std::array<char, 4> venue;};

/// Returns true on success, false if buffer too small.
/// Parses little-endian encoded fields in schema order.
bool parse_trade_update(const uint8_t* buf, size_t len, TradeUpdate& out);

/// Total bytes required for this message (fixed-size schema).
constexpr size_t TRADEUPDATE_WIRE_SIZE = 40;

#endif // TRADEUPDATE_PARSER_H