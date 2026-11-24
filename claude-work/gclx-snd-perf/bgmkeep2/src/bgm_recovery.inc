static const unsigned char kNpsDecode[256]={
204,124,243,189,181,140,121,112,19,149,205,78,161,89,217,147,
120,17,59,238,146,234,218,128,209,93,50,13,97,14,225,237,
38,206,46,49,176,187,168,216,107,27,83,175,61,195,235,141,
144,9,154,227,119,253,153,35,122,226,1,129,68,87,109,148,
117,220,244,126,65,241,4,29,232,219,130,10,150,255,166,247,
55,25,170,34,116,85,60,90,139,169,28,222,118,33,5,164,
80,56,40,151,16,111,98,48,190,20,134,47,102,72,201,131,
75,11,125,31,248,37,242,26,43,250,145,165,171,106,70,213,
138,172,160,158,100,254,84,45,156,179,193,63,3,173,132,221,
79,74,0,15,30,54,199,240,152,196,41,103,36,198,21,184,
182,137,192,223,252,245,7,215,66,249,210,42,44,39,228,96,
22,135,208,69,159,6,73,88,211,51,155,200,123,183,178,136,
105,108,180,76,71,101,81,143,32,214,233,86,57,229,197,163,
202,67,251,185,142,82,2,91,212,18,53,230,58,231,239,64,
110,104,77,114,236,62,8,127,174,12,99,23,188,95,24,52,
207,177,92,186,115,224,203,246,162,167,113,133,191,157,194,94
};
// Read-only recovery of the saved per-object gain from the first lyric compatibility build.
struct SaveEncoding {
    std::array<unsigned char,256> inverse{};
    unsigned char shift;
    explicit SaveEncoding(unsigned char first) : shift((unsigned char)(kNpsDecode[first]-'N')) {
        for(unsigned i=0;i<256;++i)inverse[(unsigned char)(kNpsDecode[i]-shift)]=(unsigned char)i;
    }
    unsigned char decode(unsigned char v) const {return (unsigned char)(kNpsDecode[v]-shift);}
};
static bool savePlain(const std::vector<unsigned char>& data,const char signature[5],std::string& plain) {
    if(data.size()<32 || memcmp(data.data(),"NPSF",4))return false;
    unsigned raw=0,stored=0,flags=0;
    memcpy(&raw,data.data()+4,4);memcpy(&stored,data.data()+8,4);memcpy(&flags,data.data()+12,4);
    if(flags || raw!=stored || raw!=data.size()-16)return false;
    SaveEncoding encoding(data[16]);plain.resize(raw);
    for(size_t i=0;i<plain.size();++i)plain[i]=(char)encoding.decode(data[i+16]);
    return !memcmp(plain.data(),signature,4) && !memcmp(plain.data()+8,&raw,4);
}
static bool readSibling(const std::string& path,std::vector<unsigned char>& data,DWORD limit) {
    HANDLE h=CreateFileA(path.c_str(),GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(h==INVALID_HANDLE_VALUE)return false;
    bool ok=readBytes(h,data,limit);CloseHandle(h);return ok;
}
static std::string savedString(const std::string& vars,const char* name) {
    std::string key=std::string(1,'\1')+name+std::string(4,'\0');
    auto i=vars.find(key);
    if(i==std::string::npos || vars.find(key,i+1)!=std::string::npos)return {};
    size_t from=i+key.size()+8;
    if(from>=vars.size())return {};
    auto end=vars.find('\0',from);
    if(end==std::string::npos || end-from>90)return {};
    return vars.substr(from,end-from);
}
static std::string readGainTable(const std::wstring& folder) {
    HANDLE h=CreateFileW((folder+L"active-bgm.n2l").c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,0,nullptr);
    if(h==INVALID_HANDLE_VALUE)return {};
    std::vector<unsigned char> buf;bool ok=readBytes(h,buf,512*1024);CloseHandle(h);
    if(!ok||buf.size()<7||memcmp(buf.data(),"N2BGM1\n",7))return {};
    return std::string(buf.begin(),buf.end());
}
static unsigned authoredGain(const std::string& vars,const std::wstring& folder,std::string& handle) {
    auto scene=savedString(vars,"$GameName");auto line=savedString(vars,"$SYSTEM_present_text");
    handle=savedString(vars,"$SoundPlayName");
    if(!line.empty()&&line.front()=='@')line.erase(0,1);
    if(!handle.empty()&&handle.front()=='@')handle.erase(0,1);
    auto token=[](const std::string& s){return !s.empty() && s.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.")==std::string::npos;};
    if(!token(scene)||!token(line)||!token(handle))return 0;
    static const std::string table=readGainTable(folder);
    std::string key="\n"+scene+"\t"+line+"\t"+handle+"\t";
    auto at=table.find(key);
    if(at==std::string::npos)return 0;
    at+=key.size();unsigned n=0;
    while(at<table.size()&&table[at]>='0'&&table[at]<='9'){
        n=n*10+table[at++]-'0';if(n>2000)return 0;
    }
    return at<table.size()&&table[at]=='\n'?n:0;
}
static bool repairFrames(std::vector<unsigned char>& data,const char* name,const Patch& broken,const std::vector<unsigned char>* knownProgram=nullptr,const std::string* knownVars=nullptr) {
    if(broken.spans.empty())return false;
    // Inspect the matching slot directly. Never persist changes to a save or match a fresh scenario.
    std::string directory(name,strlen(name)-strlen("frames.npf"));
    std::vector<unsigned char> other;
    if(knownProgram)other=*knownProgram;else if(!readSibling(directory+"script.npf",other,64*1024*1024))return false;
    if(!apply(other,broken))return false;
    std::string vars;
    if(knownVars)vars=*knownVars;else if(!readSibling(directory+"val.npf",other,32*1024*1024)||!savePlain(other,"NPSL",vars))return false;
    std::string handle;unsigned gain=authoredGain(vars,broken.folder,handle);
    if(!gain)return false;
    std::string frames;if(!savePlain(data,"NPSD",frames))return false;
    const std::string cue="CreateSound(\""+handle+"\",BGM,\"sound/bgm/";
    size_t start=frames.find(cue);
    if(start==std::string::npos||frames.find(cue,start+1)!=std::string::npos)return false;
    size_t p=frames.find("\");",start+cue.size());
    if(p==std::string::npos||p-start>125)return false;
    p+=3;
    const std::string nul(4,'\0');
    if(frames.compare(p,4,nul))return false;
    p+=4;
    for(unsigned k=0;k<4;++k) {
        auto end=frames.find('\0',p);
        if(end==std::string::npos||end-p>512||frames.compare(end,4,nul))return false;
        if((k==1||k==3)&&frames.substr(p,end-p)!=handle)return false;
        p=end+4;
    }
    // NPSD sound record, relative to its four scope/name strings. Only change a running,
    // silent 44.1 kHz buffer with a positive play cursor. All other fields retain their bytes.
    if(p+157>frames.size() || (unsigned char)frames[p+136]!=0x11)return false;
    auto field=[&](size_t offset){uint32_t value;memcpy(&value,frames.data()+p+offset,4);return value;};
    if(field(141)!=0 || field(145)!=44100 || field(153)==0)return false;
    SaveEncoding encoding(data[16]);
    for(unsigned i=0;i<4;++i)data[16+p+141+i]=encoding.inverse[(gain>>(i*8))&255];
    return true;
}