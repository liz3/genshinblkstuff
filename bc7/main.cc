#include "bcn.h"
#include <iostream>
#include <filesystem>
#include <fstream>
namespace fs = std::filesystem;

int main(int argc, char** argv) {
  std::string dir = std::string(argv[1]);
  std::string dir_out = std::string(argv[2]);
  for(const auto& entry : fs::directory_iterator(dir)) {
    std::string as_str(entry.path());
    std::string path = "/" + as_str.substr(1, as_str.length()-1);
    std::ifstream stream(path, std::ios::binary);
    stream.seekg(0, stream.end);
    size_t len = stream.tellg();
    stream.seekg(0, stream.beg);
    uint32_t w, h;
    stream.read((char*)&w, 4);
    stream.read((char*)&h, 4);
    uint8_t* data = new uint8_t[len-8];
    stream.read((char*)data, len-8);
    uint8_t* out = new uint8_t[w * h * 4];
    std::string outPath = dir_out + path.substr(path.find_last_of("/")+1);
    std::cout << outPath << "\n";
    decode_bc7(static_cast<const uint8_t*>(data), w, h, static_cast<uint32_t*>((void*)out));
    std::ofstream outFile(outPath, std::ios::binary);
    outFile.write((char*)&w, 4);
    outFile.write((char*)&h, 4);
    outFile.write((char*)out, w * h * 4);
    stream.close();
    outFile.close();
    delete[] out;
    delete[] data;
  }
  return 0;
}
