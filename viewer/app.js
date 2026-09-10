import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { bfs, parseEndpoint, stateLookup } from './planning.js';
import { createRenderScheduler, disposeObject } from './rendering.js';
import { diagnose, chooseBaseline } from './diagnostics.js';

const moduleStartedAt=performance.now();
const COLORS={free:0x117d83,occupied:0xd66750,unknown:0xc19b43,narrow:0x886aa8,ink:0x152f43};
const $=id=>document.getElementById(id);
const ui=Object.fromEntries(['loadState','caseSelect','caseDescription','methodSelect','reconMode','oracleMode','sourceNote','radius','radiusValue','heightValue','assumption','pickStart','pickGoal','startX','startZ','goalX','goalZ','frameCount','frameCountValue','frameStrip','viewport','statusDot','resultStatus','resultReason','clearance','pathLength','resolution','metrics','comparisonBody','sceneId','splitFamily','gridShape','observationSection','frameDialog','frameDialogTitle','closeFrameDialog','dialogRgb','dialogDepth','dialogDepthMissing','dialogDepthLabel','resetQuery','frameSelection','viewSource','stageStatus','fitView','topView','showPoints','coverageBar','coverageSummary','pathLengthLabel'].map(id=>[id,$(id)]));
let study,currentCase,currentMethod,pick='start',oracle=false,frameLimit=0;
let scene,camera,renderer,controls,content,pathLine,markers,raycaster,mouse,groundPlane,oracleObject;
let contentRevision=0,observedPoints,requestRender=()=>{},renderCount=0;
let differenceOverlay=null,normalFloor=[];

try { init3D(); bind(); bindCoordinateInput(); loadStudy(); }
catch(error) { setFatal(`3D 視圖無法啟動（${error.message}）。請確認瀏覽器支援 WebGL，重新載入後再試。`); }

function bindCoordinateInput(){
  const names=['startX','startZ','goalX','goalZ'];
  for(const name of names)ui[name].addEventListener('input',()=>replan());
}

async function loadStudy(){
  try{
    const response=await fetch('/artifacts/study.json',{cache:'no-store'});
    if(!response.ok) throw new Error(`HTTP ${response.status}`);
    const raw=await response.text();study=JSON.parse(raw);document.body.dataset.studyBytes=response.headers.get('content-length')||String(new TextEncoder().encode(raw).byteLength);
    if(study?.schema_version!==1||!Array.isArray(study.cases)) throw new Error('不支援的資料格式');
    if(!study.cases.length){ setFatal('研究資料中沒有案例。請先產生 artifacts/study.json。'); return; }
    ui.loadState.textContent=`資料就緒 · ${study.cases.length} 案例`;
    ui.loadState.style.borderColor='#117d83';
    ui.radius.value=study.body?.radius ?? .3; ui.heightValue.textContent=fmtM(study.body?.height);
    ui.assumption.textContent=study.body?.assumption||'未提供通行模型說明。';
    ui.caseSelect.innerHTML=study.cases.map((c,i)=>`<option value="${i}">${esc(c.title||c.id)}</option>`).join('');
    const preferred=study.cases.findIndex(c=>c.id==='replica-normal');selectCase(preferred>=0?preferred:0);ui.caseSelect.value=String(preferred>=0?preferred:0);renderer.render(scene,camera);document.body.dataset.viewerReadyMs=(performance.now()-moduleStartedAt).toFixed(1);
  }catch(error){setFatal(`無法讀取 /artifacts/study.json（${error.message}）。請在專案根目錄啟動靜態伺服器。`)}
}

function setFatal(message){ui.loadState.textContent='資料載入失敗';ui.loadState.style.borderColor='#d66750';document.body.classList.add('fatal');const p=document.createElement('p');p.className='empty';p.textContent=message;document.querySelector('.workbench').append(p)}

