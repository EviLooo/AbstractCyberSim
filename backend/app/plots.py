"""Standalone descriptive figures from saved metadata; no execution or providers."""
import io
from collections import defaultdict
from statistics import mean


def analysis_plots(analysis, rows, title):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    output={}
    fig,axes=plt.subplots(1,3,figsize=(12,3.7),layout='constrained')
    for axis,key,label in zip(axes,('success_difference','token_difference','restricted_completion_difference'),
                             ('Success difference','Token difference','Restricted completion ticks')):
        estimate=analysis.get('estimates',{}).get(key,{})
        value=estimate.get('estimate')
        if value is None:
            axis.text(.5,.5,'No eligible paired\nstudy observations',ha='center',va='center',transform=axis.transAxes)
            axis.set_xticks([])
        else:
            interval=estimate.get('world_cluster_bootstrap_95_ci')
            axis.plot([0],[value],'o',color='#216c63')
            if interval:axis.vlines(0,interval[0],interval[1],color='#216c63',linewidth=2)
            axis.axhline(0,color='#88928e',linewidth=.8)
            axis.set_xticks([0],['Hierarchy − swarm'])
            axis.set_title(f"{estimate.get('worlds',0)} causal world clusters")
        axis.set_ylabel(label)
    fig.suptitle(title+' · descriptive paired contrasts')
    for suffix in ('png','svg'):
        buffer=io.BytesIO();fig.savefig(buffer,format=suffix,dpi=160);output['paired-contrasts.'+suffix]=buffer.getvalue()
    plt.close(fig)
    excluded={r['id'] for r in analysis.get('excluded',[])}
    groups=defaultdict(list)
    for row in rows:
        if row['id'] not in excluded:
            groups[row['architecture']].append(row)
    fig,axis=plt.subplots(figsize=(6.2,4.2),layout='constrained')
    if groups:
        for name,group in sorted(groups.items()):
            axis.scatter(mean(r['metrics']['charged_tokens'] for r in group),
                         mean(int(r['metrics']['success']) for r in group),label=f'{name} (n={len(group)})')
        axis.legend()
        axis.set_ylim(-.05,1.05)
    else:axis.text(.5,.5,'No eligible study observations\nSoftware checks are excluded',ha='center',va='center',transform=axis.transAxes)
    axis.set_xlabel('Mean charged tokens · all eligible successes and failures')
    axis.set_ylabel('Mission success fraction');axis.set_title(title+' · success versus cost')
    for suffix in ('png','svg'):
        buffer=io.BytesIO();fig.savefig(buffer,format=suffix,dpi=160);output['success-cost.'+suffix]=buffer.getvalue()
    plt.close(fig)
    return output
