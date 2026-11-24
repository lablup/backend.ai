import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";/* empty css            */import{t as n}from"./jsx-runtime-BapUIyWk.js";import{t as r}from"./SessionDetailDrawer-D0rtmtC2.js";import{G as i,rt as a}from"./helper-BWFKT_2Y.js";import{t as o}from"./react-relay-BfoHYpUf.js";import{t as s}from"./BAIUnmountAfterClose-Cxr4Dp_U.js";import{n as c}from"./SessionActionButtons-BKP8A1TC.js";var l=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`sessionId`}],t=[{kind:`Variable`,name:`id`,variableName:`sessionId`}],n={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},r={alias:null,args:null,kind:`ScalarField`,name:`row_id`,storageKey:null};return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`ContainerLogModalWithLazyQueryLoaderQuery`,selections:[{alias:null,args:t,concreteType:`ComputeSessionNode`,kind:`LinkedField`,name:`compute_session_node`,plural:!1,selections:[{args:null,kind:`FragmentSpread`,name:`ContainerLogModalFragment`}],storageKey:null}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`ContainerLogModalWithLazyQueryLoaderQuery`,selections:[{alias:null,args:t,concreteType:`ComputeSessionNode`,kind:`LinkedField`,name:`compute_session_node`,plural:!1,selections:[n,r,{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`access_key`,storageKey:null},{alias:null,args:null,concreteType:`KernelConnection`,kind:`LinkedField`,name:`kernel_nodes`,plural:!1,selections:[{alias:null,args:null,concreteType:`KernelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`KernelNode`,kind:`LinkedField`,name:`node`,plural:!1,selections:[n,r,{alias:null,args:null,kind:`ScalarField`,name:`container_id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_idx`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_role`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`cluster_hostname`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:`89fc3e7f92ccd61c1a3e682390072ccb`,id:null,metadata:{},name:`ContainerLogModalWithLazyQueryLoaderQuery`,operationKind:`query`,text:`query ContainerLogModalWithLazyQueryLoaderQuery(
  $sessionId: GlobalIDField!
) {
  compute_session_node(id: $sessionId) {
    ...ContainerLogModalFragment
    id
  }
}

fragment ContainerLogModalFragment on ComputeSessionNode {
  id
  row_id
  name
  status
  access_key
  kernel_nodes {
    edges {
      node {
        id
        row_id
        container_id
        cluster_idx
        cluster_role
        cluster_hostname
      }
    }
  }
}
`}}})();l.hash=`5e3c1a9c71ef2548c32579df194e26ee`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var u=o(),d=n(),f=({sessionId:e,open:t,loading:n,onRequestClose:r})=>{let{compute_session_node:i}=(0,u.useLazyLoadQuery)(l,{sessionId:e},{fetchPolicy:e?`network-only`:`store-only`});return(0,d.jsx)(s,{children:(0,d.jsx)(c,{sessionFrgmt:i||null,open:t,loading:n,onCancel:()=>{r&&r()}})})},p=e(t(),1),m=({project:e})=>{
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
let t=a(),n=i(),o=new URLSearchParams(t.search).get(`sessionDetail`),c=e=>{let r=new URLSearchParams(t.search);e===null?r.delete(`sessionDetail`):r.set(`sessionDetail`,e),n({pathname:t.pathname,hash:t.hash,search:r.toString()},{replace:!0})},[l,u]=(0,p.useState)(),[m,h]=(0,p.useTransition)();return(0,p.useEffect)(()=>{let e=e=>{h(()=>{u(e.detail)})};return document.addEventListener(`bai-open-session-log`,e),()=>{document.removeEventListener(`bai-open-session-log`,e)}},[h,u]),(0,d.jsxs)(d.Fragment,{children:[(0,d.jsx)(s,{children:(0,d.jsx)(r,{open:!!o,sessionId:o||void 0,project:e,onClose:()=>{c(null)}})}),(0,d.jsx)(f,{open:!!l||m,loading:m,sessionId:l,onRequestClose:()=>{u(void 0)}})]})};export{m as default};