function selectCase(index){
  currentCase=study.cases[index];
  $('inspectDa3').hidden=!currentCase.methods?.some(m=>m.id==='da3-all');
  $('sceneTitle').textContent=currentCase.title||currentCase.id;
  ui.caseDescription.textContent=currentCase.description||'';
  ui.methodSelect.innerHTML=(currentCase.methods||[]).map((m,i)=>`<option value="${i}">${esc(m.label||m.id)}</option>`).join('');
  ui.sceneId.textContent=currentCase.scene_id||'—';ui.splitFamily.textContent=[currentCase.split,currentCase.family].filter(Boolean).join(' / ')||'—';ui.gridShape.textContent=Array.isArray(currentCase.shape)?currentCase.shape.join(' × '):'—';ui.resolution.textContent=fmtM(currentCase.resolution);
  ui.radius.min=Math.max(.05,currentCase.resolution||.1); ui.radiusValue.textContent=fmtM(+ui.radius.value);
  frameLimit=(currentCase.frames||[]).length;ui.frameCount.max=frameLimit;ui.frameCount.value=frameLimit;ui.frameCountValue.textContent=`${frameLimit} / ${frameLimit}`;
  for(const id of ['methodSelect','radius','resetQuery','startX','startZ','goalX','goalZ','frameCount','reconMode','oracleMode','pickStart','pickGoal'])ui[id].disabled=!currentCase.methods?.length;
  if(!currentCase.methods?.length){currentMethod=null;clearContent();renderEmptyMethod();return}
  ui.viewSource.textContent=oracle?'參考幾何載入中…':'重建證據 · 已知相機姿態';
  selectMethod(0,true); fitCamera();
}

function selectMethod(index,resetEndpoints=false){
  currentMethod=currentCase.methods[index];
  ui.methodSelect.value=String(index);
  const r=currentMethod.result||{};
  if(resetEndpoints){setEndpoint('start',r.start||[currentCase.bounds[0],currentCase.bounds[1]]);setEndpoint('goal',r.goal||[currentCase.bounds[2],currentCase.bounds[3]])}
  renderScene();renderFrames();renderMetrics();renderComparison();replan();
}

function init3D(){
  scene=new THREE.Scene();scene.background=new THREE.Color(0xeaf0f4);
  camera=new THREE.PerspectiveCamera(42,1,.02,100);camera.position.set(5,5,5);
  renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;ui.viewport.append(renderer.domElement);
  controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.08;
  scene.add(new THREE.HemisphereLight(0xffffff,0x91a4af,2.4));const sun=new THREE.DirectionalLight(0xffffff,2);sun.position.set(3,7,4);scene.add(sun);
  content=new THREE.Group();markers=new THREE.Group();scene.add(content,markers);raycaster=new THREE.Raycaster();mouse=new THREE.Vector2();groundPlane=new THREE.Plane(new THREE.Vector3(0,1,0),0);
  requestRender=createRenderScheduler(()=>{
    if(document.hidden)return;
    controls.update();renderer.render(scene,camera);
    document.body.dataset.renderCount=String(++renderCount);
    document.body.dataset.geometryCount=String(renderer.info.memory.geometries);
    document.body.dataset.textureCount=String(renderer.info.memory.textures);
  });
  controls.addEventListener('change',requestRender);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)requestRender()});
  new ResizeObserver(resize).observe(ui.viewport);
  renderer.domElement.addEventListener('pointerdown',beginPointer);
}
let down;
function beginPointer(e){down=[e.clientX,e.clientY];renderer.domElement.addEventListener('pointerup',endPointer,{once:true})}
function endPointer(e){if(!currentMethod||e.button!==0||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const rect=renderer.domElement.getBoundingClientRect();mouse.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(mouse,camera);const p=new THREE.Vector3();if(raycaster.ray.intersectPlane(groundPlane,p)){setEndpoint(pick,[snap(p.x),snap(p.z)]);replan()}}
function resize(){const w=ui.viewport.clientWidth,h=ui.viewport.clientHeight;if(!w||!h)return;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);requestRender()}

