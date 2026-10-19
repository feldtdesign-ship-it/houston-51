import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
const MODEL='assets/houston_51.glb';
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const loadEl=document.getElementById('load'), fillEl=document.getElementById('fill');
// glTF space: x east, y up, z south. The room frame (feet): x from the east corner of the front going west, y into the building, z up.
const P=__POINTS__, PINS=__PINS__, LINES=__LINES__, FLOW=__FLOW__;
const FT=P.ft, RO=P.room;
const R=(x,y,z)=>[RO.o[0]+RO.ex[0]*x*FT+RO['in'][0]*y*FT, RO.o[1]+z*FT, RO.o[2]+RO.ex[2]*x*FT+RO['in'][2]*y*FT];
const SITE=R(6.5,0,0);
// every section: where the camera sits, how much of the world it shows (s), how far the picture slides clear of the card (o),
// and what the scene is doing (st): lite 0..1 white world, doll 1 = building off (dollhouse), ex = as-found layer, fit = the shop, hE/hW = hide the near wall, mon = screens on, pins, flow = people and cars
const st=(lite,doll,ex,fit,hE,hW,mon,pins,flow)=>({lite,doll,ex,fit,hE,hW,mon,pins,flow});
const WP=[
 {p:[330,470,330],t:[0,8,0],s:250,o:0,st:st(0,0,1,0,0,0,0,0,1)},                                              // s0 the block
 {p:R(2,-82,30),t:R(6.5,0,14),s:11,o:-.40,st:st(0,0,1,0,0,0,0,0,1)},                                         // s1 the building, from over East Houston
 {p:[SITE[0]+150,330,SITE[2]+210],t:[SITE[0]-40,0,SITE[2]-10],s:175,o:-.42,st:st(0,0,1,0,0,0,0,1,1)},       // s2 the corner, pins
 {p:R(34,-24,62),t:R(7,31,3),s:12,o:.40,st:st(0,1,1,0,0,1,0,0,0)},                                           // s3 as found, from the west, near wall off
 {p:R(34,-24,62),t:R(7,31,3),s:11.4,o:-.38,st:st(1,1,0,0,0,1,0,0,0)},                                        // s4 the white box
 {p:R(38,10,42),t:R(3,33,5),s:10.5,o:.36,st:st(1,1,0,1,0,1,0,0,0)},                                           // s5 the walls (east wall, prints)
 {p:R(-24,10,42),t:R(11,33,5),s:10.5,o:-.36,st:st(1,1,0,1,1,0,0,0,0)},                                        // s6 the rail (west wall, tees)
 {p:R(7,6,30),t:R(9,56,5),s:5.6,o:.34,st:st(0,1,0,1,0,0,1,0,0)},                                         // s7 the screens, lights down, along the corridor
 {p:R(-34,-74,9),t:R(6.5,0,6),s:7.5,o:-.40,st:st(0,0,0,1,0,0,1,0,1)}];                                       // s8 the street, the window
