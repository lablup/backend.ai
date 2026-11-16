/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var e=e=>{if(e instanceof Error)return e.message;if(Array.isArray(e)){let t=e.map(e=>typeof e==`object`&&e&&`message`in e?String(e.message):String(e)).filter(Boolean);if(t.length>0)return t.join(`
`)}return String(e)};export{e as t};
