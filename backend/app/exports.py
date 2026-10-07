"""Offline checksummed study bundle. No simulator/provider is constructed."""
import hashlib
import json
import zipfile

from backend.app.evaluation import compare_research
from backend.app.studies import Study, source_manifest
from backend.app.storage import digest
from backend.app.studies import file_hash


def export_study(store, study_id, output):
    study = Study(store,study_id)
    freeze = study.read()
    rows = [m for m in store.list() if m.get('freeze_id')==study_id]
    if any(m['status'] in ('initializing','running') for m in rows):
        raise ValueError('Pause bound runs before exporting a consistent frozen study')
    # Do not mix development and test outcomes or silently recompute with an
    # edited formula. Archival export still works after code changes.
    current_hash = digest(source_manifest())
    unchanged = current_hash==freeze['payload']['source_hash']
    analyses = {split:compare_research([m for m in rows if m.get('split')==split])
                for split in ('development','validation','test')} if unchanged else {}
    entries = {'freeze.json':study.path.read_bytes(),
               'analysis.json':json.dumps({'analyses':analyses,'analysis_source_hash':current_hash,
                   'source_matches_freeze':unchanged,'analysis_omitted_reason':None if unchanged else 'Source changed; archive only. Use the frozen source to reproduce analysis.'},indent=2).encode(),
               'metadata.json':json.dumps(rows,indent=2).encode(),
               'metrics.csv':store.csv(rows).encode()}
    omitted_sources=[]
    for name,expected in freeze['payload']['sources'].items():
        source=study.directory/'source'/name
        if source.is_file() and file_hash(source)==expected:
            entries['source/'+name]=source.read_bytes()
        else:omitted_sources.append(name)
    entries['reproduction.json']=json.dumps({'frozen_source_complete':not omitted_sources,
        'omitted_source_files':omitted_sources,'instructions':'Verify checksums; use bundled frozen source and dependency/runtime declarations for offline metric reproduction. Model blobs and native engine checkout are content-identified external dependencies, not copied into this archive.'},indent=2).encode()
    if unchanged:
        from backend.app.plots import analysis_plots
        for split,analysis in analyses.items():
            for name,data in analysis_plots(analysis,[m for m in rows if m.get('split')==split],split).items():
                entries['figures/'+split+'/'+name]=data
    for meta in rows:
        directory = store.path(meta['id'])
        for file in sorted(directory.rglob('*')):
            if file.is_file() and file.suffix!='.tmp':
                entries['runs/'+meta['id']+'/'+file.relative_to(directory).as_posix()] = file.read_bytes()
    entries['checksums.json'] = json.dumps({name:hashlib.sha256(data).hexdigest() for name,data in entries.items()},indent=2).encode()
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary = output.with_suffix(output.suffix+'.tmp')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(entries.items()):
            archive.writestr(name,data)
    temporary.replace(output)
    return {'path':str(output.resolve()),'runs':len(rows),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'analysis_source_matches_freeze':unchanged}
