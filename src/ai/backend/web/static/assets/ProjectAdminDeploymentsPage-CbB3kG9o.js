import{k as Dl,u as Sl,L as Il,j as a,bR as jl,r as Fe,aM as gl,J as Cl,H as Tl,a0 as Al,a1 as Ll,b9 as Pl,bD as fl,an as Nl,al as Rl,ab as Ml,aH as xl,c2 as Vl,l as kl,a_ as _l,as as Bl,aK as wl,c8 as Ol,B as el,c1 as Ul,ba as El,bb as $l,V as Fl,T as ll,de as ql,bj as Gl,w as Ql,G as zl}from"./index-CrFvxZIN.js";import{i as Hl,B as Jl,D as Wl}from"./DeploymentRevisionDetailDrawer-CoGWrqnO.js";import{a as Yl,B as Xl}from"./BAIModelDeploymentNodes-DkSgbwhz.js";import{B as Zl}from"./BAIGraphQLPropertyFilter-Nw6tLZrH.js";import{S as en}from"./square-pen-CbJIrIOh.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-BO0tWhos.js";import"./BAIId-DDwepSJA.js";import"./BooleanTag-By_86yqr.js";const vl=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e},params:{cacheID:"1463ddcf31aa971e7f72ca3901c5db76",id:null,metadata:{},name:"ProjectAdminDeploymentsPageDeleteMutation",operationKind:"mutation",text:`mutation ProjectAdminDeploymentsPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();vl.hash="42ff73332d0c41e5828ba82d49920b78";const Kl=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},m={defaultValue:null,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"orderBy"},u={defaultValue:null,kind:"LocalArgument",name:"projectId"},c=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},De={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},h={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,d,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},Se={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},f=[d,g];return{fragment:{argumentDefinitions:[n,e,m,l,u],kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:c,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[d,De],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,b,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[u,n,l,e,m],kind:"Operation",name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:c,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},d,De,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},C,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[d],storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[o],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,b,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[h,Se,I,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},C,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:f,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[d,t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:f,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},g,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},t],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[Se,I,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},h],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[t,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"87367d284c7c2b5500c11add9a83bdae",id:null,metadata:{},name:"ProjectAdminDeploymentsPageQuery",operationKind:"query",text:`query ProjectAdminDeploymentsPageQuery(
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
`}}})();Kl.hash="c0915455c90833c0f8fa382e2c4d6319";const ln=n=>{"use memo";var il,rl,sl,ol,ul,dl,cl,ml,pl;const e=Dl.c(161),{projectId:m}=n,{t:l}=Sl(),{message:u}=Cl.useApp(),{logger:c}=Tl(),o=Al(),t=Ll(),[d,De]=Fe.useState(null),[b,C]=Fe.useState(null),[h,Se]=Fe.useState(null);let I;e[0]===Symbol.for("react.memo_cache_sentinel")?(I={current:1,pageSize:10},e[0]=I):I=e[0];const{baiPaginationOption:g,tablePaginationOption:f,setTablePaginationOption:k}=Pl(I);let Ie,je;e[1]===Symbol.for("react.memo_cache_sentinel")?(Ie={filter:Nl(nn),order:fl(Yl),statusCategory:fl(["running","finished"]).withDefault("running")},je={history:"replace"},e[1]=Ie,e[2]=je):(Ie=e[1],je=e[2]);const[s,F]=Rl(Ie,je),[Oe,Ue]=Ml("table_column_overrides.ProjectAdminDeploymentsPage"),[ve,D]=xl();let Ce;e[3]===Symbol.for("react.memo_cache_sentinel")?(Ce=["STOPPED"],e[3]=Ce):Ce=e[3];const nl=Ce;let Te;e[4]!==s.statusCategory?(Te=s.statusCategory==="finished"?{status:{in:nl}}:{status:{notIn:nl}},e[4]=s.statusCategory,e[5]=Te):Te=e[5];const Ee=Te;let T;e[6]!==s.filter?(T=s.filter??{},e[6]=s.filter,e[7]=T):T=e[7];let A;e[8]!==Ee||e[9]!==T?(A={...T,...Ee},e[8]=Ee,e[9]=T,e[10]=A):A=e[10];let L;e[11]!==s.order?(L=Vl(s.order),e[11]=s.order,e[12]=L):L=e[12];let Ae;e[13]!==g.limit||e[14]!==g.offset||e[15]!==m||e[16]!==A||e[17]!==L?(Ae={projectId:m,filter:A,orderBy:L,limit:g.limit,offset:g.offset},e[13]=g.limit,e[14]=g.offset,e[15]=m,e[16]=A,e[17]=L,e[18]=Ae):Ae=e[18];const al=Ae,tl=Fe.useDeferredValue(al),Ke=Fe.useDeferredValue(ve);let Le;e[19]===Symbol.for("react.memo_cache_sentinel")?(Le=Kl,e[19]=Le):Le=e[19];const $e=Ke===wl?"store-and-network":"network-only";let Pe;e[20]!==Ke||e[21]!==$e?(Pe={fetchKey:Ke,fetchPolicy:$e},e[20]=Ke,e[21]=$e,e[22]=Pe):Pe=e[22];const P=kl.useLazyLoadQuery(Le,tl,Pe);let p,be,Ne,N;e[23]!==((il=P.projectDeployments)==null?void 0:il.count)||e[24]!==((rl=P.projectDeployments)==null?void 0:rl.edges)||e[25]!==b||e[26]!==d?(p=_l(Bl((sl=P.projectDeployments)==null?void 0:sl.edges,"node")),N=((ol=P.projectDeployments)==null?void 0:ol.count)??0,be=d==null?null:p.find(i=>i.id===d)??null,Ne=b==null?null:p.find(i=>i.id===b)??null,e[23]=(ul=P.projectDeployments)==null?void 0:ul.count,e[24]=(dl=P.projectDeployments)==null?void 0:dl.edges,e[25]=b,e[26]=d,e[27]=p,e[28]=be,e[29]=Ne,e[30]=N):(p=e[27],be=e[28],Ne=e[29],N=e[30]);const r=Ne,R=tl!==al||Ke!==ve;let Re;e[31]===Symbol.for("react.memo_cache_sentinel")?(Re=vl,e[31]=Re):Re=e[31];const[qe,Ge]=kl.useMutation(Re);let M;e[32]!==l?(M=l("deployment.filter.Name"),e[32]=l,e[33]=M):M=e[33];let x;e[34]!==M?(x={key:"name",propertyLabel:M,type:"string"},e[34]=M,e[35]=x):x=e[35];let V;e[36]!==l?(V=l("deployment.filter.Tags"),e[36]=l,e[37]=V):V=e[37];let _;e[38]!==V?(_={key:"tags",propertyLabel:V,type:"string"},e[38]=V,e[39]=_):_=e[39];let B;e[40]!==l?(B=l("deployment.filter.EndpointUrl"),e[40]=l,e[41]=B):B=e[41];let w;e[42]!==B?(w={key:"endpointUrl",propertyLabel:B,type:"string"},e[42]=B,e[43]=w):w=e[43];let O;e[44]!==l?(O=l("deployment.filter.OpenToPublic"),e[44]=l,e[45]=O):O=e[45];let U;e[46]!==O?(U={key:"openToPublic",propertyLabel:O,type:"boolean"},e[46]=O,e[47]=U):U=e[47];let Me;e[48]!==x||e[49]!==_||e[50]!==w||e[51]!==U?(Me=[x,_,w,U],e[48]=x,e[49]=_,e[50]=w,e[51]=U,e[52]=Me):Me=e[52];const Qe=Me;let xe;e[53]===Symbol.for("react.memo_cache_sentinel")?(xe={flexShrink:1},e[53]=xe):xe=e[53];const bl=s.statusCategory;let E;e[54]!==F||e[55]!==k?(E=i=>{F({statusCategory:i.target.value}),k({current:1})},e[54]=F,e[55]=k,e[56]=E):E=e[56];let $;e[57]!==l?($=l("deployment.Running"),e[57]=l,e[58]=$):$=e[58];let q;e[59]!==$?(q={label:$,value:"running"},e[59]=$,e[60]=q):q=e[60];let G;e[61]!==l?(G=l("deployment.status.Terminated"),e[61]=l,e[62]=G):G=e[62];let Q;e[63]!==G?(Q={label:G,value:"finished"},e[63]=G,e[64]=Q):Q=e[64];let z;e[65]!==q||e[66]!==Q?(z=[q,Q],e[65]=q,e[66]=Q,e[67]=z):z=e[67];let H;e[68]!==s.statusCategory||e[69]!==E||e[70]!==z?(H=a.jsx(Ol,{optionType:"button",value:bl,onChange:E,options:z}),e[68]=s.statusCategory,e[69]=E,e[70]=z,e[71]=H):H=e[71];const ze=s.filter??void 0;let J;e[72]!==F||e[73]!==k?(J=i=>{F({filter:i??null}),k({current:1})},e[72]=F,e[73]=k,e[74]=J):J=e[74];let W;e[75]!==Qe||e[76]!==ze||e[77]!==J?(W=a.jsx(Zl,{filterProperties:Qe,value:ze,onChange:J}),e[75]=Qe,e[76]=ze,e[77]=J,e[78]=W):W=e[78];let Y;e[79]!==H||e[80]!==W?(Y=a.jsxs(el,{gap:"sm",align:"start",wrap:"wrap",style:xe,children:[H,W]}),e[79]=H,e[80]=W,e[81]=Y):Y=e[81];let X;e[82]!==D?(X=i=>D(i),e[82]=D,e[83]=X):X=e[83];let Z;e[84]!==ve||e[85]!==R||e[86]!==X?(Z=a.jsx(Ul,{settingId:"project-admin-deployments",defaultAutoUpdateDelay:15e3,loading:R,value:ve,onChange:X}),e[84]=ve,e[85]=R,e[86]=X,e[87]=Z):Z=e[87];let ee;e[88]!==Y||e[89]!==Z?(ee=a.jsxs(el,{justify:"between",wrap:"wrap",gap:"sm",children:[Y,Z]}),e[88]=Y,e[89]=Z,e[90]=ee):ee=e[90];let le;e[91]!==F?(le=i=>{F({order:i??null})},e[91]=F,e[92]=le):le=e[92];let ne;e[93]!==k?(ne=(i,j)=>{k({current:i,pageSize:j})},e[93]=k,e[94]=ne):ne=e[94];let ae;e[95]!==ne||e[96]!==f.current||e[97]!==f.pageSize||e[98]!==N?(ae={current:f.current,pageSize:f.pageSize,total:N,onChange:ne},e[95]=ne,e[96]=f.current,e[97]=f.pageSize,e[98]=N,e[99]=ae):ae=e[99];let te;e[100]!==Oe||e[101]!==Ue?(te={columnOverrides:Oe,onColumnOverridesChange:Ue},e[100]=Oe,e[101]=Ue,e[102]=te):te=e[102];let ie;e[103]!==t||e[104]!==p||e[105]!==l||e[106]!==o?(ie=i=>{const j=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup","domainName","projectId"],hl=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner"]);return i.filter(y=>j.includes(y.key)).map(y=>{let he=y;return y.key==="name"?he={...y,render:(yl,S)=>{var K,we;const v=Hl((K=S.metadata)==null?void 0:K.status);return a.jsx(El,{title:((we=S.metadata)==null?void 0:we.name)??"-",onTitleClick:()=>o(t(`deployments/${Fl(S.id)}`)),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:a.jsx(en,{}),disabled:v,onClick:()=>De(S.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:a.jsx($l,{}),type:"danger",disabled:v,onClick:()=>C(S.id)}]})}}:y.key==="currentRevisionNumber"?he={...y,render:(yl,S)=>{const v=p.find(we=>we.id===S.id),K=v==null?void 0:v.currentRevision;return(K==null?void 0:K.revisionNumber)==null?a.jsx(ll.Text,{type:"secondary",children:"-"}):a.jsx(ll.Link,{onClick:()=>Se(K),children:`#${K.revisionNumber}`})}}:y.key==="tags"&&(he={...y,render:(yl,S)=>a.jsx(Jl,{metadataFrgmt:S.metadata,stopRowClick:!0,onTagClick:v=>{o({pathname:t("deployments"),search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:v}})}).toString()})},fallback:a.jsx(ll.Text,{type:"secondary",children:"-"})})}),y.key==="name"?he:{...he,defaultHidden:!hl.has(y.key)}})},e[103]=t,e[104]=p,e[105]=l,e[106]=o,e[107]=ie):ie=e[107];let re;e[108]!==p||e[109]!==R||e[110]!==s.order||e[111]!==le||e[112]!==ae||e[113]!==te||e[114]!==ie?(re=a.jsx(Xl,{deploymentsFrgmt:p,loading:R,order:s.order,onChangeOrder:le,pagination:ae,tableSettings:te,customizeColumns:ie}),e[108]=p,e[109]=R,e[110]=s.order,e[111]=le,e[112]=ae,e[113]=te,e[114]=ie,e[115]=re):re=e[115];let se;e[116]!==ee||e[117]!==re?(se=a.jsxs(el,{direction:"column",align:"stretch",gap:"sm",children:[ee,re]}),e[116]=ee,e[117]=re,e[118]=se):se=e[118];const He=!!be,Je=be??null;let oe;e[119]!==D?(oe=i=>{De(null),i&&D()},e[119]=D,e[120]=oe):oe=e[120];let ue;e[121]!==He||e[122]!==Je||e[123]!==oe?(ue=a.jsx(ql,{open:He,deploymentFrgmt:Je,onRequestClose:oe}),e[121]=He,e[122]=Je,e[123]=oe,e[124]=ue):ue=e[124];const We=!!r;let de;e[125]!==l?(de=l("deployment.DeleteDeployment"),e[125]=l,e[126]=de):de=e[126];let ce;e[127]!==l?(ce=l("deployment.Deployment"),e[127]=l,e[128]=ce):ce=e[128];let me;e[129]!==r?(me=r?[{key:r.id,label:((cl=r.metadata)==null?void 0:cl.name)??""}]:[],e[129]=r,e[130]=me):me=e[130];const Ye=((ml=r==null?void 0:r.metadata)==null?void 0:ml.name)??"",Xe=((pl=r==null?void 0:r.metadata)==null?void 0:pl.name)??"";let pe;e[131]!==Xe?(pe={placeholder:Xe},e[131]=Xe,e[132]=pe):pe=e[132];let ye;e[133]!==Ge?(ye={loading:Ge},e[133]=Ge,e[134]=ye):ye=e[134];let ge;e[135]!==qe||e[136]!==r||e[137]!==c||e[138]!==u||e[139]!==l||e[140]!==D?(ge=()=>{r&&qe({variables:{input:{id:Fl(r.id)??r.id}},onCompleted:(i,j)=>{if(j&&j.length>0){c.error("Failed to delete deployment",j),u.error(l("deployment.FailedToDeleteDeployment"));return}u.success(l("deployment.DeploymentDeleted")),C(null),D()},onError:i=>{c.error("Failed to delete deployment",i),u.error(l("deployment.FailedToDeleteDeployment"))}})},e[135]=qe,e[136]=r,e[137]=c,e[138]=u,e[139]=l,e[140]=D,e[141]=ge):ge=e[141];let Ve;e[142]===Symbol.for("react.memo_cache_sentinel")?(Ve=()=>C(null),e[142]=Ve):Ve=e[142];let fe;e[143]!==We||e[144]!==de||e[145]!==ce||e[146]!==me||e[147]!==Ye||e[148]!==pe||e[149]!==ye||e[150]!==ge?(fe=a.jsx(Gl,{open:We,title:de,target:ce,items:me,confirmText:Ye,requireConfirmInput:!0,inputProps:pe,okButtonProps:ye,onOk:ge,onCancel:Ve}),e[143]=We,e[144]=de,e[145]=ce,e[146]=me,e[147]=Ye,e[148]=pe,e[149]=ye,e[150]=ge,e[151]=fe):fe=e[151];const Ze=!!h;let _e;e[152]===Symbol.for("react.memo_cache_sentinel")?(_e=()=>Se(null),e[152]=_e):_e=e[152];let ke;e[153]!==h||e[154]!==Ze?(ke=a.jsx(Ql,{children:a.jsx(Wl,{open:Ze,revisionFrgmt:h,onClose:_e})}),e[153]=h,e[154]=Ze,e[155]=ke):ke=e[155];let Be;return e[156]!==se||e[157]!==ue||e[158]!==fe||e[159]!==ke?(Be=a.jsxs(a.Fragment,{children:[se,ue,fe,ke]}),e[156]=se,e[157]=ue,e[158]=fe,e[159]=ke,e[160]=Be):Be=e[160],Be},pn=()=>{"use memo";const n=Dl.c(9),{t:e}=Sl(),m=Il();let l;n[0]!==e?(l=e("webui.menu.ProjectDeployments"),n[0]=e,n[1]=l):l=n[1];let u;n[2]===Symbol.for("react.memo_cache_sentinel")?(u={header:{borderBottom:"none"},body:{paddingTop:0}},n[2]=u):u=n[2];let c;n[3]===Symbol.for("react.memo_cache_sentinel")?(c=a.jsx(gl,{active:!0}),n[3]=c):c=n[3];let o;n[4]!==m.id?(o=a.jsx(jl,{children:a.jsx(Fe.Suspense,{fallback:c,children:m.id?a.jsx(ln,{projectId:m.id}):a.jsx(gl,{active:!0})})}),n[4]=m.id,n[5]=o):o=n[5];let t;return n[6]!==l||n[7]!==o?(t=a.jsx(zl,{variant:"borderless",title:l,styles:u,children:o}),n[6]=l,n[7]=o,n[8]=t):t=n[8],t};function nn(n){return typeof n=="object"&&n!==null&&!Array.isArray(n)?n:{}}export{pn as default};
//# sourceMappingURL=ProjectAdminDeploymentsPage-CbB3kG9o.js.map
