import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { bfs } from './planning.js';

const moduleStartedAt=performance.now();
const COLORS={free:0x117d83,occupied:0xd66750,unknown:0xc19b43,narrow:0x886aa8,ink:0x152f43};
const $=id=>document.getElementById(id);
const ui=Object.fromEntries(['loadState','caseSelect','caseDescription','methodSelect','reconMode','oracleMode','sourceNote','radius','radiusValue','heightValue','assumption','pickStart','pickGoal','startX','startZ','goalX','goalZ','frameCount','frameCountValue','frameStrip','viewport','statusDot','resultStatus','resultReason','clearance','pathLength','resolution','metrics','comparisonBody','sceneId','splitFamily','gridShape','observationSection','frameDialog','frameDialogTitle','closeFrameDialog','dialogRgb','dialogDepth','dialogDepthMissing','dialogDepthLabel'].map(id=>[id,$(id)]));
let study,currentCase,currentMethod,pick='start',oracle=false,frameLimit=0;
let scene,camera,renderer,controls,content,pathLine,markers,raycaster,mouse,groundPlane,oracleObject;

init3D(); bind(); bindCoordinateInput(); loadStudy();

function bindCoordinateInput(){
  const names=['startX','startZ','goalX','goalZ'];
  for(const name of names)ui[name].addEventListener('input',()=>{
    if(names.every(key=>ui[key].value.trim()!==''&&Number.isFinite(+ui[key].value)))replan(false);
  });
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
  ui.caseDescription.textContent=currentCase.description||'';
  ui.methodSelect.innerHTML=(currentCase.methods||[]).map((m,i)=>`<option value="${i}">${esc(m.label||m.id)}</option>`).join('');
  ui.sceneId.textContent=currentCase.scene_id||'—';ui.splitFamily.textContent=[currentCase.split,currentCase.family].filter(Boolean).join(' / ')||'—';ui.gridShape.textContent=Array.isArray(currentCase.shape)?currentCase.shape.join(' × '):'—';ui.resolution.textContent=fmtM(currentCase.resolution);
  ui.radius.min=Math.max(.05,currentCase.resolution||.1); ui.radiusValue.textContent=fmtM(+ui.radius.value);
  frameLimit=(currentCase.frames||[]).length;ui.frameCount.max=frameLimit;ui.frameCount.value=frameLimit;ui.frameCountValue.textContent=`${frameLimit} / ${frameLimit}`;
  if(!currentCase.methods?.length){currentMethod=null;clearContent();renderEmptyMethod();return}
  selectMethod(0,true); fitCamera();
}

function selectMethod(index,resetEndpoints=false){
  currentMethod=currentCase.methods[index];
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
  new ResizeObserver(resize).observe(ui.viewport);renderer.domElement.addEventListener('pointerdown',beginPointer);renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera)});
}
let down;
function beginPointer(e){down=[e.clientX,e.clientY];renderer.domElement.addEventListener('pointerup',endPointer,{once:true})}
function endPointer(e){if(!currentMethod||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const rect=renderer.domElement.getBoundingClientRect();mouse.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(mouse,camera);const p=new THREE.Vector3();if(raycaster.ray.intersectPlane(groundPlane,p)){setEndpoint(pick,[snap(p.x),snap(p.z)]);syncEndpointFields();replan()}}
function resize(){const w=ui.viewport.clientWidth,h=ui.viewport.clientHeight;if(!w||!h)return;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false)}

