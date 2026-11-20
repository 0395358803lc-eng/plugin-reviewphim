# -*- coding: utf-8 -*-
"""Build portable ZIP on D:; verify ZIP CRC, names, SHA-256 and skill entry.
Safe to rerun: replaces only the generated ZIP package, not Traffic movie assets.
"""
from pathlib import Path
import json,hashlib,zipfile,datetime,sys,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/(ROOT.name+".zip")
CHECKSUM=ROOT.parent/(ROOT.name+".sha256.txt")
def hashfile(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for buf in iter(lambda:f.read(1024*1024),b""):h.update(buf)
 return h.hexdigest()
files=[p for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.name not in ("PACKAGE_MANIFEST.json",)]
assert len(files)>=9,files
assert (ROOT/"SKILL.md") in files
manifest={
 "package":ROOT.name,
 "title":"Vietnamese Movie Review Production — reusable AI agent skill",
 "created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "case_study":"Traffic (2000)",
 "runtime":"portable documentation; external Windows/FFmpeg/TTS/Remotion runtime not embedded",
 "files":[{"path":p.relative_to(ROOT).as_posix(),"bytes":p.stat().st_size,"sha256":hashfile(p)} for p in files]
}
m=ROOT/"PACKAGE_MANIFEST.json"
m.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
members=files+[m]
with zipfile.ZipFile(OUT,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=8,allowZip64=True) as z:
 for p in members:z.write(p,arcname=ROOT.name+"/"+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(OUT,"r") as z:
 assert z.testzip() is None
 names=set(z.namelist())
 assert len(names)==len(members)
 for p in members:
  key=ROOT.name+"/"+p.relative_to(ROOT).as_posix()
  assert key in names
  assert hashlib.sha256(z.read(key)).hexdigest()==hashfile(p)
CHECKSUM.write_text(f"{hashfile(OUT)}  {OUT.name}\n",encoding="ascii")
print("PACKAGED",OUT,flush=True)
print("ZIP_FILES",len(members),flush=True)
print("ZIP_BYTES",OUT.stat().st_size,flush=True)
print("ZIP_SHA256",hashfile(OUT),flush=True)
print("MANIFEST_FILES",len(manifest["files"]),flush=True)
print("PACKAGING_VALIDATED",flush=True)
