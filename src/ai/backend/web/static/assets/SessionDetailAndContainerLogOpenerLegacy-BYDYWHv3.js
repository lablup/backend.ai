import{r as p,j as l,an as m,gB as L,ac as k,X as h,l as d}from"./index-4XAoWQdC.js";import{S}from"./SessionDetailDrawer-r93Udkje.js";import"./scroll-text-CMSbKmDU.js";import"./orderBy-DR_M0o9Z.js";import"./FolderLink-B13SaUe_.js";import"./ScopedAuditLog-BTAaHqWC.js";import"./rotate-ccw-clock-Bp9ZfyAh.js";const y=(function(){var a=[{defaultValue:null,kind:"LocalArgument",name:"sessionId"}],e=[{kind:"Variable",name:"id",variableName:"sessionId"}],s={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},n={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:a,kind:"Fragment",metadata:null,name:"ContainerLogModalWithLazyQueryLoaderQuery",selections:[{alias:null,args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"ContainerLogModalFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:a,kind:"Operation",name:"ContainerLogModalWithLazyQueryLoaderQuery",selections:[{alias:null,args:e,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[s,n,{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[s,n,{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"89fc3e7f92ccd61c1a3e682390072ccb",id:null,metadata:{},name:"ContainerLogModalWithLazyQueryLoaderQuery",operationKind:"query",text:`query ContainerLogModalWithLazyQueryLoaderQuery(
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
`}}})();y.hash="5e3c1a9c71ef2548c32579df194e26ee";const _=({sessionId:a,open:e,loading:s,onRequestClose:n})=>{const{compute_session_node:r}=p.useLazyLoadQuery(y,{sessionId:a},{fetchPolicy:a?"network-only":"store-only"});return l.jsx(m,{children:l.jsx(L,{sessionFrgmt:r||null,open:e,loading:s,onCancel:()=>{n&&n()}})})},M=({project:a})=>{const e=k(),s=h(),n=new URLSearchParams(e.search).get("sessionDetail"),r=t=>{const o=new URLSearchParams(e.search);o.delete("sessionDetail"),s({pathname:e.pathname,hash:e.hash,search:o.toString()},{replace:!0})},[u,i]=d.useState(),[c,g]=d.useTransition();return d.useEffect(()=>{const t=o=>{g(()=>{i(o.detail)})};return document.addEventListener("bai-open-session-log",t),()=>{document.removeEventListener("bai-open-session-log",t)}},[g,i]),l.jsxs(l.Fragment,{children:[l.jsx(m,{children:l.jsx(S,{open:!!n,sessionId:n||void 0,project:a,onClose:()=>{r()}})}),l.jsx(_,{open:!!u||c,loading:c,sessionId:u,onRequestClose:()=>{i(void 0)}})]})};export{M as default};
//# sourceMappingURL=SessionDetailAndContainerLogOpenerLegacy-BYDYWHv3.js.map
