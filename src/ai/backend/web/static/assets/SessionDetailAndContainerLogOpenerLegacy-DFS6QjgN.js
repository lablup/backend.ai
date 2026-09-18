import{r as k,j as s,ap as p,g6 as h,ad as S,Z as _,l as u,a as F}from"./index-B-6GqBhJ.js";import{S as f}from"./SessionDetailDrawer-_Qk8OrZd.js";import"./scroll-text-CncKp3rA.js";import"./orderBy-BcAKhHRm.js";import"./FolderLink-BixUYyr6.js";import"./zip-DUWDYNfS.js";import"./unzip-DGQyn8Q9.js";import"./ScopedAuditLog-D4HOQVjA.js";import"./BAIGraphQLPropertyFilter-Bp1GJNAy.js";import"./rotate-ccw-clock-DIhz6B-L.js";const y=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"sessionId"}],e=[{kind:"Variable",name:"id",variableName:"sessionId"}],l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},n={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"ContainerLogModalWithLazyQueryLoaderQuery",selections:[{alias:null,args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"ContainerLogModalFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"ContainerLogModalWithLazyQueryLoaderQuery",selections:[{alias:null,args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[l,n,{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,n,{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"89fc3e7f92ccd61c1a3e682390072ccb",id:null,metadata:{},name:"ContainerLogModalWithLazyQueryLoaderQuery",operationKind:"query",text:`query ContainerLogModalWithLazyQueryLoaderQuery(
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
`}}})();y.hash="5e3c1a9c71ef2548c32579df194e26ee";const K=({sessionId:a,open:e,loading:l,onRequestClose:n})=>{const{compute_session_node:r}=k.useLazyLoadQuery(y,{sessionId:a},{fetchPolicy:a?"network-only":"store-only"});return s.jsx(p,{children:s.jsx(h,{sessionFrgmt:r||null,open:e,loading:l,onCancel:()=>{n&&n()}})})},E=({project:a})=>{const e=S(),l=_(),n=new URLSearchParams(e.search).get("sessionDetail"),r=d=>{const o=new URLSearchParams(e.search);o.delete("sessionDetail"),l({pathname:e.pathname,hash:e.hash,search:o.toString()},{replace:!0})},[c,i]=u.useState(),[m,g]=u.useTransition(),t=F();u.useEffect(()=>{const d=o=>{g(()=>{i(o.detail)})};return document.addEventListener("bai-open-session-log",d),()=>{document.removeEventListener("bai-open-session-log",d)}},[g,i]);const L=t==null?void 0:t.supports("session-node");return s.jsxs(s.Fragment,{children:[L?s.jsx(p,{children:s.jsx(f,{open:!!n,sessionId:n||void 0,project:a,onClose:()=>{r()}})}):null,s.jsx(K,{open:!!c||m,loading:m,sessionId:c,onRequestClose:()=>{i(void 0)}})]})};export{E as default};
//# sourceMappingURL=SessionDetailAndContainerLogOpenerLegacy-DFS6QjgN.js.map
