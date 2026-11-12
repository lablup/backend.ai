import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";/* empty css            */import{s as n}from"./useThemeMode-Dg5yAWy7.js";import{H as r,z as i}from"./helper-BWFKT_2Y.js";import{t as a}from"./react-relay-BfoHYpUf.js";import"./helper-DF1Eunoe.js";import"./const-vars-C9oKr_t-.js";var o=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`accessKey`}],t=[{alias:null,args:[{kind:`Variable`,name:`access_key`,variableName:`accessKey`}],concreteType:`KeyPair`,kind:`LinkedField`,name:`keypair`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`resource_policy`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`concurrency_used`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`hooksUsingRelay_KeyPairQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`hooksUsingRelay_KeyPairQuery`,selections:t},params:{cacheID:`1f8fc324e9907111de581f5cd2dc3640`,id:null,metadata:{},name:`hooksUsingRelay_KeyPairQuery`,operationKind:`query`,text:`query hooksUsingRelay_KeyPairQuery(
  $accessKey: String!
) {
  keypair(access_key: $accessKey) {
    id
    resource_policy
    concurrency_used
  }
}
`}}})();o.hash=`d8f5c91f0fc46a3366f57566ab688d81`;var s=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`name`}],t=[{alias:null,args:[{kind:`Variable`,name:`name`,variableName:`name`}],concreteType:`KeyPairResourcePolicy`,kind:`LinkedField`,name:`keypair_resource_policy`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`max_containers_per_session`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`max_concurrent_sessions`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`hooksUsingRelay_KeyPairResourcePolicyQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`hooksUsingRelay_KeyPairResourcePolicyQuery`,selections:t},params:{cacheID:`ad7039c1935637fe3f3841f0ea8bf347`,id:null,metadata:{},name:`hooksUsingRelay_KeyPairResourcePolicyQuery`,operationKind:`query`,text:`query hooksUsingRelay_KeyPairResourcePolicyQuery(
  $name: String!
) {
  keypair_resource_policy(name: $name) {
    max_containers_per_session
    max_concurrent_sessions
  }
}
`}}})();s.hash=`f3f7364c63aefe9b03111b584c48c103`;var c=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`id`}],t=[{kind:`Variable`,name:`id`,variableName:`id`}],n={alias:null,args:null,concreteType:`ImageV2IdentityInfo`,kind:`LinkedField`,name:`identity`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`canonicalName`,storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`hooksUsingRelay_ImageCanonicalNameQuery`,selections:[{alias:null,args:t,concreteType:`ImageV2`,kind:`LinkedField`,name:`imageV2`,plural:!1,selections:[n],storageKey:null}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`hooksUsingRelay_ImageCanonicalNameQuery`,selections:[{alias:null,args:t,concreteType:`ImageV2`,kind:`LinkedField`,name:`imageV2`,plural:!1,selections:[n,{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null}],storageKey:null}]},params:{cacheID:`558d007b29459001f7e11ab7c77f04bf`,id:null,metadata:{},name:`hooksUsingRelay_ImageCanonicalNameQuery`,operationKind:`query`,text:`query hooksUsingRelay_ImageCanonicalNameQuery(
  $id: ID!
) {
  imageV2(id: $id) {
    identity {
      canonicalName
    }
    id
  }
}
`}}})();c.hash=`2b692ed8ddc7d228e00b9577e8585a15`;var l=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`id`},{defaultValue:null,kind:`LocalArgument`,name:`scope`}],t=[{fields:[{fields:[{kind:`Variable`,name:`equals`,variableName:`id`}],kind:`ObjectValue`,name:`id`}],kind:`ObjectValue`,name:`filter`},{kind:`Literal`,name:`limit`,value:1},{kind:`Variable`,name:`scope`,variableName:`scope`}],n={alias:null,args:null,concreteType:`ImageV2IdentityInfo`,kind:`LinkedField`,name:`identity`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`canonicalName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`architecture`,storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`hooksUsingRelay_ScopedImageReferenceQuery`,selections:[{alias:null,args:t,concreteType:`ImageV2Connection`,kind:`LinkedField`,name:`scopedImagesV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`ImageV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ImageV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[n],storageKey:null}],storageKey:null}],storageKey:null}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`hooksUsingRelay_ScopedImageReferenceQuery`,selections:[{alias:null,args:t,concreteType:`ImageV2Connection`,kind:`LinkedField`,name:`scopedImagesV2`,plural:!1,selections:[{alias:null,args:null,concreteType:`ImageV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ImageV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[n,{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:`fab5172f99ca7cbdd0a8ce894b1dff41`,id:null,metadata:{},name:`hooksUsingRelay_ScopedImageReferenceQuery`,operationKind:`query`,text:`query hooksUsingRelay_ScopedImageReferenceQuery(
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
`}}})();l.hash=`64331ab01b07af6759f80b8c8fd0f0a4`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var u=e(t(),1),d=a(),f=(e,t={fetchPolicy:`store-and-network`})=>{let[r,i]=n(`first`),{keypair:a}=(0,d.useLazyLoadQuery)(o,{accessKey:e},{...t,fetchKey:r+t.fetchKey});return[a,{refresh:(0,u.useCallback)(()=>{i()},[i])}]},p=(e={fetchPolicy:`store-and-network`})=>{let[t,i]=n(`first`),a=r(),[o]=f(a==null?void 0:a._config.accessKey),{keypair_resource_policy:c}=(0,d.useLazyLoadQuery)(s,{name:(o==null?void 0:o.resource_policy)||``},{...e,fetchKey:t+e.fetchKey}),l=(0,u.useCallback)(()=>{i()},[i]);return[{keypairResourcePolicy:c||{},keypair:o||{},sessionLimitAndRemaining:{max:(c||{}).max_concurrent_sessions||2147483647,remaining:((c||{}).max_concurrent_sessions||2147483647)-((o||{}).concurrency_used||0)}},{refresh:l}]},m=(e,t={fetchPolicy:`store-or-network`})=>{var n;let{id:r}=i(),a=(0,d.useLazyLoadQuery)(l,{id:e??``,scope:{domain:[{value:r}],public:!0}},t);if(!e)return;let o=(n=a.scopedImagesV2)==null||(n=n.edges)==null||(n=n[0])==null||(n=n.node)==null?void 0:n.identity;return o!=null&&o.canonicalName?o.architecture?`${o.canonicalName}@${o.architecture}`:o.canonicalName:e};export{m as n,p as t};
