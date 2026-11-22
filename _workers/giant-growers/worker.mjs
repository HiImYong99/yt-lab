import {weekly, weekKey, simulate} from '../../play/giant-growers/engine.mjs';

const origin = 'https://ytlab.site';
const adjectives = ['달빛','초록','안개','새벽','노을','바람','이슬','햇살','별빛','여름','봄날','가을'];
const places = ['언덕','골짜기','들판','동산','고개','자락','오솔길','골목','냇가','숲길','정원','고원'];
function farmName(id) {
  return adjectives[parseInt(id.slice(0,2),16)%adjectives.length] + places[parseInt(id.slice(2,4),16)%places.length] + ' ' + id.slice(4,8).toUpperCase();
}
async function farmerId(token) {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(token)));
  return Array.from(digest, b => b.toString(16).padStart(2,'0')).join('');
}
export default {
 async fetch(req, env) {
  const headers = {'Content-Type':'application/json; charset=utf-8','Access-Control-Allow-Origin':origin,'Access-Control-Allow-Headers':'Content-Type','Access-Control-Allow-Methods':'GET,POST,OPTIONS','Cache-Control':'no-store'};
  const reply = (body,status=200) => new Response(JSON.stringify(body),{status,headers});
  if (req.method === 'OPTIONS') return new Response(null,{status:204,headers});
  if (new URL(req.url).pathname !== '/fair') return reply({},404);
  const key = weekKey();
  let own = null;
  if (req.method === 'POST') {
    if (req.headers.get('Origin') && req.headers.get('Origin') !== origin) return reply({},403);
    if (!req.headers.get('content-type')?.startsWith('application/json')) return reply({},415);
    if (Number(req.headers.get('content-length')) > 1024) return reply({},413);
    let body;
    try {body = await req.json();} catch {return reply({},400);}
    if (!body || typeof body.token !== 'string' || !/^[0-9a-f]{32}$/.test(body.token)) return reply({},400);
    if (body.week !== key) return reply({error:'지난 대회가 마감됐습니다.'},409);
    const spec = weekly(key);
    let result;
    try {result = simulate(spec,body.actions);} catch {return reply({},400);}
    if (!result.canPick && !result.finished) return reply({},400);
    const id = await farmerId(body.token);
    await env.DB.prepare('INSERT INTO results(week,farmer,weight) VALUES(?,?,?) ON CONFLICT(week,farmer) DO UPDATE SET weight=excluded.weight WHERE excluded.weight>results.weight').bind(key,id,result.weight).run();
    own = {name:farmName(id)};
  } else if (req.method !== 'GET') return reply({},405);
  const {results} = await env.DB.prepare('SELECT farmer,weight FROM results WHERE week=? ORDER BY weight DESC,farmer LIMIT 10').bind(key).all();
  return reply({key, crop:weekly(key).crop, own, rows:results.map(r=>({name:farmName(r.farmer),weight:r.weight}))});
 }
};
