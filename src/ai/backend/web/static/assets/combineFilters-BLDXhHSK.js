/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var e=(e,t=`AND`)=>{let n=e.filter(e=>!!e);return n.length===0?null:n.length===1&&t!==`NOT`?n[0]:{[t]:n}};export{e as t};
