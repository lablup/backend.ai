/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const c=/[\s'"\\$`]/,u=[["\\","\\\\"],['"','\\"'],[`
`,"\\n"],["	","\\t"],["\r","\\r"]],a={"\\":"\\",'"':'"',n:`
`,t:"	",r:"\r"};function E(r){return r.map(t=>{if(!c.test(t))return t;let e=t;for(const[l,o]of u)e=e.split(l).join(o);return`"${e}"`}).join(" ")}function h(r){const t=[];let e="",l=!1,o=!1,s=!1,i=!1;for(let f=0;f<r.length;f++){const n=r[f];if(s){e+=a[n]??n,s=!1;continue}if(n==="\\"&&!l){s=!0;continue}if(n==="'"&&!o){l=!l,i=!0;continue}if(n==='"'&&!l){o=!o,i=!0;continue}if((n===" "||n==="	"||n===`
`)&&!l&&!o){(e.length>0||i)&&(t.push(e),e="",i=!1);continue}e+=n}return(e.length>0||i)&&t.push(e),t}export{E as f,h as t};
//# sourceMappingURL=parseCliCommand-DLNI3aPC.js.map
