"""Fixed exploratory rule on cached learned depth; never rewrites study.json."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import hashlib
import html
import json
from pathlib import Path
import time
import numpy as np
from carespace.abstention import endpoint_support,abstain_single_frame,ABSTENTION_REV
from carespace.contracts import Grid
from carespace.evaluation import classification_metrics
from carespace.fusion import FUSION_REV
from carespace.learned import prediction_key,CODE_REV,MODEL_REV,ADAPTER_REV
from carespace.pipeline import load_observation,observation_digest
from carespace.planning import analyze

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts';OUT=ART/'abstention'
sha=lambda b:hashlib.sha256(b).hexdigest()
esc=lambda s:html.escape(str(s),quote=True)
LABELS={'passable':'可通行','blocked':'阻斷','unknown':'未知'}


def main():
    started=time.perf_counter();OUT.mkdir(exist_ok=True)
    raw=(ART/'study.json').read_bytes();study=json.loads(raw)
    if study.get('reconstruction_revision')!=FUSION_REV:raise ValueError('Stale fusion revision')
    sources={p:sha((ROOT/p).read_bytes()) for p in ['src/carespace/abstention.py',
        'src/carespace/fusion.py','src/carespace/synthesis.py','src/carespace/planning.py',
        'src/carespace/contracts.py','src/carespace/evaluation.py','src/carespace/learned.py',
        'src/carespace/pipeline.py','scripts/run_abstention.py','docs/abstention-plan.md']}
    records=[];failures=[];inputs=[];expected=0
    for case in study['cases']:
        if case['split']!='evaluation':continue
        support={};input_records={}
        for method_id in ['da3-all','da3-interval']:
            expected+=1
            try:
                m=next(m for m in case['methods'] if m['id']==method_id)
                ids=m['selected_frames']
                if len(set(ids))!=len(ids):raise ValueError('Duplicate selected frame IDs')
                frames={f['id']:f for f in case['frames']}
                for fid in ids:
                    if fid in support:continue
                    path=ART/'observations'/case['id']/f'{fid:03d}.npz'
                    obs=load_observation(path)
                    if obs.scene_id!=case['scene_id'] or observation_digest(obs)!=frames[fid]['observation_sha256']:
                        raise ValueError('Stale observation')
                    key=prediction_key(obs.rgb,obs.K);pred_path=ART/'predictions'/(key+'.npz')
                    meta_path=ART/'predictions'/(key+'.json');meta=json.loads(meta_path.read_text(encoding='utf8'))
                    if any(meta.get(k)!=v for k,v in [('code_revision',CODE_REV),('model_revision',MODEL_REV),('adapter_revision',ADAPTER_REV)]):
                        raise ValueError('Prediction revision mismatch')
                    with np.load(pred_path,allow_pickle=False) as npz:depth=npz['depth']
                    if depth.shape!=obs.depth.shape:raise ValueError('Prediction dimensions changed')
                    # Reference depth participates only in input-integrity verification above.
                    # The rule receives predicted depth, K and known pose, never reference pixels.
                    support[fid]=endpoint_support(depth,obs.K,obs.T_world_camera,case['bounds'],case['resolution'],study['body']['height'])
                    input_records[fid]={'case_id':case['id'],'frame_id':fid,'prediction_key':key,
                        'observation_sha256':sha(path.read_bytes()),'prediction_sha256':sha(pred_path.read_bytes()),
                        'metadata_sha256':sha(meta_path.read_bytes())}
                before=np.asarray(m['states'],np.int8).reshape(case['shape'])
                tick=time.perf_counter();after,votes=abstain_single_frame(before,{fid:support[fid] for fid in ids})
                def plan(states):
                    return analyze(Grid(states,case['bounds'][:2],case['resolution'],case['scene_id']),
                        m['result']['start'],m['result']['goal'],study['body']['radius'])
                original=plan(before);proposed=plan(after)
                transform_and_plan_seconds=time.perf_counter()-tick
                if original['status']!=m['result']['status']:raise ValueError('Saved planner status no longer reproducible')
                if not np.array_equal(before==0,after==0):raise ValueError('Free-space invariant violated')
                if proposed['status']=='passable' and original['status']!='passable':raise ValueError('New passable route violates abstention invariant')
                states_path=OUT/(case['id']+'-'+method_id+'.npz')
                np.savez_compressed(states_path,states=after,supporting_frames=votes,scene_id=case['scene_id'])
                records.append({'case_id':case['id'],'title':case['title'],'method':method_id,
                    'selected_frames':ids,'oracle_status':case['oracle_result']['status'],
                    'original':original,'proposed':proposed,'total_cells':int(before.size),
                    'demoted_cells':int((before!=after).sum()),'free_cells_unchanged':True,
                    'unknown_before':int((before==-1).sum()),'unknown_after':int((after==-1).sum()),
                    'transform_and_plan_seconds':transform_and_plan_seconds,
                    'grid_file':states_path.name,'grid_sha256':sha(states_path.read_bytes())})
            except Exception as exc:
                failures.append({'case_id':case['id'],'method':method_id,'error':str(exc)})
        inputs.extend(input_records.values())
    metrics={}
    for mid in ['da3-all','da3-interval']:
        subset=[r for r in records if r['method']==mid]
        metrics[mid]={stage:classification_metrics([r[stage]['status'] for r in subset],
                     [r['oracle_status'] for r in subset]) for stage in ['original','proposed']}
    result={'revision':ABSTENTION_REV,'exploratory_reused_evaluation':True,
        'rule':'Exactly one distinct selected frame supports occupied XZ column: occupied -> unknown.',
        'study_sha256':sha(raw),'source_sha256':sources,'inputs':inputs,'records':records,
        'expected_queries':expected,'completed_queries':len(records),'failed_queries':len(failures),
        'metrics_completed_queries_only':metrics,'failures':failures,
        'runtime_seconds':time.perf_counter()-started,'inference_performed':False}
    (OUT/'experiment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    write_report(result)
    print(json.dumps({'completed':len(records),'failures':failures,'metrics':metrics},ensure_ascii=True))
    if failures:raise SystemExit(1)


def write_report(result):
    note='探索性重用既有評估案例；規則受先前診斷啟發，不能宣稱未見資料泛化。僅一張影格支援的障礙欄降為未知，其餘保持原狀。自由格集合完全不變；阻斷變未知是拒絕下結論，不是成功重建。不同影格支援同一 XZ 欄，不代表觀測到同一物體表面。'
    headers=['案例／方法','原判斷','降為未知後','Oracle','降級格數','未知格：前 → 後／全部格']
    rows=[];lines=['# 單影格障礙降為未知實驗','',note,'',
        '| '+' | '.join(headers)+' |','|---|---|---|---|---:|---|']
    for r in result['records']:
        values=[r['title']+' / '+r['method'],LABELS[r['original']['status']],LABELS[r['proposed']['status']],
            LABELS[r['oracle_status']],r['demoted_cells'],f"{r['unknown_before']} → {r['unknown_after']} / {r['total_cells']}"]
        rows.append('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in values)+'</tr>')
        lines.append('| '+' | '.join(map(str,values))+' |')
    metric_rows=[]
    lines+=['','## 查詢指標','',
        '| 方法 | 階段 | 完成查詢 | 決策覆蓋 | 放行／阻斷／未知 | 錯誤放行／oracle 阻斷 | 錯誤放行／預測放行 |',
        '|---|---|---:|---|---|---|---|']
    ratio=lambda n,d:f'{n}/{d}' if d else '不適用（分母 0）'
    for mid,stages in result['metrics_completed_queries_only'].items():
        for stage,m in stages.items():
            c=m['counts'];n=m['n_queries']
            values=[mid,'原方法' if stage=='original' else '降為未知',n,
                ratio(n-c['unknown'],n),f"{c['passable']} / {c['blocked']} / {c['unknown']}",
                ratio(m['false_release_count'],m['oracle_blocked_count']),
                ratio(m['false_release_count'],m['predicted_pass_count'])]
            metric_rows.append('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in values)+'</tr>')
            lines.append('| '+' | '.join(map(str,values))+' |')
    failures=''.join('<p>'+esc(f)+'</p>' for f in result['failures'])
    accounting=f"預定 {result['expected_queries']} 個案例／方法查詢；完成 {result['completed_queries']}；失敗 {result['failed_queries']}。指標只計完成查詢；相同房間的變體與方法不是獨立家庭。"
    page=f'''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CareSpace 3D｜障礙降為未知實驗</title>
<style>body{{max-width:1250px;margin:24px auto;padding:0 20px;background:#eaf0f4;color:#152f43;font:15px/1.7 system-ui}}h1{{font-size:26px}}h2{{font-size:20px;margin-top:32px}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{padding:12px;border-bottom:1px solid #bdcdd5;text-align:left}}.table{{overflow:auto}}code{{overflow-wrap:anywhere}}a{{color:#09656a}}[hidden]{{display:none}}</style>
<a href="/viewer/">返回通行工作台</a> · <a href="/artifacts/depth-audit/index.html">來源診斷</a><h1>把低支援障礙降為未知，會改變什麼？</h1><p>{esc(note)}</p><p id=validation>核對研究指紋中…</p>
<main hidden><p>{accounting}</p>{failures}<h2>固定查詢結果</h2><div class=table><table><thead><tr>{''.join('<th>'+h+'</th>' for h in headers)}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>決策覆蓋與錯誤放行分母</h2><div class=table><table><thead><tr><th>方法</th><th>階段</th><th>完成查詢</th><th>決策覆蓋</th><th>放行／阻斷／未知</th><th>錯誤放行／oracle 阻斷</th><th>錯誤放行／預測放行</th></tr></thead><tbody>{''.join(metric_rows)}</tbody></table></div>
<p>原始研究與主要工作台的融合規則未變更。新格網、影格支援數、各狀態覆蓋率、路徑與淨空、來源雜湊、執行時間及失敗紀錄保存於 <a href="experiment.json">experiment.json</a>，每個格網有獨立 NPZ。沒有新模型推論；變換只使用預測深度、相機 K 與已知姿態，oracle 標籤僅供評估。</p><p>Study SHA256：<code>{result['study_sha256']}</code></p></main>
<script type=module>const label=document.getElementById('validation');try{{const r=await fetch('../study.json',{{cache:'no-store'}});if(!r.ok)throw Error('研究資料無法讀取');const d=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await r.arrayBuffer())),x=>x.toString(16).padStart(2,'0')).join('');if(d!=='{result['study_sha256']}')throw Error('研究已變更，請重新執行實驗');label.textContent='研究指紋相符 · 探索性實驗';document.querySelector('main').hidden=false}}catch(e){{label.textContent=e.message}}</script></html>'''
    (OUT/'index.html').write_text(page,encoding='utf8')
    lines+=['',accounting,*[str(f) for f in result['failures']],'',
        '未知格比例與決策覆蓋分開報告；無預測放行時錯誤放行／預測放行為不適用。',
        '重現：`.venv/Scripts/python scripts/run_abstention.py`；本機頁面 `/artifacts/abstention/index.html`。',
        '此實驗未修改 study.json 或主要工作台方法。完整格網、路徑、來源雜湊與失敗紀錄在 artifacts/abstention/。','']
    (ROOT/'docs/abstention.md').write_text('\n'.join(lines),encoding='utf8')


if __name__=='__main__':main()
