import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{t}from"./compiler-runtime-CZQb2eIb.js";import{et as n}from"./lodash-ClfL87UH.js";/* empty css            */import{t as r}from"./jsx-runtime-BapUIyWk.js";import{t as i}from"./useControllableValue-BOAfgoBq.js";import{t as a}from"./dayjs.min-PJVk-kyH.js";import{t as o}from"./DateTimeInput-CGHzW8j0.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

antd `DatePicker showTime` -> Astryx `DateTimeInput` (MAPPING §3.13, which
CORRECTS ticket 04's "no Date family" — `DateInput` / `DateTimeInput` /
`DateRangeInput` / `TimeInput` / `Calendar` all ship in core 0.3.0).

FRONTIER: this component exists precisely to be the dayjs<->string boundary,
and that is now also the dayjs<->`ISODateTimeString` boundary. The PUBLIC prop
surface stays what the single consumer (`SessionLauncherPage`, inside a
`Form.Item name={['batch','scheduleDate']}`) already passes — `disabled`,
`showTime`, `localFormat`, `disabledDate(dayjs)` — so that file stays at zero
diff. antd's `PickerProps<Dayjs>` / `GetRef` type imports are gone with the
render (§6: a type-only antd import is still an antd import).

PILOT-DECISIONs:
- `showTime` becomes a NO-OP prop. `DateTimeInput` always renders the time
portion; the antd picker needed telling. Kept for source compatibility
rather than editing the consumer (frontier rule).
- `localFormat` keeps its meaning — it selects between `dayjs().format()`
(local, with offset) and `.tz().toISOString()` (UTC) on the way OUT. On the
way IN the ISO string is parsed by dayjs either way.
- antd's `ref` (a `GetRef<typeof DatePicker>` imperative handle) is DROPPED.
Astryx uses a `handleRef` convention rather than `ref` + `GetRef`
(MAPPING §6.2), and no consumer holds this ref.
- `disabledDate(dayjs)` returns `true` to DISABLE a date, while an Astryx
`dateConstraints` entry returns `true` to ALLOW it, so the predicate is
negated (and the native `Date` wrapped back into a `dayjs`).
*/
var s=t(),c=e(a(),1),l=r(),u=e=>{"use memo";let t=(0,s.c)(27),r,a,u,d,f,p,m,h;if(t[0]!==e){let{value:n,onChange:i,localFormat:o,label:s,disabled:c,placeholder:l,showTime:g,disabledDate:_,...v}=e;h=n,f=i,d=o,u=s,r=c,p=l,a=_,m=v,t[0]=e,t[1]=r,t[2]=a,t[3]=u,t[4]=d,t[5]=f,t[6]=p,t[7]=m,t[8]=h}else r=t[1],a=t[2],u=t[3],d=t[4],f=t[5],p=t[6],m=t[7],h=t[8];let g;t[9]!==f||t[10]!==h?(g={value:h,onChange:f},t[9]=f,t[10]=h,t[11]=g):g=t[11];let[,_]=i(g),v;t[12]===h?v=t[13]:(v=h?(0,c.default)(h).format(`YYYY-MM-DDTHH:mm`):void 0,t[12]=h,t[13]=v);let y;t[14]!==d||t[15]!==_?(y=e=>{if(n(e)||e===``){_(void 0);return}let t=(0,c.default)(e);_(d?t.format():t.tz().toISOString())},t[14]=d,t[15]=_,t[16]=y):y=t[16];let b;t[17]===a?b=t[18]:(b=a?[e=>!a((0,c.default)(e))]:void 0,t[17]=a,t[18]=b);let x;return t[19]!==r||t[20]!==u||t[21]!==p||t[22]!==m||t[23]!==v||t[24]!==y||t[25]!==b?(x=(0,l.jsx)(o,{value:v,onChange:y,"aria-label":u,disabled:r,placeholder:p,hourFormat:`24h`,hasClear:!0,width:`100%`,dateConstraints:b,...m}),t[19]=r,t[20]=u,t[21]=p,t[22]=m,t[23]=v,t[24]=y,t[25]=b,t[26]=x):x=t[26],x};u.displayName=`DatePickerISO`;export{u as t};
