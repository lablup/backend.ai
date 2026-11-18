import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{t}from"./jsx-runtime-BapUIyWk.js";var n=e(),r=t();
/**
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
*/
function i(e){let t=t=>{"use memo";let i=(0,n.c)(13),{size:o,style:s,className:c,title:l}=t,u=o===void 0?`1em`:o,d=l===void 0?e.title:l,f=d===null?`presentation`:`img`,p=d===null||void 0,m;i[0]===s?m=i[1]:(m={flex:`none`,lineHeight:1,...s},i[0]=s,i[1]=m);let h;i[2]===d?h=i[3]:(h=d===null?``:`<title>${a(d)}</title>`,i[2]=d,i[3]=h);let g=h+e.body,_;i[4]===g?_=i[5]:(_={__html:g},i[4]=g,i[5]=_);let v;return i[6]!==c||i[7]!==u||i[8]!==f||i[9]!==p||i[10]!==m||i[11]!==_?(v=(0,r.jsx)(`svg`,{className:c,width:u,height:u,viewBox:e.viewBox,fill:e.fill,fillRule:e.fillRule,xmlns:`http://www.w3.org/2000/svg`,role:f,"aria-hidden":p,style:m,dangerouslySetInnerHTML:_}),i[6]=c,i[7]=u,i[8]=f,i[9]=p,i[10]=m,i[11]=_,i[12]=v):v=i[12],v};return t.displayName=`BrandIcon(${e.title})`,t}function a(e){return e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`)}export{i as t};
