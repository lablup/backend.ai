import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Rn as t,Zn as n,gn as r,mt as i,pt as a}from"./icons-Btg1s2wy.js";import{Jt as o,Ut as s,at as c,ot as l,ut as u,vt as d}from"./lodash-ClfL87UH.js";import{t as f}from"./jsx-runtime-BapUIyWk.js";import{_ as p}from"./usePressFeedback-BIoIGSxE.js";import{K as m}from"./DefaultProviders-BFjPhnQa.js";import{n as h}from"./Skeleton-D35z7Ria.js";import{t as g}from"./BAIFlex-BElkJeHW.js";import{t as _}from"./vfolderHostPermission-DEsjvwOu.js";import{n as v}from"./hooks-UUY7pxyu.js";import{t as y}from"./react-relay-BfoHYpUf.js";import{t as b}from"./BAISelect-D7nL9svF.js";import{t as x}from"./BAIModal-XZIjYM23.js";import{t as S}from"./BAITable-BRd_Ua6I.js";
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

`BAIAllowedHostNamesSelect` on Astryx (to-astryx phase 3, wave 2 / W2-D).

antd `Select` + `Select.Option` children -> `BAISelect` with an `options`
array. `BAISelect` is now the Astryx-backed frontier wrapper (this file's
sibling), so this module keeps its antd-shaped surface (`mode="multiple"`,
`allowClear`, `placeholder`, `style`, `value`, `onChange`) with no direct antd
import of its own (P15).

PILOT-DECISION — **`Select.Option` children become `options`.** MAPPING §3.1
lists `OptGroup`/child-option syntax as having no destination; Astryx's
`Selector` is `options`-driven only. The two shapes were already equivalent
here (a flat list of `{value, label}` pairs where label === value), so this is
a rewrite of the call, not a change of behaviour.
*/
var C=f(),w=({...e})=>{let t=v();return(0,C.jsx)(b,{...e,options:d(t,e=>({value:e,label:e}))})},T={argumentDefinitions:[],kind:`Fragment`,metadata:null,name:`BAIAllowedVfolderHostsWithPermissionFromKeyPairResourcePolicyFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`allowed_vfolder_hosts`,storageKey:null}],type:`KeyPairResourcePolicy`,abstractKey:null};T.hash=`a9c58cd69e62182cd7a68a75e81c48c7`;var E={argumentDefinitions:[],kind:`Fragment`,metadata:null,name:`BAIAllowedVfolderHostsWithPermissionFromGroupFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`allowed_vfolder_hosts`,storageKey:null}],type:`GroupNode`,abstractKey:null};E.hash=`27383c90858e3deb78916da7a2df8518`;var D=(function(){var e=[{alias:null,args:null,concreteType:`PredefinedAtomicPermission`,kind:`LinkedField`,name:`vfolder_host_permissions`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`vfolder_host_permission_list`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:`Fragment`,metadata:null,name:`BAIAllowedVfolderHostsWithPermissionQuery`,selections:e,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[],kind:`Operation`,name:`BAIAllowedVfolderHostsWithPermissionQuery`,selections:e},params:{cacheID:`c0663cd792c7e10aaf1f1c8a7a572192`,id:null,metadata:{},name:`BAIAllowedVfolderHostsWithPermissionQuery`,operationKind:`query`,text:`query BAIAllowedVfolderHostsWithPermissionQuery {
  vfolder_host_permissions {
    vfolder_host_permission_list
  }
}
`}}})();D.hash=`50ff00f392a8e1476b30a736f2c09523`;var O=e(n(),1),k=y(),A=({allowedHostPermissionFrgmtFromKeyPair:e,allowedHostPermissionFrgmtFromGroup:n,allowedVfolderHostEntries:f})=>{let{t:v}=h(),{token:y}=p(),[b,w]=O.useState(),A=(0,k.useFragment)(T,e),j=(0,k.useFragment)(E,n),M=f?_(f):JSON.parse((A==null?void 0:A.allowed_vfolder_hosts)||(j==null?void 0:j.allowed_vfolder_hosts)||`{}`),{vfolder_host_permissions:N}=(0,k.useLazyLoadQuery)(D,{}),P=e=>{var t;return c(new Set(M[e]),new Set((N==null?void 0:N.vfolder_host_permission_list)||null))?`success`:((t=M[e])==null?void 0:t.length)>0?`warning`:`error`};return(0,C.jsxs)(C.Fragment,{children:[(0,C.jsx)(g,{gap:`xs`,wrap:`wrap`,children:d(o(M),e=>{let t=P(e);return(0,C.jsx)(m,{onClick:()=>{w(e)},type:`hover`,children:(0,C.jsxs)(g,{gap:`xxs`,align:`center`,children:[t===`error`?(0,C.jsx)(a,{size:14,"aria-hidden":`true`,focusable:!1,style:{color:y(`--color-error`)}}):(0,C.jsx)(i,{size:14,"aria-hidden":`true`,focusable:!1,style:{color:y(t===`success`?`--color-success`:`--color-warning`)}}),e]})},e)})}),(0,C.jsx)(x,{centered:!0,title:`${b} ${v(`comp:AllowedVfolderHostsWithPermission.Permission`)}`,open:!l(b),onCancel:()=>w(null),footer:null,children:(0,C.jsx)(S,{pagination:!1,size:`small`,dataSource:d(N==null?void 0:N.vfolder_host_permission_list,e=>({key:e,permission:e,isAllowed:u(s(M,b||``),e)})),columns:[{title:v(`comp:AllowedVfolderHostsWithPermission.Permission`),dataIndex:`permission`,key:`permission`},{title:v(`comp:AllowedVfolderHostsWithPermission.Allowed`),dataIndex:`isAllowed`,key:`isAllowed`,render:e=>(0,C.jsx)(g,{justify:`center`,children:e?(0,C.jsx)(r,{style:{color:y(`--preset-green-5`),fontSize:y(`--font-size-lg`)},size:`1em`}):(0,C.jsx)(t,{style:{color:y(`--preset-red-5`),fontSize:y(`--font-size-lg`)},size:`1em`})})}]})})]})};export{w as n,A as t};
