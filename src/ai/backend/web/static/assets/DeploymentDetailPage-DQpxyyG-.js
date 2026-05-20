import{c3 as xt,h as Je,ad as Rt,r as N,aE as pn,cY as bt,au as Cl,cZ as Mn,b8 as Al,i as je,c_ as Tt,a6 as Rl,c4 as Kt,ac as Dt,bi as yn,j as n,az as pl,ak as It,c$ as At,bA as Mt,N as $e,m as Ct,cl as jt,d0 as Lt,aj as Vt,u as Ze,t as yl,A as bl,v as Kl,K as Cn,cm as sn,T as Oe,bM as Wl,c7 as ml,aq as dl,B as ae,aD as Dl,b5 as Vl,b3 as Ye,bI as jl,a7 as vl,P as Ul,aN as Hl,F as ue,d1 as Pt,aZ as rn,a$ as on,b6 as Gl,b7 as un,aS as wl,d2 as jn,z as ql,c6 as xl,cR as Nt,y as Tl,aR as Ln,bp as ul,d3 as _t,an as Et,d4 as Ot,a4 as Xl,d5 as El,d6 as $t,w as Ol,cp as wt,cd as fn,b4 as kn,aJ as hn,d7 as qt,d8 as Qt,d9 as Bt,da as Yl,db as zt,Y as Wt,dc as Ut,a8 as Ht,bm as Sn,dd as Pl,bC as Nl,H as Gt,de as Xt,c1 as Vn,bf as Yt,a as Pn,aI as Jt,df as Zt,M as ea,a5 as la,dg as na,cn as Ml,cW as ta,bt as Ll,bu as dn,bs as aa,dh as cl,a_ as ia,f as _l,c8 as Nn,cT as _n,di as Ql,ca as Bl,dj as vn,cJ as zl,c5 as cn,bW as sa,ax as ln,dk as ra,p as En,Z as oa,dl as ua,ay as da,ai as Fn,dm as ca,dn as ma,G as ga,cX as pa,a1 as On,D as ya,cc as fa,a3 as ka,b$ as ha,aX as Sa,dp as va,bJ as Fa}from"./index-CC9H5FpY.js";import{t as $n,f as xa,D as mn,a as Ra,b as ba,c as Ta}from"./DeploymentTagChips-Cg3xRmto.js";import{R as Ka}from"./UndoOutlined-DJgDgnNU.js";import{B as xn}from"./BAIVFolderSelect-Dta5VYUH.js";import{P as Da}from"./PrometheusQueryTemplatePreview-CVPUmRmO.js";import{o as Ia,S as Aa}from"./SessionDetailDrawer-BVjO_cba.js";import{B as gn}from"./BAIGraphQLPropertyFilter-Ckmil7rC.js";import{B as Sl}from"./BAIId-BWHiWB9O.js";import{B as Ma}from"./BooleanTag-CpUC1Jz5.js";import"./FolderLink-C7chKJFz.js";import"./corner-down-left-BhZTgxok.js";import"./zip-TaKZGqdT.js";import"./unzip-Cji1UvDK.js";/**
 * @license lucide-react v0.552.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ca=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2",key:"usdka0"}]],Rn=xt("folder-open",Ca),wn=function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},a={defaultValue:null,kind:"LocalArgument",name:"offset"},i=[{alias:null,args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Literal",name:"orderBy",value:[{direction:"ASC",field:"NAME"}]}],concreteType:"RuntimeVariantConnection",kind:"LinkedField",name:"runtimeVariants",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[l,e,a],kind:"Fragment",metadata:null,name:"BAIRuntimeVariantSelectPaginatedQuery",selections:i,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[a,e,l],kind:"Operation",name:"BAIRuntimeVariantSelectPaginatedQuery",selections:i},params:{cacheID:"e8d20623434b823880b9543cf3297c3f",id:null,metadata:{},name:"BAIRuntimeVariantSelectPaginatedQuery",operationKind:"query",text:`query BAIRuntimeVariantSelectPaginatedQuery(
  $offset: Int!
  $limit: Int!
  $filter: RuntimeVariantFilter
) {
  runtimeVariants(offset: $offset, limit: $limit, filter: $filter, orderBy: [{field: NAME, direction: "ASC"}]) {
    count
    edges {
      node {
        id
        name
      }
    }
  }
}
`}}}();wn.hash="65da05baef2fee7bd3840fc61e39a8d8";const qn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"},{defaultValue:null,kind:"LocalArgument",name:"skip"}],e=[{condition:"skip",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}]}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"BAIRuntimeVariantSelectValueQuery",selections:e,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"BAIRuntimeVariantSelectValueQuery",selections:e},params:{cacheID:"f029b9c8b12e9bc799f1ff1caaebd031",id:null,metadata:{},name:"BAIRuntimeVariantSelectValueQuery",operationKind:"query",text:`query BAIRuntimeVariantSelectValueQuery(
  $id: UUID!
  $skip: Boolean!
) {
  runtimeVariant(id: $id) @skip(if: $skip) {
    id
    name
  }
}
`}}}();qn.hash="f7c1435633aeb06ecc9eafe324f06550";const ja=l=>{"use memo";var he;const e=Je.c(74);let a,i,t,r;e[0]!==l?({loading:a,onResolvedNamesChange:i,ref:t,...r}=l,e[0]=l,e[1]=a,e[2]=i,e[3]=t,e[4]=r):(a=e[1],i=e[2],t=e[3],r=e[4]);const{t:p}=Rt(),u=N.useRef(null),[o,s]=pn(r);let y;e[5]===Symbol.for("react.memo_cache_sentinel")?(y={valuePropName:"open",trigger:"onOpenChange",defaultValuePropName:"defaultOpen"},e[5]=y):y=e[5];const[c,k]=pn(r,y),V=N.useDeferredValue(c),[M,f]=N.useState(),g=bt(M),[K,j]=N.useOptimistic(M),[_,q]=N.useTransition(),[C,$]=Cl(),Q=N.useDeferredValue(C),D=N.useDeferredValue(o);let I;e[6]!==D?(I=D?Mn(Al(D)):"",e[6]=D,e[7]=I):I=e[7];const x=I;let S;e[8]===Symbol.for("react.memo_cache_sentinel")?(S=qn,e[8]=S):S=e[8];const R=!x;let b;e[9]!==x||e[10]!==R?(b={id:x,skip:R},e[9]=x,e[10]=R,e[11]=b):b=e[11];const d=x?"store-or-network":"store-only";let v;e[12]!==Q||e[13]!==d?(v={fetchPolicy:d,fetchKey:Q},e[12]=Q,e[13]=d,e[14]=v):v=e[14];const{runtimeVariant:h}=je.useLazyLoadQuery(S,b,v);let B;e[15]!==g?(B=g?{name:{iContains:g}}:null,e[15]=g,e[16]=B):B=e[16];const G=B;let z,W;e[17]===Symbol.for("react.memo_cache_sentinel")?(W=wn,z={limit:20},e[17]=z,e[18]=W):(z=e[17],W=e[18]);let H;e[19]!==G?(H={filter:G},e[19]=G,e[20]=H):H=e[20];const J=V?"network-only":"store-only";let se;e[21]!==Q||e[22]!==J?(se={fetchPolicy:J,fetchKey:Q},e[21]=Q,e[22]=J,e[23]=se):se=e[23];let T;e[24]===Symbol.for("react.memo_cache_sentinel")?(T={getTotal:La,getItem:Pa,getId:Na},e[24]=T):T=e[24];const{paginationData:F,result:A,loadNext:P,isLoadingNext:U}=Tt(W,z,H,se,T);let Y,ne;e[25]!==$?(Y=()=>({refetch:()=>{q(()=>{$()})}}),ne=[$,q],e[25]=$,e[26]=Y,e[27]=ne):(Y=e[26],ne=e[27]),N.useImperativeHandle(t,Y,ne);let Z;e[28]!==i||e[29]!==F||e[30]!==h?(Z=()=>{if(!i)return;const de={};if(h!=null&&h.id&&h.name){const ie=$e(h.id);ie&&(de[ie]=h.name)}for(const ie of F??[])if(ie!=null&&ie.id&&ie.name){const ge=$e(ie.id);ge&&(de[ge]=ie.name)}Ct(de)||i(de)},e[28]=i,e[29]=F,e[30]=h,e[31]=Z):Z=e[31];const te=N.useEffectEvent(Z);let re;e[32]!==te?(re=()=>{te()},e[32]=te,e[33]=re):re=e[33];let ee;e[34]!==F||e[35]!==h?(ee=[h,F],e[34]=F,e[35]=h,e[36]=ee):ee=e[36],N.useEffect(re,ee);let O;e[37]!==F?(O=Rl(F,_a),e[37]=F,e[38]=O):O=e[38];const Se=O,pe=h==null?void 0:h.name;let me;e[39]!==D||e[40]!==pe?(me=D?{label:pe??Al(D),value:Al(D)}:void 0,e[39]=D,e[40]=pe,e[41]=me):me=e[41];const ke=me,[ve,ye]=N.useState(ke);let Fe;e[42]!==p?(Fe=p("comp:BAIRuntimeVariantSelect.SelectRuntimeVariant"),e[42]=p,e[43]=Fe):Fe=e[43];const Re=a||o!==D||M!==g||_;let be;e[44]!==r||e[45]!==j?(be=async de=>{var ie;j(de),f(de),await((ie=r.searchAction)==null?void 0:ie.call(r,de))},e[44]=r,e[45]=j,e[46]=be):be=e[46];let Me;e[47]!==K||e[48]!==r.showSearch?(Me=r.showSearch===!1?!1:{searchValue:K,autoClearSearchValue:!0,...Kt(r.showSearch)?Dt(r.showSearch,["searchValue"]):{},filterOption:!1},e[47]=K,e[48]=r.showSearch,e[49]=Me):Me=e[49];const m=o!==D?ve:ke;let L;e[50]!==Se||e[51]!==s?(L=(de,ie)=>{var xe;if(yn(de)||jt(de)){ye(void 0),s(void 0,ie);return}const ge=Lt(de)[0],oe={label:Vt(ge.label)?ge.label:((xe=Se.find(Ke=>Ke.value===ge.value))==null?void 0:xe.label)??Al(ge.value),value:Al(ge.value)};ye(oe),s(oe.value,ie)},e[50]=Se,e[51]=s,e[52]=L):L=e[52];let w;e[53]!==P?(w=()=>{P()},e[53]=P,e[54]=w):w=e[54];let E;e[55]!==F?(E=yn(F)?n.jsx(pl.Input,{active:!0,size:"small",block:!0}):void 0,e[55]=F,e[56]=E):E=e[56];let X;e[57]!==U||e[58]!==A.runtimeVariants?(X=It((he=A.runtimeVariants)==null?void 0:he.count)&&A.runtimeVariants.count>0?n.jsx(At,{loading:U,total:A.runtimeVariants.count}):void 0,e[57]=U,e[58]=A.runtimeVariants,e[59]=X):X=e[59];let le;return e[60]!==Se||e[61]!==c||e[62]!==r||e[63]!==k||e[64]!==Fe||e[65]!==Re||e[66]!==be||e[67]!==Me||e[68]!==m||e[69]!==L||e[70]!==w||e[71]!==E||e[72]!==X?(le=n.jsx(Mt,{ref:u,placeholder:Fe,loading:Re,...r,searchAction:be,showSearch:Me,value:m,labelInValue:!0,onChange:L,options:Se,endReached:w,open:c,onOpenChange:k,notFoundContent:E,footer:X}),e[60]=Se,e[61]=c,e[62]=r,e[63]=k,e[64]=Fe,e[65]=Re,e[66]=be,e[67]=Me,e[68]=m,e[69]=L,e[70]=w,e[71]=E,e[72]=X,e[73]=le):le=e[73],le};function La(l){var e;return((e=l.runtimeVariants)==null?void 0:e.count)??void 0}function Va(l){return l==null?void 0:l.node}function Pa(l){var e,a;return(a=(e=l.runtimeVariants)==null?void 0:e.edges)==null?void 0:a.map(Va)}function Na(l){return l==null?void 0:l.id}function _a(l){return{label:l==null?void 0:l.name,value:l!=null&&l.id?$e(l.id):void 0}}const Qn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},p=[a],u={alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},y=[a,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[i,a],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[o,s,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[a,i],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfoGQL",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[o,s,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[a,i,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentDetailPageQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[i,t],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[r],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:p,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:p,storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[u],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentConfigurationSection_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentReplicasTab_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAccessTokensTab_deployment"},{args:null,kind:"FragmentSpread",name:"DeploymentAutoScalingTab_deployment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentDetailPageQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[i,t,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[i],storageKey:null},a],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[r,{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:y,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:y,storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[u,a],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"d3e7112ef9cb1308b807bdb05132fd54",id:null,metadata:{},name:"DeploymentDetailPageQuery",operationKind:"query",text:`query DeploymentDetailPageQuery(
  $deploymentId: ID!
) {
  deployment(id: $deploymentId) {
    id
    metadata {
      name
      status
    }
    networkAccess {
      openToPublic
    }
    currentRevision @since(version: "26.4.3") {
      id
    }
    deployingRevision @since(version: "26.4.3") {
      id
    }
    creator @since(version: "26.4.3") {
      basicInfo {
        email
      }
      id
    }
    ...DeploymentConfigurationSection_deployment
    ...DeploymentReplicasTab_deployment
    ...DeploymentAccessTokensTab_deployment
    ...DeploymentAutoScalingTab_deployment
  }
}

fragment DeploymentAccessTokensTab_deployment on ModelDeployment {
  id
}

fragment DeploymentAutoScalingTab_deployment on ModelDeployment {
  id
  metadata {
    status
  }
  creator @since(version: "26.4.3") {
    basicInfo {
      email
    }
    id
  }
}

fragment DeploymentConfigurationSection_deployment on ModelDeployment {
  id
  ...DeploymentSettingModal_deployment
  metadata {
    name
    projectId
    domainName
    status
    resourceGroupName
    projectV2 @since(version: "26.4.3") {
      basicInfo {
        name
      }
      id
    }
    ...DeploymentTagChips_metadata
  }
  networkAccess {
    openToPublic
    endpointUrl
  }
  replicaState {
    desiredReplicaCount
  }
  currentRevision @since(version: "26.4.3") {
    id
    revisionNumber
    ...DeploymentRevisionDetail_revision
  }
  deployingRevision @since(version: "26.4.3") {
    id
    revisionNumber
    ...DeploymentRevisionDetail_revision
  }
  ...DeploymentRevisionHistoryTab_deployment
}

fragment DeploymentReplicasTab_deployment on ModelDeployment {
  id
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots @since(version: "26.4.2") {
    slotName
    quantity
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    environ {
      entries {
        name
        value
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    vfolder {
      id
      name
    }
  }
  extraMounts {
    vfolderId
    mountDestination
    mountPerm
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  imageV2 @since(version: "26.4.3") {
    id
    identity {
      canonicalName
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        port
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
        }
      }
    }
  }
}

fragment DeploymentRevisionHistoryTab_deployment on ModelDeployment {
  id
}

fragment DeploymentSettingModal_deployment on ModelDeployment {
  id
  metadata {
    name
    tags
    resourceGroupName
  }
  networkAccess {
    openToPublic
  }
  replicaState {
    desiredReplicaCount
  }
}

fragment DeploymentTagChips_metadata on ModelDeploymentMetadata {
  tags
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
}
`}}}();Qn.hash="e560e46f065f52f67a0ba290d440fc26";const Bn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteAccessTokenPayload",kind:"LinkedField",name:"deleteAccessToken",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensTabDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensTabDeleteMutation",selections:e},params:{cacheID:"a511c067913c62224123dba5853f9c55",id:null,metadata:{},name:"DeploymentAccessTokensTabDeleteMutation",operationKind:"mutation",text:`mutation DeploymentAccessTokensTabDeleteMutation(
  $input: DeleteAccessTokenInput!
) {
  deleteAccessToken(input: $input) {
    id
  }
}
`}}}();Bn.hash="a82f98c3e592ea37497b90c70d69d6b4";const zn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={alias:null,args:[{kind:"Literal",name:"orderBy",value:[{direction:"DESC",field:"CREATED_AT"}]}],concreteType:"AccessTokenConnection",kind:"LinkedField",name:"accessTokens",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},{alias:null,args:null,concreteType:"AccessTokenEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AccessToken",kind:"LinkedField",name:"node",plural:!1,selections:[a,{alias:null,args:null,kind:"ScalarField",name:"token",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expiresAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:'accessTokens(orderBy:[{"direction":"DESC","field":"CREATED_AT"}])'};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensTabListQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensTabListQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[i,a],storageKey:null}]},params:{cacheID:"cb48b0e9b4930dfa44b7157fc8f289da",id:null,metadata:{},name:"DeploymentAccessTokensTabListQuery",operationKind:"query",text:`query DeploymentAccessTokensTabListQuery(
  $deploymentId: ID!
) {
  deployment(id: $deploymentId) {
    accessTokens(orderBy: [{field: CREATED_AT, direction: DESC}]) {
      count
      edges {
        node {
          id
          token
          createdAt
          expiresAt
        }
      }
    }
    id
  }
}
`}}}();zn.hash="4e84247d3aa97d220f9a949a56d396e1";const Wn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAccessTokenPayload",kind:"LinkedField",name:"createAccessToken",plural:!1,selections:[{alias:null,args:null,concreteType:"AccessToken",kind:"LinkedField",name:"accessToken",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"token",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expiresAt",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAccessTokensTabCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAccessTokensTabCreateMutation",selections:e},params:{cacheID:"ad0b1632c09adadb34c59dfacd183923",id:null,metadata:{},name:"DeploymentAccessTokensTabCreateMutation",operationKind:"mutation",text:`mutation DeploymentAccessTokensTabCreateMutation(
  $input: CreateAccessTokenInput!
) {
  createAccessToken(input: $input) {
    accessToken {
      id
      token
      createdAt
      expiresAt
    }
  }
}
`}}}();Wn.hash="df1b417c9205070e2bf82168815c312e";const Un={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAccessTokensTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"ModelDeployment",abstractKey:null};Un.hash="3bd042288d60da5fa0247bf2a96e06dd";const Ea=l=>{"use memo";const e=Je.c(71),{deploymentFrgmt:a,deploymentId:i,isOwnedByCurrentUser:t,isDeploymentDestroying:r}=l,p=t===void 0?!0:t,u=r===void 0?!1:r,{t:o}=Ze(),{token:s}=yl.useToken(),{message:y}=bl.useApp(),{logger:c}=Kl(),[k,V]=N.useTransition(),[M,f]=N.useState(0),[g,K]=N.useState(!1),[j,_]=N.useState(null);let q;e[0]===Symbol.for("react.memo_cache_sentinel")?(q=Un,e[0]=q):q=e[0];const C=je.useFragment(q,a);let $;e[1]===Symbol.for("react.memo_cache_sentinel")?($=Wn,e[1]=$):$=e[1];const Q=Cn($);let D;e[2]===Symbol.for("react.memo_cache_sentinel")?(D=()=>{V(()=>{f(wa)})},e[2]=D):D=e[2];const I=D,x=u||!p;let S;e[3]!==o?(S=o("deployment.tab.AccessTokens"),e[3]=o,e[4]=S):S=e[4];let R;e[5]!==o?(R=o("deployment.tab.description.AccessTokens"),e[5]=o,e[6]=R):R=e[6];let b;e[7]!==s.colorTextDescription?(b=n.jsx(sn,{style:{color:s.colorTextDescription}}),e[7]=s.colorTextDescription,e[8]=b):b=e[8];let d;e[9]!==R||e[10]!==b?(d=n.jsx(dl,{title:R,children:b}),e[9]=R,e[10]=b,e[11]=d):d=e[11];let v;e[12]!==S||e[13]!==d?(v=n.jsxs(ae,{gap:"xs",align:"center",children:[S,d]}),e[12]=S,e[13]=d,e[14]=v):v=e[14];let h;e[15]!==k?(h=n.jsx(Dl,{loading:k,value:"",onChange:I}),e[15]=k,e[16]=h):h=e[16];let B;e[17]===Symbol.for("react.memo_cache_sentinel")?(B=n.jsx(Vl,{}),e[17]=B):B=e[17];let G;e[18]===Symbol.for("react.memo_cache_sentinel")?(G=()=>K(!0),e[18]=G):G=e[18];let z;e[19]!==o?(z=o("deployment.accessToken.Create"),e[19]=o,e[20]=z):z=e[20];let W;e[21]!==x||e[22]!==z?(W=n.jsx(Ye,{type:"primary",icon:B,disabled:x,onClick:G,children:z}),e[21]=x,e[22]=z,e[23]=W):W=e[23];let H;e[24]!==h||e[25]!==W?(H=n.jsxs(ae,{gap:"xs",align:"center",children:[h,W]}),e[24]=h,e[25]=W,e[26]=H):H=e[26];let J;e[27]===Symbol.for("react.memo_cache_sentinel")?(J={body:{paddingTop:0}},e[27]=J):J=e[27];let se;e[28]===Symbol.for("react.memo_cache_sentinel")?(se=n.jsx(pl,{active:!0}),e[28]=se):se=e[28];let T;e[29]!==i||e[30]!==M||e[31]!==x||e[32]!==k?(T=n.jsx(N.Suspense,{fallback:se,children:n.jsx(Oa,{deploymentId:i,fetchKey:M,isPendingRefetch:k,isDeleteDisabled:x,onAfterDelete:I})}),e[29]=i,e[30]=M,e[31]=x,e[32]=k,e[33]=T):T=e[33];let F;e[34]!==v||e[35]!==H||e[36]!==T?(F=n.jsx(jl,{title:v,extra:H,styles:J,children:T}),e[34]=v,e[35]=H,e[36]=T,e[37]=F):F=e[37];let A;e[38]!==Q||e[39]!==C||e[40]!==c||e[41]!==y||e[42]!==o?(A=me=>{K(!1),me&&Q({input:{modelDeploymentId:$e(C.id),expiresAt:me.expiresAt??new Date("2099-12-31").toISOString()}}).then(ke=>{var ye;const ve=(ye=ke.createAccessToken)==null?void 0:ye.accessToken;ve&&_({token:ve.token,expiresAt:ve.expiresAt??null}),y.success({key:"access-token-created",content:o("deployment.accessToken.Created")}),I()}).catch(ke=>{const ve=Array.isArray(ke)?ke:[ke];for(const ye of ve)y.error((ye==null?void 0:ye.message)||o("dialog.ErrorOccurred"));c.error(ke)})},e[38]=Q,e[39]=C,e[40]=c,e[41]=y,e[42]=o,e[43]=A):A=e[43];let P;e[44]!==g||e[45]!==A?(P=n.jsx(vl,{children:n.jsx($a,{open:g,confirmLoading:!1,onRequestClose:A})}),e[44]=g,e[45]=A,e[46]=P):P=e[46];const U=j!==null;let Y;e[47]!==o?(Y=o("deployment.accessToken.Token"),e[47]=o,e[48]=Y):Y=e[48];let ne;e[49]===Symbol.for("react.memo_cache_sentinel")?(ne=()=>_(null),e[49]=ne):ne=e[49];let Z;e[50]!==o?(Z=o("deployment.accessToken.Created"),e[50]=o,e[51]=Z):Z=e[51];let te;e[52]!==Z?(te=n.jsx(Oe.Text,{children:Z}),e[52]=Z,e[53]=te):te=e[53];let re;e[54]!==j?(re=j?n.jsx(Wl,{copyable:{text:j.token},ellipsis:!0,code:!0,children:j.token}):null,e[54]=j,e[55]=re):re=e[55];let ee;e[56]!==j||e[57]!==o?(ee=j!=null&&j.expiresAt?n.jsx(Oe.Text,{type:"secondary",children:`${o("deployment.accessToken.Expiration")}: ${ml(j.expiresAt).format("ll LT")}`}):n.jsx(Oe.Text,{type:"secondary",children:o("deployment.accessToken.NoExpiration")}),e[56]=j,e[57]=o,e[58]=ee):ee=e[58];let O;e[59]!==te||e[60]!==re||e[61]!==ee?(O=n.jsxs(ae,{direction:"column",align:"stretch",gap:"sm",children:[te,re,ee]}),e[59]=te,e[60]=re,e[61]=ee,e[62]=O):O=e[62];let Se;e[63]!==U||e[64]!==Y||e[65]!==O?(Se=n.jsx(vl,{children:n.jsx(Ul,{open:U,destroyOnHidden:!0,title:Y,onCancel:ne,footer:null,width:520,children:O})}),e[63]=U,e[64]=Y,e[65]=O,e[66]=Se):Se=e[66];let pe;return e[67]!==F||e[68]!==P||e[69]!==Se?(pe=n.jsxs(n.Fragment,{children:[F,P,Se]}),e[67]=F,e[68]=P,e[69]=Se,e[70]=pe):pe=e[70],pe},Oa=l=>{"use memo";var Y,ne,Z,te;const e=Je.c(70),{deploymentId:a,fetchKey:i,isPendingRefetch:t,isDeleteDisabled:r,onAfterDelete:p}=l,{t:u}=Ze(),{message:o}=bl.useApp(),{logger:s}=Kl(),[y,c]=N.useState(null);let k;e[0]===Symbol.for("react.memo_cache_sentinel")?(k=zn,e[0]=k):k=e[0];let V;e[1]!==a?(V={deploymentId:a},e[1]=a,e[2]=V):V=e[2];let M;e[3]!==i?(M={fetchKey:i,fetchPolicy:"network-only"},e[3]=i,e[4]=M):M=e[4];const{deployment:f}=je.useLazyLoadQuery(k,V,M);let g;e[5]!==((Y=f==null?void 0:f.accessTokens)==null?void 0:Y.edges)?(g=Hl((Z=(ne=f==null?void 0:f.accessTokens)==null?void 0:ne.edges)==null?void 0:Z.map(qa)),e[5]=(te=f==null?void 0:f.accessTokens)==null?void 0:te.edges,e[6]=g):g=e[6];const K=g;let j;e[7]===Symbol.for("react.memo_cache_sentinel")?(j=Bn,e[7]=j):j=e[7];const[_,q]=je.useMutation(j);let C;e[8]===Symbol.for("react.memo_cache_sentinel")?(C={x:"max-content"},e[8]=C):C=e[8];const $=t||q;let Q;e[9]!==u?(Q=u("deployment.accessToken.Token"),e[9]=u,e[10]=Q):Q=e[10];let D;e[11]!==r||e[12]!==u?(D=(re,ee)=>ee?n.jsx(rn,{title:n.jsx(Wl,{copyable:{text:ee.token},ellipsis:!0,style:{maxWidth:200},children:ee.token}),showActions:"always",actions:[{key:"delete",title:u("deployment.accessToken.Delete"),icon:n.jsx(on,{}),type:"danger",disabled:r,onClick:()=>c({id:ee.id,token:ee.token??""})}]}):"-",e[11]=r,e[12]=u,e[13]=D):D=e[13];let I;e[14]!==Q||e[15]!==D?(I={key:"token",title:Q,dataIndex:"token",render:D},e[14]=Q,e[15]=D,e[16]=I):I=e[16];let x;e[17]!==u?(x=u("deployment.CreatedAt"),e[17]=u,e[18]=x):x=e[18];let S;e[19]!==x?(S={key:"createdAt",title:x,dataIndex:"createdAt",render:Qa},e[19]=x,e[20]=S):S=e[20];let R;e[21]!==u?(R=u("deployment.accessToken.Expiration"),e[21]=u,e[22]=R):R=e[22];let b;e[23]!==u?(b=(re,ee)=>ee!=null&&ee.expiresAt?ml(ee.expiresAt).format("ll LT"):u("deployment.accessToken.NoExpiration"),e[23]=u,e[24]=b):b=e[24];let d;e[25]!==R||e[26]!==b?(d={key:"expiresAt",title:R,dataIndex:"expiresAt",render:b},e[25]=R,e[26]=b,e[27]=d):d=e[27];let v;e[28]!==I||e[29]!==S||e[30]!==d?(v=[I,S,d],e[28]=I,e[29]=S,e[30]=d,e[31]=v):v=e[31];let h;e[32]!==K||e[33]!==v||e[34]!==$?(h=n.jsx(Gl,{scroll:C,rowKey:"id",loading:$,dataSource:K,pagination:!1,resizable:!0,columns:v}),e[32]=K,e[33]=v,e[34]=$,e[35]=h):h=e[35];const B=!!y;let G;e[36]!==u?(G=u("deployment.accessToken.Delete"),e[36]=u,e[37]=G):G=e[37];let z;e[38]!==u?(z=u("deployment.AccessToken"),e[38]=u,e[39]=z):z=e[39];let W;e[40]!==y?(W=y?[{key:y.id,label:y.id}]:[],e[40]=y,e[41]=W):W=e[41];let H;e[42]!==u?(H=u("data.folders.DeleteForeverConfirmText"),e[42]=u,e[43]=H):H=e[43];let J;e[44]!==u?(J=u("data.folders.DeleteForeverConfirmText"),e[44]=u,e[45]=J):J=e[45];let se;e[46]!==J?(se={placeholder:J},e[46]=J,e[47]=se):se=e[47];let T;e[48]!==q?(T={loading:q},e[48]=q,e[49]=T):T=e[49];let F;e[50]!==_||e[51]!==y||e[52]!==s||e[53]!==o||e[54]!==p||e[55]!==u?(F=()=>{y&&_({variables:{input:{id:$e(y.id)??y.id}},onCompleted:(re,ee)=>{var O;if(ee&&ee.length>0){s.error(ee[0]),o.error(((O=ee[0])==null?void 0:O.message)??u("dialog.ErrorOccurred"));return}o.success(u("deployment.accessToken.Deleted")),c(null),p()},onError:re=>{s.error(re),o.error(re.message??u("dialog.ErrorOccurred"))}})},e[50]=_,e[51]=y,e[52]=s,e[53]=o,e[54]=p,e[55]=u,e[56]=F):F=e[56];let A;e[57]===Symbol.for("react.memo_cache_sentinel")?(A=()=>c(null),e[57]=A):A=e[57];let P;e[58]!==B||e[59]!==G||e[60]!==z||e[61]!==W||e[62]!==H||e[63]!==se||e[64]!==T||e[65]!==F?(P=n.jsx(un,{open:B,title:G,target:z,items:W,confirmText:H,requireConfirmInput:!0,inputProps:se,okButtonProps:T,onOk:F,onCancel:A}),e[58]=B,e[59]=G,e[60]=z,e[61]=W,e[62]=H,e[63]=se,e[64]=T,e[65]=F,e[66]=P):P=e[66];let U;return e[67]!==h||e[68]!==P?(U=n.jsxs(n.Fragment,{children:[h,P]}),e[67]=h,e[68]=P,e[69]=U):U=e[69],U},$a=l=>{"use memo";const e=Je.c(64),{open:a,confirmLoading:i,onRequestClose:t}=l,{t:r}=Ze(),[p]=ue.useForm(),u=ue.useWatch("expiryOption",p)??7;let o;e[0]!==p||e[1]!==t?(o=()=>{p.validateFields().then(W=>{let H;W.expiryOption==="none"?H=null:W.expiryOption==="custom"?H=W.datetime.toISOString():H=ml().add(W.expiryOption,"day").toISOString(),t({expiresAt:H})}).catch(Ba)},e[0]=p,e[1]=t,e[2]=o):o=e[2];const s=o;let y;e[3]!==r?(y=r("general.Days",{num:7,defaultValue:"7 days"}),e[3]=r,e[4]=y):y=e[4];let c;e[5]!==y?(c={value:7,label:y},e[5]=y,e[6]=c):c=e[6];let k;e[7]!==r?(k=r("general.Days",{num:30,defaultValue:"30 days"}),e[7]=r,e[8]=k):k=e[8];let V;e[9]!==k?(V={value:30,label:k},e[9]=k,e[10]=V):V=e[10];let M;e[11]!==r?(M=r("general.Days",{num:90,defaultValue:"90 days"}),e[11]=r,e[12]=M):M=e[12];let f;e[13]!==M?(f={value:90,label:M},e[13]=M,e[14]=f):f=e[14];let g;e[15]!==r?(g=r("deployment.accessToken.CustomExpiration"),e[15]=r,e[16]=g):g=e[16];let K;e[17]!==g?(K={value:"custom",label:g},e[17]=g,e[18]=K):K=e[18];let j;e[19]!==r?(j=r("deployment.accessToken.NoExpiration"),e[19]=r,e[20]=j):j=e[20];let _;e[21]!==j?(_={value:"none",label:j},e[21]=j,e[22]=_):_=e[22];let q;e[23]!==_||e[24]!==c||e[25]!==V||e[26]!==f||e[27]!==K?(q=[c,V,f,K,_],e[23]=_,e[24]=c,e[25]=V,e[26]=f,e[27]=K,e[28]=q):q=e[28];const C=q;let $;e[29]!==r?($=r("deployment.accessToken.Create"),e[29]=r,e[30]=$):$=e[30];let Q;e[31]!==r?(Q=r("deployment.accessToken.Create"),e[31]=r,e[32]=Q):Q=e[32];let D;e[33]!==t?(D=()=>t(),e[33]=t,e[34]=D):D=e[34];let I,x;e[35]===Symbol.for("react.memo_cache_sentinel")?(I={expiryOption:7,datetime:ml().add(7,"day")},x=["onChange","onBlur"],e[35]=I,e[36]=x):(I=e[35],x=e[36]);let S;e[37]!==r?(S=r("deployment.accessToken.Expiration"),e[37]=r,e[38]=S):S=e[38];let R;e[39]===Symbol.for("react.memo_cache_sentinel")?(R=[{required:!0}],e[39]=R):R=e[39];let b;e[40]===Symbol.for("react.memo_cache_sentinel")?(b={width:200},e[40]=b):b=e[40];let d;e[41]!==p?(d=W=>{typeof W=="number"&&p.setFieldValue("datetime",ml().add(W,"day"))},e[41]=p,e[42]=d):d=e[42];let v;e[43]!==C||e[44]!==d?(v=n.jsx(wl,{style:b,options:C,onChange:d}),e[43]=C,e[44]=d,e[45]=v):v=e[45];let h;e[46]!==S||e[47]!==v?(h=n.jsx(ue.Item,{name:"expiryOption",label:S,rules:R,children:v}),e[46]=S,e[47]=v,e[48]=h):h=e[48];let B;e[49]!==u||e[50]!==r?(B=u==="custom"&&n.jsx(ue.Item,{name:"datetime",label:r("deployment.accessToken.CustomExpiration"),rules:[{type:"object",required:!0},()=>({validator(W,H){return H&&ml(H).isAfter(ml())?Promise.resolve():Promise.reject(new Error(r("dialog.ErrorOccurred")))}})],children:n.jsx(Pt,{showTime:!0,format:"YYYY-MM-DD HH:mm:ss",style:{width:"100%"}})}),e[49]=u,e[50]=r,e[51]=B):B=e[51];let G;e[52]!==p||e[53]!==h||e[54]!==B?(G=n.jsxs(ue,{form:p,layout:"vertical",initialValues:I,validateTrigger:x,children:[h,B]}),e[52]=p,e[53]=h,e[54]=B,e[55]=G):G=e[55];let z;return e[56]!==i||e[57]!==s||e[58]!==a||e[59]!==$||e[60]!==Q||e[61]!==D||e[62]!==G?(z=n.jsx(Ul,{open:a,destroyOnHidden:!0,centered:!0,width:420,title:$,okText:Q,confirmLoading:i,onOk:s,onCancel:D,children:G}),e[56]=i,e[57]=s,e[58]=a,e[59]=$,e[60]=Q,e[61]=D,e[62]=G,e[63]=z):z=e[63],z};function wa(l){return l+1}function qa(l){return l==null?void 0:l.node}function Qa(l,e){return e!=null&&e.createdAt?ml(e.createdAt).format("ll LT"):"-"}function Ba(){}const Hn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],a={alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[a],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalImageNameQuery",selections:[{alias:null,args:e,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[a,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"c7f86a18b204736e35e7935bb3913511",id:null,metadata:{},name:"DeploymentAddRevisionModalImageNameQuery",operationKind:"query",text:`query DeploymentAddRevisionModalImageNameQuery(
  $id: ID!
) {
  imageV2(id: $id) {
    identity {
      canonicalName
    }
    id
  }
}
`}}}();Hn.hash="e0f63d644538b757a6d30c78d1771156";const Gn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"},t={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},p=[a,i],u={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},s={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},y={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},k={alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[c,a],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},V={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},M={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},f={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[V,M,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[a,c],storageKey:null}],storageKey:null},g={alias:null,args:null,concreteType:"ExtraVFolderMountInfoGQL",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[V,M,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[a,c,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null},K={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null},j={alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},_=[a,u,o,s,y,k,f,g,K,j];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[a,i,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,t,r,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:p,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:p,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalAddMutation",selections:[{alias:null,args:e,concreteType:"AddRevisionPayload",kind:"LinkedField",name:"addModelRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[a,u,o,s,y,k,f,g,K,j,{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,t,r,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:_,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:_,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"506ca99250c89a17f4b53ad4f95bca60",id:null,metadata:{},name:"DeploymentAddRevisionModalAddMutation",operationKind:"mutation",text:`mutation DeploymentAddRevisionModalAddMutation(
  $input: AddRevisionInput!
) {
  addModelRevision(input: $input) {
    revision {
      id
      ...DeploymentRevisionDetail_revision
      deployment @since(version: "26.4.4") {
        id
        currentRevisionId
        deployingRevisionId
        currentRevision @since(version: "26.4.3") {
          id
          ...DeploymentRevisionDetail_revision
        }
        deployingRevision @since(version: "26.4.3") {
          id
          ...DeploymentRevisionDetail_revision
        }
      }
    }
  }
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots @since(version: "26.4.2") {
    slotName
    quantity
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    environ {
      entries {
        name
        value
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    vfolder {
      id
      name
    }
  }
  extraMounts {
    vfolderId
    mountDestination
    mountPerm
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  imageV2 @since(version: "26.4.3") {
    id
    identity {
      canonicalName
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        port
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
        }
      }
    }
  }
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
}
`}}}();Gn.hash="889773e313c63748043b8294cd2bb0b0";const Xn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},a=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},e],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:a,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalSelectedPresetQuery",selections:a},params:{cacheID:"6728695a02d457f55b4cd4d3323823d8",id:null,metadata:{},name:"DeploymentAddRevisionModalSelectedPresetQuery",operationKind:"query",text:`query DeploymentAddRevisionModalSelectedPresetQuery(
  $id: UUID!
) {
  deploymentRevisionPreset(id: $id) {
    id
    runtimeVariantId
    cluster {
      clusterMode
      clusterSize
    }
    execution {
      imageId
      environ {
        key
        value
      }
    }
    resource {
      resourceOpts {
        name
        value
      }
    }
    resourceSlots {
      slotName
      quantity
    }
  }
}
`}}}();Xn.hash="e9d60ac2d9540dae9c821fe3abd4b65e";const Yn=function(){var l=[{alias:null,args:[{kind:"Literal",name:"first",value:1},{kind:"Literal",name:"orderBy",value:[{direction:"ASC",field:"RANK"}]}],concreteType:"DeploymentRevisionPresetConnection",kind:"LinkedField",name:"deploymentRevisionPresets",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null}],storageKey:'deploymentRevisionPresets(first:1,orderBy:[{"direction":"ASC","field":"RANK"}])'}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetCountQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"DeploymentAddRevisionModalPresetCountQuery",selections:l},params:{cacheID:"edaa5efa78debd74168a24185822d633",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetCountQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetCountQuery {
  deploymentRevisionPresets(orderBy: [{field: RANK, direction: "ASC"}], first: 1) {
    count
  }
}
`}}}();Yn.hash="4461df1967b1117642d3190b36d5cb33";const Jn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"deploymentId"}],e=[{kind:"Variable",name:"id",variableName:"deploymentId"}],a={alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null}],storageKey:null},i={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},r=[t,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],p={alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:r,storageKey:null}],storageKey:null}],storageKey:null},u={alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},y={alias:null,args:null,concreteType:"ExtraVFolderMountInfoGQL",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[o,s],storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},k={alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:r,storageKey:null}],storageKey:null},V={alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[o,s,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},M={alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},g={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[f,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,p,u,y,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[c,{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[t],storageKey:null},k],storageKey:null},V,M,g],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalQuery",selections:[{alias:null,args:e,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,p,u,y,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[c,{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[t,f],storageKey:null},k],storageKey:null},V,M,g,f],storageKey:null},f],storageKey:null}]},params:{cacheID:"41e3a773e5a73cca06b5dfb852a433a6",id:null,metadata:{},name:"DeploymentAddRevisionModalQuery",operationKind:"query",text:`query DeploymentAddRevisionModalQuery(
  $deploymentId: ID!
) {
  deployment(id: $deploymentId) {
    metadata {
      resourceGroupName
    }
    currentRevision {
      clusterConfig {
        mode
        size
      }
      resourceConfig {
        resourceOpts {
          entries {
            name
            value
          }
        }
      }
      resourceSlots {
        slotName
        quantity
      }
      extraMounts {
        vfolderId
        mountDestination
      }
      modelRuntimeConfig {
        runtimeVariantId
        runtimeVariant {
          name
          id
        }
        environ {
          entries {
            name
            value
          }
        }
      }
      modelMountConfig {
        vfolderId
        mountDestination
        definitionPath
      }
      modelDefinition {
        models {
          name
          modelPath
          service {
            startCommand
            port
            healthCheck {
              path
              maxRetries
              initialDelay
              interval
              maxWaitTime
            }
          }
        }
      }
      imageV2 {
        id
        identity {
          canonicalName
        }
      }
      id
    }
    id
  }
}
`}}}();Jn.hash="3cbc34145af86f08792b27b9e14fd580";const Zn=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"id"}],e=[{kind:"Variable",name:"id",variableName:"id"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"DeploymentPresetDetailModalFragment"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentAddRevisionModalPresetDetailQuery",selections:[{alias:null,args:e,concreteType:"DeploymentRevisionPreset",kind:"LinkedField",name:"deploymentRevisionPreset",plural:!1,selections:[a,i,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"runtimeVariantId",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[a,i],storageKey:null},{alias:null,args:null,concreteType:"PresetClusterSpec",kind:"LinkedField",name:"cluster",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetExecutionSpec",kind:"LinkedField",name:"execution",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"imageId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startupCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"bootstrapScript",storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetEnvironEntry",kind:"LinkedField",name:"environ",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetResourceAllocation",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"resourceOpts",plural:!0,selections:[i,t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"PresetDeploymentDefaults",kind:"LinkedField",name:"deploymentDefaults",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"replicaCount",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"revisionHistoryLimit",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"deploymentStrategy",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentRevisionPresetValueEntry",kind:"LinkedField",name:"presetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},t],storageKey:null}],storageKey:null}]},params:{cacheID:"218b82beeca87da0b64539597ed3fe1b",id:null,metadata:{},name:"DeploymentAddRevisionModalPresetDetailQuery",operationKind:"query",text:`query DeploymentAddRevisionModalPresetDetailQuery(
  $id: UUID!
) {
  deploymentRevisionPreset(id: $id) {
    ...DeploymentPresetDetailModalFragment
    id
  }
}

fragment DeploymentPresetDetailModalFragment on DeploymentRevisionPreset {
  id
  name
  description
  runtimeVariantId
  runtimeVariant {
    id
    name
  }
  cluster {
    clusterMode
    clusterSize
  }
  execution {
    imageId
    startupCommand
    bootstrapScript
    environ {
      key
      value
    }
  }
  resource {
    resourceOpts {
      name
      value
    }
  }
  resourceSlots {
    slotName
    quantity
  }
  deploymentDefaults {
    openToPublic
    replicaCount
    revisionHistoryLimit
    deploymentStrategy
  }
  presetValues {
    presetId
    value
  }
}
`}}}();Zn.hash="8f60ae6bcf0fa60919e80838391f66f9";/**
 @license
 Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
 */function et(l){const e=$n(l.trim()),a={},i=[];let t=0;for(;t<e.length;){const r=e[t];if(r.startsWith("--")&&r.includes("=")){const p=r.indexOf("="),u=r.slice(0,p),o=r.slice(p+1);a[u]=o,t++;continue}if(r.startsWith("--no-")){const p="--"+r.slice(5);a[p]="false",t++;continue}if(r.startsWith("--")){const p=t+1<e.length?e[t+1]:void 0;p!==void 0&&!p.startsWith("-")?(a[r]=p,t+=2):(a[r]="true",t++);continue}i.push(r),t++}return{knownArgs:a,unknownTokens:i}}function lt(l,e=[]){const a=[];for(const[i,t]of Object.entries(l))if(t==="true")a.push(i);else{if(t==="false")continue;t.includes(" ")||t.includes("	")?a.push(`${i} "${t}"`):a.push(`${i} ${t}`)}return e.length>0&&a.push(e.join(" ")),a.join(" ")}function za(l,e,a={}){const i=et(e),t={...l,...i.knownArgs},r={};for(const[p,u]of Object.entries(t))a[p]!==void 0&&a[p]===u||(r[p]=u);return lt(r,i.unknownTokens)}function nt(l,e){const{knownArgs:a,unknownTokens:i}=et(l),t={},r={};for(const[u,o]of Object.entries(a))e.has(u)?t[u]=o:r[u]=o;const p=lt(r,i);return{mappedArgs:t,unmappedText:p}}const tt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"filter"},{defaultValue:null,kind:"LocalArgument",name:"orderBy"}],e=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Literal",name:"first",value:100},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],a={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"rank",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"category",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},u={alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetTarget",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"valueType",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"defaultValue",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"min",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"max",storageKey:null},y={alias:null,args:null,concreteType:"UIOption",kind:"LinkedField",name:"uiOption",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"uiType",storageKey:null},{alias:null,args:null,concreteType:"SliderOption",kind:"LinkedField",name:"slider",plural:!1,selections:[o,s,{alias:null,args:null,kind:"ScalarField",name:"step",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"NumberOption",kind:"LinkedField",name:"number",plural:!1,selections:[o,s],storageKey:null},{alias:null,args:null,concreteType:"ChoiceOption",kind:"LinkedField",name:"choices",plural:!1,selections:[{alias:null,args:null,concreteType:"ChoiceItem",kind:"LinkedField",name:"items",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"label",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"TextOption",kind:"LinkedField",name:"text",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"placeholder",storageKey:null}],storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"useRuntimeParameterSchemaPresetsQuery",selections:[{kind:"CatchField",field:{alias:"runtimeVariantPresetsResult",args:e,concreteType:"RuntimeVariantPresetConnection",kind:"LinkedField",name:"runtimeVariantPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariantPresetEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"node",plural:!1,selections:[a,i,t,r,p,u,y],storageKey:null}],storageKey:null}],storageKey:null},to:"RESULT"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"useRuntimeParameterSchemaPresetsQuery",selections:[{alias:"runtimeVariantPresetsResult",args:e,concreteType:"RuntimeVariantPresetConnection",kind:"LinkedField",name:"runtimeVariantPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariantPresetEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"node",plural:!1,selections:[a,i,t,r,p,u,y,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"9ec67e7389f1f7cec0f197e6ff23ec91",id:null,metadata:{},name:"useRuntimeParameterSchemaPresetsQuery",operationKind:"query",text:`query useRuntimeParameterSchemaPresetsQuery(
  $filter: RuntimeVariantPresetFilter
  $orderBy: [RuntimeVariantPresetOrderBy!]
) {
  runtimeVariantPresetsResult: runtimeVariantPresets(filter: $filter, orderBy: $orderBy, first: 100) {
    edges {
      node {
        name
        description
        rank
        category
        displayName
        targetSpec {
          presetTarget
          valueType
          defaultValue
          key
        }
        uiOption {
          uiType
          slider {
            min
            max
            step
          }
          number {
            min
            max
          }
          choices {
            items {
              value
              label
            }
          }
          text {
            placeholder
          }
        }
        id
      }
    }
  }
}
`}}}();tt.hash="ca5ee1b8f0a7378db0a58b62f8709a68";const at=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"filter"}],e={alias:"runtimeVariantsResult",args:[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Literal",name:"first",value:1}],concreteType:"RuntimeVariantConnection",kind:"LinkedField",name:"runtimeVariants",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariantEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"useRuntimeParameterSchemaVariantsQuery",selections:[{kind:"CatchField",field:e,to:"RESULT"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"useRuntimeParameterSchemaVariantsQuery",selections:[e]},params:{cacheID:"c682513f5e9e13cb4231c771873116d0",id:null,metadata:{},name:"useRuntimeParameterSchemaVariantsQuery",operationKind:"query",text:`query useRuntimeParameterSchemaVariantsQuery(
  $filter: RuntimeVariantFilter
) {
  runtimeVariantsResult: runtimeVariants(filter: $filter, first: 1) {
    edges {
      node {
        id
        name
      }
    }
  }
}
`}}}();at.hash="4a430bb72586e76dae1f300fdd57f51a";function Wa(l){var r,p,u,o,s;const e=je.useLazyLoadQuery(at,{filter:l?{name:{equals:l}}:{name:{equals:"__none__"}}},{fetchPolicy:"store-or-network"}),a=((r=e.runtimeVariantsResult)==null?void 0:r.ok)===!0?((s=(o=(u=(p=e.runtimeVariantsResult.value)==null?void 0:p.edges)==null?void 0:u[0])==null?void 0:o.node)==null?void 0:s.id)??null:null,i=a?$e(a):null,t=je.useLazyLoadQuery(tt,{filter:i?{runtimeVariantId:{equals:i}}:{name:{equals:"__none__"}},orderBy:[{field:"RANK",direction:"ASC"}]},{fetchPolicy:"store-or-network"});return N.useMemo(()=>{var V,M;if(!l||!i)return null;const y=((V=t.runtimeVariantPresetsResult)==null?void 0:V.ok)===!0?((M=t.runtimeVariantPresetsResult.value)==null?void 0:M.edges)??[]:[];if(y.length===0)return null;const c=y.map(f=>f==null?void 0:f.node).filter(Boolean).map(f=>{var g,K,j,_,q;return{name:f.name,description:f.description??null,rank:f.rank,category:f.category??null,displayName:f.displayName??null,presetTarget:f.targetSpec.presetTarget,valueType:f.targetSpec.valueType,defaultValue:f.targetSpec.defaultValue??null,key:f.targetSpec.key,uiType:((g=f.uiOption)==null?void 0:g.uiType)??null,slider:(K=f.uiOption)!=null&&K.slider?{min:f.uiOption.slider.min,max:f.uiOption.slider.max,step:f.uiOption.slider.step}:null,number:(j=f.uiOption)!=null&&j.number?{min:f.uiOption.number.min??null,max:f.uiOption.number.max??null}:null,choices:(_=f.uiOption)!=null&&_.choices?{items:f.uiOption.choices.items.map(C=>({value:C.value,label:C.label}))}:null,text:(q=f.uiOption)!=null&&q.text?{placeholder:f.uiOption.text.placeholder??null}:null}}),k=new Map;for(const f of c){const g=f.category??"general",K=k.get(g)??[];K.push(f),k.set(g,K)}return Array.from(k.entries()).map(([f,g])=>({category:f,params:g}))},[l,i,t])}function nn(l){const e={};for(const a of l)for(const i of a.params)i.defaultValue!==null&&(e[i.key]=i.defaultValue);return e}function it(l){const e=new Set;for(const a of l)for(const i of a.params)i.presetTarget==="ARGS"&&e.add(i.key);return e}function Ua(l){const e=new Set;for(const a of l)for(const i of a.params)i.presetTarget==="ENV"&&e.add(i.key);return e}function tn(l){return`${l.toUpperCase()}_EXTRA_ARGS`}const Ha=["vllm","sglang"];function Ga(){return Ha.map(tn)}function Xa(l){return l.flatMap(e=>e.params)}function Ya(l){return l.split("_").map(e=>e.charAt(0).toUpperCase()+e.slice(1)).join(" ")}const Ja=l=>{"use memo";const e=Je.c(114),{runtimeVariant:a,onChange:i,onTouchedKeysChange:t,onGroupsLoaded:r,initialExtraArgs:p,initialEnvVars:u}=l,{t:o}=Ze(),{token:s}=yl.useToken(),y=Wa(a);let c;e[0]!==y||e[1]!==r?(c=()=>{r==null||r(y)},e[0]=y,e[1]=r,e[2]=c):c=e[2];const k=N.useEffectEvent(c);let V;e[3]!==r?(V=()=>{r==null||r(null)},e[3]=r,e[4]=V):V=e[4];const M=N.useEffectEvent(V);let f;e[5]!==k||e[6]!==M?(f=()=>(k(),()=>{M()}),e[5]=k,e[6]=M,e[7]=f):f=e[7];let g;e[8]!==y?(g=[y],e[8]=y,e[9]=g):g=e[9],N.useEffect(f,g);let K;e[10]===Symbol.for("react.memo_cache_sentinel")?(K={},e[10]=K):K=e[10];const[j,_]=N.useState(K),q=j;let C;e[11]===Symbol.for("react.memo_cache_sentinel")?(C=new Set,e[11]=C):C=e[11];const[$,Q]=N.useState(C),[D,I]=N.useState("");let x;e[12]!==i?(x=O=>{_(O),i==null||i(O)},e[12]=i,e[13]=x):x=e[13];const S=x;let R;e[14]!==y||e[15]!==u||e[16]!==p||e[17]!==t||e[18]!==S?(R=()=>{if(!y)return;const O=nn(y);if(!!p||!!u){let pe={};const me={};if(p){const ye=it(y),{mappedArgs:Fe}=nt(p,ye);pe=Fe}if(u){const ye=Ua(y);for(const Fe of ye)u[Fe]!==void 0&&(me[Fe]=u[Fe])}const ke={...pe,...me};S({...O,...ke});const ve=new Set(Object.keys(ke));Q(ve),t==null||t(ve)}else S(O),Q(new Set),t==null||t(new Set)},e[14]=y,e[15]=u,e[16]=p,e[17]=t,e[18]=S,e[19]=R):R=e[19];const b=N.useEffectEvent(R);let d;e[20]!==b?(d=()=>{b()},e[20]=b,e[21]=d):d=e[21];let v;e[22]!==y||e[23]!==a?(v=[a,y],e[22]=y,e[23]=a,e[24]=v):v=e[24],N.useEffect(d,v);let h;e[25]!==i||e[26]!==t?(h=(O,Se)=>{_(pe=>{const me={...pe,[O]:Se};return queueMicrotask(()=>i==null?void 0:i(me)),me}),Q(pe=>{if(pe.has(O))return pe;const me=new Set(pe);return me.add(O),queueMicrotask(()=>t==null?void 0:t(me)),me})},e[25]=i,e[26]=t,e[27]=h):h=e[27];const B=h;let G;e[28]!==y||e[29]!==t||e[30]!==S?(G=()=>{if(!y)return;const O=nn(y);S(O),Q(new Set),t==null||t(new Set)},e[28]=y,e[29]=t,e[30]=S,e[31]=G):G=e[31];const z=G;if(!y)return null;let W,H,J,se,T,F,A,P,U,Y,ne;if(e[32]!==D||e[33]!==y||e[34]!==B||e[35]!==z||e[36]!==o||e[37]!==s.colorTextSecondary||e[38]!==s.marginSM||e[39]!==$||e[40]!==q){const O=y.map(li),Se=O.map(ni),pe=O.includes(D)?D:O[0]??"";H=jn,Y="small",e[52]===Symbol.for("react.memo_cache_sentinel")?(ne=["runtime-params"],e[52]=ne):ne=e[52],P="runtime-params";let me;e[53]===Symbol.for("react.memo_cache_sentinel")?(me={flex:1},e[53]=me):me=e[53];let ke;e[54]!==o?(ke=o("modelService.RuntimeParamTitle"),e[54]=o,e[55]=ke):ke=e[55];let ve;e[56]!==s.colorTextSecondary?(ve={color:s.colorTextSecondary},e[56]=s.colorTextSecondary,e[57]=ve):ve=e[57];let ye;e[58]!==o?(ye=o("general.Optional"),e[58]=o,e[59]=ye):ye=e[59];let Fe;e[60]!==ve||e[61]!==ye?(Fe=n.jsxs("span",{style:ve,children:["(",ye,")"]}),e[60]=ve,e[61]=ye,e[62]=Fe):Fe=e[62];let Re;e[63]!==ke||e[64]!==Fe?(Re=n.jsxs("span",{children:[ke," ",Fe]}),e[63]=ke,e[64]=Fe,e[65]=Re):Re=e[65];let be;e[66]!==o?(be=o("button.Reset"),e[66]=o,e[67]=be):be=e[67];let Me;e[68]===Symbol.for("react.memo_cache_sentinel")?(Me=n.jsx(Ka,{}),e[68]=Me):Me=e[68];let m;e[69]!==o?(m=o("button.Reset"),e[69]=o,e[70]=m):m=e[70];let L;e[71]!==z?(L=ie=>{ie.stopPropagation(),z()},e[71]=z,e[72]=L):L=e[72];const w=$.size===0;let E;e[73]!==m||e[74]!==L||e[75]!==w?(E=n.jsx(ql,{type:"link",size:"small",icon:Me,"aria-label":m,onClick:L,disabled:w}),e[73]=m,e[74]=L,e[75]=w,e[76]=E):E=e[76];let X;e[77]!==be||e[78]!==E?(X=n.jsx(dl,{title:be,children:E}),e[77]=be,e[78]=E,e[79]=X):X=e[79],e[80]!==Re||e[81]!==X?(U=n.jsxs(ae,{justify:"between",align:"center",style:me,children:[Re,X]}),e[80]=Re,e[81]=X,e[82]=U):U=e[82];let le;e[83]!==o?(le=o("modelService.RuntimeParamUnchangedHint"),e[83]=o,e[84]=le):le=e[84];let he;e[85]!==s.marginSM?(he={marginBottom:s.marginSM},e[85]=s.marginSM,e[86]=he):he=e[86],e[87]!==le||e[88]!==he?(A=n.jsx(xl,{type:"warning",showIcon:!0,title:le,style:he}),e[87]=le,e[88]=he,e[89]=A):A=e[89],W=Nt,J="small",se=pe,e[90]===Symbol.for("react.memo_cache_sentinel")?(T=ie=>I(ie),e[90]=T):T=e[90];let de;e[91]!==y||e[92]!==B||e[93]!==$||e[94]!==q?(de=ie=>{const ge=y.find(Ie=>Ie.category===ie.key);return{key:ie.key,label:ie.label,children:ge?n.jsx(Za,{group:ge,values:q,touchedKeys:$,onParamChange:B}):null}},e[91]=y,e[92]=B,e[93]=$,e[94]=q,e[95]=de):de=e[95],F=Se.map(de),e[32]=D,e[33]=y,e[34]=B,e[35]=z,e[36]=o,e[37]=s.colorTextSecondary,e[38]=s.marginSM,e[39]=$,e[40]=q,e[41]=W,e[42]=H,e[43]=J,e[44]=se,e[45]=T,e[46]=F,e[47]=A,e[48]=P,e[49]=U,e[50]=Y,e[51]=ne}else W=e[41],H=e[42],J=e[43],se=e[44],T=e[45],F=e[46],A=e[47],P=e[48],U=e[49],Y=e[50],ne=e[51];let Z;e[96]!==W||e[97]!==J||e[98]!==se||e[99]!==T||e[100]!==F?(Z=n.jsx(W,{size:J,activeKey:se,onChange:T,items:F}),e[96]=W,e[97]=J,e[98]=se,e[99]=T,e[100]=F,e[101]=Z):Z=e[101];let te;e[102]!==A||e[103]!==Z?(te=n.jsxs(n.Fragment,{children:[A,Z]}),e[102]=A,e[103]=Z,e[104]=te):te=e[104];let re;e[105]!==P||e[106]!==U||e[107]!==te?(re=[{key:P,label:U,children:te}],e[105]=P,e[106]=U,e[107]=te,e[108]=re):re=e[108];let ee;return e[109]!==H||e[110]!==Y||e[111]!==ne||e[112]!==re?(ee=n.jsx(H,{size:Y,defaultActiveKey:ne,items:re}),e[109]=H,e[110]=Y,e[111]=ne,e[112]=re,e[113]=ee):ee=e[113],ee},Za=l=>{"use memo";const e=Je.c(11),{group:a,values:i,touchedKeys:t,onParamChange:r}=l;let p;if(e[0]!==a.params||e[1]!==r||e[2]!==t||e[3]!==i){let o;e[5]!==r||e[6]!==t||e[7]!==i?(o=s=>n.jsx(ei,{param:s,value:i[s.key]??s.defaultValue??"",touched:t.has(s.key),onChange:y=>r(s.key,y)},s.key),e[5]=r,e[6]=t,e[7]=i,e[8]=o):o=e[8],p=a.params.map(o),e[0]=a.params,e[1]=r,e[2]=t,e[3]=i,e[4]=p}else p=e[4];let u;return e[9]!==p?(u=n.jsx(ae,{direction:"column",gap:"xxs",align:"stretch",children:p}),e[9]=p,e[10]=u):u=e[10],u},ei=l=>{"use memo";var M,f,g,K,j,_,q,C,$,Q;const e=Je.c(91),{param:a,value:i,touched:t,onChange:r}=l,{t:p}=Ze(),{token:u}=yl.useToken(),o=a.displayName??a.name,s=a.description??void 0;let y;e[0]!==u.marginXS?(y={marginBottom:u.marginXS},e[0]=u.marginXS,e[1]=y):y=e[1];const c=y,k=t?void 0:.45;switch(a.uiType){case"slider":{const D=((M=a.slider)==null?void 0:M.min)??0,I=((f=a.slider)==null?void 0:f.max)??100,x=((g=a.slider)==null?void 0:g.step)??1,S=i?parseFloat(i):D;let R;e[2]!==r?(R=z=>r(String(z)),e[2]=r,e[3]=R):R=e[3];let b;e[4]!==k?(b={opacity:k,transition:"opacity 0.2s"},e[4]=k,e[5]=b):b=e[5];let d;e[6]!==u.colorTextSecondary?(d={color:u.colorTextSecondary},e[6]=u.colorTextSecondary,e[7]=d):d=e[7];let v;e[8]!==I||e[9]!==d?(v={style:d,label:I},e[8]=I,e[9]=d,e[10]=v):v=e[10];let h;e[11]!==I||e[12]!==D||e[13]!==v?(h={marks:{[D]:D,[I]:v}},e[11]=I,e[12]=D,e[13]=v,e[14]=h):h=e[14];let B;e[15]!==I||e[16]!==D||e[17]!==x||e[18]!==S||e[19]!==R||e[20]!==b||e[21]!==h?(B=n.jsx(_t,{min:D,max:I,step:x,value:S,onChange:R,inputContainerMinWidth:190,style:b,sliderProps:h}),e[15]=I,e[16]=D,e[17]=x,e[18]=S,e[19]=R,e[20]=b,e[21]=h,e[22]=B):B=e[22];let G;return e[23]!==c||e[24]!==o||e[25]!==B||e[26]!==s?(G=n.jsx(ue.Item,{label:o,tooltip:s,style:c,required:!0,children:B}),e[23]=c,e[24]=o,e[25]=B,e[26]=s,e[27]=G):G=e[27],G}case"number_input":{const D=((K=a.number)==null?void 0:K.min)??void 0,I=((j=a.number)==null?void 0:j.max)??void 0,x=a.valueType==="INT",S=x?1:.1,R=i?x?parseInt(i,10):parseFloat(i):void 0;let b;e[28]!==r?(b=B=>{B!==null&&r(String(B))},e[28]=r,e[29]=b):b=e[29];let d;e[30]!==k?(d={width:"100%",opacity:k,transition:"opacity 0.2s"},e[30]=k,e[31]=d):d=e[31];let v;e[32]!==I||e[33]!==D||e[34]!==S||e[35]!==R||e[36]!==b||e[37]!==d?(v=n.jsx(ul,{min:D,max:I,step:S,value:R,onChange:b,style:d}),e[32]=I,e[33]=D,e[34]=S,e[35]=R,e[36]=b,e[37]=d,e[38]=v):v=e[38];let h;return e[39]!==c||e[40]!==o||e[41]!==v||e[42]!==s?(h=n.jsx(ue.Item,{label:o,tooltip:s,style:c,required:!0,children:v}),e[39]=c,e[40]=o,e[41]=v,e[42]=s,e[43]=h):h=e[43],h}case"select":{const D=i||void 0;let I;e[44]!==r?(I=d=>r(d??""),e[44]=r,e[45]=I):I=e[45];let x;e[46]!==k?(x={opacity:k,transition:"opacity 0.2s"},e[46]=k,e[47]=x):x=e[47];let S;e[48]!==((_=a.choices)==null?void 0:_.items)?(S=(q=a.choices)==null?void 0:q.items.map(ti),e[48]=(C=a.choices)==null?void 0:C.items,e[49]=S):S=e[49];let R;e[50]!==D||e[51]!==I||e[52]!==x||e[53]!==S?(R=n.jsx(wl,{value:D,allowClear:!0,onChange:I,style:x,options:S}),e[50]=D,e[51]=I,e[52]=x,e[53]=S,e[54]=R):R=e[54];let b;return e[55]!==c||e[56]!==o||e[57]!==R||e[58]!==s?(b=n.jsx(ue.Item,{label:o,tooltip:s,style:c,required:!0,children:R}),e[55]=c,e[56]=o,e[57]=R,e[58]=s,e[59]=b):b=e[59],b}case"checkbox":{const D=i==="true";let I;e[60]!==r?(I=d=>r(d.target.checked?"true":"false"),e[60]=r,e[61]=I):I=e[61];let x;e[62]!==k?(x={opacity:k,transition:"opacity 0.2s"},e[62]=k,e[63]=x):x=e[63];let S;e[64]!==p?(S=p("general.Enable"),e[64]=p,e[65]=S):S=e[65];let R;e[66]!==o||e[67]!==D||e[68]!==I||e[69]!==x||e[70]!==S?(R=n.jsx(Ln,{checked:D,onChange:I,"aria-label":o,style:x,children:S}),e[66]=o,e[67]=D,e[68]=I,e[69]=x,e[70]=S,e[71]=R):R=e[71];let b;return e[72]!==c||e[73]!==o||e[74]!==R||e[75]!==s?(b=n.jsx(ue.Item,{label:o,tooltip:s,style:c,required:!0,children:R}),e[72]=c,e[73]=o,e[74]=R,e[75]=s,e[76]=b):b=e[76],b}case"text_input":default:{const D=t?i:"";let I;e[77]!==r?(I=d=>r(d.target.value),e[77]=r,e[78]=I):I=e[78];const x=t?((Q=a.text)==null?void 0:Q.placeholder)??void 0:i||((($=a.text)==null?void 0:$.placeholder)??void 0);let S;e[79]!==k?(S={opacity:k,transition:"opacity 0.2s"},e[79]=k,e[80]=S):S=e[80];let R;e[81]!==D||e[82]!==I||e[83]!==x||e[84]!==S?(R=n.jsx(Tl,{value:D,onChange:I,placeholder:x,style:S}),e[81]=D,e[82]=I,e[83]=x,e[84]=S,e[85]=R):R=e[85];let b;return e[86]!==c||e[87]!==o||e[88]!==R||e[89]!==s?(b=n.jsx(ue.Item,{label:o,tooltip:s,style:c,required:!0,children:R}),e[86]=c,e[87]=o,e[88]=R,e[89]=s,e[90]=b):b=e[90],b}}};function li(l){return l.category}function ni(l){return{key:l,label:Ya(l)}}function ti(l){return{value:l.value,label:l.label}}const Jl=({children:l})=>{const{token:e}=yl.useToken();return n.jsx(Gt,{titlePlacement:"left",children:n.jsx(Oe.Text,{type:"secondary",style:{fontSize:e.fontSizeSM},children:l})})},ai=l=>{"use memo";const e=Je.c(6),{presetId:a,onCancel:i}=l;let t;e[0]===Symbol.for("react.memo_cache_sentinel")?(t=Zn,e[0]=t):t=e[0];let r;e[1]!==a?(r={id:a},e[1]=a,e[2]=r):r=e[2];const p=je.useLazyLoadQuery(t,r);let u;return e[3]!==p.deploymentRevisionPreset||e[4]!==i?(u=n.jsx(Xt,{open:!0,presetFrgmt:p.deploymentRevisionPreset,onCancel:i}),e[3]=p.deploymentRevisionPreset,e[4]=i,e[5]=u):u=e[5],u},ii=({onRequestClose:l,deploymentId:e,open:a,...i})=>{"use memo";var Re,be,Me;const{t}=Ze(),{token:r}=yl.useToken(),{message:p}=bl.useApp(),u=je.useRelayEnvironment(),{id:o}=Et(),{logger:s}=Kl(),{open:y}=Ot(),c=N.useRef(null),k=N.useRef(null),[V,M]=N.useState(!1),f=N.useDeferredValue(a),[g]=ue.useForm(),[K]=ue.useForm(),[j,_]=N.useState(!0),[q,C]=Xl("deploymentRevisionCreationMode"),$=q??"preset",[Q,D]=N.useState(null),[I,x]=N.useState(null),[S,R]=N.useState(null),[b,d]=N.useState({}),v=N.useRef({}),h=N.useRef(new Set),B=N.useRef(null),[G,z]=N.useState(""),[W,H]=N.useState(void 0),J=N.useRef({}),T=je.useLazyLoadQuery(Jn,{deploymentId:e},{fetchPolicy:f&&a?"store-and-network":"store-only"}).deployment,F=T==null?void 0:T.currentRevision,[A,P]=N.useState(void 0);N.useEffect(()=>{if(!a)return;let m=!1;return je.fetchQuery(u,Yn,{},{fetchPolicy:"store-or-network"}).toPromise().then(L=>{var w;m||P((((w=L==null?void 0:L.deploymentRevisionPresets)==null?void 0:w.count)??0)===0)}).catch(()=>{m||P(!1)}),()=>{m=!0}},[a,u]);const U=(Re=F==null?void 0:F.modelMountConfig)!=null&&Re.vfolderId?El("VirtualFolderNode",(be=F==null?void 0:F.modelMountConfig)==null?void 0:be.vfolderId):void 0,Y=N.useRef(new Map),ne=async m=>{const L=Y.current.get(m);if(L)return L;const w=await je.fetchQuery(u,Xn,{id:m},{fetchPolicy:"store-or-network"}).toPromise(),E=(w==null?void 0:w.deploymentRevisionPreset)??null;return E&&Y.current.set(m,E),E},[Z,te]=je.useMutation(Gn),re=async m=>{var Ie,oe,xe,Ke,we,qe,Pe,Ne,De;const L=m.resourceSlots??[],w=L.find(ce=>ce.slotName==="cpu"),E=L.find(ce=>ce.slotName==="mem"),X=L.find(ce=>ce.slotName!=="cpu"&&ce.slotName!=="mem"),le=(((Ie=m.resource)==null?void 0:Ie.resourceOpts)??[]).find(ce=>ce.name==="shmem"),he=((oe=m.cluster)==null?void 0:oe.clusterMode)==="SINGLE_NODE"?"single-node":"multi-node";let de;if((xe=m.execution)!=null&&xe.imageId)try{const ce=await je.fetchQuery(u,Hn,{id:m.execution.imageId},{fetchPolicy:"store-or-network"}).toPromise();de=((we=(Ke=ce==null?void 0:ce.imageV2)==null?void 0:Ke.identity)==null?void 0:we.canonicalName)??void 0}catch{de=void 0}const ie=(((qe=m.execution)==null?void 0:qe.environ)??[]).map(ce=>({variable:ce.key,value:ce.value}));return{cluster_mode:he,cluster_size:((Pe=m.cluster)==null?void 0:Pe.clusterSize)??1,allocationPreset:"custom",resource:{cpu:w?Number(w.quantity):0,mem:((Ne=Nl(String((E==null?void 0:E.quantity)??"0"),"g",2))==null?void 0:Ne.value)??"0g",shmem:((De=Nl((le==null?void 0:le.value)??Pl,"g",2))==null?void 0:De.value)??Pl,...X?{acceleratorType:X.slotName,accelerator:X.slotName==="cuda.shares"?parseFloat(String(X.quantity)):parseInt(String(X.quantity),10)}:{}},enabledAutomaticShmem:!le,runtimeVariantId:m.runtimeVariantId??void 0,environ:ie,...de?{environments:{version:de}}:{}}},ee=async m=>{if(m===$)return;if($==="preset"&&m==="custom"){const E=K.getFieldsValue(),X=E.revisionPresetId;let le={};if(X){const he=await ne(X);he&&(le=await re(he))}E.modelFolderId&&(le.modelFolderId=E.modelFolderId),D(Object.keys(le).length>0?le:null),C("custom");return}const L=g.getFieldsValue(),w={};L.modelFolderId&&(w.modelFolderId=L.modelFolderId),g.resetFields(),D(null),x(Object.keys(w).length>0?w:null),C("preset")},O=()=>{var Ke,we,qe,Pe,Ne,De,ce,Ce,Le,Ee,Qe,Be,ze,We,He,Ve,Ue,Ge,al,el,ll,nl,il,sl,rl,ol,gl,kl,Te,Ae,Xe;if(!F)return;const m=F,L=m.resourceSlots??[],w=L.find(fe=>fe.slotName==="cpu"),E=L.find(fe=>fe.slotName==="mem"),X=L.find(fe=>fe.slotName!=="cpu"&&fe.slotName!=="mem"),le=(((we=(Ke=m.resourceConfig)==null?void 0:Ke.resourceOpts)==null?void 0:we.entries)??[]).find(fe=>fe.name==="shmem"),he=((Pe=(qe=m.modelRuntimeConfig)==null?void 0:qe.runtimeVariant)==null?void 0:Pe.name)??"",de=he==="custom",ie=(Ne=m.modelRuntimeConfig)==null?void 0:Ne.runtimeVariantId;ie&&he&&d(fe=>({...fe,[ie]:he}));const ge=(Ce=(ce=(De=m.modelDefinition)==null?void 0:De.models)==null?void 0:ce[0])==null?void 0:Ce.service,Ie=(Qe=(Ee=(Le=m.modelDefinition)==null?void 0:Le.models)==null?void 0:Ee[0])==null?void 0:Qe.modelPath,oe=de&&!!ge&&(((Be=ge.startCommand)==null?void 0:Be.length)??0)>0;J.current=Sn((m.extraMounts??[]).filter(fe=>!!fe.mountDestination).map(fe=>[fe.vfolderId.replace(/-/g,""),fe.mountDestination]));const xe=Object.fromEntries((((We=(ze=m.modelRuntimeConfig)==null?void 0:ze.environ)==null?void 0:We.entries)??[]).map(fe=>[fe.name,fe.value]));if(!de&&he){const fe=tn(he),{[fe]:tl,...hl}=xe;z(tl??""),H(Object.keys(hl).length>0?hl:void 0)}g.setFieldsValue({cluster_mode:((He=m.clusterConfig)==null?void 0:He.mode)==="SINGLE_NODE"?"single-node":"multi-node",cluster_size:((Ve=m.clusterConfig)==null?void 0:Ve.size)??1,allocationPreset:"custom",resource:{cpu:w?Number(w.quantity):0,mem:((Ue=Nl(String((E==null?void 0:E.quantity)??"0"),"g",2))==null?void 0:Ue.value)??"0g",shmem:((Ge=Nl((le==null?void 0:le.value)??Pl,"g",2))==null?void 0:Ge.value)??Pl,...X?{acceleratorType:X.slotName,accelerator:X.slotName==="cuda.shares"?parseFloat(String(X.quantity)):parseInt(String(X.quantity),10)}:{}},enabledAutomaticShmem:!le,mount_ids:(m.extraMounts??[]).map(fe=>fe.vfolderId.replace(/-/g,"")),mount_id_map:Sn((m.extraMounts??[]).filter(fe=>!!fe.mountDestination).map(fe=>[fe.vfolderId.replace(/-/g,""),fe.mountDestination])),runtimeVariantId:((al=m.modelRuntimeConfig)==null?void 0:al.runtimeVariantId)??void 0,modelFolderId:(el=m.modelMountConfig)!=null&&el.vfolderId?El("VirtualFolderNode",m.modelMountConfig.vfolderId):void 0,mountDestination:((ll=m.modelMountConfig)==null?void 0:ll.mountDestination)??"/models",definitionPath:((nl=m.modelMountConfig)==null?void 0:nl.definitionPath)??void 0,environments:(sl=(il=m.imageV2)==null?void 0:il.identity)!=null&&sl.canonicalName?{version:m.imageV2.identity.canonicalName}:void 0,environ:(((ol=(rl=m.modelRuntimeConfig)==null?void 0:rl.environ)==null?void 0:ol.entries)??[]).map(fe=>({variable:fe.name,value:fe.value})),...oe&&ge?{customDefinitionMode:"command",startCommand:xa(ge.startCommand??[]),commandPort:ge.port,commandHealthCheck:((gl=ge.healthCheck)==null?void 0:gl.path)??void 0,commandModelMount:Ie??"/models",commandInitialDelay:((kl=ge.healthCheck)==null?void 0:kl.initialDelay)??void 0,commandMaxRetries:((Te=ge.healthCheck)==null?void 0:Te.maxRetries)??void 0,commandInterval:((Ae=ge.healthCheck)==null?void 0:Ae.interval)??void 0,commandMaxWaitTime:((Xe=ge.healthCheck)==null?void 0:Xe.maxWaitTime)??void 0}:de?{customDefinitionMode:"file"}:{}})},Se=N.useEffectEvent(()=>{Q&&(g.setFieldsValue(Q),D(null))}),pe=N.useEffectEvent(()=>{I&&(K.setFieldsValue(I),x(null))});N.useEffect(()=>{$==="custom"?Se():pe()},[$]);const me=(m,L)=>{const w=B.current;if(!w||Object.keys(v.current).length===0)return;const E=tn(L);for(const oe of Ga())oe!==E&&delete m[oe];const X={};for(const[oe,xe]of Object.entries(v.current))h.current.has(oe)&&(X[oe]=xe);const le=Xa(w),he=new Map(le.map(oe=>[oe.key,oe])),de=nn(w),ie={},ge={};for(const[oe,xe]of Object.entries(X)){if(xe===""||xe===void 0)continue;const Ke=he.get(oe);Ke&&(Ke.presetTarget==="ENV"?ge[oe]=xe:ie[oe]=xe)}const Ie=it(w);if(m[E]&&Ie.size>0){const{unmappedText:oe}=nt(m[E],Ie);oe?m[E]=oe:delete m[E]}for(const oe of le)oe.presetTarget==="ENV"&&delete m[oe.key];if(Object.keys(ie).length>0){const oe=m[E]??"",xe=za(ie,oe,de);xe?m[E]=xe:delete m[E]}for(const[oe,xe]of Object.entries(ge)){const Ke=he.get(oe);(Ke==null?void 0:Ke.defaultValue)!==null&&(Ke==null?void 0:Ke.defaultValue)===xe||(m[oe]=xe)}},ke=m=>{var Pe,Ne;const L=()=>{g.setFields([{name:["environments","version"],errors:[t("modelService.ImageRequired")]}]),g.scrollToField(["environments","version"],{behavior:"smooth",block:"center"})},w=(Ne=(Pe=m.environments)==null?void 0:Pe.image)==null?void 0:Ne.id;if(!w){L();return}const E=Yl(w);if(!E){L();return}const X=[{resourceType:"cpu",quantity:String(m.resource.cpu)},{resourceType:"mem",quantity:m.resource.mem}];m.resource.acceleratorType&&m.resource.accelerator&&m.resource.accelerator>0&&X.push({resourceType:m.resource.acceleratorType,quantity:String(m.resource.accelerator)});const le=[];m.resource.shmem&&le.push({name:"shmem",value:m.resource.shmem});const he=m.cluster_mode==="single-node"||m.cluster_mode==="multi-node"&&m.cluster_size===1?"SINGLE_NODE":"MULTI_NODE",de=m.vfoldersNameMap??{},ie=(m.mount_ids??[]).map(De=>{var Ce;const ce=((Ce=m.mount_id_map)==null?void 0:Ce[De])||J.current[De]||(de[De]?`/home/work/${de[De]}`:`/home/work/${De}`);return{vfolderId:Mn(De),mountDestination:ce}}),ge=b[m.runtimeVariantId]??"",Ie=ge==="custom",oe=m.customDefinitionMode==="command",xe={};for(const{variable:De,value:ce}of m.environ??[])De&&(xe[De]=ce);Ie||me(xe,ge);const Ke=Object.entries(xe).map(([De,ce])=>({name:De,value:ce})),we=Ie&&oe&&m.startCommand?{models:[{name:"model",modelPath:m.commandModelMount??"/models",service:{preStartActions:[],startCommand:$n(m.startCommand),port:m.commandPort??8e3,healthCheck:m.commandHealthCheck?{path:m.commandHealthCheck,interval:m.commandInterval??10,maxRetries:m.commandMaxRetries??10,maxWaitTime:m.commandMaxWaitTime??15,initialDelay:m.commandInitialDelay}:null}}]}:null,qe=Ie&&oe?m.commandModelMount??"/models":m.mountDestination||"/models";Z({variables:{input:{deploymentId:$e(e)??e,clusterConfig:{mode:he,size:m.cluster_size},resourceConfig:{resourceSlots:{entries:X},resourceOpts:le.length>0?{entries:le}:null},image:{id:E},modelRuntimeConfig:{runtimeVariantId:m.runtimeVariantId,environ:Ke.length>0?{entries:Ke}:null},modelMountConfig:{vfolderId:$e(m.modelFolderId),mountDestination:qe,definitionPath:m.definitionPath},modelDefinition:we,extraMounts:ie.length>0?ie:null,options:{autoActivate:j}}},onCompleted:(De,ce)=>{var Ce;if(ce&&ce.length>0){const Le=ce[0],Ee=(Ce=Le==null?void 0:Le.message)==null?void 0:Ce.includes("Another deployment is already in progress");p.error(Ee?t("deployment.AnotherDeploymentInProgress"):(Le==null?void 0:Le.message)??t("general.ErrorOccurred"));return}g.resetFields(),p.success(t("deployment.RevisionAdded")),l(!0)},onError:De=>{var Ce;const ce=(Ce=De.message)==null?void 0:Ce.includes("Another deployment is already in progress");p.error(ce?t("deployment.AnotherDeploymentInProgress"):De.message??t("general.ErrorOccurred"))}})},ve=m=>{Z({variables:{input:{deploymentId:$e(e)??e,revisionPresetId:m.revisionPresetId,modelMountConfig:{vfolderId:$e(m.modelFolderId),mountDestination:"/models"},options:{autoActivate:j}}},onCompleted:(L,w)=>{var E;if(w&&w.length>0){const X=w[0],le=(E=X==null?void 0:X.message)==null?void 0:E.includes("Another deployment is already in progress");s.error("[DeploymentAddRevisionModal] addModelRevision (preset) returned errors",w),p.error(le?t("deployment.AnotherDeploymentInProgress"):(X==null?void 0:X.message)??t("general.ErrorOccurred"));return}K.resetFields(),p.success(t("deployment.RevisionAdded")),l(!0)},onError:L=>{var E;const w=(E=L.message)==null?void 0:E.includes("Another deployment is already in progress");s.error("[DeploymentAddRevisionModal] addModelRevision (preset) failed",L),p.error(w?t("deployment.AnotherDeploymentInProgress"):L.message??t("general.ErrorOccurred"))}})},ye=()=>{requestAnimationFrame(()=>{const m=document.querySelector(".ant-modal-body .ant-form-item-has-error");m&&m.scrollIntoView({behavior:"smooth",block:"start"})})},Fe=async()=>{const m=$==="preset"?K:g;try{await m.validateFields()}catch{ye();return}m.submit()};return n.jsxs(Ul,{open:a,loading:f!==a,title:n.jsxs(ae,{direction:"row",align:"center",justify:"between",gap:"md",wrap:"wrap",style:{paddingRight:r.paddingLG},children:[n.jsx("span",{children:t("deployment.AddRevision")}),n.jsx(hn,{value:$,onChange:ee,options:[{label:t("deployment.PresetMode"),value:"preset"},{label:t("deployment.CustomMode"),value:"custom"}],style:{fontWeight:"normal"}})]}),width:720,footer:n.jsxs(ae,{direction:"row",align:"center",justify:"between",gap:"sm",children:[n.jsx(Ln,{checked:j,onChange:m=>_(m.target.checked),disabled:$==="preset"&&A,children:t("deployment.AutoApply")}),n.jsxs(ae,{direction:"row",align:"center",gap:"xs",children:[n.jsx(Ye,{onClick:()=>l(),children:t("button.Cancel")}),n.jsx(Ye,{type:"primary",loading:te,onClick:Fe,disabled:$==="preset"&&A,children:t("deployment.AddRevision")})]})]}),onCancel:()=>l(),confirmLoading:te,destroyOnHidden:!0,...i,children:[$==="preset"?A?n.jsx(xl,{type:"info",showIcon:!0,style:{marginTop:r.marginXS},title:t("deployment.NoPresetsAvailable"),description:t("deployment.NoPresetsAvailableSwitchToCustom")}):n.jsxs(ue,{form:K,layout:"vertical",style:{marginTop:r.marginXS},onFinish:ve,onFinishFailed:ye,initialValues:{modelFolderId:U},children:[n.jsx(ue.Item,{label:t("modelStore.Preset"),tooltip:t("modelStore.PresetTooltip"),required:!0,children:n.jsxs(ae,{direction:"row",gap:"xs",children:[n.jsx(ue.Item,{name:"revisionPresetId",noStyle:!0,rules:[{required:!0}],children:n.jsx($t,{style:{flex:1}})}),n.jsx(ue.Item,{dependencies:["revisionPresetId"],noStyle:!0,children:({getFieldValue:m})=>{const L=m("revisionPresetId");return n.jsx(Ol.Compact,{children:n.jsx(dl,{title:t("modelService.DeploymentPresetDetail"),children:n.jsx(Ye,{icon:n.jsx(wt,{}),disabled:!L,onClick:()=>{L&&R(L)}})})})}})]})}),n.jsx(ue.Item,{label:t("deployment.ModelFolder"),tooltip:t("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(ae,{direction:"row",gap:"xs",children:[n.jsx(ue.Item,{name:"modelFolderId",noStyle:!0,rules:[{required:!0}],children:n.jsx(xn,{ref:c,currentProjectId:o??void 0,disabled:!o,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})}),n.jsx(ue.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:m})=>{const L=m("modelFolderId");return n.jsxs(Ol.Compact,{children:[n.jsx(dl,{title:t("modelService.OpenFolder"),children:n.jsx(Ye,{icon:n.jsx(Rn,{}),disabled:!L,onClick:()=>{L&&y($e(L))}})}),n.jsx(dl,{title:t("data.CreateANewStorageFolder"),children:n.jsx(Ye,{icon:n.jsx(fn,{}),onClick:()=>M(!0)})}),n.jsx(dl,{title:t("button.Refresh"),children:n.jsx(Ye,{icon:n.jsx(kn,{}),onClick:()=>{N.startTransition(()=>{var w;(w=c.current)==null||w.refetch()})}})})]})}})]})})]},"preset-form"):n.jsxs(ue,{form:g,layout:"vertical",style:{marginTop:r.marginXS},onFinish:ke,onFinishFailed:ye,initialValues:Wt({},Ut,{resourceGroup:(Me=T==null?void 0:T.metadata)==null?void 0:Me.resourceGroupName,mountDestination:"/models",customDefinitionMode:"command",commandPort:8e3,commandHealthCheck:"/health",commandModelMount:"/models",commandInitialDelay:60,commandMaxRetries:10,commandInterval:10,commandMaxWaitTime:15,environ:[]}),children:[F?n.jsx(xl,{type:"info",showIcon:!0,style:{marginBottom:r.marginMD},title:t("deployment.CurrentRevisionAvailableDescription"),action:n.jsx(Ye,{size:"small",type:"primary",onClick:()=>O(),children:t("deployment.LoadCurrentRevision")})}):null,n.jsx(Jl,{children:t("deployment.step.ModelAndRuntime")}),n.jsx(ue.Item,{label:t("deployment.ModelFolder"),tooltip:t("deployment.ModelFolderTooltip"),required:!0,children:n.jsxs(ae,{direction:"row",gap:"xs",children:[n.jsx(ue.Item,{name:"modelFolderId",noStyle:!0,rules:[{required:!0}],children:n.jsx(xn,{ref:k,currentProjectId:o??void 0,disabled:!o,excludeDeleted:!0,filter:'usage_mode == "model"',style:{flex:1}})}),n.jsx(ue.Item,{dependencies:["modelFolderId"],noStyle:!0,children:({getFieldValue:m})=>{const L=m("modelFolderId");return n.jsxs(Ol.Compact,{children:[n.jsx(dl,{title:t("modelService.OpenFolder"),children:n.jsx(Ye,{icon:n.jsx(Rn,{}),disabled:!L,onClick:()=>{L&&y($e(L))}})}),n.jsx(dl,{title:t("data.CreateANewStorageFolder"),children:n.jsx(Ye,{icon:n.jsx(fn,{}),onClick:()=>M(!0)})}),n.jsx(dl,{title:t("button.Refresh"),children:n.jsx(Ye,{icon:n.jsx(kn,{}),onClick:()=>{N.startTransition(()=>{var w;(w=k.current)==null||w.refetch()})}})})]})}})]})}),n.jsx(ue.Item,{name:"runtimeVariantId",label:t("deployment.RuntimeVariant"),tooltip:t("deployment.RuntimeVariantTooltip"),rules:[{required:!0},{warningOnly:!0,validator:async(m,L)=>{const w=b[L];return w&&w!=="custom"?Promise.reject(t("modelService.RuntimeVariantDefaultCommandAppliedNote")):Promise.resolve()}}],children:n.jsx(ja,{onResolvedNamesChange:m=>d(L=>({...L,...m}))})}),n.jsx(ue.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:m})=>{const L=m("runtimeVariantId"),w=b[L];return!w||w==="custom"?null:n.jsx("div",{style:{marginBottom:r.marginMD},children:n.jsx(N.Suspense,{fallback:null,children:n.jsx(Ja,{runtimeVariant:w,onChange:E=>{v.current={...v.current,...E}},onTouchedKeysChange:E=>{h.current=E},onGroupsLoaded:E=>{B.current=E},initialExtraArgs:G,initialEnvVars:W})})})}}),n.jsx(ue.Item,{dependencies:["runtimeVariantId"],noStyle:!0,children:({getFieldValue:m})=>{const L=m("runtimeVariantId");return b[L]!=="custom"?null:n.jsxs(n.Fragment,{children:[n.jsx(ue.Item,{name:"customDefinitionMode",noStyle:!0,children:n.jsx(hn,{options:[{label:t("modelService.EnterCommand"),value:"command"},{label:t("modelService.UseConfigFile"),value:"file"}],style:{marginBottom:r.marginMD}})}),n.jsx(ue.Item,{dependencies:["customDefinitionMode"],noStyle:!0,children:({getFieldValue:E})=>E("customDefinitionMode")==="command"?n.jsxs(n.Fragment,{children:[n.jsx(ue.Item,{name:"startCommand",label:t("modelService.StartCommand"),tooltip:t("modelService.StartCommandTooltip"),rules:[{required:!0,whitespace:!0}],children:n.jsx(Tl.TextArea,{placeholder:t("modelService.StartCommandPlaceholder"),autoSize:{minRows:2}})}),n.jsx(ue.Item,{name:"commandModelMount",label:t("modelService.ModelMountDestination"),tooltip:t("modelService.ModelMountTooltip"),children:n.jsx(Tl,{placeholder:"/models",allowClear:!0})}),n.jsxs(ae,{gap:"sm",children:[n.jsx(ue.Item,{name:"commandPort",label:t("modelService.Port"),tooltip:t("modelService.PortTooltip"),style:{flex:1},children:n.jsx(ul,{min:1,max:65535,style:{width:"100%"}})}),n.jsx(ue.Item,{name:"commandHealthCheck",label:t("modelService.HealthCheck"),tooltip:t("modelService.HealthCheckTooltip"),style:{flex:1},children:n.jsx(Tl,{placeholder:"/health",allowClear:!0})})]}),n.jsxs(ae,{gap:"sm",children:[n.jsx(ue.Item,{name:"commandInitialDelay",label:t("modelService.InitialDelay"),tooltip:t("modelService.InitialDelayTooltip"),style:{flex:1},children:n.jsx(ul,{min:0,step:.5,style:{width:"100%"}})}),n.jsx(ue.Item,{name:"commandMaxRetries",label:t("modelService.MaxRetries"),tooltip:t("modelService.MaxRetriesTooltip"),style:{flex:1},children:n.jsx(ul,{min:0,style:{width:"100%"}})})]}),n.jsxs(ae,{gap:"sm",children:[n.jsx(ue.Item,{name:"commandInterval",label:t("modelService.Interval"),tooltip:t("modelService.IntervalTooltip"),style:{flex:1},children:n.jsx(ul,{min:1,step:.5,style:{width:"100%"}})}),n.jsx(ue.Item,{name:"commandMaxWaitTime",label:t("modelService.MaxWaitTime"),tooltip:t("modelService.MaxWaitTimeTooltip"),style:{flex:1},children:n.jsx(ul,{min:1,step:.5,style:{width:"100%"}})})]})]}):n.jsxs(ae,{gap:"sm",children:[n.jsx(ue.Item,{name:"mountDestination",label:t("deployment.ModelMountDestination"),tooltip:t("modelService.ModelMountTooltip"),rules:[{required:!0}],style:{flex:1},children:n.jsx(Tl,{allowClear:!0,placeholder:"/models"})}),n.jsx(ue.Item,{name:"definitionPath",label:t("deployment.ModelDefinitionPath"),tooltip:t("modelService.ModelDefinitionPathTooltip"),style:{flex:1},children:n.jsx(Tl,{allowClear:!0,placeholder:"model-definition.yaml"})})]})})]})}}),n.jsx(Jl,{children:t("session.launcher.Environments")}),n.jsx(N.Suspense,{fallback:n.jsx(pl,{active:!0,paragraph:{rows:2}}),children:n.jsx(qt,{})}),n.jsx(Qt,{name:"environ",formItemProps:{validateTrigger:["onChange","onBlur"]}}),n.jsx(Jl,{children:t("deployment.step.ClusterAndResources")}),n.jsx(N.Suspense,{fallback:n.jsx(pl,{active:!0,paragraph:{rows:4}}),children:n.jsx(Bt,{enableResourcePresets:!0,hideResourceGroupFormItem:!0})}),n.jsx(jn,{items:[{key:"advanced",label:t("session.launcher.AdvancedSettings"),children:n.jsx(N.Suspense,{fallback:n.jsx(pl,{active:!0}),children:n.jsx(ue.Item,{noStyle:!0,dependencies:["modelFolderId","mount_id_map","mount_ids"],children:({getFieldValue:m})=>{var E;const L=m("modelFolderId"),w=L?(E=Yl(String(L)))==null?void 0:E.replace(/-/g,""):void 0;return n.jsx(zt,{label:t("modelService.AdditionalMounts"),tooltip:t("modelService.AdditionalMountsTooltip"),rowKey:"id",tableProps:{scroll:{x:"max-content",y:300}},rowFilter:X=>{var le;return X.usage_mode!=="model"&&X.status==="ready"&&!((le=X.name)!=null&&le.startsWith("."))&&X.id!==w}})}})})}]})]},"custom-form"),S&&n.jsx(N.Suspense,{fallback:null,children:n.jsx(ai,{presetId:S,onCancel:()=>R(null)})}),n.jsx(Ht,{open:V,initialValues:{usage_mode:"model"},onRequestClose:m=>{if(M(!1),m!=null&&m.id){const L=Yl(m.id);if(!L)return;const w=El("VirtualFolderNode",L),E=$==="preset"?K:g,X=$==="preset"?c:k;E.setFieldValue("modelFolderId",w),N.startTransition(()=>{var le;(le=X.current)==null||le.refetch()})}}})]})},st={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentAutoScalingTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null}],type:"ModelDeployment",abstractKey:null};st.hash="129d74dafb7ab8394c47065f3b9af25e";const rt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteAutoScalingRulePayload",kind:"LinkedField",name:"deleteAutoScalingRule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleListDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleListDeleteMutation",selections:e},params:{cacheID:"84fac37f17347340ba1f6a7991bc3624",id:null,metadata:{},name:"AutoScalingRuleListDeleteMutation",operationKind:"mutation",text:`mutation AutoScalingRuleListDeleteMutation(
  $input: DeleteAutoScalingRuleInput!
) {
  deleteAutoScalingRule(input: $input) {
    id
  }
}
`}}}();rt.hash="c0d22df767771306d1fc0a431e5d177b";const ot=function(){var l=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleListPresetsQuery",selections:l,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"AutoScalingRuleListPresetsQuery",selections:l},params:{cacheID:"9b99973a6bf38ac02bd91f644c8cb1a1",id:null,metadata:{},name:"AutoScalingRuleListPresetsQuery",operationKind:"query",text:`query AutoScalingRuleListPresetsQuery {
  prometheusQueryPresets {
    edges {
      node {
        id
        name
      }
    }
  }
}
`}}}();ot.hash="7f4c998b34def6faefe25959c5cb64e2";const ut=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},a={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},r=[{kind:"Variable",name:"id",variableName:"deploymentId"}],p=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],u={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null};return{fragment:{argumentDefinitions:[l,e,a,i,t],kind:"Fragment",metadata:null,name:"AutoScalingRuleListQuery",selections:[{alias:null,args:r,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:p,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[u,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[o,s,{args:null,kind:"FragmentSpread",name:"AutoScalingRuleListNodesFragment"},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,i,a,t,e],kind:"Operation",name:"AutoScalingRuleListQuery",selections:[{alias:null,args:r,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:p,concreteType:"AutoScalingRuleConnection",kind:"LinkedField",name:"autoScalingRules",plural:!1,selections:[u,{alias:null,args:null,concreteType:"AutoScalingRuleEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"node",plural:!1,selections:[o,s,{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},o],storageKey:null}]},params:{cacheID:"79f124acac426955bf7fe564f6d9a5c1",id:null,metadata:{},name:"AutoScalingRuleListQuery",operationKind:"query",text:`query AutoScalingRuleListQuery(
  $deploymentId: ID!
  $offset: Int
  $limit: Int
  $orderBy: [AutoScalingRuleOrderBy!]
  $filter: AutoScalingRuleFilter
) {
  deployment(id: $deploymentId) {
    autoScalingRules(offset: $offset, limit: $limit, orderBy: $orderBy, filter: $filter) {
      count
      edges {
        node {
          id
          metricName
          ...AutoScalingRuleListNodesFragment
          ...AutoScalingRuleEditorModalFragment
        }
      }
    }
    id
  }
}

fragment AutoScalingRuleEditorModalFragment on AutoScalingRule {
  id
  metricSource
  metricName
  minThreshold
  maxThreshold
  stepSize
  timeWindow
  minReplicas
  maxReplicas
  prometheusQueryPresetId
}

fragment AutoScalingRuleListNodesFragment on AutoScalingRule {
  id
  metricSource
  metricName
  minThreshold
  maxThreshold
  stepSize
  timeWindow
  minReplicas
  maxReplicas
  prometheusQueryPresetId
  createdAt
  lastTriggeredAt
  ...AutoScalingRuleEditorModalFragment
}
`}}}();ut.hash="bfa849a7cb503e04b249b2f73510b568";const dt={argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"AutoScalingRuleListNodesFragment",selections:[{kind:"RequiredField",field:{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},action:"NONE"},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastTriggeredAt",storageKey:null},{args:null,kind:"FragmentSpread",name:"AutoScalingRuleEditorModalFragment"}],type:"AutoScalingRule",abstractKey:null};dt.hash="54a32b764fc7e506f5bddfe218691cd2";const ct=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"UpdateAutoScalingRulePayload",kind:"LinkedField",name:"updateAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalUpdateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalUpdateMutation",selections:e},params:{cacheID:"f5194bd994f4693e29536fec36e4f0e4",id:null,metadata:{},name:"AutoScalingRuleEditorModalUpdateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalUpdateMutation(
  $input: UpdateAutoScalingRuleInput!
) {
  updateAutoScalingRule(input: $input) {
    rule {
      id
      metricSource
      metricName
      minThreshold
      maxThreshold
      stepSize
      timeWindow
      minReplicas
      maxReplicas
      prometheusQueryPresetId
    }
  }
}
`}}}();ct.hash="8e953443e1aa963b955810e5f97de017";const mt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"CreateAutoScalingRulePayload",kind:"LinkedField",name:"createAutoScalingRule",plural:!1,selections:[{alias:null,args:null,concreteType:"AutoScalingRule",kind:"LinkedField",name:"rule",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalCreateMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"AutoScalingRuleEditorModalCreateMutation",selections:e},params:{cacheID:"c7c250dabfc49b66cf1aebbff6414d44",id:null,metadata:{},name:"AutoScalingRuleEditorModalCreateMutation",operationKind:"mutation",text:`mutation AutoScalingRuleEditorModalCreateMutation(
  $input: CreateAutoScalingRuleInput!
) {
  createAutoScalingRule(input: $input) {
    rule {
      id
      metricSource
      metricName
      minThreshold
      maxThreshold
      stepSize
      timeWindow
      minReplicas
      maxReplicas
      prometheusQueryPresetId
    }
  }
}
`}}}();mt.hash="7afa475334295923b7754d0563a8b919";const gt={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricSource",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxThreshold",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"stepSize",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"minReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxReplicas",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"prometheusQueryPresetId",storageKey:null}],type:"AutoScalingRule",abstractKey:null};gt.hash="9dff1f6ce3b17626029eee3484220a7d";const pt=function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},a=[{alias:null,args:null,concreteType:"QueryDefinitionConnection",kind:"LinkedField",name:"prometheusQueryPresets",plural:!1,selections:[{alias:null,args:null,concreteType:"QueryDefinitionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"QueryDefinition",kind:"LinkedField",name:"node",plural:!1,selections:[l,e,{alias:null,args:null,kind:"ScalarField",name:"description",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"rank",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"categoryId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"metricName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queryTemplate",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"timeWindow",storageKey:null},{alias:null,args:null,concreteType:"QueryPresetCategory",kind:"LinkedField",name:"category",plural:!1,selections:[l,e],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"AutoScalingRuleEditorModalPresetsQuery",selections:a,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"AutoScalingRuleEditorModalPresetsQuery",selections:a},params:{cacheID:"04d06fec5284e709aaee3606d8a4bb53",id:null,metadata:{},name:"AutoScalingRuleEditorModalPresetsQuery",operationKind:"query",text:`query AutoScalingRuleEditorModalPresetsQuery {
  prometheusQueryPresets {
    edges {
      node {
        id
        name
        description
        rank
        categoryId
        metricName
        queryTemplate
        timeWindow
        category @since(version: "26.4.3") {
          id
          name
        }
      }
    }
  }
}
`}}}();pt.hash="6582d4cf067148f5b39755e919c0f4f2";const Zl={KERNEL:["cpu_util","mem","net_rx","net_tx"],INFERENCE_FRAMEWORK:[]},bn=l=>l?l.minThreshold!=null&&l.maxThreshold!=null?"scale_in_out":l.maxThreshold!=null?"scale_out":"scale_in":"scale_out",si=l=>{"use memo";var kl;const e=Je.c(195),{autoScalingRule:a,formRef:i}=l,{t}=Ze(),{token:r}=yl.useToken(),p=Pn();let u;e[0]!==p?(u=p.supports("prometheus-auto-scaling-rule"),e[0]=p,e[1]=u):u=e[1];const o=u;let s,y;e[2]===Symbol.for("react.memo_cache_sentinel")?(s=pt,y={},e[2]=s,e[3]=y):(s=e[2],y=e[3]);const{prometheusQueryPresets:c}=je.useLazyLoadQuery(s,y);let k;e[4]!==(c==null?void 0:c.edges)?(k=Jt(Rl(c==null?void 0:c.edges,oi)),e[4]=c==null?void 0:c.edges,e[5]=k):k=e[5];const V=k;let M;e[6]!==a?(M=bn(a),e[6]=a,e[7]=M):M=e[7];const[f,g]=N.useState(M),[K,j]=N.useState((a==null?void 0:a.metricSource)||"KERNEL");let _;e[8]!==a||e[9]!==V?(_=a!=null&&a.prometheusQueryPresetId?(kl=V.find(Te=>$e(Te.id)===a.prometheusQueryPresetId))==null?void 0:kl.id:void 0,e[8]=a,e[9]=V,e[10]=_):_=e[10];const[q,C]=N.useState(_);let $;e[11]!==(a==null?void 0:a.metricSource)?($=Zl[(a==null?void 0:a.metricSource)||"KERNEL"]||[],e[11]=a==null?void 0:a.metricSource,e[12]=$):$=e[12];const[Q,D]=N.useState($);let I;if(e[13]!==V||e[14]!==q){let Te;e[16]!==q?(Te=Ae=>Ae.id===q,e[16]=q,e[17]=Te):Te=e[17],I=V.find(Te),e[13]=V,e[14]=q,e[15]=I}else I=e[15];const x=I;let S;if(e[18]!==V){const Te=Ia(V,["rank"],["asc"]),Ae=Te.filter(ui),Xe=Te.filter(di),fe=ci,tl=Zt(Ae,mi),hl=Object.entries(tl).map(_e=>{const[Fl,Il]=_e;return{label:Fl,options:Il.map(fe)}});S=Xe.length>0?[...hl,...Xe.map(fe)]:hl,e[18]=V,e[19]=S}else S=e[19];const R=S;let b;e[20]!==a||e[21]!==q?(b=()=>{if(a){const Te=bn(a);let Ae;return Te==="scale_in"&&a.minThreshold!=null?Ae=Number(a.minThreshold):Te==="scale_out"&&a.maxThreshold!=null&&(Ae=Number(a.maxThreshold)),{metricSource:a.metricSource,metricName:a.metricName,prometheusQueryPresetId:q,conditionMode:Te,threshold:Ae,minThreshold:a.minThreshold!=null?Number(a.minThreshold):void 0,maxThreshold:a.maxThreshold!=null?Number(a.maxThreshold):void 0,stepSize:Math.abs(a.stepSize),timeWindow:a.timeWindow,minReplicas:a.minReplicas??void 0,maxReplicas:a.maxReplicas??void 0}}return{metricSource:"KERNEL",conditionMode:"scale_out",stepSize:1,timeWindow:300,minReplicas:0,maxReplicas:5}},e[20]=a,e[21]=q,e[22]=b):b=e[22];const d=b,v=K==="PROMETHEUS";let h;e[23]!==d?(h=d(),e[23]=d,e[24]=h):h=e[24];let B;e[25]!==t?(B=t("autoScalingRule.MetricSource"),e[25]=t,e[26]=B):B=e[26];let G;e[27]!==t?(G=t("autoScalingRule.MetricSourceTooltip"),e[27]=t,e[28]=G):G=e[28];let z;e[29]===Symbol.for("react.memo_cache_sentinel")?(z=[{required:!0}],e[29]=z):z=e[29];let W;e[30]!==i?(W=Te=>{var Ae,Xe;if(j(Te),(Ae=i.current)==null||Ae.setFieldsValue({metricName:void 0}),Te!=="PROMETHEUS")D(Zl[Te]||[]),C(void 0);else{const fe=(Xe=i.current)==null?void 0:Xe.getFieldValue("prometheusQueryPresetId");fe&&C(fe)}},e[30]=i,e[31]=W):W=e[31];let H;e[32]!==t?(H=t("autoScalingRule.MetricSourceKernel"),e[32]=t,e[33]=H):H=e[33];let J;e[34]!==H?(J={label:H,value:"KERNEL"},e[34]=H,e[35]=J):J=e[35];let se;e[36]!==o||e[37]!==t?(se=o?[]:[{label:t("autoScalingRule.MetricSourceInferenceFramework"),value:"INFERENCE_FRAMEWORK"}],e[36]=o,e[37]=t,e[38]=se):se=e[38];let T;e[39]!==t?(T=t("autoScalingRule.MetricSourcePrometheus"),e[39]=t,e[40]=T):T=e[40];let F;e[41]!==T?(F={label:T,value:"PROMETHEUS"},e[41]=T,e[42]=F):F=e[42];let A;e[43]!==J||e[44]!==se||e[45]!==F?(A=[J,...se,F],e[43]=J,e[44]=se,e[45]=F,e[46]=A):A=e[46];let P;e[47]!==W||e[48]!==A?(P=n.jsx(wl,{onChange:W,options:A}),e[47]=W,e[48]=A,e[49]=P):P=e[49];let U;e[50]!==B||e[51]!==G||e[52]!==P?(U=n.jsx(ue.Item,{label:B,name:"metricSource",tooltip:G,rules:z,children:P}),e[50]=B,e[51]=G,e[52]=P,e[53]=U):U=e[53];let Y;e[54]!==t?(Y=t("autoScalingRule.MetricName"),e[54]=t,e[55]=Y):Y=e[55];let ne;e[56]!==t?(ne=t("autoScalingRule.MetricNameTooltip"),e[56]=t,e[57]=ne):ne=e[57];const Z=!v;let te;e[58]!==Z?(te=[{required:Z}],e[58]=Z,e[59]=te):te=e[59];let re;e[60]!==t?(re=t("autoScalingRule.MetricName"),e[60]=t,e[61]=re):re=e[61];let ee;e[62]!==Q?(ee=Rl(Q,gi),e[62]=Q,e[63]=ee):ee=e[63];let O;e[64]!==i?(O={onSearch:Te=>{var Xe;const Ae=((Xe=i.current)==null?void 0:Xe.getFieldValue("metricSource"))||"KERNEL";D(la(Zl[Ae]||[],fe=>fe.includes(Te)))}},e[64]=i,e[65]=O):O=e[65];let Se;e[66]!==re||e[67]!==ee||e[68]!==O?(Se=n.jsx(na,{placeholder:re,options:ee,showSearch:O,allowClear:!0,popupMatchSelectWidth:!1}),e[66]=re,e[67]=ee,e[68]=O,e[69]=Se):Se=e[69];let pe;e[70]!==v||e[71]!==Y||e[72]!==ne||e[73]!==te||e[74]!==Se?(pe=n.jsx(ue.Item,{label:Y,name:"metricName",hidden:v,tooltip:ne,rules:te,children:Se}),e[70]=v,e[71]=Y,e[72]=ne,e[73]=te,e[74]=Se,e[75]=pe):pe=e[75];let me;e[76]!==i||e[77]!==v||e[78]!==V||e[79]!==R||e[80]!==x||e[81]!==t||e[82]!==r.fontSizeSM?(me=v&&n.jsx(n.Fragment,{children:n.jsx(ue.Item,{label:`${t("autoScalingRule.MetricName")} (${t("autoScalingRule.PrometheusPreset")})`,name:"prometheusQueryPresetId",tooltip:t("autoScalingRule.PrometheusPresetTooltip"),rules:[{required:!0,message:t("autoScalingRule.PrometheusPresetRequired")}],extra:x?n.jsx(Da,{queryTemplate:x.queryTemplate},x.id):void 0,children:n.jsx(wl,{onChange:Te=>{var Xe,fe;C(Te);const Ae=V.find(tl=>tl.id===Te);if(Ae){(Xe=i.current)==null||Xe.setFieldsValue({metricName:Ae.metricName});const tl=Ae.timeWindow!=null?Number(Ae.timeWindow):void 0;tl!=null&&!isNaN(tl)&&((fe=i.current)==null||fe.setFieldsValue({timeWindow:tl}))}},placeholder:t("autoScalingRule.SelectPrometheusPreset"),showSearch:{filterOption:pi},options:R,optionRender:Te=>n.jsxs(ae,{direction:"column",align:"start",children:[Te.label,Te.data.description&&n.jsx(Oe.Text,{type:"secondary",style:{fontSize:r.fontSizeSM},ellipsis:!0,children:Te.data.description})]}),allowClear:!0,onClear:()=>C(void 0)})})}),e[76]=i,e[77]=v,e[78]=V,e[79]=R,e[80]=x,e[81]=t,e[82]=r.fontSizeSM,e[83]=me):me=e[83];let ke;e[84]!==t?(ke=t("autoScalingRule.Condition"),e[84]=t,e[85]=ke):ke=e[85];let ve;e[86]!==t?(ve=t("autoScalingRule.ConditionTooltip"),e[86]=t,e[87]=ve):ve=e[87];let ye;e[88]===Symbol.for("react.memo_cache_sentinel")?(ye=Te=>{g(Te.target.value)},e[88]=ye):ye=e[88];let Fe;e[89]!==r.marginSM?(Fe={marginBottom:r.marginSM},e[89]=r.marginSM,e[90]=Fe):Fe=e[90];let Re;e[91]!==t?(Re=t("autoScalingRule.ScaleIn"),e[91]=t,e[92]=Re):Re=e[92];let be;e[93]!==Re?(be={label:Re,value:"scale_in"},e[93]=Re,e[94]=be):be=e[94];let Me;e[95]!==t?(Me=t("autoScalingRule.ScaleOut"),e[95]=t,e[96]=Me):Me=e[96];let m;e[97]!==Me?(m={label:Me,value:"scale_out"},e[97]=Me,e[98]=m):m=e[98];let L;e[99]!==t?(L=t("autoScalingRule.ScaleInAndOut"),e[99]=t,e[100]=L):L=e[100];let w;e[101]!==L?(w={label:L,value:"scale_in_out"},e[101]=L,e[102]=w):w=e[102];let E;e[103]!==be||e[104]!==m||e[105]!==w?(E=[be,m,w],e[103]=be,e[104]=m,e[105]=w,e[106]=E):E=e[106];let X;e[107]!==Fe||e[108]!==E?(X=n.jsx(ue.Item,{name:"conditionMode",noStyle:!0,children:n.jsx(ea.Group,{optionType:"button",onChange:ye,style:Fe,options:E})}),e[107]=Fe,e[108]=E,e[109]=X):X=e[109];let le;e[110]!==f||e[111]!==t?(le=f==="scale_in"&&n.jsxs(ae,{align:"center",gap:"xs",children:[n.jsxs(Oe.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(ue.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(ul,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),e[110]=f,e[111]=t,e[112]=le):le=e[112];let he;e[113]!==f||e[114]!==t?(he=f==="scale_out"&&n.jsxs(ae,{align:"center",gap:"xs",children:[n.jsx(ue.Item,{name:"threshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.ThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(ul,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(Oe.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]}),e[113]=f,e[114]=t,e[115]=he):he=e[115];let de;e[116]!==f||e[117]!==t?(de=f==="scale_in_out"&&n.jsxs(ae,{direction:"column",gap:"xs",align:"stretch",children:[n.jsxs(ae,{align:"center",gap:"xs",children:[n.jsxs(Oe.Text,{style:{flexShrink:0},children:[t("autoScalingRule.Metric")," ","<"]}),n.jsx(ue.Item,{name:"minThreshold",noStyle:!0,rules:[{required:!0,message:t("autoScalingRule.MinThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")}],children:n.jsx(ul,{placeholder:t("autoScalingRule.MinThreshold"),style:{flex:1,width:"100%"},min:0})})]}),n.jsxs(ae,{align:"center",gap:"xs",children:[n.jsx(ue.Item,{name:"maxThreshold",noStyle:!0,dependencies:["minThreshold"],rules:[{required:!0,message:t("autoScalingRule.MaxThresholdRequired")},{type:"number",min:0,message:t("autoScalingRule.ThresholdMustBeNonNegative")},Te=>{const{getFieldValue:Ae}=Te;return{validator(Xe,fe){const tl=Ae("minThreshold");return tl!=null&&fe!=null&&tl>=fe?Promise.reject(new Error(t("autoScalingRule.MinMustBeLessThanMax"))):Promise.resolve()}}}],children:n.jsx(ul,{placeholder:t("autoScalingRule.MaxThreshold"),style:{flex:1,width:"100%"},min:0})}),n.jsxs(Oe.Text,{style:{flexShrink:0},children:["<"," ",t("autoScalingRule.Metric")]})]})]}),e[116]=f,e[117]=t,e[118]=de):de=e[118];let ie;e[119]!==ke||e[120]!==ve||e[121]!==X||e[122]!==le||e[123]!==he||e[124]!==de?(ie=n.jsxs(ue.Item,{label:ke,required:!0,tooltip:ve,children:[X,le,he,de]}),e[119]=ke,e[120]=ve,e[121]=X,e[122]=le,e[123]=he,e[124]=de,e[125]=ie):ie=e[125];let ge;e[126]!==t?(ge=t("autoScalingRule.StepSize"),e[126]=t,e[127]=ge):ge=e[127];let Ie;e[128]!==t?(Ie=t("autoScalingRule.StepSizeTooltip"),e[128]=t,e[129]=Ie):Ie=e[129];let oe,xe;e[130]===Symbol.for("react.memo_cache_sentinel")?(oe={required:!0},xe={type:"number",min:1,max:Ml},e[130]=oe,e[131]=xe):(oe=e[130],xe=e[131]);let Ke;e[132]!==t?(Ke=[oe,xe,{validator:(Te,Ae)=>Ae%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[132]=t,e[133]=Ke):Ke=e[133];let we;e[134]===Symbol.for("react.memo_cache_sentinel")?(we={width:"100%"},e[134]=we):we=e[134];const qe=f==="scale_in_out"?"±":f==="scale_out"?"+":"−";let Pe;e[135]!==qe?(Pe=n.jsx(ul,{min:1,step:1,style:we,prefix:n.jsx(Oe.Text,{type:"secondary",children:qe})}),e[135]=qe,e[136]=Pe):Pe=e[136];let Ne;e[137]!==ge||e[138]!==Ie||e[139]!==Ke||e[140]!==Pe?(Ne=n.jsx(ue.Item,{label:ge,name:"stepSize",tooltip:Ie,rules:Ke,children:Pe}),e[137]=ge,e[138]=Ie,e[139]=Ke,e[140]=Pe,e[141]=Ne):Ne=e[141];let De;e[142]!==t?(De=t("autoScalingRule.CoolDownSeconds"),e[142]=t,e[143]=De):De=e[143];let ce;e[144]!==t?(ce=t("autoScalingRule.CoolDownTooltip"),e[144]=t,e[145]=ce):ce=e[145];let Ce,Le;e[146]===Symbol.for("react.memo_cache_sentinel")?(Ce={required:!0},Le={type:"number",min:1},e[146]=Ce,e[147]=Le):(Ce=e[146],Le=e[147]);let Ee;e[148]!==t?(Ee=[Ce,Le,{validator:(Te,Ae)=>Ae%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[148]=t,e[149]=Ee):Ee=e[149];let Qe;e[150]===Symbol.for("react.memo_cache_sentinel")?(Qe={width:"100%"},e[150]=Qe):Qe=e[150];let Be;e[151]!==t?(Be=t("autoScalingRule.Seconds"),e[151]=t,e[152]=Be):Be=e[152];let ze;e[153]!==Be?(ze=n.jsx(ul,{min:1,step:1,style:Qe,suffix:n.jsx(Oe.Text,{type:"secondary",children:Be})}),e[153]=Be,e[154]=ze):ze=e[154];let We;e[155]!==De||e[156]!==ce||e[157]!==Ee||e[158]!==ze?(We=n.jsx(ue.Item,{label:De,name:"timeWindow",tooltip:ce,rules:Ee,children:ze}),e[155]=De,e[156]=ce,e[157]=Ee,e[158]=ze,e[159]=We):We=e[159];let He;e[160]!==t?(He=t("autoScalingRule.MinReplicas"),e[160]=t,e[161]=He):He=e[161];let Ve;e[162]!==t?(Ve=t("autoScalingRule.MinReplicasTooltip"),e[162]=t,e[163]=Ve):Ve=e[163];let Ue;e[164]===Symbol.for("react.memo_cache_sentinel")?(Ue={min:0,max:Ml,type:"number"},e[164]=Ue):Ue=e[164];let Ge;e[165]!==t?(Ge=[Ue,{validator:(Te,Ae)=>Ae!=null&&Ae%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[165]=t,e[166]=Ge):Ge=e[166];let al;e[167]===Symbol.for("react.memo_cache_sentinel")?(al=n.jsx(ul,{min:0,max:Ml,style:{width:"100%"}}),e[167]=al):al=e[167];let el;e[168]!==He||e[169]!==Ve||e[170]!==Ge?(el=n.jsx(ue.Item,{label:He,name:"minReplicas",tooltip:Ve,rules:Ge,children:al}),e[168]=He,e[169]=Ve,e[170]=Ge,e[171]=el):el=e[171];let ll;e[172]!==t?(ll=t("autoScalingRule.MaxReplicas"),e[172]=t,e[173]=ll):ll=e[173];let nl;e[174]!==t?(nl=t("autoScalingRule.MaxReplicasTooltip"),e[174]=t,e[175]=nl):nl=e[175];let il;e[176]===Symbol.for("react.memo_cache_sentinel")?(il={min:0,max:Ml,type:"number"},e[176]=il):il=e[176];let sl;e[177]!==t?(sl=[il,{validator:(Te,Ae)=>Ae!=null&&Ae%1!==0?Promise.reject(new Error(t("error.OnlyPositiveIntegersAreAllowed"))):Promise.resolve()}],e[177]=t,e[178]=sl):sl=e[178];let rl;e[179]===Symbol.for("react.memo_cache_sentinel")?(rl=n.jsx(ul,{min:0,max:Ml,style:{width:"100%"}}),e[179]=rl):rl=e[179];let ol;e[180]!==ll||e[181]!==nl||e[182]!==sl?(ol=n.jsx(ue.Item,{label:ll,name:"maxReplicas",tooltip:nl,rules:sl,children:rl}),e[180]=ll,e[181]=nl,e[182]=sl,e[183]=ol):ol=e[183];let gl;return e[184]!==i||e[185]!==h||e[186]!==U||e[187]!==pe||e[188]!==me||e[189]!==ie||e[190]!==Ne||e[191]!==We||e[192]!==el||e[193]!==ol?(gl=n.jsxs(ue,{ref:i,layout:"vertical",initialValues:h,children:[U,pe,me,ie,Ne,We,el,ol]}),e[184]=i,e[185]=h,e[186]=U,e[187]=pe,e[188]=me,e[189]=ie,e[190]=Ne,e[191]=We,e[192]=el,e[193]=ol,e[194]=gl):gl=e[194],gl},ri=l=>{"use memo";const e=Je.c(34);let a,i,t,r,p;e[0]!==l?({onRequestClose:p,onComplete:r,modelDeploymentId:t,autoScalingRuleFrgmt:a,...i}=l,e[0]=l,e[1]=a,e[2]=i,e[3]=t,e[4]=r,e[5]=p):(a=e[1],i=e[2],t=e[3],r=e[4],p=e[5]);const{t:u}=Ze(),{message:o}=bl.useApp(),{logger:s}=Kl();let y;e[6]===Symbol.for("react.memo_cache_sentinel")?(y=gt,e[6]=y):y=e[6];const c=je.useFragment(y,a??null),k=N.useRef(null);let V;e[7]===Symbol.for("react.memo_cache_sentinel")?(V=mt,e[7]=V):V=e[7];const[M,f]=je.useMutation(V);let g;e[8]===Symbol.for("react.memo_cache_sentinel")?(g=ct,e[8]=g):g=e[8];const[K,j]=je.useMutation(g);let _;e[9]!==c||e[10]!==M||e[11]!==K||e[12]!==s||e[13]!==o||e[14]!==t||e[15]!==r||e[16]!==p||e[17]!==u?(_=()=>{var b;return(b=k.current)==null?void 0:b.validateFields().then(d=>{let v=null,h=null;d.conditionMode==="scale_in_out"?(v=d.minThreshold??null,h=d.maxThreshold??null):d.conditionMode==="scale_in"?v=d.threshold??null:h=d.threshold??null;const B=d.metricName,G=d.metricSource==="PROMETHEUS"&&d.prometheusQueryPresetId?$e(d.prometheusQueryPresetId):null;c?K({variables:{input:{id:$e(c.id),metricSource:d.metricSource,metricName:B,minThreshold:v!=null?String(v):null,maxThreshold:h!=null?String(h):null,stepSize:d.stepSize,timeWindow:d.timeWindow,minReplicas:d.minReplicas,maxReplicas:d.maxReplicas,prometheusQueryPresetId:G??void 0}},onCompleted:(z,W)=>{if(W&&W.length>0){const H=Rl(W,yi);for(const J of H)o.error(J);return}o.success(u("autoScalingRule.SuccessfullyUpdated")),r==null||r(),p(!0)},onError:z=>{o.error(z.message)}}):M({variables:{input:{modelDeploymentId:t,metricSource:d.metricSource,metricName:B,minThreshold:v!=null?String(v):null,maxThreshold:h!=null?String(h):null,stepSize:d.stepSize,timeWindow:d.timeWindow,minReplicas:d.minReplicas,maxReplicas:d.maxReplicas,prometheusQueryPresetId:G??void 0}},onCompleted:(z,W)=>{if(W&&W.length>0){const H=Rl(W,fi);for(const J of H)o.error(J);return}o.success(u("autoScalingRule.SuccessfullyCreated")),r==null||r(),p(!0)},onError:z=>{o.error(z.message)}})}).catch(d=>{s.error(d)})},e[9]=c,e[10]=M,e[11]=K,e[12]=s,e[13]=o,e[14]=t,e[15]=r,e[16]=p,e[17]=u,e[18]=_):_=e[18];const q=_;let C;e[19]!==p?(C=()=>{p(!1)},e[19]=p,e[20]=C):C=e[20];const $=C;let Q;e[21]!==c||e[22]!==u?(Q=u(c?"autoScalingRule.EditAutoScalingRule":"autoScalingRule.AddAutoScalingRule"),e[21]=c,e[22]=u,e[23]=Q):Q=e[23];const D=f||j;let I;e[24]===Symbol.for("react.memo_cache_sentinel")?(I=n.jsx(pl,{active:!0,paragraph:{rows:6}}),e[24]=I):I=e[24];const x=c??null;let S;e[25]!==x?(S=n.jsx(Vn,{children:n.jsx(Yt.Suspense,{fallback:I,children:n.jsx(si,{autoScalingRule:x,formRef:k})})}),e[25]=x,e[26]=S):S=e[26];let R;return e[27]!==i||e[28]!==$||e[29]!==q||e[30]!==S||e[31]!==Q||e[32]!==D?(R=n.jsx(Ul,{...i,onOk:q,onCancel:$,centered:!0,title:Q,confirmLoading:D,children:S}),e[27]=i,e[28]=$,e[29]=q,e[30]=S,e[31]=Q,e[32]=D,e[33]=R):R=e[33],R};function oi(l){return l==null?void 0:l.node}function ui(l){var e;return(e=l.category)==null?void 0:e.name}function di(l){var e;return!((e=l.category)!=null&&e.name)}function ci(l){return{label:l.name,value:l.id,description:l.description}}function mi(l){return l.category.name}function gi(l){return{label:l,value:l}}function pi(l,e){return String((e==null?void 0:e.label)??"").toLowerCase().includes(l.toLowerCase())}function yi(l){return l.message}function fi(l){return l.message}const ki=(l,e,a)=>{const i=l.metricSource==="PROMETHEUS"&&l.prometheusQueryPresetId?(a==null?void 0:a.get(l.prometheusQueryPresetId))??l.metricName:l.metricName,t=l.minThreshold,r=l.maxThreshold;return t!=null&&r!=null?n.jsxs(ae,{direction:"column",gap:"xxs",children:[n.jsxs(ae,{gap:"xs",children:[n.jsx(_l,{children:i})," < ",t]}),n.jsxs(ae,{gap:"xs",children:[r," < ",n.jsx(_l,{children:i})]})]}):r!=null?n.jsxs(ae,{gap:"xs",children:[r,n.jsx(dl,{title:e("autoScalingRule.MaxThreshold"),children:"<"}),n.jsx(_l,{children:i})]}):t!=null?n.jsxs(ae,{gap:"xs",children:[n.jsx(_l,{children:i}),n.jsx(dl,{title:e("autoScalingRule.MinThreshold"),children:"<"}),t]}):"-"},$l=l=>{const e={};return l.createdAt&&(e.createdAt=l.createdAt),l.lastTriggeredAt&&(e.lastTriggeredAt=l.lastTriggeredAt),Array.isArray(l.AND)&&(e.AND=l.AND.map($l)),Array.isArray(l.OR)&&(e.OR=l.OR.map($l)),Array.isArray(l.NOT)&&(e.NOT=l.NOT.map($l)),e},hi=l=>{"use memo";const e=Je.c(103);let a,i,t,r,p,u,o;e[0]!==l?({autoScalingRulesFrgmt:a,presetMap:u,isEndpointDestroying:i,isOwnedByCurrentUser:t,onEditRule:p,onDeleteRule:r,...o}=l,e[0]=l,e[1]=a,e[2]=i,e[3]=t,e[4]=r,e[5]=p,e[6]=u,e[7]=o):(a=e[1],i=e[2],t=e[3],r=e[4],p=e[5],u=e[6],o=e[7]);const{t:s}=Ze();let y;e[8]===Symbol.for("react.memo_cache_sentinel")?(y=dt,e[8]=y):y=e[8];const c=je.useFragment(y,a);let k;e[9]!==c?(k=Hl(c),e[9]=c,e[10]=k):k=e[10];const V=k;let M;e[11]===Symbol.for("react.memo_cache_sentinel")?(M={x:"max-content"},e[11]=M):M=e[11];let f;e[12]!==s?(f=s("autoScalingRule.MetricSource"),e[12]=s,e[13]=f):f=e[13];let g;e[14]!==s?(g=s("autoScalingRule.MetricSourceTooltip"),e[14]=s,e[15]=g):g=e[15];let K;e[16]!==g?(K=n.jsx(cl,{title:g}),e[16]=g,e[17]=K):K=e[17];let j;e[18]!==f||e[19]!==K?(j={key:"metricSource",title:n.jsxs(ae,{gap:"xxs",align:"center",children:[f,K]}),dataIndex:"metricSource",fixed:"left"},e[18]=f,e[19]=K,e[20]=j):j=e[20];let _;e[21]!==s?(_=s("autoScalingRule.Condition"),e[21]=s,e[22]=_):_=e[22];let q;e[23]!==s?(q=s("autoScalingRule.ConditionTooltip"),e[23]=s,e[24]=q):q=e[24];let C;e[25]!==q?(C=n.jsx(cl,{title:q}),e[25]=q,e[26]=C):C=e[26];let $;e[27]!==C||e[28]!==_?($=n.jsxs(ae,{gap:"xxs",align:"center",children:[_,C]}),e[27]=C,e[28]=_,e[29]=$):$=e[29];let Q;e[30]!==i||e[31]!==t||e[32]!==r||e[33]!==p||e[34]!==u||e[35]!==s?(Q=(ee,O)=>O?n.jsx(rn,{title:ki(O,s,u),showActions:"always",actions:[{key:"edit",title:s("button.Edit"),icon:n.jsx(ia,{}),disabled:i||!t,onClick:()=>p(O.id)},{key:"delete",title:s("button.Delete"),icon:n.jsx(on,{}),type:"danger",disabled:i||!t,onClick:()=>r(O.id,O.metricName??"")}]}):"-",e[30]=i,e[31]=t,e[32]=r,e[33]=p,e[34]=u,e[35]=s,e[36]=Q):Q=e[36];let D;e[37]!==$||e[38]!==Q?(D={key:"condition",title:$,fixed:"left",render:Q},e[37]=$,e[38]=Q,e[39]=D):D=e[39];let I;e[40]!==s?(I=s("autoScalingRule.CoolDownSeconds"),e[40]=s,e[41]=I):I=e[41];let x;e[42]!==s?(x=s("autoScalingRule.CoolDownTooltip"),e[42]=s,e[43]=x):x=e[43];let S;e[44]!==x?(S=n.jsx(cl,{title:x}),e[44]=x,e[45]=S):S=e[45];let R;e[46]!==I||e[47]!==S?(R=n.jsxs(ae,{gap:"xxs",align:"center",children:[I,S]}),e[46]=I,e[47]=S,e[48]=R):R=e[48];let b;e[49]!==s?(b=ee=>ee!=null?s("autoScalingRule.CoolDownSecondsValue",{value:ee}):"-",e[49]=s,e[50]=b):b=e[50];let d;e[51]!==R||e[52]!==b?(d={key:"timeWindow",title:R,dataIndex:"timeWindow",render:b},e[51]=R,e[52]=b,e[53]=d):d=e[53];let v;e[54]!==s?(v=s("autoScalingRule.StepSize"),e[54]=s,e[55]=v):v=e[55];let h;e[56]!==s?(h=s("autoScalingRule.StepSizeTooltip"),e[56]=s,e[57]=h):h=e[57];let B;e[58]!==h?(B=n.jsx(cl,{title:h}),e[58]=h,e[59]=B):B=e[59];let G;e[60]!==v||e[61]!==B?(G={key:"stepSize",title:n.jsxs(ae,{gap:"xxs",align:"center",children:[v,B]}),dataIndex:"stepSize",render:vi},e[60]=v,e[61]=B,e[62]=G):G=e[62];let z;e[63]!==s?(z=s("autoScalingRule.MIN/MAXReplicas"),e[63]=s,e[64]=z):z=e[64];let W;e[65]!==s?(W=s("autoScalingRule.MinMaxReplicasTooltip"),e[65]=s,e[66]=W):W=e[66];let H;e[67]!==W?(H=n.jsx(cl,{title:W}),e[67]=W,e[68]=H):H=e[68];let J;e[69]!==z||e[70]!==H?(J=n.jsxs(ae,{gap:"xxs",align:"center",children:[z,H]}),e[69]=z,e[70]=H,e[71]=J):J=e[71];let se;e[72]!==s?(se=(ee,O)=>{if(!(O!=null&&O.stepSize))return"-";const Se=O.minThreshold!=null,pe=O.maxThreshold!=null;return Se&&pe?n.jsxs("span",{children:[s("autoScalingRule.MinReplicasValue",{value:O==null?void 0:O.minReplicas})," / ",s("autoScalingRule.MaxReplicasValue",{value:O==null?void 0:O.maxReplicas})]}):pe?n.jsx("span",{children:s("autoScalingRule.MaxReplicasValue",{value:O==null?void 0:O.maxReplicas})}):n.jsx("span",{children:s("autoScalingRule.MinReplicasValue",{value:O==null?void 0:O.minReplicas})})},e[72]=s,e[73]=se):se=e[73];let T;e[74]!==J||e[75]!==se?(T={key:"minMaxReplicas",title:J,render:se},e[74]=J,e[75]=se,e[76]=T):T=e[76];let F;e[77]!==s?(F=s("autoScalingRule.CreatedAt"),e[77]=s,e[78]=F):F=e[78];let A;e[79]===Symbol.for("react.memo_cache_sentinel")?(A=["descend","ascend"],e[79]=A):A=e[79];let P;e[80]!==F?(P={key:"createdAt",title:F,dataIndex:"createdAt",sorter:!0,sortDirections:A,render:Fi},e[80]=F,e[81]=P):P=e[81];let U;e[82]!==s?(U=s("autoScalingRule.LastTriggered"),e[82]=s,e[83]=U):U=e[83];let Y;e[84]!==s?(Y=s("autoScalingRule.LastTriggeredTooltip"),e[84]=s,e[85]=Y):Y=e[85];let ne;e[86]!==Y?(ne=n.jsx(cl,{title:Y}),e[86]=Y,e[87]=ne):ne=e[87];let Z;e[88]!==U||e[89]!==ne?(Z={key:"lastTriggeredAt",title:n.jsxs(ae,{gap:"xxs",align:"center",children:[U,ne]}),render:xi},e[88]=U,e[89]=ne,e[90]=Z):Z=e[90];let te;e[91]!==D||e[92]!==d||e[93]!==G||e[94]!==T||e[95]!==P||e[96]!==Z||e[97]!==j?(te=[j,D,d,G,T,P,Z],e[91]=D,e[92]=d,e[93]=G,e[94]=T,e[95]=P,e[96]=Z,e[97]=j,e[98]=te):te=e[98];let re;return e[99]!==V||e[100]!==te||e[101]!==o?(re=n.jsx(Gl,{scroll:M,rowKey:"id",columns:te,showSorterTooltip:!1,dataSource:V,...o}),e[99]=V,e[100]=te,e[101]=o,e[102]=re):re=e[102],re},Si=l=>{"use memo";var gl,kl,Te,Ae,Xe,fe,tl,hl;const e=Je.c(136),{deploymentId:a,isEndpointDestroying:i,isOwnedByCurrentUser:t,fetchKey:r,hideInlineAddButton:p,hideInlineRefreshButton:u,ref:o}=l,s=p===void 0?!1:p,y=u===void 0?!1:u,{t:c}=Ze(),{message:k}=bl.useApp(),[V,M]=N.useTransition(),[f,g]=Cl(),[K,j]=N.useState(null),[_,q]=N.useState(!1),[C,$]=N.useState(null);let Q,D;e[0]===Symbol.for("react.memo_cache_sentinel")?(Q=()=>({openAddModal:()=>{j(null),q(!0)}}),D=[],e[0]=Q,e[1]=D):(Q=e[0],D=e[1]),N.useImperativeHandle(o,Q,D);const[I,x]=Xl("table_column_overrides.AutoScalingRuleList");let S,R;e[2]===Symbol.for("react.memo_cache_sentinel")?(S={order:Ll(["createdAt","-createdAt"]).withDefault("-createdAt"),filter:ta(Ri)},R={history:"replace"},e[2]=S,e[3]=R):(S=e[2],R=e[3]);const[b,d]=dn(S,R),v=b.order,h=b.filter??void 0;let B;e[4]===Symbol.for("react.memo_cache_sentinel")?(B={current:1,pageSize:10},e[4]=B):B=e[4];const{baiPaginationOption:G,tablePaginationOption:z,setTablePaginationOption:W}=aa(B);let H;e[5]!==h?(H=h?$l(h):null,e[5]=h,e[6]=H):H=e[6];const J=H,se=v.startsWith("-")?"DESC":"ASC";let T;e[7]!==se?(T=[{field:"CREATED_AT",direction:se}],e[7]=se,e[8]=T):T=e[8];let F;e[9]!==G.limit||e[10]!==G.offset||e[11]!==a||e[12]!==J||e[13]!==T?(F={deploymentId:a,offset:G.offset,limit:G.limit,orderBy:T,filter:J},e[9]=G.limit,e[10]=G.offset,e[11]=a,e[12]=J,e[13]=T,e[14]=F):F=e[14];const A=F,P=N.useDeferredValue(A);let U;e[15]===Symbol.for("react.memo_cache_sentinel")?(U=ut,e[15]=U):U=e[15];const Y=r?`${r}_${f}`:f;let ne;e[16]!==Y?(ne={fetchPolicy:"store-and-network",fetchKey:Y},e[16]=Y,e[17]=ne):ne=e[17];const Z=je.useLazyLoadQuery(U,P,ne);let te,re;e[18]===Symbol.for("react.memo_cache_sentinel")?(te=ot,re={},e[18]=te,e[19]=re):(te=e[18],re=e[19]);const{prometheusQueryPresets:ee}=je.useLazyLoadQuery(te,re);let O;if(e[20]!==ee){if(O=new Map,ee!=null&&ee.edges)for(const _e of ee.edges)_e!=null&&_e.node&&O.set($e(_e.node.id),_e.node.name);e[20]=ee,e[21]=O}else O=e[21];const Se=O;let pe;e[22]!==((kl=(gl=Z==null?void 0:Z.deployment)==null?void 0:gl.autoScalingRules)==null?void 0:kl.edges)?(pe=Hl(Rl((Ae=(Te=Z==null?void 0:Z.deployment)==null?void 0:Te.autoScalingRules)==null?void 0:Ae.edges,"node")),e[22]=(fe=(Xe=Z==null?void 0:Z.deployment)==null?void 0:Xe.autoScalingRules)==null?void 0:fe.edges,e[23]=pe):pe=e[23];const me=pe,ke=((hl=(tl=Z==null?void 0:Z.deployment)==null?void 0:tl.autoScalingRules)==null?void 0:hl.count)??0;let ve;e[24]===Symbol.for("react.memo_cache_sentinel")?(ve=rt,e[24]=ve):ve=e[24];const ye=Cn(ve);let Fe;e[25]!==g?(Fe=()=>{M(()=>{g()})},e[25]=g,e[26]=Fe):Fe=e[26];const Re=Fe;let be;e[27]===Symbol.for("react.memo_cache_sentinel")?(be=(_e,Fl)=>{$({id:_e,metricName:Fl})},e[27]=be):be=e[27];const Me=be;let m;e[28]===Symbol.for("react.memo_cache_sentinel")?(m={flex:1},e[28]=m):m=e[28];let L;e[29]!==c?(L=c("autoScalingRule.CreatedAt"),e[29]=c,e[30]=L):L=e[30];let w;e[31]===Symbol.for("react.memo_cache_sentinel")?(w=["after","before"],e[31]=w):w=e[31];let E;e[32]!==L?(E={key:"createdAt",propertyLabel:L,type:"datetime",operators:w,defaultOperator:"after"},e[32]=L,e[33]=E):E=e[33];let X;e[34]!==c?(X=c("autoScalingRule.LastTriggered"),e[34]=c,e[35]=X):X=e[35];let le;e[36]===Symbol.for("react.memo_cache_sentinel")?(le=["after","before"],e[36]=le):le=e[36];let he;e[37]!==X?(he={key:"lastTriggeredAt",propertyLabel:X,type:"datetime",operators:le,defaultOperator:"after"},e[37]=X,e[38]=he):he=e[38];let de;e[39]!==E||e[40]!==he?(de=[E,he],e[39]=E,e[40]=he,e[41]=de):de=e[41];let ie;e[42]!==d||e[43]!==W?(ie=_e=>{M(()=>{d({filter:_e??null}),W({current:1})})},e[42]=d,e[43]=W,e[44]=ie):ie=e[44];let ge;e[45]!==h||e[46]!==de||e[47]!==ie?(ge=n.jsx(gn,{style:m,filterProperties:de,value:h,onChange:ie}),e[45]=h,e[46]=de,e[47]=ie,e[48]=ge):ge=e[48];let Ie;e[49]!==y||e[50]!==V||e[51]!==g?(Ie=!y&&n.jsx(Dl,{loading:V,value:"",onChange:()=>{M(()=>g())}}),e[49]=y,e[50]=V,e[51]=g,e[52]=Ie):Ie=e[52];let oe;e[53]!==s||e[54]!==i||e[55]!==t||e[56]!==c?(oe=!s&&n.jsx(Ye,{type:"primary",icon:n.jsx(Vl,{}),disabled:i||!t,onClick:()=>{j(null),q(!0)},children:c("modelService.AddRules")}),e[53]=s,e[54]=i,e[55]=t,e[56]=c,e[57]=oe):oe=e[57];let xe;e[58]!==ge||e[59]!==Ie||e[60]!==oe?(xe=n.jsxs(ae,{align:"center",gap:"sm",children:[ge,Ie,oe]}),e[58]=ge,e[59]=Ie,e[60]=oe,e[61]=xe):xe=e[61];const Ke=V||P!==A;let we;e[62]!==I||e[63]!==x?(we={columnOverrides:I,onColumnOverridesChange:x},e[62]=I,e[63]=x,e[64]=we):we=e[64];let qe;e[65]!==d?(qe=_e=>{M(()=>{d({order:_e||null})})},e[65]=d,e[66]=qe):qe=e[66];let Pe;e[67]!==W?(Pe=(_e,Fl)=>{W({current:_e,pageSize:Fl})},e[67]=W,e[68]=Pe):Pe=e[68];let Ne;e[69]!==Pe||e[70]!==z.current||e[71]!==z.pageSize||e[72]!==ke?(Ne={pageSize:z.pageSize,current:z.current,total:ke,onChange:Pe},e[69]=Pe,e[70]=z.current,e[71]=z.pageSize,e[72]=ke,e[73]=Ne):Ne=e[73];let De;e[74]===Symbol.for("react.memo_cache_sentinel")?(De=_e=>{j(_e),q(!0)},e[74]=De):De=e[74];let ce;e[75]!==me||e[76]!==i||e[77]!==t||e[78]!==v||e[79]!==Se||e[80]!==Ke||e[81]!==we||e[82]!==qe||e[83]!==Ne?(ce=n.jsx(hi,{autoScalingRulesFrgmt:me,presetMap:Se,order:v,loading:Ke,tableSettings:we,onChangeOrder:qe,pagination:Ne,isEndpointDestroying:i,isOwnedByCurrentUser:t,onEditRule:De,onDeleteRule:Me}),e[75]=me,e[76]=i,e[77]=t,e[78]=v,e[79]=Se,e[80]=Ke,e[81]=we,e[82]=qe,e[83]=Ne,e[84]=ce):ce=e[84];let Ce;e[85]!==xe||e[86]!==ce?(Ce=n.jsxs(ae,{direction:"column",align:"stretch",gap:"sm",children:[xe,ce]}),e[85]=xe,e[86]=ce,e[87]=Ce):Ce=e[87];let Le;e[88]!==a?(Le=$e(a),e[88]=a,e[89]=Le):Le=e[89];let Ee;e[90]!==me||e[91]!==K?(Ee=K?me.find(_e=>_e.id===K)??null:null,e[90]=me,e[91]=K,e[92]=Ee):Ee=e[92];let Qe;e[93]!==Re?(Qe=_e=>{q(!1),_e&&Re()},e[93]=Re,e[94]=Qe):Qe=e[94];let Be;e[95]===Symbol.for("react.memo_cache_sentinel")?(Be=()=>{j(null)},e[95]=Be):Be=e[95];let ze;e[96]!==_||e[97]!==Le||e[98]!==Ee||e[99]!==Qe?(ze=n.jsx(vl,{children:n.jsx(ri,{open:_,modelDeploymentId:Le,autoScalingRuleFrgmt:Ee,onRequestClose:Qe,afterClose:Be})}),e[96]=_,e[97]=Le,e[98]=Ee,e[99]=Qe,e[100]=ze):ze=e[100];const We=!!C,He=(C==null?void 0:C.metricName)??"";let Ve;e[101]!==c||e[102]!==He?(Ve=c("dialog.title.DeleteSomething",{name:He}),e[101]=c,e[102]=He,e[103]=Ve):Ve=e[103];let Ue;e[104]!==c?(Ue=c("webui.menu.AutoScalingRule"),e[104]=c,e[105]=Ue):Ue=e[105];let Ge;e[106]!==C?(Ge=C?[{key:C.id,label:C.metricName}]:[],e[106]=C,e[107]=Ge):Ge=e[107];let al;e[108]!==c?(al=c("credential.PermanentlyDelete"),e[108]=c,e[109]=al):al=e[109];let el;e[110]!==c?(el=c("credential.TypePermanentlyDelete",{text:c("credential.PermanentlyDelete")}),e[110]=c,e[111]=el):el=e[111];let ll;e[112]!==c?(ll=c("credential.PermanentlyDelete"),e[112]=c,e[113]=ll):ll=e[113];let nl;e[114]!==ll?(nl={placeholder:ll},e[114]=ll,e[115]=nl):nl=e[115];let il;e[116]!==ye||e[117]!==C||e[118]!==Re||e[119]!==k||e[120]!==c?(il=()=>{if(C)return ye({input:{id:$e(C.id)}}).then(()=>{$(null),Re(),k.success({key:"autoscaling-rule-deleted",content:c("autoScalingRule.SuccessfullyDeleted")})}).catch(_e=>{const Fl=Array.isArray(_e)?_e:[_e];for(const Il of Fl)k.error((Il==null?void 0:Il.message)||c("dialog.ErrorOccurred"))})},e[116]=ye,e[117]=C,e[118]=Re,e[119]=k,e[120]=c,e[121]=il):il=e[121];let sl;e[122]===Symbol.for("react.memo_cache_sentinel")?(sl=()=>$(null),e[122]=sl):sl=e[122];let rl;e[123]!==We||e[124]!==Ve||e[125]!==Ue||e[126]!==Ge||e[127]!==al||e[128]!==el||e[129]!==nl||e[130]!==il?(rl=n.jsx(un,{open:We,title:Ve,target:Ue,items:Ge,confirmText:al,requireConfirmInput:!0,inputLabel:el,inputProps:nl,onOk:il,onCancel:sl}),e[123]=We,e[124]=Ve,e[125]=Ue,e[126]=Ge,e[127]=al,e[128]=el,e[129]=nl,e[130]=il,e[131]=rl):rl=e[131];let ol;return e[132]!==Ce||e[133]!==ze||e[134]!==rl?(ol=n.jsxs(n.Fragment,{children:[Ce,ze,rl]}),e[132]=Ce,e[133]=ze,e[134]=rl,e[135]=ol):ol=e[135],ol};function vi(l,e){if(!(e!=null&&e.stepSize))return"-";const a=e.minThreshold!=null,i=e.maxThreshold!=null;if(!a&&!i)return"-";const t=a&&i?"±":i?"+":"−";return n.jsxs(ae,{gap:"xs",children:[n.jsx(Oe.Text,{children:t}),n.jsx(Oe.Text,{children:Math.abs(e.stepSize)})]})}function Fi(l,e){return n.jsx("span",{children:e!=null&&e.createdAt?ml(e.createdAt).format("ll LT"):"-"})}function xi(l,e){return n.jsx("span",{children:e!=null&&e.lastTriggeredAt?ml.utc(e.lastTriggeredAt).tz().format("ll LTS"):"-"})}function Ri(l){return l}const bi=l=>{"use memo";var H,J,se;const e=Je.c(37),{deploymentFrgmt:a}=l,{t:i}=Ze(),{token:t}=yl.useToken(),[r]=Nn(),p=N.useRef(null),[u,o]=N.useTransition(),[s,y]=N.useState(0);let c;e[0]===Symbol.for("react.memo_cache_sentinel")?(c=st,e[0]=c):c=e[0];const k=je.useFragment(c,a);if(!(k!=null&&k.id))return null;const V=(H=k.metadata)==null?void 0:H.status,M=V==="STOPPING"||V==="STOPPED",f=((se=(J=k.creator)==null?void 0:J.basicInfo)==null?void 0:se.email)??null,g=!f||f===r.email,K=M||!g;let j;e[1]===Symbol.for("react.memo_cache_sentinel")?(j=()=>{o(()=>{y(Ti)})},e[1]=j):j=e[1];const _=j;let q;e[2]!==i?(q=i("deployment.tab.AutoScaling"),e[2]=i,e[3]=q):q=e[3];let C;e[4]!==i?(C=i("deployment.tab.description.AutoScaling"),e[4]=i,e[5]=C):C=e[5];let $;e[6]!==t.colorTextDescription?($=n.jsx(sn,{style:{color:t.colorTextDescription}}),e[6]=t.colorTextDescription,e[7]=$):$=e[7];let Q;e[8]!==C||e[9]!==$?(Q=n.jsx(dl,{title:C,children:$}),e[8]=C,e[9]=$,e[10]=Q):Q=e[10];let D;e[11]!==q||e[12]!==Q?(D=n.jsxs(ae,{gap:"xs",align:"center",children:[q,Q]}),e[11]=q,e[12]=Q,e[13]=D):D=e[13];let I;e[14]!==u?(I=n.jsx(Dl,{loading:u,value:"",onChange:_}),e[14]=u,e[15]=I):I=e[15];let x;e[16]===Symbol.for("react.memo_cache_sentinel")?(x=n.jsx(Vl,{}),e[16]=x):x=e[16];let S;e[17]===Symbol.for("react.memo_cache_sentinel")?(S=()=>{var T;return(T=p.current)==null?void 0:T.openAddModal()},e[17]=S):S=e[17];let R;e[18]!==i?(R=i("modelService.AddRules"),e[18]=i,e[19]=R):R=e[19];let b;e[20]!==K||e[21]!==R?(b=n.jsx(Ye,{type:"primary",icon:x,disabled:K,onClick:S,children:R}),e[20]=K,e[21]=R,e[22]=b):b=e[22];let d;e[23]!==b||e[24]!==I?(d=n.jsxs(ae,{gap:"xs",align:"center",children:[I,b]}),e[23]=b,e[24]=I,e[25]=d):d=e[25];let v;e[26]===Symbol.for("react.memo_cache_sentinel")?(v={body:{paddingTop:0}},e[26]=v):v=e[26];let h;e[27]===Symbol.for("react.memo_cache_sentinel")?(h=n.jsx(pl,{active:!0}),e[27]=h):h=e[27];const B=k.id,G=String(s);let z;e[28]!==k.id||e[29]!==M||e[30]!==g||e[31]!==G?(z=n.jsx(N.Suspense,{fallback:h,children:n.jsx(Si,{ref:p,deploymentId:B,isEndpointDestroying:M,isOwnedByCurrentUser:g,fetchKey:G,hideInlineAddButton:!0,hideInlineRefreshButton:!0})}),e[28]=k.id,e[29]=M,e[30]=g,e[31]=G,e[32]=z):z=e[32];let W;return e[33]!==d||e[34]!==z||e[35]!==D?(W=n.jsx(jl,{title:D,extra:d,styles:v,children:z}),e[33]=d,e[34]=z,e[35]=D,e[36]=W):W=e[36],W};function Ti(l){return l+1}const yt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentConfigurationSectionDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentConfigurationSectionDeleteMutation",selections:e},params:{cacheID:"ccb2e618fc149ec819f2dbee3d35c7a1",id:null,metadata:{},name:"DeploymentConfigurationSectionDeleteMutation",operationKind:"mutation",text:`mutation DeploymentConfigurationSectionDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}}();yt.hash="739b8de15b5a7bdec89ece3d8628621f";const ft=function(){var l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},e={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},a=[l,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}];return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentConfigurationSection_deployment",selections:[l,{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[e,{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[e],storageKey:null}],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentTagChips_metadata"}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:a,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:a,storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionHistoryTab_deployment"}],type:"ModelDeployment",abstractKey:null}}();ft.hash="9534b13462a6b065fa91132d54556187";const kt=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{kind:"Variable",name:"input",variableName:"input"}],a={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},r=[a,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],p={alias:null,args:null,kind:"ScalarField",name:"previousRevisionId",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"activatedRevisionId",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},c=[a,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[o,a],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[o,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[s,y,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[a,o],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfoGQL",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[s,y,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[a,o,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[a,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[o,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,i,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:r,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:r,storageKey:null}],storageKey:null},p,u],storageKey:null}],type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentRevisionHistoryTabActivateMutation",selections:[{alias:null,args:e,concreteType:"ActivateRevisionPayload",kind:"LinkedField",name:"activateDeploymentRevision",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[a,i,t,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:c,storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"deployingRevision",plural:!1,selections:c,storageKey:null}],storageKey:null},p,u],storageKey:null}]},params:{cacheID:"1e2043765f963e9901ab3bbfb74a581d",id:null,metadata:{},name:"DeploymentRevisionHistoryTabActivateMutation",operationKind:"mutation",text:`mutation DeploymentRevisionHistoryTabActivateMutation(
  $input: ActivateRevisionInput!
) {
  activateDeploymentRevision(input: $input) {
    deployment {
      id
      currentRevisionId
      deployingRevisionId
      currentRevision @since(version: "26.4.3") {
        id
        ...DeploymentRevisionDetail_revision
      }
      deployingRevision @since(version: "26.4.3") {
        id
        ...DeploymentRevisionDetail_revision
      }
    }
    previousRevisionId
    activatedRevisionId
  }
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots @since(version: "26.4.2") {
    slotName
    quantity
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    environ {
      entries {
        name
        value
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    vfolder {
      id
      name
    }
  }
  extraMounts {
    vfolderId
    mountDestination
    mountPerm
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  imageV2 @since(version: "26.4.3") {
    id
    identity {
      canonicalName
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        port
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
        }
      }
    }
  }
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
}
`}}}();kt.hash="153c096cf78b28827d7a04ef0f1610d4";const ht=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},a={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},r=[{kind:"Variable",name:"id",variableName:"deploymentId"}],p={alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"deployingRevisionId",storageKey:null},o=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},V={alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},M={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},f={alias:null,args:null,concreteType:"ModelMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"version",storageKey:null}],storageKey:null},g={alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[y,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},j={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[y,M],storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null};return{fragment:{argumentDefinitions:[l,e,a,i,t],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:r,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[p,u,{alias:null,args:o,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[s,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[y,c,k,V,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[M],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[M,f],storageKey:null}],storageKey:null},g,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[K,j],storageKey:null},{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,a,i],kind:"Operation",name:"DeploymentRevisionHistoryTabListQuery",selections:[{alias:null,args:r,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[p,u,{alias:null,args:o,concreteType:"ModelRevisionConnection",kind:"LinkedField",name:"revisionHistory",plural:!1,selections:[s,{alias:null,args:null,concreteType:"ModelRevisionEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"node",plural:!1,selections:[y,c,k,V,{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[M,y],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[M,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[M,f,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},g,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[K,j,_,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfoGQL",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[K,_,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[y,M,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null},g],storageKey:null}],storageKey:null}],storageKey:null},y],storageKey:null}]},params:{cacheID:"8f9baffca07f51a11d591df89bdc6253",id:null,metadata:{},name:"DeploymentRevisionHistoryTabListQuery",operationKind:"query",text:`query DeploymentRevisionHistoryTabListQuery(
  $deploymentId: ID!
  $filter: ModelRevisionFilter
  $orderBy: [ModelRevisionOrderBy!]
  $limit: Int
  $offset: Int
) {
  deployment(id: $deploymentId) {
    currentRevisionId
    deployingRevisionId
    revisionHistory(filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
      count
      edges {
        node {
          id
          revisionNumber
          createdAt
          clusterConfig {
            mode
            size
          }
          modelRuntimeConfig {
            runtimeVariant {
              name
              id
            }
          }
          modelDefinition {
            models {
              name
              metadata {
                version
              }
            }
          }
          imageV2 {
            id
            identity {
              canonicalName
            }
          }
          modelMountConfig {
            vfolderId
            vfolder {
              id
              name
            }
          }
          ...DeploymentRevisionDetail_revision
        }
      }
    }
    id
  }
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots @since(version: "26.4.2") {
    slotName
    quantity
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    environ {
      entries {
        name
        value
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    vfolder {
      id
      name
    }
  }
  extraMounts {
    vfolderId
    mountDestination
    mountPerm
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  imageV2 @since(version: "26.4.3") {
    id
    identity {
      canonicalName
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        port
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
        }
      }
    }
  }
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
}
`}}}();ht.hash="61af55e11074ae04f4d7842a72a688db";const St={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentRevisionHistoryTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"ModelDeployment",abstractKey:null};St.hash="d24c62ecda7ccb05acbbc317a5e86bb3";const Tn=["revisionNumber","createdAt","clusterMode","runtimeVariantName"],Ki=[...Tn,...Tn.map(l=>`-${l}`)],Di=({deploymentFrgmt:l,deploymentId:e,isDeploymentDestroying:a=!1,fetchKey:i})=>{"use memo";const{t}=Ze(),{token:r}=yl.useToken(),{message:p}=bl.useApp(),{logger:u}=Kl(),[o,s]=N.useTransition(),[y,c]=N.useState(null),[k,V]=N.useState(null),[M,f]=Xl("table_column_overrides.DeploymentRevisionHistoryTab"),[g,K]=dn({current:Ql.withDefault(1),pageSize:Ql.withDefault(10),order:Ll(Ki),rvFilter:_n},{history:"replace",urlKeys:{current:"rCurrent",pageSize:"rPageSize",order:"rvOrder",rvFilter:"rvFilter"}}),j=je.useFragment(St,l),_=T=>{if(!T)return null;try{const F=JSON.parse(T);return F&&typeof F=="object"&&!Array.isArray(F)?F:null}catch{return null}},q=T=>!T||Object.keys(T).length===0?"":JSON.stringify(T),[C,$]=N.useState(()=>({filter:g.rvFilter?_(g.rvFilter):null,orderBy:Bl(g.order)??[{field:"REVISION_NUMBER",direction:"DESC"}],limit:g.pageSize,offset:g.current>1?(g.current-1)*g.pageSize:0})),[Q,D]=Cl(),I=`${i??""}${Q}`,x=(i===void 0||i===ln)&&Q===ln,{deployment:S}=je.useLazyLoadQuery(ht,{deploymentId:e,...C},{fetchKey:I,fetchPolicy:x?"store-and-network":"network-only"}),[R]=je.useMutation(kt),b=S==null?void 0:S.currentRevisionId,d=S==null?void 0:S.deployingRevisionId,v=S==null?void 0:S.revisionHistory,h=Hl(Rl(v==null?void 0:v.edges,"node")),B=T=>{s(()=>{$(F=>({...F,...T}))})},G=()=>{s(()=>D())},z=T=>new Promise(F=>{c(T.id),R({variables:{input:{deploymentId:$e(j.id),revisionId:$e(T.id)}},onCompleted:(A,P)=>{var U;if(c(null),P&&P.length>0){u.error(P[0]),p.error(((U=P[0])==null?void 0:U.message)||t("general.ErrorOccurred")),F(!1);return}p.success(t("deployment.ApplySuccess",{revisionNumber:T.revisionNumber})),G(),F(!0)},onError:A=>{c(null),u.error(A),p.error((A==null?void 0:A.message)||t("general.ErrorOccurred")),F(!1)}})}),W=[{title:n.jsxs(ae,{gap:"xxs",align:"center",children:[t("deployment.RevisionNumberWithID"),n.jsx(cl,{title:t("deployment.RevisionNumberTooltip")})]}),dataIndex:"revisionNumber",key:"revisionNumber",fixed:"left",sorter:!0,render:(T,F)=>{const A=$e(F.id),P=A===b,U=A===d,Y=P||U?t("deployment.ApplyDisabled"):void 0,ne=P||U||a||y===F.id;return n.jsx(rn,{title:n.jsxs(ae,{gap:"xs",align:"center",children:[n.jsx(Oe.Link,{onClick:()=>V({frgmt:F,status:P?"current":U?"deploying":"none"}),children:F.revisionNumber!=null?`#${F.revisionNumber}`:"-"}),n.jsxs(ae,{gap:0,align:"center",children:["(",n.jsx(Sl,{globalId:F.id}),")"]}),P?n.jsx(zl,{color:"success",children:t("deployment.Current")}):null,U&&!P?n.jsx(zl,{color:"warning",icon:n.jsx(cn,{spin:!0}),children:t("deployment.Applying")}):null]}),showActions:"always",actions:[{key:"deploy",title:t("deployment.Apply"),icon:n.jsx(vn,{}),disabled:ne,disabledReason:Y,popConfirm:{title:t("deployment.Apply"),description:`#${F.revisionNumber}`,okText:t("deployment.Apply"),cancelText:t("button.Cancel"),okButtonProps:{danger:!0},onConfirm:()=>{z(F)}}}]})}},{title:t("general.CreatedAt"),dataIndex:"createdAt",key:"createdAt",sorter:!0,render:T=>T?ml(T).format("lll"):"-"},{title:t("deployment.ModelVersion"),key:"modelVersion",defaultHidden:!0,render:(T,F)=>{var ne,Z,te;const A=(Z=(ne=F.modelDefinition)==null?void 0:ne.models)==null?void 0:Z[0];if(!A)return"-";const P=A.name??"-",U=(te=A.metadata)==null?void 0:te.version,Y=typeof U=="string"?U:U!=null?String(U):null;return Y?`${P} (${Y})`:P}},{title:t("deployment.RuntimeVariant"),key:"runtimeVariantName",dataIndex:"runtimeVariantName",sorter:!0,render:(T,F)=>{var A,P;return((P=(A=F.modelRuntimeConfig)==null?void 0:A.runtimeVariant)==null?void 0:P.name)??"-"}},{title:t("deployment.Image"),key:"image",defaultHidden:!0,render:(T,F)=>{var U,Y,ne;const A=(Y=(U=F.imageV2)==null?void 0:U.identity)==null?void 0:Y.canonicalName,P=(ne=F.imageV2)==null?void 0:ne.id;return!A&&!P?"-":n.jsxs(ae,{gap:"xs",align:"center",wrap:"wrap",children:[A?n.jsx(Wl,{copyable:!0,ellipsis:{tooltip:A},style:{maxWidth:180},children:A}):null,P?n.jsxs(ae,{gap:0,align:"center",children:["(",n.jsx(Sl,{globalId:P}),")"]}):null]})}},{title:t("deployment.ModelFolder"),key:"modelFolder",defaultHidden:!0,render:(T,F)=>{var U,Y;const A=(U=F.modelMountConfig)==null?void 0:U.vfolder,P=(Y=F.modelMountConfig)==null?void 0:Y.vfolderId;return!(A!=null&&A.name)&&!P?"-":n.jsxs(ae,{gap:"xs",align:"center",wrap:"wrap",children:[A!=null&&A.name?n.jsx(Oe.Text,{children:A.name}):null,A!=null&&A.id?n.jsxs(ae,{gap:0,align:"center",children:["(",n.jsx(Sl,{globalId:A.id}),")"]}):P?n.jsx(Oe.Text,{type:"secondary",children:P}):null]})}},{title:n.jsxs(ae,{gap:"xxs",align:"center",children:[t("deployment.ClusterMode"),n.jsx(cl,{title:t("deployment.ClusterModeTooltip")})]}),key:"clusterMode",dataIndex:"clusterMode",sorter:!0,render:(T,F)=>{var U,Y;const A=(U=F.clusterConfig)==null?void 0:U.mode,P=(Y=F.clusterConfig)==null?void 0:Y.size;return A==null&&P==null?"-":A==null?`${P}`:P==null?A:`${A} / ${P}`}}],H={message:t("general.InvalidUUID"),validate:T=>ra(T.toLowerCase())},J=[{key:"revisionNumber",propertyLabel:t("deployment.RevisionNumber"),type:"number"},{key:"createdAt",propertyLabel:t("general.CreatedAt"),type:"datetime",operators:["after","before"],defaultOperator:"after"},{key:"clusterMode",propertyLabel:t("deployment.ClusterMode"),type:"string"},{key:"imageId",propertyLabel:t("deployment.Image"),type:"uuid",fixedOperator:"equals",rule:H},{key:"modelVfolderId",propertyLabel:t("deployment.ModelFolder"),type:"uuid",fixedOperator:"equals",rule:H}],se=g.rvFilter?_(g.rvFilter)??void 0:void 0;return n.jsxs(n.Fragment,{children:[n.jsx(vl,{children:n.jsx(mn,{revisionFrgmt:k==null?void 0:k.frgmt,status:k==null?void 0:k.status,open:!!k,onClose:()=>V(null),extra:k?n.jsx(sa,{title:t("deployment.Apply"),description:`#${k.frgmt.revisionNumber}`,okText:t("deployment.Apply"),cancelText:t("button.Cancel"),okButtonProps:{danger:!0},onConfirm:async()=>{await z(k.frgmt)&&V(null)},children:n.jsx(Ye,{type:"primary",icon:n.jsx(vn,{}),disabled:k.status==="current"||k.status==="deploying"||a||!!y,children:t("deployment.Apply")})}):void 0})}),n.jsxs(ae,{justify:"between",align:"center",gap:"xs",style:{marginBottom:r.marginSM},wrap:"wrap",children:[n.jsx(gn,{filterProperties:J,value:se,onChange:T=>{const F=q(T),A=_(F||null);K({rvFilter:F||null,current:1}),B({filter:A,offset:0})}}),n.jsx(Dl,{loading:o,value:"",onChange:()=>G()})]}),n.jsx(Gl,{rowKey:"id",dataSource:h,columns:W,loading:o,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:M,onColumnOverridesChange:f},order:g.order??void 0,onChangeOrder:T=>{K({order:T}),B({orderBy:Bl(T)})},pagination:{pageSize:g.pageSize,current:g.current,total:(v==null?void 0:v.count)??0,showSizeChanger:!0,onChange:(T,F)=>{const A=T>1?(T-1)*F:0;K({current:T,pageSize:F}),B({limit:F,offset:A})}}})]})},fl=()=>n.jsx(Oe.Text,{type:"secondary",children:"-"}),Ii=l=>{"use memo";var s,y,c;const e=Je.c(19),{deployment:a}=l,{t:i}=Ze(),t=((y=(s=a==null?void 0:a.metadata.projectV2)==null?void 0:s.basicInfo)==null?void 0:y.name)??(a==null?void 0:a.metadata.projectId);let r;if(e[0]!==a||e[1]!==t||e[2]!==i){const k=i("deployment.Visibility"),V=a==null?void 0:a.networkAccess.openToPublic;let M;e[4]!==i?(M=i("deployment.Public"),e[4]=i,e[5]=M):M=e[5];let f;e[6]!==i?(f=i("deployment.Private"),e[6]=i,e[7]=f):f=e[7];let g;e[8]===Symbol.for("react.memo_cache_sentinel")?(g=fl(),e[8]=g):g=e[8];let K;e[9]!==V||e[10]!==M||e[11]!==f?(K=n.jsx(Ma,{value:V,trueLabel:M,falseLabel:f,fallback:g}),e[9]=V,e[10]=M,e[11]=f,e[12]=K):K=e[12];const j=i("deployment.Tags"),_=(a==null?void 0:a.metadata)??null;let q;e[13]===Symbol.for("react.memo_cache_sentinel")?(q=fl(),e[13]=q):q=e[13];let C;e[14]!==_?(C=n.jsx(ba,{metadataFrgmt:_,fallback:q}),e[14]=_,e[15]=C):C=e[15],r=On([{key:"name",label:i("deployment.Name"),children:a!=null&&a.metadata.name?n.jsx(Wl,{copyable:!0,children:a.metadata.name}):fl()},{key:"id",label:i("deployment.DeploymentId"),children:a!=null&&a.id?n.jsx(Sl,{globalId:a.id,copyable:!0,ellipsis:!1,style:{maxWidth:"none"}}):fl()},{key:"project",label:i("deployment.Project"),children:t||fl()},{key:"domain",label:i("deployment.Domain"),children:(a==null?void 0:a.metadata.domainName)||fl()},{key:"resource-group",label:i("modelStore.ResourceGroup"),children:(a==null?void 0:a.metadata.resourceGroupName)||fl()},{key:"endpoint-url",label:i("deployment.EndpointUrl"),children:a!=null&&a.networkAccess.endpointUrl?n.jsx(Oe.Text,{copyable:!0,children:a.networkAccess.endpointUrl}):fl()},{key:"visibility",label:k,children:K},{key:"desired-replicas",label:i("deployment.DesiredReplicas"),children:((c=a==null?void 0:a.replicaState)==null?void 0:c.desiredReplicaCount)??fl()},{key:"tags",label:j,children:C}]),e[0]=a,e[1]=t,e[2]=i,e[3]=r}else r=e[3];const p=r;let u;e[16]===Symbol.for("react.memo_cache_sentinel")?(u={xs:1,sm:1,md:2,lg:2,xl:2,xxl:2},e[16]=u):u=e[16];let o;return e[17]!==p?(o=n.jsx(ya,{bordered:!0,column:u,items:p}),e[17]=p,e[18]=o):o=e[18],o},Ai=l=>{"use memo";const e=Je.c(133),{deploymentFrgmt:a,isDeploymentDestroying:i,revisionFetchKey:t,isPendingRefetch:r,onRefetch:p,onAddRevision:u}=l,o=i===void 0?!1:i,{t:s}=Ze(),{token:y}=yl.useToken(),{message:c}=bl.useApp(),{logger:k}=Kl(),V=En(),M=oa();let f;e[0]===Symbol.for("react.memo_cache_sentinel")?(f=ft,e[0]=f):f=e[0];const g=je.useFragment(f,a),[K,j]=N.useState(null);let _;e[1]===Symbol.for("react.memo_cache_sentinel")?(_=Ll(["currentRevision","revisionHistory"]).withDefault("currentRevision"),e[1]=_):_=e[1];let q;e[2]===Symbol.for("react.memo_cache_sentinel")?(q={..._,history:"replace",scroll:!1},e[2]=q):q=e[2];const[C,$]=ua("revisionTab",q),[Q,D]=N.useState(!1),[I,x]=N.useState(!1);let S;e[3]===Symbol.for("react.memo_cache_sentinel")?(S=yt,e[3]=S):S=e[3];const[R,b]=je.useMutation(S),d=(g==null?void 0:g.metadata.name)??"",h=M.pathname.startsWith("/admin-deployments")?"/admin-deployments":"/deployments";let B;e[4]!==R||e[5]!==g||e[6]!==h||e[7]!==k||e[8]!==c||e[9]!==s||e[10]!==V?(B=()=>{g!=null&&g.id&&R({variables:{input:{id:$e(g.id)??g.id}},onCompleted:(Ve,Ue)=>{if(Ue&&Ue.length>0){k.error("Failed to delete deployment",Ue),c.error(s("deployment.FailedToDeleteDeployment"));return}c.success(s("deployment.DeploymentDeleted")),x(!1),V(h)},onError:Ve=>{k.error("Failed to delete deployment",Ve),c.error(s("deployment.FailedToDeleteDeployment"))}})},e[4]=R,e[5]=g,e[6]=h,e[7]=k,e[8]=c,e[9]=s,e[10]=V,e[11]=B):B=e[11];const G=B;let z;e[12]===Symbol.for("react.memo_cache_sentinel")?(z=(Ve,Ue,Ge)=>{j({revisionFrgmt:Ve,status:Ue,title:Ge})},e[12]=z):z=e[12];const W=z,H=g==null?void 0:g.currentRevision,J=g==null?void 0:g.deployingRevision,se=!!J&&J.id!==(H==null?void 0:H.id);da(p,se?5e3:null);let T;e[13]!==s?(T=s("deployment.BasicInformation"),e[13]=s,e[14]=T):T=e[14];let F;e[15]!==r||e[16]!==p?(F=n.jsx(Dl,{loading:r,value:"",onChange:p}),e[15]=r,e[16]=p,e[17]=F):F=e[17];let A;e[18]===Symbol.for("react.memo_cache_sentinel")?(A=n.jsx(ca,{}),e[18]=A):A=e[18];let P;e[19]===Symbol.for("react.memo_cache_sentinel")?(P=async()=>{D(!0)},e[19]=P):P=e[19];let U;e[20]!==s?(U=s("button.Edit"),e[20]=s,e[21]=U):U=e[21];let Y;e[22]!==o||e[23]!==U?(Y=n.jsx(ql,{icon:A,disabled:o,action:P,children:U}),e[22]=o,e[23]=U,e[24]=Y):Y=e[24];let ne;e[25]===Symbol.for("react.memo_cache_sentinel")?(ne=["click"],e[25]=ne):ne=e[25];let Z;e[26]!==s?(Z=s("deployment.DeleteDeployment"),e[26]=s,e[27]=Z):Z=e[27];let te;e[28]===Symbol.for("react.memo_cache_sentinel")?(te=n.jsx(on,{}),e[28]=te):te=e[28];const re=o||b;let ee;e[29]===Symbol.for("react.memo_cache_sentinel")?(ee=()=>x(!0),e[29]=ee):ee=e[29];let O;e[30]!==Z||e[31]!==re?(O={items:[{key:"delete",label:Z,icon:te,danger:!0,disabled:re,onClick:ee}]},e[30]=Z,e[31]=re,e[32]=O):O=e[32];let Se;e[33]===Symbol.for("react.memo_cache_sentinel")?(Se=n.jsx(ma,{}),e[33]=Se):Se=e[33];let pe;e[34]!==s?(pe=s("button.More"),e[34]=s,e[35]=pe):pe=e[35];let me;e[36]!==pe?(me=n.jsx(Ye,{icon:Se,"aria-label":pe}),e[36]=pe,e[37]=me):me=e[37];let ke;e[38]!==O||e[39]!==me?(ke=n.jsx(ga,{trigger:ne,menu:O,children:me}),e[38]=O,e[39]=me,e[40]=ke):ke=e[40];let ve;e[41]!==Y||e[42]!==ke?(ve=n.jsxs(Ol.Compact,{children:[Y,ke]}),e[41]=Y,e[42]=ke,e[43]=ve):ve=e[43];let ye;e[44]!==ve||e[45]!==F?(ye=n.jsxs(ae,{gap:"xs",align:"center",children:[F,ve]}),e[44]=ve,e[45]=F,e[46]=ye):ye=e[46];let Fe;e[47]===Symbol.for("react.memo_cache_sentinel")?(Fe={body:{paddingTop:0}},e[47]=Fe):Fe=e[47];let Re;e[48]!==g?(Re=n.jsx(Ii,{deployment:g}),e[48]=g,e[49]=Re):Re=e[49];let be;e[50]!==ye||e[51]!==Re||e[52]!==T?(be=n.jsx(jl,{title:T,extra:ye,styles:Fe,children:Re}),e[50]=ye,e[51]=Re,e[52]=T,e[53]=be):be=e[53];let Me;e[54]!==$?(Me=Ve=>{(Ve==="currentRevision"||Ve==="revisionHistory")&&$(Ve)},e[54]=$,e[55]=Me):Me=e[55];let m;e[56]!==s?(m=s("deployment.CurrentRevision"),e[56]=s,e[57]=m):m=e[57];let L;e[58]!==m?(L={key:"currentRevision",label:m},e[58]=m,e[59]=L):L=e[59];let w;e[60]!==s?(w=s("deployment.RevisionHistory"),e[60]=s,e[61]=w):w=e[61];let E;e[62]!==w?(E={key:"revisionHistory",label:w},e[62]=w,e[63]=E):E=e[63];let X;e[64]!==L||e[65]!==E?(X=[L,E],e[64]=L,e[65]=E,e[66]=X):X=e[66];let le;e[67]===Symbol.for("react.memo_cache_sentinel")?(le=n.jsx(Vl,{}),e[67]=le):le=e[67];let he;e[68]!==u?(he=async()=>{u()},e[68]=u,e[69]=he):he=e[69];let de;e[70]!==s?(de=s("deployment.AddRevision"),e[70]=s,e[71]=de):de=e[71];let ie;e[72]!==o||e[73]!==he||e[74]!==de?(ie=n.jsx(ae,{gap:"xs",align:"center",children:n.jsx(ql,{type:"primary",icon:le,disabled:o,action:he,children:de})}),e[72]=o,e[73]=he,e[74]=de,e[75]=ie):ie=e[75];let ge;e[76]!==C||e[77]!==H||e[78]!==J||e[79]!==se||e[80]!==s||e[81]!==y?(ge=C==="currentRevision"&&n.jsxs(n.Fragment,{children:[se&&n.jsx(xl,{type:"info",icon:n.jsx(cn,{spin:!0}),showIcon:!0,title:s("deployment.ApplyingRevision",{revisionNumber:J.revisionNumber!=null?`#${J.revisionNumber}`:$e(J.id)??""}),action:n.jsx(Ye,{onClick:()=>W(J,"deploying",s("deployment.ApplyingRevisionDetail")),children:s("deployment.ViewRevision")}),style:{marginBottom:y.marginMD}}),H?n.jsx(Ra,{revisionFrgmt:H,status:"current"}):se?null:n.jsx(Fn,{image:Fn.PRESENTED_IMAGE_SIMPLE,description:s("deployment.NoCurrentRevisionDeployed")})]}),e[76]=C,e[77]=H,e[78]=J,e[79]=se,e[80]=s,e[81]=y,e[82]=ge):ge=e[82];let Ie;e[83]!==C||e[84]!==g||e[85]!==o||e[86]!==t?(Ie=C==="revisionHistory"&&g&&n.jsx(Vn,{children:n.jsx(N.Suspense,{fallback:n.jsx(pl,{active:!0,paragraph:{rows:4}}),children:n.jsx(Di,{deploymentFrgmt:g,deploymentId:g.id,isDeploymentDestroying:o,fetchKey:t})})}),e[83]=C,e[84]=g,e[85]=o,e[86]=t,e[87]=Ie):Ie=e[87];let oe;e[88]!==C||e[89]!==Me||e[90]!==X||e[91]!==ie||e[92]!==ge||e[93]!==Ie?(oe=n.jsxs(jl,{activeTabKey:C,onTabChange:Me,tabList:X,tabBarExtraContent:ie,children:[ge,Ie]}),e[88]=C,e[89]=Me,e[90]=X,e[91]=ie,e[92]=ge,e[93]=Ie,e[94]=oe):oe=e[94];let xe;e[95]!==p?(xe=Ve=>{D(!1),Ve&&p()},e[95]=p,e[96]=xe):xe=e[96];let Ke;e[97]!==g||e[98]!==Q||e[99]!==xe?(Ke=n.jsx(pa,{open:Q,deploymentFrgmt:g,onRequestClose:xe}),e[97]=g,e[98]=Q,e[99]=xe,e[100]=Ke):Ke=e[100];const we=K==null?void 0:K.revisionFrgmt,qe=K==null?void 0:K.status,Pe=K==null?void 0:K.title,Ne=!!K;let De;e[101]===Symbol.for("react.memo_cache_sentinel")?(De=()=>j(null),e[101]=De):De=e[101];let ce;e[102]!==we||e[103]!==qe||e[104]!==Pe||e[105]!==Ne?(ce=n.jsx(vl,{children:n.jsx(mn,{revisionFrgmt:we,status:qe,title:Pe,open:Ne,onClose:De})}),e[102]=we,e[103]=qe,e[104]=Pe,e[105]=Ne,e[106]=ce):ce=e[106];let Ce;e[107]!==s?(Ce=s("deployment.DeleteDeployment"),e[107]=s,e[108]=Ce):Ce=e[108];let Le;e[109]!==s?(Le=s("deployment.Deployment"),e[109]=s,e[110]=Le):Le=e[110];let Ee;e[111]!==d?(Ee=d?[{key:d,label:d}]:[],e[111]=d,e[112]=Ee):Ee=e[112];let Qe;e[113]!==d?(Qe={placeholder:d},e[113]=d,e[114]=Qe):Qe=e[114];let Be;e[115]!==b?(Be={loading:b},e[115]=b,e[116]=Be):Be=e[116];let ze;e[117]===Symbol.for("react.memo_cache_sentinel")?(ze=()=>x(!1),e[117]=ze):ze=e[117];let We;e[118]!==d||e[119]!==G||e[120]!==I||e[121]!==Ce||e[122]!==Le||e[123]!==Ee||e[124]!==Qe||e[125]!==Be?(We=n.jsx(un,{open:I,title:Ce,target:Le,items:Ee,confirmText:d,requireConfirmInput:!0,inputProps:Qe,okButtonProps:Be,onOk:G,onCancel:ze}),e[118]=d,e[119]=G,e[120]=I,e[121]=Ce,e[122]=Le,e[123]=Ee,e[124]=Qe,e[125]=Be,e[126]=We):We=e[126];let He;return e[127]!==be||e[128]!==oe||e[129]!==Ke||e[130]!==ce||e[131]!==We?(He=n.jsxs(n.Fragment,{children:[be,oe,Ke,ce,We]}),e[127]=be,e[128]=oe,e[129]=Ke,e[130]=ce,e[131]=We,e[132]=He):He=e[132],He},vt=function(){var l={defaultValue:null,kind:"LocalArgument",name:"deploymentId"},e={defaultValue:null,kind:"LocalArgument",name:"filter"},a={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},t={defaultValue:null,kind:"LocalArgument",name:"orderBy"},r=[{kind:"Variable",name:"id",variableName:"deploymentId"}],p=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],u={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"sessionId",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"revisionId",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"trafficStatus",storageKey:null},V={alias:null,args:null,kind:"ScalarField",name:"healthStatus",storageKey:null},M={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},K={alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"sessionV2",plural:!1,selections:[o,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[g],storageKey:null}],storageKey:null},j={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null};return{fragment:{argumentDefinitions:[l,e,a,i,t],kind:"Fragment",metadata:null,name:"DeploymentReplicasTabListQuery",selections:[{alias:null,args:r,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:p,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[o,s,y,c,k,V,M,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[o,f,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null},K],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,e,t,a,i],kind:"Operation",name:"DeploymentReplicasTabListQuery",selections:[{alias:null,args:r,concreteType:"ModelDeployment",kind:"LinkedField",name:"deployment",plural:!1,selections:[{alias:null,args:p,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[u,{alias:null,args:null,concreteType:"ModelReplicaEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelReplica",kind:"LinkedField",name:"node",plural:!1,selections:[o,s,y,c,k,V,M,{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"revision",plural:!1,selections:[o,f,M,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[g,o],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[g,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[j,_,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[o,g],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfoGQL",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[j,_,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[o,g,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[g,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},K],storageKey:null}],storageKey:null}],storageKey:null},o],storageKey:null}]},params:{cacheID:"acc919974a8cb5cb0d212d2a1fb6ac0d",id:null,metadata:{},name:"DeploymentReplicasTabListQuery",operationKind:"query",text:`query DeploymentReplicasTabListQuery(
  $deploymentId: ID!
  $filter: ReplicaFilter
  $orderBy: [ReplicaOrderBy!]
  $limit: Int
  $offset: Int
) {
  deployment(id: $deploymentId) {
    replicas(filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
      count
      edges {
        node {
          id
          sessionId
          revisionId
          status
          trafficStatus
          healthStatus
          createdAt
          revision {
            id
            revisionNumber
            ...DeploymentRevisionDetail_revision
          }
          sessionV2 @since(version: "26.4.3") {
            id
            metadata {
              name
            }
          }
        }
      }
    }
    id
  }
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots @since(version: "26.4.2") {
    slotName
    quantity
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    environ {
      entries {
        name
        value
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    vfolder {
      id
      name
    }
  }
  extraMounts {
    vfolderId
    mountDestination
    mountPerm
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
    }
  }
  imageV2 @since(version: "26.4.3") {
    id
    identity {
      canonicalName
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        port
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
        }
      }
    }
  }
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
}
`}}}();vt.hash="26b1dbb98e07f4bdd28168cb4a306efd";const Ft={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"DeploymentReplicasTab_deployment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],type:"ModelDeployment",abstractKey:null};Ft.hash="6134739d7e3addb802e0658f5858bcea";const Mi={HEALTHY:"success",UNHEALTHY:"error",DEGRADED:"warning",NOT_CHECKED:"default",PROVISIONING:"info",WARMING_UP:"info",RUNNING:"success",TERMINATING:"warning",TERMINATED:"default",FAILED_TO_START:"error"},Ci={HEALTHY:"Healthy",UNHEALTHY:"Unhealthy",DEGRADED:"Degraded",NOT_CHECKED:"NotChecked",PROVISIONING:"Provisioning",WARMING_UP:"WarmingUp",RUNNING:"Running",TERMINATING:"Terminating",TERMINATED:"Terminated",FAILED_TO_START:"FailedToStart"},Kn=l=>{"use memo";const e=Je.c(23);let a,i,t;e[0]!==l?({status:a,showTooltip:i,...t}=l,e[0]=l,e[1]=a,e[2]=i,e[3]=t):(a=e[1],i=e[2],t=e[3]);const r=i===void 0?!0:i,{t:p}=Ze(),u=Mi[a],o=Ci[a],s=`replicaStatus.${o}`;let y;e[4]!==p||e[5]!==s?(y=p(s),e[4]=p,e[5]=s,e[6]=y):y=e[6];const c=y;let k;e[7]!==o||e[8]!==r||e[9]!==p?(k=r?p(`replicaStatus.tooltip.${o}`,{defaultValue:""}):void 0,e[7]=o,e[8]=r,e[9]=p,e[10]=k):k=e[10];const V=k;let M;e[11]!==a?(M=a==="WARMING_UP"?n.jsx(cn,{spin:!0}):void 0,e[11]=a,e[12]=M):M=e[12];const f=M;let g;e[13]!==u||e[14]!==f||e[15]!==c||e[16]!==t?(g=n.jsx(zl,{...t,color:u,icon:f,children:c}),e[13]=u,e[14]=f,e[15]=c,e[16]=t,e[17]=g):g=e[17];const K=g;if(!r||!V)return K;let j;e[18]!==K?(j=n.jsx("span",{children:K}),e[18]=K,e[19]=j):j=e[19];let _;return e[20]!==j||e[21]!==V?(_=n.jsx(dl,{title:V,children:j}),e[20]=j,e[21]=V,e[22]=_):_=e[22],_},Dn=["TERMINATED","FAILED_TO_START"],ji=l=>l==="terminated"?{status:{in:[...Dn]}}:{status:{notIn:[...Dn]}},en=(l,e)=>({...l,...ji(e)}),an=["createdAt","id"],Li=[...an,...an.map(l=>`-${l}`)],In=l=>ka(an,l),An=l=>l??"NOT_CHECKED",Vi=({deploymentFrgmt:l,deploymentId:e})=>{"use memo";var x,S,R,b;const{t:a}=Ze(),[i,t]=N.useTransition(),[r,p]=Xl("table_column_overrides.DeploymentReplicasTab"),[u,o]=dn({current:Ql.withDefault(1),pageSize:Ql.withDefault(10),order:Ll(Li),rFilter:_n,rStatusCategory:Ll(["running","terminated"]).withDefault("running")},{history:"replace",urlKeys:{current:"rCurrent",pageSize:"rPageSize",order:"rOrder",rFilter:"rFilter",rStatusCategory:"rStatusCategory"}});je.useFragment(Ft,l);const s=d=>{if(!d)return null;try{const v=JSON.parse(d);return v&&typeof v=="object"&&!Array.isArray(v)?v:null}catch{return null}},y=d=>!d||Object.keys(d).length===0?"":JSON.stringify(d),[c,k]=N.useState(()=>({filter:en(u.rFilter?s(u.rFilter):null,u.rStatusCategory),orderBy:Bl(u.order||"-createdAt"),limit:u.pageSize,offset:u.current>1?(u.current-1)*u.pageSize:0})),[V,M]=N.useState(0),[f,g]=N.useState(null),[K,j]=N.useState(null),{deployment:_}=je.useLazyLoadQuery(vt,{deploymentId:e,...c},{fetchKey:V,fetchPolicy:"network-only"}),q=((R=(S=(x=_==null?void 0:_.replicas)==null?void 0:x.edges)==null?void 0:S.map(d=>d==null?void 0:d.node))==null?void 0:R.filter(d=>!!d))??[],C=d=>{t(()=>{k(v=>({...v,...d}))})},$=[{label:a("replicaStatus.Active"),value:"ACTIVE"},{label:a("replicaStatus.Inactive"),value:"INACTIVE"}],Q=[{key:"trafficStatus",propertyLabel:a("deployment.TrafficStatus"),type:"enum",options:$,strictSelection:!0}],D=u.rFilter?s(u.rFilter)??void 0:void 0,I=On([{key:"id",title:a("deployment.ReplicaId"),dataIndex:"id",fixed:"left",sorter:In("id"),render:d=>n.jsx(Sl,{globalId:d,copyable:!0})},{key:"status",title:n.jsxs(ae,{gap:"xxs",align:"center",children:[a("general.Status"),n.jsx(cl,{title:a("deployment.ReplicaLifecycleStatusTooltip")})]}),dataIndex:"status",render:d=>n.jsx(Kn,{status:An(d)})},{key:"healthStatus",title:n.jsxs(ae,{gap:"xxs",align:"center",children:[a("deployment.HealthStatus"),n.jsx(cl,{title:a("deployment.HealthStatusTooltip")})]}),dataIndex:"healthStatus",render:d=>n.jsx(Kn,{status:An(d)})},{key:"trafficStatus",title:n.jsxs(ae,{gap:"xxs",align:"center",children:[a("deployment.TrafficStatus"),n.jsx(cl,{title:a("deployment.TrafficStatusTooltip")})]}),dataIndex:"trafficStatus",render:d=>n.jsx(zl,{color:d==="ACTIVE"?"success":"default",children:a(d==="ACTIVE"?"replicaStatus.Active":"replicaStatus.Inactive")})},{key:"session",title:a("general.Session"),onCell:()=>({style:{maxWidth:240}}),render:(d,v)=>{var G;const h=v.sessionV2;if(!(h!=null&&h.id))return n.jsx(Oe.Text,{type:"secondary",children:"—"});const B=(G=h.metadata)==null?void 0:G.name;return B?n.jsxs(n.Fragment,{children:[n.jsx(Oe.Link,{ellipsis:{tooltip:B},onClick:()=>g($e(h.id)),style:{maxWidth:160},children:B})," ",n.jsxs(Oe.Text,{type:"secondary",children:["(",n.jsx(Sl,{globalId:h.id,type:"secondary"}),")"]})]}):n.jsx(Sl,{globalId:h.id})}},{key:"revision",title:n.jsxs(ae,{gap:"xxs",align:"center",children:[a("deployment.RevisionNumberWithID"),n.jsx(cl,{title:a("deployment.RevisionNumberTooltip")})]}),render:(d,v)=>{const h=v.revision;return h!=null&&h.id?n.jsxs(n.Fragment,{children:[n.jsx(Oe.Link,{onClick:()=>j(h),children:h.revisionNumber!=null?`#${h.revisionNumber}`:"-"})," ",n.jsxs(Oe.Text,{type:"secondary",children:["(",n.jsx(Sl,{globalId:h.id,type:"secondary"}),")"]})]}):n.jsx(Oe.Text,{type:"secondary",children:"—"})}},{key:"createdAt",title:a("deployment.CreatedAt"),dataIndex:"createdAt",sorter:In("createdAt"),render:d=>d?ml(d).format("lll"):"-"}]);return n.jsxs(n.Fragment,{children:[n.jsxs(ae,{justify:"between",align:"center",gap:"xs",style:{marginBottom:12},children:[n.jsxs(ae,{gap:"sm",align:"start",wrap:"wrap",style:{flexShrink:1},children:[n.jsx(fa,{value:u.rStatusCategory,onChange:d=>{const v=d.target.value,h=u.rFilter?s(u.rFilter):null;o({rStatusCategory:v,current:1}),C({filter:en(h,v),offset:0})},options:[{label:a("deployment.Running"),value:"running"},{label:a("deployment.status.Terminated"),value:"terminated"}]}),n.jsx(gn,{filterProperties:Q,value:D,onChange:d=>{const v=y(d);o({rFilter:v||null,current:1}),C({filter:en(d??null,u.rStatusCategory),offset:0})}})]}),n.jsx(Dl,{loading:i,value:"",onChange:()=>{t(()=>M(d=>d+1))}})]}),n.jsx(Gl,{rowKey:d=>d.id,dataSource:q,columns:I,loading:i,size:"small",scroll:{x:"max-content"},tableSettings:{columnOverrides:r,onColumnOverridesChange:p},order:u.order,onChangeOrder:d=>{o({order:d??null}),C({orderBy:Bl(d||"-createdAt")})},pagination:{pageSize:u.pageSize,current:u.current,total:((b=_==null?void 0:_.replicas)==null?void 0:b.count)??0,onChange:(d,v)=>{o({current:d,pageSize:v});const h=d>1?(d-1)*v:0;C({limit:v,offset:h})}}}),n.jsx(vl,{children:n.jsx(Aa,{open:!!f,sessionId:f??void 0,onClose:()=>g(null)})}),n.jsx(vl,{children:n.jsx(mn,{open:!!K,revisionFrgmt:K,onClose:()=>j(null)})})]})},Gi=()=>{"use memo";var Me,m,L,w,E,X;const l=Je.c(89),{t:e}=Ze(),{token:a}=yl.useToken(),[i]=Nn(),t=En(),r=Pn();let p;l[0]!==((Me=r==null?void 0:r._config)==null?void 0:Me.blockList)?(p=(L=(m=r==null?void 0:r._config)==null?void 0:m.blockList)==null?void 0:L.includes("chat"),l[0]=(w=r==null?void 0:r._config)==null?void 0:w.blockList,l[1]=p):p=l[1];const u=!!p,{deploymentId:o}=ha(),s=o??"";let y;l[2]!==s?(y=El("ModelDeployment",s),l[2]=s,l[3]=y):y=l[3];const c=y,[k,V]=N.useTransition(),[M,f]=Cl(),[g,K]=Cl(),[j,_]=Sa(!1),{setLeft:q,setRight:C}=_;let $;l[4]===Symbol.for("react.memo_cache_sentinel")?($=Qn,l[4]=$):$=l[4];let Q;l[5]!==c?(Q={deploymentId:c},l[5]=c,l[6]=Q):Q=l[6];const D=M===ln?"store-and-network":"network-only";let I;l[7]!==M||l[8]!==D?(I={fetchKey:M,fetchPolicy:D},l[7]=M,l[8]=D,l[9]=I):I=l[9];const{deployment:x}=je.useLazyLoadQuery($,Q,I);if(!x){let le;return l[10]===Symbol.for("react.memo_cache_sentinel")?(le=n.jsx(pl,{active:!0}),l[10]=le):le=l[10],le}const S=x.metadata.name,R=x.metadata.status,b=R==="STOPPING"||R==="STOPPED"||R==="TERMINATED",d=R==="READY",v=!x.currentRevision&&!x.deployingRevision,h=x.networkAccess.openToPublic===!1&&!b,B=((X=(E=x.creator)==null?void 0:E.basicInfo)==null?void 0:X.email)??null,G=!B||B===i.email;let z;l[11]!==f?(z=()=>{V(()=>f())},l[11]=f,l[12]=z):z=l[12];const W=z;let H;l[13]!==q||l[14]!==f||l[15]!==K?(H=le=>{q(),le&&V(()=>{f(),K()})},l[13]=q,l[14]=f,l[15]=K,l[16]=H):H=l[16];const J=H,se=Pi;let T;l[17]===Symbol.for("react.memo_cache_sentinel")?(T={margin:0},l[17]=T):T=l[17];let F;l[18]!==S?(F=n.jsx(Oe.Title,{level:3,style:T,children:S}),l[18]=S,l[19]=F):F=l[19];let A;l[20]!==R?(A=n.jsx(Ta,{status:R}),l[20]=R,l[21]=A):A=l[21];let P;l[22]!==F||l[23]!==A?(P=n.jsxs(ae,{direction:"row",align:"center",gap:"sm",children:[F,A]}),l[22]=F,l[23]=A,l[24]=P):P=l[24];let U;l[25]!==s||l[26]!==v||l[27]!==u||l[28]!==d||l[29]!==e||l[30]!==a.fontSizeLG||l[31]!==t?(U=d&&!v&&n.jsx(xl,{type:"success",showIcon:!0,title:e("deployment.DeploymentReady"),action:!u&&n.jsx(Ye,{type:"primary",icon:n.jsx(va,{size:a.fontSizeLG}),onClick:()=>{t({pathname:"/chat",search:new URLSearchParams({endpointId:s}).toString()})},children:e("deployment.StartChatTest")})}),l[25]=s,l[26]=v,l[27]=u,l[28]=d,l[29]=e,l[30]=a.fontSizeLG,l[31]=t,l[32]=U):U=l[32];let Y;l[33]!==v||l[34]!==b||l[35]!==C||l[36]!==e?(Y=v&&n.jsx(xl,{type:"warning",showIcon:!0,title:e("deployment.NoCurrentRevisionDeployed"),action:n.jsx(ql,{type:"primary",icon:n.jsx(Vl,{}),action:async()=>{C()},disabled:b,children:e("deployment.AddRevision")})}),l[33]=v,l[34]=b,l[35]=C,l[36]=e,l[37]=Y):Y=l[37];let ne;l[38]!==h||l[39]!==e?(ne=h&&n.jsx(xl,{type:"info",showIcon:!0,title:e("deployment.PrivateDeploymentAlertTitle"),action:n.jsx(Ye,{onClick:se,children:e("deployment.ManageAccessTokens")})}),l[38]=h,l[39]=e,l[40]=ne):ne=l[40];let Z;l[41]!==x||l[42]!==W||l[43]!==b||l[44]!==k||l[45]!==C||l[46]!==g?(Z=n.jsx(Ai,{deploymentFrgmt:x,isDeploymentDestroying:b,revisionFetchKey:g,isPendingRefetch:k,onRefetch:W,onAddRevision:C}),l[41]=x,l[42]=W,l[43]=b,l[44]=k,l[45]=C,l[46]=g,l[47]=Z):Z=l[47];let te;l[48]!==e?(te=e("deployment.tab.Replicas"),l[48]=e,l[49]=te):te=l[49];let re;l[50]!==e?(re=e("deployment.tab.description.Replicas"),l[50]=e,l[51]=re):re=l[51];let ee;l[52]!==a.colorTextDescription?(ee=n.jsx(sn,{style:{color:a.colorTextDescription}}),l[52]=a.colorTextDescription,l[53]=ee):ee=l[53];let O;l[54]!==re||l[55]!==ee?(O=n.jsx(dl,{title:re,children:ee}),l[54]=re,l[55]=ee,l[56]=O):O=l[56];let Se;l[57]!==te||l[58]!==O?(Se=n.jsxs(ae,{gap:"xs",align:"center",children:[te,O]}),l[57]=te,l[58]=O,l[59]=Se):Se=l[59];let pe;l[60]===Symbol.for("react.memo_cache_sentinel")?(pe={body:{paddingTop:0}},l[60]=pe):pe=l[60];let me;l[61]===Symbol.for("react.memo_cache_sentinel")?(me=n.jsx(pl,{active:!0}),l[61]=me):me=l[61];let ke;l[62]!==x||l[63]!==c?(ke=n.jsx(Fa,{children:n.jsx(N.Suspense,{fallback:me,children:n.jsx(Vi,{deploymentFrgmt:x,deploymentId:c})})}),l[62]=x,l[63]=c,l[64]=ke):ke=l[64];let ve;l[65]!==Se||l[66]!==ke?(ve=n.jsx(jl,{title:Se,styles:pe,children:ke}),l[65]=Se,l[66]=ke,l[67]=ve):ve=l[67];let ye;l[68]!==x?(ye=n.jsx(bi,{deploymentFrgmt:x}),l[68]=x,l[69]=ye):ye=l[69];let Fe;l[70]!==x||l[71]!==c||l[72]!==b||l[73]!==G?(Fe=n.jsx("div",{id:"deployment-access-tokens",children:n.jsx(Ea,{deploymentFrgmt:x,deploymentId:c,isOwnedByCurrentUser:G,isDeploymentDestroying:b})}),l[70]=x,l[71]=c,l[72]=b,l[73]=G,l[74]=Fe):Fe=l[74];let Re;l[75]!==j||l[76]!==c||l[77]!==J?(Re=n.jsx(N.Suspense,{fallback:null,children:n.jsx(vl,{children:n.jsx(ii,{open:j,onRequestClose:J,deploymentId:c})})}),l[75]=j,l[76]=c,l[77]=J,l[78]=Re):Re=l[78];let be;return l[79]!==P||l[80]!==U||l[81]!==Y||l[82]!==ne||l[83]!==Z||l[84]!==ve||l[85]!==ye||l[86]!==Fe||l[87]!==Re?(be=n.jsxs(ae,{direction:"column",align:"stretch",gap:"md",children:[P,U,Y,ne,Z,ve,ye,Fe,Re]}),l[79]=P,l[80]=U,l[81]=Y,l[82]=ne,l[83]=Z,l[84]=ve,l[85]=ye,l[86]=Fe,l[87]=Re,l[88]=be):be=l[88],be};function Pi(){var l;(l=document.getElementById("deployment-access-tokens"))==null||l.scrollIntoView({behavior:"smooth",block:"start"})}export{Gi as default};
//# sourceMappingURL=DeploymentDetailPage-DQpxyyG-.js.map
