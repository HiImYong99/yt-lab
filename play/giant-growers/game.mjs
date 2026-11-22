import {crops,choices,forecast,kg,seedGain,simulate,weekly,weekKey} from './engine.mjs';
import {field,seedIcon} from './field.mjs';

const $ = id => document.getElementById(id);
const endpoint = 'https://giant-growers-fair.good19422.workers.dev/fair';
const saveKey = 'giant-growers.v1';
const token = () => Array.from(crypto.getRandomValues(new Uint8Array(16)), b=>b.toString(16).padStart(2,'0')).join('');
const blank = () => ({token:token(),mode:'farm',crop:0,starts:0,lines:[null,null,null],runs:{},history:[],best:[0,0,0]});
let save;
try {save=JSON.parse(localStorage.getItem(saveKey));} catch {}
if (!save || !Array.isArray(save.lines) || !save.runs || !Array.isArray(save.history) || !Array.isArray(save.best) || !/^[a-f0-9]{32}$/.test(save.token)) save=blank();
let flashTimer;
function notify(message) {
  $('notice').textContent=message;clearTimeout(flashTimer);
  flashTimer=setTimeout(()=>$('notice').textContent='',3200);
}
function persist(){
  try {localStorage.setItem(saveKey,JSON.stringify(save));}
  catch {notify('브라우저 저장공간을 쓸 수 없어 이번 접속에서만 기록됩니다.');}
}
const modeNames={farm:'내 농장',weekly:'주간 선수권',challenge:'친구 도전'};
let challenge=null;
const input=new URLSearchParams(location.search).get('d');
if(input && input.length<500) {
  try {
    const [soil,crop,gene,year,actions]=JSON.parse(atob(input));
    const spec={soil,crop,gene,year,mode:'challenge'};
    const tested=simulate(spec,actions);
    if(tested.finished || tested.canPick){
      challenge={spec,weight:tested.weight};
      if(save.challengeCode!==input){delete save.runs.challenge;save.challengeCode=input;}
      save.mode='challenge';
    }
  } catch {}
}
if(!modeNames[save.mode] || (save.mode==='challenge' && !challenge))save.mode='farm';
function getRun(){
  const r=save.runs[save.mode];
  if(!r)return null;
  try {simulate(r.spec,r.actions);if(!r.done && r.spec.mode==='weekly' && r.spec.key!==weekKey()){delete save.runs.weekly;return null;}return r;}
  catch {delete save.runs[save.mode];return null;}
}
function selected(){
  if(save.mode==='weekly')return weekly(weekKey());
  if(save.mode==='challenge')return challenge.spec;
  const line=save.lines[save.crop];
  return {crop:save.crop,year:(line?.year??0)+1,gene:line?.gene??0,mode:'farm'};
}
const button=(id,label,cls='primary')=>'<button class="'+cls+'" data-do="'+id+'">'+label+'</button>';
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function ledger(left,center,right){
  return '<div class="ledger"><span>'+escape(left)+'</span><span>'+escape(center)+'</span><b>'+escape(right)+'</b></div>';
}
function plant(){
  const spec={...selected()};
  if(spec.mode==='farm'){save.starts++;spec.soil=save.token.slice(0,10)+'-'+save.starts;}
  save.runs[save.mode]={spec,actions:[],done:false};persist();render();
}
function finish(r) {
  if(r.done)return;
  const result=simulate(r.spec,r.actions);
  if(!result.canPick&&!result.finished)return;
  r.done=true;
  const {crop,mode,year}=r.spec;
  const old=save.best[crop]||0;
  r.record=result.weight>old;
  save.best[crop]=Math.max(old,result.weight);
  if(mode==='farm'){
    const gene=seedGain(r.spec,result);
    save.lines[crop]={year,gene,parent:result.weight};
  }
  save.history.unshift({crop,year,mode,weight:result.weight});save.history.length=Math.min(save.history.length,50);
  persist();render();
}
function newSeason(){
  delete save.runs[save.mode];persist();render();
}
function move(i){
  const r=getRun();if(!r||r.done)return;
  r.actions.push(i);
  if(simulate(r.spec,r.actions).finished)finish(r);
  else {persist();render();}
}
function showDialog(title,body){
  $('dialog-title').textContent=title;$('dialog-body').innerHTML=body;
  if(!$('dialog').open)$('dialog').showModal();
}
let boardRequest=0;
async function board(){
  const seq=++boardRequest;
  showDialog('주간 선수권 기록','<p>기록을 불러오는 중…</p>');
  try{
    const response=await fetch(endpoint,{signal:AbortSignal.timeout(9000)});
    if(!response.ok)throw Error();
    const data=await response.json();
    if(seq!==boardRequest || !$('dialog').open)return;
    const rows=data.rows.map((r,i)=>ledger((i+1)+'위',r.name,kg(r.weight)+' kg')).join('');
    showDialog('주간 선수권 기록','<p>'+escape(data.key)+' 개막 · '+escape(crops[data.crop].name)+' 부문<br>매주 월요일 0시(한국 시간)에 새 대회가 열립니다.</p>'+(rows||'<p class="empty">아직 출품작이 없습니다. 이번 주 첫 기록을 남겨 보세요.</p>')+button('fair','주간 선수권으로'));
  }catch {if(seq===boardRequest && $('dialog').open)showDialog('주간 선수권 기록','<p>대회 기록을 불러오지 못했습니다.</p>'+button('board','다시 불러오기'));}
}
let sending=false;
async function enterFair(){
  const r=getRun();if(!r?.done||r.spec.mode!=='weekly'||sending)return;
  sending=true;render();
  try{
    const res=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},signal:AbortSignal.timeout(10000),body:JSON.stringify({week:r.spec.key,token:save.token,actions:r.actions})});
    if(!res.ok)throw Error(res.status===409?'이 대회는 마감되었습니다.':'전송하지 못했습니다. 다시 출품할 수 있습니다.');
    const data=await res.json();r.entered=data.own.name;persist();notify('이번 주 농장 기록이 등록됐습니다.');
  }catch(e){notify(e.name==='Error'?e.message:'연결을 확인한 뒤 다시 출품해 주세요.');}
  finally{sending=false;render();}
}
async function share(){
  const r=getRun();if(!r?.done)return;
  const {soil,crop,gene,year}=r.spec;
  const url=new URL(location.pathname,location.origin);
  url.searchParams.set('d',btoa(JSON.stringify([soil,crop,gene,year,r.actions])));
  const message='내 '+crops[crop].short+' 기록 '+kg(simulate(r.spec,r.actions).weight)+' kg! 같은 씨앗으로 도전해 보세요.';
  try{
    if(navigator.share){await navigator.share({title:'거대작물 선수권',text:message,url:url.href});return;}
    await navigator.clipboard.writeText(message+' '+url.href);notify('친구 도전 링크를 복사했습니다.');
  }catch(e){if(e.name==='AbortError')return;showDialog('친구 도전 링크','<p>아래 링크를 복사해 같은 종자와 날씨로 겨뤄 보세요.</p><input class="shareurl" readonly aria-label="도전 링크" value="'+escape(url.href)+'">');$('dialog-body').querySelector('input').select();}
}
function nursery(s){
  const personal=save.mode==='farm', c=crops[s.crop];
  const line=save.lines[s.crop];
  const desc=personal?(line?'지난 '+kg(line.parent)+' kg 출품작에서 받은 씨앗입니다.':'작물을 고르고 첫 씨앗을 심으세요.'):(save.mode==='weekly'?'이번 주 참가자는 같은 씨앗과 날씨로 겨룹니다.':'친구와 같은 씨앗과 날씨에서 시작합니다.');
  const seeds=personal?'<div class="seeds">'+crops.map((c,i)=>'<button class="seed" data-do="seed-'+i+'" aria-pressed="'+(s.crop===i)+'"><canvas data-icon="'+i+'" aria-hidden="true"></canvas>'+c.short+'</button>').join('')+'</div>':'';
  return '<div class="eyebrow">'+(personal?s.year+'세대 종자':save.mode==='weekly'?s.key+' 개막':'기록 도전')+'</div><h2>'+(personal?'올해 심을 씨앗':c.name+' 부문')+'</h2><p>'+desc+'</p>'+seeds+'<p><b>'+c.name+'</b> · '+c.note+'</p>'+button('plant',personal?'이 씨앗 심기':'도전 시작');
}
function underway(r,v){
  const i=r.actions.length,sky=forecast(r.spec,i),danger=v.stress<32?'안정':v.stress<57?'주의':'높음';
  const weatherHint={맑음:'거름을 주면 무게를 늘리기 좋습니다.',소나기:'비가 옵니다. 물을 더 주면 껍질에 부담이 갑니다.',더위:'마른 밭입니다. 물을 주면 크게 자랍니다.',서늘:'서늘한 공기입니다. 뿌리를 돌보면 부담을 덜 수 있습니다.'}[sky];
  const recent=v.log.at(-1);
  const goal=nextRibbon(r.spec,v.weight);
  return '<div class="eyebrow">'+(i+1)+' / 7주 · '+r.spec.year+'세대</div><h2>이번 주는 '+sky+'</h2><div class="step">'+Array.from({length:7},(_,n)=>'<i class="'+(n<i?'on':'')+'"></i>').join('')+'</div><p>'+weatherHint+' <strong class="'+(danger==='높음'?'high':'')+'">갈라짐 위험 '+danger+'</strong></p>'+
    (recent?'<div class="challenge">지난주 '+choices[recent.action].title+' · +'+kg(recent.gain)+' kg</div>':'')+
    choices.map((a,n)=>'<button class="action" data-do="move-'+n+'"><b>'+a.title+'</b><small>'+a.hint+'</small></button>').join('')+
    (v.canPick?button('pick','지금 수확 · '+kg(v.weight)+' kg 확정','secondary'):'<p style="margin:9px 0 0">4주를 기르면 조기 수확할 수 있습니다.</p>')+
    '<p style="margin:9px 0 0">'+(goal?goal.name+' 기준까지 '+kg(goal.weight-v.weight)+' kg':'금상 기준을 넘었습니다.')+'</p>';
}
function ribbons(spec) {
  return [['동상',6],['은상',10],['금상',14]].map(([name,factor])=>({name,weight:crops[spec.crop].base*factor}));
}
function nextRibbon(spec,weight){return ribbons(spec).find(award=>award.weight>weight);}
function results(r,v) {
  const personal=r.spec.mode==='farm',isWeekly=r.spec.mode==='weekly';
  const note=v.damaged?'껍질이 갈라져 손상분을 덜어내고 계량했습니다.':r.actions.length===7?'마지막 주까지 밭을 지켜 완숙 작물을 출품했습니다.':'밭에서 더 키우는 대신 오늘의 무게를 확정했습니다.';
  let extra=personal?'<p>다음 종자 · '+(r.spec.year+1)+'세대 성장 보너스 +'+seedGain(r.spec,v)+'%</p>':'';
  if(isWeekly){
    extra+=r.entered?'<p><b>'+escape(r.entered)+'</b> 이름으로 출품 완료</p>'+button('board','대회 기록 보기'):
      r.spec.key!==weekKey()?'<p>이 대회는 마감됐습니다.</p>':sending?'<p>대회에 출품 중…</p>':button('enter','이번 주 기록 출품');
  }
  const award=ribbons(r.spec).filter(a=>v.weight>=a.weight).at(-1);
  return '<div class="eyebrow">'+r.spec.year+'세대 · 계량 완료'+(r.record?' · 개인 신기록':'')+'</div><h2>'+(award?crops[r.spec.crop].short+' 부문 '+award.name:'첫걸음 출품상')+'</h2><p>'+note+'</p>'+extra+button('next',personal?'다음 세대 키우기':'다시 도전',isWeekly?'secondary':'primary')+button('share','친구에게 기록 도전 보내기','secondary');
}
function render(){
  const r=getRun(),s=r?.spec??selected(),c=crops[s.crop],v=r?simulate(s,r.actions):null;
  const target=challenge && save.mode==='challenge'?challenge.weight:null;
  $('modes').innerHTML=Object.entries(modeNames).filter(([m])=>m!=='challenge'||challenge).map(([m,label])=>'<button data-do="mode-'+m+'" aria-pressed="'+(save.mode===m)+'">'+label+'</button>').join('');
  const sky=r&&!r.done?forecast(s,r.actions.length):'맑음';
  $('field-label').textContent=c.name+' · '+(r?s.year+'세대':modeNames[save.mode]);
  $('sky').textContent=r?(r.done?'계량장':(r.actions.length+1)+'주차 예보 · '+sky):'파종 준비';
  field($('scene'),{crop:s.crop,sky,size:v?Math.min(1,v.weight/(c.base*15)):.82});
  $('weight-label').textContent=r?(r.done?'공식 계량':'밭에서 잰 예상 무게'):'도전 작물';
  $('weight').innerHTML=v?kg(v.weight)+'<small>kg</small>':c.short;
  $('comparison').innerHTML=target?'친구의 기록<br><b>'+kg(target)+' kg</b>':save.best[s.crop]?'내 최고 기록<br><b>'+kg(save.best[s.crop])+' kg</b>':'첫 기록을 기다리는 중';
  let html=r?(r.done?results(r,v):underway(r,v)):nursery(s);
  if(target && r?.done) html='<div class="challenge">'+(v.weight===target?'친구와 동점입니다.':(v.weight>target?'친구 기록을 넘겼습니다. +':'친구 기록까지 ')+kg(Math.abs(v.weight-target))+' kg')+'</div>'+html;
  $('sheet').innerHTML=html;
  document.querySelectorAll('[data-icon]').forEach(n=>seedIcon(n,Number(n.dataset.icon)));
  let journal='';
  if(r && !r.done && v.log.length){
    journal='<h2>재배 일지</h2>'+v.log.map((x,i)=>ledger(i+1+'주차',x.sky+' · '+choices[x.action].title,kg(x.weight)+' kg')).reverse().join('');
  }else{
    journal='<h2>내 출품 장부</h2>'+(save.history.slice(0,5).map(x=>ledger(x.year+'세대',crops[x.crop].short+' · '+modeNames[x.mode],kg(x.weight)+' kg')).join('')||'<p>첫 작물을 계량하면 무게와 세대가 여기에 남습니다.</p>');
  }
  $('journal').innerHTML=journal;
}
$('records').onclick=board;$('close').onclick=()=>$('dialog').close();
document.addEventListener('click',e=>{
  const b=e.target.closest('button[data-do]');if(!b)return;
  const act=b.dataset.do;
  if(act.startsWith('mode-')){save.mode=act.slice(5);persist();render();}
  else if(act.startsWith('seed-')){save.crop=Number(act.slice(5));persist();render();}
  else if(act.startsWith('move-'))move(Number(act.slice(5)));
  else if(act==='plant')plant();
  else if(act==='pick')finish(getRun());
  else if(act==='next')newSeason();
  else if(act==='board')board();
  else if(act==='enter')enterFair();
  else if(act==='share')share();
  else if(act==='fair'){$('dialog').close();save.mode='weekly';persist();render();}
});
window.addEventListener('storage',e=>{if(e.key===saveKey&&e.newValue){try{const newer=JSON.parse(e.newValue);if(newer.token===save.token){const mode=save.mode;save=newer;save.mode=mode;render();}}catch{}}});
render();
