import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js";

const root=document.getElementById("moonGlobe");
const readout=document.getElementById("globeLatLon");
const hint=document.getElementById("globeHint");
if(root){
  try{
    const scene=new THREE.Scene();
    const camera=new THREE.PerspectiveCamera(42,1,0.1,100);
    camera.position.set(0,0,3.25);
    const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
    root.appendChild(renderer.domElement);
    scene.add(new THREE.AmbientLight(0x9fb8d5,1.45));
    const key=new THREE.DirectionalLight(0xffffff,2.4);key.position.set(-3,2,4);scene.add(key);
    const fill=new THREE.DirectionalLight(0x718db5,.65);fill.position.set(3,-2,-3);scene.add(fill);

    const texCanvas=document.createElement("canvas");texCanvas.width=2048;texCanvas.height=1024;
    const cx=texCanvas.getContext("2d");
    cx.fillStyle="#777b80";cx.fillRect(0,0,2048,1024);
    let seed=1234567;const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296};
    for(let i=0;i<160000;i++){const x=rand()*2048,y=rand()*1024,r=rand()*2.2+.25,v=Math.floor(95+rand()*100);cx.fillStyle="rgba("+v+","+v+","+v+","+(rand()*.13)+")";cx.fillRect(x,y,r,r)}
    for(let i=0;i<1150;i++){
      const x=rand()*2048,y=rand()*1024,r=2+Math.pow(rand(),2)*34;
      cx.beginPath();cx.arc(x,y,r,0,Math.PI*2);cx.fillStyle="rgba(28,31,36,.14)";cx.fill();
      cx.beginPath();cx.arc(x-r*.13,y-r*.12,r*.78,0,Math.PI*2);cx.strokeStyle="rgba(220,222,222,.25)";cx.lineWidth=Math.max(1,r*.07);cx.stroke();
      cx.beginPath();cx.arc(x+r*.18,y+r*.18,r*.72,0,Math.PI*2);cx.strokeStyle="rgba(22,25,30,.2)";cx.lineWidth=Math.max(1,r*.08);cx.stroke();
    }
    for(let i=0;i<17;i++){const x=rand()*2048,y=rand()*1024,rx=40+rand()*140,ry=10+rand()*38;cx.beginPath();cx.ellipse(x,y,rx,ry,rand()*Math.PI,0,Math.PI*2);cx.fillStyle="rgba(48,53,59,.12)";cx.fill()}
    const texture=new THREE.CanvasTexture(texCanvas);texture.colorSpace=THREE.SRGBColorSpace;
    const globe=new THREE.Mesh(new THREE.SphereGeometry(1,96,64),new THREE.MeshStandardMaterial({map:texture,roughness:1,metalness:0}));
    scene.add(globe);
    const grid=new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.SphereGeometry(1.003,24,12)),new THREE.LineBasicMaterial({color:0x86a5c5,transparent:true,opacity:.10}));
    scene.add(grid);
    const marker=new THREE.Mesh(new THREE.SphereGeometry(.022,16,12),new THREE.MeshBasicMaterial({color:0x62d9ed}));
    scene.add(marker);
    const ring=new THREE.Mesh(new THREE.TorusGeometry(1.035,.003,6,128),new THREE.MeshBasicMaterial({color:0x4d769d,transparent:true,opacity:.45}));ring.rotation.x=Math.PI/2;scene.add(ring);

    let selected={lat:-89.5,lon:0},drag=false,last={x:0,y:0},down={x:0,y:0};
    const pointer=new THREE.Vector2(),raycaster=new THREE.Raycaster();
    function vectorFor(lat,lon,r=1.025){const a=THREE.MathUtils.degToRad(lat),b=THREE.MathUtils.degToRad(lon);return new THREE.Vector3(r*Math.cos(a)*Math.cos(b),r*Math.sin(a),-r*Math.cos(a)*Math.sin(b))}
    function label(){const ns=selected.lat>=0?"N":"S",ew=selected.lon>=0?"E":"W";readout.textContent=Math.abs(selected.lat).toFixed(2)+"° "+ns+" / "+Math.abs(selected.lon).toFixed(2)+"° "+ew;hint.textContent="Selected coordinates in the lunar east-positive convention. Apply them to the analysis form when ready.";marker.position.copy(vectorFor(selected.lat,selected.lon));}
    label();
    function resize(){const w=root.clientWidth,h=root.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
    new ResizeObserver(resize).observe(root);resize();
    renderer.domElement.addEventListener("pointerdown",e=>{drag=true;last={x:e.clientX,y:e.clientY};down={x:e.clientX,y:e.clientY};renderer.domElement.setPointerCapture(e.pointerId)});
    renderer.domElement.addEventListener("pointermove",e=>{if(!drag)return;const dx=e.clientX-last.x,dy=e.clientY-last.y;globe.rotation.y+=dx*.006;globe.rotation.x=Math.max(-1.45,Math.min(1.45,globe.rotation.x+dy*.006));grid.rotation.copy(globe.rotation);last={x:e.clientX,y:e.clientY}});
    renderer.domElement.addEventListener("pointerup",e=>{drag=false;if(Math.hypot(e.clientX-down.x,e.clientY-down.y)>5)return;const rect=renderer.domElement.getBoundingClientRect();pointer.x=((e.clientX-rect.left)/rect.width)*2-1;pointer.y=-((e.clientY-rect.top)/rect.height)*2+1;raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObject(globe)[0];if(!hit)return;const local=globe.worldToLocal(hit.point.clone().normalize());selected.lat=THREE.MathUtils.radToDeg(Math.asin(THREE.MathUtils.clamp(local.y,-1,1)));selected.lon=THREE.MathUtils.radToDeg(Math.atan2(-local.z,local.x));label()});
    renderer.domElement.addEventListener("wheel",e=>{camera.position.z=Math.max(1.7,Math.min(5,camera.position.z+e.deltaY*.002));e.preventDefault()},{passive:false});
    document.getElementById("useGlobeSite").addEventListener("click",()=>{document.getElementById("lat").value=selected.lat.toFixed(2);document.getElementById("lon").value=selected.lon.toFixed(2);document.getElementById("explorer").scrollIntoView({behavior:"smooth"});});
    function animate(){requestAnimationFrame(animate);renderer.render(scene,camera)}animate();
  }catch(error){hint.textContent="3D globe unavailable in this browser: "+error.message}
}
