/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var e=/[\s'"\\$`]/,t=[[`\\`,`\\\\`],[`"`,`\\"`],[`
`,`\\n`],[`	`,`\\t`],[`\r`,`\\r`]],n={"\\":`\\`,'"':`"`,n:`
`,t:`	`,r:`\r`};function r(n){return n.map(n=>{if(!e.test(n))return n;let r=n;for(let[e,n]of t)r=r.split(e).join(n);return`"${r}"`}).join(` `)}function i(e){let t=[],r=``,i=!1,a=!1,o=!1,s=!1;for(let c=0;c<e.length;c++){let l=e[c];o?(r+=n[l]??l,o=!1):l===`\\`&&!i?o=!0:l===`'`&&!a?(i=!i,s=!0):l===`"`&&!i?(a=!a,s=!0):(l===` `||l===`	`||l===`
`)&&!i&&!a?(r.length>0||s)&&(t.push(r),r=``,s=!1):r+=l}return(r.length>0||s)&&t.push(r),t}export{i as n,r as t};
