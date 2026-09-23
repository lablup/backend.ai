import{aA as L,l as _,j as n,fR as N,c as E,cw as P,at as T,ht as w,i as B,u as H,ab as C,G as D}from"./index-Bg9dLa8r.js";const F=/^#[0-9a-fA-F]{6}$/,R=/^#[0-9a-fA-F]{3}$/,I=/^#[0-9a-fA-F]{8}$/,M=/^rgba?\(([^)]+)\)$/i,v=l=>Math.max(0,Math.min(255,Math.round(l))).toString(16).padStart(2,"0"),A=l=>{if(!l)return null;const e=l.trim();if(F.test(e))return e.toLowerCase();if(I.test(e))return e.slice(0,7).toLowerCase();if(R.test(e)){const[,o,r,i]=e;return`#${o}${o}${r}${r}${i}${i}`.toLowerCase()}const m=M.exec(e);if(m){const o=m[1].split(/[,/\s]+/).filter(Boolean).map(Number);if(o.length>=3&&o.slice(0,3).every(Number.isFinite))return`#${v(o[0])}${v(o[1])}${v(o[2])}`}return null},U=({value:l,onChangeComplete:e,showText:m,allowClear:o,onClear:r,disabled:i,label:f,style:p,"data-testid":t})=>{"use memo";const{t:c}=L(),d=_.useRef(null),[g,h]=_.useState(!1),a=A(l),[x,k]=_.useState(a??"#000000"),[b,S]=_.useState(a??""),j=s=>{const u=A(s);!u||u===a||e==null||e(u)};_.useEffect(()=>{const s=d.current;if(!s)return;const u=()=>j(s.value);return s.addEventListener("change",u),()=>s.removeEventListener("change",u)},[g,a]);const $=f??c("comp:BAIColorPicker.SelectColor");return n.jsx(N,{isOpen:g,onOpenChange:s=>{h(s),s&&(k(a??"#000000"),S(a??""))},label:$,placement:"below",alignment:"start",content:n.jsxs(E,{direction:"column",align:"stretch",gap:"sm",style:{minWidth:200},children:[n.jsx("input",{ref:d,type:"color",className:"bai-color-picker__area","aria-label":$,"data-testid":t?`${t}-area`:void 0,value:x,disabled:i,onChange:s=>{k(s.target.value),S(s.target.value)}}),n.jsx(P,{label:c("comp:BAIColorPicker.HexValue"),isLabelHidden:!0,size:"sm",value:b,placeholder:"#000000",isDisabled:i,"data-testid":t?`${t}-hex`:void 0,onChange:s=>{S(s);const u=A(s);u&&(k(u),j(u))},onEnter:()=>j(b)}),o?n.jsx(T,{variant:"ghost",size:"sm",label:c("comp:BAIColorPicker.Clear"),"data-testid":t?`${t}-clear`:void 0,isDisabled:i,onClick:()=>{r==null||r(),h(!1)}}):null]}),children:n.jsxs("button",{type:"button",className:"bai-color-picker__trigger",disabled:i,style:p,"data-testid":t,"aria-label":m?void 0:$,children:[n.jsx("span",{className:"bai-color-picker__swatch","aria-hidden":"true",children:n.jsx("span",{className:"bai-color-picker__swatch-fill",style:{backgroundColor:a??"transparent"}})}),m?n.jsx("span",{"data-testid":t?`${t}-value`:void 0,children:a??c("comp:BAIColorPicker.NoColor")}):null]})})};/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

 `theme.getDesignToken({ algorithm })` without antd (to-astryx final-A).

 Three settings controls — the Branding `ThemeColorPicker` and
 `FontFamilySettingItem`, and the User Settings `ThemeAccentColorPicker` — are
 theme-ALGORITHM *producers* rather than token consumers: they do not paint
 with a token, they show the value a *cleared* field falls back to. antd
 answered that with `theme.getDesignToken({ algorithm: theme.defaultAlgorithm |
 theme.darkAlgorithm })`, i.e. "run the palette algorithm over antd's own stock
 seeds". Those three call sites were the last thing holding `import { theme }
 from 'antd'` in the app.

 The theme-shim's `buildTokens(mode, seeds)` is the same function: step 3 sets
 each seed token to `palette(seed, mode)(6)` from the vendored, parity-tested
 port of `@ant-design/colors`. Feeding it antd's stock seeds reproduces
 `getDesignToken` exactly for every colour these controls read — verified
 against the still-installed package:

     colorPrimary  light #1677ff  dark #1668dc
     colorLink     light #1677ff  dark #1668dc
     colorInfo     light #1677ff  dark #1668dc
     colorError    light #ff4d4f  dark #dc4446
     colorSuccess  light #52c41a  dark #49aa19
     colorWarning  light #faad14  dark #d89614

 Two deliberate differences, both the ratified visual-value policy rather than
 a regression:

 1. `colorText` is an `astryx`-verdict token, so it resolves from the live
    Astryx cascade (`--color-text-primary`) instead of antd's
    `rgba(0,0,0,0.88)` / `rgba(255,255,255,0.85)`. That is the value the app
    actually paints, which is what a "this is your fallback" swatch should
    show. (mapping.ts records the same drift for `colorText`.)
 2. `fontFamily` is a seed, not a derivation, so it is stated below. antd's
    stock stack is kept verbatim; it is what the field showed before.

 Component tokens (`token.Layout.headerBg`) are NOT covered — `getDesignToken`
 never returned them either, so the Branding "header background" swatch had no
 fallback before this change and still has none.
*/const G={colorPrimary:"#1677ff",colorLink:"#1677ff",colorInfo:"#1677ff",colorError:"#ff4d4f",colorSuccess:"#52c41a",colorWarning:"#faad14",fontFamily:`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
'Noto Color Emoji'`},y=new Map,W=l=>{let e=y.get(l);return e||(e=w(l,G),y.set(l,e)),e},X=l=>{"use memo";const e=B.c(18),{light:m,dark:o}=l,{t:r}=H(),{token:i}=C.useToken();let f;e[0]!==r?(f=r("userSettings.LightMode"),e[0]=r,e[1]=f):f=e[1];let p;e[2]!==m||e[3]!==f?(p={label:f,pickerProps:m},e[2]=m,e[3]=f,e[4]=p):p=e[4];let t;e[5]!==r?(t=r("userSettings.DarkMode"),e[5]=r,e[6]=t):t=e[6];let c;e[7]!==o||e[8]!==t?(c={label:t,pickerProps:o},e[7]=o,e[8]=t,e[9]=c):c=e[9];let d;e[10]!==p||e[11]!==c?(d=[p,c],e[10]=p,e[11]=c,e[12]=d):d=e[12];const g=d;let h;e[13]===Symbol.for("react.memo_cache_sentinel")?(h={alignSelf:"stretch"},e[13]=h):h=e[13];let a;e[14]===Symbol.for("react.memo_cache_sentinel")?(a={minWidth:300,max:4},e[14]=a):a=e[14];let x;return e[15]!==g||e[16]!==i?(x=n.jsx(E,{align:"stretch",direction:"column",style:h,children:n.jsx(D,{columns:a,columnGap:4,rowGap:1,children:g.map(k=>{const{label:b,pickerProps:S}=k;return n.jsxs(E,{gap:"sm",style:{color:i.colorTextTertiary},wrap:"wrap",children:[b,":",n.jsx(U,{showText:!0,label:b,style:{minWidth:110},...S})]},b)})})}),e[15]=g,e[16]=i,e[17]=x):x=e[17],x};export{X as L,W as g};
//# sourceMappingURL=LightDarkColorPicker-BYKeSG4l.js.map
