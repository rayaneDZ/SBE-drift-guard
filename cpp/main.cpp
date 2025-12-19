#include "trade_parser.h"

#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

static std::string json_escape(const std::string& s) {
  std::ostringstream o;
  for (unsigned char c : s) {
    switch (c) {
      case '\"': o << "\\\""; break;
      case '\\': o << "\\\\"; break;
      case '\b': o << "\\b"; break;
      case '\f': o << "\\f"; break;
      case '\n': o << "\\n"; break;
      case '\r': o << "\\r"; break;
      case '\t': o << "\\t"; break;
      default:
        // Keep it simple for MVP: printable ASCII as-is, others as \u00XX
        if (c >= 0x20 && c <= 0x7E) {
          o << c;
        } else {
          static const char* hex = "0123456789ABCDEF";
          o << "\\u00" << hex[(c >> 4) & 0xF] << hex[c & 0xF];
        }
    }
  }
  return o.str();
}

template <size_t N>
static std::string char_array_to_string(const std::array<char, N>& a) {
  // Trim at first '\0' (common for fixed strings), otherwise use full length.
  size_t len = 0;
  while (len < N && a[len] != '\0') {
    len++;
  }
  return std::string(a.data(), len);
}

static bool read_file(const std::string& path, std::vector<uint8_t>& out) {
  std::ifstream f(path, std::ios::binary);
  if (!f) return false;
  f.seekg(0, std::ios::end);
  std::streamoff size = f.tellg();
  if (size < 0) return false;
  f.seekg(0, std::ios::beg);

  out.resize(static_cast<size_t>(size));
  if (size > 0) {
    f.read(reinterpret_cast<char*>(out.data()), size);
  }
  return static_cast<bool>(f);
}

int main(int argc, char** argv) {
  if (argc == 2 && std::string(argv[1]) == "--help") {
    std::cout << "parse_demo <fixture.bin>\n";
    std::cout << "Reads a binary fixture, parses TradeUpdate, prints JSON.\n";
    return 0;
  }

  if (argc != 2) {
    std::cerr << "Usage: parse_demo <fixture.bin>\n";
    return 2;
  }

  std::vector<uint8_t> buf;
  if (!read_file(argv[1], buf)) {
    std::cerr << "Failed to read file: " << argv[1] << "\n";
    return 3;
  }

  TradeUpdate msg{};
  if (!parse_trade_update(buf.data(), buf.size(), msg)) {
    std::cerr << "Parse failed (buffer too small or invalid)\n";
    return 4;
  }

  // Print stable JSON (no pretty printing, deterministic key order)
  std::cout << "{";
  std::cout << "\"ts\":" << msg.ts << ",";
  std::cout << "\"symbol\":\"" << json_escape(char_array_to_string(msg.symbol)) << "\",";
  std::cout << "\"price\":" << msg.price << ",";
  std::cout << "\"qty\":" << msg.qty << ",";
  std::cout << "\"venue\":\"" << json_escape(char_array_to_string(msg.venue)) << "\"";
  std::cout << "}\n";

  return 0;
}
