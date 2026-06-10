import{h as Sl,u as bl,am as Cl,j as a,bI as Al,r as ke,ay as kl,A as Ll,v as Nl,p as Pl,br as Ml,bs as Dl,cV as Rl,bt as xl,a4 as _l,at as Bl,i as Fl,aM as Vl,a6 as wl,aw as Ol,cb as El,B as nl,aC as Ul,aY as $l,cW as ql,a_ as Gl,N as vl,T as al,cX as Ql,b6 as zl,a7 as Hl,bH as Wl}from"./index-CuMUOZIG.js";import{B as Jl,D as Yl}from"./DeploymentRevisionDetailDrawer-CqqYIRLX.js";import{p as Xl,B as Zl,a as en}from"./BAIModelDeploymentNodes-DHF_sHto.js";import{B as ln}from"./BAIGraphQLPropertyFilter-BJSph4O9.js";import"./FolderLink-B_vcYigG.js";import"./BAIId-BIK-PEa4.js";import"./BooleanTag-CNCumd6I.js";const Kl=function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"input"}],e=[{alias:null,args:[{kind:"Variable",name:"input",variableName:"input"}],concreteType:"DeleteDeploymentPayload",kind:"LinkedField",name:"deleteModelDeployment",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"ProjectAdminDeploymentsPageDeleteMutation",selections:e},params:{cacheID:"1463ddcf31aa971e7f72ca3901c5db76",id:null,metadata:{},name:"ProjectAdminDeploymentsPageDeleteMutation",operationKind:"mutation",text:`mutation ProjectAdminDeploymentsPageDeleteMutation(
  $input: DeleteDeploymentInput!
) {
  deleteModelDeployment(input: $input) {
    id
  }
}
`}}}();Kl.hash="42ff73332d0c41e5828ba82d49920b78";const hl=function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},m={defaultValue:null,kind:"LocalArgument",name:"offset"},l={defaultValue:null,kind:"LocalArgument",name:"orderBy"},d={defaultValue:null,kind:"LocalArgument",name:"projectId"},u=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{kind:"Variable",name:"projectId",variableName:"projectId"}],kind:"ObjectValue",name:"scope"}],o={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},j={alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},De=[o],h={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null};return{fragment:{argumentDefinitions:[n,e,m,l,d],kind:"Fragment",metadata:null,name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{args:null,kind:"FragmentSpread",name:"BAIModelDeploymentNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeploymentSettingModal_deployment"},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[c,b],storageKey:null},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,j,{args:null,kind:"FragmentSpread",name:"DeploymentRevisionDetail_revision"}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[d,n,l,e,m],kind:"Operation",name:"ProjectAdminDeploymentsPageQuery",selections:[{alias:null,args:u,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"projectDeployments",plural:!1,selections:[o,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"currentRevisionId",storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},c,b,{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null},K,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[c],storageKey:null},t],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"preferredDomainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"DeploymentStrategyGQL",kind:"LinkedField",name:"defaultDeploymentStrategy",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"totalReplicas",args:null,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:De,storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:De,storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,j,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,c],storageKey:null},h,g,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},K,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[c,t],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfoGQL",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[h,g,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,c,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[c,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[t,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"31eed7ba8e08208453c1d15f0aadc849",id:null,metadata:{},name:"ProjectAdminDeploymentsPageQuery",operationKind:"query",text:`query ProjectAdminDeploymentsPageQuery(
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
  totalReplicas: replicas {
    count
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
  modelRuntimeConfig {
    runtimeVariant {
      name
      id
    }
    environ {
      entries {
        name
        value
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
    }
  }
  modelDefinition {
    models {
      name
      modelPath
      service {
        startCommand
        port
        healthCheck {
          path
          initialDelay
          maxRetries
          interval
          maxWaitTime
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
}
`}}}();hl.hash="c0915455c90833c0f8fa382e2c4d6319";const nn=n=>{"use memo";var rl,ol,dl,ul,ml,cl,pl,yl,gl;const e=Sl.c(162),{projectId:m}=n,{t:l}=bl(),{message:d}=Ll.useApp(),{logger:u}=Nl(),o=Pl(),[t,c]=ke.useState(null),[b,j]=ke.useState(null),[K,De]=ke.useState(null);let h;e[0]===Symbol.for("react.memo_cache_sentinel")?(h={current:1,pageSize:10},e[0]=h):h=e[0];const{baiPaginationOption:g,tablePaginationOption:T,setTablePaginationOption:f}=Ml(h);let he,Ie;e[1]===Symbol.for("react.memo_cache_sentinel")?(he={filter:Rl(an),order:Dl(en),statusCategory:Dl(["running","finished"]).withDefault("running")},Ie={history:"replace"},e[1]=he,e[2]=Ie):(he=e[1],Ie=e[2]);const[r,k]=xl(he,Ie),[Ee,Ue]=_l("table_column_overrides.ProjectAdminDeploymentsPage"),[Fe,D]=Bl();let je;e[3]===Symbol.for("react.memo_cache_sentinel")?(je=["STOPPED"],e[3]=je):je=e[3];const tl=je;let Te;e[4]!==r.statusCategory?(Te=r.statusCategory==="finished"?{status:{in:tl}}:{status:{notIn:tl}},e[4]=r.statusCategory,e[5]=Te):Te=e[5];const $e=Te;let Ce;e[6]!==r.order?(Ce=Xl(r.order),e[6]=r.order,e[7]=Ce):Ce=e[7];const ve=Ce;let Ae;e[8]!==r.filter?(Ae=r.filter??{},e[8]=r.filter,e[9]=Ae):Ae=e[9];const qe=Ae;let C;e[10]!==$e||e[11]!==qe?(C={...qe,...$e},e[10]=$e,e[11]=qe,e[12]=C):C=e[12];let A;e[13]!==ve?(A=ve?[{field:ve.field,direction:ve.direction}]:void 0,e[13]=ve,e[14]=A):A=e[14];let Le;e[15]!==g.limit||e[16]!==g.offset||e[17]!==m||e[18]!==A||e[19]!==C?(Le={projectId:m,filter:C,orderBy:A,limit:g.limit,offset:g.offset},e[15]=g.limit,e[16]=g.offset,e[17]=m,e[18]=A,e[19]=C,e[20]=Le):Le=e[20];const il=Le,sl=ke.useDeferredValue(il),Se=ke.useDeferredValue(Fe);let Ne;e[21]===Symbol.for("react.memo_cache_sentinel")?(Ne=hl,e[21]=Ne):Ne=e[21];const Ge=Se===Ol?"store-and-network":"network-only";let Pe;e[22]!==Se||e[23]!==Ge?(Pe={fetchKey:Se,fetchPolicy:Ge},e[22]=Se,e[23]=Ge,e[24]=Pe):Pe=e[24];const L=Fl.useLazyLoadQuery(Ne,sl,Pe);let p,be,Me,N;e[25]!==((rl=L.projectDeployments)==null?void 0:rl.count)||e[26]!==((ol=L.projectDeployments)==null?void 0:ol.edges)||e[27]!==b||e[28]!==t?(p=Vl(wl((dl=L.projectDeployments)==null?void 0:dl.edges,"node")),N=((ul=L.projectDeployments)==null?void 0:ul.count)??0,be=t==null?null:p.find(i=>i.id===t)??null,Me=b==null?null:p.find(i=>i.id===b)??null,e[25]=(ml=L.projectDeployments)==null?void 0:ml.count,e[26]=(cl=L.projectDeployments)==null?void 0:cl.edges,e[27]=b,e[28]=t,e[29]=p,e[30]=be,e[31]=Me,e[32]=N):(p=e[29],be=e[30],Me=e[31],N=e[32]);const s=Me,P=sl!==il||Se!==Fe;let Re;e[33]===Symbol.for("react.memo_cache_sentinel")?(Re=Kl,e[33]=Re):Re=e[33];const[Qe,ze]=Fl.useMutation(Re);let M;e[34]!==l?(M=l("deployment.filter.Name"),e[34]=l,e[35]=M):M=e[35];let R;e[36]!==M?(R={key:"name",propertyLabel:M,type:"string"},e[36]=M,e[37]=R):R=e[37];let x;e[38]!==l?(x=l("deployment.filter.Tags"),e[38]=l,e[39]=x):x=e[39];let _;e[40]!==x?(_={key:"tags",propertyLabel:x,type:"string"},e[40]=x,e[41]=_):_=e[41];let B;e[42]!==l?(B=l("deployment.filter.EndpointUrl"),e[42]=l,e[43]=B):B=e[43];let V;e[44]!==B?(V={key:"endpointUrl",propertyLabel:B,type:"string"},e[44]=B,e[45]=V):V=e[45];let w;e[46]!==l?(w=l("deployment.filter.OpenToPublic"),e[46]=l,e[47]=w):w=e[47];let O;e[48]!==w?(O={key:"openToPublic",propertyLabel:w,type:"boolean"},e[48]=w,e[49]=O):O=e[49];let xe;e[50]!==R||e[51]!==_||e[52]!==V||e[53]!==O?(xe=[R,_,V,O],e[50]=R,e[51]=_,e[52]=V,e[53]=O,e[54]=xe):xe=e[54];const He=xe,Il=tn;let _e;e[55]===Symbol.for("react.memo_cache_sentinel")?(_e={flexShrink:1},e[55]=_e):_e=e[55];const jl=r.statusCategory;let E;e[56]!==k||e[57]!==f?(E=i=>{k({statusCategory:i.target.value}),f({current:1})},e[56]=k,e[57]=f,e[58]=E):E=e[58];let U;e[59]!==l?(U=l("deployment.Running"),e[59]=l,e[60]=U):U=e[60];let $;e[61]!==U?($={label:U,value:"running"},e[61]=U,e[62]=$):$=e[62];let q;e[63]!==l?(q=l("deployment.status.Terminated"),e[63]=l,e[64]=q):q=e[64];let G;e[65]!==q?(G={label:q,value:"finished"},e[65]=q,e[66]=G):G=e[66];let Q;e[67]!==$||e[68]!==G?(Q=[$,G],e[67]=$,e[68]=G,e[69]=Q):Q=e[69];let z;e[70]!==r.statusCategory||e[71]!==E||e[72]!==Q?(z=a.jsx(El,{optionType:"button",value:jl,onChange:E,options:Q}),e[70]=r.statusCategory,e[71]=E,e[72]=Q,e[73]=z):z=e[73];const We=r.filter??void 0;let H;e[74]!==k||e[75]!==f?(H=i=>{k({filter:i??null}),f({current:1})},e[74]=k,e[75]=f,e[76]=H):H=e[76];let W;e[77]!==He||e[78]!==We||e[79]!==H?(W=a.jsx(ln,{filterProperties:He,value:We,onChange:H}),e[77]=He,e[78]=We,e[79]=H,e[80]=W):W=e[80];let J;e[81]!==z||e[82]!==W?(J=a.jsxs(nl,{gap:"sm",align:"start",wrap:"wrap",style:_e,children:[z,W]}),e[81]=z,e[82]=W,e[83]=J):J=e[83];let Y;e[84]!==D?(Y=i=>D(i),e[84]=D,e[85]=Y):Y=e[85];let X;e[86]!==Fe||e[87]!==P||e[88]!==Y?(X=a.jsx(Ul,{loading:P,value:Fe,onChange:Y,autoUpdateDelay:15e3}),e[86]=Fe,e[87]=P,e[88]=Y,e[89]=X):X=e[89];let Z;e[90]!==J||e[91]!==X?(Z=a.jsxs(nl,{justify:"between",wrap:"wrap",gap:"sm",children:[J,X]}),e[90]=J,e[91]=X,e[92]=Z):Z=e[92];let ee;e[93]!==k?(ee=i=>{k({order:i??null})},e[93]=k,e[94]=ee):ee=e[94];let le;e[95]!==f?(le=(i,I)=>{f({current:i,pageSize:I})},e[95]=f,e[96]=le):le=e[96];let ne;e[97]!==le||e[98]!==T.current||e[99]!==T.pageSize||e[100]!==N?(ne={current:T.current,pageSize:T.pageSize,total:N,onChange:le},e[97]=le,e[98]=T.current,e[99]=T.pageSize,e[100]=N,e[101]=ne):ne=e[101];let ae;e[102]!==Ee||e[103]!==Ue?(ae={columnOverrides:Ee,onColumnOverridesChange:Ue},e[102]=Ee,e[103]=Ue,e[104]=ae):ae=e[104];let te;e[105]!==p||e[106]!==l||e[107]!==o?(te=i=>{const I=["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner","id","endpointUrl","tags","updatedAt","openToPublic","resourceGroup","domainName","projectId"],Tl=new Set(["name","currentRevisionNumber","status","replicaSummary","model","createdAt","owner"]);return i.filter(y=>I.includes(y.key)).map(y=>{let Ke=y;return y.key==="name"?Ke={...y,render:(fl,F)=>{var S,Oe;const v=Il((S=F.metadata)==null?void 0:S.status);return a.jsx($l,{title:((Oe=F.metadata)==null?void 0:Oe.name)??"-",onTitleClick:()=>o(`/project-admin-deployments/${vl(F.id)}`),copyable:!0,showActions:"always",actions:[{key:"edit",title:l("deployment.EditDeployment"),icon:a.jsx(ql,{}),disabled:v,onClick:()=>c(F.id)},{key:"delete",title:l("deployment.DeleteDeployment"),icon:a.jsx(Gl,{}),type:"danger",disabled:v,onClick:()=>j(F.id)}]})}}:y.key==="currentRevisionNumber"?Ke={...y,render:(fl,F)=>{const v=p.find(Oe=>Oe.id===F.id),S=v==null?void 0:v.currentRevision;return(S==null?void 0:S.revisionNumber)==null?a.jsx(al.Text,{type:"secondary",children:"-"}):a.jsx(al.Link,{onClick:()=>De(S),children:`#${S.revisionNumber}`})}}:y.key==="tags"&&(Ke={...y,render:(fl,F)=>a.jsx(Jl,{metadataFrgmt:F.metadata,stopRowClick:!0,onTagClick:v=>{o({pathname:"/project-admin-deployments",search:new URLSearchParams({filter:JSON.stringify({tags:{iContains:v}})}).toString()})},fallback:a.jsx(al.Text,{type:"secondary",children:"-"})})}),y.key==="name"?Ke:{...Ke,defaultHidden:!Tl.has(y.key)}})},e[105]=p,e[106]=l,e[107]=o,e[108]=te):te=e[108];let ie;e[109]!==p||e[110]!==P||e[111]!==r.order||e[112]!==ee||e[113]!==ne||e[114]!==ae||e[115]!==te?(ie=a.jsx(Zl,{deploymentsFrgmt:p,loading:P,order:r.order,onChangeOrder:ee,pagination:ne,tableSettings:ae,customizeColumns:te}),e[109]=p,e[110]=P,e[111]=r.order,e[112]=ee,e[113]=ne,e[114]=ae,e[115]=te,e[116]=ie):ie=e[116];let se;e[117]!==Z||e[118]!==ie?(se=a.jsxs(nl,{direction:"column",align:"stretch",gap:"sm",children:[Z,ie]}),e[117]=Z,e[118]=ie,e[119]=se):se=e[119];const Je=!!be,Ye=be??null;let re;e[120]!==D?(re=i=>{c(null),i&&D()},e[120]=D,e[121]=re):re=e[121];let oe;e[122]!==Je||e[123]!==Ye||e[124]!==re?(oe=a.jsx(Ql,{open:Je,deploymentFrgmt:Ye,onRequestClose:re}),e[122]=Je,e[123]=Ye,e[124]=re,e[125]=oe):oe=e[125];const Xe=!!s;let de;e[126]!==l?(de=l("deployment.DeleteDeployment"),e[126]=l,e[127]=de):de=e[127];let ue;e[128]!==l?(ue=l("deployment.Deployment"),e[128]=l,e[129]=ue):ue=e[129];let me;e[130]!==s?(me=s?[{key:s.id,label:((pl=s.metadata)==null?void 0:pl.name)??""}]:[],e[130]=s,e[131]=me):me=e[131];const Ze=((yl=s==null?void 0:s.metadata)==null?void 0:yl.name)??"",el=((gl=s==null?void 0:s.metadata)==null?void 0:gl.name)??"";let ce;e[132]!==el?(ce={placeholder:el},e[132]=el,e[133]=ce):ce=e[133];let pe;e[134]!==ze?(pe={loading:ze},e[134]=ze,e[135]=pe):pe=e[135];let ye;e[136]!==Qe||e[137]!==s||e[138]!==u||e[139]!==d||e[140]!==l||e[141]!==D?(ye=()=>{s&&Qe({variables:{input:{id:vl(s.id)??s.id}},onCompleted:(i,I)=>{if(I&&I.length>0){u.error("Failed to delete deployment",I),d.error(l("deployment.FailedToDeleteDeployment"));return}d.success(l("deployment.DeploymentDeleted")),j(null),D()},onError:i=>{u.error("Failed to delete deployment",i),d.error(l("deployment.FailedToDeleteDeployment"))}})},e[136]=Qe,e[137]=s,e[138]=u,e[139]=d,e[140]=l,e[141]=D,e[142]=ye):ye=e[142];let Be;e[143]===Symbol.for("react.memo_cache_sentinel")?(Be=()=>j(null),e[143]=Be):Be=e[143];let ge;e[144]!==Xe||e[145]!==de||e[146]!==ue||e[147]!==me||e[148]!==Ze||e[149]!==ce||e[150]!==pe||e[151]!==ye?(ge=a.jsx(zl,{open:Xe,title:de,target:ue,items:me,confirmText:Ze,requireConfirmInput:!0,inputProps:ce,okButtonProps:pe,onOk:ye,onCancel:Be}),e[144]=Xe,e[145]=de,e[146]=ue,e[147]=me,e[148]=Ze,e[149]=ce,e[150]=pe,e[151]=ye,e[152]=ge):ge=e[152];const ll=!!K;let Ve;e[153]===Symbol.for("react.memo_cache_sentinel")?(Ve=()=>De(null),e[153]=Ve):Ve=e[153];let fe;e[154]!==K||e[155]!==ll?(fe=a.jsx(Hl,{children:a.jsx(Yl,{open:ll,revisionFrgmt:K,onClose:Ve})}),e[154]=K,e[155]=ll,e[156]=fe):fe=e[156];let we;return e[157]!==se||e[158]!==oe||e[159]!==ge||e[160]!==fe?(we=a.jsxs(a.Fragment,{children:[se,oe,ge,fe]}),e[157]=se,e[158]=oe,e[159]=ge,e[160]=fe,e[161]=we):we=e[161],we},pn=()=>{"use memo";const n=Sl.c(9),{t:e}=bl(),m=Cl();let l;n[0]!==e?(l=e("webui.menu.ProjectDeployments"),n[0]=e,n[1]=l):l=n[1];let d;n[2]===Symbol.for("react.memo_cache_sentinel")?(d={header:{borderBottom:"none"},body:{paddingTop:0}},n[2]=d):d=n[2];let u;n[3]===Symbol.for("react.memo_cache_sentinel")?(u=a.jsx(kl,{active:!0}),n[3]=u):u=n[3];let o;n[4]!==m.id?(o=a.jsx(Al,{children:a.jsx(ke.Suspense,{fallback:u,children:m.id?a.jsx(nn,{projectId:m.id}):a.jsx(kl,{active:!0})})}),n[4]=m.id,n[5]=o):o=n[5];let t;return n[6]!==l||n[7]!==o?(t=a.jsx(Wl,{variant:"borderless",title:l,styles:d,children:o}),n[6]=l,n[7]=o,n[8]=t):t=n[8],t};function an(n){return typeof n=="object"&&n!==null&&!Array.isArray(n)?n:{}}function tn(n){return!n||n==="%future added value"?!1:["STOPPING","STOPPED","TERMINATED"].includes(n)}export{pn as default};
//# sourceMappingURL=ProjectAdminDeploymentsPage-PaqEoQ1Z.js.map
