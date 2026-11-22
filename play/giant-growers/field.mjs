const palettes = [
 ['#914023','#bd5422','#e67a29','#ffae44','#ffcd65'],
 ['#294c35','#356741','#4d8950','#7ba852','#acc55e'],
 ['#385b42','#517f51','#77a35b','#a3c379','#c7d796']
];
function painter(canvas, w, h) {
  canvas.width=w; canvas.height=h;
  const ctx=canvas.getContext('2d');
  const box=(x,y,a,b,color)=>{ctx.fillStyle=color;ctx.fillRect(Math.round(x),Math.round(y),Math.round(a),Math.round(b))};
  const oval=(x,y,rx,ry,color)=>{for(let i=-ry;i<=ry;i++){const dx=Math.round(rx*Math.sqrt(Math.max(0,1-i*i/(ry*ry))));box(x-dx,y+i,dx*2+1,1,color)}};
  const poly=(pts,color)=>{ctx.fillStyle=color;ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();ctx.fill()};
  return {box,oval,poly};
}
function fruit(p,x,y,r,id) {
  const {box,oval,poly}=p, col=palettes[id];
  const h=Math.max(3,Math.round(r*(id===1?.72:.78)));
  const e=(dx,dy,a,b,color)=>oval(x+Math.round(dx*r),y+Math.round(dy*h),Math.max(1,Math.round(r*a)),Math.max(1,Math.round(h*b)),color);
  e(0,0,1.02,1.02,col[0]);
  if(id===0) {
    for(const [offset,scale] of [[-.55,.44],[.55,.43],[-.26,.46],[.27,.44],[0,.35]]){
      e(offset,-.015,scale,.95,col[1]);e(offset-.027,-.06,scale*.82,.88,col[2]);e(offset-.08,-.21,scale*.44,.57,col[3]);
    }
    e(-.12,-.49,.065,.19,col[4]);
    poly([[x-r*.12,y-h*.88],[x-r*.16,y-h*1.18],[x+r*.03,y-h*1.48],[x+r*.2,y-h*1.42],[x+r*.06,y-h*1.14],[x+r*.12,y-h*.88]],'#475738');
    box(x-r*.02,y-h*1.3,Math.max(1,r*.08),Math.max(1,h*.28),'#819055');
  } else if(id===1){
    e(-.02,-.02,.96,.94,col[2]);
    for(const offset of [-.67,-.22,.25,.69]){e(offset,0,.105,Math.sqrt(1-offset**2)*.91,col[1]);}
    e(-.39,-.48,.17,.13,col[4]);
  } else {
    e(-.45,.22,.51,.65,col[1]);e(.39,.15,.56,.77,col[2]);e(.01,-.26,.6,.68,col[3]);e(-.42,.25,.47,.52,col[2]);e(.35,.4,.49,.46,col[3]);e(.02,.6,.52,.29,col[2]);
    for(let i=0;i<4;i++)box(x-r*.43+i*r*.12,y+i*h*.14,r*.14,1,col[4]);
  }
}
export function seedIcon(node,id){const p=painter(node,32,32);fruit(p,16,18,11,id);}
export function field(canvas,{crop=0, size=.84, sky='맑음'}={}) {
  const p=painter(canvas,360,160),{box,oval,poly}=p;
  let seed=47321;const random=()=>((seed=Math.imul(seed,1664525)+1013904223|0)>>>0)/4294967296;
  const wet=sky==='소나기';
  box(0,0,360,160,wet?'#a9bdba':'#b9d7c8');box(0,40,360,30,wet?'#bbcbc0':'#d0e0c7');box(0,70,360,32,'#e0e5bf');
  oval(275,29,12,12,wet?'#d7d8bd':'#fff1b1');
  for(const [cx,cy,w] of [[34,33,33],[90,18,17],[210,30,28],[315,45,37],[253,15,12]]){
    box(cx,cy,w,3,'#edf0d6');box(cx+w*.2,cy-3,w*.64,4,'#f6f4dd');box(cx+w*.35,cy-5,w*.31,3,'#f6f4dd');
  }
  for(let x=0;x<360;x+=2){
    const ridge=76-10*Math.sin(x/49)-8*Math.cos(x/24); box(x,ridge,2,97-ridge,'#86a68a');
    const mid=83-7*Math.cos(x/39)-5*Math.sin(x/22);box(x,mid,2,100-mid,'#62876d');
  }
  box(0,91,360,35,'#a4af68');
  for(let j=0;j<18;j++){const x=random()*360,y=82+random()*13;box(x,y,2,10,'#596b46');oval(x,y,4,6,'#708951');oval(x-1,y-2,3,4,'#8b9c60');}
  // The shed and its weathered siding establish the scale of the harvest.
  box(18,78,41,21,'#b26546');for(let x=20;x<59;x+=4)box(x,79,1,19,'#ce8051');
  poly([[13,79],[27,64],[50,64],[63,79]],'#704a3d');poly([[13,77],[27,62],[49,62],[60,75]],'#a75841');
  box(39,82,13,17,'#574a39');box(41,83,9,1,'#d7a66a');box(22,82,7,6,'#eac795');
  for(let y=100;y<116;y+=5){box(0,y,360,2,'#b9ba70');}
  for(let i=0;i<100;i++){const x=random()*360,y=98+random()*18;box(x,y,2,1,'#d2c57f');}
  box(0,108,360,2,'#e8d69d');box(0,113,360,2,'#baa675');
  for(let x=3;x<360;x+=15){box(x,105,3,13,'#d5c18e');box(x,104,2,1,'#eee0b7');}
  box(0,121,360,39,'#94714a');box(0,120,360,4,'#76914e');
  for(let y=127;y<162;y+=8){box(0,y,360,3,'#7e613f');for(let i=0;i<36;i++)box(random()*360,y-1,1+random()*5,1,'#b99559');}
  for(let i=0;i<85;i++){const x=random()*360,y=122+random()*34;if(x>115&&x<247)continue;const n=2+random()*3;
    box(x,y,6,1,'#556b3d');box(x+2,y-n,2,n,'#637b40');box(x-1,y-2,3,1,'#a3a354');
    if(i%8===0)box(x+2,y-n-1,2,2,'#e9ba61');
  }
  const r=Math.round(12+size*48), x=196, y=137-Math.round(r*.78);
  oval(x+2,138,Math.round(r*1.19),4,'#685b3a');
  for(let i=0;i<5;i++) {const xx=x-r-6-i*5;box(xx,135+(i%2),7,2,'#526942');oval(xx-2,131+i%3,4,2,'#778943');}
  fruit(p,x,y,r,crop);
  // A neighboring grower stands beside the crop for a consistent human reference.
  const fx=274;box(fx-6,137,13,2,'#756442');box(fx-4,127,3,10,'#384a43');box(fx+1,127,3,10,'#3f5146');
  box(fx-5,114,10,14,'#617d79');box(fx-5,121,10,7,'#455c56');box(fx-3,108,7,7,'#c88c66');box(fx-1,109,5,5,'#e0aa77');
  box(fx-5,104,10,5,'#bc9152');box(fx-9,108,17,2,'#8d6b43');box(fx-4,105,8,2,'#e0ba72');box(fx-8,117,3,8,'#d7a075');box(fx+5,117,3,7,'#cf966b');
  if(wet)for(let i=0;i<35;i++){const xx=random()*360, yy=random()*115;box(xx,yy,1,3,'#c8dad3');}
}
