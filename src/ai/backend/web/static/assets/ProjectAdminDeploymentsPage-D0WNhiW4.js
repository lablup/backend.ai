import{i as kn,u as Fn,z as bn,j as a,cr as In,l as Se,aV as cn,x as hn,Y as Tn,Z as jn,bG as Ln,ca as pn,ag as An,ae as Cn,a7 as Nn,aN as Pn,aS as Mn,r as gn,aT as Vn,al as Rn,bh as xn,X as Bn,dg as _n,c as Ye,dF as wn,bI as On,aK as En,aM as Un,N as yn,a2 as fn,L as $n,bO as qn,ao as zn,d as Gn}from"./index-Bg9dLa8r.js";import{D as Qn,a as Hn}from"./DeploymentSettingModal-C6pW9IYJ.js";import{a as Wn,B as Jn}from"./BAIModelDeploymentNodes-CL_ZUHok.js";import{B as Yn}from"./BAIGraphQLPropertyFilter-CsaKfYKW.js";import{i as Xn,B as Zn}from"./BAIDeploymentTagTokens-ZxoaXw6A.js";import"./parseCliCommand-DLNI3aPC.js";import"./FolderLink-QnkTdekF.js";import"./BAIBooleanToken-Dgc-5MGf.js";const Sn=(function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e},params:{cacheID:"1463ddcf31aa971e7f72ca3901c5db76",id:null,metadata:{},name:"ProjectAdminDeploymentsPageDeleteMutation",operationKind:"mutation",text:`mutation ProjectAdminDeploymentsPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}})();Sn.hash="42ff73332d0c41e5828ba82d49920b78";const Dn=(function(){var l={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},p={defaultValue:null,kind:"LocalArgument",name:"offset"},n={defaultValue:null,kind:"LocalArgument",name:"orderBy"},u={defaultValue:null,kind:"LocalArgument",name:"projectId"},m=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},De={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},b={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,d,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},ve={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},I={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},k=[d,f],c={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},h=[c,f];return{fragment:{argumentDefinitions:[l,e,p,n,u],kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:m,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[d,De],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,K,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[u,l,n,e,p],kind:"Operation",name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:m,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},d,De,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},L,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[d],storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategy",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:[o],storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,K,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[b,ve,I,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"subpath",storageKey:null}],storageKey:null},L,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ResourceConfig",kind:"LinkedField",name:"resourceConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOpts",kind:"LinkedField",name:"resourceOpts",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceOptsEntry",kind:"LinkedField",name:"entries",plural:!0,selections:k,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[d,t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"inferenceRuntimeConfig",storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:k,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantPresetValue",kind:"LinkedField",name:"runtimeVariantPresetValues",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"presetId",storageKey:null},f,{alias:null,args:null,concreteType:"RuntimeVariantPreset",kind:"LinkedField",name:"preset",plural:!1,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"displayName",storageKey:null},{alias:null,args:null,concreteType:"PresetTargetSpec",kind:"LinkedField",name:"targetSpec",plural:!1,selections:[c],storageKey:null},t],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfo",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[ve,I,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},b],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2TagEntry",kind:"LinkedField",name:"tags",plural:!0,selections:h,storageKey:null},{alias:null,args:null,concreteType:"ImageV2LabelEntry",kind:"LinkedField",name:"labels",plural:!0,selections:h,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"command",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"shell",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"PreStartAction",kind:"LinkedField",name:"preStartActions",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"action",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"args",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"expectedStatusCode",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[t,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"5f7ebeb075011440a16eb67ee86b71f9",id:null,metadata:{},name:"ProjectAdminDeploymentsPageQuery",operationKind:"query",text:`query ProjectAdminDeploymentsPageQuery(
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

fragment BAIDeploymentTagTokens_metadata on ModelDeploymentMetadata {
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
`}}})();Dn.hash="c0915455c90833c0f8fa382e2c4d6319";const el=l=>{"use memo";var nn,ln,an,tn,rn,sn,on,un,dn;const e=kn.c(157),{projectId:p}=l,{t:n}=Fn(),{message:u}=Bn.useApp(),{logger:m}=hn(),o=Tn(),t=jn(),[d,De]=Se.useState(null),[K,L]=Se.useState(null),[b,ve]=Se.useState(null);let I;e[0]===Symbol.for("react.memo_cache_sentinel")?(I={current:1,pageSize:10},e[0]=I):I=e[0];const{baiPaginationOption:f,tablePaginationOption:k,setTablePaginationOption:c}=Ln(I);let h,he;e[1]===Symbol.for("react.memo_cache_sentinel")?(h={filter:An(nl),order:pn(Wn),statusCategory:pn(["running","finished"]).withDefault("running")},he={history:"replace"},e[1]=h,e[2]=he):(h=e[1],he=e[2]);const[s,F]=Cn(h,he),[we,Oe]=Nn("table_column_overrides.ProjectAdminDeploymentsPage"),[Ke,A]=Pn();let Te;e[3]===Symbol.for("react.memo_cache_sentinel")?(Te=["STOPPED"],e[3]=Te):Te=e[3];const Xe=Te;let je;e[4]!==s.statusCategory?(je=s.statusCategory==="finished"?{status:{in:Xe}}:{status:{notIn:Xe}},e[4]=s.statusCategory,e[5]=je):je=e[5];const Ee=je;let C;e[6]!==s.filter?(C=s.filter??{},e[6]=s.filter,e[7]=C):C=e[7];let N;e[8]!==Ee||e[9]!==C?(N={...C,...Ee},e[8]=Ee,e[9]=C,e[10]=N):N=e[10];let P;e[11]!==s.order?(P=Mn(s.order),e[11]=s.order,e[12]=P):P=e[12];let Le;e[13]!==f.limit||e[14]!==f.offset||e[15]!==p||e[16]!==N||e[17]!==P?(Le={projectId:p,filter:N,orderBy:P,limit:f.limit,offset:f.offset},e[13]=f.limit,e[14]=f.offset,e[15]=p,e[16]=N,e[17]=P,e[18]=Le):Le=e[18];const Ze=Le,en=Se.useDeferredValue(Ze),be=Se.useDeferredValue(Ke);let Ae;e[19]===Symbol.for("react.memo_cache_sentinel")?(Ae=Dn,e[19]=Ae):Ae=e[19];const Ue=be===xn?"store-and-network":"network-only";let Ce;e[20]!==be||e[21]!==Ue?(Ce={fetchKey:be,fetchPolicy:Ue},e[20]=be,e[21]=Ue,e[22]=Ce):Ce=e[22];const M=gn.useLazyLoadQuery(Ae,en,Ce);let g,T,Ne,V;e[23]!==((nn=M.projectDeployments)==null?void 0:nn.count)||e[24]!==((ln=M.projectDeployments)==null?void 0:ln.edges)||e[25]!==K||e[26]!==d?(g=Vn(Rn((an=M.projectDeployments)==null?void 0:an.edges,"node")),V=((tn=M.projectDeployments)==null?void 0:tn.count)??0,T=d==null?null:g.find(i=>i.id===d)??null,Ne=K==null?null:g.find(i=>i.id===K)??null,e[23]=(rn=M.projectDeployments)==null?void 0:rn.count,e[24]=(sn=M.projectDeployments)==null?void 0:sn.edges,e[25]=K,e[26]=d,e[27]=g,e[28]=T,e[29]=Ne,e[30]=V):(g=e[27],T=e[28],Ne=e[29],V=e[30]);const r=Ne,R=en!==Ze||be!==Ke;let Pe;e[31]===Symbol.for("react.memo_cache_sentinel")?(Pe=Sn,e[31]=Pe):Pe=e[31];const[$e,qe]=gn.useMutation(Pe);let x;e[32]!==n?(x=n("deployment.filter.Name"),e[32]=n,e[33]=x):x=e[33];let B;e[34]!==x?(B={key:"name",propertyLabel:x,type:"string"},e[34]=x,e[35]=B):B=e[35];let _;e[36]!==n?(_=n("deployment.filter.Tags"),e[36]=n,e[37]=_):_=e[37];let w;e[38]!==_?(w={key:"tags",propertyLabel:_,type:"string"},e[38]=_,e[39]=w):w=e[39];let O;e[40]!==n?(O=n("deployment.filter.EndpointUrl"),e[40]=n,e[41]=O):O=e[41];let E;e[42]!==O?(E={key:"endpointUrl",propertyLabel:O,type:"string"},e[42]=O,e[43]=E):E=e[43];let U;e[44]!==n?(U=n("deployment.filter.OpenToPublic"),e[44]=n,e[45]=U):U=e[45];let $;e[46]!==U?($={key:"openToPublic",propertyLabel:U,type:"boolean"},e[46]=U,e[47]=$):$=e[47];let Me;e[48]!==B||e[49]!==w||e[50]!==E||e[51]!==$?(Me=[B,w,E,$],e[48]=B,e[49]=w,e[50]=E,e[51]=$,e[52]=Me):Me=e[52];const ze=Me;let Ve;e[53]===Symbol.for("react.memo_cache_sentinel")?(Ve={flexShrink:1},e[53]=Ve):Ve=e[53];const vn=s.statusCategory;let q;e[54]!==F||e[55]!==c?(q=i=>{F({statusCategory:i.target.value}),c({current:1})},e[54]=F,e[55]=c,e[56]=q):q=e[56];let z;e[57]!==n?(z=n("deployment.Running"),e[57]=n,e[58]=z):z=e[58];let G;e[59]!==z?(G={label:z,value:"running"},e[59]=z,e[60]=G):G=e[60];let Q;e[61]!==n?(Q=n("deployment.status.Terminated"),e[61]=n,e[62]=Q):Q=e[62];let H;e[63]!==Q?(H={label:Q,value:"finished"},e[63]=Q,e[64]=H):H=e[64];let W;e[65]!==G||e[66]!==H?(W=[G,H],e[65]=G,e[66]=H,e[67]=W):W=e[67];let J;e[68]!==s.statusCategory||e[69]!==q||e[70]!==W?(J=a.jsx(_n,{optionType:"button",value:vn,onChange:q,options:W}),e[68]=s.statusCategory,e[69]=q,e[70]=W,e[71]=J):J=e[71];const Ge=s.filter??void 0;let Y;e[72]!==F||e[73]!==c?(Y=i=>{F({filter:i??null}),c({current:1})},e[72]=F,e[73]=c,e[74]=Y):Y=e[74];let X;e[75]!==ze||e[76]!==Ge||e[77]!==Y?(X=a.jsx(Yn,{filterProperties:ze,value:Ge,onChange:Y}),e[75]=ze,e[76]=Ge,e[77]=Y,e[78]=X):X=e[78];let Z;e[79]!==J||e[80]!==X?(Z=a.jsxs(Ye,{gap:"sm",align:"start",wrap:"wrap",style:Ve,children:[J,X]}),e[79]=J,e[80]=X,e[81]=Z):Z=e[81];let ee;e[82]!==A?(ee=i=>A(i),e[82]=A,e[83]=ee):ee=e[83];let ne;e[84]!==Ke||e[85]!==R||e[86]!==ee?(ne=a.jsx(wn,{settingId:"project-admin-deployments",defaultAutoUpdateDelay:15e3,loading:R,value:Ke,onChange:ee}),e[84]=Ke,e[85]=R,e[86]=ee,e[87]=ne):ne=e[87];let le;e[88]!==Z||e[89]!==ne?(le=a.jsxs(Ye,{justify:"between",wrap:"wrap",gap:"sm",children:[Z,ne]}),e[88]=Z,e[89]=ne,e[90]=le):le=e[90];let ae;e[91]!==F?(ae=i=>{F({order:i??null})},e[91]=F,e[92]=ae):ae=e[92];let te;e[93]!==c?(te=(i,j)=>{c({current:i,pageSize:j})},e[93]=c,e[94]=te):te=e[94];let ie;e[95]!==te||e[96]!==k.current||e[97]!==k.pageSize||e[98]!==V?(ie={current:k.current,pageSize:k.pageSize,total:V,onChange:te},e[95]=te,e[96]=k.current,e[97]=k.pageSize,e[98]=V,e[99]=ie):ie=e[99];let re;e[100]!==we||e[101]!==Oe?(re={columnOverrides:we,onColumnOverridesChange:Oe},e[100]=we,e[101]=Oe,e[102]=re):re=e[102];let se;e[103]!==t||e[104]!==g||e[105]!==n||e[106]!==o?(se=i=>{const j=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup","domainName","projectId"],Kn=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner"]);return i.filter(y=>j.includes(y.key)).map(y=>{let Ie=y;return y.key==="name"?Ie={...y,render:(mn,S)=>{var v,_e;const D=Xn((v=S.metadata)==null?void 0:v.status);return a.jsx(On,{title:((_e=S.metadata)==null?void 0:_e.name)??"-",onTitleClick:()=>o(t(`deployments/${yn(S.id)}`)),copyable:!0,showActions:"always",actions:[{key:"edit",title:n("deployment.EditDeployment"),icon:a.jsx(En,{}),disabled:D,onClick:()=>De(S.id)},{key:"delete",title:n("deployment.DeleteDeployment"),icon:a.jsx(Un,{size:"1em"}),type:"danger",disabled:D,onClick:()=>L(S.id)}]})}}:y.key==="currentRevisionNumber"?Ie={...y,render:(mn,S)=>{const D=g.find(_e=>_e.id===S.id),v=D==null?void 0:D.currentRevision;return(v==null?void 0:v.revisionNumber)==null?a.jsx(fn,{color:"secondary",children:"-"}):a.jsx($n,{onClick:()=>ve(v),children:`#${v.revisionNumber}`})}}:y.key==="tags"&&(Ie={...y,render:(mn,S)=>a.jsx(Zn,{metadataFrgmt:S.metadata,stopRowClick:!0,onTagClick:D=>{o({pathname:t("deployments"),search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:D}})}).toString()})},fallback:a.jsx(fn,{color:"secondary",children:"-"})})}),y.key==="name"?Ie:{...Ie,defaultHidden:!Kn.has(y.key)}})},e[103]=t,e[104]=g,e[105]=n,e[106]=o,e[107]=se):se=e[107];let oe;e[108]!==g||e[109]!==R||e[110]!==s.order||e[111]!==ae||e[112]!==ie||e[113]!==re||e[114]!==se?(oe=a.jsx(Jn,{deploymentsFrgmt:g,loading:R,order:s.order,onChangeOrder:ae,pagination:ie,tableSettings:re,customizeColumns:se}),e[108]=g,e[109]=R,e[110]=s.order,e[111]=ae,e[112]=ie,e[113]=re,e[114]=se,e[115]=oe):oe=e[115];let ue;e[116]!==le||e[117]!==oe?(ue=a.jsxs(Ye,{direction:"column",align:"stretch",gap:"sm",children:[le,oe]}),e[116]=le,e[117]=oe,e[118]=ue):ue=e[118];let de;e[119]!==T?(de=T!=null&&a.jsx(Qn,{open:!0,deploymentFrgmt:T,onRequestClose:()=>{De(null)}}),e[119]=T,e[120]=de):de=e[120];const Qe=!!r;let me;e[121]!==n?(me=n("deployment.DeleteDeployment"),e[121]=n,e[122]=me):me=e[122];let ce;e[123]!==n?(ce=n("deployment.Deployment"),e[123]=n,e[124]=ce):ce=e[124];let pe;e[125]!==r?(pe=r?[{key:r.id,label:((on=r.metadata)==null?void 0:on.name)??""}]:[],e[125]=r,e[126]=pe):pe=e[126];const He=((un=r==null?void 0:r.metadata)==null?void 0:un.name)??"",We=((dn=r==null?void 0:r.metadata)==null?void 0:dn.name)??"";let ge;e[127]!==We?(ge={placeholder:We},e[127]=We,e[128]=ge):ge=e[128];let ye;e[129]!==qe?(ye={loading:qe},e[129]=qe,e[130]=ye):ye=e[130];let fe;e[131]!==$e||e[132]!==r||e[133]!==m||e[134]!==u||e[135]!==n||e[136]!==A?(fe=()=>{r&&$e({variables:{input:{id:yn(r.id)??r.id}},onCompleted:(i,j)=>{if(j&&j.length>0){m.error("Failed to delete deployment",j),u.error(n("deployment.FailedToDeleteDeployment"));return}u.success(n("deployment.DeploymentDeleted")),L(null),A()},onError:i=>{m.error("Failed to delete deployment",i),u.error(n("deployment.FailedToDeleteDeployment"))}})},e[131]=$e,e[132]=r,e[133]=m,e[134]=u,e[135]=n,e[136]=A,e[137]=fe):fe=e[137];let Re;e[138]===Symbol.for("react.memo_cache_sentinel")?(Re=()=>L(null),e[138]=Re):Re=e[138];let ke;e[139]!==Qe||e[140]!==me||e[141]!==ce||e[142]!==pe||e[143]!==He||e[144]!==ge||e[145]!==ye||e[146]!==fe?(ke=a.jsx(qn,{open:Qe,title:me,target:ce,items:pe,confirmText:He,requireConfirmInput:!0,inputProps:ge,okButtonProps:ye,onOk:fe,onCancel:Re}),e[139]=Qe,e[140]=me,e[141]=ce,e[142]=pe,e[143]=He,e[144]=ge,e[145]=ye,e[146]=fe,e[147]=ke):ke=e[147];const Je=!!b;let xe;e[148]===Symbol.for("react.memo_cache_sentinel")?(xe=()=>ve(null),e[148]=xe):xe=e[148];let Fe;e[149]!==b||e[150]!==Je?(Fe=a.jsx(zn,{children:a.jsx(Hn,{open:Je,revisionFrgmt:b,onClose:xe})}),e[149]=b,e[150]=Je,e[151]=Fe):Fe=e[151];let Be;return e[152]!==ue||e[153]!==de||e[154]!==ke||e[155]!==Fe?(Be=a.jsxs(a.Fragment,{children:[ue,de,ke,Fe]}),e[152]=ue,e[153]=de,e[154]=ke,e[155]=Fe,e[156]=Be):Be=e[156],Be},dl=()=>{"use memo";const l=kn.c(9),{t:e}=Fn(),p=bn();let n;l[0]!==e?(n=e("webui.menu.ProjectDeployments"),l[0]=e,l[1]=n):n=l[1];let u;l[2]===Symbol.for("react.memo_cache_sentinel")?(u={header:{borderBottom:"none"},body:{paddingTop:0}},l[2]=u):u=l[2];let m;l[3]===Symbol.for("react.memo_cache_sentinel")?(m=a.jsx(cn,{}),l[3]=m):m=l[3];let o;l[4]!==p.id?(o=a.jsx(In,{children:a.jsx(Se.Suspense,{fallback:m,children:p.id?a.jsx(el,{projectId:p.id}):a.jsx(cn,{})})}),l[4]=p.id,l[5]=o):o=l[5];let t;return l[6]!==n||l[7]!==o?(t=a.jsx(Gn,{variant:"borderless",title:n,styles:u,children:o}),l[6]=n,l[7]=o,l[8]=t):t=l[8],t};function nl(l){return typeof l=="object"&&l!==null&&!Array.isArray(l)?l:{}}export{dl as default};
//# sourceMappingURL=ProjectAdminDeploymentsPage-D0WNhiW4.js.map