function renderScene(){
  clearContent();if(!currentMethod)return;
  const [nx,nz]=currentCase.shape||[0,0],res=currentCase.resolution,[xmin,zmin]=currentCase.bounds,states=currentMethod.states||[];
  const mats={0:new THREE.MeshStandardMaterial({color:COLORS.free,transparent:true,opacity:.34,roughness:.8}),1:new THREE.MeshStandardMaterial({color:COLORS.occupied,transparent:true,opacity:.8,roughness:.75}),'-1':new THREE.MeshStandardMaterial({color:COLORS.unknown,transparent:true,opacity:.44,roughness:1})};
  const groups={0:[],1:[],'-1':[]};for(let ix=0;ix<nx;ix++)for(let iz=0;iz<nz;iz++)groups[states[ix*nz+iz]??-1].push([ix,iz]);
  for(const key of ['0','-1','1']){const h=key==='1'?.12:.018;const geo=new THREE.BoxGeometry(res*.9,h,res*.9),mesh=new THREE.InstancedMesh(geo,mats[key],groups[key].length);const m=new THREE.Matrix4();groups[key].forEach(([ix,iz],i)=>mesh.setMatrixAt(i,m.makeTranslation(xmin+(ix+.5)*res,h/2+(key==='1'?0:.02),zmin+(iz+.5)*res)));content.add(mesh)}
  addNarrowBand();
  normalFloor=[...content.children];
  const pos=currentMethod.points?.positions||[];
  if(pos.length){
    const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
    observedPoints=new THREE.Points(geo,new THREE.PointsMaterial({size:.045,color:0x345569,sizeAttenuation:true}));
    observedPoints.visible=ui.showPoints.checked;content.add(observedPoints);
  }
  const grid=new THREE.GridHelper(Math.max(nx*res,nz*res),Math.max(nx*res,nz*res),0x9daeb9,0xc2cfd7);grid.position.set((currentCase.bounds[0]+currentCase.bounds[2])/2,-.005,(currentCase.bounds[1]+currentCase.bounds[3])/2);content.add(grid);
  addFrameMarkers();if(oracle)loadOracle();requestRender();
}
function clearContent(){contentRevision++;for(const child of [...content.children])disposeObject(child);oracleObject=null;observedPoints=null;differenceOverlay=null;normalFloor=[];requestRender()}
function loadOracle(){
  if(!currentCase.reference_mesh){ui.sourceNote.textContent='此案例沒有可用的標註參考網格。';ui.viewSource.textContent='無參考網格 · 仍顯示重建';return}
  const requestedRevision=contentRevision;
  ui.sourceNote.textContent='完整來源幾何僅供視覺對照；通行判定仍使用所選方法的重建網格。';
  ui.viewSource.textContent='參考幾何載入中…';
  new GLTFLoader().load(resolveArtifact(currentCase.reference_mesh),g=>{
    if(!oracle||requestedRevision!==contentRevision){disposeObject(g.scene);return}
    oracleObject=g.scene;
    // Retain source materials so their textures are released with the whole hierarchy.
    oracleObject.traverse(o=>{if(o.isMesh)for(const m of (Array.isArray(o.material)?o.material:[o.material])){m.color.set(0x708798);m.transparent=true;m.opacity=.35;m.wireframe=true}});
    content.add(oracleObject);ui.viewSource.textContent='完整參考幾何疊加 · 非重建成果';requestRender();
  },undefined,()=>{if(requestedRevision===contentRevision){ui.sourceNote.textContent='標註參考網格載入失敗；重建證據仍可檢視。';ui.viewSource.textContent='參考載入失敗 · 仍顯示重建'}});
}
function addFrameMarkers(){const selected=new Set(currentMethod.selected_frames||[]);for(const f of (currentCase.frames||[]).slice(0,frameLimit)){if(!Array.isArray(f.position)||f.position.length<3)continue;const marker=new THREE.Mesh(new THREE.ConeGeometry(.045,.13,4),new THREE.MeshStandardMaterial({color:selected.has(f.id)?COLORS.free:COLORS.ink,transparent:true,opacity:selected.has(f.id)?.95:.38}));marker.position.set(...f.position);marker.rotation.x=Math.PI;content.add(marker)}}
function addNarrowBand(){const [nx,nz]=currentCase.shape,res=currentCase.resolution,states=currentMethod.states||[],obstacles=[],cells=[];for(let x=0;x<nx;x++)for(let z=0;z<nz;z++)if(states[x*nz+z]===1)obstacles.push([x,z]);for(let x=0;x<nx;x++)for(let z=0;z<nz;z++){if(states[x*nz+z]!==0)continue;let clearance=Math.min((x+1)*res,(z+1)*res,(nx-x)*res,(nz-z)*res);for(const [ox,oz] of obstacles)clearance=Math.min(clearance,Math.hypot((x-ox)*res,(z-oz)*res));clearance=Math.max(0,clearance-res/Math.SQRT2);if(clearance>=.3&&clearance<.6)cells.push([x,z])}if(!cells.length)return;const mesh=new THREE.InstancedMesh(new THREE.BoxGeometry(res*.72,.012,res*.72),new THREE.MeshStandardMaterial({color:COLORS.narrow,transparent:true,opacity:.88}),cells.length),m=new THREE.Matrix4();cells.forEach(([x,z],i)=>mesh.setMatrixAt(i,m.makeTranslation(currentCase.bounds[0]+(x+.5)*res,.052,currentCase.bounds[1]+(z+.5)*res)));content.add(mesh)}

