import{c4 as y,e as k,r as c,cL as d,cM as K}from"./index-CwWAznqi.js";import{r as m}from"./icons-BgdBQS0N.js";const g=(function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"id"},{defaultValue:null,kind:"LocalArgument",name:"scope"}],a=[{fields:[{fields:[{kind:"Variable",name:"equals",variableName:"id"}],kind:"ObjectValue",name:"id"}],kind:"ObjectValue",name:"filter"},{kind:"Literal",name:"limit",value:1},{kind:"Variable",name:"scope",variableName:"scope"}],l={alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"hooksUsingRelay_ScopedImageReferenceQuery",selections:[{alias:null,args:a,concreteType:"ImageV2Connection",kind:"LinkedField",name:"scopedImagesV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"node",plural:!1,selections:[l],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"hooksUsingRelay_ScopedImageReferenceQuery",selections:[{alias:null,args:a,concreteType:"ImageV2Connection",kind:"LinkedField",name:"scopedImagesV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"node",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"fab5172f99ca7cbdd0a8ce894b1dff41",id:null,metadata:{},name:"hooksUsingRelay_ScopedImageReferenceQuery",operationKind:"query",text:`query hooksUsingRelay_ScopedImageReferenceQuery(
  $id: UUID!
  $scope: ImageSearchScope!
) {
  scopedImagesV2(scope: $scope, filter: {id: {equals: $id}}, limit: 1) {
    edges {
      node {
        identity {
          canonicalName
          architecture
        }
        id
      }
    }
  }
}
`}}})();g.hash="64331ab01b07af6759f80b8c8fd0f0a4";const p=(function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"name"}],a=[{alias:null,args:[{kind:"Variable",name:"name",variableName:"name"}],concreteType:"KeyPairResourcePolicy",kind:"LinkedField",name:"keypair_resource_policy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"max_containers_per_session",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_concurrent_sessions",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"hooksUsingRelay_KeyPairResourcePolicyQuery",selections:a,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"hooksUsingRelay_KeyPairResourcePolicyQuery",selections:a},params:{cacheID:"ad7039c1935637fe3f3841f0ea8bf347",id:null,metadata:{},name:"hooksUsingRelay_KeyPairResourcePolicyQuery",operationKind:"query",text:`query hooksUsingRelay_KeyPairResourcePolicyQuery(
  $name: String!
) {
  keypair_resource_policy(name: $name) {
    max_containers_per_session
    max_concurrent_sessions
  }
}
`}}})();p.hash="f3f7364c63aefe9b03111b584c48c103";const f=(function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"accessKey"}],a=[{alias:null,args:[{kind:"Variable",name:"access_key",variableName:"accessKey"}],concreteType:"KeyPair",kind:"LinkedField",name:"keypair",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_policy",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"concurrency_used",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"hooksUsingRelay_KeyPairQuery",selections:a,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"hooksUsingRelay_KeyPairQuery",selections:a},params:{cacheID:"1f8fc324e9907111de581f5cd2dc3640",id:null,metadata:{},name:"hooksUsingRelay_KeyPairQuery",operationKind:"query",text:`query hooksUsingRelay_KeyPairQuery(
  $accessKey: String!
) {
  keypair(access_key: $accessKey) {
    id
    resource_policy
    concurrency_used
  }
}
`}}})();f.hash="d8f5c91f0fc46a3366f57566ab688d81";const _=(e,a={fetchPolicy:"store-and-network"})=>{const[l,r]=y("first"),{keypair:s}=c.useLazyLoadQuery(f,{accessKey:e},{...a,fetchKey:l+a.fetchKey}),n=m.useCallback(()=>{r()},[r]);return[s,{refresh:n}]},b=(e={fetchPolicy:"store-and-network"})=>{const[a,l]=y("first"),r=k(),[s]=_(r==null?void 0:r._config.accessKey),{keypair_resource_policy:n}=c.useLazyLoadQuery(p,{name:(s==null?void 0:s.resource_policy)||""},{...e,fetchKey:a+e.fetchKey}),i=m.useCallback(()=>{l()},[l]);return[{keypairResourcePolicy:n||{},keypair:s||{},sessionLimitAndRemaining:{max:(n||{}).max_concurrent_sessions||d,remaining:((n||{}).max_concurrent_sessions||d)-((s||{}).concurrency_used||0)}},{refresh:i}]},L=(e,a={fetchPolicy:"store-or-network"})=>{var i,o,t,u;const{id:l}=K(),r={domain:[{value:l}]},s=c.useLazyLoadQuery(g,{id:e??"",scope:{...r,public:!0}},a);if(!e)return;const n=(u=(t=(o=(i=s.scopedImagesV2)==null?void 0:i.edges)==null?void 0:o[0])==null?void 0:t.node)==null?void 0:u.identity;return n!=null&&n.canonicalName?n.architecture?`${n.canonicalName}@${n.architecture}`:n.canonicalName:e};export{L as a,b as u};
//# sourceMappingURL=hooksUsingRelay-BF9vEFTu.js.map
