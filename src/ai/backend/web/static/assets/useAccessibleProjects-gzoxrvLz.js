import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{bt as t,ut as n,vt as r}from"./lodash-ClfL87UH.js";import{f as i}from"./DefaultProviders-BFjPhnQa.js";import{B as a,H as o}from"./helper-BWFKT_2Y.js";import{t as s}from"./react-relay-BfoHYpUf.js";var c=e(),l=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`domain_name`},{defaultValue:null,kind:`LocalArgument`,name:`type`}],t={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},n={alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null},r={alias:null,args:null,kind:`ScalarField`,name:`type`,storageKey:null},i={alias:null,args:[{kind:`Variable`,name:`domain_name`,variableName:`domain_name`},{kind:`Literal`,name:`is_active`,value:!0},{kind:`Variable`,name:`type`,variableName:`type`}],concreteType:`Group`,kind:`LinkedField`,name:`groups`,plural:!0,selections:[t,{alias:null,args:null,kind:`ScalarField`,name:`is_active`,storageKey:null},n,{alias:null,args:null,kind:`ScalarField`,name:`resource_policy`,storageKey:null},r],storageKey:null},a={alias:null,args:[{fields:[{fields:[{kind:`Variable`,name:`equals`,variableName:`domain_name`}],kind:`ObjectValue`,name:`domainName`},{kind:`Literal`,name:`isActive`,value:!0}],kind:`ObjectValue`,name:`filter`},{kind:`Literal`,name:`limit`,value:1e3}],concreteType:`ProjectV2Connection`,kind:`LinkedField`,name:`projects`,plural:!1,selections:[{alias:null,args:null,concreteType:`ProjectV2Edge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`ProjectV2`,kind:`LinkedField`,name:`node`,plural:!1,selections:[t,{alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},{alias:null,args:null,concreteType:`ProjectBasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[n,r],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useAccessibleProjectsQuery`,selections:[i,{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`myUserV2`,plural:!1,selections:[a],storageKey:null}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useAccessibleProjectsQuery`,selections:[i,{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`myUserV2`,plural:!1,selections:[a,t],storageKey:null}]},params:{cacheID:`706fd94a99fad6f0e28397fcab64dac4`,id:null,metadata:{},name:`useAccessibleProjectsQuery`,operationKind:`query`,text:`query useAccessibleProjectsQuery(
  $domain_name: String
  $type: [String]
) {
  groups(domain_name: $domain_name, is_active: true, type: $type) {
    id
    is_active
    name
    resource_policy
    type
  }
  myUserV2 {
    projects(filter: {isActive: true, domainName: {equals: $domain_name}}, limit: 1000) {
      edges {
        node {
          id
          entityId
          basicInfo {
            name
            type
          }
        }
      }
    }
    id
  }
}
`}}})();l.hash=`0a8f67856e31164ddeaf54cb475aa2c9`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var u=s(),d=e=>{"use memo";var s,d,f;let h=(0,c.c)(21),g=o(),_=a(),v=i(),y=(g==null||(s=g._config)==null?void 0:s.blockList)??null,b=(e==null?void 0:e.domain)??_,x;h[0]!==y||h[1]!==v?(x=(v===`admin`||v===`superadmin`)&&n(y,`model-store`)?[`GENERAL`]:[`GENERAL`,`MODEL_STORE`],h[0]=y,h[1]=v,h[2]=x):x=h[2];let S;h[3]!==b||h[4]!==x?(S={domain_name:b,type:x},h[3]=b,h[4]=x,h[5]=S):S=h[5];let C=(e==null?void 0:e.fetchPolicy)??`store-or-network`,w;h[6]===C?w=h[7]:(w={fetchPolicy:C},h[6]=C,h[7]=w);let{groups:T,myUserV2:E}=(0,u.useLazyLoadQuery)(l,S,w),D;if(h[8]!==(E==null||(d=E.projects)==null?void 0:d.edges)){var O,k;D=new Set(r(E==null||(O=E.projects)==null?void 0:O.edges,p)),h[8]=E==null||(k=E.projects)==null?void 0:k.edges,h[9]=D}else D=h[9];let A=D,j;h[10]!==T||h[11]!==A?(j=T==null?void 0:T.filter(e=>!!(e!=null&&e.id)&&A.has(e.id)),h[10]=T,h[11]=A,h[12]=j):j=h[12];let M=j,N;if(h[13]!==(E==null||(f=E.projects)==null?void 0:f.edges)){var P,F,I;N=(P=t(E==null||(F=E.projects)==null?void 0:F.edges,m))==null?void 0:P.node,h[13]=E==null||(I=E.projects)==null?void 0:I.edges,h[14]=N}else N=h[14];let L=N,R;h[15]===L?R=h[16]:(R=L?{id:L.entityId,name:L.basicInfo.name}:void 0,h[15]=L,h[16]=R);let z=R,B;return h[17]!==M||h[18]!==T||h[19]!==z?(B={groups:T,accessibleProjects:M,personalProject:z},h[17]=M,h[18]=T,h[19]=z,h[20]=B):B=h[20],B},f=e=>{"use memo";let{personalProject:t}=d();return!!e&&(t==null?void 0:t.id)===e};function p(e){return e.node.entityId}function m(e){var t;return(e==null||(t=e.node)==null||(t=t.basicInfo)==null?void 0:t.type)===`PERSONAL`}export{f as n,d as t};
