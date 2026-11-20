"""Bounded process-local verification caches, never executor-supplied flags.

On Windows use NTFS ChangeTime and USN when available, not creation time.
Without an active journal, wait out the clock tick before caching a new file.
This detects same-size writes even if LastWriteTime is restored.
Missing reliable metadata disables reuse.
Permissions and file identity are checked with a fresh read handle on each hit.
"""
from collections import OrderedDict
import copy
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

LIMIT=256
_hashes=OrderedDict()
_tools=OrderedDict()
_media=OrderedDict()
stats={'hash_reads':0,'hash_bytes':0,'hash_hits':0,'probe_runs':0,'decode_runs':0,'media_hits':0}


def clear():
    for cache in (_hashes,_tools,_media):cache.clear()
    for key in stats:stats[key]=0


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def remember(cache,key,value):
    cache[key]=copy.deepcopy(value);cache.move_to_end(key)
    while len(cache)>LIMIT:cache.popitem(last=False)


def _signature(stream,path,settle=True):
    st=os.fstat(stream.fileno())
    change_ns=st.st_ctime_ns;usn=None
    reliable=bool(st.st_ino)
    if os.name=='nt':
        import msvcrt
        class BasicInfo(ctypes.Structure):
            _fields_=[('CreationTime',ctypes.c_longlong),('LastAccessTime',ctypes.c_longlong),
                      ('LastWriteTime',ctypes.c_longlong),('ChangeTime',ctypes.c_longlong),('FileAttributes',ctypes.c_ulong)]
        info=BasicInfo()
        fn=ctypes.windll.kernel32.GetFileInformationByHandleEx
        fn.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_ulong]
        fn.restype=ctypes.c_int
        if fn(msvcrt.get_osfhandle(stream.fileno()),0,ctypes.byref(info),ctypes.sizeof(info)):
            change_ns=info.ChangeTime*100-11644473600000000000;reliable=reliable and change_ns>0
        else:reliable=False
        # Prefer a USN; an inactive NTFS journal can return zero successfully.
        ioctl=ctypes.windll.kernel32.DeviceIoControl
        ioctl.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_ulong,
                        ctypes.c_void_p,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_void_p]
        ioctl.restype=ctypes.c_int
        buffer=ctypes.create_string_buffer(4096);count=ctypes.c_ulong()
        ok=ioctl(msvcrt.get_osfhandle(stream.fileno()),0x000900eb,None,0,buffer,len(buffer),ctypes.byref(count),None)
        if ok and count.value>=32 and int.from_bytes(buffer.raw[4:6],'little')==2:
            usn=int.from_bytes(buffer.raw[24:32],'little',signed=True)
        if not usn:
            # Do not cache during the timestamp's clock tick. This read-only
            # settling delay also works when the USN journal is disabled; it
            # does not change security settings or enable the journal.
            remaining=0.032-(time.time_ns()-change_ns)/1e9
            if settle and 0<remaining<=0.032:
                time.sleep(remaining)
                return _signature(stream,path,settle=False)
            reliable=reliable and remaining<=0
    return {'path':str(Path(path).resolve(strict=True)),'device':st.st_dev,'inode':st.st_ino,
        'size':st.st_size,'mtime_ns':st.st_mtime_ns,'change_ns':change_ns,
        'mode':st.st_mode,'usn':usn,'reliable':reliable}


def fingerprint(path):
    with Path(path).open('rb') as stream:return _signature(stream,path)


def file_sha(path,*,force=False):
    path=Path(path)
    with path.open('rb') as stream:
        before=_signature(stream,path);key=before['path']
        cached=_hashes.get(key)
        if not force and before['reliable'] and cached and cached['fingerprint']==before:
            stats['hash_hits']+=1
            return cached['sha256']
        result=hashlib.file_digest(stream,'sha256').hexdigest()
        if before!=_signature(stream,path):raise ValueError('file changed while hashing')
    stats['hash_reads']+=1;stats['hash_bytes']+=before['size']
    remember(_hashes,key,{'fingerprint':before,'sha256':result})
    return result


def tool_identity(binary):
    before=fingerprint(binary);key=before['path']
    old=_tools.get(key)
    if before['reliable'] and old and old['fingerprint']==before:return copy.deepcopy(old)
    version=subprocess.run([binary,'-version'],capture_output=True,text=True,check=True,timeout=30).stdout.splitlines()[0]
    result={'path':key,'fingerprint':before,'sha256':file_sha(binary),'version':version}
    if fingerprint(binary)!=before:raise ValueError('tool changed during identification')
    remember(_tools,key,result)
    return result


def media_get(key):
    result=_media.get(key)
    return copy.deepcopy(result) if result else None


def media_put(key,result):remember(_media,key,result)


def sealed_evidence(evidence):
    return evidence.get('verification_sha256')==digest({k:v for k,v in evidence.items() if k!='verification_sha256'})
