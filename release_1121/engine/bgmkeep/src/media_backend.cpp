#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <d3d9.h>
#include <dxva2api.h>
#include <wrl/client.h>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <deque>
#include <unordered_map>
#include <string>
#include <atomic>
#include <chrono>
#include "media_backend.h"
using Microsoft::WRL::ComPtr;
struct Decoder {
 std::mutex lock;std::condition_variable wake;std::deque<std::shared_ptr<HDVideoFrame>> queue;std::shared_ptr<HDVideoFrame> current;std::thread worker;
 bool stopping=false,ready=false,eof=false;int64_t clock=0;uint64_t decoded=0,shown=0,skipped=0,seekGeneration=0,seekApplied=0;HRESULT error=S_OK;unsigned width=0,height=0;std::wstring path;ComPtr<IDirect3DDevice9> device;
 Decoder(const wchar_t* p,IDirect3DDevice9* d):path(p),device(d){worker=std::thread([this](){run();});}
 void stop(){{std::lock_guard<std::mutex> g(lock);stopping=true;}wake.notify_all();if(worker.joinable())worker.join();}
 ~Decoder(){stop();}
 void run(){CoInitializeEx(0,COINIT_MULTITHREADED);HRESULT hr=MFStartup(MF_VERSION);bool started=SUCCEEDED(hr);if(started){
  ComPtr<IMFAttributes> attrs;MFCreateAttributes(&attrs,5);UINT token=0;ComPtr<IDirect3DDeviceManager9> manager;hr=DXVA2CreateDirect3DDeviceManager9(&token,&manager);if(SUCCEEDED(hr))hr=manager->ResetDevice(device.Get(),token);if(SUCCEEDED(hr))hr=attrs->SetUnknown(MF_SOURCE_READER_D3D_MANAGER,manager.Get());attrs->SetUINT32(MF_READWRITE_ENABLE_HARDWARE_TRANSFORMS,TRUE);attrs->SetUINT32(MF_SOURCE_READER_DISABLE_DXVA,FALSE);
  ComPtr<IMFSourceReader> reader;if(SUCCEEDED(hr))hr=MFCreateSourceReaderFromURL(path.c_str(),attrs.Get(),&reader);
  if(SUCCEEDED(hr)){reader->SetStreamSelection(MF_SOURCE_READER_ALL_STREAMS,FALSE);reader->SetStreamSelection(MF_SOURCE_READER_FIRST_VIDEO_STREAM,TRUE);ComPtr<IMFMediaType> type;MFCreateMediaType(&type);type->SetGUID(MF_MT_MAJOR_TYPE,MFMediaType_Video);type->SetGUID(MF_MT_SUBTYPE,MFVideoFormat_NV12);hr=reader->SetCurrentMediaType(MF_SOURCE_READER_FIRST_VIDEO_STREAM,0,type.Get());type.Reset();if(SUCCEEDED(hr))hr=reader->GetCurrentMediaType(MF_SOURCE_READER_FIRST_VIDEO_STREAM,&type);UINT32 w=0,h=0,stride=0;if(SUCCEEDED(hr))hr=MFGetAttributeSize(type.Get(),MF_MT_FRAME_SIZE,&w,&h);if(SUCCEEDED(hr)){type->GetUINT32(MF_MT_DEFAULT_STRIDE,&stride);if(!stride)stride=w;if(w!=3840||h!=2160||stride<w)hr=E_INVALIDARG;else {std::lock_guard<std::mutex> g(lock);width=w;height=h;}}
   while(SUCCEEDED(hr)){int64_t seek=-1;{
    std::unique_lock<std::mutex> g(lock);wake.wait(g,[this](){return stopping||queue.size()<3||seekGeneration!=seekApplied;});if(stopping)break;if(seekGeneration!=seekApplied){seek=clock;seekApplied=seekGeneration;queue.clear();current.reset();eof=false;}}
    if(seek>=0){PROPVARIANT pos={};pos.vt=VT_I8;pos.hVal.QuadPart=seek;hr=reader->SetCurrentPosition(GUID_NULL,pos);if(FAILED(hr))break;}
    DWORD flags=0;LONGLONG pts=0;ComPtr<IMFSample> sample;hr=reader->ReadSample(MF_SOURCE_READER_FIRST_VIDEO_STREAM,0,0,&flags,&pts,&sample);if(FAILED(hr))break;if(flags&MF_SOURCE_READERF_ENDOFSTREAM){std::lock_guard<std::mutex> g(lock);eof=true;break;}if(!sample)continue;
    ComPtr<IMFMediaBuffer> buffer;hr=sample->ConvertToContiguousBuffer(&buffer);if(FAILED(hr))break;BYTE* bytes=0;DWORD length=0;hr=buffer->Lock(&bytes,0,&length);if(FAILED(hr))break;
    auto frame=std::make_shared<HDVideoFrame>();frame->w=w;frame->h=h;frame->pts=pts;frame->nv12.resize(size_t(w)*h*3/2);if(length<size_t(stride)*h*3/2){buffer->Unlock();hr=E_UNEXPECTED;break;}for(unsigned y=0;y<h*3/2;++y)memcpy(frame->nv12.data()+size_t(y)*w,bytes+size_t(y)*stride,w);buffer->Unlock();{
     std::lock_guard<std::mutex> g(lock);frame->serial=++decoded;queue.push_back(frame);ready=true;}wake.notify_all();
   }
  }
  {std::lock_guard<std::mutex> g(lock);error=hr;ready=true;}wake.notify_all();
 }else{{std::lock_guard<std::mutex> g(lock);error=hr;ready=true;}wake.notify_all();}if(started)MFShutdown();CoUninitialize();}
 bool waitReady(){std::unique_lock<std::mutex> g(lock);wake.wait_for(g,std::chrono::seconds(5),[this](){return ready;});return ready&&SUCCEEDED(error)&&!queue.empty();}
 std::shared_ptr<HDVideoFrame> get(){std::lock_guard<std::mutex> g(lock);unsigned consumed=0;while(!queue.empty()&&(!current||queue.front()->pts<=clock+170000)){current=queue.front();queue.pop_front();++consumed;}if(consumed){++shown;skipped+=consumed-1;wake.notify_all();}return current;}
};
struct State{std::mutex lock;std::unordered_map<void*,std::shared_ptr<Decoder>> videos;std::shared_ptr<Decoder> pending,last;};static State& state(){static State* s=new State;return *s;}
static std::shared_ptr<Decoder> find(void* data){auto& s=state();std::lock_guard<std::mutex> g(s.lock);auto i=s.videos.find(data);return i==s.videos.end()?nullptr:i->second;}
void VideoPrepare(const char* name,IDirect3DDevice9* dev){auto& s=state();std::shared_ptr<Decoder> old;{std::lock_guard<std::mutex> g(s.lock);old=std::move(s.pending);}if(old)old->stop();if(!name||!dev)return;const char* base=name;for(auto p=name;*p;++p)if(*p=='/'||*p=='\\')base=p+1;const wchar_t* path=0;if(!_stricmp(base,"mv_op.ngs"))path=L"dx4k/mv_op.mp4";else if(!_stricmp(base,"GC_eyecatch_E.ngs"))path=L"dx4k/GC_eyecatch_E.mp4";else if(!_stricmp(base,"mv_lx0201.ngs"))path=L"dx4k/mv_lx0201.mp4";/*Claude 11-23: 2장 영상 4K(코덱스 10-26 판을 11-21 자막 고쳐 다시 구움) — 그동안 이 줄이 없어 한 번도 안 쓰였다*/if(!path||GetFileAttributesW(path)==INVALID_FILE_ATTRIBUTES)return;auto decoder=std::make_shared<Decoder>(path,dev);if(!decoder->waitReady()){decoder->stop();return;}std::lock_guard<std::mutex> g(s.lock);s.pending=decoder;}
void VideoBind(void* data){auto& s=state();std::lock_guard<std::mutex> g(s.lock);if(data&&s.pending){s.videos[data]=s.pending;s.last=s.pending;s.pending.reset();}}
void VideoStop(void* data){auto& s=state();std::shared_ptr<Decoder>d;{std::lock_guard<std::mutex>g(s.lock);auto i=s.videos.find(data);if(i!=s.videos.end()){d=i->second;s.videos.erase(i);}}if(d)d->stop();}
void VideoReset(){auto& s=state();std::unordered_map<void*,std::shared_ptr<Decoder>> v;std::shared_ptr<Decoder> p;{std::lock_guard<std::mutex>g(s.lock);v.swap(s.videos);p=std::move(s.pending);}for(auto&i:v)i.second->stop();if(p)p->stop();}
std::shared_ptr<HDVideoFrame> VideoFrame(void* data){auto d=find(data);return d?d->get():nullptr;}
extern "C" int __cdecl N2HD_HasVideo(void* data){return find(data)?1:0;}
extern "C" void __cdecl N2HD_VideoTime(void* data,int64_t pts){auto d=find(data);if(!d)return;std::lock_guard<std::mutex>g(d->lock);if(pts+500000<d->clock){++d->seekGeneration;d->wake.notify_all();}d->clock=pts;}
extern "C" __declspec(dllexport) void __cdecl N2HD_VideoStats(uint64_t* out){memset(out,0,10*sizeof(uint64_t));auto&s=state();std::shared_ptr<Decoder>d;{std::lock_guard<std::mutex>g(s.lock);d=s.last;out[9]=s.videos.size();}if(!d)return;std::lock_guard<std::mutex>g(d->lock);out[0]=d->width;out[1]=d->height;out[2]=d->decoded;out[3]=d->shown;out[4]=d->skipped;out[5]=d->current?d->current->pts:0;out[6]=d->clock;out[7]=(uint32_t)d->error;out[8]=d->eof?1:0;}