let renderer,scene,cam,ready=false;
function fail(m){console.warn('3D unavailable:',m);document.body.classList.add('fallback');loadEl.classList.add('done');}
try{renderer=new THREE.WebGLRenderer({antialias:true});}catch(e){fail(e);}
if(renderer){
 renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.setSize(innerWidth,innerHeight);
 renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 document.getElementById('stage').appendChild(renderer.domElement);
 const DARK=new THREE.Color(0x141210), LIGHT=new THREE.Color(0xECE9E3);
 scene=new THREE.Scene(); scene.background=DARK.clone(); scene.fog=new THREE.Fog(0x141210,900,2200);
 cam=new THREE.OrthographicCamera(-1,1,1,-1,-3000,6000);
 const hemi=new THREE.HemisphereLight(0xfff1e0,0x1a1816,0.9); scene.add(hemi);
 const key=new THREE.DirectionalLight(0xffe2c4,2.2); key.position.set(-260,420,200); key.castShadow=true; key.shadow.mapSize.set(2048,2048); key.shadow.bias=-0.0006; key.shadow.normalBias=1.2;
 const c=key.shadow.camera; c.left=-500;c.right=500;c.top=500;c.bottom=-500;c.near=1;c.far=1400; scene.add(key);
 const fl=new THREE.DirectionalLight(0xc9d6ff,0.4); fl.position.set(320,200,-280); scene.add(fl);
 // ---- palette: [dark, light, emissive dark, emissive light] ----
 const PAL=[]; const pal=(m,d,l,ed=.3,el=.5)=>{PAL.push({m,d:new THREE.Color(d),l:new THREE.Color(l),ed,el});};
 const groups={facade:[],ex:[],fit:[],near:{E:[],W:[]},ceil:[],trees:[],massing:null,screens:{},exMats:new Set(),fitMats:new Set(),inMats:new Set()};
 const col=h=>new THREE.Color(h);
 const draco=new DRACOLoader(); draco.setDecoderPath('https://unpkg.com/three@0.161.0/examples/jsm/libs/draco/gltf/');
 const loader=new GLTFLoader(); loader.setDRACOLoader(draco);
 loader.load(MODEL,(g)=>{
  g.scene.traverse(o=>{ if(!o.isMesh)return; const m=o.material; if(m){m.roughness=1;m.metalness=0;m.flatShading=true;}
   const n=o.name; const N=n.toUpperCase();
   const near=(side)=>{o.userData.near=side;groups.near[side].push(o);};
   if(N.startsWith('NOLITA_MASSING')){o.castShadow=true;o.receiveShadow=true;if(m){m.transparent=true;pal(m,0x302C28,0xE9E6DF,0,.55);}groups.massing=o;}
   else if(N==='SITE_51'||N.startsWith('B51_')||N==='SITE_W'||N==='SITE_E'||N.startsWith('BW_')||N.startsWith('BE_')){
     groups.facade.push(o); o.castShadow=true;
     if(N==='SITE_51'||N.startsWith('B51_HOUSTON_BRICK')){if(m){m.color=col(0x8F5A48);m.emissive=col(0x8F5A48);m.emissiveIntensity=.30;}}
     else if(N==='SITE_W'||N.startsWith('BW_')){if(m){m.color=col(0xB89B72);m.emissive=col(0xB89B72);m.emissiveIntensity=.26;}}
     else if(N==='SITE_E'||N.startsWith('BE_')){if(m){m.color=col(0xD9CBA8);m.emissive=col(0xD9CBA8);m.emissiveIntensity=.30;}}
     if(N.includes('_IRON')){if(m){m.color=col(0x121212);m.emissive=col(0x000000);}}
     else if(N.includes('_TRIM')||N.includes('_STONE')){if(m){m.color=col(0xC9C2B4);m.emissive=col(0xC9C2B4);m.emissiveIntensity=.3;}}
     else if(N.includes('_GLASS')){if(m){m.color=col(0x0D1714);}}
     else if(N.includes('_SHOPGLASS')){if(m){m.color=col(0xFF6319);m.emissive=col(0xFF6319);m.emissiveIntensity=.35;m.transparent=true;m.opacity=.18;m.depthWrite=false;}}
   }
   else if(N.startsWith('MON_SCR_')){groups.screens[n]=o; groups.fit.push(o);}
   else if(N.startsWith('EX_')){o.userData.y0=o.position.y;groups.ex.push(o);o.receiveShadow=true;if(m){m.transparent=true;groups.exMats.add(m);const c0=m.color.clone();m.emissive=c0.clone();m.emissiveIntensity=.38;}
     if(/^EX_(TILEWALL_E|TILEHEX_E|ROSETTE)/.test(N)) near('E'); else if(/^EX_(TILEWALL_W|TILEHEX_W|STEEL|TIMBER)/.test(N)) near('W');}
   else if(N.startsWith('FIT_')){groups.fit.push(o);o.castShadow=true;if(m){m.transparent=true;groups.fitMats.add(m);
       if(N.startsWith('FIT_GAL_PRINT')){m.emissive=col(0xFFFFFF);m.emissiveIntensity=.35;m.emissiveMap=m.map||null;}
       else if(N.startsWith('FIT_FOLD')||N.startsWith('FIT_TEE')){m.emissive=m.color.clone();m.emissiveIntensity=.45;}
       else if(N.startsWith('FIT_TBL_TOP')||N.startsWith('FIT_UNIT_PLANK')){m.emissive=m.color.clone();m.emissiveIntensity=.35;}
       else if(N.startsWith('FIT_GAL_MAT')){m.emissive=m.color.clone();m.emissiveIntensity=.5;}}
     if(/^FIT_GAL_/.test(N)) near('E'); else if(/^FIT_(UNIT_|TEE_)/.test(N)||(/^FIT_FOLD_\d/.test(N))) near('W');}
   else if(N.startsWith('IN_')){o.receiveShadow=true;o.castShadow=true;if(m){if(/^IN_FLOOR/.test(N)) m.color.set(0xEAE7E1); const w=/^IN_(WALL|CEIL|BATH|HALL)/.test(N);m.userData.w=w;groups.inMats.add(m);m.emissive=m.color.clone();m.emissiveIntensity=w?.5:.4;}
     if(/^IN_(WALLE)/.test(N)) near('E'); else if(/^IN_WALLW1/.test(N)) near('W');
     if(/^IN_(CEIL|TRACK|HEAD)/.test(N)) groups.ceil.push(o);}
   else if(N.startsWith('TREES')){o.castShadow=true;if(m)pal(m,0x4A5A3A,0xC9D3BC,.2,.3);groups.trees.push(o);}
   else if(N.startsWith('GROUND')||N.startsWith('PLANE')){o.receiveShadow=true;if(m)pal(m,0x141210,0xECE9E3,0,.9);}
   else if(N.startsWith('ROADBED')){o.receiveShadow=true;if(m)pal(m,0x1C1A18,0xE3E0D9,0,.7);}
   else if(N.startsWith('SIDEWALK')){o.receiveShadow=true;if(m)pal(m,0x2B2823,0xF8F6F2,0,.8);}
   else if(N.startsWith('MEDIAN')){if(m)pal(m,0x34302A,0xE9E6DF,0,.6);}
   else if(N.startsWith('ST_')){if(m)pal(m,0x8A857C,0xAAA59B,0,.2);}
   else {o.receiveShadow=true;} });
  scene.add(g.scene); setupScreens(); ready=true; window.__ready=true; loadEl.classList.add('done'); onScroll();
 },(ev)=>{ if(ev.total) fillEl.style.width=(ev.loaded/ev.total*100).toFixed(0)+'%'; },(err)=>fail(err));

 // ---------------- the screens ----------------
 const VID={}; const ASP={ontheblock:16/9};
 function vid(n){ if(VID[n]) return VID[n]; const v=document.createElement('video'); v.src='media/'+n+'.mp4'; v.muted=true; v.loop=true; v.playsInline=true; v.preload='auto'; v.setAttribute('playsinline',''); VID[n]=v; return v; }
 function vtex(n,scrAsp,tile){ const t=new THREE.VideoTexture(vid(n)); t.colorSpace=THREE.SRGBColorSpace; t.generateMipmaps=false; t.minFilter=THREE.LinearFilter; cover(t,ASP[n]||1,scrAsp,tile); return t; }
 function cover(t,va,sa,tile){ // crop the clip to the screen like object-fit: cover; tile = {c,r,cols,rows,wa} cuts one panel out of a wall-sized picture
  if(tile){ const wa=tile.wa; let rx=1,ry=1,ox=0,oy=0; if(va>wa){rx=wa/va;ox=(1-rx)/2;}else{ry=va/wa;oy=(1-ry)/2;}
   t.repeat.set(rx/tile.cols,ry/tile.rows); t.offset.set(ox+rx*tile.c/tile.cols, oy+ry*(tile.rows-1-tile.r)/tile.rows); return; }
  if(va>sa){t.repeat.set(sa/va,1);t.offset.set((1-sa/va)/2,0);}else{t.repeat.set(1,va/sa);t.offset.set(0,(1-va/sa)/2);} }
 const ARTS=[];
 function art(names,asp,w=360){ const c=document.createElement('canvas'); c.width=w; c.height=Math.round(w/asp); const imgs=names.map(n=>{const i=new Image(); i.src='assets/art/'+n+'.jpg'; return i;});
  const tex=new THREE.CanvasTexture(c); tex.colorSpace=THREE.SRGBColorSpace; const a={c,ctx:c.getContext('2d'),imgs,tex,asp,t0:Math.random()*6,on:false}; ARTS.push(a); return a; }
 function drawArt(a,t){ const {ctx,c,imgs}=a; ctx.fillStyle='#f4f2ed'; ctx.fillRect(0,0,c.width,c.height); const per=4.4, tt=t+a.t0, k=Math.floor(tt/per)%imgs.length, f=(tt%per)/per;
  const draw=(img,al,z)=>{ if(!img.complete||!img.naturalWidth)return; const ia=img.naturalWidth/img.naturalHeight; let sw,sh; if(ia>a.asp){sh=img.naturalHeight;sw=sh*a.asp;}else{sw=img.naturalWidth;sh=sw/a.asp;} sw/=z; sh/=z; ctx.globalAlpha=al; ctx.drawImage(img,(img.naturalWidth-sw)/2,(img.naturalHeight-sh)/2,sw,sh,0,0,c.width,c.height); };
  draw(imgs[k],1,1+.14*f); const fd=Math.max(0,(f-.86)/.14); if(fd>0) draw(imgs[(k+1)%imgs.length],fd,1); ctx.globalAlpha=1;
  ctx.fillStyle='rgba(255,99,25,.07)'; ctx.fillRect(0,0,c.width,c.height); ctx.fillStyle='rgba(0,0,0,.07)'; for(let y=0;y<c.height;y+=3) ctx.fillRect(0,y,c.width,1);
  const j=(Math.sin(tt*37)>.985)?4:0; if(j){ctx.drawImage(c,0,0,c.width,c.height,j,0,c.width,c.height);} a.tex.needsUpdate=true; }
 const wall=[], mats=[]; let wallMode=0, wallT=0;
 function setupScreens(){
  const S=groups.screens, mk=(map)=>new THREE.MeshBasicMaterial({map,toneMapped:false});
  const put=(name,map)=>{ const o=S[name]; if(!o)return null; const m=mk(map); o.material=m; mats.push(m); return {o,m}; };
  const WA=(3*3.1+2*.05)/(2*1.75+.05), PA=1.75/3.1, LA=3.1/1.75;
  // window triptych: art, a moving clip, art
  put('MON_SCR_W1',art(['gumbit_citibike','art_02','gumbit_bubbles'],PA,300).tex); put('MON_SCR_W2',vtex('breakdance',PA)); put('MON_SCR_W3',art(['gumbit_bubbles','art_04','gumbit_citibike'],PA,300).tex);
  // the wall: one picture across six, six pictures, six sets of prints
  const six=['hornets','fatgumbit','pizzarat','headspin','suitpink','nyloop'], sets=[['art_01','art_05'],['art_02','art_06'],['art_03','art_07'],['art_04','gumbit_citibike'],['art_05','art_cats'],['art_06','gumbit_bubbles']];
  for(let i=0;i<6;i++){ const r=Math.floor(i/3), c2=i%3; const o=put('MON_SCR_B'+(i+1),null); if(!o)continue;
   const span=vtex('ontheblock',LA,{c:c2,r,cols:3,rows:2,wa:WA}), sx=vtex(six[i],LA), ar=art(sets[i],LA,320).tex; wall.push({m:o.m,maps:[span,sx,ar]}); o.m.map=span; }
  const hang=[['H1a','fatgumbit'],['H1b','pizzarat'],['H2a','headspin'],['H2b','nyloop'],['H3a','hornets'],['H3b','suitpink']];
  hang.forEach(([k,v])=>put('MON_SCR_'+k,vtex(v,LA)));
 }
 function videos(on){ Object.values(VID).forEach(v=>{ if(on&&v.paused){v.play().catch(()=>{});} else if(!on&&!v.paused){v.pause();} }); }

 // ---------------- people and cars: one weekday, sped up ----------------
 const FLOWG=new THREE.Group(); scene.add(FLOWG); let pedMesh,carMesh; const PED=[],CAR=[];
 const paths=LINES.map(l=>{ const pts=l.p.map(q=>[q[0],-q[1]]); const cum=[0]; for(let i=1;i<pts.length;i++) cum.push(cum[i-1]+Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1])); return {pts,cum,len:cum[cum.length-1],w:l.w*FT}; })
   .filter(p=>p.len>12 && p.pts.some(q=>Math.hypot(q[0]-SITE[0],q[1]-SITE[2])<300));
 const totalLen=paths.reduce((s,p)=>s+p.len,0);
 const pickPath=(wide)=>{ let r=Math.random()*totalLen; for(const p of paths){ if(wide&&p.w<8.5) {continue;} r-=p.len; if(r<=0) return p; } return paths[0]; };
 function at(p,s){ let i=1; while(i<p.cum.length-1&&p.cum[i]<s) i++; const a=p.pts[i-1], b=p.pts[i], L=p.cum[i]-p.cum[i-1]||1, f=(s-p.cum[i-1])/L; const tx=(b[0]-a[0])/L, tz=(b[1]-a[1])/L; return [a[0]+(b[0]-a[0])*f, a[1]+(b[1]-a[1])*f, tx, tz]; }
 function buildFlow(){
  const NP=520, NC=120; const pg=new THREE.SphereGeometry(.3,6,5), cg=new THREE.BoxGeometry(4.2,1.3,1.8);
  pedMesh=new THREE.InstancedMesh(pg,new THREE.MeshBasicMaterial({color:0xFF6319}),NP); carMesh=new THREE.InstancedMesh(cg,new THREE.MeshBasicMaterial({color:0xE9E4DA}),NC);
  for(let i=0;i<NP;i++){ const p=pickPath(false); PED.push({p,s:Math.random()*p.len,d:Math.random()<.5?1:-1,v:1.1+Math.random()*.6,off:(Math.random()<.5?1:-1)*(p.w/2+2.0+Math.random()*1.2),k:Math.random()}); }
  for(let i=0;i<NC;i++){ const p=pickPath(true); CAR.push({p,s:Math.random()*p.len,d:Math.random()<.5?1:-1,v:5+Math.random()*4,off:(p.w/4)*(Math.random()<.5?1:-1),k:Math.random()}); }
  pedMesh.frustumCulled=false; carMesh.frustumCulled=false; FLOWG.add(pedMesh,carMesh); }
 buildFlow();
 const dummy=new THREE.Object3D(); let simH=17, lastT=performance.now(), flowOn=0;
 const dens=(arr,h)=>{ const a=Math.floor(h)%24,b=(a+1)%24,f=h-Math.floor(h); return arr[a]*(1-f)+arr[b]*f; };
 function stepFlow(dt,on){
  FLOWG.visible=on>.02; if(!FLOWG.visible) return; simH=(simH+dt*.2)%24;
  const dp=dens(FLOW.ped,simH), dc=dens(FLOW.car,simH), SP=7, zk=Math.max(1,state.s/40);
  const upd=(arr,mesh,den,h,sc,zs)=>{ arr.forEach((q,i)=>{ q.s+=q.d*q.v*dt*SP*(sc||1); if(q.s<0){q.s=0;q.d=1;} else if(q.s>q.p.len){q.s=q.p.len;q.d=-1;}
    const a=at(q.p,q.s), nx=-a[3], nz=a[2]; dummy.position.set(a[0]+nx*q.off,h,a[1]+nz*q.off); const show=q.k<den?on:0;
    dummy.scale.setScalar(show*(zs||zk)); dummy.rotation.set(0,Math.atan2(-a[3]*q.d,a[2]*q.d),0); dummy.updateMatrix(); mesh.setMatrixAt(i,dummy.matrix); }); mesh.instanceMatrix.needsUpdate=true; };
  upd(PED,pedMesh,dp,1.0,1); upd(CAR,carMesh,dc,.9,1,Math.max(1,state.s/110));
  const hh=Math.floor(simH), mm=Math.floor((simH-hh)*60/5)*5; document.getElementById('m-v').textContent=`${(hh+11)%12+1}:${String(mm).padStart(2,'0')} ${hh<12?'am':'pm'}`; }

 // ---------------- pins ----------------
 const pinsEl=document.getElementById('pins'); const pinEls=PINS.map(p=>{ const d=document.createElement('div'); d.className='pin'+(p.hot?' hot':''); d.innerHTML=`<i></i><span>${p.n}<em>${p.d?p.d+' m':'this building'}</em></span>`; pinsEl.appendChild(d); return {d,x:p.xy[0],z:-p.xy[1]}; });
 const v3=new THREE.Vector3(); function projectPins(vis){ pinsEl.style.opacity=vis; pinEls.forEach(p=>{ v3.set(p.x,6,p.z).project(cam); p.d.style.transform=`translate(${((v3.x+1)/2*innerWidth).toFixed(1)}px,${((1-v3.y)/2*innerHeight).toFixed(1)}px)`; }); }

 // ---------------- scroll, camera, scene state ----------------
 const state={p:new THREE.Vector3(),t:new THREE.Vector3(),s:250,o:0}, goal={p:new THREE.Vector3(),t:new THREE.Vector3(),s:250,o:0};
 const S0=st(0,0,1,0,0,0,0,0,1), S=Object.assign({},S0), SG=Object.assign({},S0);
 const secs=[...document.querySelectorAll('main#dossier section')], links=[...document.querySelectorAll('#rail a')];
 const cap=document.getElementById('cap'), bar=document.getElementById('bar'), scrim=document.getElementById('scrim'), num=document.getElementById('num'), meter=document.getElementById('meter');
 let shown=-1; const mult=()=>innerWidth<760?1.5:1; const lerp=(a,b,t)=>a+(b-a)*t; const smooth=t=>t*t*(3-2*t);
 function onScroll(){
  const dm=document.getElementById('dossier'); const max=dm.offsetTop+dm.offsetHeight-innerHeight; const t=max>0?Math.min(1,Math.max(0,scrollY/max)):0;
  const nb=document.getElementById('numbers').getBoundingClientRect().top; document.body.classList.toggle('numbers-on', nb<innerHeight*0.5); window.__numbersOn = nb<innerHeight*0.5;
  bar.style.width=(t*100).toFixed(2)+'%';
  const yc=scrollY+innerHeight*0.5, cs=secs.map(x=>x.offsetTop+dm.offsetTop+x.offsetHeight/2); let k=0; while(k<cs.length-2&&yc>=cs[k+1])k++;
  const seg=Math.min(WP.length-1,Math.max(0,k+(yc-cs[k])/(cs[k+1]-cs[k]))), i=Math.min(WP.length-2,Math.floor(seg)), f=smooth(seg-i), a=WP[i], b=WP[i+1];
  goal.p.set(lerp(a.p[0],b.p[0],f),lerp(a.p[1],b.p[1],f),lerp(a.p[2],b.p[2],f)); goal.t.set(lerp(a.t[0],b.t[0],f),lerp(a.t[1],b.t[1],f),lerp(a.t[2],b.t[2],f));
  goal.s=lerp(a.s,b.s,f)*mult(); goal.o=innerWidth<760?0:lerp(a.o,b.o,f);
  for(const kk in S0) SG[kk]=lerp(a.st[kk],b.st[kk],f);
  const close=1-Math.min(1,Math.max(0,(goal.s/mult()-10)/(250-10)));
  document.documentElement.style.setProperty('--opsz',(72-60*close).toFixed(1)); document.documentElement.style.setProperty('--w',(700+100*close).toFixed(0));
  if(reduced){state.p.copy(goal.p);state.t.copy(goal.t);state.s=goal.s;state.o=goal.o;}
  const mid=innerHeight*0.45; let n=0,bd=1e9; secs.forEach((s,j)=>{const r=s.getBoundingClientRect(); const d=Math.abs(r.top+r.height/2-mid); if(d<bd){bd=d;n=j;}});
  if(n!==shown){shown=n; links.forEach((l,j)=>l.classList.toggle('on',j===n)); const s=secs[n]; cap.textContent=s.dataset.cap||'';
   scrim.className=(s.querySelector('.wrap.right')?'flip':''); const nv=s.dataset.num||''; num.textContent=nv||num.textContent; num.classList.toggle('on',!!nv); num.style.color='var(--'+(s.dataset.numc||'f')+')'; }
 }
 function applyState(dt){
  const k=reduced?1:Math.min(1,dt*5); for(const kk in S0) S[kk]=reduced?SG[kk]:S[kk]+(SG[kk]-S[kk])*k;
  const L=S.lite; document.body.classList.toggle('lite-on',L>.5);
  scene.background.copy(DARK).lerp(LIGHT,L); scene.fog.color.copy(scene.background); scene.fog.near=lerp(900,6000,L); scene.fog.far=lerp(2200,9000,L); hemi.intensity=lerp(.9,1.25,L); key.intensity=lerp(2.2,1.6,L);
  PAL.forEach(q=>{ q.m.color.copy(q.d).lerp(q.l,L); if(q.m.emissive){ q.m.emissive.copy(q.m.color); q.m.emissiveIntensity=lerp(q.ed,q.el,L);} });
  const dh=S.doll>.5; groups.facade.forEach(o=>o.visible=!dh); groups.trees.forEach(o=>o.visible=!dh); groups.ceil.forEach(o=>o.visible=!dh);
  if(groups.massing){ groups.massing.material.opacity=1-.88*S.doll; groups.massing.castShadow=!dh; }
  const setFade=(mats,v,objs,lift)=>{ mats.forEach(m=>{ m.opacity=v; m.transparent=v<.995; m.depthWrite=v>.5; }); objs.forEach(o=>{ o.userData.base=v>.02; }); };
  setFade(groups.exMats,S.ex,groups.ex); setFade(groups.fitMats,S.fit,groups.fit);
  groups.ex.forEach(o=>{ o.position.y=o.userData.y0+(1-S.ex)*.9; });                            // the finishes lift as they go
  const hid=(o)=>(o.userData.near==='E'&&S.hE>.5)||(o.userData.near==='W'&&S.hW>.5);
  groups.ex.forEach(o=>o.visible=o.userData.base&&!hid(o)); groups.fit.forEach(o=>o.visible=o.userData.base&&!hid(o));
  groups.near.E.forEach(o=>{ if(!o.userData.base&&o.userData.base!==undefined) return; if(/^IN_/.test(o.name)) o.visible=S.hE<=.5; }); groups.near.W.forEach(o=>{ if(/^IN_/.test(o.name)) o.visible=S.hW<=.5; });
  mats.forEach(m=>{ m.opacity=1; });
  groups.inMats.forEach(m=>{ const w=m.userData.w; m.emissiveIntensity=lerp(w?.5:.4,w?.2:.14,S.mon); });
  const monOn=S.mon>.05&&S.fit>.5; videos(monOn); meter.classList.toggle('on',S.flow>.5&&!dh);
 }
 let T=0;
 function frame(){ requestAnimationFrame(frame); if(!ready||window.__numbersOn)return; const now=performance.now(), dt=Math.min(.1,(now-lastT)/1000); lastT=now; T+=dt;
  if(!reduced){state.p.lerp(goal.p,0.07);state.t.lerp(goal.t,0.07);state.s+=(goal.s-state.s)*0.07;state.o+=(goal.o-state.o)*0.07;}
  applyState(dt); stepFlow(dt,S.flow);
  if(S.fit>.5&&S.mon>.05){ ARTS.forEach(a=>{ if(((T*15)|0)!==a.f){a.f=(T*15)|0; drawArt(a,T);} });
   wallT+=dt; const m=Math.floor(wallT/14)%3; if(m!==wallMode){ wallMode=m; wall.forEach(w=>{ w.m.map=w.maps[m]; w.m.needsUpdate=true; }); } }
  const a=innerWidth/innerHeight; const off=state.o*state.s*a; cam.left=-state.s*a-off; cam.right=state.s*a-off; cam.top=state.s; cam.bottom=-state.s; cam.near=state.s<30?0.5:-3000;
  cam.position.copy(state.p); cam.up.set(0,1,0); cam.lookAt(state.t); cam.updateProjectionMatrix(); projectPins(Math.max(0,Math.min(1,S.pins))); renderer.render(scene,cam); }
 addEventListener('scroll',onScroll,{passive:true}); addEventListener('resize',()=>{renderer.setSize(innerWidth,innerHeight);onScroll();});
 onScroll(); state.p.copy(goal.p); state.t.copy(goal.t); state.s=goal.s; state.o=goal.o; for(const kk in S0) S[kk]=SG[kk]; frame();
 setTimeout(()=>{if(!ready)fail('timeout');},25000);
 window.__h51={WP,S,SG,groups,R,state,goal,VID,wall,get wallMode(){return wallMode;}};
}
