import{h as vl,u as Kl,aj as jl,j as a,bJ as Tl,r as ke,aw as kl,A as Al,v as Ll,p as Nl,bs as Pl,bt as Fl,c$ as Rl,bu as Ml,a4 as xl,ar as Vl,i as Dl,aK as Bl,a6 as _l,au as wl,c1 as Ol,B as nl,aA as El,aX as Ul,d0 as $l,aZ as ql,N as Sl,T as al,d1 as Ql,b7 as zl,a7 as Gl,bI as Hl}from"./index-DLl5_15D.js";import{i as Jl,B as Wl,D as Xl}from"./DeploymentRevisionDetailDrawer-yvw1W0py.js";import{p as Yl,B as Zl,a as en}from"./BAIModelDeploymentNodes-qJmGIh6-.js";import{B as ln}from"./BAIGraphQLPropertyFilter-BVY69KXO.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-C2HMK66Z.js";import"./BAIId-CUEnOS4w.js";import"./BooleanTag-Ca7dIHjt.js";const bl=function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e},params:{cacheID:"1463ddcf31aa971e7f72ca3901c5db76",id:null,metadata:{},name:"ProjectAdminDeploymentsPageDeleteMutation",operationKind:"mutation",text:`mutation ProjectAdminDeploymentsPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}}();bl.hash="42ff73332d0c41e5828ba82d49920b78";const hl=function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},m={defaultValue:null,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"orderBy"},d={defaultValue:null,kind:"LocalArgument",name:"projectId"},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},j={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},Fe={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,p,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},c=[p,k];return{fragment:{argumentDefinitions:[n,e,m,l,d],kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[p,b],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,j,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[d,n,l,e,m],kind:"Operation",name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},p,b,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},h,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[p],storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[o],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,j,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[Fe,I,f,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},h,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:c,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[p,t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:c,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},k,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},t],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[I,f,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},Fe],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[p,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[t,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"87367d284c7c2b5500c11add9a83bdae",id:null,metadata:{},name:"ProjectAdminDeploymentsPageQuery",operationKind:"query",text:`query ProjectAdminDeploymentsPageQuery(
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
`}}}();hl.hash="c0915455c90833c0f8fa382e2c4d6319";const nn=n=>{"use memo";var sl,ol,dl,ul,cl,ml,pl,yl,gl;const e=vl.c(162),{projectId:m}=n,{t:l}=Kl(),{message:d}=Al.useApp(),{logger:u}=Ll(),o=Nl(),[t,p]=ke.useState(null),[b,j]=ke.useState(null),[h,Fe]=ke.useState(null);let I;e[0]===Symbol.for("react.memo_cache_sentinel")?(I={current:1,pageSize:10},e[0]=I):I=e[0];const{baiPaginationOption:f,tablePaginationOption:k,setTablePaginationOption:c}=Pl(I);let he,Ie;e[1]===Symbol.for("react.memo_cache_sentinel")?(he={filter:Rl(an),order:Fl(en),statusCategory:Fl(["running","finished"]).withDefault("running")},Ie={history:"replace"},e[1]=he,e[2]=Ie):(he=e[1],Ie=e[2]);const[s,F]=Ml(he,Ie),[Ee,Ue]=xl("table_column_overrides.ProjectAdminDeploymentsPage"),[De,D]=Vl();let Ce;e[3]===Symbol.for("react.memo_cache_sentinel")?(Ce=["STOPPED"],e[3]=Ce):Ce=e[3];const tl=Ce;let je;e[4]!==s.statusCategory?(je=s.statusCategory==="finished"?{status:{in:tl}}:{status:{notIn:tl}},e[4]=s.statusCategory,e[5]=je):je=e[5];const $e=je;let Te;e[6]!==s.order?(Te=Yl(s.order),e[6]=s.order,e[7]=Te):Te=e[7];const Se=Te;let Ae;e[8]!==s.filter?(Ae=s.filter??{},e[8]=s.filter,e[9]=Ae):Ae=e[9];const qe=Ae;let T;e[10]!==$e||e[11]!==qe?(T={...qe,...$e},e[10]=$e,e[11]=qe,e[12]=T):T=e[12];let A;e[13]!==Se?(A=Se?[{field:Se.field,direction:Se.direction}]:void 0,e[13]=Se,e[14]=A):A=e[14];let Le;e[15]!==f.limit||e[16]!==f.offset||e[17]!==m||e[18]!==A||e[19]!==T?(Le={projectId:m,filter:T,orderBy:A,limit:f.limit,offset:f.offset},e[15]=f.limit,e[16]=f.offset,e[17]=m,e[18]=A,e[19]=T,e[20]=Le):Le=e[20];const il=Le,rl=ke.useDeferredValue(il),ve=ke.useDeferredValue(De);let Ne;e[21]===Symbol.for("react.memo_cache_sentinel")?(Ne=hl,e[21]=Ne):Ne=e[21];const Qe=ve===wl?"store-and-network":"network-only";let Pe;e[22]!==ve||e[23]!==Qe?(Pe={fetchKey:ve,fetchPolicy:Qe},e[22]=ve,e[23]=Qe,e[24]=Pe):Pe=e[24];const L=Dl.useLazyLoadQuery(Ne,rl,Pe);let y,Ke,Re,N;e[25]!==((sl=L.projectDeployments)==null?void 0:sl.count)||e[26]!==((ol=L.projectDeployments)==null?void 0:ol.edges)||e[27]!==b||e[28]!==t?(y=Bl(_l((dl=L.projectDeployments)==null?void 0:dl.edges,"node")),N=((ul=L.projectDeployments)==null?void 0:ul.count)??0,Ke=t==null?null:y.find(i=>i.id===t)??null,Re=b==null?null:y.find(i=>i.id===b)??null,e[25]=(cl=L.projectDeployments)==null?void 0:cl.count,e[26]=(ml=L.projectDeployments)==null?void 0:ml.edges,e[27]=b,e[28]=t,e[29]=y,e[30]=Ke,e[31]=Re,e[32]=N):(y=e[29],Ke=e[30],Re=e[31],N=e[32]);const r=Re,P=rl!==il||ve!==De;let Me;e[33]===Symbol.for("react.memo_cache_sentinel")?(Me=bl,e[33]=Me):Me=e[33];const[ze,Ge]=Dl.useMutation(Me);let R;e[34]!==l?(R=l("deployment.filter.Name"),e[34]=l,e[35]=R):R=e[35];let M;e[36]!==R?(M={key:"name",propertyLabel:R,type:"string"},e[36]=R,e[37]=M):M=e[37];let x;e[38]!==l?(x=l("deployment.filter.Tags"),e[38]=l,e[39]=x):x=e[39];let V;e[40]!==x?(V={key:"tags",propertyLabel:x,type:"string"},e[40]=x,e[41]=V):V=e[41];let B;e[42]!==l?(B=l("deployment.filter.EndpointUrl"),e[42]=l,e[43]=B):B=e[43];let _;e[44]!==B?(_={key:"endpointUrl",propertyLabel:B,type:"string"},e[44]=B,e[45]=_):_=e[45];let w;e[46]!==l?(w=l("deployment.filter.OpenToPublic"),e[46]=l,e[47]=w):w=e[47];let O;e[48]!==w?(O={key:"openToPublic",propertyLabel:w,type:"boolean"},e[48]=w,e[49]=O):O=e[49];let xe;e[50]!==M||e[51]!==V||e[52]!==_||e[53]!==O?(xe=[M,V,_,O],e[50]=M,e[51]=V,e[52]=_,e[53]=O,e[54]=xe):xe=e[54];const He=xe;let Ve;e[55]===Symbol.for("react.memo_cache_sentinel")?(Ve={flexShrink:1},e[55]=Ve):Ve=e[55];const Il=s.statusCategory;let E;e[56]!==F||e[57]!==c?(E=i=>{F({statusCategory:i.target.value}),c({current:1})},e[56]=F,e[57]=c,e[58]=E):E=e[58];let U;e[59]!==l?(U=l("deployment.Running"),e[59]=l,e[60]=U):U=e[60];let $;e[61]!==U?($={label:U,value:"running"},e[61]=U,e[62]=$):$=e[62];let q;e[63]!==l?(q=l("deployment.status.Terminated"),e[63]=l,e[64]=q):q=e[64];let Q;e[65]!==q?(Q={label:q,value:"finished"},e[65]=q,e[66]=Q):Q=e[66];let z;e[67]!==$||e[68]!==Q?(z=[$,Q],e[67]=$,e[68]=Q,e[69]=z):z=e[69];let G;e[70]!==s.statusCategory||e[71]!==E||e[72]!==z?(G=a.jsx(Ol,{optionType:"button",value:Il,onChange:E,options:z}),e[70]=s.statusCategory,e[71]=E,e[72]=z,e[73]=G):G=e[73];const Je=s.filter??void 0;let H;e[74]!==F||e[75]!==c?(H=i=>{F({filter:i??null}),c({current:1})},e[74]=F,e[75]=c,e[76]=H):H=e[76];let J;e[77]!==He||e[78]!==Je||e[79]!==H?(J=a.jsx(ln,{filterProperties:He,value:Je,onChange:H}),e[77]=He,e[78]=Je,e[79]=H,e[80]=J):J=e[80];let W;e[81]!==G||e[82]!==J?(W=a.jsxs(nl,{gap:"sm",align:"start",wrap:"wrap",style:Ve,children:[G,J]}),e[81]=G,e[82]=J,e[83]=W):W=e[83];let X;e[84]!==D?(X=i=>D(i),e[84]=D,e[85]=X):X=e[85];let Y;e[86]!==De||e[87]!==P||e[88]!==X?(Y=a.jsx(El,{loading:P,value:De,onChange:X,autoUpdateDelay:15e3}),e[86]=De,e[87]=P,e[88]=X,e[89]=Y):Y=e[89];let Z;e[90]!==W||e[91]!==Y?(Z=a.jsxs(nl,{justify:"between",wrap:"wrap",gap:"sm",children:[W,Y]}),e[90]=W,e[91]=Y,e[92]=Z):Z=e[92];let ee;e[93]!==F?(ee=i=>{F({order:i??null})},e[93]=F,e[94]=ee):ee=e[94];let le;e[95]!==c?(le=(i,C)=>{c({current:i,pageSize:C})},e[95]=c,e[96]=le):le=e[96];let ne;e[97]!==le||e[98]!==k.current||e[99]!==k.pageSize||e[100]!==N?(ne={current:k.current,pageSize:k.pageSize,total:N,onChange:le},e[97]=le,e[98]=k.current,e[99]=k.pageSize,e[100]=N,e[101]=ne):ne=e[101];let ae;e[102]!==Ee||e[103]!==Ue?(ae={columnOverrides:Ee,onColumnOverridesChange:Ue},e[102]=Ee,e[103]=Ue,e[104]=ae):ae=e[104];let te;e[105]!==y||e[106]!==l||e[107]!==o?(te=i=>{const C=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup","domainName","projectId"],Cl=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner"]);return i.filter(g=>C.includes(g.key)).map(g=>{let be=g;return g.key==="name"?be={...g,render:(fl,S)=>{var K,Oe;const v=Jl((K=S.metadata)==null?void 0:K.status);return a.jsx(Ul,{title:((Oe=S.metadata)==null?void 0:Oe.name)??"-",onTitleClick:()=>o(`/project-admin-deployments/${Sl(S.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:a.jsx($l,{}),disabled:v,onClick:()=>p(S.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:a.jsx(ql,{}),type:"danger",disabled:v,onClick:()=>j(S.id)}]})}}:g.key==="currentRevisionNumber"?be={...g,render:(fl,S)=>{const v=y.find(Oe=>Oe.id===S.id),K=v==null?void 0:v.currentRevision;return(K==null?void 0:K.revisionNumber)==null?a.jsx(al.Text,{type:"secondary",children:"-"}):a.jsx(al.Link,{onClick:()=>Fe(K),children:`#${K.revisionNumber}`})}}:g.key==="tags"&&(be={...g,render:(fl,S)=>a.jsx(Wl,{metadataFrgmt:S.metadata,stopRowClick:!0,onTagClick:v=>{o({pathname:"/project-admin-deployments",search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:v}})}).toString()})},fallback:a.jsx(al.Text,{type:"secondary",children:"-"})})}),g.key==="name"?be:{...be,defaultHidden:!Cl.has(g.key)}})},e[105]=y,e[106]=l,e[107]=o,e[108]=te):te=e[108];let ie;e[109]!==y||e[110]!==P||e[111]!==s.order||e[112]!==ee||e[113]!==ne||e[114]!==ae||e[115]!==te?(ie=a.jsx(Zl,{deploymentsFrgmt:y,loading:P,order:s.order,onChangeOrder:ee,pagination:ne,tableSettings:ae,customizeColumns:te}),e[109]=y,e[110]=P,e[111]=s.order,e[112]=ee,e[113]=ne,e[114]=ae,e[115]=te,e[116]=ie):ie=e[116];let re;e[117]!==Z||e[118]!==ie?(re=a.jsxs(nl,{direction:"column",align:"stretch",gap:"sm",children:[Z,ie]}),e[117]=Z,e[118]=ie,e[119]=re):re=e[119];const We=!!Ke,Xe=Ke??null;let se;e[120]!==D?(se=i=>{p(null),i&&D()},e[120]=D,e[121]=se):se=e[121];let oe;e[122]!==We||e[123]!==Xe||e[124]!==se?(oe=a.jsx(Ql,{open:We,deploymentFrgmt:Xe,onRequestClose:se}),e[122]=We,e[123]=Xe,e[124]=se,e[125]=oe):oe=e[125];const Ye=!!r;let de;e[126]!==l?(de=l("deployment.DeleteDeployment"),e[126]=l,e[127]=de):de=e[127];let ue;e[128]!==l?(ue=l("deployment.Deployment"),e[128]=l,e[129]=ue):ue=e[129];let ce;e[130]!==r?(ce=r?[{key:r.id,label:((pl=r.metadata)==null?void 0:pl.name)??""}]:[],e[130]=r,e[131]=ce):ce=e[131];const Ze=((yl=r==null?void 0:r.metadata)==null?void 0:yl.name)??"",el=((gl=r==null?void 0:r.metadata)==null?void 0:gl.name)??"";let me;e[132]!==el?(me={placeholder:el},e[132]=el,e[133]=me):me=e[133];let pe;e[134]!==Ge?(pe={loading:Ge},e[134]=Ge,e[135]=pe):pe=e[135];let ye;e[136]!==ze||e[137]!==r||e[138]!==u||e[139]!==d||e[140]!==l||e[141]!==D?(ye=()=>{r&&ze({variables:{input:{id:Sl(r.id)??r.id}},onCompleted:(i,C)=>{if(C&&C.length>0){u.error("Failed to delete deployment",C),d.error(l("deployment.FailedToDeleteDeployment"));return}d.success(l("deployment.DeploymentDeleted")),j(null),D()},onError:i=>{u.error("Failed to delete deployment",i),d.error(l("deployment.FailedToDeleteDeployment"))}})},e[136]=ze,e[137]=r,e[138]=u,e[139]=d,e[140]=l,e[141]=D,e[142]=ye):ye=e[142];let Be;e[143]===Symbol.for("react.memo_cache_sentinel")?(Be=()=>j(null),e[143]=Be):Be=e[143];let ge;e[144]!==Ye||e[145]!==de||e[146]!==ue||e[147]!==ce||e[148]!==Ze||e[149]!==me||e[150]!==pe||e[151]!==ye?(ge=a.jsx(zl,{open:Ye,title:de,target:ue,items:ce,confirmText:Ze,requireConfirmInput:!0,inputProps:me,okButtonProps:pe,onOk:ye,onCancel:Be}),e[144]=Ye,e[145]=de,e[146]=ue,e[147]=ce,e[148]=Ze,e[149]=me,e[150]=pe,e[151]=ye,e[152]=ge):ge=e[152];const ll=!!h;let _e;e[153]===Symbol.for("react.memo_cache_sentinel")?(_e=()=>Fe(null),e[153]=_e):_e=e[153];let fe;e[154]!==h||e[155]!==ll?(fe=a.jsx(Gl,{children:a.jsx(Xl,{open:ll,revisionFrgmt:h,onClose:_e})}),e[154]=h,e[155]=ll,e[156]=fe):fe=e[156];let we;return e[157]!==re||e[158]!==oe||e[159]!==ge||e[160]!==fe?(we=a.jsxs(a.Fragment,{children:[re,oe,ge,fe]}),e[157]=re,e[158]=oe,e[159]=ge,e[160]=fe,e[161]=we):we=e[161],we},pn=()=>{"use memo";const n=vl.c(9),{t:e}=Kl(),m=jl();let l;n[0]!==e?(l=e("webui.menu.ProjectDeployments"),n[0]=e,n[1]=l):l=n[1];let d;n[2]===Symbol.for("react.memo_cache_sentinel")?(d={header:{borderBottom:"none"},body:{paddingTop:0}},n[2]=d):d=n[2];let u;n[3]===Symbol.for("react.memo_cache_sentinel")?(u=a.jsx(kl,{active:!0}),n[3]=u):u=n[3];let o;n[4]!==m.id?(o=a.jsx(Tl,{children:a.jsx(ke.Suspense,{fallback:u,children:m.id?a.jsx(nn,{projectId:m.id}):a.jsx(kl,{active:!0})})}),n[4]=m.id,n[5]=o):o=n[5];let t;return n[6]!==l||n[7]!==o?(t=a.jsx(Hl,{variant:"borderless",title:l,styles:d,children:o}),n[6]=l,n[7]=o,n[8]=t):t=n[8],t};function an(n){return typeof n=="object"&&n!==null&&!Array.isArray(n)?n:{}}export{pn as default};
//# sourceMappingURL=ProjectAdminDeploymentsPage-DmnTkuOh.js.map