function renderScene(){
  clearContent();if(!currentMethod)return;
  const [nx,nz]=currentCase.shape||[0,0],res=currentCase.resolution,[xmin,zmin]=currentCase.bounds,states=currentMethod.states||[];
  const mats={0:new THREE.MeshStandardMaterial({color:COLORS.free,transparent:true,opacity:.34,roughness:.8}),1:new THREE.MeshStandardMaterial({color:COLORS.occupied,transparent:true,opacity:.8,roughness:.75}),'-1':new THREE.MeshStandardMaterial({color:COLORS.unknown,transparent:true,opacity:.44,roughness:1})};
  const groups={0:[],1:[],'-1':[]};for(let ix=0;ix<nx;ix++)for(let iz=0;iz<nz;iz++)groups[states[ix*nz+iz]??-1].push([ix,iz]);
  for(const key of ['0','-1','1']){const h=key==='1'?.12:.018;const geo=new THREE.BoxGeometry(res*.9,h,res*.9),mesh=new THREE.InstancedMesh(geo,mats[key],groups[key].length);const m=new THREE.Matrix4();groups[key].forEach(([ix,iz],i)=>mesh.setMatrixAt(i,m.makeTranslation(xmin+(ix+.5)*res,h/2+(key==='1'?0:.02),zmin+(iz+.5)*res)));content.add(mesh)}
  addNarrowBand();
  const pos=currentMethod.points?.positions||[],col=currentMethod.points?.colors||[];if(pos.length){const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));if(col.length===pos.length)geo.setAttribute('color',new THREE.Float32BufferAttribute(col,3));content.add(new THREE.Points(geo,new THREE.PointsMaterial({size:.05,vertexColors:col.length===pos.length,color:col.length===pos.length?0xffffff:0x152f43,sizeAttenuation:true})))}
  const grid=new THREE.GridHelper(Math.max(nx*res,nz*res),Math.max(nx,nz),0x8fa3ae,0xb9c6cd);grid.position.set((currentCase.bounds[0]+currentCase.bounds[2])/2,.025,(currentCase.bounds[1]+currentCase.bounds[3])/2);content.add(grid);
  addFrameMarkers();if(oracle)loadOracle();
}
function clearContent(){while(content.children.length){const o=content.children.pop();o.geometry?.dispose();if(Array.isArray(o.material))o.material.forEach(m=>m.dispose());else o.material?.dispose()}oracleObject=null}
function loadOracle(){if(!currentCase.reference_mesh){ui.sourceNote.textContent='此案例沒有可用的標註參考網格。';return}const requestedCase=currentCase;new GLTFLoader().load(resolveArtifact(currentCase.reference_mesh),g=>{if(!oracle||requestedCase!==currentCase)return;oracleObject=g.scene;oracleObject.traverse(o=>{if(o.isMesh)o.material=new THREE.MeshStandardMaterial({color:0x708798,transparent:true,opacity:.46,wireframe:true})});content.add(oracleObject)},undefined,()=>{if(requestedCase===currentCase)ui.sourceNote.textContent='標註參考網格載入失敗；重建證據仍可檢視。'})}
function addFrameMarkers(){const selected=new Set(currentMethod.selected_frames||[]);for(const f of (currentCase.frames||[]).slice(0,frameLimit)){if(!Array.isArray(f.position)||f.position.length<3)continue;const marker=new THREE.Mesh(new THREE.ConeGeometry(.045,.13,4),new THREE.MeshStandardMaterial({color:selected.has(f.id)?COLORS.free:COLORS.ink,transparent:true,opacity:selected.has(f.id)?.95:.38}));marker.position.set(...f.position);marker.rotation.x=Math.PI;content.add(marker)}}
function addNarrowBand(){const [nx,nz]=currentCase.shape,res=currentCase.resolution,states=currentMethod.states||[],obstacles=[],cells=[];for(let x=0;x<nx;x++)for(let z=0;z<nz;z++)if(states[x*nz+z]===1)obstacles.push([x,z]);for(let x=0;x<nx;x++)for(let z=0;z<nz;z++){if(states[x*nz+z]!==0)continue;let clearance=Math.min((x+1)*res,(z+1)*res,(nx-x)*res,(nz-z)*res);for(const [ox,oz] of obstacles)clearance=Math.min(clearance,Math.hypot((x-ox)*res,(z-oz)*res));clearance=Math.max(0,clearance-res/Math.SQRT2);if(clearance>=.3&&clearance<.6)cells.push([x,z])}if(!cells.length)return;const mesh=new THREE.InstancedMesh(new THREE.BoxGeometry(res*.72,.012,res*.72),new THREE.MeshStandardMaterial({color:COLORS.narrow,transparent:true,opacity:.88}),cells.length),m=new THREE.Matrix4();cells.forEach(([x,z],i)=>mesh.setMatrixAt(i,m.makeTranslation(currentCase.bounds[0]+(x+.5)*res,.052,currentCase.bounds[1]+(z+.5)*res)));content.add(mesh)}

