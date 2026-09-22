import{i as h,j as v}from"./index-Dd8bt51s.js";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

 to-astryx TICKET 30 — the local replacement for `@lobehub/icons`.

 ## Why this exists

 `@lobehub/icons` declares `@lobehub/ui` as a peerDependency. With
 `auto-install-peers` on, installing the icon set pulled the whole LobeHub
 component library into the tree — and with it `rc-collapse`, `rc-footer`,
 `rc-image`, `rc-input-number` and `rc-menu`, the LAST non-antd `rc-*` paths in
 the lockfile. Three files used the package, for a total of 36 brand glyphs.
 The glyphs are MIT-licensed static SVG, so they are vendored here (see
 `generated/`, produced once by the extractor documented in the ticket) and the
 dependency — plus its ~30 MB peer — is gone.

 ## Shape

 `createBrandIcon` returns a component with the same call surface the three
 consumers used from `@lobehub/icons`' `IconType`: `size`, `style`, `className`.
 The consumers keep their lazy `import()` loaders (one chunk per brand), so the
 bundle only ever carries the brands a page actually renders — the property
 that made the vendored set affordable in the first place.

 ## Why `dangerouslySetInnerHTML`

 The bodies are build-time-extracted static strings — no user input reaches
 them. Several brand marks are multi-path with `<linearGradient>` defs, and
 keeping the markup verbatim is what guarantees the vendored glyph is pixel-
 identical to what shipped before. Re-expressing them as hand-written JSX would
 mean 36 opportunities to silently mangle a path. The gradient ids are rewritten
 at extraction time to a stable `bai-brand-<brand>-<variant>-<n>` token, so two
 instances of the SAME icon share an id (valid enough — the browser resolves to
 the first, and the defs are identical) while different icons never collide.
*/function B(t){const f=p=>{"use memo";const e=h.c(13),{size:g,style:a,className:c,title:x}=p,o=g===void 0?"1em":g,l=x===void 0?t.title:x,m=l===null?"presentation":"img",u=l===null?!0:void 0;let i;e[0]!==a?(i={flex:"none",lineHeight:1,...a},e[0]=a,e[1]=i):i=e[1];let s;e[2]!==l?(s=l===null?"":`<title>${w(l)}</title>`,e[2]=l,e[3]=s):s=e[3];const d=s+t.body;let n;e[4]!==d?(n={__html:d},e[4]=d,e[5]=n):n=e[5];let r;return e[6]!==c||e[7]!==o||e[8]!==m||e[9]!==u||e[10]!==i||e[11]!==n?(r=v.jsx("svg",{className:c,width:o,height:o,viewBox:t.viewBox,fill:t.fill,fillRule:t.fillRule,xmlns:"http://www.w3.org/2000/svg",role:m,"aria-hidden":u,style:i,dangerouslySetInnerHTML:n}),e[6]=c,e[7]=o,e[8]=m,e[9]=u,e[10]=i,e[11]=n,e[12]=r):r=e[12],r};return f.displayName=`BrandIcon(${t.title})`,f}function w(t){return t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}export{B as c};
//# sourceMappingURL=createBrandIcon-Dl8dlz2a.js.map
