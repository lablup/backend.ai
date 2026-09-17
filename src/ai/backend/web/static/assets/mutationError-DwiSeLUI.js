/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */const s=r=>{if(r instanceof Error)return r.message;if(Array.isArray(r)){const n=r.map(e=>e!==null&&typeof e=="object"&&"message"in e?String(e.message):String(e)).filter(Boolean);if(n.length>0)return n.join(`
`)}return String(r)};export{s as r};
//# sourceMappingURL=mutationError-DwiSeLUI.js.map
