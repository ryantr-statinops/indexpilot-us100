"""Append-only hash-chained experiment history with process locking."""
from contextlib import contextmanager
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
from ..export import git_revision
from .protocol import digest


def decode_history(text):
    events=[]; previous=None
    for line in text.splitlines():
        record=json.loads(line)
        body={key:value for key,value in record.items() if key!='record_hash'}
        if body.get('sequence')!=len(events) or body.get('previous_hash')!=previous or record.get('record_hash')!=digest(body):
            raise ValueError('Experiment ledger integrity failed')
        events.append(record); previous=record['record_hash']
    return events


class ExperimentLedger:
    def __init__(self,path): self.path=Path(path)

    def events(self):
        if not self.path.exists(): return []
        with self.path.open() as file:
            fcntl.flock(file,fcntl.LOCK_SH)
            return decode_history(file.read())

    def require_new_reason(self,reason):
        if any(record['event']=='completed' for record in self.events()) and (not isinstance(reason,str) or not reason.strip()):
            raise ValueError('A test has already completed; a new protocol requires --reason')

    def append(self,event,protocol_id=None,**details):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('a+') as file:
            fcntl.flock(file,fcntl.LOCK_EX)
            file.seek(0); records=decode_history(file.read())
            body=dict(sequence=len(records),previous_hash=records[-1]['record_hash'] if records else None,event=event,protocol_id=protocol_id,timestamp=datetime.now(timezone.utc).isoformat(),git_revision=git_revision(),details=details)
            record={**body,'record_hash':digest(body)}
            file.write(json.dumps(record,allow_nan=False)+'\n'); file.flush(); os.fsync(file.fileno())
            return record


@contextmanager
def run_lock(root):
    path=Path(root)/'.run.lock'
    with path.open('a+') as file:
        try: fcntl.flock(file,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as error: raise ValueError('This protocol is already being evaluated') from error
        try: yield
        finally: fcntl.flock(file,fcntl.LOCK_UN)
