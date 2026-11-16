import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{P as t}from"./useWebUIConfig-DvlZdUc9.js";import{R as n,St as r,vt as i}from"./lodash-ClfL87UH.js";/* empty css            */import{N as a}from"./DefaultProviders-BFjPhnQa.js";import{J as o,M as s}from"./helper-BWFKT_2Y.js";import{a as c}from"./hooks-UUY7pxyu.js";import{t as l}from"./react-relay-BfoHYpUf.js";import{t as u}from"./utils-DCpr9tfC.js";var d=e(),f=(function(){var e=[{kind:`Literal`,name:`filter`,value:{status:{equals:`PENDING`}}},{kind:`Literal`,name:`limit`,value:100},{kind:`Literal`,name:`orderBy`,value:[{direction:`DESC`,field:`CREATED_AT`}]},{kind:`Literal`,name:`sides`,value:[`RECIPIENT`]}],t={alias:null,args:null,kind:`ScalarField`,name:`entityId`,storageKey:null},n={alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null},r={alias:null,args:null,kind:`ScalarField`,name:`permissions`,storageKey:null},i={alias:null,args:null,kind:`ScalarField`,name:`targetEntityType`,storageKey:null},a={alias:null,args:null,kind:`ScalarField`,name:`targetEntityId`,storageKey:null},o={alias:null,args:null,kind:`ScalarField`,name:`createdAt`,storageKey:null},s={alias:null,args:null,concreteType:`UserV2BasicInfo`,kind:`LinkedField`,name:`basicInfo`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`email`,storageKey:null}],storageKey:null},c={alias:null,args:null,kind:`ScalarField`,name:`__typename`,storageKey:null},l={kind:`InlineFragment`,selections:[{alias:null,args:null,concreteType:`VFolderMetadataInfo`,kind:`LinkedField`,name:`metadata`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`name`,storageKey:null}],storageKey:null}],type:`VFolder`,abstractKey:null},u={alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},d=[u];return{fragment:{argumentDefinitions:[],kind:`Fragment`,metadata:null,name:`useVFolderInvitationsQuery`,selections:[{alias:null,args:e,concreteType:`EntityShareConnection`,kind:`LinkedField`,name:`myEntityShares`,plural:!1,selections:[{alias:null,args:null,concreteType:`EntityShareEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`EntityShare`,kind:`LinkedField`,name:`node`,plural:!1,selections:[t,n,r,i,a,o,{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`sharer`,plural:!1,selections:[s],storageKey:null},{alias:null,args:null,concreteType:null,kind:`LinkedField`,name:`targetEntity`,plural:!1,selections:[c,l],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:`myEntityShares(filter:{"status":{"equals":"PENDING"}},limit:100,orderBy:[{"direction":"DESC","field":"CREATED_AT"}],sides:["RECIPIENT"])`}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[],kind:`Operation`,name:`useVFolderInvitationsQuery`,selections:[{alias:null,args:e,concreteType:`EntityShareConnection`,kind:`LinkedField`,name:`myEntityShares`,plural:!1,selections:[{alias:null,args:null,concreteType:`EntityShareEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`EntityShare`,kind:`LinkedField`,name:`node`,plural:!1,selections:[t,n,r,i,a,o,{alias:null,args:null,concreteType:`UserV2`,kind:`LinkedField`,name:`sharer`,plural:!1,selections:[s,u],storageKey:null},{alias:null,args:null,concreteType:null,kind:`LinkedField`,name:`targetEntity`,plural:!1,selections:[c,l,{kind:`InlineFragment`,selections:d,type:`Node`,abstractKey:`__isNode`},{kind:`InlineFragment`,selections:d,type:`ArtifactRegistry`,abstractKey:null}],storageKey:null},u],storageKey:null}],storageKey:null}],storageKey:`myEntityShares(filter:{"status":{"equals":"PENDING"}},limit:100,orderBy:[{"direction":"DESC","field":"CREATED_AT"}],sides:["RECIPIENT"])`}]},params:{cacheID:`59c30f2ab8d4319c9061ce34e21d7f28`,id:null,metadata:{},name:`useVFolderInvitationsQuery`,operationKind:`query`,text:`query useVFolderInvitationsQuery {
  myEntityShares(sides: [RECIPIENT], filter: {status: {equals: PENDING}}, orderBy: [{field: CREATED_AT, direction: "DESC"}], limit: 100) {
    edges {
      node {
        entityId
        status
        permissions
        targetEntityType
        targetEntityId
        createdAt
        sharer {
          basicInfo {
            email
          }
          id
        }
        targetEntity {
          __typename
          ... on VFolder {
            metadata {
              name
            }
          }
          ... on Node {
            __isNode: __typename
            id
          }
          ... on ArtifactRegistry {
            id
          }
        }
        id
      }
    }
  }
}
`}}})();f.hash=`cfc89c0bad7f355cdb962928b147a345`;var p=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`id`}],t=[{alias:null,args:[{kind:`Variable`,name:`id`,variableName:`id`}],concreteType:`EntitySharePayload`,kind:`LinkedField`,name:`acceptEntityShare`,plural:!1,selections:[{alias:null,args:null,concreteType:`EntityShare`,kind:`LinkedField`,name:`share`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useVFolderInvitationsAcceptMutation`,selections:t,type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useVFolderInvitationsAcceptMutation`,selections:t},params:{cacheID:`4a9451b7f9a52cf6f07818ba62216b2e`,id:null,metadata:{},name:`useVFolderInvitationsAcceptMutation`,operationKind:`mutation`,text:`mutation useVFolderInvitationsAcceptMutation(
  $id: UUID!
) {
  acceptEntityShare(id: $id) {
    share {
      id
      status
    }
  }
}
`}}})();p.hash=`19aeb7a0dc8935ae11ab278a3972c9e5`;var m=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`id`}],t=[{alias:null,args:[{kind:`Variable`,name:`id`,variableName:`id`}],concreteType:`EntitySharePayload`,kind:`LinkedField`,name:`rejectEntityShare`,plural:!1,selections:[{alias:null,args:null,concreteType:`EntityShare`,kind:`LinkedField`,name:`share`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`status`,storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useVFolderInvitationsRejectMutation`,selections:t,type:`Mutation`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useVFolderInvitationsRejectMutation`,selections:t},params:{cacheID:`702788d6c1431143aa5967a70949afa0`,id:null,metadata:{},name:`useVFolderInvitationsRejectMutation`,operationKind:`mutation`,text:`mutation useVFolderInvitationsRejectMutation(
  $id: UUID!
) {
  rejectEntityShare(id: $id) {
    share {
      id
      status
    }
  }
}
`}}})();m.hash=`62fe2c960f93031827ca05e2f8135f88`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var h=l(),g=`vfolder`,_=e=>n(i(r(e,e=>e.status===`PENDING`&&e.targetEntityType===g),e=>{var t,n;return{id:e.entityId,vfolderId:e.targetEntityId,vfolderName:((t=e.targetEntity)==null?void 0:t.__typename)===`VFolder`&&`metadata`in e.targetEntity?e.targetEntity.metadata.name:null,sharerEmail:((n=e.sharer)==null?void 0:n.basicInfo.email)??null,permissions:e.permissions,createdAt:e.createdAt}}),`createdAt`,`desc`),v=f,y=async()=>{var e;let t=await(0,h.fetchQuery)(a,v,{},{fetchPolicy:`network-only`}).toPromise();return _(i(t==null||(e=t.myEntityShares)==null?void 0:e.edges,e=>e.node))},b=u(async()=>(await s,y())),x=()=>{"use memo";let e=(0,d.c)(29),[n,r]=t(b),i;e[0]===r?i=e[1]:(i=async()=>{r(await y())},e[0]=r,e[1]=i);let a=i,s=c(p),l=c(m),u;e[2]===s?u=e[3]:(u=e=>s({id:e.inv_id}),e[2]=s,e[3]=u);let f;e[4]===a?f=e[5]:(f=()=>{a()},e[4]=a,e[5]=f);let h;e[6]!==u||e[7]!==f?(h={mutationFn:u,onSuccess:f},e[6]=u,e[7]=f,e[8]=h):h=e[8];let g=o(h),_;e[9]===l?_=e[10]:(_=e=>l({id:e.inv_id}),e[9]=l,e[10]=_);let v;e[11]===a?v=e[12]:(v=()=>{a()},e[11]=a,e[12]=v);let x;e[13]!==_||e[14]!==v?(x={mutationFn:_,onSuccess:v},e[13]=_,e[14]=v,e[15]=x):x=e[15];let S=o(x),C;e[16]===g?C=e[17]:(C=(e,t)=>g.mutateAsync({inv_id:e},{onSuccess:()=>{var n;t==null||(n=t.onSuccess)==null||n.call(t,e)},onError:e=>{var n;t==null||(n=t.onError)==null||n.call(t,e)}}),e[16]=g,e[17]=C);let w;e[18]===S?w=e[19]:(w=(e,t)=>S.mutateAsync({inv_id:e},{onSuccess:()=>{var n;t==null||(n=t.onSuccess)==null||n.call(t,e)},onError:e=>{var n;t==null||(n=t.onError)==null||n.call(t,e)}}),e[18]=S,e[19]=w);let T;e[20]!==g.isPending||e[21]!==S.isPending||e[22]!==C||e[23]!==w||e[24]!==a?(T={updateInvitations:a,acceptInvitation:C,isPendingAcceptInvitation:g.isPending,rejectInvitation:w,isPendingRejectInvitation:S.isPending},e[20]=g.isPending,e[21]=S.isPending,e[22]=C,e[23]=w,e[24]=a,e[25]=T):T=e[25];let E;return e[26]!==T||e[27]!==n?(E=[n,T],e[26]=T,e[27]=n,e[28]=E):E=e[28],E};export{x as t};