function replan(formatFields=true){
  if(!currentMethod)return;if(formatFields)syncEndpointFields();const start=getEndpoint('start'),goal=getEndpoint('goal'),radius=+ui.radius.value;ui.radiusValue.textContent=fmtM(radius);
  const blocked=classifyCenters(radius),s=worldCell(start),g=worldCell(goal);let status='unknown',path=[],reason='端點或路徑穿越未觀測區域。';
  if(!s||!g||blocked(s[0],s[1])===1||blocked(g[0],g[1])===1){status='blocked';reason='端點位於障礙膨脹區或研究邊界外。'}else{path=bfs(s,g,v=>v===0,blocked);if(path.length){status='passable';reason='已知自由空間存在四鄰接通路。'}else{const optimistic=bfs(s,g,v=>v!==1,blocked);if(!optimistic.length){status='blocked';reason='即使允許穿越未知區，仍無可連通路徑。'}else{path=optimistic}}}
  const worldPath=path.map(([ix,iz])=>cellWorld(ix,iz));drawPath(worldPath,status);drawMarkers(start,goal);
  const clearance=status==='passable'&&path.length?pathClearance(path):null;ui.resultStatus.textContent={passable:'可通行',blocked:'阻斷',unknown:'未知'}[status];ui.resultReason.textContent=reason;ui.statusDot.style.background={passable:'#117d83',blocked:'#d66750',unknown:'#c19b43'}[status];ui.clearance.textContent=clearance==null?'—':fmtM(clearance);ui.pathLength.textContent=worldPath.length?fmtM((worldPath.length-1)*currentCase.resolution):'—';
}

function classifyCenters(radius){const [nx,nz]=currentCase.shape,res=currentCase.resolution,states=currentMethod.states||[],threshold=radius+Math.SQRT2*res;return(ix,iz)=>{if(ix<0||iz<0||ix>=nx||iz>=nz)return 1;let unknown=false;const reach=Math.ceil(threshold/res);for(let dx=-reach;dx<=reach;dx++)for(let dz=-reach;dz<=reach;dz++){if(Math.hypot(dx*res,dz*res)>threshold)continue;const x=ix+dx,z=iz+dz;if(x<0||z<0||x>=nx||z>=nz)return 1;const v=states[x*nz+z]??-1;if(v===1)return 1;if(v===-1)unknown=true}return unknown?-1:0}}
function pathClearance(path){const [nx,nz]=currentCase.shape,res=currentCase.resolution,states=currentMethod.states||[];let best=Infinity;for(const [x,z] of path){best=Math.min(best,(x+1)*res,(z+1)*res,(nx-x)*res,(nz-z)*res);for(let ox=0;ox<nx;ox++)for(let oz=0;oz<nz;oz++)if((states[ox*nz+oz]??-1)!==0)best=Math.min(best,Math.hypot((x-ox)*res,(z-oz)*res))}return Math.max(0,best-res/Math.SQRT2)}
function drawPath(points,status){if(pathLine){scene.remove(pathLine);pathLine.geometry.dispose();pathLine.material.dispose();pathLine=null}if(points.length){const pts=points.map(([x,z])=>new THREE.Vector3(x,.075,z));pathLine=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color:status==='passable'?COLORS.free:COLORS.unknown,linewidth:2}));scene.add(pathLine)}}
function drawMarkers(start,goal){while(markers.children.length){const o=markers.children.pop();o.geometry.dispose();o.material.dispose()}for(const [p,label,color] of [[start,'S',0x117d83],[goal,'G',0xd66750]]){const mesh=new THREE.Mesh(new THREE.CylinderGeometry(.08,.08,.08,24),new THREE.MeshStandardMaterial({color}));mesh.position.set(p[0],.08,p[1]);mesh.userData.label=label;markers.add(mesh)}}

