// These calls come from the game's existing script-safe native Save/Load dispatcher.
static int __cdecl storyCheckpointQuery(int id){return LyricSave::StoryResume::queried(id)?1:0;}
static void __cdecl storyNormalLoadStart(){LyricSave::StoryResume::reset();}
static int __cdecl storyCheckpointSave(){
    namespace S=LyricSave::StoryResume;
    if(!S::startCapture())return 0;
    S::Bytes program,objects;bool saved=false;std::string scratch;
    try{
        char app[MAX_PATH];DWORD len=GetModuleFileNameA(nullptr,app,MAX_PATH);
        if(len&&len<MAX_PATH){
            std::string base(app,len);auto slash=base.find_last_of("\\/");
            if(slash!=std::string::npos){
                static std::atomic<unsigned> counter{0};
                base.resize(slash+1);auto path=base+"lyrics-resume\\stage-"+std::to_string(GetCurrentProcessId())+"-"+std::to_string(GetTickCount64())+"-"+std::to_string(++counter);
                if(path.size()<204 && CreateDirectoryA(path.c_str(),nullptr)){
                    scratch=path;
                    if(Jump::dir(path+"\\0001")&&Jump::dir(path+"\\images")&&Jump::dir(path+"\\common")){
                        struct RestoreDirectory {char old[260];RestoreDirectory(){strcpy_s(old,(const char*)0x5a54b4);}~RestoreDirectory(){strcpy_s((char*)0x5a54b4,260,old);}} directory;
                        strcpy_s((char*)0x5a54b4,260,path.c_str());
                        saved=Jump::nativeSave(1)!=0;
                    }
                    saved=saved&&Jump::read(path+"\\0001\\script.npf",program)&&Jump::read(path+"\\0001\\frames.npf",objects);
                }
            }
        }
    }catch(...){saved=false;}
    if(!scratch.empty()){
        for(const char* child:{"0001","images","common"}){
            auto p=scratch+"\\"+child;
            for(const auto& n:Jump::names(p,"*.npf"))DeleteFileW(Jump::wp(p+"\\"+n).c_str());
            RemoveDirectoryW(Jump::wp(p).c_str());
        }
        RemoveDirectoryW(Jump::wp(scratch).c_str());
    }
    try{S::finishCapture(program,objects,saved);}catch(...){S::finishCapture(program,objects,false);}
    return saved?1:0;
}
static int __cdecl storyCheckpointLoad(){
    int id=LyricSave::StoryResume::startReload();if(id<0)return 0;
    *(int*)0x5b3ec4=id;
    int ok=Jump::load();LyricSave::StoryResume::finishReload();return ok;
}
