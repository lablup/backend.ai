import{i as fl,u as kl,z as vl,j as a,co as bl,l as Fe,aU as cl,x as hl,Y as Il,Z as Cl,bE as jl,c8 as ml,ag as Tl,ae as Al,a7 as Ll,aN as Pl,aR as Nl,r as pl,aS as Ml,al as Rl,bg as xl,X as Vl,cC as Bl,c as Ye,cz as _l,bG as wl,aK as Ol,aM as Ul,N as gl,a2 as yl,L as El,bM as $l,ao as ql,d as zl}from"./index-DPebpL40.js";import{D as Gl,a as Ql}from"./DeploymentSettingModal-CWC6mALg.js";import{a as Hl,B as Wl}from"./BAIModelDeploymentNodes-l1D51jn_.js";import{B as Jl}from"./BAIGraphQLPropertyFilter-CPqP1l9W.js";import{i as Yl,B as Xl}from"./BAIDeploymentTagChips-zcg8l2YM.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-rZTSRFdj.js";import"./BAIId-oHD2WVBQ.js";import"./BooleanTag-DTKAExzX.js";import"./BAITag-dedPDMOM.js";const Fl=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e},params:{cacheID:"1463ddcf31aa971e7f72ca3901c5db76",id:null,metadata:{},name:"ProjectAdminDeploymentsPageDeleteMutation",operationKind:"mutation",text:`mutation ProjectAdminDeploymentsPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();Fl.hash="42ff73332d0c41e5828ba82d49920b78";const Sl=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},m={defaultValue:null,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"orderBy"},u={defaultValue:null,kind:"LocalArgument",name:"projectId"},c=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},Se={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},j={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},b={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,d,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},De={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},f=[d,y];return{fragment:{argumentDefinitions:[n,e,m,l,u],kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:c,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[d,Se],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,v,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[u,n,l,e,m],kind:"Operation",name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:c,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},d,Se,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},j,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[d],storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[o],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,v,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[b,De,h,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"subpath",storageKey:null}],storageKey:null},j,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:f,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[d,t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:f,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},y,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null}],storageKey:null},t],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[De,h,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},b],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"command",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[t,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"a44d64365a09e82b0ae5753829a546aa",id:null,metadata:{},name:"ProjectAdminDeploymentsPageQuery",operationKind:"query",text:`query ProjectAdminDeploymentsPageQuery(
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
`}}})();Sl.hash="c0915455c90833c0f8fa382e2c4d6319";const Zl=n=>{"use memo";var ll,nl,al,tl,il,rl,sl,ol,ul;const e=fl.c(157),{projectId:m}=n,{t:l}=kl(),{message:u}=Vl.useApp(),{logger:c}=hl(),o=Il(),t=Cl(),[d,Se]=Fe.useState(null),[v,j]=Fe.useState(null),[b,De]=Fe.useState(null);let h;e[0]===Symbol.for("react.memo_cache_sentinel")?(h={current:1,pageSize:10},e[0]=h):h=e[0];const{baiPaginationOption:y,tablePaginationOption:f,setTablePaginationOption:k}=jl(h);let he,Ie;e[1]===Symbol.for("react.memo_cache_sentinel")?(he={filter:Tl(en),order:ml(Hl),statusCategory:ml(["running","finished"]).withDefault("running")},Ie={history:"replace"},e[1]=he,e[2]=Ie):(he=e[1],Ie=e[2]);const[s,F]=Al(he,Ie),[we,Oe]=Ll("table_column_overrides.ProjectAdminDeploymentsPage"),[Ke,T]=Pl();let Ce;e[3]===Symbol.for("react.memo_cache_sentinel")?(Ce=["STOPPED"],e[3]=Ce):Ce=e[3];const Xe=Ce;let je;e[4]!==s.statusCategory?(je=s.statusCategory==="finished"?{status:{in:Xe}}:{status:{notIn:Xe}},e[4]=s.statusCategory,e[5]=je):je=e[5];const Ue=je;let A;e[6]!==s.filter?(A=s.filter??{},e[6]=s.filter,e[7]=A):A=e[7];let L;e[8]!==Ue||e[9]!==A?(L={...A,...Ue},e[8]=Ue,e[9]=A,e[10]=L):L=e[10];let P;e[11]!==s.order?(P=Nl(s.order),e[11]=s.order,e[12]=P):P=e[12];let Te;e[13]!==y.limit||e[14]!==y.offset||e[15]!==m||e[16]!==L||e[17]!==P?(Te={projectId:m,filter:L,orderBy:P,limit:y.limit,offset:y.offset},e[13]=y.limit,e[14]=y.offset,e[15]=m,e[16]=L,e[17]=P,e[18]=Te):Te=e[18];const Ze=Te,el=Fe.useDeferredValue(Ze),ve=Fe.useDeferredValue(Ke);let Ae;e[19]===Symbol.for("react.memo_cache_sentinel")?(Ae=Sl,e[19]=Ae):Ae=e[19];const Ee=ve===xl?"store-and-network":"network-only";let Le;e[20]!==ve||e[21]!==Ee?(Le={fetchKey:ve,fetchPolicy:Ee},e[20]=ve,e[21]=Ee,e[22]=Le):Le=e[22];const N=pl.useLazyLoadQuery(Ae,el,Le);let p,I,Pe,M;e[23]!==((ll=N.projectDeployments)==null?void 0:ll.count)||e[24]!==((nl=N.projectDeployments)==null?void 0:nl.edges)||e[25]!==v||e[26]!==d?(p=Ml(Rl((al=N.projectDeployments)==null?void 0:al.edges,"node")),M=((tl=N.projectDeployments)==null?void 0:tl.count)??0,I=d==null?null:p.find(i=>i.id===d)??null,Pe=v==null?null:p.find(i=>i.id===v)??null,e[23]=(il=N.projectDeployments)==null?void 0:il.count,e[24]=(rl=N.projectDeployments)==null?void 0:rl.edges,e[25]=v,e[26]=d,e[27]=p,e[28]=I,e[29]=Pe,e[30]=M):(p=e[27],I=e[28],Pe=e[29],M=e[30]);const r=Pe,R=el!==Ze||ve!==Ke;let Ne;e[31]===Symbol.for("react.memo_cache_sentinel")?(Ne=Fl,e[31]=Ne):Ne=e[31];const[$e,qe]=pl.useMutation(Ne);let x;e[32]!==l?(x=l("deployment.filter.Name"),e[32]=l,e[33]=x):x=e[33];let V;e[34]!==x?(V={key:"name",propertyLabel:x,type:"string"},e[34]=x,e[35]=V):V=e[35];let B;e[36]!==l?(B=l("deployment.filter.Tags"),e[36]=l,e[37]=B):B=e[37];let _;e[38]!==B?(_={key:"tags",propertyLabel:B,type:"string"},e[38]=B,e[39]=_):_=e[39];let w;e[40]!==l?(w=l("deployment.filter.EndpointUrl"),e[40]=l,e[41]=w):w=e[41];let O;e[42]!==w?(O={key:"endpointUrl",propertyLabel:w,type:"string"},e[42]=w,e[43]=O):O=e[43];let U;e[44]!==l?(U=l("deployment.filter.OpenToPublic"),e[44]=l,e[45]=U):U=e[45];let E;e[46]!==U?(E={key:"openToPublic",propertyLabel:U,type:"boolean"},e[46]=U,e[47]=E):E=e[47];let Me;e[48]!==V||e[49]!==_||e[50]!==O||e[51]!==E?(Me=[V,_,O,E],e[48]=V,e[49]=_,e[50]=O,e[51]=E,e[52]=Me):Me=e[52];const ze=Me;let Re;e[53]===Symbol.for("react.memo_cache_sentinel")?(Re={flexShrink:1},e[53]=Re):Re=e[53];const Dl=s.statusCategory;let $;e[54]!==F||e[55]!==k?($=i=>{F({statusCategory:i.target.value}),k({current:1})},e[54]=F,e[55]=k,e[56]=$):$=e[56];let q;e[57]!==l?(q=l("deployment.Running"),e[57]=l,e[58]=q):q=e[58];let z;e[59]!==q?(z={label:q,value:"running"},e[59]=q,e[60]=z):z=e[60];let G;e[61]!==l?(G=l("deployment.status.Terminated"),e[61]=l,e[62]=G):G=e[62];let Q;e[63]!==G?(Q={label:G,value:"finished"},e[63]=G,e[64]=Q):Q=e[64];let H;e[65]!==z||e[66]!==Q?(H=[z,Q],e[65]=z,e[66]=Q,e[67]=H):H=e[67];let W;e[68]!==s.statusCategory||e[69]!==$||e[70]!==H?(W=a.jsx(Bl,{optionType:"button",value:Dl,onChange:$,options:H}),e[68]=s.statusCategory,e[69]=$,e[70]=H,e[71]=W):W=e[71];const Ge=s.filter??void 0;let J;e[72]!==F||e[73]!==k?(J=i=>{F({filter:i??null}),k({current:1})},e[72]=F,e[73]=k,e[74]=J):J=e[74];let Y;e[75]!==ze||e[76]!==Ge||e[77]!==J?(Y=a.jsx(Jl,{filterProperties:ze,value:Ge,onChange:J}),e[75]=ze,e[76]=Ge,e[77]=J,e[78]=Y):Y=e[78];let X;e[79]!==W||e[80]!==Y?(X=a.jsxs(Ye,{gap:"sm",align:"start",wrap:"wrap",style:Re,children:[W,Y]}),e[79]=W,e[80]=Y,e[81]=X):X=e[81];let Z;e[82]!==T?(Z=i=>T(i),e[82]=T,e[83]=Z):Z=e[83];let ee;e[84]!==Ke||e[85]!==R||e[86]!==Z?(ee=a.jsx(_l,{settingId:"project-admin-deployments",defaultAutoUpdateDelay:15e3,loading:R,value:Ke,onChange:Z}),e[84]=Ke,e[85]=R,e[86]=Z,e[87]=ee):ee=e[87];let le;e[88]!==X||e[89]!==ee?(le=a.jsxs(Ye,{justify:"between",wrap:"wrap",gap:"sm",children:[X,ee]}),e[88]=X,e[89]=ee,e[90]=le):le=e[90];let ne;e[91]!==F?(ne=i=>{F({order:i??null})},e[91]=F,e[92]=ne):ne=e[92];let ae;e[93]!==k?(ae=(i,C)=>{k({current:i,pageSize:C})},e[93]=k,e[94]=ae):ae=e[94];let te;e[95]!==ae||e[96]!==f.current||e[97]!==f.pageSize||e[98]!==M?(te={current:f.current,pageSize:f.pageSize,total:M,onChange:ae},e[95]=ae,e[96]=f.current,e[97]=f.pageSize,e[98]=M,e[99]=te):te=e[99];let ie;e[100]!==we||e[101]!==Oe?(ie={columnOverrides:we,onColumnOverridesChange:Oe},e[100]=we,e[101]=Oe,e[102]=ie):ie=e[102];let re;e[103]!==t||e[104]!==p||e[105]!==l||e[106]!==o?(re=i=>{const C=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup","domainName","projectId"],Kl=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner"]);return i.filter(g=>C.includes(g.key)).map(g=>{let be=g;return g.key==="name"?be={...g,render:(dl,S)=>{var K,_e;const D=Yl((K=S.metadata)==null?void 0:K.status);return a.jsx(wl,{title:((_e=S.metadata)==null?void 0:_e.name)??"-",onTitleClick:()=>o(t(`deployments/${gl(S.id)}`)),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:a.jsx(Ol,{}),disabled:D,onClick:()=>Se(S.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:a.jsx(Ul,{size:"1em"}),type:"danger",disabled:D,onClick:()=>j(S.id)}]})}}:g.key==="currentRevisionNumber"?be={...g,render:(dl,S)=>{const D=p.find(_e=>_e.id===S.id),K=D==null?void 0:D.currentRevision;return(K==null?void 0:K.revisionNumber)==null?a.jsx(yl,{color:"secondary",children:"-"}):a.jsx(El,{onClick:()=>De(K),children:`#${K.revisionNumber}`})}}:g.key==="tags"&&(be={...g,render:(dl,S)=>a.jsx(Xl,{metadataFrgmt:S.metadata,stopRowClick:!0,onTagClick:D=>{o({pathname:t("deployments"),search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:D}})}).toString()})},fallback:a.jsx(yl,{color:"secondary",children:"-"})})}),g.key==="name"?be:{...be,defaultHidden:!Kl.has(g.key)}})},e[103]=t,e[104]=p,e[105]=l,e[106]=o,e[107]=re):re=e[107];let se;e[108]!==p||e[109]!==R||e[110]!==s.order||e[111]!==ne||e[112]!==te||e[113]!==ie||e[114]!==re?(se=a.jsx(Wl,{deploymentsFrgmt:p,loading:R,order:s.order,onChangeOrder:ne,pagination:te,tableSettings:ie,customizeColumns:re}),e[108]=p,e[109]=R,e[110]=s.order,e[111]=ne,e[112]=te,e[113]=ie,e[114]=re,e[115]=se):se=e[115];let oe;e[116]!==le||e[117]!==se?(oe=a.jsxs(Ye,{direction:"column",align:"stretch",gap:"sm",children:[le,se]}),e[116]=le,e[117]=se,e[118]=oe):oe=e[118];let ue;e[119]!==I?(ue=I!=null&&a.jsx(Gl,{open:!0,deploymentFrgmt:I,onRequestClose:()=>{Se(null)}}),e[119]=I,e[120]=ue):ue=e[120];const Qe=!!r;let de;e[121]!==l?(de=l("deployment.DeleteDeployment"),e[121]=l,e[122]=de):de=e[122];let ce;e[123]!==l?(ce=l("deployment.Deployment"),e[123]=l,e[124]=ce):ce=e[124];let me;e[125]!==r?(me=r?[{key:r.id,label:((sl=r.metadata)==null?void 0:sl.name)??""}]:[],e[125]=r,e[126]=me):me=e[126];const He=((ol=r==null?void 0:r.metadata)==null?void 0:ol.name)??"",We=((ul=r==null?void 0:r.metadata)==null?void 0:ul.name)??"";let pe;e[127]!==We?(pe={placeholder:We},e[127]=We,e[128]=pe):pe=e[128];let ge;e[129]!==qe?(ge={loading:qe},e[129]=qe,e[130]=ge):ge=e[130];let ye;e[131]!==$e||e[132]!==r||e[133]!==c||e[134]!==u||e[135]!==l||e[136]!==T?(ye=()=>{r&&$e({variables:{input:{id:gl(r.id)??r.id}},onCompleted:(i,C)=>{if(C&&C.length>0){c.error("Failed to delete deployment",C),u.error(l("deployment.FailedToDeleteDeployment"));return}u.success(l("deployment.DeploymentDeleted")),j(null),T()},onError:i=>{c.error("Failed to delete deployment",i),u.error(l("deployment.FailedToDeleteDeployment"))}})},e[131]=$e,e[132]=r,e[133]=c,e[134]=u,e[135]=l,e[136]=T,e[137]=ye):ye=e[137];let xe;e[138]===Symbol.for("react.memo_cache_sentinel")?(xe=()=>j(null),e[138]=xe):xe=e[138];let fe;e[139]!==Qe||e[140]!==de||e[141]!==ce||e[142]!==me||e[143]!==He||e[144]!==pe||e[145]!==ge||e[146]!==ye?(fe=a.jsx($l,{open:Qe,title:de,target:ce,items:me,confirmText:He,requireConfirmInput:!0,inputProps:pe,okButtonProps:ge,onOk:ye,onCancel:xe}),e[139]=Qe,e[140]=de,e[141]=ce,e[142]=me,e[143]=He,e[144]=pe,e[145]=ge,e[146]=ye,e[147]=fe):fe=e[147];const Je=!!b;let Ve;e[148]===Symbol.for("react.memo_cache_sentinel")?(Ve=()=>De(null),e[148]=Ve):Ve=e[148];let ke;e[149]!==b||e[150]!==Je?(ke=a.jsx(ql,{children:a.jsx(Ql,{open:Je,revisionFrgmt:b,onClose:Ve})}),e[149]=b,e[150]=Je,e[151]=ke):ke=e[151];let Be;return e[152]!==oe||e[153]!==ue||e[154]!==fe||e[155]!==ke?(Be=a.jsxs(a.Fragment,{children:[oe,ue,fe,ke]}),e[152]=oe,e[153]=ue,e[154]=fe,e[155]=ke,e[156]=Be):Be=e[156],Be},mn=()=>{"use memo";const n=fl.c(9),{t:e}=kl(),m=vl();let l;n[0]!==e?(l=e("webui.menu.ProjectDeployments"),n[0]=e,n[1]=l):l=n[1];let u;n[2]===Symbol.for("react.memo_cache_sentinel")?(u={header:{borderBottom:"none"},body:{paddingTop:0}},n[2]=u):u=n[2];let c;n[3]===Symbol.for("react.memo_cache_sentinel")?(c=a.jsx(cl,{}),n[3]=c):c=n[3];let o;n[4]!==m.id?(o=a.jsx(bl,{children:a.jsx(Fe.Suspense,{fallback:c,children:m.id?a.jsx(Zl,{projectId:m.id}):a.jsx(cl,{})})}),n[4]=m.id,n[5]=o):o=n[5];let t;return n[6]!==l||n[7]!==o?(t=a.jsx(zl,{variant:"borderless",title:l,styles:u,children:o}),n[6]=l,n[7]=o,n[8]=t):t=n[8],t};function en(n){return typeof n=="object"&&n!==null&&!Array.isArray(n)?n:{}}export{mn as default};
//# sourceMappingURL=ProjectAdminDeploymentsPage-DzlDoBzk.js.map
