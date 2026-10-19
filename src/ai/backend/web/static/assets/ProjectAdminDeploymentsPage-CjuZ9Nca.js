import{i as Al,u as jl,z as Rl,j as a,cu as Vl,l as j,aV as vl,x as xl,X as Bl,Y as _l,dd as El,bJ as wl,ce as Ll,af as Ol,ae as Ul,a7 as $l,aM as ql,aS as zl,r as Il,aT as Ql,ak as Gl,bk as Jl,W as Wl,dj as Hl,b2 as Yl,c as ol,dJ as Xl,dh as Zl,bL as en,aJ as ln,aL as nn,K as Tl,a2 as hl,L as an,dk as tn,bR as sn,an as rn,d as on}from"./index-4XAoWQdC.js";import{D as dn,a as un}from"./DeploymentSettingModal-DKW6wAC4.js";import{B as mn,a as cn}from"./BAIModelDeploymentNodes-BTdMt6K7.js";import{i as yn,B as gn}from"./BAIDeploymentTagTokens-DaVJhxci.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-B13SaUe_.js";import"./BAIBooleanToken-D4JLjIi_.js";const Cl=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e},params:{cacheID:"1463ddcf31aa971e7f72ca3901c5db76",id:null,metadata:{},name:"ProjectAdminDeploymentsPageDeleteMutation",operationKind:"mutation",text:`mutation ProjectAdminDeploymentsPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();Cl.hash="42ff73332d0c41e5828ba82d49920b78";const Pl=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},p={defaultValue:null,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"orderBy"},d={defaultValue:null,kind:"LocalArgument",name:"projectId"},m=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},Te={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},T={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[i,u,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},he={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},Ae=[u,F],K={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},b=[K,F];return{fragment:{argumentDefinitions:[n,e,p,l,d],kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:m,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[i,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[u,Te],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,I,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[d,n,l,e,p],kind:"Operation",name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:m,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},u,Te,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},C,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[u],storageKey:null},i],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[o],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[i,I,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[T,c,he,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"subpath",storageKey:null}],storageKey:null},C,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:Ae,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[u,i],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:Ae,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},F,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[K],storageKey:null},i],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[c,he,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},T],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[i,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2TagEntry",kind:"LinkedField",name:"tags",plural:!0,selections:b,storageKey:null},{alias:null,args:null,concreteType:"ImageV2LabelEntry",kind:"LinkedField",name:"labels",plural:!0,selections:b,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"command",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:[{kind:"Literal",name:"limit",value:100}],concreteType:"EntityLabelConnection",kind:"LinkedField",name:"entityLabels",plural:!1,selections:[{alias:null,args:null,concreteType:"EntityLabelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"EntityLabel",kind:"LinkedField",name:"node",plural:!1,selections:[K,F,i,{alias:null,args:null,kind:"ScalarField",name:"fieldId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:"entityLabels(limit:100)"},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[i,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"38dd69b67558f20e6462d81aa0fa80f6",id:null,metadata:{},name:"ProjectAdminDeploymentsPageQuery",operationKind:"query",text:`query ProjectAdminDeploymentsPageQuery(
  $projectId: UUID!
  $filter: DeploymentFilter
  $orderBy: [DeploymentOrderBy!]
  $limit: Int
  $offset: Int
) {
  projectDeployments(scope: {projectId: $projectId}, filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
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
`}}})();Pl.hash="c25a61811c5da96b20ea537235c62251";const pn=n=>{"use memo";var cl,yl,gl,pl,fl,kl,Fl,bl,Sl,Dl;const e=Al.c(176),{projectId:p}=n,{t:l}=jl(),{message:d}=Wl.useApp(),{logger:m}=xl(),o=Bl(),i=_l(),[u,Te]=j.useState(null),[I,C]=j.useState(null),T=El("deployment"),[c,he]=j.useState(null),[F,Ae]=j.useState(null);let K;e[0]===Symbol.for("react.memo_cache_sentinel")?(K={current:1,pageSize:10},e[0]=K):K=e[0];const{baiPaginationOption:b,tablePaginationOption:P,setTablePaginationOption:y}=wl(K);let Ne,Me;e[1]===Symbol.for("react.memo_cache_sentinel")?(Ne={filter:Ol(fn),order:Ll(cn),statusCategory:Ll(["running","finished"]).withDefault("running")},Me={history:"replace"},e[1]=Ne,e[2]=Me):(Ne=e[1],Me=e[2]);const[r,g]=Ul(Ne,Me),[Ge,Je]=$l("table_column_overrides.ProjectAdminDeploymentsPage"),[je,S]=ql();let Re;e[3]===Symbol.for("react.memo_cache_sentinel")?(Re=["STOPPED"],e[3]=Re):Re=e[3];const dl=Re;let Ve;e[4]!==r.statusCategory?(Ve=r.statusCategory==="finished"?{status:{in:dl}}:{status:{notIn:dl}},e[4]=r.statusCategory,e[5]=Ve):Ve=e[5];const We=Ve;let N;e[6]!==r.filter?(N=r.filter??{},e[6]=r.filter,e[7]=N):N=e[7];let M;e[8]!==We||e[9]!==N?(M={...N,...We},e[8]=We,e[9]=N,e[10]=M):M=e[10];let R;e[11]!==r.order?(R=zl(r.order),e[11]=r.order,e[12]=R):R=e[12];let xe;e[13]!==b.limit||e[14]!==b.offset||e[15]!==p||e[16]!==M||e[17]!==R?(xe={projectId:p,filter:M,orderBy:R,limit:b.limit,offset:b.offset},e[13]=b.limit,e[14]=b.offset,e[15]=p,e[16]=M,e[17]=R,e[18]=xe):xe=e[18];const ul=xe,ml=j.useDeferredValue(ul),Ce=j.useDeferredValue(je);let Be;e[19]===Symbol.for("react.memo_cache_sentinel")?(Be=Pl,e[19]=Be):Be=e[19];const He=Ce===Jl?"store-and-network":"network-only";let _e;e[20]!==Ce||e[21]!==He?(_e={fetchKey:Ce,fetchPolicy:He},e[20]=Ce,e[21]=He,e[22]=_e):_e=e[22];const V=Il.useLazyLoadQuery(Be,ml,_e);let f,h,Ee,x;e[23]!==((cl=V.projectDeployments)==null?void 0:cl.count)||e[24]!==((yl=V.projectDeployments)==null?void 0:yl.edges)||e[25]!==I||e[26]!==u?(f=Ql(Gl((gl=V.projectDeployments)==null?void 0:gl.edges,"node")),x=((pl=V.projectDeployments)==null?void 0:pl.count)??0,h=u==null?null:f.find(t=>t.id===u)??null,Ee=I==null?null:f.find(t=>t.id===I)??null,e[23]=(fl=V.projectDeployments)==null?void 0:fl.count,e[24]=(kl=V.projectDeployments)==null?void 0:kl.edges,e[25]=I,e[26]=u,e[27]=f,e[28]=h,e[29]=Ee,e[30]=x):(f=e[27],h=e[28],Ee=e[29],x=e[30]);const s=Ee,B=ml!==ul||Ce!==je;let we;e[31]===Symbol.for("react.memo_cache_sentinel")?(we=Cl,e[31]=we):we=e[31];const[Ye,Xe]=Il.useMutation(we);let _;e[32]!==l?(_=l("deployment.filter.Name"),e[32]=l,e[33]=_):_=e[33];let E;e[34]!==_?(E={key:"name",propertyLabel:_,type:"string"},e[34]=_,e[35]=E):E=e[35];let w;e[36]!==l?(w=l("deployment.filter.Tags"),e[36]=l,e[37]=w):w=e[37];let O;e[38]!==w?(O={key:"tags",propertyLabel:w,type:"string"},e[38]=w,e[39]=O):O=e[39];let U;e[40]!==l?(U=l("deployment.filter.EndpointUrl"),e[40]=l,e[41]=U):U=e[41];let $;e[42]!==U?($={key:"endpointUrl",propertyLabel:U,type:"string"},e[42]=U,e[43]=$):$=e[43];let q;e[44]!==l?(q=l("deployment.filter.OpenToPublic"),e[44]=l,e[45]=q):q=e[45];let z;e[46]!==q?(z={key:"openToPublic",propertyLabel:q,type:"boolean"},e[46]=q,e[47]=z):z=e[47];let Q;e[48]!==T||e[49]!==l?(Q=T?[{key:"labels.some.key",propertyLabel:l("entityLabel.LabelKey"),type:"string"},{key:"labels.some.value",propertyLabel:l("entityLabel.LabelValue"),type:"string"}]:[],e[48]=T,e[49]=l,e[50]=Q):Q=e[50];let Oe;e[51]!==E||e[52]!==O||e[53]!==$||e[54]!==z||e[55]!==Q?(Oe=[E,O,$,z,...Q],e[51]=E,e[52]=O,e[53]=$,e[54]=z,e[55]=Q,e[56]=Oe):Oe=e[56];const Ze=Oe;let Ue;e[57]===Symbol.for("react.memo_cache_sentinel")?(Ue={flexShrink:1},e[57]=Ue):Ue=e[57];const Nl=r.statusCategory;let G;e[58]!==g||e[59]!==y?(G=t=>{g({statusCategory:t.target.value}),y({current:1})},e[58]=g,e[59]=y,e[60]=G):G=e[60];let J;e[61]!==l?(J=l("deployment.Running"),e[61]=l,e[62]=J):J=e[62];let W;e[63]!==J?(W={label:J,value:"running"},e[63]=J,e[64]=W):W=e[64];let H;e[65]!==l?(H=l("deployment.status.Terminated"),e[65]=l,e[66]=H):H=e[66];let Y;e[67]!==H?(Y={label:H,value:"finished"},e[67]=H,e[68]=Y):Y=e[68];let X;e[69]!==W||e[70]!==Y?(X=[W,Y],e[69]=W,e[70]=Y,e[71]=X):X=e[71];let Z;e[72]!==r.statusCategory||e[73]!==G||e[74]!==X?(Z=a.jsx(Hl,{optionType:"button",value:Nl,onChange:G,options:X}),e[72]=r.statusCategory,e[73]=G,e[74]=X,e[75]=Z):Z=e[75];const el=r.filter??void 0;let ee;e[76]!==g||e[77]!==y?(ee=t=>{g({filter:t??null}),y({current:1})},e[76]=g,e[77]=y,e[78]=ee):ee=e[78];let le;e[79]!==Ze||e[80]!==el||e[81]!==ee?(le=a.jsx(Yl,{filterProperties:Ze,value:el,onChange:ee}),e[79]=Ze,e[80]=el,e[81]=ee,e[82]=le):le=e[82];let ne;e[83]!==Z||e[84]!==le?(ne=a.jsxs(ol,{gap:"sm",align:"start",wrap:"wrap",style:Ue,children:[Z,le]}),e[83]=Z,e[84]=le,e[85]=ne):ne=e[85];let ae;e[86]!==S?(ae=t=>S(t),e[86]=S,e[87]=ae):ae=e[87];let te;e[88]!==je||e[89]!==B||e[90]!==ae?(te=a.jsx(Xl,{settingId:"project-admin-deployments",defaultAutoUpdateDelay:15e3,loading:B,value:je,onChange:ae}),e[88]=je,e[89]=B,e[90]=ae,e[91]=te):te=e[91];let ie;e[92]!==ne||e[93]!==te?(ie=a.jsxs(ol,{justify:"between",wrap:"wrap",gap:"sm",children:[ne,te]}),e[92]=ne,e[93]=te,e[94]=ie):ie=e[94];const ll=T?he:void 0;let se;e[95]!==g||e[96]!==y?(se=t=>{g({filter:Zl(t)}),y({current:1})},e[95]=g,e[96]=y,e[97]=se):se=e[97];let re;e[98]!==g?(re=t=>{g({order:t??null})},e[98]=g,e[99]=re):re=e[99];let oe;e[100]!==y?(oe=(t,A)=>{y({current:t,pageSize:A})},e[100]=y,e[101]=oe):oe=e[101];let de;e[102]!==oe||e[103]!==P.current||e[104]!==P.pageSize||e[105]!==x?(de={current:P.current,pageSize:P.pageSize,total:x,onChange:oe},e[102]=oe,e[103]=P.current,e[104]=P.pageSize,e[105]=x,e[106]=de):de=e[106];let ue;e[107]!==Ge||e[108]!==Je?(ue={columnOverrides:Ge,onColumnOverridesChange:Je},e[107]=Ge,e[108]=Je,e[109]=ue):ue=e[109];let me;e[110]!==i||e[111]!==f||e[112]!==l||e[113]!==o?(me=t=>{const A=["name","currentRevisionNumber","status","labels","replicaSummary","model","createdAt","owner","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup","domainName","projectId"],Ml=new Set(["name","currentRevisionNumber","status","labels","replicaSummary","model","createdAt","owner"]);return t.filter(k=>A.includes(k.key)).map(k=>{let Pe=k;return k.key==="name"?Pe={...k,render:(Kl,D)=>{var L,Qe;const v=yn((L=D.metadata)==null?void 0:L.status);return a.jsx(en,{title:((Qe=D.metadata)==null?void 0:Qe.name)??"-",onTitleClick:()=>o(i(`deployments/${Tl(D.id)}`)),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:a.jsx(ln,{}),disabled:v,onClick:()=>Te(D.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:a.jsx(nn,{size:"1em"}),type:"danger",disabled:v,onClick:()=>C(D.id)}]})}}:k.key==="currentRevisionNumber"?Pe={...k,render:(Kl,D)=>{const v=f.find(Qe=>Qe.id===D.id),L=v==null?void 0:v.currentRevision;return(L==null?void 0:L.revisionNumber)==null?a.jsx(hl,{color:"secondary",children:"-"}):a.jsx(an,{onClick:()=>Ae(L),children:`#${L.revisionNumber}`})}}:k.key==="tags"&&(Pe={...k,render:(Kl,D)=>a.jsx(gn,{metadataFrgmt:D.metadata,stopRowClick:!0,onTagClick:v=>{o({pathname:i("deployments"),search:new URLSearchParams({filter:JSON.stringify({tags:{iEquals:v}})}).toString()})},fallback:a.jsx(hl,{color:"secondary",children:"-"})})}),k.key==="name"?Pe:{...Pe,defaultHidden:!Ml.has(k.key)}})},e[110]=i,e[111]=f,e[112]=l,e[113]=o,e[114]=me):me=e[114];let ce;e[115]!==f||e[116]!==B||e[117]!==r.order||e[118]!==ll||e[119]!==se||e[120]!==re||e[121]!==de||e[122]!==ue||e[123]!==me?(ce=a.jsx(mn,{onEditLabels:ll,showLabelsByDefault:!0,onLabelClick:se,deploymentsFrgmt:f,loading:B,order:r.order,onChangeOrder:re,pagination:de,tableSettings:ue,customizeColumns:me}),e[115]=f,e[116]=B,e[117]=r.order,e[118]=ll,e[119]=se,e[120]=re,e[121]=de,e[122]=ue,e[123]=me,e[124]=ce):ce=e[124];let ye;e[125]!==ie||e[126]!==ce?(ye=a.jsxs(ol,{direction:"column",align:"stretch",gap:"sm",children:[ie,ce]}),e[125]=ie,e[126]=ce,e[127]=ye):ye=e[127];const nl=!!c;let ge;e[128]!==c?(ge=c?[{entityId:c.entityId,name:((Fl=c.metadata)==null?void 0:Fl.name)??void 0}]:[],e[128]=c,e[129]=ge):ge=e[129];const al=c==null?void 0:c.entityLabels;let pe;e[130]!==S?(pe=t=>{he(null),t&&S()},e[130]=S,e[131]=pe):pe=e[131];let fe;e[132]!==nl||e[133]!==ge||e[134]!==al||e[135]!==pe?(fe=a.jsx(tn,{open:nl,entityType:"deployment",targets:ge,entityLabelsFrgmt:al,onRequestClose:pe}),e[132]=nl,e[133]=ge,e[134]=al,e[135]=pe,e[136]=fe):fe=e[136];let ke;e[137]!==h?(ke=h!=null&&a.jsx(dn,{open:!0,deploymentFrgmt:h,onRequestClose:()=>{Te(null)}}),e[137]=h,e[138]=ke):ke=e[138];const tl=!!s;let Fe;e[139]!==l?(Fe=l("deployment.DeleteDeployment"),e[139]=l,e[140]=Fe):Fe=e[140];let be;e[141]!==l?(be=l("deployment.Deployment"),e[141]=l,e[142]=be):be=e[142];let Se;e[143]!==s?(Se=s?[{key:s.id,label:((bl=s.metadata)==null?void 0:bl.name)??""}]:[],e[143]=s,e[144]=Se):Se=e[144];const il=((Sl=s==null?void 0:s.metadata)==null?void 0:Sl.name)??"",sl=((Dl=s==null?void 0:s.metadata)==null?void 0:Dl.name)??"";let De;e[145]!==sl?(De={placeholder:sl},e[145]=sl,e[146]=De):De=e[146];let Ke;e[147]!==Xe?(Ke={loading:Xe},e[147]=Xe,e[148]=Ke):Ke=e[148];let ve;e[149]!==Ye||e[150]!==s||e[151]!==m||e[152]!==d||e[153]!==l||e[154]!==S?(ve=()=>{s&&Ye({variables:{input:{id:Tl(s.id)??s.id}},onCompleted:(t,A)=>{if(A&&A.length>0){m.error("Failed to delete deployment",A),d.error(l("deployment.FailedToDeleteDeployment"));return}d.success(l("deployment.DeploymentDeleted")),C(null),S()},onError:t=>{m.error("Failed to delete deployment",t),d.error(l("deployment.FailedToDeleteDeployment"))}})},e[149]=Ye,e[150]=s,e[151]=m,e[152]=d,e[153]=l,e[154]=S,e[155]=ve):ve=e[155];let $e;e[156]===Symbol.for("react.memo_cache_sentinel")?($e=()=>C(null),e[156]=$e):$e=e[156];let Le;e[157]!==tl||e[158]!==Fe||e[159]!==be||e[160]!==Se||e[161]!==il||e[162]!==De||e[163]!==Ke||e[164]!==ve?(Le=a.jsx(sn,{open:tl,title:Fe,target:be,items:Se,confirmText:il,requireConfirmInput:!0,inputProps:De,okButtonProps:Ke,onOk:ve,onCancel:$e}),e[157]=tl,e[158]=Fe,e[159]=be,e[160]=Se,e[161]=il,e[162]=De,e[163]=Ke,e[164]=ve,e[165]=Le):Le=e[165];const rl=!!F;let qe;e[166]===Symbol.for("react.memo_cache_sentinel")?(qe=()=>Ae(null),e[166]=qe):qe=e[166];let Ie;e[167]!==F||e[168]!==rl?(Ie=a.jsx(rn,{children:a.jsx(un,{open:rl,revisionFrgmt:F,onClose:qe})}),e[167]=F,e[168]=rl,e[169]=Ie):Ie=e[169];let ze;return e[170]!==ye||e[171]!==fe||e[172]!==ke||e[173]!==Le||e[174]!==Ie?(ze=a.jsxs(a.Fragment,{children:[ye,fe,ke,Le,Ie]}),e[170]=ye,e[171]=fe,e[172]=ke,e[173]=Le,e[174]=Ie,e[175]=ze):ze=e[175],ze},Ln=()=>{"use memo";const n=Al.c(9),{t:e}=jl(),p=Rl();let l;n[0]!==e?(l=e("webui.menu.ProjectDeployments"),n[0]=e,n[1]=l):l=n[1];let d;n[2]===Symbol.for("react.memo_cache_sentinel")?(d={header:{borderBottom:"none"},body:{paddingTop:0}},n[2]=d):d=n[2];let m;n[3]===Symbol.for("react.memo_cache_sentinel")?(m=a.jsx(vl,{}),n[3]=m):m=n[3];let o;n[4]!==p.id?(o=a.jsx(Vl,{children:a.jsx(j.Suspense,{fallback:m,children:p.id?a.jsx(pn,{projectId:p.id}):a.jsx(vl,{})})}),n[4]=p.id,n[5]=o):o=n[5];let i;return n[6]!==l||n[7]!==o?(i=a.jsx(on,{variant:"borderless",title:l,styles:d,children:o}),n[6]=l,n[7]=o,n[8]=i):i=n[8],i};function fn(n){return typeof n=="object"&&n!==null&&!Array.isArray(n)?n:{}}export{Ln as default};
//# sourceMappingURL=ProjectAdminDeploymentsPage-CjuZ9Nca.js.map
