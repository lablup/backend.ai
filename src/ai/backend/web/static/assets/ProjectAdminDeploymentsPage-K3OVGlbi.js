import{k as vl,u as Kl,av as jl,j as a,bM as Tl,r as Fe,aG as kl,A as Al,x as Ll,V as Pl,W as Nl,b3 as Rl,by as Fl,ag as Ml,ae as xl,a4 as Vl,aB as _l,l as Dl,aU as Bl,al as wl,aE as Ol,c5 as Ul,B as nl,b_ as El,b4 as $l,b5 as ql,L as Sl,T as al,dd as Gl,bd as Ql,w as zl,bN as Wl}from"./index-C08xJCnW.js";import{i as Hl,B as Jl,D as Yl}from"./DeploymentRevisionDetailDrawer-j9ejY0i9.js";import{a as Xl,p as Zl,B as en}from"./BAIModelDeploymentNodes-C8MafYYW.js";import{B as ln}from"./BAIGraphQLPropertyFilter-ZoG762m3.js";import{S as nn}from"./square-pen-CvvQiV8i.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-CP5sADwg.js";import"./BAIId-CThGof7r.js";import"./BooleanTag-DBZVsE5Z.js";const bl=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e},params:{cacheID:"1463ddcf31aa971e7f72ca3901c5db76",id:null,metadata:{},name:"ProjectAdminDeploymentsPageDeleteMutation",operationKind:"mutation",text:`mutation ProjectAdminDeploymentsPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();bl.hash="42ff73332d0c41e5828ba82d49920b78";const hl=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},m={defaultValue:null,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"orderBy"},d={defaultValue:null,kind:"LocalArgument",name:"projectId"},c=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},De={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},j={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},h={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,u,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},Se={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},f=[u,g];return{fragment:{argumentDefinitions:[n,e,m,l,d],kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:c,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[u,De],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,b,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[d,n,l,e,m],kind:"Operation",name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:c,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},u,De,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},j,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[u],storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[o],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,b,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[h,Se,I,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},j,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:f,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[u,t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:f,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},g,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},t],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[Se,I,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},h],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[u,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[t,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"87367d284c7c2b5500c11add9a83bdae",id:null,metadata:{},name:"ProjectAdminDeploymentsPageQuery",operationKind:"query",text:`query ProjectAdminDeploymentsPageQuery(
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
`}}})();hl.hash="c0915455c90833c0f8fa382e2c4d6319";const an=n=>{"use memo";var sl,ol,dl,ul,cl,ml,pl,yl,gl;const e=vl.c(163),{projectId:m}=n,{t:l}=Kl(),{message:d}=Al.useApp(),{logger:c}=Ll(),o=Pl(),t=Nl(),[u,De]=Fe.useState(null),[b,j]=Fe.useState(null),[h,Se]=Fe.useState(null);let I;e[0]===Symbol.for("react.memo_cache_sentinel")?(I={current:1,pageSize:10},e[0]=I):I=e[0];const{baiPaginationOption:g,tablePaginationOption:f,setTablePaginationOption:k}=Rl(I);let Ce,je;e[1]===Symbol.for("react.memo_cache_sentinel")?(Ce={filter:Ml(tn),order:Fl(Xl),statusCategory:Fl(["running","finished"]).withDefault("running")},je={history:"replace"},e[1]=Ce,e[2]=je):(Ce=e[1],je=e[2]);const[s,F]=xl(Ce,je),[Ee,$e]=Vl("table_column_overrides.ProjectAdminDeploymentsPage"),[ve,D]=_l();let Te;e[3]===Symbol.for("react.memo_cache_sentinel")?(Te=["STOPPED"],e[3]=Te):Te=e[3];const tl=Te;let Ae;e[4]!==s.statusCategory?(Ae=s.statusCategory==="finished"?{status:{in:tl}}:{status:{notIn:tl}},e[4]=s.statusCategory,e[5]=Ae):Ae=e[5];const qe=Ae;let Le;e[6]!==s.order?(Le=Zl(s.order),e[6]=s.order,e[7]=Le):Le=e[7];const Ke=Le;let T;e[8]!==s.filter?(T=s.filter??{},e[8]=s.filter,e[9]=T):T=e[9];let A;e[10]!==qe||e[11]!==T?(A={...T,...qe},e[10]=qe,e[11]=T,e[12]=A):A=e[12];let L;e[13]!==Ke?(L=Ke?[{field:Ke.field,direction:Ke.direction}]:void 0,e[13]=Ke,e[14]=L):L=e[14];let Pe;e[15]!==g.limit||e[16]!==g.offset||e[17]!==m||e[18]!==A||e[19]!==L?(Pe={projectId:m,filter:A,orderBy:L,limit:g.limit,offset:g.offset},e[15]=g.limit,e[16]=g.offset,e[17]=m,e[18]=A,e[19]=L,e[20]=Pe):Pe=e[20];const il=Pe,rl=Fe.useDeferredValue(il),be=Fe.useDeferredValue(ve);let Ne;e[21]===Symbol.for("react.memo_cache_sentinel")?(Ne=hl,e[21]=Ne):Ne=e[21];const Ge=be===Ol?"store-and-network":"network-only";let Re;e[22]!==be||e[23]!==Ge?(Re={fetchKey:be,fetchPolicy:Ge},e[22]=be,e[23]=Ge,e[24]=Re):Re=e[24];const P=Dl.useLazyLoadQuery(Ne,rl,Re);let p,he,Me,N;e[25]!==((sl=P.projectDeployments)==null?void 0:sl.count)||e[26]!==((ol=P.projectDeployments)==null?void 0:ol.edges)||e[27]!==b||e[28]!==u?(p=Bl(wl((dl=P.projectDeployments)==null?void 0:dl.edges,"node")),N=((ul=P.projectDeployments)==null?void 0:ul.count)??0,he=u==null?null:p.find(i=>i.id===u)??null,Me=b==null?null:p.find(i=>i.id===b)??null,e[25]=(cl=P.projectDeployments)==null?void 0:cl.count,e[26]=(ml=P.projectDeployments)==null?void 0:ml.edges,e[27]=b,e[28]=u,e[29]=p,e[30]=he,e[31]=Me,e[32]=N):(p=e[29],he=e[30],Me=e[31],N=e[32]);const r=Me,R=rl!==il||be!==ve;let xe;e[33]===Symbol.for("react.memo_cache_sentinel")?(xe=bl,e[33]=xe):xe=e[33];const[Qe,ze]=Dl.useMutation(xe);let M;e[34]!==l?(M=l("deployment.filter.Name"),e[34]=l,e[35]=M):M=e[35];let x;e[36]!==M?(x={key:"name",propertyLabel:M,type:"string"},e[36]=M,e[37]=x):x=e[37];let V;e[38]!==l?(V=l("deployment.filter.Tags"),e[38]=l,e[39]=V):V=e[39];let _;e[40]!==V?(_={key:"tags",propertyLabel:V,type:"string"},e[40]=V,e[41]=_):_=e[41];let B;e[42]!==l?(B=l("deployment.filter.EndpointUrl"),e[42]=l,e[43]=B):B=e[43];let w;e[44]!==B?(w={key:"endpointUrl",propertyLabel:B,type:"string"},e[44]=B,e[45]=w):w=e[45];let O;e[46]!==l?(O=l("deployment.filter.OpenToPublic"),e[46]=l,e[47]=O):O=e[47];let U;e[48]!==O?(U={key:"openToPublic",propertyLabel:O,type:"boolean"},e[48]=O,e[49]=U):U=e[49];let Ve;e[50]!==x||e[51]!==_||e[52]!==w||e[53]!==U?(Ve=[x,_,w,U],e[50]=x,e[51]=_,e[52]=w,e[53]=U,e[54]=Ve):Ve=e[54];const We=Ve;let _e;e[55]===Symbol.for("react.memo_cache_sentinel")?(_e={flexShrink:1},e[55]=_e):_e=e[55];const Il=s.statusCategory;let E;e[56]!==F||e[57]!==k?(E=i=>{F({statusCategory:i.target.value}),k({current:1})},e[56]=F,e[57]=k,e[58]=E):E=e[58];let $;e[59]!==l?($=l("deployment.Running"),e[59]=l,e[60]=$):$=e[60];let q;e[61]!==$?(q={label:$,value:"running"},e[61]=$,e[62]=q):q=e[62];let G;e[63]!==l?(G=l("deployment.status.Terminated"),e[63]=l,e[64]=G):G=e[64];let Q;e[65]!==G?(Q={label:G,value:"finished"},e[65]=G,e[66]=Q):Q=e[66];let z;e[67]!==q||e[68]!==Q?(z=[q,Q],e[67]=q,e[68]=Q,e[69]=z):z=e[69];let W;e[70]!==s.statusCategory||e[71]!==E||e[72]!==z?(W=a.jsx(Ul,{optionType:"button",value:Il,onChange:E,options:z}),e[70]=s.statusCategory,e[71]=E,e[72]=z,e[73]=W):W=e[73];const He=s.filter??void 0;let H;e[74]!==F||e[75]!==k?(H=i=>{F({filter:i??null}),k({current:1})},e[74]=F,e[75]=k,e[76]=H):H=e[76];let J;e[77]!==We||e[78]!==He||e[79]!==H?(J=a.jsx(ln,{filterProperties:We,value:He,onChange:H}),e[77]=We,e[78]=He,e[79]=H,e[80]=J):J=e[80];let Y;e[81]!==W||e[82]!==J?(Y=a.jsxs(nl,{gap:"sm",align:"start",wrap:"wrap",style:_e,children:[W,J]}),e[81]=W,e[82]=J,e[83]=Y):Y=e[83];let X;e[84]!==D?(X=i=>D(i),e[84]=D,e[85]=X):X=e[85];let Z;e[86]!==ve||e[87]!==R||e[88]!==X?(Z=a.jsx(El,{settingId:"project-admin-deployments",defaultAutoUpdateDelay:15e3,loading:R,value:ve,onChange:X}),e[86]=ve,e[87]=R,e[88]=X,e[89]=Z):Z=e[89];let ee;e[90]!==Y||e[91]!==Z?(ee=a.jsxs(nl,{justify:"between",wrap:"wrap",gap:"sm",children:[Y,Z]}),e[90]=Y,e[91]=Z,e[92]=ee):ee=e[92];let le;e[93]!==F?(le=i=>{F({order:i??null})},e[93]=F,e[94]=le):le=e[94];let ne;e[95]!==k?(ne=(i,C)=>{k({current:i,pageSize:C})},e[95]=k,e[96]=ne):ne=e[96];let ae;e[97]!==ne||e[98]!==f.current||e[99]!==f.pageSize||e[100]!==N?(ae={current:f.current,pageSize:f.pageSize,total:N,onChange:ne},e[97]=ne,e[98]=f.current,e[99]=f.pageSize,e[100]=N,e[101]=ae):ae=e[101];let te;e[102]!==Ee||e[103]!==$e?(te={columnOverrides:Ee,onColumnOverridesChange:$e},e[102]=Ee,e[103]=$e,e[104]=te):te=e[104];let ie;e[105]!==t||e[106]!==p||e[107]!==l||e[108]!==o?(ie=i=>{const C=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup","domainName","projectId"],Cl=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner"]);return i.filter(y=>C.includes(y.key)).map(y=>{let Ie=y;return y.key==="name"?Ie={...y,render:(fl,S)=>{var K,Ue;const v=Hl((K=S.metadata)==null?void 0:K.status);return a.jsx($l,{title:((Ue=S.metadata)==null?void 0:Ue.name)??"-",onTitleClick:()=>o(t(`deployments/${Sl(S.id)}`)),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:a.jsx(nn,{}),disabled:v,onClick:()=>De(S.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:a.jsx(ql,{}),type:"danger",disabled:v,onClick:()=>j(S.id)}]})}}:y.key==="currentRevisionNumber"?Ie={...y,render:(fl,S)=>{const v=p.find(Ue=>Ue.id===S.id),K=v==null?void 0:v.currentRevision;return(K==null?void 0:K.revisionNumber)==null?a.jsx(al.Text,{type:"secondary",children:"-"}):a.jsx(al.Link,{onClick:()=>Se(K),children:`#${K.revisionNumber}`})}}:y.key==="tags"&&(Ie={...y,render:(fl,S)=>a.jsx(Jl,{metadataFrgmt:S.metadata,stopRowClick:!0,onTagClick:v=>{o({pathname:t("deployments"),search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:v}})}).toString()})},fallback:a.jsx(al.Text,{type:"secondary",children:"-"})})}),y.key==="name"?Ie:{...Ie,defaultHidden:!Cl.has(y.key)}})},e[105]=t,e[106]=p,e[107]=l,e[108]=o,e[109]=ie):ie=e[109];let re;e[110]!==p||e[111]!==R||e[112]!==s.order||e[113]!==le||e[114]!==ae||e[115]!==te||e[116]!==ie?(re=a.jsx(en,{deploymentsFrgmt:p,loading:R,order:s.order,onChangeOrder:le,pagination:ae,tableSettings:te,customizeColumns:ie}),e[110]=p,e[111]=R,e[112]=s.order,e[113]=le,e[114]=ae,e[115]=te,e[116]=ie,e[117]=re):re=e[117];let se;e[118]!==ee||e[119]!==re?(se=a.jsxs(nl,{direction:"column",align:"stretch",gap:"sm",children:[ee,re]}),e[118]=ee,e[119]=re,e[120]=se):se=e[120];const Je=!!he,Ye=he??null;let oe;e[121]!==D?(oe=i=>{De(null),i&&D()},e[121]=D,e[122]=oe):oe=e[122];let de;e[123]!==Je||e[124]!==Ye||e[125]!==oe?(de=a.jsx(Gl,{open:Je,deploymentFrgmt:Ye,onRequestClose:oe}),e[123]=Je,e[124]=Ye,e[125]=oe,e[126]=de):de=e[126];const Xe=!!r;let ue;e[127]!==l?(ue=l("deployment.DeleteDeployment"),e[127]=l,e[128]=ue):ue=e[128];let ce;e[129]!==l?(ce=l("deployment.Deployment"),e[129]=l,e[130]=ce):ce=e[130];let me;e[131]!==r?(me=r?[{key:r.id,label:((pl=r.metadata)==null?void 0:pl.name)??""}]:[],e[131]=r,e[132]=me):me=e[132];const Ze=((yl=r==null?void 0:r.metadata)==null?void 0:yl.name)??"",el=((gl=r==null?void 0:r.metadata)==null?void 0:gl.name)??"";let pe;e[133]!==el?(pe={placeholder:el},e[133]=el,e[134]=pe):pe=e[134];let ye;e[135]!==ze?(ye={loading:ze},e[135]=ze,e[136]=ye):ye=e[136];let ge;e[137]!==Qe||e[138]!==r||e[139]!==c||e[140]!==d||e[141]!==l||e[142]!==D?(ge=()=>{r&&Qe({variables:{input:{id:Sl(r.id)??r.id}},onCompleted:(i,C)=>{if(C&&C.length>0){c.error("Failed to delete deployment",C),d.error(l("deployment.FailedToDeleteDeployment"));return}d.success(l("deployment.DeploymentDeleted")),j(null),D()},onError:i=>{c.error("Failed to delete deployment",i),d.error(l("deployment.FailedToDeleteDeployment"))}})},e[137]=Qe,e[138]=r,e[139]=c,e[140]=d,e[141]=l,e[142]=D,e[143]=ge):ge=e[143];let Be;e[144]===Symbol.for("react.memo_cache_sentinel")?(Be=()=>j(null),e[144]=Be):Be=e[144];let fe;e[145]!==Xe||e[146]!==ue||e[147]!==ce||e[148]!==me||e[149]!==Ze||e[150]!==pe||e[151]!==ye||e[152]!==ge?(fe=a.jsx(Ql,{open:Xe,title:ue,target:ce,items:me,confirmText:Ze,requireConfirmInput:!0,inputProps:pe,okButtonProps:ye,onOk:ge,onCancel:Be}),e[145]=Xe,e[146]=ue,e[147]=ce,e[148]=me,e[149]=Ze,e[150]=pe,e[151]=ye,e[152]=ge,e[153]=fe):fe=e[153];const ll=!!h;let we;e[154]===Symbol.for("react.memo_cache_sentinel")?(we=()=>Se(null),e[154]=we):we=e[154];let ke;e[155]!==h||e[156]!==ll?(ke=a.jsx(zl,{children:a.jsx(Yl,{open:ll,revisionFrgmt:h,onClose:we})}),e[155]=h,e[156]=ll,e[157]=ke):ke=e[157];let Oe;return e[158]!==se||e[159]!==de||e[160]!==fe||e[161]!==ke?(Oe=a.jsxs(a.Fragment,{children:[se,de,fe,ke]}),e[158]=se,e[159]=de,e[160]=fe,e[161]=ke,e[162]=Oe):Oe=e[162],Oe},gn=()=>{"use memo";const n=vl.c(9),{t:e}=Kl(),m=jl();let l;n[0]!==e?(l=e("webui.menu.ProjectDeployments"),n[0]=e,n[1]=l):l=n[1];let d;n[2]===Symbol.for("react.memo_cache_sentinel")?(d={header:{borderBottom:"none"},body:{paddingTop:0}},n[2]=d):d=n[2];let c;n[3]===Symbol.for("react.memo_cache_sentinel")?(c=a.jsx(kl,{active:!0}),n[3]=c):c=n[3];let o;n[4]!==m.id?(o=a.jsx(Tl,{children:a.jsx(Fe.Suspense,{fallback:c,children:m.id?a.jsx(an,{projectId:m.id}):a.jsx(kl,{active:!0})})}),n[4]=m.id,n[5]=o):o=n[5];let t;return n[6]!==l||n[7]!==o?(t=a.jsx(Wl,{variant:"borderless",title:l,styles:d,children:o}),n[6]=l,n[7]=o,n[8]=t):t=n[8],t};function tn(n){return typeof n=="object"&&n!==null&&!Array.isArray(n)?n:{}}export{gn as default};
//# sourceMappingURL=ProjectAdminDeploymentsPage-K3OVGlbi.js.map
