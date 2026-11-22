export const crops = [
  { name: '자이언트 호박', short: '호박', base: 150, likes: '맑음', note: '맑은 날 쑥쑥 자라는 중량급' },
  { name: '줄무늬 수박', short: '수박', base: 42, likes: '더위', note: '한여름 더위에 강한 여름 작물' },
  { name: '왕양배추', short: '양배추', base: 21, likes: '서늘', note: '서늘한 밭에서 잎을 겹겹이' }
];
export const choices = [
  { title: '물을 준다', hint: '건조할 때 성장 · 비에는 갈라짐' },
  { title: '거름을 준다', hint: '성장량 증가 · 껍질에 부담' },
  { title: '뿌리를 돌본다', hint: '성장은 느리게 · 손상 위험 완화' }
];
const weather = ['맑음', '소나기', '더위', '서늘'];
export const kg = n => (n / 10).toLocaleString('ko-KR',{minimumFractionDigits:1,maximumFractionDigits:1});
export function rand(key) {
  let v = 2166136261;
  for (const c of String(key)) v = Math.imul(v ^ c.charCodeAt(0), 16777619);
  v ^= v >>> 16; v = Math.imul(v, 0x45d9f3b); v ^= v >>> 16;
  return (v >>> 0) / 4294967296;
}
export function weekKey(time = Date.now()) {
  const d = new Date(time + 9 * 3600000);
  d.setUTCDate(d.getUTCDate() - (d.getUTCDay() + 6) % 7);
  return d.toISOString().slice(0,10);
}
export function weekly(key) {
  return { soil:'fair-' + key, crop:Math.floor(rand(key) * crops.length), gene:0, year:1, mode:'weekly', key };
}
export function validSpec(s) {
  return !!s && typeof s.soil === 'string' && /^[a-z0-9-]{1,55}$/.test(s.soil) &&
    Number.isInteger(s.crop) && !!crops[s.crop] && Number.isInteger(s.gene) && s.gene >= 0 && s.gene <= 30 &&
    Number.isInteger(s.year) && s.year >= 1 && s.year <= 999999;
}
export function forecast(s, i) { return weather[Math.floor(rand(s.soil + '/sky/' + i) * weather.length)]; }
export function simulate(s, actions) {
  if (!validSpec(s) || !Array.isArray(actions) || actions.length > 7) throw Error('잘못된 재배 기록');
  const c = crops[s.crop];
  let weight = Math.round(c.base * 0.25), stress = 14, damaged = false;
  const log = [];
  for (const [i, action] of actions.entries()) {
    if (damaged || !Number.isInteger(action) || !choices[action]) throw Error('잘못된 농사 선택');
    const sky = forecast(s, i);
    const wet = sky === '소나기', hot = sky === '더위';
    const before = weight;
    const gain = action === 0 ? (wet ? .69 : hot ? 1.7 : 1.16) : action === 1 ? (wet ? 1.68 : hot ? 1.08 : 1.45) : .82;
    const strain = action === 0 ? (wet ? 25 : hot ? -4 : 3) : action === 1 ? (hot ? 25 : 14) : -25;
    stress = Math.max(3, Math.min(94, stress + strain + (i >= 4 ? 6 : 0)));
    const vigor = 1 + s.gene / 100 + (sky === c.likes ? .15 : 0);
    weight += Math.round(c.base * (1 + i * .21) * vigor * gain * (.87 + .29 * rand(s.soil + '/size/' + i)));
    const risk = i < 2 ? 0 : Math.max(0, (stress - 35) / 150);
    damaged = rand(s.soil + '/crack/' + i) < risk;
    if (damaged) weight = Math.max(1,Math.round(weight * .68));
    log.push({sky, action, gain:weight - before, weight, damaged});
  }
  return {weight, stress, damaged, log, finished:damaged || actions.length === 7, canPick:actions.length >= 4};
}
export function seedGain(s, result) {
  const relative = result.weight / (crops[s.crop].base * 11);
  return Math.min(30, s.gene + Math.max(1, Math.min(5,Math.round(relative * 2))));
}
