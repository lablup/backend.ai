import{i as fl,u as kl,bF as Dl,dR as hl,j as a,au as bl,aV as Cl,l as ve,c as be,d as Ll,Y as Il,y as Tl,Z as Nl,_ as Al,bG as Pl,ca as cl,ah as Rl,af as xl,a8 as Ml,aO as Vl,A as jl,X as Bl,aS as _l,r as ml,aT as Ol,am as wl,bh as El,de as Ul,dx as $l,bI as ql,aL as zl,aN as Gl,O as gl,a3 as pl,L as Ql,ap as yl,bO as Hl}from"./index-B-6GqBhJ.js";import{D as Wl,a as Jl}from"./DeploymentSettingModal-_fG53NM2.js";import{a as Yl,B as Xl}from"./BAIModelDeploymentNodes-BWzByDMU.js";import{B as Zl}from"./BAIGraphQLPropertyFilter-Bp1GJNAy.js";import{i as en,B as ln}from"./BAIDeploymentTagChips-ykKB6D-V.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-BixUYyr6.js";import"./BooleanTag-ZCSHdESd.js";import"./BAITag-CYNOC3Sq.js";const Fl=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentListPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentListPageDeleteMutation",selections:e},params:{cacheID:"4639cd2572faeb586296319d8202e23a",id:null,metadata:{},name:"DeploymentListPageDeleteMutation",operationKind:"mutation",text:`mutation DeploymentListPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();Fl.hash="867cc2a31d2fc3342a0bafe7502c0483";const Sl=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},k={defaultValue:null,kind:"LocalArgument",name:"offset"},b={defaultValue:null,kind:"LocalArgument",name:"orderBy"},n=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],d={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},p={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,i,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},R={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},x={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},N=[i,x],F={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},S=[F,x];return{fragment:{argumentDefinitions:[l,e,k,b],kind:"Fragment",metadata:null,name:"DeploymentListPageQuery",selections:[{alias:null,args:n,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[i,c],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,m,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,b,e,k],kind:"Operation",name:"DeploymentListPageQuery",selections:[{alias:null,args:n,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},i,c,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},g,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[i],storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[d],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,m,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[p,R,T,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"subpath",storageKey:null}],storageKey:null},g,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:N,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[i,t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:N,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},x,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[F],storageKey:null},t],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[R,T,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},p],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2TagEntry",kind:"LinkedField",name:"tags",plural:!0,selections:S,storageKey:null},{alias:null,args:null,concreteType:"ImageV2LabelEntry",kind:"LinkedField",name:"labels",plural:!0,selections:S,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"command",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[t,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"5a688d5d28bdd339e2d0a323021a5ad2",id:null,metadata:{},name:"DeploymentListPageQuery",operationKind:"query",text:`query DeploymentListPageQuery(
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
        currentRevision @since(version: "26.4.3") {
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
  creator @since(version: "26.4.3") {
    id
    basicInfo {
      email
      username
      fullName
    }
  }
}

fragment BAIDeploymentTagChips_metadata on ModelDeploymentMetadata {
  tags
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
    projectV2 @since(version: "26.4.3") {
      basicInfo {
        name
      }
      id
    }
    ...BAIDeploymentTagChips_metadata
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
  currentRevision @since(version: "26.4.3") {
    id
    revisionNumber
    modelMountConfig {
      vfolder {
        id
        name
      }
    }
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
  resourceSlots @since(version: "26.4.2") {
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
    runtimeVariantPresetValues @since(version: "26.4.4rc9") {
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
    subpath @since(version: "26.4.4")
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
  imageV2 @since(version: "26.4.3") {
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
`}}})();Sl.hash="7e57808b70c4eb1aab4a7a4d8af607d7";const nn=l=>{"use memo";var rl,ol,ul;const e=fl.c(163),{isCreating:k,onCloseCreate:b}=l,{t:n}=kl(),{message:d}=Il.useApp(),{logger:t}=Tl(),i=Nl(),c=Al(),[m,g]=ve.useState(null),[p,R]=ve.useState(null),[T,x]=ve.useState(null);let N;e[0]===Symbol.for("react.memo_cache_sentinel")?(N={current:1,pageSize:10},e[0]=N):N=e[0];const{baiPaginationOption:F,tablePaginationOption:S,setTablePaginationOption:v}=Pl(N);let Ce,Le;e[1]===Symbol.for("react.memo_cache_sentinel")?(Ce={filter:Rl(an),order:cl(Yl),statusCategory:cl(["running","finished"]).withDefault("running")},Le={history:"replace"},e[1]=Ce,e[2]=Le):(Ce=e[1],Le=e[2]);const[u,K]=xl(Ce,Le),[qe,ze]=Ml("table_column_overrides.DeploymentListPage"),[Ke,D]=Vl(),A=jl();let Ie;e[3]!==A?(Ie=Bl(A),e[3]=A,e[4]=Ie):Ie=e[4];const Te=Ie;let Ne;e[5]!==u.order?(Ne=_l(u.order),e[5]=u.order,e[6]=Ne):Ne=e[6];const Ge=Ne;let Ae;e[7]===Symbol.for("react.memo_cache_sentinel")?(Ae=["STOPPED"],e[7]=Ae):Ae=e[7];const tl=Ae;let Pe;e[8]!==u.statusCategory?(Pe=u.statusCategory==="finished"?{status:{in:tl}}:{status:{notIn:tl}},e[8]=u.statusCategory,e[9]=Pe):Pe=e[9];const Qe=Pe;let Re;e[10]!==A.id?(Re=A.id?{projectId:{equals:A.id}}:{},e[10]=A.id,e[11]=Re):Re=e[11];const He=Re;let M;e[12]!==u.filter?(M=u.filter??{},e[12]=u.filter,e[13]=M):M=e[13];let V;e[14]!==He||e[15]!==Qe||e[16]!==M?(V={...M,...Qe,...He},e[14]=He,e[15]=Qe,e[16]=M,e[17]=V):V=e[17];let xe;e[18]!==F.limit||e[19]!==F.offset||e[20]!==Ge||e[21]!==V?(xe={filter:V,orderBy:Ge,limit:F.limit,offset:F.offset},e[18]=F.limit,e[19]=F.offset,e[20]=Ge,e[21]=V,e[22]=xe):xe=e[22];const il=xe,sl=ve.useDeferredValue(il),De=ve.useDeferredValue(Ke);let Me;e[23]===Symbol.for("react.memo_cache_sentinel")?(Me=Sl,e[23]=Me):Me=e[23];const We=De===El?"store-and-network":"network-only";let Ve;e[24]!==De||e[25]!==We?(Ve={fetchPolicy:We,fetchKey:De},e[24]=De,e[25]=We,e[26]=Ve):Ve=e[26];const{myDeployments:s}=ml.useLazyLoadQuery(Me,sl,Ve);let y,C,je,j;e[27]!==p||e[28]!==m||e[29]!==(s==null?void 0:s.count)||e[30]!==(s==null?void 0:s.edges)?(y=Ol(wl(s==null?void 0:s.edges,"node")),j=(s==null?void 0:s.count)??0,C=m==null?null:y.find(r=>r.id===m)??null,je=p==null?null:y.find(r=>r.id===p)??null,e[27]=p,e[28]=m,e[29]=s==null?void 0:s.count,e[30]=s==null?void 0:s.edges,e[31]=y,e[32]=C,e[33]=je,e[34]=j):(y=e[31],C=e[32],je=e[33],j=e[34]);const o=je,B=sl!==il||De!==Ke;let Be;e[35]===Symbol.for("react.memo_cache_sentinel")?(Be=Fl,e[35]=Be):Be=e[35];const[Je,Ye]=ml.useMutation(Be);let _;e[36]!==n?(_=n("deployment.filter.Name"),e[36]=n,e[37]=_):_=e[37];let O;e[38]!==_?(O={key:"name",propertyLabel:_,type:"string"},e[38]=_,e[39]=O):O=e[39];let w;e[40]!==n?(w=n("deployment.filter.Tags"),e[40]=n,e[41]=w):w=e[41];let E;e[42]!==w?(E={key:"tags",propertyLabel:w,type:"string"},e[42]=w,e[43]=E):E=e[43];let U;e[44]!==n?(U=n("deployment.filter.EndpointUrl"),e[44]=n,e[45]=U):U=e[45];let $;e[46]!==U?($={key:"endpointUrl",propertyLabel:U,type:"string"},e[46]=U,e[47]=$):$=e[47];let q;e[48]!==n?(q=n("deployment.filter.OpenToPublic"),e[48]=n,e[49]=q):q=e[49];let z;e[50]!==q?(z={key:"openToPublic",propertyLabel:q,type:"boolean"},e[50]=q,e[51]=z):z=e[51];let _e;e[52]!==O||e[53]!==E||e[54]!==$||e[55]!==z?(_e=[O,E,$,z],e[52]=O,e[53]=E,e[54]=$,e[55]=z,e[56]=_e):_e=e[56];const Xe=_e;let Oe;e[57]===Symbol.for("react.memo_cache_sentinel")?(Oe={flexShrink:1},e[57]=Oe):Oe=e[57];const vl=u.statusCategory;let G;e[58]!==K||e[59]!==v?(G=r=>{K({statusCategory:r.target.value}),v({current:1})},e[58]=K,e[59]=v,e[60]=G):G=e[60];let Q;e[61]!==n?(Q=n("deployment.Running"),e[61]=n,e[62]=Q):Q=e[62];let H;e[63]!==Q?(H={label:Q,value:"running"},e[63]=Q,e[64]=H):H=e[64];let W;e[65]!==n?(W=n("deployment.status.Terminated"),e[65]=n,e[66]=W):W=e[66];let J;e[67]!==W?(J={label:W,value:"finished"},e[67]=W,e[68]=J):J=e[68];let Y;e[69]!==H||e[70]!==J?(Y=[H,J],e[69]=H,e[70]=J,e[71]=Y):Y=e[71];let X;e[72]!==u.statusCategory||e[73]!==G||e[74]!==Y?(X=a.jsx(Ul,{value:vl,onChange:G,options:Y}),e[72]=u.statusCategory,e[73]=G,e[74]=Y,e[75]=X):X=e[75];const Ze=u.filter??void 0;let Z;e[76]!==K||e[77]!==v?(Z=r=>{K({filter:r??null}),v({current:1})},e[76]=K,e[77]=v,e[78]=Z):Z=e[78];let ee;e[79]!==Xe||e[80]!==Ze||e[81]!==Z?(ee=a.jsx(Zl,{filterProperties:Xe,value:Ze,onChange:Z}),e[79]=Xe,e[80]=Ze,e[81]=Z,e[82]=ee):ee=e[82];let le;e[83]!==X||e[84]!==ee?(le=a.jsxs(be,{gap:"sm",align:"start",wrap:"wrap",style:Oe,children:[X,ee]}),e[83]=X,e[84]=ee,e[85]=le):le=e[85];let ne;e[86]!==Ke||e[87]!==B||e[88]!==D?(ne=a.jsx(be,{gap:"xs",align:"center",children:a.jsx($l,{settingId:"deployment-list",defaultAutoUpdateDelay:15e3,value:Ke,onChange:D,loading:B})}),e[86]=Ke,e[87]=B,e[88]=D,e[89]=ne):ne=e[89];let ae;e[90]!==le||e[91]!==ne?(ae=a.jsxs(be,{justify:"between",wrap:"wrap",gap:"sm",children:[le,ne]}),e[90]=le,e[91]=ne,e[92]=ae):ae=e[92];let te;e[93]!==K?(te=r=>{K({order:r??null})},e[93]=K,e[94]=te):te=e[94];let ie;e[95]!==v?(ie=(r,P)=>{v({current:r,pageSize:P})},e[95]=v,e[96]=ie):ie=e[96];let se;e[97]!==ie||e[98]!==S.current||e[99]!==S.pageSize||e[100]!==j?(se={current:S.current,pageSize:S.pageSize,total:j,onChange:ie},e[97]=ie,e[98]=S.current,e[99]=S.pageSize,e[100]=j,e[101]=se):se=e[101];let re;e[102]!==qe||e[103]!==ze?(re={columnOverrides:qe,onColumnOverridesChange:ze},e[102]=qe,e[103]=ze,e[104]=re):re=e[104];let oe;e[105]!==c||e[106]!==y||e[107]!==n||e[108]!==i?(oe=r=>{const P=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup"],Kl=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt"]);return r.filter(f=>P.includes(f.key)).map(f=>{let he=f;return f.key==="name"?he={...f,render:(dl,h)=>{var I,$e;const L=en((I=h.metadata)==null?void 0:I.status);return a.jsx(ql,{title:(($e=h.metadata)==null?void 0:$e.name)??"-",onTitleClick:()=>i(`${c("deployments")}/${gl(h.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:n("deployment.EditDeployment"),icon:a.jsx(zl,{}),disabled:L,onClick:()=>g(h.id)},{key:"delete",title:n("deployment.DeleteDeployment"),icon:a.jsx(Gl,{size:"1em"}),type:"danger",disabled:L,onClick:()=>R(h.id)}]})}}:f.key==="currentRevisionNumber"?he={...f,render:(dl,h)=>{const L=y.find($e=>$e.id===h.id),I=L==null?void 0:L.currentRevision;return(I==null?void 0:I.revisionNumber)==null?a.jsx(pl,{color:"secondary",children:"-"}):a.jsx(Ql,{onClick:()=>x(I),children:`#${I.revisionNumber}`})}}:f.key==="tags"&&(he={...f,render:(dl,h)=>a.jsx(ln,{metadataFrgmt:h.metadata,stopRowClick:!0,onTagClick:L=>{i({pathname:c("deployments"),search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:L}})}).toString()})},fallback:a.jsx(pl,{color:"secondary",children:"-"})})}),f.key==="name"?he:{...he,defaultHidden:!Kl.has(f.key)}})},e[105]=c,e[106]=y,e[107]=n,e[108]=i,e[109]=oe):oe=e[109];let ue;e[110]!==y||e[111]!==B||e[112]!==u.order||e[113]!==te||e[114]!==se||e[115]!==re||e[116]!==oe?(ue=a.jsx(Xl,{deploymentsFrgmt:y,loading:B,order:u.order,onChangeOrder:te,pagination:se,tableSettings:re,customizeColumns:oe}),e[110]=y,e[111]=B,e[112]=u.order,e[113]=te,e[114]=se,e[115]=re,e[116]=oe,e[117]=ue):ue=e[117];let de;e[118]!==ae||e[119]!==ue?(de=a.jsxs(be,{direction:"column",align:"stretch",gap:"sm",children:[ae,ue]}),e[118]=ae,e[119]=ue,e[120]=de):de=e[120];let ce;e[121]!==C||e[122]!==k||e[123]!==b||e[124]!==Te||e[125]!==D?(ce=Te!=null&&a.jsx(yl,{children:a.jsx(Wl,{open:k||!!C,deploymentFrgmt:C??null,project:Te,onRequestClose:r=>{b(),g(null),r&&!C&&D()}})}),e[121]=C,e[122]=k,e[123]=b,e[124]=Te,e[125]=D,e[126]=ce):ce=e[126];const el=!!o;let me;e[127]!==n?(me=n("deployment.DeleteDeployment"),e[127]=n,e[128]=me):me=e[128];let ge;e[129]!==n?(ge=n("deployment.Deployment"),e[129]=n,e[130]=ge):ge=e[130];let pe;e[131]!==o?(pe=o?[{key:o.id,label:((rl=o.metadata)==null?void 0:rl.name)??""}]:[],e[131]=o,e[132]=pe):pe=e[132];const ll=((ol=o==null?void 0:o.metadata)==null?void 0:ol.name)??"",nl=((ul=o==null?void 0:o.metadata)==null?void 0:ul.name)??"";let ye;e[133]!==nl?(ye={placeholder:nl},e[133]=nl,e[134]=ye):ye=e[134];let fe;e[135]!==Ye?(fe={loading:Ye},e[135]=Ye,e[136]=fe):fe=e[136];let ke;e[137]!==Je||e[138]!==o||e[139]!==t||e[140]!==d||e[141]!==n||e[142]!==D?(ke=()=>{o&&Je({variables:{input:{id:gl(o.id)??o.id}},onCompleted:(r,P)=>{if(P&&P.length>0){t.error("Failed to delete deployment",P),d.error(n("deployment.FailedToDeleteDeployment"));return}d.success(n("deployment.DeploymentDeleted")),R(null),D()},onError:r=>{t.error("Failed to delete deployment",r),d.error(n("deployment.FailedToDeleteDeployment"))}})},e[137]=Je,e[138]=o,e[139]=t,e[140]=d,e[141]=n,e[142]=D,e[143]=ke):ke=e[143];let we;e[144]===Symbol.for("react.memo_cache_sentinel")?(we=()=>R(null),e[144]=we):we=e[144];let Fe;e[145]!==el||e[146]!==me||e[147]!==ge||e[148]!==pe||e[149]!==ll||e[150]!==ye||e[151]!==fe||e[152]!==ke?(Fe=a.jsx(Hl,{open:el,title:me,target:ge,items:pe,confirmText:ll,requireConfirmInput:!0,inputProps:ye,okButtonProps:fe,onOk:ke,onCancel:we}),e[145]=el,e[146]=me,e[147]=ge,e[148]=pe,e[149]=ll,e[150]=ye,e[151]=fe,e[152]=ke,e[153]=Fe):Fe=e[153];const al=!!T;let Ee;e[154]===Symbol.for("react.memo_cache_sentinel")?(Ee=()=>x(null),e[154]=Ee):Ee=e[154];let Se;e[155]!==T||e[156]!==al?(Se=a.jsx(yl,{children:a.jsx(Jl,{open:al,revisionFrgmt:T,onClose:Ee})}),e[155]=T,e[156]=al,e[157]=Se):Se=e[157];let Ue;return e[158]!==de||e[159]!==ce||e[160]!==Fe||e[161]!==Se?(Ue=a.jsxs(a.Fragment,{children:[de,ce,Fe,Se]}),e[158]=de,e[159]=ce,e[160]=Fe,e[161]=Se,e[162]=Ue):Ue=e[162],Ue},pn=()=>{"use memo";const l=fl.c(15),{t:e}=kl(),[k,b]=Dl(!1),{setLeft:n,setRight:d}=b;hl(d);let t;l[0]!==e?(t=e("webui.menu.Deployments"),l[0]=e,l[1]=t):t=l[1];let i;l[2]!==e?(i=e("deployment.CreateDeployment"),l[2]=e,l[3]=i):i=l[3];let c;l[4]!==d||l[5]!==i?(c=a.jsx(bl,{variant:"primary",label:i,onClick:d}),l[4]=d,l[5]=i,l[6]=c):c=l[6];let m;l[7]===Symbol.for("react.memo_cache_sentinel")?(m=a.jsx(Cl,{}),l[7]=m):m=l[7];let g;l[8]!==n||l[9]!==k?(g=a.jsx(ve.Suspense,{fallback:m,children:a.jsx(nn,{isCreating:k,onCloseCreate:n})}),l[8]=n,l[9]=k,l[10]=g):g=l[10];let p;return l[11]!==t||l[12]!==c||l[13]!==g?(p=a.jsx(be,{direction:"column",align:"stretch",gap:"md",children:a.jsx(Ll,{variant:"borderless",title:t,extra:c,children:g})}),l[11]=t,l[12]=c,l[13]=g,l[14]=p):p=l[14],p};function an(l){return typeof l=="object"&&l!==null&&!Array.isArray(l)?l:{}}export{pn as default};
//# sourceMappingURL=DeploymentListPage-DvvtGBrD.js.map
