"""Four paused native-qualified software split examples; no competing policy run.

Default prints the recipe. --execute creates isolated witnesses and stopped tick0
records for the UI freeze acceptance. This is not a scientific experiment sweep.
"""
import argparse
import asyncio
import json
import random
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.runs import Run
from backend.app.storage import Store
from tools.prepare_review_examples import configurations


def recipe_seed(reverse):
    for seed in range(20):
        order=[1,2]
        random.Random('recipe-v1:{}'.format(seed)).shuffle(order)
        if (order[0]==2)==reverse:return seed
    raise ValueError('No bounded role fixture found')


async def execute(args):
    store=Store(args.data_root.resolve()); refs=[]
    for variant,reverse,split in [('import_enabled',False,'development'),
        ('import_disabled',True,'development'),('import_enabled',True,'validation'),
        ('import_disabled',False,'test')]:
        cfg=configurations()['investigation'].model_copy(deep=True)
        cfg.name='Paused software split · '+split+' · '+variant
        cfg.scenario.research.condition_variant=variant
        cfg.scenario.research.seed_namespaces.recipe=recipe_seed(reverse)
        run=Run(cfg,store)
        try:
            await run.initialize()
            assert run.meta['tick']==0 and run.cognition.calls==0
            assert run.meta['feasibility_status']=='native_witness_validated'
            refs.append({'run_id':run.id,'split':split})
            print(json.dumps({'run_id':run.id,'split':split,'tick':0}),flush=True)
        finally:await run.stop()
    store.write_json(args.output,{'name':'Software split and export acceptance',
        'purpose':'software_qualification','worlds':refs,'protocol':{}})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--data-root',type=Path,default=Path('.local/graduation-demo'))
    parser.add_argument('--output',type=Path,default=Path('.local/graduation-demo/split-manifest.json'))
    args=parser.parse_args()
    if args.execute:asyncio.run(execute(args))
    else:print('Four stopped tick0 software worlds: enabled/A, disabled/B development; enabled/B validation; disabled/A held combination. No policy/provider run.')


if __name__=='__main__':main()
