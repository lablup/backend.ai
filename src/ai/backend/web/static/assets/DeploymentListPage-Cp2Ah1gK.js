import{i as Cl,u as Al,bI as xl,e2 as Vl,j as a,at as jl,aV as Bl,l as M,c as Me,d as _l,W as El,x as wl,X as Ol,Y as ql,dd as Ul,bJ as $l,ce as vl,af as zl,ae as Ql,a7 as Gl,aM as Jl,z as Wl,V as Hl,aS as Yl,r as Dl,aT as Xl,ak as Zl,bk as en,dj as ln,b2 as nn,dJ as an,dh as tn,bL as sn,aJ as rn,aL as on,K as Il,a2 as hl,L as un,dk as dn,an as Tl,bR as cn}from"./index-4XAoWQdC.js";import{D as mn,a as gn}from"./DeploymentSettingModal-DKW6wAC4.js";import{B as yn,a as pn}from"./BAIModelDeploymentNodes-BTdMt6K7.js";import{i as fn,B as kn}from"./BAIDeploymentTagTokens-DaVJhxci.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-B13SaUe_.js";import"./BAIBooleanToken-D4JLjIi_.js";const Nl=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentListPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentListPageDeleteMutation",selections:e},params:{cacheID:"4639cd2572faeb586296319d8202e23a",id:null,metadata:{},name:"DeploymentListPageDeleteMutation",operationKind:"mutation",text:`mutation DeploymentListPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();Nl.hash="867cc2a31d2fc3342a0bafe7502c0483";const Ml=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},K={defaultValue:null,kind:"LocalArgument",name:"offset"},v={defaultValue:null,kind:"LocalArgument",name:"orderBy"},n=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},p={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,s,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},P={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},he=[s,m],D={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},Te=[D,m];return{fragment:{argumentDefinitions:[l,e,K,v],kind:"Fragment",metadata:null,name:"DeploymentListPageQuery",selections:[{alias:null,args:n,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[s,c],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,g,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,v,e,K],kind:"Operation",name:"DeploymentListPageQuery",selections:[{alias:null,args:n,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},s,c,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},y,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[s],storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[d],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,g,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[p,P,C,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"subpath",storageKey:null}],storageKey:null},y,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:he,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[s,t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:he,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},m,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[s,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[D],storageKey:null},t],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[P,C,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},p],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2TagEntry",kind:"LinkedField",name:"tags",plural:!0,selections:Te,storageKey:null},{alias:null,args:null,concreteType:"ImageV2LabelEntry",kind:"LinkedField",name:"labels",plural:!0,selections:Te,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[s,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"command",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:[{kind:"Literal",name:"limit",value:100}],concreteType:"EntityLabelConnection",kind:"LinkedField",name:"entityLabels",plural:!1,selections:[{alias:null,args:null,concreteType:"EntityLabelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"EntityLabel",kind:"LinkedField",name:"node",plural:!1,selections:[D,m,t,{alias:null,args:null,kind:"ScalarField",name:"fieldId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:"entityLabels(limit:100)"},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[t,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"f7b8bf22c4eb81873225274888e184ea",id:null,metadata:{},name:"DeploymentListPageQuery",operationKind:"query",text:`query DeploymentListPageQuery(
  $filter: DeploymentFilter
  $orderBy: [DeploymentOrderBy!]
  $limit: Int
  $offset: Int
) {
  myDeployments(filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        id
        ...BAIModelDeploymentNodesFragment
        ...DeploymentSettingModal_deployment
        metadata {
          name
          status
        }
        currentRevision {
          id
          revisionNumber
          ...DeploymentRevisionDetail_revision
        }
      }
    }
  }
}

fragment BAIDeploymentOwnerInfo_deployment on ModelDeployment {
  id
  creator {
    id
    basicInfo {
      email
      username
      fullName
    }
  }
}

fragment BAIDeploymentTagTokens_metadata on ModelDeploymentMetadata {
  tags
}

fragment BAIEntityLabelSettingModalFragment on EntityLabelConnection {
  edges {
    node {
      fieldId
      key
      value
      id
    }
  }
}

fragment BAIEntityLabelTokensFragment on EntityLabelConnection {
  edges {
    node {
      key
      value
      id
    }
  }
}

fragment BAIImageNodeSimpleTagV2Fragment on ImageV2 {
  identity {
    canonicalName
    architecture
  }
  metadata {
    tags {
      key
      value
    }
    labels {
      key
      value
    }
  }
}

fragment BAIModelDeploymentNodesFragment on ModelDeployment {
  id
  entityId
  currentRevisionId
  metadata {
    projectId
    domainName
    name
    status
    tags
    createdAt
    updatedAt
    resourceGroupName
    projectV2 {
      basicInfo {
        name
      }
      id
    }
    ...BAIDeploymentTagTokens_metadata
  }
  networkAccess {
    endpointUrl
    preferredDomainName
    openToPublic
  }
  defaultDeploymentStrategy {
    type
  }
  replicaState {
    desiredReplicaCount
  }
  runningReplicas: replicas(filter: {status: {equals: RUNNING}}) {
    count
  }
  currentRevision {
    id
    revisionNumber
    modelMountConfig {
      vfolder {
        id
        name
      }
    }
  }
  entityLabels(limit: 100) {
    ...BAIEntityLabelTokensFragment
    ...BAIEntityLabelSettingModalFragment
  }
  ...BAIDeploymentOwnerInfo_deployment
}

fragment DeploymentRevisionDetail_revision on ModelRevision {
  id
  revisionNumber
  createdAt
  clusterConfig {
    mode
    size
  }
  resourceSlots {
    slotName
    quantity
  }
  resourceConfig {
    resourceOpts {
      entries {
        name
        value
      }
    }
  }
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    inferenceRuntimeConfig
    environ {
      entries {
        name
        value
      }
    }
    runtimeVariantPresetValues {
      presetId
      value
      preset {
        name
        displayName
        targetSpec {
          key
        }
        id
      }
    }
  }
  modelMountConfig {
    vfolderId
    mountDestination
    definitionPath
    subpath
    vfolder {
      id
      name
      ...FolderLink_vfolderNode
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
  imageV2 {
    id
    identity {
      canonicalName
      architecture
    }
    ...BAIImageNodeSimpleTagV2Fragment
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        command @since(version: "26.7.0")
        startCommand
        shell
        port
        preStartActions {
          action
          args
        }
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
          expectedStatusCode
        }
      }
    }
  }
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

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
  ...VFolderNodeIdenticonFragment
}

fragment VFolderNodeIdenticonFragment on VirtualFolderNode {
  id
}
`}}})();Ml.hash="a93a788c3494e0e0d4407521956af7ce";const Fn=l=>{"use memo";var Fl,Sl,bl,Kl;const e=Cl.c(182),{isCreating:K,onCloseCreate:v}=l,{t:n}=Al(),{message:d}=El.useApp(),{logger:t}=wl(),s=Ol(),c=ql(),[g,y]=M.useState(null),[p,P]=M.useState(null),C=Ul("deployment"),[m,he]=M.useState(null),[D,Te]=M.useState(null);let Pe;e[0]===Symbol.for("react.memo_cache_sentinel")?(Pe={current:1,pageSize:10},e[0]=Pe):Pe=e[0];const{baiPaginationOption:R,tablePaginationOption:x,setTablePaginationOption:f}=$l(Pe);let Re,xe;e[1]===Symbol.for("react.memo_cache_sentinel")?(Re={filter:zl(Sn),order:vl(pn),statusCategory:vl(["running","finished"]).withDefault("running")},xe={history:"replace"},e[1]=Re,e[2]=xe):(Re=e[1],xe=e[2]);const[u,k]=Ql(Re,xe),[Xe,Ze]=Gl("table_column_overrides.DeploymentListPage"),[Ce,F]=Jl(),A=Wl();let Ve;e[3]!==A?(Ve=Hl(A),e[3]=A,e[4]=Ve):Ve=e[4];const je=Ve;let Be;e[5]!==u.order?(Be=Yl(u.order),e[5]=u.order,e[6]=Be):Be=e[6];const el=Be;let _e;e[7]===Symbol.for("react.memo_cache_sentinel")?(_e=["STOPPED"],e[7]=_e):_e=e[7];const pl=_e;let Ee;e[8]!==u.statusCategory?(Ee=u.statusCategory==="finished"?{status:{in:pl}}:{status:{notIn:pl}},e[8]=u.statusCategory,e[9]=Ee):Ee=e[9];const ll=Ee;let we;e[10]!==A.id?(we=A.id?{projectId:{equals:A.id}}:{},e[10]=A.id,e[11]=we):we=e[11];const nl=we;let V;e[12]!==u.filter?(V=u.filter??{},e[12]=u.filter,e[13]=V):V=e[13];let j;e[14]!==nl||e[15]!==ll||e[16]!==V?(j={...V,...ll,...nl},e[14]=nl,e[15]=ll,e[16]=V,e[17]=j):j=e[17];let Oe;e[18]!==R.limit||e[19]!==R.offset||e[20]!==el||e[21]!==j?(Oe={filter:j,orderBy:el,limit:R.limit,offset:R.offset},e[18]=R.limit,e[19]=R.offset,e[20]=el,e[21]=j,e[22]=Oe):Oe=e[22];const fl=Oe,kl=M.useDeferredValue(fl),Ae=M.useDeferredValue(Ce);let qe;e[23]===Symbol.for("react.memo_cache_sentinel")?(qe=Ml,e[23]=qe):qe=e[23];const al=Ae===en?"store-and-network":"network-only";let Ue;e[24]!==Ae||e[25]!==al?(Ue={fetchPolicy:al,fetchKey:Ae},e[24]=Ae,e[25]=al,e[26]=Ue):Ue=e[26];const{myDeployments:r}=Dl.useLazyLoadQuery(qe,kl,Ue);let S,I,$e,B;e[27]!==p||e[28]!==g||e[29]!==(r==null?void 0:r.count)||e[30]!==(r==null?void 0:r.edges)?(S=Xl(Zl(r==null?void 0:r.edges,"node")),B=(r==null?void 0:r.count)??0,I=g==null?null:S.find(i=>i.id===g)??null,$e=p==null?null:S.find(i=>i.id===p)??null,e[27]=p,e[28]=g,e[29]=r==null?void 0:r.count,e[30]=r==null?void 0:r.edges,e[31]=S,e[32]=I,e[33]=$e,e[34]=B):(S=e[31],I=e[32],$e=e[33],B=e[34]);const o=$e,_=kl!==fl||Ae!==Ce;let ze;e[35]===Symbol.for("react.memo_cache_sentinel")?(ze=Nl,e[35]=ze):ze=e[35];const[tl,il]=Dl.useMutation(ze);let E;e[36]!==n?(E=n("deployment.filter.Name"),e[36]=n,e[37]=E):E=e[37];let w;e[38]!==E?(w={key:"name",propertyLabel:E,type:"string"},e[38]=E,e[39]=w):w=e[39];let O;e[40]!==n?(O=n("deployment.filter.Tags"),e[40]=n,e[41]=O):O=e[41];let q;e[42]!==O?(q={key:"tags",propertyLabel:O,type:"string"},e[42]=O,e[43]=q):q=e[43];let U;e[44]!==n?(U=n("deployment.filter.EndpointUrl"),e[44]=n,e[45]=U):U=e[45];let $;e[46]!==U?($={key:"endpointUrl",propertyLabel:U,type:"string"},e[46]=U,e[47]=$):$=e[47];let z;e[48]!==n?(z=n("deployment.filter.OpenToPublic"),e[48]=n,e[49]=z):z=e[49];let Q;e[50]!==z?(Q={key:"openToPublic",propertyLabel:z,type:"boolean"},e[50]=z,e[51]=Q):Q=e[51];let G;e[52]!==C||e[53]!==n?(G=C?[{key:"labels.some.key",propertyLabel:n("entityLabel.LabelKey"),type:"string"},{key:"labels.some.value",propertyLabel:n("entityLabel.LabelValue"),type:"string"}]:[],e[52]=C,e[53]=n,e[54]=G):G=e[54];let Qe;e[55]!==w||e[56]!==q||e[57]!==$||e[58]!==Q||e[59]!==G?(Qe=[w,q,$,Q,...G],e[55]=w,e[56]=q,e[57]=$,e[58]=Q,e[59]=G,e[60]=Qe):Qe=e[60];const sl=Qe;let Ge;e[61]===Symbol.for("react.memo_cache_sentinel")?(Ge={flexShrink:1},e[61]=Ge):Ge=e[61];const Pl=u.statusCategory;let J;e[62]!==k||e[63]!==f?(J=i=>{k({statusCategory:i.target.value}),f({current:1})},e[62]=k,e[63]=f,e[64]=J):J=e[64];let W;e[65]!==n?(W=n("deployment.Running"),e[65]=n,e[66]=W):W=e[66];let H;e[67]!==W?(H={label:W,value:"running"},e[67]=W,e[68]=H):H=e[68];let Y;e[69]!==n?(Y=n("deployment.status.Terminated"),e[69]=n,e[70]=Y):Y=e[70];let X;e[71]!==Y?(X={label:Y,value:"finished"},e[71]=Y,e[72]=X):X=e[72];let Z;e[73]!==H||e[74]!==X?(Z=[H,X],e[73]=H,e[74]=X,e[75]=Z):Z=e[75];let ee;e[76]!==u.statusCategory||e[77]!==J||e[78]!==Z?(ee=a.jsx(ln,{value:Pl,onChange:J,options:Z}),e[76]=u.statusCategory,e[77]=J,e[78]=Z,e[79]=ee):ee=e[79];const rl=u.filter??void 0;let le;e[80]!==k||e[81]!==f?(le=i=>{k({filter:i??null}),f({current:1})},e[80]=k,e[81]=f,e[82]=le):le=e[82];let ne;e[83]!==sl||e[84]!==rl||e[85]!==le?(ne=a.jsx(nn,{filterProperties:sl,value:rl,onChange:le}),e[83]=sl,e[84]=rl,e[85]=le,e[86]=ne):ne=e[86];let ae;e[87]!==ee||e[88]!==ne?(ae=a.jsxs(Me,{gap:"sm",align:"start",wrap:"wrap",style:Ge,children:[ee,ne]}),e[87]=ee,e[88]=ne,e[89]=ae):ae=e[89];let te;e[90]!==Ce||e[91]!==_||e[92]!==F?(te=a.jsx(Me,{gap:"xs",align:"center",children:a.jsx(an,{settingId:"deployment-list",defaultAutoUpdateDelay:15e3,value:Ce,onChange:F,loading:_})}),e[90]=Ce,e[91]=_,e[92]=F,e[93]=te):te=e[93];let ie;e[94]!==ae||e[95]!==te?(ie=a.jsxs(Me,{justify:"between",wrap:"wrap",gap:"sm",children:[ae,te]}),e[94]=ae,e[95]=te,e[96]=ie):ie=e[96];const ol=C?he:void 0;let se;e[97]!==k||e[98]!==f?(se=i=>{k({filter:tn(i)}),f({current:1})},e[97]=k,e[98]=f,e[99]=se):se=e[99];let re;e[100]!==k?(re=i=>{k({order:i??null})},e[100]=k,e[101]=re):re=e[101];let oe;e[102]!==f?(oe=(i,N)=>{f({current:i,pageSize:N})},e[102]=f,e[103]=oe):oe=e[103];let ue;e[104]!==oe||e[105]!==x.current||e[106]!==x.pageSize||e[107]!==B?(ue={current:x.current,pageSize:x.pageSize,total:B,onChange:oe},e[104]=oe,e[105]=x.current,e[106]=x.pageSize,e[107]=B,e[108]=ue):ue=e[108];let de;e[109]!==Xe||e[110]!==Ze?(de={columnOverrides:Xe,onColumnOverridesChange:Ze},e[109]=Xe,e[110]=Ze,e[111]=de):de=e[111];let ce;e[112]!==c||e[113]!==S||e[114]!==n||e[115]!==s?(ce=i=>{const N=["name","currentRevisionNumber","status","labels","replicaSummary","model","createdAt","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup"],Rl=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt"]);return i.filter(b=>N.includes(b.key)).map(b=>{let Ne=b;return b.key==="name"?Ne={...b,render:(Ll,L)=>{var T,Ye;const h=fn((T=L.metadata)==null?void 0:T.status);return a.jsx(sn,{title:((Ye=L.metadata)==null?void 0:Ye.name)??"-",onTitleClick:()=>s(`${c("deployments")}/${Il(L.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:n("deployment.EditDeployment"),icon:a.jsx(rn,{}),disabled:h,onClick:()=>y(L.id)},{key:"delete",title:n("deployment.DeleteDeployment"),icon:a.jsx(on,{size:"1em"}),type:"danger",disabled:h,onClick:()=>P(L.id)}]})}}:b.key==="currentRevisionNumber"?Ne={...b,render:(Ll,L)=>{const h=S.find(Ye=>Ye.id===L.id),T=h==null?void 0:h.currentRevision;return(T==null?void 0:T.revisionNumber)==null?a.jsx(hl,{color:"secondary",children:"-"}):a.jsx(un,{onClick:()=>Te(T),children:`#${T.revisionNumber}`})}}:b.key==="tags"&&(Ne={...b,render:(Ll,L)=>a.jsx(kn,{metadataFrgmt:L.metadata,stopRowClick:!0,onTagClick:h=>{s({pathname:c("deployments"),search:new URLSearchParams({filter:JSON.stringify({tags:{iEquals:h}})}).toString()})},fallback:a.jsx(hl,{color:"secondary",children:"-"})})}),b.key==="name"?Ne:{...Ne,defaultHidden:!Rl.has(b.key)}})},e[112]=c,e[113]=S,e[114]=n,e[115]=s,e[116]=ce):ce=e[116];let me;e[117]!==S||e[118]!==_||e[119]!==u.order||e[120]!==ol||e[121]!==se||e[122]!==re||e[123]!==ue||e[124]!==de||e[125]!==ce?(me=a.jsx(yn,{onEditLabels:ol,onLabelClick:se,deploymentsFrgmt:S,loading:_,order:u.order,onChangeOrder:re,pagination:ue,tableSettings:de,customizeColumns:ce}),e[117]=S,e[118]=_,e[119]=u.order,e[120]=ol,e[121]=se,e[122]=re,e[123]=ue,e[124]=de,e[125]=ce,e[126]=me):me=e[126];let ge;e[127]!==ie||e[128]!==me?(ge=a.jsxs(Me,{direction:"column",align:"stretch",gap:"sm",children:[ie,me]}),e[127]=ie,e[128]=me,e[129]=ge):ge=e[129];const ul=!!m;let ye;e[130]!==m?(ye=m?[{entityId:m.entityId,name:((Fl=m.metadata)==null?void 0:Fl.name)??void 0}]:[],e[130]=m,e[131]=ye):ye=e[131];const dl=m==null?void 0:m.entityLabels;let pe;e[132]!==F?(pe=i=>{he(null),i&&F()},e[132]=F,e[133]=pe):pe=e[133];let fe;e[134]!==ul||e[135]!==ye||e[136]!==dl||e[137]!==pe?(fe=a.jsx(dn,{open:ul,entityType:"deployment",targets:ye,entityLabelsFrgmt:dl,onRequestClose:pe}),e[134]=ul,e[135]=ye,e[136]=dl,e[137]=pe,e[138]=fe):fe=e[138];let ke;e[139]!==I||e[140]!==K||e[141]!==v||e[142]!==je||e[143]!==F?(ke=je!=null&&a.jsx(Tl,{children:a.jsx(mn,{open:K||!!I,deploymentFrgmt:I??null,project:je,onRequestClose:i=>{v(),y(null),i&&!I&&F()}})}),e[139]=I,e[140]=K,e[141]=v,e[142]=je,e[143]=F,e[144]=ke):ke=e[144];const cl=!!o;let Fe;e[145]!==n?(Fe=n("deployment.DeleteDeployment"),e[145]=n,e[146]=Fe):Fe=e[146];let Se;e[147]!==n?(Se=n("deployment.Deployment"),e[147]=n,e[148]=Se):Se=e[148];let be;e[149]!==o?(be=o?[{key:o.id,label:((Sl=o.metadata)==null?void 0:Sl.name)??""}]:[],e[149]=o,e[150]=be):be=e[150];const ml=((bl=o==null?void 0:o.metadata)==null?void 0:bl.name)??"",gl=((Kl=o==null?void 0:o.metadata)==null?void 0:Kl.name)??"";let Ke;e[151]!==gl?(Ke={placeholder:gl},e[151]=gl,e[152]=Ke):Ke=e[152];let Le;e[153]!==il?(Le={loading:il},e[153]=il,e[154]=Le):Le=e[154];let ve;e[155]!==tl||e[156]!==o||e[157]!==t||e[158]!==d||e[159]!==n||e[160]!==F?(ve=()=>{o&&tl({variables:{input:{id:Il(o.id)??o.id}},onCompleted:(i,N)=>{if(N&&N.length>0){t.error("Failed to delete deployment",N),d.error(n("deployment.FailedToDeleteDeployment"));return}d.success(n("deployment.DeploymentDeleted")),P(null),F()},onError:i=>{t.error("Failed to delete deployment",i),d.error(n("deployment.FailedToDeleteDeployment"))}})},e[155]=tl,e[156]=o,e[157]=t,e[158]=d,e[159]=n,e[160]=F,e[161]=ve):ve=e[161];let Je;e[162]===Symbol.for("react.memo_cache_sentinel")?(Je=()=>P(null),e[162]=Je):Je=e[162];let De;e[163]!==cl||e[164]!==Fe||e[165]!==Se||e[166]!==be||e[167]!==ml||e[168]!==Ke||e[169]!==Le||e[170]!==ve?(De=a.jsx(cn,{open:cl,title:Fe,target:Se,items:be,confirmText:ml,requireConfirmInput:!0,inputProps:Ke,okButtonProps:Le,onOk:ve,onCancel:Je}),e[163]=cl,e[164]=Fe,e[165]=Se,e[166]=be,e[167]=ml,e[168]=Ke,e[169]=Le,e[170]=ve,e[171]=De):De=e[171];const yl=!!D;let We;e[172]===Symbol.for("react.memo_cache_sentinel")?(We=()=>Te(null),e[172]=We):We=e[172];let Ie;e[173]!==D||e[174]!==yl?(Ie=a.jsx(Tl,{children:a.jsx(gn,{open:yl,revisionFrgmt:D,onClose:We})}),e[173]=D,e[174]=yl,e[175]=Ie):Ie=e[175];let He;return e[176]!==ge||e[177]!==fe||e[178]!==ke||e[179]!==De||e[180]!==Ie?(He=a.jsxs(a.Fragment,{children:[ge,fe,ke,De,Ie]}),e[176]=ge,e[177]=fe,e[178]=ke,e[179]=De,e[180]=Ie,e[181]=He):He=e[181],He},Tn=()=>{"use memo";const l=Cl.c(15),{t:e}=Al(),[K,v]=xl(!1),{setLeft:n,setRight:d}=v;Vl(d);let t;l[0]!==e?(t=e("webui.menu.Deployments"),l[0]=e,l[1]=t):t=l[1];let s;l[2]!==e?(s=e("deployment.CreateDeployment"),l[2]=e,l[3]=s):s=l[3];let c;l[4]!==d||l[5]!==s?(c=a.jsx(jl,{variant:"primary",label:s,onClick:d}),l[4]=d,l[5]=s,l[6]=c):c=l[6];let g;l[7]===Symbol.for("react.memo_cache_sentinel")?(g=a.jsx(Bl,{}),l[7]=g):g=l[7];let y;l[8]!==n||l[9]!==K?(y=a.jsx(M.Suspense,{fallback:g,children:a.jsx(Fn,{isCreating:K,onCloseCreate:n})}),l[8]=n,l[9]=K,l[10]=y):y=l[10];let p;return l[11]!==t||l[12]!==c||l[13]!==y?(p=a.jsx(Me,{direction:"column",align:"stretch",gap:"md",children:a.jsx(_l,{variant:"borderless",title:t,extra:c,children:y})}),l[11]=t,l[12]=c,l[13]=y,l[14]=p):p=l[14],p};function Sn(l){return typeof l=="object"&&l!==null&&!Array.isArray(l)?l:{}}export{Tn as default};
//# sourceMappingURL=DeploymentListPage-Cp2Ah1gK.js.map