function renderFrames(){const frames=currentCase.frames||[],selected=new Set(currentMethod.selected_frames||[]),learned=currentMethod.id.startsWith('da3-');ui.observationSection.hidden=!frames.length;ui.frameCountValue.textContent=`${frameLimit} / ${frames.length}`;ui.frameStrip.innerHTML=frames.slice(0,frameLimit).map(f=>{const depth=learned?f.learned_depth_preview:f.depth_preview,depthLabel=learned?'預測深度':'感測深度',preview=depth?`<img src="${esc(resolveArtifact(depth))}" alt="">`:`<span class="thumb-missing">無預覽</span>`;return `<button class="frame ${selected.has(f.id)?'active':''}" data-frame-id="${f.id}" aria-label="開啟影格 ${f.id} 的 RGB 與${depthLabel}大圖" title="影格 ${f.id}：左 RGB，右${depthLabel}" type="button"><span class="previews"><span><img src="${esc(resolveArtifact(f.rgb))}" alt=""><em>RGB</em></span><span>${preview}<em>${depthLabel}</em></span></span><span class="frame-id">F${f.id}</span></button>`}).join('')}
function renderMetrics(){const entries=Object.entries(currentMethod.metrics||{});ui.metrics.innerHTML=entries.length?entries.map(([k,v])=>`<div><dt>${esc(labelMetric(k))}</dt><dd title="${esc(formatMetric(v,k,false))}">${esc(formatMetric(v,k,true))}</dd></div>`).join(''):'<div><dt>方法未提供量測</dt><dd>—</dd></div>'}
function renderComparison(){ui.comparisonBody.innerHTML=(currentCase.methods||[]).map(m=>{const x=m.metrics||{},status={passable:'可通',blocked:'阻斷',unknown:'未知'}[m.result?.status]||'—';return `<tr class="${m===currentMethod?'current':''}"><td title="${esc(m.label||m.id)}">${esc(m.label||m.id)}</td><td>${status}</td><td>${m.selected_frames?.length??'—'}</td><td>${percent(x.observed_fraction)}</td><td>${compactNumber(x.runtime_seconds)}</td><td>${x.depth_mae_m==null?'—':compactNumber(x.depth_mae_m)+' m'}</td></tr>`}).join('')}
function renderEmptyMethod(){ui.resultStatus.textContent='無方法資料';ui.resultReason.textContent='此案例沒有可檢視的重建方法。';ui.metrics.innerHTML='';ui.frameStrip.innerHTML=''}
function bind(){ui.caseSelect.addEventListener('change',()=>selectCase(+ui.caseSelect.value));ui.methodSelect.addEventListener('change',()=>selectMethod(+ui.methodSelect.value,true));ui.radius.addEventListener('input',replan);ui.frameCount.addEventListener('input',()=>{frameLimit=+ui.frameCount.value;renderFrames();renderScene();replan()});for(const id of ['startX','startZ','goalX','goalZ'])ui[id].addEventListener('change',replan);ui.pickStart.addEventListener('click',()=>setPick('start'));ui.pickGoal.addEventListener('click',()=>setPick('goal'));ui.reconMode.addEventListener('click',()=>setOracle(false));ui.oracleMode.addEventListener('click',()=>setOracle(true));ui.frameStrip.addEventListener('click',e=>{const button=e.target.closest('[data-frame-id]');if(button)openFrameDialog(+button.dataset.frameId)});ui.closeFrameDialog.addEventListener('click',()=>ui.frameDialog.close());ui.viewport.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)||!currentCase)return;e.preventDefault();const p=getEndpoint(pick),d=currentCase.resolution;p[0]+=e.key==='ArrowLeft'?-d:e.key==='ArrowRight'?d:0;p[1]+=e.key==='ArrowUp'?-d:e.key==='ArrowDown'?d:0;setEndpoint(pick,p);syncEndpointFields();replan()})}
function openFrameDialog(id){const f=(currentCase.frames||[]).find(frame=>frame.id===id);if(!f)return;const learned=currentMethod.id.startsWith('da3-'),depth=learned?f.learned_depth_preview:f.depth_preview,label=learned?'預測深度':'感測深度';ui.frameDialogTitle.textContent=`影格 ${id} · ${currentMethod.label||currentMethod.id}`;ui.dialogRgb.src=resolveArtifact(f.rgb);ui.dialogRgb.alt=`影格 ${id} RGB 大圖`;ui.dialogDepthLabel.textContent=label;ui.dialogDepth.hidden=!depth;ui.dialogDepthMissing.hidden=!!depth;if(depth){ui.dialogDepth.src=resolveArtifact(depth);ui.dialogDepth.alt=`影格 ${id} ${label}大圖`}else{ui.dialogDepth.removeAttribute('src');ui.dialogDepth.alt=''}ui.frameDialog.showModal()}
function setPick(v){pick=v;ui.pickStart.classList.toggle('active',v==='start');ui.pickGoal.classList.toggle('active',v==='goal')}
function setOracle(v){oracle=v;ui.reconMode.classList.toggle('active',!v);ui.oracleMode.classList.toggle('active',v);ui.oracleMode.setAttribute('aria-pressed',String(v));ui.sourceNote.textContent=v?'標註參考：完整來源幾何，僅供 oracle 對照；不是重建結果。':'顯示有限觀測所重建的證據。';renderScene();replan()}
function setEndpoint(kind,p){ui[kind+'X'].value=(+p[0]).toFixed(2);ui[kind+'Z'].value=(+p[1]).toFixed(2)}function getEndpoint(kind){const p=[+ui[kind+'X'].value,+ui[kind+'Z'].value];if(p.every(Number.isFinite))return p;const fallback=currentMethod?.result?.[kind]||[(currentCase.bounds[0]+currentCase.bounds[2])/2,(currentCase.bounds[1]+currentCase.bounds[3])/2];setEndpoint(kind,fallback);return[+fallback[0],+fallback[1]]}function syncEndpointFields(){for(const k of ['start','goal'])setEndpoint(k,getEndpoint(k))}
function worldCell([x,z]){const [xmin,zmin,xmax,zmax]=currentCase.bounds,res=currentCase.resolution;if(!Number.isFinite(x)||!Number.isFinite(z)||x<xmin||z<zmin||x>=xmax||z>=zmax)return null;return[Math.floor((x-xmin)/res),Math.floor((z-zmin)/res)]}function cellWorld(ix,iz){return[currentCase.bounds[0]+(ix+.5)*currentCase.resolution,currentCase.bounds[1]+(iz+.5)*currentCase.resolution]}function snap(v){return Math.round(v/currentCase.resolution)*currentCase.resolution}
function fitCamera(){const [xmin,zmin,xmax,zmax]=currentCase.bounds,cx=(xmin+xmax)/2,cz=(zmin+zmax)/2,size=Math.max(xmax-xmin,zmax-zmin);controls.target.set(cx,.3,cz);camera.position.set(cx+size*1.05,size*.95,cz+size*1.05);camera.near=Math.max(.01,size/1000);camera.far=Math.max(100,size*10);camera.updateProjectionMatrix();controls.update()}
function resolveArtifact(path){if(!path)return'';if(/^(https?:|data:|\/)/.test(path))return path;return'/'+path.replaceAll('\\','/').replace(/^\.\//,'')}
function fmtM(v){return Number.isFinite(+v)?`${(+v).toFixed(2)} m`:'—'}function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function compactNumber(v){return Number.isFinite(+v)?(+v).toFixed(3):'—'}function percent(v){return Number.isFinite(+v)?`${(+v*100).toFixed(1)}%`:'—'}function formatMetric(v,k,compact=false){if(v==null)return'—';if(compact&&/(revision|sha256|fingerprint)/.test(k)&&String(v).length>14)return String(v).slice(0,10)+'…';if(typeof v==='number'){if(/fraction$/.test(k))return percent(v);return Number.isInteger(v)?String(v):v.toFixed(4)}if(typeof v==='object')return JSON.stringify(v);return String(v)}function labelMetric(k){return ({observation_count:'觀測數',candidate_count:'候選影格',observed_fraction:'已觀測比例',unknown_fraction:'未知比例',free_fraction:'自由比例',occupied_fraction:'障礙比例',geometry_occupied_iou:'障礙 IoU',clearance_error_m:'淨空誤差（m）',runtime_seconds:'執行時間（秒）',peak_vram_mb:'峰值 VRAM（MB）',device:'運算裝置',reconstruction_failed:'重建失敗',observation_failure_fraction:'觀測失敗比例',pose_source:'姿態來源',pose_failure_rate:'姿態失敗率',oracle_status:'Oracle 判定',depth_mae_m:'深度 MAE（m）',depth_abs_rel:'深度 AbsRel',model_revision:'模型版本',code_revision:'程式版本',scale_alignment:'尺度對齊'})[k]||k.replaceAll('_',' ')}
