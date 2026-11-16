import{t as e}from"./jsx-runtime-BapUIyWk.js";import{t}from"./Button-BKkkrlg5.js";import{t as n}from"./IconButton-DGkWhkpU.js";import{n as r}from"./Skeleton-D35z7Ria.js";import{t as i}from"./astryxLabel-C5P0iFEX.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

`BAIButton` on Astryx (to-astryx phase 3, wave 2 / ticket W2-D).

FRONTIER COMPONENT. 81 call sites in 20 files, plus six components that
declare `interface XProps extends BAIButtonProps` and spread the bag straight
through (`SFTPServerButton[V2]`, `FileBrowserButton[V2]`,
`SwitchToProjectButton`, `ImportArtifactRevisionToFolderButton`,
`BAIArtifactRevision{Delete,Download}Button`). Per the
frontier rule the public prop surface stays antd `Button`-SHAPED so none of
them change; only the internals move to Astryx, and `ButtonProps` is replaced
by a locally-declared interface so this module — the #5 taint hub at 576
files — drops out of the antd import graph (P15).

Split (MAPPING §3.3):

`icon` and no children     -> `IconButton` (icon-only row action)
everything else            -> `Button`

`type="primary"`           -> `variant="primary"`
`type="text" | "link"`     -> `variant="ghost"`
`type="default"` / absent  -> `variant="secondary"`
`danger`                   -> `variant="destructive"` (wins over `type`)
`size: small|middle|large` -> `sm|md|lg`
`loading`                  -> `isLoading`
`disabled`                 -> `isDisabled`
`block`                    -> `width="100%"`
`title`                    -> `tooltip`
`children`                 -> `children` + a flattened `label`

PILOT-DECISION — **`action` becomes `clickAction`, and the hand-rolled
transition is deleted.** SKILL.md calls this out explicitly: "`clickAction` is
a native match for `BAIButton.action`". The old body was `useTransition` + an
`isRunningRef` re-entrancy guard + `loading={isPending || props.loading}`;
Astryx's `clickAction` shows the spinner while the returned promise is
pending, sets `aria-busy`, and dedupes re-clicks itself. 18 `action` call
sites keep working with strictly better a11y (antd announced nothing).

PILOT-DECISION — **`type="link"` renders a ghost Button, not `Link`.**
MAPPING §3.3 routes `type="link"` to Astryx `Link`, which is anchor-first. The
three `type="link"` sites here (`SwitchToProjectButton`, `RoleDetail*`) are
pure-`onClick` router/mutation actions with no `href` — no `BAIButton` call
site in the repo passes `href` at all — so `Link` would mean a
destination-less `<a>`, exactly what D3 rejected for `BAILink`. `ghost` keeps
button semantics and the low-emphasis look.

PILOT-DECISION — **`type="dashed"` (5 sites) becomes `variant="secondary"`.**
MAPPING §3.3: "no equivalent -> `variant="secondary"`, record the decision".
The dashed border was antd's "add another one of these" affordance; Astryx's
closed variant enum cannot express a border style (P5), and the five sites all
sit next to a `+` icon that carries the same meaning.

PILOT-DECISION — **icon-only buttons fall back to a generic accessible name,
and the real copy is queued.** 46 of the 168 call sites are icon-only and only
7 of those carry an `aria-label` or `title`, so ~39 icon-only buttons have NO
accessible name under antd — a screen reader announces "button". Astryx makes
`label` required, and SKILL.md is explicit that "a wrapper can only supply a
placeholder". So the resolution order is `children` text -> `aria-label` ->
`title` -> `general.button.Action`. The placeholder is deliberately visible in
an accessibility audit rather than silently empty; naming each of those ~39
controls is per-surface copywriting (P8) and is queued for REMAINDER.md, not
guessed here.

PILOT-DECISION — **antd's `ghost`, `shape`, `htmlType` and `iconPosition` are
not in the surface.** No call site in the repo passes any of them to
`BAIButton` (measured across 168 sites in 72 files), and each is either a
closed-enum loss (P5, `ghost` / `shape="circle"`) or expressible another way
(`htmlType` -> Astryx's `type`, which IS the HTML button type). Declaring
props nothing passes would invite call sites that then break.
*/
var a=e(),o={small:`sm`,middle:`md`,large:`lg`},s=({action:e,type:s,size:c,icon:l,loading:u,disabled:d,danger:f,block:p,color:m,variant:h,children:g,onClick:_,title:v,style:y,...b})=>{let x=s??h,S=f||m===`danger`?`destructive`:x===`primary`||x===`solid`?`primary`:x===`text`||x===`link`?`ghost`:`secondary`,{t:C}=r(),w=!!l&&g==null,T=i(g)||(b[`aria-label`]??``)||(typeof v==`string`?v:``)||(w?C(`general.button.Action`):``),E={...b,variant:S,size:c?o[c]:void 0,isLoading:u,isDisabled:d,tooltip:typeof v==`string`?v:void 0,onClick:_,clickAction:e,style:y};return w?(0,a.jsx)(n,{...E,icon:l,label:T}):(0,a.jsx)(t,{...E,icon:l,label:T,width:p?`100%`:void 0,children:g})};export{s as t};