function replan(){
  if(!currentMethod)return;
  const start=getEndpoint('start'),goal=getEndpoint('goal'),radius=+ui.radius.value;
  for(const kind of ['start','goal'])for(const axis of ['X','Z'])ui[kind+axis].setAttribute('aria-invalid',String(!getEndpoint(kind)));
  ui.radiusValue.textContent=fmtM(radius);
  if(!start||!goal){
    drawPath([],'unknown');for(const child of [...markers.children])disposeObject(child);
    ui.resultStatus.textContent=ui.stageStatus.textContent='待輸入';ui.resultReason.textContent='請填入完整、有限的 X / Z 座標；空白不會自動當成 0。';
    ui.statusDot.style.background='#607585';ui.stageStatus.dataset.status='invalid';
    ui.clearance.textContent=ui.pathLength.textContent='—';updateDiagnostics();requestRender();return;
  }
  const blocked=stateLookup(currentCase,currentMethod.states,radius),s=worldCell(start),g=worldCell(goal);let status='unknown',path=[],reason='端點或路徑穿越未觀測區域。';
  if(!s||!g||blocked(s[0],s[1])===1||blocked(g[0],g[1])===1){status='blocked';reason='端點位於障礙膨脹區或研究邊界外。'}else{path=bfs(s,g,v=>v===0,blocked);if(path.length){status='passable';reason='已知自由空間存在四鄰接通路。'}else{const optimistic=bfs(s,g,v=>v!==1,blocked);if(!optimistic.length){status='blocked';reason='即使允許穿越未知區，仍無可連通路徑。'}else{path=optimistic}}}
  const worldPath=path.map(([ix,iz])=>cellWorld(ix,iz));drawPath(worldPath,status);drawMarkers(start,goal);
  const clearance=status==='passable'&&path.length?pathClearance(path):null;ui.resultStatus.textContent={passable:'可通行',blocked:'阻斷',unknown:'未知'}[status];ui.resultReason.textContent=reason;ui.statusDot.style.background={passable:'#117d83',blocked:'#d66750',unknown:'#c19b43'}[status];ui.clearance.textContent=clearance==null?'—':fmtM(clearance);ui.pathLength.textContent=worldPath.length?fmtM((worldPath.length-1)*currentCase.resolution):'—';
  ui.stageStatus.textContent=ui.resultStatus.textContent;ui.stageStatus.dataset.status=status;
  ui.pathLengthLabel.textContent=status==='unknown'?'候選路線長度':'路徑長度';updateDiagnostics();requestRender();
}

