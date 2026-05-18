import{i as y,j as l,a7 as u,gB as p,aL as L,aa as k,r as i,a as S}from"./index-M9a7wauv.js";import{S as _}from"./SessionDetailDrawer-DdbAmY1L.js";import"./corner-down-left-C3b1tE_4.js";import"./FolderLink-B4Tyaydh.js";import"./zip-CWIpHMud.js";import"./unzip-BNy8xCy7.js";import"./BAIGraphQLPropertyFilter-FbNAR0Ex.js";const c=function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"sessionId"}],s=[{kind:"Variable",name:"id",variableName:"sessionId"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"ContainerLogModalWithLazyQueryLoaderQuery",selections:[{alias:null,args:s,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"ContainerLogModalFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"ContainerLogModalWithLazyQueryLoaderQuery",selections:[{alias:null,args:s,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[a,e,{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[a,e,{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"89fc3e7f92ccd61c1a3e682390072ccb",id:null,metadata:{},name:"ContainerLogModalWithLazyQueryLoaderQuery",operationKind:"query",text:`query ContainerLogModalWithLazyQueryLoaderQuery(
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
`}}}();c.hash="5e3c1a9c71ef2548c32579df194e26ee";const F=({sessionId:n,open:s,loading:a,onRequestClose:e})=>{const{compute_session_node:o}=y.useLazyLoadQuery(c,{sessionId:n},{fetchPolicy:n?"network-only":"store-only"});return l.jsx(u,{children:l.jsx(p,{sessionFrgmt:o||null,open:s,loading:a,onCancel:()=>{e&&e()}})})},Q=()=>{const[n,s]=L("sessionDetail",k),[a,e]=i.useState(),[o,t]=i.useTransition(),r=S();i.useEffect(()=>{const d=m=>{t(()=>{e(m.detail)})};return document.addEventListener("bai-open-session-log",d),()=>{document.removeEventListener("bai-open-session-log",d)}},[t,e]);const g=r==null?void 0:r.supports("session-node");return l.jsxs(l.Fragment,{children:[g?l.jsx(u,{children:l.jsx(_,{open:!!n,sessionId:n||void 0,onClose:()=>{s(null,"replaceIn")}})}):null,l.jsx(F,{open:!!a||o,loading:o,sessionId:a,onRequestClose:()=>{e(void 0)}})]})};export{Q as default};
//# sourceMappingURL=SessionDetailAndContainerLogOpenerLegacy-bOwL2aBZ.js.map
