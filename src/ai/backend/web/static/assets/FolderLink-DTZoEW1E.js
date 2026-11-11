import{Lt as e}from"./icons-Btg1s2wy.js";/* empty css            */import{t}from"./jsx-runtime-BapUIyWk.js";import{K as n}from"./DefaultProviders-BFjPhnQa.js";import{t as r}from"./BAIFlex-BElkJeHW.js";import{t as i}from"./react-relay-BfoHYpUf.js";import{t as a}from"./BAIVFolderIdenticon-pFWv-FjT.js";import{n as o}from"./FolderExplorerOpener-DAkYQMOx.js";var s={argumentDefinitions:[],kind:`Fragment`,metadata:null,name:`FolderLink_vfolderNode`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},{args:null,kind:`FragmentSpread`,name:`VFolderNodeIdenticonFragment`}],type:`VirtualFolderNode`,abstractKey:null};s.hash=`fcdabede98521b5a4d2b25506908e356`;var c={argumentDefinitions:[],kind:`Fragment`,metadata:null,name:`VFolderNodeIdenticonFragment`,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null}],type:`VirtualFolderNode`,abstractKey:null};c.hash=`d78fd4251748b63aa2174c9dfc1a178e`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var l=i(),u=t(),d=({vfolderNodeIdenticonFrgmt:e,style:t})=>{let n=(0,l.useFragment)(c,e);return(0,u.jsx)(a,{seed:n==null?void 0:n.id,style:t})},f=({vfolderNodeFragment:t,folderId:i,folderName:a,showIcon:c,...f})=>{
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
let{generateFolderPath:p}=o(),m=(0,l.useFragment)(s,t);return(0,u.jsxs)(r,{gap:`xs`,align:`start`,style:{minWidth:0,maxWidth:`100%`},children:[m?(0,u.jsx)(d,{vfolderNodeIdenticonFrgmt:m,style:{flexShrink:0,marginTop:`0.25em`}}):c?(0,u.jsx)(e,{style:{flexShrink:0,marginTop:`0.25em`},size:`1em`}):null,(0,u.jsx)(n,{to:p(i??(m==null?void 0:m.row_id)??``),style:{wordBreak:`break-all`,minWidth:0},...f,children:a??(m==null?void 0:m.name)??``})]})};export{f as t};
