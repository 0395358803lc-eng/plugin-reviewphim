"""REVIEW_PHIM v1.3.29 CLI facade: keep original interface, apply new contract."""
from __future__ import annotations
import sys
import project_flow_cli_v1325 as old_cli
import project_flow_v1329 as new_flow
old_cli.flow=new_flow

if __name__=='__main__':
    sys.exit(old_cli.main())
