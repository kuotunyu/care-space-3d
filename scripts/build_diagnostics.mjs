import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {diagnose,chooseBaseline} from '../viewer/diagnostics.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const sha=data=>createHash('sha256').update(data).digest('hex');
const raw=fs.readFileSync(path.join(root,'artifacts/study.json')),study=JSON.parse(raw);
const sourceHashes=Object.fromEntries(['viewer/diagnostics.js','viewer/planning.js','scripts/build_diagnostics.mjs'].map(p=>[p,sha(fs.readFileSync(path.join(root,p)))]));
const results=[],failures=[],started=performance.now(),labels={passable:'可通行',blocked:'阻斷',unknown:'未知'};
for(const c of study.cases){
  for(const method of c.methods){
    if(method.id==='all')continue;
    const base=chooseBaseline(c.methods,method);
    if(!base){failures.push({case_id:c.id,method_id:method.id,reason:'No compatible RGB-D baseline / frame identities'});continue}
    try{
    results.push({case_id:c.id,scene_id:c.scene_id,split:c.split,case_label:c.title,method_label:method.label,baseline_label:base.label,
      radius:study.body.radius,start:method.result.start,goal:method.result.goal,
      diagnosis:diagnose(c,base,method,study.body.radius,method.result.start,method.result.goal)});
    }catch(error){failures.push({case_id:c.id,method_id:method.id,reason:error.message})}
  }
}
const output={schema_version:1,study_sha256:sha(raw),source_sha256:sourceHashes,node:process.version,runtime_seconds:(performance.now()-started)/1000,requested_comparisons:results.length+failures.length,failures,results};
fs.writeFileSync(path.join(root,'artifacts/diagnostics.json'),JSON.stringify(output,null,2)+'\n');
const lines=['# 方法差異診斷','',
  '由重建網格計算；基線不是完整真值，分歧率不是錯誤率。沒有用原始幾何修正模型。',
  'DA3 與同取樣策略的 RGB-D 比較；RGB-D 取樣方法與全部 RGB-D 比較，後者改變觀測子集。',
  '報告使用保存端點與預設圓柱半徑；介面診斷則隨目前端點／半徑重新計算。','',
  `開發與評估合計：${results.length} 組診斷可用，${failures.length} 組無法診斷；下表僅列 evaluation。`,
  ...failures.map(f=>`- 無法診斷 ${f.case_id}/${f.method_id}: ${f.reason}`),'',
  '| 案例 | 方法 ← 基線 | 同影格 | 判定（基線→方法） | 障礙分歧／共同已觀測格 | 已觀測→未知 | 未知→已觀測 | 基線路徑受阻／總中心 |',
  '|---|---|---|---|---:|---:|---:|---:|'];
for(const r of results.filter(r=>r.split==='evaluation')){
  const d=r.diagnosis;
  lines.push(`| ${r.case_label} | ${r.method_label} ← ${r.baseline_label} | ${d.same_frames?'是':'否'} | ${labels[d.baseline_status]}→${labels[d.selected_status]} | ${d.counts.conflict}/${d.known_both}${d.known_both?'':'（N/A）'} | ${d.counts.lost} | ${d.counts.gained} | ${d.path?`${d.path.blocked}/${d.path.total}`:'N/A'} |`);
}
lines.push('','障礙分歧指兩者都已觀測、但自由／障礙標籤相反；分母為共同已觀測格。',
  '觀測增減以全圖格數為母體，各 evaluation 圖有 4,800 格。完整三態轉移矩陣記錄於 JSON，列為基線、欄為目前方法，順序 unknown/free/occupied。',
  '路徑統計的分母是基線已知自由路徑中心數；基線無自由路徑則不適用，不能記成 0% 成功。',
  '單條基线路徑受阻不等於所有替代路徑都受阻；最終判定仍由完整四鄰接連通搜尋得到。','',
  '## 正常場景的 DA3 負例','');
for(const r of results.filter(r=>r.case_id==='replica-normal'&&r.diagnosis.selected_id.startsWith('da3-'))){
  const d=r.diagnosis,label=s=>({'-1':'未知',0:'自由',1:'障礙／邊界'})[s];
  lines.push(`- ${r.method_label}：起點圓柱中心 ${label(d.endpoints.selected[0])}，終點 ${label(d.endpoints.selected[1])}。`);
  lines.push(`  基線自由→目前障礙 ${d.matrix[1][2]} 格，基線障礙→目前自由 ${d.matrix[2][1]} 格。`);
  if(d.path)lines.push(`  基線自由路徑 ${d.path.total} 個中心中，${d.path.blocked} 個受障礙限制、${d.path.unknown} 個為未知；第一個受限中心 X/Z = ${JSON.stringify(d.path.first_restricted_center?.map(v=>+v.toFixed(4)))} m。`);
}
lines.push('','以上定位了占據／膨脹／連通階段的差異，尚不能把根因歸給單一影格、尺度偏差或特定家具。',
  '不依照這些 evaluation 負例調整門檻；未執行模型再訓練或未知姿態實驗。','',
  `Study SHA256: \`${output.study_sha256}\``,
  ...Object.entries(sourceHashes).map(([p,h])=>`${p} SHA256: \`${h}\``),'');
fs.writeFileSync(path.join(root,'docs/diagnostics.md'),lines.join('\n'));
console.log(JSON.stringify({comparisons:results.length,runtime_seconds:output.runtime_seconds,study_sha256:output.study_sha256}));