function updateDiagnostics(){
  if(differenceOverlay){disposeObject(differenceOverlay);differenceOverlay=null}
  for(const object of normalFloor)object.visible=true;
  $('normalLegend').hidden=false;$('differenceLegend').hidden=true;$('differenceSource').hidden=true;
  const baseline=currentMethod&&chooseBaseline(currentCase.methods,currentMethod),start=getEndpoint('start'),goal=getEndpoint('goal');
  if(!baseline)$('showDifference').checked=false;
  $('showDifference').disabled=!baseline||!start||!goal;
  if(!baseline||!start||!goal){
    $('diagnosticPair').textContent=!currentMethod?'無方法資料':!baseline?'目前方法沒有可配對的 RGB-D 基線；可切換 DA3 或選樣方法。':'請先填入完整端點。';
    $('diagnosticDetails').replaceChildren();requestRender();return;
  }
  try{
    const d=diagnose(currentCase,baseline,currentMethod,+ui.radius.value,start,goal),labels={'-1':'未知',0:'自由',1:'障礙／邊界'};
    $('diagnosticPair').textContent=`${baseline.label} → ${currentMethod.label}；${d.same_frames?'相同觀測影格':'觀測子集不同'}`;
    const p=d.path,location=p?.first_restricted_center?.map(v=>v.toFixed(2)).join(', ');
    const rows=[`共同已觀測格中的障礙分歧：${d.counts.conflict} / ${d.known_both}（${d.known_conflict_fraction==null?'N/A':percent(d.known_conflict_fraction)}）`,
      `基線自由→目前障礙：${d.matrix[1][2]} 格；基線障礙→目前自由：${d.matrix[2][1]} 格。`,
      `已觀測→未知：${d.counts.lost} 格；未知→已觀測：${d.counts.gained} 格（全圖 ${d.total} 格）`,
      `目前方法的圓柱中心：起點 ${labels[d.endpoints.selected[0]]}，終點 ${labels[d.endpoints.selected[1]]}。`,
      p?`沿基線自由路徑的 ${p.total} 個中心，目前方法有 ${p.blocked} 個受障礙限制、${p.unknown} 個為未知。${location?`第一個受限中心 X/Z = (${location}) m。`:''}`:'基線沒有已知自由路徑，路徑局部統計不適用。',
      '單條基线路徑受限不代表沒有其他路徑；目前判定另由完整連通搜尋得出。'];
    $('diagnosticDetails').replaceChildren(...rows.map(text=>{const p=document.createElement('p');p.textContent=text;return p}));
    if($('showDifference').checked){
      differenceOverlay=new THREE.Group();content.add(differenceOverlay);
      const colors={conflict:0xa5457c,lost:0xa17b28,gained:0x2874a8},res=currentCase.resolution,nz=currentCase.shape[1];
      for(const [kind,indices] of Object.entries(d.groups)){
        if(!indices.length)continue;
        const mesh=new THREE.InstancedMesh(new THREE.BoxGeometry(res*.9,.016,res*.9),new THREE.MeshBasicMaterial({color:colors[kind]}),indices.length),matrix=new THREE.Matrix4();
        indices.forEach((index,i)=>{const [x,z]=cellWorld(Math.floor(index/nz),index%nz);mesh.setMatrixAt(i,matrix.makeTranslation(x,.055,z))});differenceOverlay.add(mesh);
      }
      for(const object of normalFloor)object.visible=false;
      $('normalLegend').hidden=true;$('differenceLegend').hidden=false;$('differenceSource').hidden=false;
    }
  }catch(error){$('diagnosticPair').textContent=`無法比較：${error.message}`;$('diagnosticDetails').replaceChildren();$('showDifference').disabled=true}
  requestRender();
}
function pathClearance(path){const [nx,nz]=currentCase.shape,res=currentCase.resolution,states=currentMethod.states||[];let best=Infinity;for(const [x,z] of path){best=Math.min(best,(x+1)*res,(z+1)*res,(nx-x)*res,(nz-z)*res);for(let ox=0;ox<nx;ox++)for(let oz=0;oz<nz;oz++)if((states[ox*nz+oz]??-1)!==0)best=Math.min(best,Math.hypot((x-ox)*res,(z-oz)*res))}return Math.max(0,best-res/Math.SQRT2)}
function drawPath(points,status){
  if(pathLine){disposeObject(pathLine);pathLine=null}
  if(!points.length)return;
  const material=status==='passable'?new THREE.LineBasicMaterial({color:0x085358}):new THREE.LineDashedMaterial({color:0x8a641a,dashSize:.13,gapSize:.10});
  pathLine=new THREE.Line(new THREE.BufferGeometry().setFromPoints(points.map(([x,z])=>new THREE.Vector3(x,.09,z))),material);
  pathLine.computeLineDistances();scene.add(pathLine);
}
function drawMarkers(start,goal){
  for(const child of [...markers.children])disposeObject(child);
  for(const [p,label,color] of [[start,'S',0x117d83],[goal,'G',0xd66750]]){
    const mesh=new THREE.Mesh(new THREE.CylinderGeometry(.08,.08,.08,24),new THREE.MeshStandardMaterial({color}));
    mesh.position.set(p[0],.08,p[1]);markers.add(mesh);
    const ring=new THREE.Mesh(new THREE.RingGeometry(+ui.radius.value-.012,+ui.radius.value+.012,48),new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide}));
    ring.rotation.x=-Math.PI/2;ring.position.set(p[0],.065,p[1]);markers.add(ring);
    const canvas=document.createElement('canvas');canvas.width=64;canvas.height=64;
    const context=canvas.getContext('2d');context.fillStyle='#152f43';context.font='bold 48px system-ui';context.textAlign='center';context.fillText(label,32,49);
    const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(canvas),depthTest:false}));
    sprite.position.set(p[0],.45,p[1]);sprite.scale.set(.42,.42,1);markers.add(sprite);
  }
}

