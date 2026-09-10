"""CPU, cached-prediction forensic report; never alters the study or depth estimates."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2')
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import hashlib
import html
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
from PIL import Image
from carespace.depth_audit import trace_frame,summarize_support,support_risk,AUDIT_REV,FLOOR_TOLERANCE_M
from carespace.scenes import build_scene,oracle_grid
from carespace.learned import prediction_key,metric_scale,CODE_REV,MODEL_REV,ADAPTER_REV
from carespace.pipeline import load_observation,observation_digest
from carespace.synthesis import camera_rays
from carespace.fusion import FUSION_REV

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts'
OUT=ART/'depth-audit'
sha=lambda data:hashlib.sha256(data).hexdigest()
esc=lambda value:html.escape(str(value),quote=True)

def upstream_check(obs):
    source=ROOT/'third_party/Depth-Anything-3'
    revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if revision!=CODE_REV or subprocess.run(['git','-C',str(source),'diff','--quiet','HEAD','--']).returncode:
        raise ValueError('Unverified upstream source')
    sys.path.insert(0,str(source/'src'))
    import torch
    from depth_anything_3.utils.alignment import apply_metric_scaling
    from depth_anything_3.utils.geometry import unproject_depth
    from depth_anything_3.utils.io.input_processor import InputProcessor
    torch.set_num_threads(2)
    images,_,kp=InputProcessor()(image=[obs.rgb],intrinsics=np.asarray([obs.K],np.float32),
        process_res=224,process_res_method='upper_bound_resize',num_workers=1,sequential=True)
    if tuple(images.shape[-2:])!=obs.depth.shape or not np.allclose(kp[0].numpy(),obs.K):
        raise ValueError('Current observations unexpectedly changed size or intrinsics in preprocessing')
    canonical=np.linspace(.1,10,12,dtype=np.float32).reshape(3,4)
    upstream=apply_metric_scaling(torch.from_numpy(canonical)[None,None],kp[None])[0,0].numpy()
    metric_error=float(np.max(np.abs(upstream-metric_scale(canonical,kp[0].numpy()))))
    h,w=obs.depth.shape
    official=unproject_depth(torch.tensor(obs.depth,dtype=torch.float64)[None,None,:,:,None],
        torch.tensor(obs.K,dtype=torch.float64)[None,None],torch.tensor(obs.T_world_camera,dtype=torch.float64)[None,None])
    origins,rays=camera_rays(obs.K,obs.T_world_camera,w,h)
    camera_error=float(np.max(np.abs(official.numpy().reshape(-1,3)-(origins+rays*obs.depth.ravel()[:,None]))))
    if metric_error>1e-6 or camera_error>1e-8:raise ValueError('Upstream conversion mismatch')
    return {'code_revision':revision,'metric_max_error_m':metric_error,'world_projection_max_error_m':camera_error,
        'processed_shape':list(images.shape),'processed_intrinsics':kp[0].numpy().tolist(),
        'weights_loaded':False,'note':'Pinned upstream CPU utility equivalence; not a new model inference.'}

def diagnostic_images(trace,stem,rgb,reference_depth,predicted_depth):
    # Snapshot the actual audited arrays; mutable study preview PNGs are not evidence.
    Image.fromarray(rgb).save(OUT/(stem+'-rgb.png'))
    for label,depth in [('reference',reference_depth),('predicted',predicted_depth)]:
        d=np.clip(np.nan_to_num(depth)/10,0,1)
        color=np.stack([255*(1-d),220*np.sqrt(d),255*d],axis=-1).astype(np.uint8)
        color[(~np.isfinite(depth))|(depth<=0)]=[30,40,50]
        Image.fromarray(color).save(OUT/(stem+'-'+label+'.png'))
    error=trace['signed_error'];valid=np.isfinite(error)
    # Fixed visualization only: blue = underestimated, red = overestimated, ±1 m.
    strength=np.minimum(np.abs(np.nan_to_num(error)),1)[...,None]
    target=np.where((np.nan_to_num(error)>=0)[...,None],[188,52,56],[34,100,180])
    color=(245*(1-strength)+target*strength).astype(np.uint8);color[~valid]=[85,95,105]
    Image.fromarray(color).save(OUT/(stem+'-error.png'))
    mask=np.full((*error.shape,3),245,np.uint8);mask[trace['floor_lift_mask']]=[174,48,100]
    Image.fromarray(mask).save(OUT/(stem+'-floor.png'))

def main():
    started=time.perf_counter();OUT.mkdir(exist_ok=True)
    raw=(ART/'study.json').read_bytes();study=json.loads(raw)
    if study.get('reconstruction_revision')!=FUSION_REV:raise ValueError('Unsupported saved fusion revision')
    sources={p:sha((ROOT/p).read_bytes()) for p in ['src/carespace/depth_audit.py','src/carespace/fusion.py',
        'src/carespace/synthesis.py','src/carespace/scenes.py','src/carespace/learned.py','scripts/build_depth_audit.py']}
    records=[];summaries=[];panels=[];failures=[];conversion=None
    for case in study['cases']:
        if case['split']!='evaluation':continue
        try:
            baseline=next(m for m in case['methods'] if m['id']=='all')
            selected=next(m for m in case['methods'] if m['id']=='da3-all')
            if sorted(baseline['selected_frames'])!=sorted(selected['selected_frames']):raise ValueError('Unmatched frame IDs')
            if len(set(selected['selected_frames']))!=len(selected['selected_frames']):raise ValueError('Duplicate frame IDs')
            scene=build_scene(case['id'].removeprefix('replica-'),replica=True)
            if scene.scene_id!=case['scene_id'] or scene.bounds!=case['bounds']:
                raise ValueError('Oracle scene does not match saved experiment')
            oracle=oracle_grid(scene,case['resolution'],study['body']['height'])
            base=np.asarray(baseline['states']).reshape(case['shape']);grid=np.asarray(selected['states']).reshape(case['shape'])
            conflict=(base==0)&(grid==1);traces=[];local=[];visuals={}
            by_id={f['id']:f for f in case['frames']}
            for frame_id in selected['selected_frames']:
                frame=by_id[frame_id];obs_path=ART/'observations'/case['id']/f'{frame_id:03d}.npz'
                obs=load_observation(obs_path)
                if obs.scene_id!=case['scene_id'] or observation_digest(obs)!=frame['observation_sha256']:
                    raise ValueError(f'Stale observation {frame_id}')
                if conversion is None:conversion=upstream_check(obs)
                key=prediction_key(obs.rgb,obs.K);pred_path=ART/'predictions'/(key+'.npz')
                metadata=json.loads((ART/'predictions'/(key+'.json')).read_text())
                if any(metadata.get(k)!=v for k,v in [('code_revision',CODE_REV),('model_revision',MODEL_REV),('adapter_revision',ADAPTER_REV)]):
                    raise ValueError(f'Prediction revision mismatch {frame_id}')
                with np.load(pred_path,allow_pickle=False) as saved:predicted=saved['depth']
                trace=trace_frame(obs,predicted,case['bounds'],case['resolution'],study['body']['height'])
                trace['metrics']['floor_supported_conflict_cells']=int((trace['floor_support']&conflict).sum())
                trace['metrics']['supported_conflict_cells']=int((trace['occupied_support']&conflict).sum())
                record={'case_id':case['id'],'frame_id':frame_id,'prediction_key':key,
                    'observation_sha256':sha(obs_path.read_bytes()),'prediction_sha256':sha(pred_path.read_bytes()),**trace['metrics']}
                records.append(record);local.append(record);traces.append(trace);visuals[frame_id]=(trace,obs.rgb,obs.depth,predicted)
            summary={'case_id':case['id'],'title':case['title'],'frames':len(traces),**summarize_support(traces,base,grid)}
            summary['support_risk']=support_risk(traces,base,grid,oracle.states)
            summary['oracle_states_sha256']=sha(oracle.states.astype(np.int8).tobytes())
            summary['floor_lift_pixels']=sum(r['floor_lift_pixels'] for r in local)
            summary['floor_valid_prediction_pixels']=sum(r['floor_valid_prediction_pixels'] for r in local)
            summaries.append(summary)
            # Diagnostic selection is declared; every frame remains in JSON.
            largest=max(local,key=lambda r:(r['floor_supported_conflict_cells'],-r['frame_id']))['frame_id']
            most=max(local,key=lambda r:(r['supported_conflict_cells'],-r['frame_id']))['frame_id']
            for frame_id in sorted({min(visuals),largest,most}):
                trace,rgb,reference_depth,predicted=visuals[frame_id]
                record=next(r for r in local if r['frame_id']==frame_id)
                token=sha((record['observation_sha256']+record['prediction_sha256']+json.dumps(sources,sort_keys=True)).encode())[:16]
                stem=f"{case['id']}-{frame_id:03d}-{token}"
                diagnostic_images(trace,stem,rgb,reference_depth,predicted)
                why='；'.join(label for match,label in [(frame_id==min(visuals),'固定首張'),(frame_id==largest,'最多地板支援分歧格'),(frame_id==most,'最多整體支援分歧格')] if match)
                panels.append({'title':case['title'],'id':frame_id,'selection':why,
                    'rgb':stem+'-rgb.png','reference':stem+'-reference.png','predicted':stem+'-predicted.png',
                    'error':stem+'-error.png','mask':stem+'-floor.png','metrics':record})
        except Exception as exc:
            failures.append({'case_id':case['id'],'error':str(exc)})
    result={'audit_revision':AUDIT_REV,'reference_assisted_evaluation':True,'study_sha256':sha(raw),
        'source_sha256':sources,'floor_tolerance_m':FLOOR_TOLERANCE_M,'height_m':study['body']['height'],
        'upstream_check':conversion,'summaries':summaries,'frames':records,'failures':failures,
        'runtime_seconds':time.perf_counter()-started,'inference_performed':False}
    (OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    write_report(result,panels)
    print(json.dumps({'summaries':summaries,'failures':failures,'upstream_check':conversion,'runtime_seconds':result['runtime_seconds']},ensure_ascii=False))
    if failures:raise SystemExit(1)

def write_report(result,panels):
    risk_note='以全部 DA3 障礙格為母體，依不同影格的端點支援數分組。Oracle 是同一場景完整三角形幾何的離散參考；RGB-D 基線仍可能未知。單影格與 oracle 障礙重疊比例的分母是全部單影格支援障礙格，不是路徑錯誤放行率；多次支援也不保證正確。沒有執行刪除、改成自由或重新規劃。'
    risk_sections=[];risk_lines=['## 單影格障礙是否可以刪除？','',risk_note,'']
    for s in result['summaries']:
        risk=s['support_risk'];single=next((g for g in risk['groups'] if g['supporting_frames']==1),None)
        fraction=risk['single_frame_oracle_occupied_fraction']
        description=(f"單影格支援的 {single['cells']} 格中，{single['oracle_occupied']} 格與 oracle 障礙重疊（{fraction:.1%}）。" if single else '沒有單影格支援障礙格，比例不適用。')
        risk_rows=[]
        risk_lines += [f"### {s['title']}",'',description,'',
            '| 支援影格數 | 全部障礙格 | Oracle 障礙 | Oracle 自由 | RGB-D 障礙 | RGB-D 自由 | RGB-D 未知 |',
            '|---:|---:|---:|---:|---:|---:|---:|']
        for g in risk['groups']:
            values=[g[k] for k in ['supporting_frames','cells','oracle_occupied','oracle_free','baseline_occupied','baseline_free','baseline_unknown']]
            risk_rows.append('<tr>'+''.join(f'<td>{v}</td>' for v in values)+'</tr>')
            risk_lines.append('| '+' | '.join(map(str,values))+' |')
        risk_lines.append('')
        risk_sections.append(f"<section><h3>{esc(s['title'])}</h3><p>{esc(description)}全部 DA3 障礙格：{risk['occupied_cells']}。</p><div class=table><table><thead><tr><th>支援影格數</th><th>全部障礙格</th><th>Oracle 障礙</th><th>Oracle 自由</th><th>RGB-D 障礙</th><th>RGB-D 自由</th><th>RGB-D 未知</th></tr></thead><tbody>{''.join(risk_rows)}</tbody></table></div></section>")
    risk_html='<section><h2>單影格障礙是否可以刪除？</h2><p>'+esc(risk_note)+'</p>'+''.join(risk_sections)+'</section>'
    rows=[]
    for s in result['summaries']:
        rows.append(f"<tr><th>{esc(s['title'])}</th><td>{s['conflict_cells']}</td><td>{s['floor_supported_conflict_cells']}</td><td>{s['floor_only_conflict_cells']}</td><td>{s['single_frame_supported_conflict_cells']}</td><td>{s['floor_lift_pixels']} / {s['floor_valid_prediction_pixels']}</td></tr>")
    figures=[]
    for p in panels:
        m=p['metrics'];caption=f"地板預測／參考深度比中位數 {m['floor_depth_ratio_median']:.3f}" if m['floor_depth_ratio_median'] is not None else '無有效地板深度比'
        imgs=''.join(f'<figure><img src="{esc(p[key])}" alt="{esc(label)}"><figcaption>{esc(label)}</figcaption></figure>' for key,label in
            [('rgb','原始 RGB'),('reference','合成參考深度（僅評估）'),('predicted','DA3 預測深度'),('error','深度誤差：藍低估／紅高估，±1 m'),('mask','紫紅：真地板像素的預測落入障礙高度／範圍')])
        figures.append(f"<section><h2>{esc(p['title'])} · F{p['id']}</h2><p>{esc(p['selection'])}；{esc(caption)}。本影格支援 {m['floor_supported_conflict_cells']} 個地板相關分歧格。</p><div class=images>{imgs}</div></section>")
    errors=''.join(f"<p>無法完成 {esc(f['case_id'])}：{esc(f['error'])}</p>" for f in result['failures'])
    check=result['upstream_check']
    check_text=f"固定官方工具核對：focal/300 最大差 {check['metric_max_error_m']:.2g} m；相機 Z→世界投影最大差 {check['world_projection_max_error_m']:.2g} m；未載入權重或執行推論。" if check else '官方工具核對未完成。'
    normal=next((s for s in result['summaries'] if s['case_id']=='replica-normal'),None)
    finding=(f"正常場景的 {normal['conflict_cells']} 個分歧格中，只有 {normal['floor_only_conflict_cells']} 格僅由真地板像素支援，地板抬升不是充分解釋。另有 {normal['single_frame_supported_conflict_cells']} 格只在一張影格中出現占據端點；目前 occupied-wins 規則會保留這些端點。這是融合對零星預測誤差敏感的線索，不能據此直接刪除障礙。" if normal else '正常案例未完成，不能據此歸因。')
    page=f'''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CareSpace 3D｜深度與障礙來源診斷</title>
<style>body{{margin:0;background:#eaf0f4;color:#152f43;font:15px/1.65 system-ui,"Microsoft JhengHei",sans-serif}}header,main{{max-width:1250px;margin:auto;padding:24px}}h1{{font-size:26px}}h2{{font-size:19px}}section{{margin:28px 0;padding-top:20px;border-top:1px solid #bdcdd5}}.images{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}}figure{{margin:0}}img{{width:100%;image-rendering:auto}}figcaption{{font-size:12px}}table{{width:100%;border-collapse:collapse;font-size:13px}}td,th{{padding:10px;border-bottom:1px solid #bdcdd5;text-align:left}}.table{{overflow:auto}}code{{overflow-wrap:anywhere}}a{{color:#09656a}}#validation{{font-weight:600}}[hidden]{{display:none}}@media(max-width:800px){{.images{{grid-template-columns:1fr 1fr}}header,main{{padding:16px}}}}</style>
<header><a href="/viewer/">返回通行工作台</a><h1>深度偏差如何進入障礙網格</h1><p>使用合成真值的事後診斷。這些地板標記不會輸入重建、校正深度或改變通行判定。</p><p id=validation>正在核對研究資料指紋…</p></header>
<main hidden><p>{esc(check_text)}</p><p>{esc(finding)}</p>{errors}<h2>全部觀測的來源追溯</h2><div class=table><table><thead><tr><th>案例</th><th>基線自由→DA3 障礙格</th><th>有真地板像素支援</th><th>僅有真地板像素支援</th><th>僅一張影格支援</th><th>地板預測進入障礙高度／有效地板像素</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p>「支援」表示預測深度反投影端點落入該障礙欄。多影格可重複支援同格；表中格數取聯集，不把像素或影格當獨立家庭。「僅有」排除任何非地板及無參考回波像素的共同支援。每個成功案例都已核對端點聯集與原存 DA3 障礙網格完全一致。</p>
<p>真地板以合成參考端點 |Y|≤0.0001 m 識別。預測端點須位於研究 XZ 範圍與既有高度體素內（Y 從 0.10 m 起，上界依設定向上取整）。無效預測不算成正確地板。深度比只描述偏差，未用它擬合或修正尺度。</p>
{risk_html}{''.join(figures)}<section><h2>可追溯性與限制</h2><p>逐影格完整統計、來源雜湊與失敗紀錄：<a href="audit.json">audit.json</a>。本頁只展示固定首張、地板支援分歧格數最高及整體支援分歧格數最高的影格，最高者是診斷選樣，非新的評估集。</p><p>這證明了所選資料中部分地板深度誤差如何支援障礙格，不能單憑此結果斷言模型根因、全域尺度失準或移除這些格後一定可通行。</p><p>Study SHA256：<code>{result['study_sha256']}</code></p></section></main>
<script type=module>const label=document.getElementById('validation');try{{const response=await fetch('../study.json',{{cache:'no-store'}});if(!response.ok)throw Error('無法讀取研究資料');const bytes=await response.arrayBuffer();const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');if(digest!=='{result['study_sha256']}')throw Error('研究資料已變更，請重新產生深度診斷');label.textContent='研究資料指紋相符 · 保存實驗的事後評估';document.querySelector('main').hidden=false}}catch(e){{label.textContent=e.message}}</script></html>'''
    (OUT/'index.html').write_text(page,encoding='utf8')
    lines=['# 深度與障礙來源診斷','',check_text,'','使用合成真值進行事後評估；沒有修正深度、重跑模型或調整門檻。','',finding,'',
        '| 案例 | 基線自由→DA3 障礙 | 地板支援 | 僅地板支援 | 抬升像素／有效地板像素 |','|---|---:|---:|---:|---:|']
    for s in result['summaries']:lines.append(f"| {s['title']} | {s['conflict_cells']} | {s['floor_supported_conflict_cells']} | {s['floor_only_conflict_cells']} | {s['floor_lift_pixels']}/{s['floor_valid_prediction_pixels']} |")
    lines+=['','成功案例的預測端點聯集均與原存 DA3 障礙網格完全一致。地板支援表示至少有一個真地板像素的預測端點落入該格；僅地板支援排除非地板與無參考回波的共同支援。',
        '固定首張、地板支援分歧格數最高及整體支援分歧格數最高的影格顯示於本機 HTML，完整逐影格數字、來源 SHA256 及失敗紀錄存於 audit.json。',
        '這是現有失敗案例的來源追溯，不能推論全域尺度失準，也沒有驗證移除地板誤差後的通行結果。','',
        f"失敗案例數：{len(result['failures'])}。",*[str(f) for f in result['failures']],
        f"Study SHA256: `{result['study_sha256']}`",'',
        '重現：`.venv/Scripts/python scripts/build_depth_audit.py`。本機開啟 `/artifacts/depth-audit/index.html`，畫面先核對 study 指紋，過期時拒絕展示。','']
    (ROOT/'docs/depth-audit.md').write_text('\n'.join(lines+risk_lines),encoding='utf8')

if __name__=='__main__':main()
