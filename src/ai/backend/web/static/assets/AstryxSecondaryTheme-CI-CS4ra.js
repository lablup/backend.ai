import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{t}from"./jsx-runtime-BapUIyWk.js";import{_ as n}from"./usePressFeedback-BIoIGSxE.js";import{S as r,w as i}from"./DefaultProviders-BFjPhnQa.js";import{s as a}from"./app-shim-DTEBzR8d.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

Astryx counterpart of `ThemeAdminProvider` (to-astryx ticket 02): wraps an
admin region in a nested `<Theme>` carrying the admin accent
(theme.json `colorInfo`).

The explicit `mode` is NOT optional politeness. Measured (pilot phase 3b +
re-verified in this ticket's probe): a nested `<Theme>` with no `mode` prop
falls back to `system` — NOT to the parent's resolved mode — so with
OS=light and the app set to dark, the admin region renders light inside a
dark page. `useTheme().mode` returns the nearest ancestor Theme's RESOLVED
mode ('light' | 'dark', never 'system'), which is the Astryx equivalent of
the `isParentDark` read `ThemeAdminProvider` performs on the parent
ConfigProvider — and unlike the app-level `useThemeMode`, it also follows
deliberately inverted/forced ancestor regions.
*/
var o=e(),s=t(),c=e=>{"use memo";let t=(0,o.c)(7),{children:c}=e,{rawThemeConfig:l,activeThemeFamily:u}=i(),{mode:d}=n(),f=l==null?void 0:l.theme,p;t[0]!==u||t[1]!==f?(p=r(f,`admin`,u),t[0]=u,t[1]=f,t[2]=p):p=t[2];let m=p,h;return t[3]!==c||t[4]!==d||t[5]!==m?(h=(0,s.jsx)(a,{theme:m,mode:d,children:c}),t[3]=c,t[4]=d,t[5]=m,t[6]=h):h=t[6],h},l=e=>{"use memo";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

Astryx counterpart of `ThemeSecondaryProvider` (to-astryx ticket 02): wraps
a region in a nested `<Theme>` carrying the secondary accent (theme.json
`colorSuccess`, the secondary role accent).

`mode` is passed explicitly from the nearest ancestor Theme's resolved mode
— nested Astryx Themes do NOT inherit mode (they fall back to `system`).
See `AstryxAdminTheme.tsx` for the measured failure this prevents.
*/
let t=(0,o.c)(7),{children:c}=e,{rawThemeConfig:l,activeThemeFamily:u}=i(),{mode:d}=n(),f=l==null?void 0:l.theme,p;t[0]!==u||t[1]!==f?(p=r(f,`secondary`,u),t[0]=u,t[1]=f,t[2]=p):p=t[2];let m=p,h;return t[3]!==c||t[4]!==d||t[5]!==m?(h=(0,s.jsx)(a,{theme:m,mode:d,children:c}),t[3]=c,t[4]=d,t[5]=m,t[6]=h):h=t[6],h};export{c as n,l as t};