function renderFrames(){const frames=currentCase.frames||[],selected=new Set(currentMethod.selected_frames||[]),learned=currentMethod.id.startsWith('da3-');ui.observationSection.hidden=!frames.length;ui.frameCountValue.textContent=`${frameLimit} / ${frames.length}`;ui.frameStrip.innerHTML=frames.slice(0,frameLimit).map(f=>{const depth=learned?f.learned_depth_preview:f.depth_preview,depthLabel=learned?'預測深度':'感測深度',preview=depth?`<img src="${esc(resolveArtifact(depth))}" alt="">`:`<span class="thumb-missing">無預覽</span>`;return `<button class="frame ${selected.has(f.id)?'active':''}" data-frame-id="${f.id}" aria-label="開啟影格 ${f.id} 的 RGB 與${depthLabel}大圖" title="影格 ${f.id}：左 RGB，右${depthLabel}" type="button"><span class="previews"><span><img src="${esc(resolveArtifact(f.rgb))}" alt=""><em>RGB</em></span><span>${preview}<em>${depthLabel}</em></span></span><span class="frame-id">F${f.id}</span></button>`}).join('')}
function renderMetrics(){
  const entries=Object.entries(currentMethod.metrics||{});
  ui.metrics.innerHTML=entries.length?entries.map(([k,v])=>`<div><dt>${esc(labelMetric(k))}</dt><dd title="${esc(formatMetric(v,k,false))}">${esc(formatMetric(v,k,true))}</dd></div>`).join(''):'<div><dt>方法未提供量測</dt><dd>—</dd></div>';
  const states=currentMethod.states||[],total=states.length;
  const fractions=[0,1,-1].map(state=>total?states.filter(v=>v===state).length/total:0);
  ui.coverageBar.innerHTML=fractions.map((value,i)=>`<span class="${['free','occupied','unknown'][i]}" style="width:${value*100}%"></span>`).join('');
  ui.coverageSummary.textContent=total?`自由 ${percent(fractions[0])} · 障礙 ${percent(fractions[1])} · 未知 ${percent(fractions[2])}`:'尚無網格證據';
  ui.frameSelection.textContent=`重建使用 ${currentMethod.selected_frames?.length??0} / ${currentCase.frames?.length??0} 張影格`;
}
function renderComparison(){ui.comparisonBody.innerHTML=(currentCase.methods||[]).map((m,index)=>{const x=m.metrics||{},status={passable:'可通',blocked:'阻斷',unknown:'未知'}[m.result?.status]||'—';return `<tr class="${m===currentMethod?'current':''}"><td><button type="button" data-method-index="${index}" aria-pressed="${m===currentMethod}">${esc(m.label||m.id)}</button></td><td class="status-${esc(m.result?.status)}">${status}</td><td>${m.selected_frames?.length??'—'}</td><td>${percent(x.observed_fraction)}</td><td>${compactNumber(x.runtime_seconds)}</td><td>${x.depth_mae_m==null?'—':compactNumber(x.depth_mae_m)+' m'}</td></tr>`}).join('')}
function renderEmptyMethod(){
  drawPath([],'unknown');for(const child of [...markers.children])disposeObject(child);
  ui.resultStatus.textContent=ui.stageStatus.textContent='無方法資料';ui.stageStatus.dataset.status='invalid';
  ui.resultReason.textContent='此案例沒有可檢視的重建方法。請切換其他案例。';ui.statusDot.style.background='#607585';
  ui.viewSource.textContent='無重建證據';ui.clearance.textContent=ui.pathLength.textContent='—';
  for(const id of ['metrics','frameStrip','comparisonBody','coverageBar'])ui[id].replaceChildren();
  ui.coverageSummary.textContent='尚無網格證據';ui.observationSection.hidden=true;requestRender();
  updateDiagnostics();
}
function bind(){
  $('showDifference').addEventListener('change',updateDiagnostics);
  $('inspectDa3').addEventListener('click',()=>{const index=currentCase.methods.findIndex(m=>m.id==='da3-all');if(index>=0){$('showDifference').checked=true;ui.showPoints.checked=false;selectMethod(index);fitCamera(true)}});
  ui.caseSelect.addEventListener('change',()=>selectCase(+ui.caseSelect.value));
  ui.methodSelect.addEventListener('change',()=>selectMethod(+ui.methodSelect.value));
  ui.comparisonBody.addEventListener('click',e=>{const button=e.target.closest('[data-method-index]');if(button)selectMethod(+button.dataset.methodIndex)});
  ui.radius.addEventListener('input',()=>replan());
  ui.frameCount.addEventListener('input',()=>{frameLimit=+ui.frameCount.value;renderFrames();renderScene();replan()});
  ui.resetQuery.addEventListener('click',()=>{ui.radius.value=study.body.radius;setEndpoint('start',currentMethod.result.start);setEndpoint('goal',currentMethod.result.goal);replan()});
  ui.fitView.addEventListener('click',()=>fitCamera());ui.topView.addEventListener('click',()=>fitCamera(true));
  ui.showPoints.addEventListener('change',()=>{if(observedPoints)observedPoints.visible=ui.showPoints.checked;requestRender()});
  for(const id of ['startX','startZ','goalX','goalZ'])ui[id].addEventListener('change',()=>replan());
  ui.pickStart.addEventListener('click',()=>setPick('start'));ui.pickGoal.addEventListener('click',()=>setPick('goal'));
  ui.reconMode.addEventListener('click',()=>setOracle(false));ui.oracleMode.addEventListener('click',()=>setOracle(true));
  ui.frameStrip.addEventListener('click',e=>{const button=e.target.closest('[data-frame-id]');if(button)openFrameDialog(+button.dataset.frameId)});
  ui.closeFrameDialog.addEventListener('click',()=>ui.frameDialog.close());
  ui.viewport.addEventListener('keydown',e=>{
    if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)||!currentMethod)return;
    e.preventDefault();const p=getEndpoint(pick),d=currentCase.resolution;if(!p)return;
    p[0]+=e.key==='ArrowLeft'?-d:e.key==='ArrowRight'?d:0;p[1]+=e.key==='ArrowUp'?-d:e.key==='ArrowDown'?d:0;
    setEndpoint(pick,p);replan();
  });
}
function openFrameDialog(id){const f=(currentCase.frames||[]).find(frame=>frame.id===id);if(!f)return;const learned=currentMethod.id.startsWith('da3-'),depth=learned?f.learned_depth_preview:f.depth_preview,label=learned?'預測深度':'感測深度';ui.frameDialogTitle.textContent=`影格 ${id} · ${currentMethod.label||currentMethod.id}`;ui.dialogRgb.src=resolveArtifact(f.rgb);ui.dialogRgb.alt=`影格 ${id} RGB 大圖`;ui.dialogDepthLabel.textContent=label;ui.dialogDepth.hidden=!depth;ui.dialogDepthMissing.hidden=!!depth;if(depth){ui.dialogDepth.src=resolveArtifact(depth);ui.dialogDepth.alt=`影格 ${id} ${label}大圖`}else{ui.dialogDepth.removeAttribute('src');ui.dialogDepth.alt=''}ui.frameDialog.showModal()}
function setPick(v){pick=v;ui.pickStart.classList.toggle('active',v==='start');ui.pickGoal.classList.toggle('active',v==='goal');ui.pickStart.setAttribute('aria-pressed',String(v==='start'));ui.pickGoal.setAttribute('aria-pressed',String(v==='goal'))}
function setOracle(v){oracle=v;ui.reconMode.classList.toggle('active',!v);ui.oracleMode.classList.toggle('active',v);ui.oracleMode.setAttribute('aria-pressed',String(v));ui.reconMode.setAttribute('aria-pressed',String(!v));ui.sourceNote.textContent=v?'完整來源幾何僅供視覺對照；通行判定仍使用所選方法的重建網格。':'顯示有限觀測所重建的證據。';ui.viewSource.textContent=v?'參考幾何載入中…':'重建證據 · 已知相機姿態';ui.viewSource.classList.toggle('reference',v);renderScene();replan()}
function setEndpoint(kind,p){ui[kind+'X'].value=(+p[0]).toFixed(2);ui[kind+'Z'].value=(+p[1]).toFixed(2)}
function getEndpoint(kind){return parseEndpoint(ui[kind+'X'].value,ui[kind+'Z'].value)}
function worldCell([x,z]){const [xmin,zmin,xmax,zmax]=currentCase.bounds,res=currentCase.resolution;if(!Number.isFinite(x)||!Number.isFinite(z)||x<xmin||z<zmin||x>=xmax||z>=zmax)return null;return[Math.floor((x-xmin)/res),Math.floor((z-zmin)/res)]}function cellWorld(ix,iz){return[currentCase.bounds[0]+(ix+.5)*currentCase.resolution,currentCase.bounds[1]+(iz+.5)*currentCase.resolution]}function snap(v){return Math.round(v/currentCase.resolution)*currentCase.resolution}
function fitCamera(top=false){
  if(!currentCase)return;
  resize();const [xmin,zmin,xmax,zmax]=currentCase.bounds,cx=(xmin+xmax)/2,cz=(zmin+zmax)/2,size=Math.max(xmax-xmin,zmax-zmin),scale=Math.max(1,1.08/camera.aspect);
  camera.up.set(0,1,0);controls.target.set(cx,.3,cz);
  if(top){camera.position.set(cx,size*1.55*scale,cz+.001)}else{camera.position.set(cx+size*1.05*scale,size*.95*scale,cz+size*1.05*scale)}
  camera.near=Math.max(.01,size/1000);camera.far=Math.max(100,size*10);camera.updateProjectionMatrix();controls.update();requestRender();
}
function resolveArtifact(path){if(!path)return'';if(/^(https?:|data:|\/)/.test(path))return path;return'/'+path.replaceAll('\\','/').replace(/^\.\//,'')}
function fmtM(v){return Number.isFinite(+v)?`${(+v).toFixed(2)} m`:'—'}function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function compactNumber(v){return Number.isFinite(+v)?(+v).toFixed(3):'—'}function percent(v){return Number.isFinite(+v)?`${(+v*100).toFixed(1)}%`:'—'}function formatMetric(v,k,compact=false){if(v==null)return'—';if(compact&&/(revision|sha256|fingerprint)/.test(k)&&String(v).length>14)return String(v).slice(0,10)+'…';if(typeof v==='number'){if(/fraction$/.test(k))return percent(v);return Number.isInteger(v)?String(v):v.toFixed(4)}if(typeof v==='object')return JSON.stringify(v);return String(v)}function labelMetric(k){return ({observation_count:'觀測數',candidate_count:'候選影格',observed_fraction:'已觀測比例',unknown_fraction:'未知比例',free_fraction:'自由比例',occupied_fraction:'障礙比例',geometry_occupied_iou:'障礙 IoU',clearance_error_m:'淨空誤差（m）',runtime_seconds:'執行時間（秒）',peak_vram_mb:'峰值 VRAM（MB）',device:'運算裝置',reconstruction_failed:'重建失敗',observation_failure_fraction:'觀測失敗比例',pose_source:'姿態來源',pose_failure_rate:'姿態失敗率',oracle_status:'Oracle 判定',depth_mae_m:'深度 MAE（m）',depth_abs_rel:'深度 AbsRel',model_revision:'模型版本',code_revision:'程式版本',scale_alignment:'尺度對齊'})[k]||k.replaceAll('_',' ')}
