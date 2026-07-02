import{h as bl,u as hl,j as n,r as Se,aw as Nl,B as Te,bI as Rl,A as Al,v as Ml,p as xl,aV as Pl,bs as Vl,bt as Sl,c$ as jl,bu as _l,a4 as Bl,ar as wl,aj as Ol,i as Kl,aK as El,a6 as $l,au as Ul,c1 as ql,aA as Ql,b2 as zl,aX as Gl,d0 as Hl,aZ as Wl,N as vl,T as cl,a7 as Dl,d1 as Jl,b7 as Xl}from"./index-DLl5_15D.js";import{i as Yl,B as Zl,D as en}from"./DeploymentRevisionDetailDrawer-yvw1W0py.js";import{p as ln,B as nn,a as an}from"./BAIModelDeploymentNodes-qJmGIh6-.js";import{B as tn}from"./BAIGraphQLPropertyFilter-BVY69KXO.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-C2HMK66Z.js";import"./BAIId-CUEnOS4w.js";import"./BooleanTag-Ca7dIHjt.js";const Cl=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"input"}],l=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"DeploymentListPageDeleteMutation",selections:l,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"DeploymentListPageDeleteMutation",selections:l},params:{cacheID:"4639cd2572faeb586296319d8202e23a",id:null,metadata:{},name:"DeploymentListPageDeleteMutation",operationKind:"mutation",text:`mutation DeploymentListPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}}();Cl.hash="867cc2a31d2fc3342a0bafe7502c0483";const Ll=function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},l={defaultValue:null,kind:"LocalArgument",name:"limit"},r={defaultValue:null,kind:"LocalArgument",name:"offset"},o={defaultValue:null,kind:"LocalArgument",name:"orderBy"},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],p={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},Ke={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},D={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[d,c,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},T={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},ve={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},h=[c,ve];return{fragment:{argumentDefinitions:[e,l,r,o],kind:"Fragment",metadata:null,name:"DeploymentListPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[p,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[d,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[c,L],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[d,v,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,o,l,r],kind:"Operation",name:"DeploymentListPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[p,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},c,L,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},Ke,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[c],storageKey:null},d],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[p],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[d,v,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[D,T,b,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},Ke,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:h,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[c,d],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:h,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},ve,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},d],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[T,b,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},D],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[d,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[d,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"4e6b325179329c7c916583ab20770756",id:null,metadata:{},name:"DeploymentListPageQuery",operationKind:"query",text:`query DeploymentListPageQuery(
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
`}}}();Ll.hash="7e57808b70c4eb1aab4a7a4d8af607d7";const sn=()=>{"use memo";var yl,fl,kl;const e=bl.c(171),{t:l}=hl(),{message:r}=Al.useApp(),{logger:o}=Ml(),u=xl(),[p,d]=Pl(!1),{setLeft:c,setRight:L}=d,[v,Ke]=Se.useState(null),[D,T]=Se.useState(null),[b,ve]=Se.useState(null);let h;e[0]===Symbol.for("react.memo_cache_sentinel")?(h={current:1,pageSize:10},e[0]=h):h=e[0];const{baiPaginationOption:I,tablePaginationOption:N,setTablePaginationOption:y}=Vl(h);let Ie,Ne;e[1]===Symbol.for("react.memo_cache_sentinel")?(Ie={filter:jl(rn),order:Sl(an),statusCategory:Sl(["running","finished"]).withDefault("running")},Ne={history:"replace"},e[1]=Ie,e[2]=Ne):(Ie=e[1],Ne=e[2]);const[s,f]=_l(Ie,Ne),[He,We]=Bl("table_column_overrides.DeploymentListPage"),[De,k]=wl(),Re=Ol();let Ae;e[3]!==s.order?(Ae=ln(s.order),e[3]=s.order,e[4]=Ae):Ae=e[4];const be=Ae;let Me;e[5]!==be?(Me=be?[{field:be.field,direction:be.direction}]:void 0,e[5]=be,e[6]=Me):Me=e[6];const Je=Me;let xe;e[7]===Symbol.for("react.memo_cache_sentinel")?(xe=["STOPPED"],e[7]=xe):xe=e[7];const ml=xe;let Pe;e[8]!==s.statusCategory?(Pe=s.statusCategory==="finished"?{status:{in:ml}}:{status:{notIn:ml}},e[8]=s.statusCategory,e[9]=Pe):Pe=e[9];const Xe=Pe;let Ve;e[10]!==Re.id?(Ve=Re.id?{projectId:{equals:Re.id}}:{},e[10]=Re.id,e[11]=Ve):Ve=e[11];const Ye=Ve;let je;e[12]!==s.filter?(je=s.filter??{},e[12]=s.filter,e[13]=je):je=e[13];const Ze=je;let R;e[14]!==Ye||e[15]!==Xe||e[16]!==Ze?(R={...Ze,...Xe,...Ye},e[14]=Ye,e[15]=Xe,e[16]=Ze,e[17]=R):R=e[17];let _e;e[18]!==I.limit||e[19]!==I.offset||e[20]!==Je||e[21]!==R?(_e={filter:R,orderBy:Je,limit:I.limit,offset:I.offset},e[18]=I.limit,e[19]=I.offset,e[20]=Je,e[21]=R,e[22]=_e):_e=e[22];const gl=_e,pl=Se.useDeferredValue(gl),he=Se.useDeferredValue(De);let Be;e[23]===Symbol.for("react.memo_cache_sentinel")?(Be=Ll,e[23]=Be):Be=e[23];const el=he===Ul?"store-and-network":"network-only";let we;e[24]!==he||e[25]!==el?(we={fetchPolicy:el,fetchKey:he},e[24]=he,e[25]=el,e[26]=we):we=e[26];const{myDeployments:a}=Kl.useLazyLoadQuery(Be,pl,we);let m,Ce,Oe,A;e[27]!==D||e[28]!==v||e[29]!==(a==null?void 0:a.count)||e[30]!==(a==null?void 0:a.edges)?(m=El($l(a==null?void 0:a.edges,"node")),A=(a==null?void 0:a.count)??0,Ce=v==null?null:m.find(t=>t.id===v)??null,Oe=D==null?null:m.find(t=>t.id===D)??null,e[27]=D,e[28]=v,e[29]=a==null?void 0:a.count,e[30]=a==null?void 0:a.edges,e[31]=m,e[32]=Ce,e[33]=Oe,e[34]=A):(m=e[31],Ce=e[32],Oe=e[33],A=e[34]);const i=Oe,M=pl!==gl||he!==De;let Ee;e[35]===Symbol.for("react.memo_cache_sentinel")?(Ee=Cl,e[35]=Ee):Ee=e[35];const[ll,nl]=Kl.useMutation(Ee);let x;e[36]!==l?(x=l("deployment.filter.Name"),e[36]=l,e[37]=x):x=e[37];let P;e[38]!==x?(P={key:"name",propertyLabel:x,type:"string"},e[38]=x,e[39]=P):P=e[39];let V;e[40]!==l?(V=l("deployment.filter.Tags"),e[40]=l,e[41]=V):V=e[41];let j;e[42]!==V?(j={key:"tags",propertyLabel:V,type:"string"},e[42]=V,e[43]=j):j=e[43];let _;e[44]!==l?(_=l("deployment.filter.EndpointUrl"),e[44]=l,e[45]=_):_=e[45];let B;e[46]!==_?(B={key:"endpointUrl",propertyLabel:_,type:"string"},e[46]=_,e[47]=B):B=e[47];let w;e[48]!==l?(w=l("deployment.filter.OpenToPublic"),e[48]=l,e[49]=w):w=e[49];let O;e[50]!==w?(O={key:"openToPublic",propertyLabel:w,type:"boolean"},e[50]=w,e[51]=O):O=e[51];let $e;e[52]!==P||e[53]!==j||e[54]!==B||e[55]!==O?($e=[P,j,B,O],e[52]=P,e[53]=j,e[54]=B,e[55]=O,e[56]=$e):$e=e[56];const al=$e;let Ue;e[57]===Symbol.for("react.memo_cache_sentinel")?(Ue={flexShrink:1},e[57]=Ue):Ue=e[57];const Tl=s.statusCategory;let E;e[58]!==f||e[59]!==y?(E=t=>{f({statusCategory:t.target.value}),y({current:1})},e[58]=f,e[59]=y,e[60]=E):E=e[60];let $;e[61]!==l?($=l("deployment.Running"),e[61]=l,e[62]=$):$=e[62];let U;e[63]!==$?(U={label:$,value:"running"},e[63]=$,e[64]=U):U=e[64];let q;e[65]!==l?(q=l("deployment.status.Terminated"),e[65]=l,e[66]=q):q=e[66];let Q;e[67]!==q?(Q={label:q,value:"finished"},e[67]=q,e[68]=Q):Q=e[68];let z;e[69]!==U||e[70]!==Q?(z=[U,Q],e[69]=U,e[70]=Q,e[71]=z):z=e[71];let G;e[72]!==s.statusCategory||e[73]!==E||e[74]!==z?(G=n.jsx(ql,{value:Tl,onChange:E,options:z}),e[72]=s.statusCategory,e[73]=E,e[74]=z,e[75]=G):G=e[75];const tl=s.filter??void 0;let H;e[76]!==f||e[77]!==y?(H=t=>{f({filter:t??null}),y({current:1})},e[76]=f,e[77]=y,e[78]=H):H=e[78];let W;e[79]!==al||e[80]!==tl||e[81]!==H?(W=n.jsx(tn,{filterProperties:al,value:tl,onChange:H}),e[79]=al,e[80]=tl,e[81]=H,e[82]=W):W=e[82];let J;e[83]!==G||e[84]!==W?(J=n.jsxs(Te,{gap:"sm",align:"start",wrap:"wrap",style:Ue,children:[G,W]}),e[83]=G,e[84]=W,e[85]=J):J=e[85];let X;e[86]!==De||e[87]!==M||e[88]!==k?(X=n.jsx(Ql,{autoUpdateDelay:15e3,value:De,onChange:k,loading:M}),e[86]=De,e[87]=M,e[88]=k,e[89]=X):X=e[89];let Y;e[90]!==l?(Y=l("deployment.CreateDeployment"),e[90]=l,e[91]=Y):Y=e[91];let Z;e[92]!==L||e[93]!==Y?(Z=n.jsx(zl,{type:"primary",onClick:L,children:Y}),e[92]=L,e[93]=Y,e[94]=Z):Z=e[94];let ee;e[95]!==X||e[96]!==Z?(ee=n.jsxs(Te,{gap:"xs",align:"center",children:[X,Z]}),e[95]=X,e[96]=Z,e[97]=ee):ee=e[97];let le;e[98]!==J||e[99]!==ee?(le=n.jsxs(Te,{justify:"between",wrap:"wrap",gap:"sm",children:[J,ee]}),e[98]=J,e[99]=ee,e[100]=le):le=e[100];let ne;e[101]!==f?(ne=t=>{f({order:t??null})},e[101]=f,e[102]=ne):ne=e[102];let ae;e[103]!==y?(ae=(t,C)=>{y({current:t,pageSize:C})},e[103]=y,e[104]=ae):ae=e[104];let te;e[105]!==ae||e[106]!==N.current||e[107]!==N.pageSize||e[108]!==A?(te={current:N.current,pageSize:N.pageSize,total:A,onChange:ae},e[105]=ae,e[106]=N.current,e[107]=N.pageSize,e[108]=A,e[109]=te):te=e[109];let ie;e[110]!==He||e[111]!==We?(ie={columnOverrides:He,onColumnOverridesChange:We},e[110]=He,e[111]=We,e[112]=ie):ie=e[112];let se;e[113]!==m||e[114]!==l||e[115]!==u?(se=t=>{const C=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup"],Il=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt"]);return t.filter(g=>C.includes(g.key)).map(g=>{let Le=g;return g.key==="name"?Le={...g,render:(Fl,F)=>{var K,Ge;const S=Yl((K=F.metadata)==null?void 0:K.status);return n.jsx(Gl,{title:((Ge=F.metadata)==null?void 0:Ge.name)??"-",onTitleClick:()=>u(`/deployments/${vl(F.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:n.jsx(Hl,{}),disabled:S,onClick:()=>Ke(F.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:n.jsx(Wl,{}),type:"danger",disabled:S,onClick:()=>T(F.id)}]})}}:g.key==="currentRevisionNumber"?Le={...g,render:(Fl,F)=>{const S=m.find(Ge=>Ge.id===F.id),K=S==null?void 0:S.currentRevision;return(K==null?void 0:K.revisionNumber)==null?n.jsx(cl.Text,{type:"secondary",children:"-"}):n.jsx(cl.Link,{onClick:()=>ve(K),children:`#${K.revisionNumber}`})}}:g.key==="tags"&&(Le={...g,render:(Fl,F)=>n.jsx(Zl,{metadataFrgmt:F.metadata,stopRowClick:!0,onTagClick:S=>{u({pathname:"/deployments",search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:S}})}).toString()})},fallback:n.jsx(cl.Text,{type:"secondary",children:"-"})})}),g.key==="name"?Le:{...Le,defaultHidden:!Il.has(g.key)}})},e[113]=m,e[114]=l,e[115]=u,e[116]=se):se=e[116];let re;e[117]!==m||e[118]!==M||e[119]!==s.order||e[120]!==ne||e[121]!==te||e[122]!==ie||e[123]!==se?(re=n.jsx(nn,{deploymentsFrgmt:m,loading:M,order:s.order,onChangeOrder:ne,pagination:te,tableSettings:ie,customizeColumns:se}),e[117]=m,e[118]=M,e[119]=s.order,e[120]=ne,e[121]=te,e[122]=ie,e[123]=se,e[124]=re):re=e[124];let oe;e[125]!==le||e[126]!==re?(oe=n.jsxs(Te,{direction:"column",align:"stretch",gap:"sm",children:[le,re]}),e[125]=le,e[126]=re,e[127]=oe):oe=e[127];const il=p||!!Ce,sl=Ce??null;let ue;e[128]!==c||e[129]!==k?(ue=t=>{c(),Ke(null),t&&k()},e[128]=c,e[129]=k,e[130]=ue):ue=e[130];let de;e[131]!==il||e[132]!==sl||e[133]!==ue?(de=n.jsx(Dl,{children:n.jsx(Jl,{open:il,deploymentFrgmt:sl,onRequestClose:ue})}),e[131]=il,e[132]=sl,e[133]=ue,e[134]=de):de=e[134];const rl=!!i;let ce;e[135]!==l?(ce=l("deployment.DeleteDeployment"),e[135]=l,e[136]=ce):ce=e[136];let me;e[137]!==l?(me=l("deployment.Deployment"),e[137]=l,e[138]=me):me=e[138];let ge;e[139]!==i?(ge=i?[{key:i.id,label:((yl=i.metadata)==null?void 0:yl.name)??""}]:[],e[139]=i,e[140]=ge):ge=e[140];const ol=((fl=i==null?void 0:i.metadata)==null?void 0:fl.name)??"",ul=((kl=i==null?void 0:i.metadata)==null?void 0:kl.name)??"";let pe;e[141]!==ul?(pe={placeholder:ul},e[141]=ul,e[142]=pe):pe=e[142];let ye;e[143]!==nl?(ye={loading:nl},e[143]=nl,e[144]=ye):ye=e[144];let fe;e[145]!==ll||e[146]!==i||e[147]!==o||e[148]!==r||e[149]!==l||e[150]!==k?(fe=()=>{i&&ll({variables:{input:{id:vl(i.id)??i.id}},onCompleted:(t,C)=>{if(C&&C.length>0){o.error("Failed to delete deployment",C),r.error(l("deployment.FailedToDeleteDeployment"));return}r.success(l("deployment.DeploymentDeleted")),T(null),k()},onError:t=>{o.error("Failed to delete deployment",t),r.error(l("deployment.FailedToDeleteDeployment"))}})},e[145]=ll,e[146]=i,e[147]=o,e[148]=r,e[149]=l,e[150]=k,e[151]=fe):fe=e[151];let qe;e[152]===Symbol.for("react.memo_cache_sentinel")?(qe=()=>T(null),e[152]=qe):qe=e[152];let ke;e[153]!==rl||e[154]!==ce||e[155]!==me||e[156]!==ge||e[157]!==ol||e[158]!==pe||e[159]!==ye||e[160]!==fe?(ke=n.jsx(Xl,{open:rl,title:ce,target:me,items:ge,confirmText:ol,requireConfirmInput:!0,inputProps:pe,okButtonProps:ye,onOk:fe,onCancel:qe}),e[153]=rl,e[154]=ce,e[155]=me,e[156]=ge,e[157]=ol,e[158]=pe,e[159]=ye,e[160]=fe,e[161]=ke):ke=e[161];const dl=!!b;let Qe;e[162]===Symbol.for("react.memo_cache_sentinel")?(Qe=()=>ve(null),e[162]=Qe):Qe=e[162];let Fe;e[163]!==b||e[164]!==dl?(Fe=n.jsx(Dl,{children:n.jsx(en,{open:dl,revisionFrgmt:b,onClose:Qe})}),e[163]=b,e[164]=dl,e[165]=Fe):Fe=e[165];let ze;return e[166]!==oe||e[167]!==de||e[168]!==ke||e[169]!==Fe?(ze=n.jsxs(n.Fragment,{children:[oe,de,ke,Fe]}),e[166]=oe,e[167]=de,e[168]=ke,e[169]=Fe,e[170]=ze):ze=e[170],ze},fn=()=>{"use memo";const e=bl.c(6),{t:l}=hl();let r;e[0]!==l?(r=l("webui.menu.Deployments"),e[0]=l,e[1]=r):r=e[1];let o;e[2]===Symbol.for("react.memo_cache_sentinel")?(o={body:{paddingTop:0}},e[2]=o):o=e[2];let u;e[3]===Symbol.for("react.memo_cache_sentinel")?(u=n.jsx(Se.Suspense,{fallback:n.jsx(Nl,{active:!0}),children:n.jsx(sn,{})}),e[3]=u):u=e[3];let p;return e[4]!==r?(p=n.jsx(Te,{direction:"column",align:"stretch",gap:"md",children:n.jsx(Rl,{variant:"borderless",title:r,styles:o,children:u})}),e[4]=r,e[5]=p):p=e[5],p};function rn(e){return typeof e=="object"&&e!==null&&!Array.isArray(e)?e:{}}export{fn as default};
//# sourceMappingURL=DeploymentListPage-DTV2gBgx.js.map
