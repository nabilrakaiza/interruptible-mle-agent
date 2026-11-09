"""Per task: are the split files, A1 harness and evaluation settings identical across all runs?"""
import hashlib, json, glob, os, collections, yaml
def h(p):
    """Short SHA-256 of the file at p, or 'missing'."""
    return hashlib.sha256(open(p,'rb').read()).hexdigest()[:12] if os.path.exists(p) else "missing"
tasks={"spooky-author-identification":"runs/grid","detecting-insults-in-social-commentary":"runs/kaggle","random-acts-of-pizza":"runs/kaggle"}
for task,root in tasks.items():
    runs=sorted(glob.glob(f"{root}/[CA]*_{task}_seed?"))+sorted(glob.glob(f"runs/C6_{task}_seed*"))
    keys=collections.defaultdict(collections.Counter)
    for r in runs:
        files={"labels.csv":"stand_in/harness/labels.csv","test_rows.csv":"stand_in/harness/test_rows.csv","meta.json":"stand_in/harness/meta.json",
               "train.csv (agent)":"stand_in/input/train.csv","predict.csv (agent)":"stand_in/input/predict.csv","a1/harness.sha256":"a1/harness.sha256"}
        for k,p in files.items(): keys[k][h(f"{r}/{p}")]+=1
        cfg=yaml.safe_load(open(f"{r}/config.yaml"))
        keys["config splits"][json.dumps(cfg.get("splits"),sort_keys=True)]+=1
        keys["config evaluator/metric"][json.dumps({k:cfg.get(k) for k in ("evaluator","metric","final_selection")},sort_keys=True)]+=1
        a1=json.load(open(f"{r}/a1/harness.json")); keys["a1 metric/rows/split_seed"][json.dumps({k:a1.get(k) for k in ("metric","rows","split_seed","mode")},sort_keys=True)]+=1
    print(f"== {task}: {len(runs)} runs")
    for k,c in keys.items(): print(f"  {k:26} {'IDENTICAL' if len(c)==1 else 'DIFFERS'} {dict(c) if len(c)>1 else list(c)[0][:90]}")
