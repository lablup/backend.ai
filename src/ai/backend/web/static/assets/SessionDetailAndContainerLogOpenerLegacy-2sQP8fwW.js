import{k as p,j as l,v as u,hJ as y,aL as L,a5 as k,r,a as S}from"./index-DB7yUW94.js";import{S as _}from"./SessionDetailDrawer-3BikG1o_.js";import"./BAIId-DEscoFqK.js";import"./corner-down-left-YcyydeqR.js";import"./FolderLink-DJPzhdHs.js";import"./zip-DRoFeMJl.js";import"./unzip-kgVO-3Vy.js";import"./ScopedAuditLog-BgqNEK4R.js";import"./camelCase-D3Ek1WIG.js";import"./BAIGraphQLPropertyFilter-URVW9R-R.js";import"./union-CChSQL5X.js";import"./WarningOutlined-BN1g72Bn.js";const c=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"sessionId"}],s=[{kind:"Variable",name:"id",variableName:"sessionId"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"ContainerLogModalWithLazyQueryLoaderQuery",selections:[{alias:null,args:s,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"ContainerLogModalFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"ContainerLogModalWithLazyQueryLoaderQuery",selections:[{alias:null,args:s,concreteType:"ComputeSessionNode",kind:"LinkedField",name:"compute_session_node",plural:!1,selections:[a,e,{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[a,e,{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"89fc3e7f92ccd61c1a3e682390072ccb",id:null,metadata:{},name:"ContainerLogModalWithLazyQueryLoaderQuery",operationKind:"query",text:`query ContainerLogModalWithLazyQueryLoaderQuery(
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
`}}})();c.hash="5e3c1a9c71ef2548c32579df194e26ee";const F=({sessionId:n,open:s,loading:a,onRequestClose:e})=>{const{compute_session_node:o}=p.useLazyLoadQuery(c,{sessionId:n},{fetchPolicy:n?"network-only":"store-only"});return l.jsx(u,{children:l.jsx(y,{sessionFrgmt:o||null,open:s,loading:a,onCancel:()=>{e&&e()}})})},T=()=>{const[n,s]=L("sessionDetail",k.withOptions({history:"replace"})),[a,e]=r.useState(),[o,t]=r.useTransition(),i=S();r.useEffect(()=>{const d=g=>{t(()=>{e(g.detail)})};return document.addEventListener("bai-open-session-log",d),()=>{document.removeEventListener("bai-open-session-log",d)}},[t,e]);const m=i==null?void 0:i.supports("session-node");return l.jsxs(l.Fragment,{children:[m?l.jsx(u,{children:l.jsx(_,{open:!!n,sessionId:n||void 0,onClose:()=>{s(null)}})}):null,l.jsx(F,{open:!!a||o,loading:o,sessionId:a,onRequestClose:()=>{e(void 0)}})]})};export{T as default};
//# sourceMappingURL=SessionDetailAndContainerLogOpenerLegacy-2sQP8fwW.js.map
