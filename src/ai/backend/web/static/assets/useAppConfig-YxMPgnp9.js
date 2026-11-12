import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{Nt as t,O as n,Ut as r,a as i,m as a}from"./lodash-ClfL87UH.js";/* empty css            */import{B as o,z as s}from"./helper-BWFKT_2Y.js";import{a as c}from"./hooks-UUY7pxyu.js";import{t as l}from"./react-relay-BfoHYpUf.js";var u=e(),d=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`configNames`}],t=[{alias:null,args:[{kind:`Variable`,name:`configNames`,variableName:`configNames`}],concreteType:`AppConfig`,kind:`LinkedField`,name:`myAppConfigs`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`configName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`config`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useAppConfigMyQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useAppConfigMyQuery`,selections:t},params:{cacheID:`9e89356de6cfbbec3c5ab6a3abae5ccc`,id:null,metadata:{},name:`useAppConfigMyQuery`,operationKind:`query`,text:`query useAppConfigMyQuery(
  $configNames: [String!]!
) {
  myAppConfigs(configNames: $configNames) {
    configName
    config
  }
}
`}}})();d.hash=`202cdeea55d7128e47305776c0859d4f`;var f=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`configNames`}],t=[{alias:null,args:[{kind:`Variable`,name:`configNames`,variableName:`configNames`}],concreteType:`AppConfig`,kind:`LinkedField`,name:`publicAppConfigs`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`configName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`config`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useAppConfigPublicQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useAppConfigPublicQuery`,selections:t},params:{cacheID:`68c288e53c4c1040af4adcb18d478ea4`,id:null,metadata:{},name:`useAppConfigPublicQuery`,operationKind:`query`,text:`query useAppConfigPublicQuery(
  $configNames: [String!]!
) {
  publicAppConfigs(configNames: $configNames) {
    configName
    config
  }
}
`}}})();f.hash=`198a90073dc62b2acc37dc2bf78cb638`;var p=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`configNames`}],t=[{alias:null,args:[{kind:`Variable`,name:`configNames`,variableName:`configNames`},{kind:`Literal`,name:`scope`,value:{scopeType:`PUBLIC`}}],concreteType:`AppConfigFragment`,kind:`LinkedField`,name:`scopedAppConfigFragmentsByNames`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`configName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`config`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useAppConfigPublicRawQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useAppConfigPublicRawQuery`,selections:t},params:{cacheID:`bf1a302d87a854e1f7eb4fc16f29be48`,id:null,metadata:{},name:`useAppConfigPublicRawQuery`,operationKind:`query`,text:`query useAppConfigPublicRawQuery(
  $configNames: [String!]!
) {
  scopedAppConfigFragmentsByNames(scope: {scopeType: PUBLIC}, configNames: $configNames) {
    id
    configName
    config
  }
}
`}}})();p.hash=`621b4f7461517e46e40fb4b63d76ef39`;var m=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`configNames`},t={defaultValue:null,kind:`LocalArgument`,name:`scopeId`},n=[{alias:null,args:[{kind:`Variable`,name:`configNames`,variableName:`configNames`},{fields:[{kind:`Variable`,name:`scopeId`,variableName:`scopeId`},{kind:`Literal`,name:`scopeType`,value:`DOMAIN`}],kind:`ObjectValue`,name:`scope`}],concreteType:`AppConfigFragment`,kind:`LinkedField`,name:`scopedAppConfigFragmentsByNames`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`configName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`config`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,t],kind:`Fragment`,metadata:null,name:`useAppConfigDomainRawQuery`,selections:n,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[t,e],kind:`Operation`,name:`useAppConfigDomainRawQuery`,selections:n},params:{cacheID:`1d361fa75e2154bda74a382fd8621e51`,id:null,metadata:{},name:`useAppConfigDomainRawQuery`,operationKind:`query`,text:`query useAppConfigDomainRawQuery(
  $scopeId: UUID!
  $configNames: [String!]!
) {
  scopedAppConfigFragmentsByNames(scope: {scopeType: DOMAIN, scopeId: $scopeId}, configNames: $configNames) {
    id
    configName
    config
  }
}
`}}})();m.hash=`da4a8cf295f7377e3ce13a08a869b0f1`;var h=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`configNames`}],t=[{alias:null,args:[{kind:`Variable`,name:`configNames`,variableName:`configNames`}],concreteType:`AppConfigFragment`,kind:`LinkedField`,name:`myAppConfigFragmentsByNames`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`configName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`config`,storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useAppConfigUserRawQuery`,selections:t,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useAppConfigUserRawQuery`,selections:t},params:{cacheID:`e476c6218d5fa057aff9b9db4c9fe0cc`,id:null,metadata:{},name:`useAppConfigUserRawQuery`,operationKind:`query`,text:`query useAppConfigUserRawQuery(
  $configNames: [String!]!
) {
  myAppConfigFragmentsByNames(configNames: $configNames) {
    id
    configName
    config
  }
}
`}}})();h.hash=`7f9848765da70b4686294fe8adfa28d7`;var g=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`input`}],t=[{alias:null,args:[{kind:`Variable`,name:`input`,variableName:`input`}],concreteType:`AtomicBulkUpsertAppConfigFragmentsPayload`,kind:`LinkedField`,name:`scopedAtomicBulkUpsertAppConfigFragments`,plural:!1,selections:[{alias:null,args:null,concreteType:`AppConfigFragment`,kind:`LinkedField`,name:`items`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`configName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`config`,storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useAppConfigUpsertMutation`,selections:t,type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useAppConfigUpsertMutation`,selections:t},params:{cacheID:`3d2c57add9cce1ef8c7953aa562f838e`,id:null,metadata:{},name:`useAppConfigUpsertMutation`,operationKind:`mutation`,text:`mutation useAppConfigUpsertMutation(
  $input: ScopedUpsertAppConfigFragmentsInput!
) {
  scopedAtomicBulkUpsertAppConfigFragments(input: $input) {
    items {
      id
      configName
      config
    }
  }
}
`}}})();g.hash=`60cd6220b2cdfe588de70b238bb1d967`;var _=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`input`}],t=[{alias:null,args:[{kind:`Variable`,name:`input`,variableName:`input`}],concreteType:`AtomicBulkUpsertAppConfigFragmentsPayload`,kind:`LinkedField`,name:`myAtomicBulkUpsertAppConfigFragments`,plural:!1,selections:[{alias:null,args:null,concreteType:`AppConfigFragment`,kind:`LinkedField`,name:`items`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`configName`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`config`,storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useAppConfigMyUpsertMutation`,selections:t,type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useAppConfigMyUpsertMutation`,selections:t},params:{cacheID:`1b38df03b9587c117cbdfdc30df340dd`,id:null,metadata:{},name:`useAppConfigMyUpsertMutation`,operationKind:`mutation`,text:`mutation useAppConfigMyUpsertMutation(
  $input: MyUpsertAppConfigFragmentsInput!
) {
  myAtomicBulkUpsertAppConfigFragments(input: $input) {
    items {
      id
      configName
      config
    }
  }
}
`}}})();_.hash=`bb1b7330394f783ac0e8bcbf28f6d73d`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var v=l(),y=d,b=f,x=p,S=m,C=h,w=g,T=_,E=(e,a,o)=>{let s=t(e),c=typeof o==`function`?o(r(e,a)):o;return c===void 0?i(s,a):n(s,a,c),s},D=e=>{"use memo";let t=(0,u.c)(4),n;t[0]===Symbol.for(`react.memo_cache_sentinel`)?(n={configNames:[`userConfig`]},t[0]=n):n=t[0];let i=(0,v.useLazyLoadQuery)(y,n),a;if(t[1]!==(i==null?void 0:i.myAppConfigs)||t[2]!==e){var o;let n=i==null||(o=i.myAppConfigs)==null||(o=o.find(F))==null?void 0:o.config;a=e===void 0?n:r(n,e),t[1]=i==null?void 0:i.myAppConfigs,t[2]=e,t[3]=a}else a=t[3];return a},O=e=>{"use memo";let t=(0,u.c)(4),n;t[0]===Symbol.for(`react.memo_cache_sentinel`)?(n={configNames:[`domainConfig`]},t[0]=n):n=t[0];let i=(0,v.useLazyLoadQuery)(y,n),a;if(t[1]!==i.myAppConfigs||t[2]!==e){var o;let n=(o=i.myAppConfigs.find(I))==null?void 0:o.config;a=e===void 0?n:r(n,e),t[1]=i.myAppConfigs,t[2]=e,t[3]=a}else a=t[3];return a},k=e=>{"use memo";let t=(0,u.c)(5),n=o(),i;t[0]===Symbol.for(`react.memo_cache_sentinel`)?(i={configNames:[`publicConfigByDomain`]},t[0]=i):i=t[0];let a=(0,v.useLazyLoadQuery)(b,i),s;if(t[1]!==n||t[2]!==a.publicAppConfigs||t[3]!==e){var c;let i=(c=a.publicAppConfigs.find(L))==null?void 0:c.config,o=r(i,[n]);s=e===void 0?o:r(o,e),t[1]=n,t[2]=a.publicAppConfigs,t[3]=e,t[4]=s}else s=t[4];return s},A=(e,t)=>{"use memo";var n;let i=(0,u.c)(7),a=o(),s,c;i[0]===Symbol.for(`react.memo_cache_sentinel`)?(s={configNames:[`publicConfigByDomain`]},c={fetchPolicy:`network-only`},i[0]=s,i[1]=c):(s=i[0],c=i[1]);let l=(0,v.useLazyLoadQuery)(x,s,c),d=l==null||(n=l.scopedAppConfigFragmentsByNames)==null||(n=n[0])==null?void 0:n.config,f;if(i[2]!==a||i[3]!==d||i[4]!==t||i[5]!==e){let n=r(d,[t??a]);f=e===void 0?n:r(n,e),i[2]=a,i[3]=d,i[4]=t,i[5]=e,i[6]=f}else f=i[6];return f},j=()=>{"use memo";let e=(0,u.c)(4),t=(0,v.useRelayEnvironment)(),n=o(),r=c(w),i;return e[0]!==n||e[1]!==t||e[2]!==r?(i=async(e,i,o)=>{var s;let c=o??n,l=await(0,v.fetchQuery)(t,x,{configNames:[`publicConfigByDomain`]},{fetchPolicy:`network-only`}).toPromise(),u=(l==null||(s=l.scopedAppConfigFragmentsByNames)==null||(s=s[0])==null?void 0:s.config)??{};await r({input:{scope:{scopeType:`PUBLIC`},items:[{configName:`publicConfigByDomain`,config:E(u,[c,...a(e)],i)}]}})},e[0]=n,e[1]=t,e[2]=r,e[3]=i):i=e[3],i},M=()=>{"use memo";let e=(0,u.c)(4),t=(0,v.useRelayEnvironment)(),{id:n}=s(),i=c(w),o;return e[0]!==t||e[1]!==n||e[2]!==i?(o=async(e,o)=>{var s;let c=await(0,v.fetchQuery)(t,S,{scopeId:n,configNames:[`domainConfig`]},{fetchPolicy:`network-only`}).toPromise(),l=(c==null||(s=c.scopedAppConfigFragmentsByNames)==null||(s=s[0])==null?void 0:s.config)??{};await i({input:{scope:{scopeType:`DOMAIN`,scopeId:n},items:[{configName:`domainConfig`,config:E(l,a(e),typeof o==`function`?o(r(l,e)):o)}]}}),await(0,v.fetchQuery)(t,y,{configNames:[`domainConfig`]},{fetchPolicy:`network-only`}).toPromise()},e[0]=t,e[1]=n,e[2]=i,e[3]=o):o=e[3],o},N=()=>{"use memo";let e=(0,u.c)(2),t=(0,v.useRelayEnvironment)(),n;return e[0]===t?n=e[1]:(n=async()=>{await(0,v.fetchQuery)(t,y,{configNames:[`userConfig`]},{fetchPolicy:`network-only`}).toPromise()},e[0]=t,e[1]=n),n},P=()=>{"use memo";let e=(0,u.c)(3),t=(0,v.useRelayEnvironment)(),n=c(T),i;return e[0]!==t||e[1]!==n?(i=async(e,i)=>{var o;let s=await(0,v.fetchQuery)(t,C,{configNames:[`userConfig`]},{fetchPolicy:`network-only`}).toPromise(),c=(s==null||(o=s.myAppConfigFragmentsByNames)==null||(o=o[0])==null?void 0:o.config)??{};await n({input:{items:[{configName:`userConfig`,config:E(c,a(e),typeof i==`function`?i(r(c,e)):i)}]}})},e[0]=t,e[1]=n,e[2]=i):i=e[2],i};function F(e){return e.configName===`userConfig`}function I(e){return e.configName===`domainConfig`}function L(e){return e.configName===`publicConfigByDomain`}export{N as a,j as c,A as i,D as n,M as o,k as r,P as s,O as t};
