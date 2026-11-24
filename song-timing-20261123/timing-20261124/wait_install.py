"""Finish the verified installation once Windows releases the player's open scenario archive."""
import ctypes, sys, time
from ctypes import wintypes as W
from install import HERE, LIVE, install

def archive_is_released():
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    open_file=k.CreateFileW
    open_file.restype=W.HANDLE
    open_file.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,W.LPVOID,W.DWORD,W.DWORD,W.HANDLE]
    k.CloseHandle.argtypes=[W.HANDLE]
    h=open_file(str(LIVE/'nss.npa'),0x10000,7,None,3,0,None)
    if h==ctypes.c_void_p(-1).value:
        error=ctypes.get_last_error()
        if error in (5,32,33):return False
        raise ctypes.WinError(error)
    k.CloseHandle(h)
    return True

if __name__=='__main__':
    print('Waiting for exclusive rename access to the play archive.',flush=True)
    while True:
        if archive_is_released():
            try:install();break
            except PermissionError as error:
                if error.winerror not in (5,32,33):raise
        time.sleep(.35)
