"""Append-only v3 deltas with periodic snapshots; read/append v2 unchanged.

Cold loads verify the complete chain once. Warm reads compare the real file's
identity/change metadata and reuse the verified head. Any external change
invalidates that cache and triggers a full chain audit, including old prefixes.
No history is truncated, compacted in place, or silently migrated.
"""
import copy
from contextlib import contextmanager
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path

SNAPSHOT_INTERVAL=32
_heads={}
stats={'ledger_reads':0,'ledger_bytes':0,'head_hits':0,'appends':0,'snapshots':0}


def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()


def clear():
    _heads.clear()
    for key in stats:stats[key]=0


def delta(old,new,path=()):
    changes=[]
    if isinstance(old,dict) and isinstance(new,dict):
        for key in sorted(old.keys()-new.keys()):changes.append({'op':'remove','path':list(path+(key,))})
        for key in sorted(new):
            if key not in old:changes.append({'op':'set','path':list(path+(key,)),'value':copy.deepcopy(new[key])})
            else:changes.extend(delta(old[key],new[key],path+(key,)))
    elif old!=new:changes.append({'op':'set','path':list(path),'value':copy.deepcopy(new)})
    return changes


def apply_delta(state,changes):
    out=copy.deepcopy(state)
    for change in changes:
        path=change['path']
        if not isinstance(path,list) or not all(isinstance(k,str) for k in path):raise ValueError('invalid delta path')
        if not path:
            if change['op']!='set' or not isinstance(change['value'],dict):raise ValueError('invalid root delta')
            out=copy.deepcopy(change['value']);continue
        parent=out
        for key in path[:-1]:parent=parent[key]
        if change['op']=='set':parent[path[-1]]=copy.deepcopy(change['value'])
        elif change['op']=='remove':del parent[path[-1]]
        else:raise ValueError('unknown delta operation')
    return out


def head(ledger,fingerprint,*,audit=False):
    ledger=Path(ledger);key=str(ledger.resolve(strict=False))
    if not ledger.exists():
        _heads.pop(key,None)
        return {'seq':0,'event_hash':None,'state':{},'events':[],'schema':None,'fingerprint':None}
    before=fingerprint(ledger);cached=_heads.get(key)
    if not audit and before['reliable'] and cached and cached['fingerprint']==before:
        stats['head_hits']+=1;return cached
    state={};events=[];previous=None;schema=None
    with ledger.open('rb') as stream:
        for line in stream:
            if not line.endswith(b'\n'):raise ValueError('incomplete ledger tail; history is never truncated')
            event=json.loads(line)
            if event.get('schema') not in {'project-flow-event.v2','project-flow-event.v3'}:
                raise ValueError('unsupported legacy ledger; preserve it read-only')
            if schema and event['schema']!=schema:raise ValueError('mixed ledger schema; no automatic migration')
            schema=event['schema']
            if event.get('seq')!=len(events)+1 or event.get('previous_hash')!=previous:raise ValueError('ledger sequence mismatch')
            raw={k:v for k,v in event.items() if k!='event_hash'}
            # Preserve the historical canonical hash encoding for v2.
            expected=(hashlib.sha256(json.dumps(raw,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest())
            if expected!=event.get('event_hash'):raise ValueError('ledger hash mismatch')
            if schema=='project-flow-event.v2' or 'state' in event:state=copy.deepcopy(event['state'])
            else:state=apply_delta(state,event['delta'])
            if state.get('ledger_seq')!=event['seq']:raise ValueError('ledger state sequence mismatch')
            if schema=='project-flow-event.v3' and digest(state)!=event.get('state_sha256'):raise ValueError('delta state hash mismatch')
            previous=event['event_hash'];events.append(event)
    if fingerprint(ledger)!=before:raise ValueError('ledger changed during audit; reload')
    stats['ledger_reads']+=1;stats['ledger_bytes']+=before['size']
    result={'seq':len(events),'event_hash':previous,'state':state,'events':events,'schema':schema,'fingerprint':before}
    _heads[key]=result
    if len(_heads)>64:_heads.pop(next(iter(_heads)))
    return result


@contextmanager
def writer(logs):
    path=Path(logs)/'project_flow.writer.lock'
    if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('writer lock redirects')
    with path.open('a+b') as stream:
        stream.seek(0,os.SEEK_END)
        if not stream.tell():stream.write(b'0');stream.flush()
        stream.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:yield
        finally:
            stream.seek(0)
            if os.name=='nt':msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream.fileno(),fcntl.LOCK_UN)


def append(logs,state,event,details,fingerprint,write_snapshot):
    ledger=Path(logs)/'project_flow_v1325.jsonl'
    with writer(logs):
        old=head(ledger,fingerprint)
        if not old['seq'] and (Path(logs)/'project_flow_v1325.json').exists():
            raise ValueError('snapshot without canonical ledger is read-only')
        if old['seq'] and state.get('ledger_seq',0)!=old['seq']:raise ValueError('stale state; reload canonical ledger')
        current=copy.deepcopy(state);current['ledger_seq']=old['seq']+1;current['state_schema']='project-flow.v2'
        schema=old['schema'] or 'project-flow-event.v3'
        important=event in {'WAITING_USER','FAILED','FINAL_REVIEW','PACKAGE_DONE','ACCEPTED','REVISION_REQUESTED','REVISION_STARTED'}
        snapshot=not old['seq'] or current['ledger_seq']%SNAPSHOT_INTERVAL==0 or important
        # Full completion is already in the delta. Keep the event detail digest.
        compact_details=copy.deepcopy(details or {})
        if 'record' in compact_details:compact_details['record_sha256']=compact_details.pop('record').get('record_sha256')
        entry={'schema':schema,'seq':current['ledger_seq'],'previous_hash':old['event_hash'],
               'timestamp':datetime.now(timezone.utc).isoformat(),'event':event,'details':compact_details}
        if schema=='project-flow-event.v2' or snapshot:entry['state']=copy.deepcopy(current)
        else:entry['delta']=delta(old['state'],current)
        if schema=='project-flow-event.v3':entry['state_sha256']=digest(current)
        entry['event_hash']=digest(entry)
        payload=canonical(entry)+b'\n'
        with ledger.open('ab') as stream:
            stream.write(payload);stream.flush();os.fsync(stream.fileno())
        state.clear();state.update(current)
        _heads[str(ledger.resolve())]={'seq':entry['seq'],'event_hash':entry['event_hash'],'state':copy.deepcopy(current),
            'events':old['events']+[entry],'schema':schema,'fingerprint':fingerprint(ledger)}
        stats['appends']+=1
        if snapshot or schema=='project-flow-event.v2':
            write_snapshot(state);stats['snapshots']+=1
