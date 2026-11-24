#pragma once
#include <d3d9.h>
#include <stdint.h>
#include <memory>
#include <vector>
struct HDVideoFrame {unsigned w=0,h=0;int64_t pts=0;uint64_t serial=0;std::vector<unsigned char> nv12;};
void VideoPrepare(const char*,IDirect3DDevice9*);
void VideoBind(void*);
void VideoStop(void*);
void VideoReset();
std::shared_ptr<HDVideoFrame> VideoFrame(void*);
extern "C" int __cdecl N2HD_HasVideo(void*);
extern "C" void __cdecl N2HD_VideoTime(void*,int64_t);
