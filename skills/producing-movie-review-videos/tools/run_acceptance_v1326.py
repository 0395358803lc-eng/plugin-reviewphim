"""Reproduce the release tests with real local FFmpeg, keeping media evidence.

This is a development test harness, not a movie-production or remote executor.
It uses installed Python/pytest/FFmpeg only and never installs dependencies.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,help='new directory for test logs and real codec artifacts')
    args=parser.parse_args()
    output=Path(args.output).resolve()
    if output.exists():raise ValueError('use a new output directory; evidence is never overwritten')
    for tool in ('ffmpeg','ffprobe'):
        if not shutil.which(tool):raise RuntimeError(tool+' must already be installed')
    output.mkdir(parents=True)
    skill=Path(__file__).resolve().parents[1]
    repo=skill.parents[1]
    env=dict(os.environ,REVIEW_EVIDENCE_DIR=str(output),PYTHONIOENCODING='utf-8')
    # tempfile selects a unique directory; pytest never clears a user path.
    with tempfile.TemporaryDirectory(prefix='review-v1326-') as temp:
        command=[sys.executable,'-m','pytest','-q',str(skill/'tests'),'--tb=short','-rs',
                 '--basetemp',str(Path(temp)/'pytest'),'--junitxml',str(output/'pytest.xml')]
        result=subprocess.run(command,cwd=repo,env=env,capture_output=True,text=True,encoding='utf-8')
    (output/'pytest.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    probes={}
    for video in sorted(output.glob('*.mp4')):
        probe=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(video)],
                             check=True,capture_output=True,text=True)
        decode=subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-err_detect','explode','-i',str(video),
                               '-map','0:v','-map','0:a?','-f','null','-'],capture_output=True,text=True)
        probes[video.name]={'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
                           'probe':json.loads(probe.stdout),'decode_exit':decode.returncode,'decode_stderr':decode.stderr}
        if decode.returncode or decode.stderr:raise RuntimeError('release MP4 decode failed')
    report={'pytest_exit':result.returncode,'python':sys.version,'command':command,'videos':probes,
        'ffmpeg':subprocess.run(['ffmpeg','-version'],capture_output=True,text=True,check=True).stdout.splitlines()[0],
        'scope':'Local orchestration integration with real decodable video. Business-stage fixtures do not certify remote models or film content.'}
    (output/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    checksums={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}
    (output/'sha256.json').write_text(json.dumps(checksums,indent=2),encoding='utf-8')
    print(result.stdout)
    print('Evidence:',output)
    return result.returncode if probes else 2


if __name__=='__main__':sys.exit(main())
