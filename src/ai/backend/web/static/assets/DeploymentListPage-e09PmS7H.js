import{k as vl,u as Dl,j as n,r as Ke,aM as Tl,B as Te,G as Il,J as Nl,H as Pl,a0 as Rl,a1 as Al,p as Ml,b9 as xl,bD as kl,an as Vl,al as jl,ab as _l,aH as Bl,L as wl,c2 as Ol,l as Fl,a_ as El,as as Ul,aK as $l,c8 as ql,c1 as Gl,v as Ql,ba as zl,bb as Hl,V as Sl,T as ul,w as Kl,de as Jl,bj as Wl}from"./index-CrFvxZIN.js";import{i as Yl,B as Xl,D as Zl}from"./DeploymentRevisionDetailDrawer-CoGWrqnO.js";import{a as en,B as ln}from"./BAIModelDeploymentNodes-DkSgbwhz.js";import{B as nn}from"./BAIGraphQLPropertyFilter-Nw6tLZrH.js";import{S as an}from"./square-pen-CbJIrIOh.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-BO0tWhos.js";import"./BAIId-DDwepSJA.js";import"./BooleanTag-By_86yqr.js";const bl=(function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"input"}],l=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"DeploymentListPageDeleteMutation",selections:l,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"DeploymentListPageDeleteMutation",selections:l},params:{cacheID:"4639cd2572faeb586296319d8202e23a",id:null,metadata:{},name:"DeploymentListPageDeleteMutation",operationKind:"mutation",text:`mutation DeploymentListPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();bl.hash="867cc2a31d2fc3342a0bafe7502c0483";const hl=(function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},l={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},u={defaultValue:null,kind:"LocalArgument",name:"orderBy"},d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},ve={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[c,p,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},D={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},De=[p,b];return{fragment:{argumentDefinitions:[e,l,r,u],kind:"Fragment",metadata:null,name:"DeploymentListPageQuery",selections:[{alias:null,args:d,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[c,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[p,C],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[c,L,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,u,l,r],kind:"Operation",name:"DeploymentListPageQuery",selections:[{alias:null,args:d,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},p,C,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},v,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[p],storageKey:null},c],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[o],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[c,L,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[ve,D,T,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},v,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:De,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[p,c],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:De,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},b,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},c],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[D,T,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},ve],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[c,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[c,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"4e6b325179329c7c916583ab20770756",id:null,metadata:{},name:"DeploymentListPageQuery",operationKind:"query",text:`query DeploymentListPageQuery(
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
`}}})();hl.hash="7e57808b70c4eb1aab4a7a4d8af607d7";const tn=()=>{"use memo";var gl,pl,yl;const e=vl.c(170),{t:l}=Dl(),{message:r}=Nl.useApp(),{logger:u}=Pl(),d=Rl(),o=Al(),[c,p]=Ml(!1),{setLeft:C,setRight:L}=p,[v,ve]=Ke.useState(null),[D,T]=Ke.useState(null),[b,De]=Ke.useState(null);let Ie;e[0]===Symbol.for("react.memo_cache_sentinel")?(Ie={current:1,pageSize:10},e[0]=Ie):Ie=e[0];const{baiPaginationOption:I,tablePaginationOption:N,setTablePaginationOption:y}=xl(Ie);let Ne,Pe;e[1]===Symbol.for("react.memo_cache_sentinel")?(Ne={filter:Vl(sn),order:kl(en),statusCategory:kl(["running","finished"]).withDefault("running")},Pe={history:"replace"},e[1]=Ne,e[2]=Pe):(Ne=e[1],Pe=e[2]);const[s,f]=jl(Ne,Pe),[ze,He]=_l("table_column_overrides.DeploymentListPage"),[be,k]=Bl(),Re=wl();let Ae;e[3]!==s.order?(Ae=Ol(s.order),e[3]=s.order,e[4]=Ae):Ae=e[4];const Je=Ae;let Me;e[5]===Symbol.for("react.memo_cache_sentinel")?(Me=["STOPPED"],e[5]=Me):Me=e[5];const dl=Me;let xe;e[6]!==s.statusCategory?(xe=s.statusCategory==="finished"?{status:{in:dl}}:{status:{notIn:dl}},e[6]=s.statusCategory,e[7]=xe):xe=e[7];const We=xe;let Ve;e[8]!==Re.id?(Ve=Re.id?{projectId:{equals:Re.id}}:{},e[8]=Re.id,e[9]=Ve):Ve=e[9];const Ye=Ve;let P;e[10]!==s.filter?(P=s.filter??{},e[10]=s.filter,e[11]=P):P=e[11];let R;e[12]!==Ye||e[13]!==We||e[14]!==P?(R={...P,...We,...Ye},e[12]=Ye,e[13]=We,e[14]=P,e[15]=R):R=e[15];let je;e[16]!==I.limit||e[17]!==I.offset||e[18]!==Je||e[19]!==R?(je={filter:R,orderBy:Je,limit:I.limit,offset:I.offset},e[16]=I.limit,e[17]=I.offset,e[18]=Je,e[19]=R,e[20]=je):je=e[20];const cl=je,ml=Ke.useDeferredValue(cl),he=Ke.useDeferredValue(be);let _e;e[21]===Symbol.for("react.memo_cache_sentinel")?(_e=hl,e[21]=_e):_e=e[21];const Xe=he===$l?"store-and-network":"network-only";let Be;e[22]!==he||e[23]!==Xe?(Be={fetchPolicy:Xe,fetchKey:he},e[22]=he,e[23]=Xe,e[24]=Be):Be=e[24];const{myDeployments:a}=Fl.useLazyLoadQuery(_e,ml,Be);let m,Ce,we,A;e[25]!==D||e[26]!==v||e[27]!==(a==null?void 0:a.count)||e[28]!==(a==null?void 0:a.edges)?(m=El(Ul(a==null?void 0:a.edges,"node")),A=(a==null?void 0:a.count)??0,Ce=v==null?null:m.find(t=>t.id===v)??null,we=D==null?null:m.find(t=>t.id===D)??null,e[25]=D,e[26]=v,e[27]=a==null?void 0:a.count,e[28]=a==null?void 0:a.edges,e[29]=m,e[30]=Ce,e[31]=we,e[32]=A):(m=e[29],Ce=e[30],we=e[31],A=e[32]);const i=we,M=ml!==cl||he!==be;let Oe;e[33]===Symbol.for("react.memo_cache_sentinel")?(Oe=bl,e[33]=Oe):Oe=e[33];const[Ze,el]=Fl.useMutation(Oe);let x;e[34]!==l?(x=l("deployment.filter.Name"),e[34]=l,e[35]=x):x=e[35];let V;e[36]!==x?(V={key:"name",propertyLabel:x,type:"string"},e[36]=x,e[37]=V):V=e[37];let j;e[38]!==l?(j=l("deployment.filter.Tags"),e[38]=l,e[39]=j):j=e[39];let _;e[40]!==j?(_={key:"tags",propertyLabel:j,type:"string"},e[40]=j,e[41]=_):_=e[41];let B;e[42]!==l?(B=l("deployment.filter.EndpointUrl"),e[42]=l,e[43]=B):B=e[43];let w;e[44]!==B?(w={key:"endpointUrl",propertyLabel:B,type:"string"},e[44]=B,e[45]=w):w=e[45];let O;e[46]!==l?(O=l("deployment.filter.OpenToPublic"),e[46]=l,e[47]=O):O=e[47];let E;e[48]!==O?(E={key:"openToPublic",propertyLabel:O,type:"boolean"},e[48]=O,e[49]=E):E=e[49];let Ee;e[50]!==V||e[51]!==_||e[52]!==w||e[53]!==E?(Ee=[V,_,w,E],e[50]=V,e[51]=_,e[52]=w,e[53]=E,e[54]=Ee):Ee=e[54];const ll=Ee;let Ue;e[55]===Symbol.for("react.memo_cache_sentinel")?(Ue={flexShrink:1},e[55]=Ue):Ue=e[55];const Cl=s.statusCategory;let U;e[56]!==f||e[57]!==y?(U=t=>{f({statusCategory:t.target.value}),y({current:1})},e[56]=f,e[57]=y,e[58]=U):U=e[58];let $;e[59]!==l?($=l("deployment.Running"),e[59]=l,e[60]=$):$=e[60];let q;e[61]!==$?(q={label:$,value:"running"},e[61]=$,e[62]=q):q=e[62];let G;e[63]!==l?(G=l("deployment.status.Terminated"),e[63]=l,e[64]=G):G=e[64];let Q;e[65]!==G?(Q={label:G,value:"finished"},e[65]=G,e[66]=Q):Q=e[66];let z;e[67]!==q||e[68]!==Q?(z=[q,Q],e[67]=q,e[68]=Q,e[69]=z):z=e[69];let H;e[70]!==s.statusCategory||e[71]!==U||e[72]!==z?(H=n.jsx(ql,{value:Cl,onChange:U,options:z}),e[70]=s.statusCategory,e[71]=U,e[72]=z,e[73]=H):H=e[73];const nl=s.filter??void 0;let J;e[74]!==f||e[75]!==y?(J=t=>{f({filter:t??null}),y({current:1})},e[74]=f,e[75]=y,e[76]=J):J=e[76];let W;e[77]!==ll||e[78]!==nl||e[79]!==J?(W=n.jsx(nn,{filterProperties:ll,value:nl,onChange:J}),e[77]=ll,e[78]=nl,e[79]=J,e[80]=W):W=e[80];let Y;e[81]!==H||e[82]!==W?(Y=n.jsxs(Te,{gap:"sm",align:"start",wrap:"wrap",style:Ue,children:[H,W]}),e[81]=H,e[82]=W,e[83]=Y):Y=e[83];let X;e[84]!==be||e[85]!==M||e[86]!==k?(X=n.jsx(Gl,{settingId:"deployment-list",defaultAutoUpdateDelay:15e3,value:be,onChange:k,loading:M}),e[84]=be,e[85]=M,e[86]=k,e[87]=X):X=e[87];let Z;e[88]!==l?(Z=l("deployment.CreateDeployment"),e[88]=l,e[89]=Z):Z=e[89];let ee;e[90]!==L||e[91]!==Z?(ee=n.jsx(Ql,{type:"primary",onClick:L,children:Z}),e[90]=L,e[91]=Z,e[92]=ee):ee=e[92];let le;e[93]!==X||e[94]!==ee?(le=n.jsxs(Te,{gap:"xs",align:"center",children:[X,ee]}),e[93]=X,e[94]=ee,e[95]=le):le=e[95];let ne;e[96]!==Y||e[97]!==le?(ne=n.jsxs(Te,{justify:"between",wrap:"wrap",gap:"sm",children:[Y,le]}),e[96]=Y,e[97]=le,e[98]=ne):ne=e[98];let ae;e[99]!==f?(ae=t=>{f({order:t??null})},e[99]=f,e[100]=ae):ae=e[100];let te;e[101]!==y?(te=(t,h)=>{y({current:t,pageSize:h})},e[101]=y,e[102]=te):te=e[102];let ie;e[103]!==te||e[104]!==N.current||e[105]!==N.pageSize||e[106]!==A?(ie={current:N.current,pageSize:N.pageSize,total:A,onChange:te},e[103]=te,e[104]=N.current,e[105]=N.pageSize,e[106]=A,e[107]=ie):ie=e[107];let se;e[108]!==ze||e[109]!==He?(se={columnOverrides:ze,onColumnOverridesChange:He},e[108]=ze,e[109]=He,e[110]=se):se=e[110];let re;e[111]!==o||e[112]!==m||e[113]!==l||e[114]!==d?(re=t=>{const h=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup"],Ll=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt"]);return t.filter(g=>h.includes(g.key)).map(g=>{let Le=g;return g.key==="name"?Le={...g,render:(fl,F)=>{var K,Qe;const S=Yl((K=F.metadata)==null?void 0:K.status);return n.jsx(zl,{title:((Qe=F.metadata)==null?void 0:Qe.name)??"-",onTitleClick:()=>d(`${o("deployments")}/${Sl(F.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:n.jsx(an,{}),disabled:S,onClick:()=>ve(F.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:n.jsx(Hl,{}),type:"danger",disabled:S,onClick:()=>T(F.id)}]})}}:g.key==="currentRevisionNumber"?Le={...g,render:(fl,F)=>{const S=m.find(Qe=>Qe.id===F.id),K=S==null?void 0:S.currentRevision;return(K==null?void 0:K.revisionNumber)==null?n.jsx(ul.Text,{type:"secondary",children:"-"}):n.jsx(ul.Link,{onClick:()=>De(K),children:`#${K.revisionNumber}`})}}:g.key==="tags"&&(Le={...g,render:(fl,F)=>n.jsx(Xl,{metadataFrgmt:F.metadata,stopRowClick:!0,onTagClick:S=>{d({pathname:o("deployments"),search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:S}})}).toString()})},fallback:n.jsx(ul.Text,{type:"secondary",children:"-"})})}),g.key==="name"?Le:{...Le,defaultHidden:!Ll.has(g.key)}})},e[111]=o,e[112]=m,e[113]=l,e[114]=d,e[115]=re):re=e[115];let oe;e[116]!==m||e[117]!==M||e[118]!==s.order||e[119]!==ae||e[120]!==ie||e[121]!==se||e[122]!==re?(oe=n.jsx(ln,{deploymentsFrgmt:m,loading:M,order:s.order,onChangeOrder:ae,pagination:ie,tableSettings:se,customizeColumns:re}),e[116]=m,e[117]=M,e[118]=s.order,e[119]=ae,e[120]=ie,e[121]=se,e[122]=re,e[123]=oe):oe=e[123];let ue;e[124]!==ne||e[125]!==oe?(ue=n.jsxs(Te,{direction:"column",align:"stretch",gap:"sm",children:[ne,oe]}),e[124]=ne,e[125]=oe,e[126]=ue):ue=e[126];const al=c||!!Ce,tl=Ce??null;let de;e[127]!==C||e[128]!==k?(de=t=>{C(),ve(null),t&&k()},e[127]=C,e[128]=k,e[129]=de):de=e[129];let ce;e[130]!==al||e[131]!==tl||e[132]!==de?(ce=n.jsx(Kl,{children:n.jsx(Jl,{open:al,deploymentFrgmt:tl,onRequestClose:de})}),e[130]=al,e[131]=tl,e[132]=de,e[133]=ce):ce=e[133];const il=!!i;let me;e[134]!==l?(me=l("deployment.DeleteDeployment"),e[134]=l,e[135]=me):me=e[135];let ge;e[136]!==l?(ge=l("deployment.Deployment"),e[136]=l,e[137]=ge):ge=e[137];let pe;e[138]!==i?(pe=i?[{key:i.id,label:((gl=i.metadata)==null?void 0:gl.name)??""}]:[],e[138]=i,e[139]=pe):pe=e[139];const sl=((pl=i==null?void 0:i.metadata)==null?void 0:pl.name)??"",rl=((yl=i==null?void 0:i.metadata)==null?void 0:yl.name)??"";let ye;e[140]!==rl?(ye={placeholder:rl},e[140]=rl,e[141]=ye):ye=e[141];let fe;e[142]!==el?(fe={loading:el},e[142]=el,e[143]=fe):fe=e[143];let ke;e[144]!==Ze||e[145]!==i||e[146]!==u||e[147]!==r||e[148]!==l||e[149]!==k?(ke=()=>{i&&Ze({variables:{input:{id:Sl(i.id)??i.id}},onCompleted:(t,h)=>{if(h&&h.length>0){u.error("Failed to delete deployment",h),r.error(l("deployment.FailedToDeleteDeployment"));return}r.success(l("deployment.DeploymentDeleted")),T(null),k()},onError:t=>{u.error("Failed to delete deployment",t),r.error(l("deployment.FailedToDeleteDeployment"))}})},e[144]=Ze,e[145]=i,e[146]=u,e[147]=r,e[148]=l,e[149]=k,e[150]=ke):ke=e[150];let $e;e[151]===Symbol.for("react.memo_cache_sentinel")?($e=()=>T(null),e[151]=$e):$e=e[151];let Fe;e[152]!==il||e[153]!==me||e[154]!==ge||e[155]!==pe||e[156]!==sl||e[157]!==ye||e[158]!==fe||e[159]!==ke?(Fe=n.jsx(Wl,{open:il,title:me,target:ge,items:pe,confirmText:sl,requireConfirmInput:!0,inputProps:ye,okButtonProps:fe,onOk:ke,onCancel:$e}),e[152]=il,e[153]=me,e[154]=ge,e[155]=pe,e[156]=sl,e[157]=ye,e[158]=fe,e[159]=ke,e[160]=Fe):Fe=e[160];const ol=!!b;let qe;e[161]===Symbol.for("react.memo_cache_sentinel")?(qe=()=>De(null),e[161]=qe):qe=e[161];let Se;e[162]!==b||e[163]!==ol?(Se=n.jsx(Kl,{children:n.jsx(Zl,{open:ol,revisionFrgmt:b,onClose:qe})}),e[162]=b,e[163]=ol,e[164]=Se):Se=e[164];let Ge;return e[165]!==ue||e[166]!==ce||e[167]!==Fe||e[168]!==Se?(Ge=n.jsxs(n.Fragment,{children:[ue,ce,Fe,Se]}),e[165]=ue,e[166]=ce,e[167]=Fe,e[168]=Se,e[169]=Ge):Ge=e[169],Ge},fn=()=>{"use memo";const e=vl.c(6),{t:l}=Dl();let r;e[0]!==l?(r=l("webui.menu.Deployments"),e[0]=l,e[1]=r):r=e[1];let u;e[2]===Symbol.for("react.memo_cache_sentinel")?(u={body:{paddingTop:0}},e[2]=u):u=e[2];let d;e[3]===Symbol.for("react.memo_cache_sentinel")?(d=n.jsx(Ke.Suspense,{fallback:n.jsx(Tl,{active:!0}),children:n.jsx(tn,{})}),e[3]=d):d=e[3];let o;return e[4]!==r?(o=n.jsx(Te,{direction:"column",align:"stretch",gap:"md",children:n.jsx(Il,{variant:"borderless",title:r,styles:u,children:d})}),e[4]=r,e[5]=o):o=e[5],o};function sn(e){return typeof e=="object"&&e!==null&&!Array.isArray(e)?e:{}}export{fn as default};
//# sourceMappingURL=DeploymentListPage-e09PmS7H.js.map
