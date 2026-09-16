import{i as fl,u as kl,bD as Dl,j as a,at as bl,aU as hl,l as Se,c as he,d as Cl,X as Ll,x as Tl,Y as Il,Z as Nl,bE as Pl,c8 as cl,ag as Rl,ae as Al,a7 as Ml,aN as xl,z as jl,W as Vl,aR as Bl,r as ml,aS as _l,al as wl,bg as Ol,cC as El,cz as Ul,bG as $l,aK as ql,aM as zl,N as gl,a2 as pl,L as Gl,ao as yl,bM as Ql}from"./index-DPebpL40.js";import{D as Wl,a as Hl}from"./DeploymentSettingModal-CWC6mALg.js";import{a as Jl,B as Yl}from"./BAIModelDeploymentNodes-l1D51jn_.js";import{B as Xl}from"./BAIGraphQLPropertyFilter-CPqP1l9W.js";import{i as Zl,B as en}from"./BAIDeploymentTagChips-zcg8l2YM.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-rZTSRFdj.js";import"./BAIId-oHD2WVBQ.js";import"./BooleanTag-DTKAExzX.js";import"./BAITag-dedPDMOM.js";const Fl=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"DeploymentListPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"DeploymentListPageDeleteMutation",selections:e},params:{cacheID:"4639cd2572faeb586296319d8202e23a",id:null,metadata:{},name:"DeploymentListPageDeleteMutation",operationKind:"mutation",text:`mutation DeploymentListPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();Fl.hash="867cc2a31d2fc3342a0bafe7502c0483";const Sl=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},k={defaultValue:null,kind:"LocalArgument",name:"offset"},D={defaultValue:null,kind:"LocalArgument",name:"orderBy"},n=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],c={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},p={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,i,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},P={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},Ke={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},T=[i,Ke];return{fragment:{argumentDefinitions:[l,e,k,D],kind:"Fragment",metadata:null,name:"DeploymentListPageQuery",selections:[{alias:null,args:n,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[c,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[i,d],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,m,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[l,D,e,k],kind:"Operation",name:"DeploymentListPageQuery",selections:[{alias:null,args:n,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[c,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},i,d,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},g,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[i],storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[c],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,m,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[p,P,L,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"subpath",storageKey:null}],storageKey:null},g,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:T,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[i,t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:T,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},Ke,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},t],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[P,L,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},p],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"command",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[t,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"08a0b04578ebf757b1a5fbecacbb0b4b",id:null,metadata:{},name:"DeploymentListPageQuery",operationKind:"query",text:`query DeploymentListPageQuery(
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
`}}})();Sl.hash="7e57808b70c4eb1aab4a7a4d8af607d7";const ln=l=>{"use memo";var rl,ol,ul;const e=fl.c(163),{isCreating:k,onCloseCreate:D}=l,{t:n}=kl(),{message:c}=Ll.useApp(),{logger:t}=Tl(),i=Il(),d=Nl(),[m,g]=Se.useState(null),[p,P]=Se.useState(null),[L,Ke]=Se.useState(null);let T;e[0]===Symbol.for("react.memo_cache_sentinel")?(T={current:1,pageSize:10},e[0]=T):T=e[0];const{baiPaginationOption:R,tablePaginationOption:A,setTablePaginationOption:F}=Pl(T);let Ce,Le;e[1]===Symbol.for("react.memo_cache_sentinel")?(Ce={filter:Rl(nn),order:cl(Jl),statusCategory:cl(["running","finished"]).withDefault("running")},Le={history:"replace"},e[1]=Ce,e[2]=Le):(Ce=e[1],Le=e[2]);const[u,S]=Al(Ce,Le),[qe,ze]=Ml("table_column_overrides.DeploymentListPage"),[ve,K]=xl(),I=jl();let Te;e[3]!==I?(Te=Vl(I),e[3]=I,e[4]=Te):Te=e[4];const Ie=Te;let Ne;e[5]!==u.order?(Ne=Bl(u.order),e[5]=u.order,e[6]=Ne):Ne=e[6];const Ge=Ne;let Pe;e[7]===Symbol.for("react.memo_cache_sentinel")?(Pe=["STOPPED"],e[7]=Pe):Pe=e[7];const tl=Pe;let Re;e[8]!==u.statusCategory?(Re=u.statusCategory==="finished"?{status:{in:tl}}:{status:{notIn:tl}},e[8]=u.statusCategory,e[9]=Re):Re=e[9];const Qe=Re;let Ae;e[10]!==I.id?(Ae=I.id?{projectId:{equals:I.id}}:{},e[10]=I.id,e[11]=Ae):Ae=e[11];const We=Ae;let M;e[12]!==u.filter?(M=u.filter??{},e[12]=u.filter,e[13]=M):M=e[13];let x;e[14]!==We||e[15]!==Qe||e[16]!==M?(x={...M,...Qe,...We},e[14]=We,e[15]=Qe,e[16]=M,e[17]=x):x=e[17];let Me;e[18]!==R.limit||e[19]!==R.offset||e[20]!==Ge||e[21]!==x?(Me={filter:x,orderBy:Ge,limit:R.limit,offset:R.offset},e[18]=R.limit,e[19]=R.offset,e[20]=Ge,e[21]=x,e[22]=Me):Me=e[22];const il=Me,sl=Se.useDeferredValue(il),De=Se.useDeferredValue(ve);let xe;e[23]===Symbol.for("react.memo_cache_sentinel")?(xe=Sl,e[23]=xe):xe=e[23];const He=De===Ol?"store-and-network":"network-only";let je;e[24]!==De||e[25]!==He?(je={fetchPolicy:He,fetchKey:De},e[24]=De,e[25]=He,e[26]=je):je=e[26];const{myDeployments:s}=ml.useLazyLoadQuery(xe,sl,je);let y,b,Ve,j;e[27]!==p||e[28]!==m||e[29]!==(s==null?void 0:s.count)||e[30]!==(s==null?void 0:s.edges)?(y=_l(wl(s==null?void 0:s.edges,"node")),j=(s==null?void 0:s.count)??0,b=m==null?null:y.find(r=>r.id===m)??null,Ve=p==null?null:y.find(r=>r.id===p)??null,e[27]=p,e[28]=m,e[29]=s==null?void 0:s.count,e[30]=s==null?void 0:s.edges,e[31]=y,e[32]=b,e[33]=Ve,e[34]=j):(y=e[31],b=e[32],Ve=e[33],j=e[34]);const o=Ve,V=sl!==il||De!==ve;let Be;e[35]===Symbol.for("react.memo_cache_sentinel")?(Be=Fl,e[35]=Be):Be=e[35];const[Je,Ye]=ml.useMutation(Be);let B;e[36]!==n?(B=n("deployment.filter.Name"),e[36]=n,e[37]=B):B=e[37];let _;e[38]!==B?(_={key:"name",propertyLabel:B,type:"string"},e[38]=B,e[39]=_):_=e[39];let w;e[40]!==n?(w=n("deployment.filter.Tags"),e[40]=n,e[41]=w):w=e[41];let O;e[42]!==w?(O={key:"tags",propertyLabel:w,type:"string"},e[42]=w,e[43]=O):O=e[43];let E;e[44]!==n?(E=n("deployment.filter.EndpointUrl"),e[44]=n,e[45]=E):E=e[45];let U;e[46]!==E?(U={key:"endpointUrl",propertyLabel:E,type:"string"},e[46]=E,e[47]=U):U=e[47];let $;e[48]!==n?($=n("deployment.filter.OpenToPublic"),e[48]=n,e[49]=$):$=e[49];let q;e[50]!==$?(q={key:"openToPublic",propertyLabel:$,type:"boolean"},e[50]=$,e[51]=q):q=e[51];let _e;e[52]!==_||e[53]!==O||e[54]!==U||e[55]!==q?(_e=[_,O,U,q],e[52]=_,e[53]=O,e[54]=U,e[55]=q,e[56]=_e):_e=e[56];const Xe=_e;let we;e[57]===Symbol.for("react.memo_cache_sentinel")?(we={flexShrink:1},e[57]=we):we=e[57];const Kl=u.statusCategory;let z;e[58]!==S||e[59]!==F?(z=r=>{S({statusCategory:r.target.value}),F({current:1})},e[58]=S,e[59]=F,e[60]=z):z=e[60];let G;e[61]!==n?(G=n("deployment.Running"),e[61]=n,e[62]=G):G=e[62];let Q;e[63]!==G?(Q={label:G,value:"running"},e[63]=G,e[64]=Q):Q=e[64];let W;e[65]!==n?(W=n("deployment.status.Terminated"),e[65]=n,e[66]=W):W=e[66];let H;e[67]!==W?(H={label:W,value:"finished"},e[67]=W,e[68]=H):H=e[68];let J;e[69]!==Q||e[70]!==H?(J=[Q,H],e[69]=Q,e[70]=H,e[71]=J):J=e[71];let Y;e[72]!==u.statusCategory||e[73]!==z||e[74]!==J?(Y=a.jsx(El,{value:Kl,onChange:z,options:J}),e[72]=u.statusCategory,e[73]=z,e[74]=J,e[75]=Y):Y=e[75];const Ze=u.filter??void 0;let X;e[76]!==S||e[77]!==F?(X=r=>{S({filter:r??null}),F({current:1})},e[76]=S,e[77]=F,e[78]=X):X=e[78];let Z;e[79]!==Xe||e[80]!==Ze||e[81]!==X?(Z=a.jsx(Xl,{filterProperties:Xe,value:Ze,onChange:X}),e[79]=Xe,e[80]=Ze,e[81]=X,e[82]=Z):Z=e[82];let ee;e[83]!==Y||e[84]!==Z?(ee=a.jsxs(he,{gap:"sm",align:"start",wrap:"wrap",style:we,children:[Y,Z]}),e[83]=Y,e[84]=Z,e[85]=ee):ee=e[85];let le;e[86]!==ve||e[87]!==V||e[88]!==K?(le=a.jsx(he,{gap:"xs",align:"center",children:a.jsx(Ul,{settingId:"deployment-list",defaultAutoUpdateDelay:15e3,value:ve,onChange:K,loading:V})}),e[86]=ve,e[87]=V,e[88]=K,e[89]=le):le=e[89];let ne;e[90]!==ee||e[91]!==le?(ne=a.jsxs(he,{justify:"between",wrap:"wrap",gap:"sm",children:[ee,le]}),e[90]=ee,e[91]=le,e[92]=ne):ne=e[92];let ae;e[93]!==S?(ae=r=>{S({order:r??null})},e[93]=S,e[94]=ae):ae=e[94];let te;e[95]!==F?(te=(r,N)=>{F({current:r,pageSize:N})},e[95]=F,e[96]=te):te=e[96];let ie;e[97]!==te||e[98]!==A.current||e[99]!==A.pageSize||e[100]!==j?(ie={current:A.current,pageSize:A.pageSize,total:j,onChange:te},e[97]=te,e[98]=A.current,e[99]=A.pageSize,e[100]=j,e[101]=ie):ie=e[101];let se;e[102]!==qe||e[103]!==ze?(se={columnOverrides:qe,onColumnOverridesChange:ze},e[102]=qe,e[103]=ze,e[104]=se):se=e[104];let re;e[105]!==d||e[106]!==y||e[107]!==n||e[108]!==i?(re=r=>{const N=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup"],vl=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt"]);return r.filter(f=>N.includes(f.key)).map(f=>{let be=f;return f.key==="name"?be={...f,render:(dl,v)=>{var C,$e;const h=Zl((C=v.metadata)==null?void 0:C.status);return a.jsx($l,{title:(($e=v.metadata)==null?void 0:$e.name)??"-",onTitleClick:()=>i(`${d("deployments")}/${gl(v.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:n("deployment.EditDeployment"),icon:a.jsx(ql,{}),disabled:h,onClick:()=>g(v.id)},{key:"delete",title:n("deployment.DeleteDeployment"),icon:a.jsx(zl,{size:"1em"}),type:"danger",disabled:h,onClick:()=>P(v.id)}]})}}:f.key==="currentRevisionNumber"?be={...f,render:(dl,v)=>{const h=y.find($e=>$e.id===v.id),C=h==null?void 0:h.currentRevision;return(C==null?void 0:C.revisionNumber)==null?a.jsx(pl,{color:"secondary",children:"-"}):a.jsx(Gl,{onClick:()=>Ke(C),children:`#${C.revisionNumber}`})}}:f.key==="tags"&&(be={...f,render:(dl,v)=>a.jsx(en,{metadataFrgmt:v.metadata,stopRowClick:!0,onTagClick:h=>{i({pathname:d("deployments"),search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:h}})}).toString()})},fallback:a.jsx(pl,{color:"secondary",children:"-"})})}),f.key==="name"?be:{...be,defaultHidden:!vl.has(f.key)}})},e[105]=d,e[106]=y,e[107]=n,e[108]=i,e[109]=re):re=e[109];let oe;e[110]!==y||e[111]!==V||e[112]!==u.order||e[113]!==ae||e[114]!==ie||e[115]!==se||e[116]!==re?(oe=a.jsx(Yl,{deploymentsFrgmt:y,loading:V,order:u.order,onChangeOrder:ae,pagination:ie,tableSettings:se,customizeColumns:re}),e[110]=y,e[111]=V,e[112]=u.order,e[113]=ae,e[114]=ie,e[115]=se,e[116]=re,e[117]=oe):oe=e[117];let ue;e[118]!==ne||e[119]!==oe?(ue=a.jsxs(he,{direction:"column",align:"stretch",gap:"sm",children:[ne,oe]}),e[118]=ne,e[119]=oe,e[120]=ue):ue=e[120];let de;e[121]!==b||e[122]!==k||e[123]!==D||e[124]!==Ie||e[125]!==K?(de=Ie!=null&&a.jsx(yl,{children:a.jsx(Wl,{open:k||!!b,deploymentFrgmt:b??null,project:Ie,onRequestClose:r=>{D(),g(null),r&&!b&&K()}})}),e[121]=b,e[122]=k,e[123]=D,e[124]=Ie,e[125]=K,e[126]=de):de=e[126];const el=!!o;let ce;e[127]!==n?(ce=n("deployment.DeleteDeployment"),e[127]=n,e[128]=ce):ce=e[128];let me;e[129]!==n?(me=n("deployment.Deployment"),e[129]=n,e[130]=me):me=e[130];let ge;e[131]!==o?(ge=o?[{key:o.id,label:((rl=o.metadata)==null?void 0:rl.name)??""}]:[],e[131]=o,e[132]=ge):ge=e[132];const ll=((ol=o==null?void 0:o.metadata)==null?void 0:ol.name)??"",nl=((ul=o==null?void 0:o.metadata)==null?void 0:ul.name)??"";let pe;e[133]!==nl?(pe={placeholder:nl},e[133]=nl,e[134]=pe):pe=e[134];let ye;e[135]!==Ye?(ye={loading:Ye},e[135]=Ye,e[136]=ye):ye=e[136];let fe;e[137]!==Je||e[138]!==o||e[139]!==t||e[140]!==c||e[141]!==n||e[142]!==K?(fe=()=>{o&&Je({variables:{input:{id:gl(o.id)??o.id}},onCompleted:(r,N)=>{if(N&&N.length>0){t.error("Failed to delete deployment",N),c.error(n("deployment.FailedToDeleteDeployment"));return}c.success(n("deployment.DeploymentDeleted")),P(null),K()},onError:r=>{t.error("Failed to delete deployment",r),c.error(n("deployment.FailedToDeleteDeployment"))}})},e[137]=Je,e[138]=o,e[139]=t,e[140]=c,e[141]=n,e[142]=K,e[143]=fe):fe=e[143];let Oe;e[144]===Symbol.for("react.memo_cache_sentinel")?(Oe=()=>P(null),e[144]=Oe):Oe=e[144];let ke;e[145]!==el||e[146]!==ce||e[147]!==me||e[148]!==ge||e[149]!==ll||e[150]!==pe||e[151]!==ye||e[152]!==fe?(ke=a.jsx(Ql,{open:el,title:ce,target:me,items:ge,confirmText:ll,requireConfirmInput:!0,inputProps:pe,okButtonProps:ye,onOk:fe,onCancel:Oe}),e[145]=el,e[146]=ce,e[147]=me,e[148]=ge,e[149]=ll,e[150]=pe,e[151]=ye,e[152]=fe,e[153]=ke):ke=e[153];const al=!!L;let Ee;e[154]===Symbol.for("react.memo_cache_sentinel")?(Ee=()=>Ke(null),e[154]=Ee):Ee=e[154];let Fe;e[155]!==L||e[156]!==al?(Fe=a.jsx(yl,{children:a.jsx(Hl,{open:al,revisionFrgmt:L,onClose:Ee})}),e[155]=L,e[156]=al,e[157]=Fe):Fe=e[157];let Ue;return e[158]!==ue||e[159]!==de||e[160]!==ke||e[161]!==Fe?(Ue=a.jsxs(a.Fragment,{children:[ue,de,ke,Fe]}),e[158]=ue,e[159]=de,e[160]=ke,e[161]=Fe,e[162]=Ue):Ue=e[162],Ue},pn=()=>{"use memo";const l=fl.c(15),{t:e}=kl(),[k,D]=Dl(!1),{setLeft:n,setRight:c}=D;let t;l[0]!==e?(t=e("webui.menu.Deployments"),l[0]=e,l[1]=t):t=l[1];let i;l[2]!==e?(i=e("deployment.CreateDeployment"),l[2]=e,l[3]=i):i=l[3];let d;l[4]!==c||l[5]!==i?(d=a.jsx(bl,{variant:"primary",label:i,onClick:c}),l[4]=c,l[5]=i,l[6]=d):d=l[6];let m;l[7]===Symbol.for("react.memo_cache_sentinel")?(m=a.jsx(hl,{}),l[7]=m):m=l[7];let g;l[8]!==n||l[9]!==k?(g=a.jsx(Se.Suspense,{fallback:m,children:a.jsx(ln,{isCreating:k,onCloseCreate:n})}),l[8]=n,l[9]=k,l[10]=g):g=l[10];let p;return l[11]!==t||l[12]!==d||l[13]!==g?(p=a.jsx(he,{direction:"column",align:"stretch",gap:"md",children:a.jsx(Cl,{variant:"borderless",title:t,extra:d,children:g})}),l[11]=t,l[12]=d,l[13]=g,l[14]=p):p=l[14],p};function nn(l){return typeof l=="object"&&l!==null&&!Array.isArray(l)?l:{}}export{pn as default};
//# sourceMappingURL=DeploymentListPage-BLRu82CZ.js.map
