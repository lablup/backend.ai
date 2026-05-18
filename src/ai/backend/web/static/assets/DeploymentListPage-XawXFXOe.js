import{h as ge,u as ye,j as s,r as Y,az as Ke,B as pe,bK as Se,p as ve,aX as De,bt as Ce,bu as me,cX as Le,bv as be,a4 as he,au as Te,an as Ne,i as Ie,ax as _e,N as Re,aD as Me,b3 as Ve,cY as Pe}from"./index-M9a7wauv.js";import{t as xe,a as je,D as Ae}from"./DeploymentList-DiFvAerm.js";import"./DeploymentTagChips-DGmoCFj5.js";import"./FolderLink-B4Tyaydh.js";import"./BAIId-CgZSCiQm.js";import"./BAIGraphQLPropertyFilter-FbNAR0Ex.js";const fe=function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},o={defaultValue:null,kind:"LocalArgument",name:"limit"},n={defaultValue:null,kind:"LocalArgument",name:"offset"},u={defaultValue:null,kind:"LocalArgument",name:"orderBy"},d=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],r={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},V={alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},p=[r],c={alias:null,args:null,kind:"ScalarField",name:"vfolderId",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"mountDestination",storageKey:null};return{fragment:{argumentDefinitions:[e,o,n,u],kind:"Fragment",metadata:null,name:"DeploymentListPageQuery",selections:[{alias:null,args:d,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"DeploymentList_modelDeploymentConnection"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,u,o,n],kind:"Operation",name:"DeploymentListPageQuery",selections:[{alias:null,args:d,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},V,{alias:null,args:null,kind:"ScalarField",name:"updatedAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"projectV2",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[i],storageKey:null},t],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"totalReplicas",args:null,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:p,storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:p,storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[t,{alias:null,args:null,kind:"ScalarField",name:"revisionNumber",storageKey:null},{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,i],storageKey:null},c,f,{alias:null,args:null,kind:"ScalarField",name:"definitionPath",storageKey:null}],storageKey:null},V,{alias:null,args:null,concreteType:"ClusterConfig",kind:"LinkedField",name:"clusterConfig",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"AllocatedResourceSlot",kind:"LinkedField",name:"resourceSlots",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"slotName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelRuntimeConfig",kind:"LinkedField",name:"modelRuntimeConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"RuntimeVariant",kind:"LinkedField",name:"runtimeVariant",plural:!1,selections:[i,t],storageKey:null},{alias:null,args:null,concreteType:"EnvironmentVariables",kind:"LinkedField",name:"environ",plural:!1,selections:[{alias:null,args:null,concreteType:"EnvironmentVariableEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ExtraVFolderMountInfoGQL",kind:"LinkedField",name:"extraMounts",plural:!0,selections:[c,f,{alias:null,args:null,kind:"ScalarField",name:"mountPerm",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[t,i,{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"imageV2",plural:!1,selections:[t,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDefinition",kind:"LinkedField",name:"modelDefinition",plural:!1,selections:[{alias:null,args:null,concreteType:"ModelConfig",kind:"LinkedField",name:"models",plural:!0,selections:[i,{alias:null,args:null,kind:"ScalarField",name:"modelPath",storageKey:null},{alias:null,args:null,concreteType:"ModelServiceConfig",kind:"LinkedField",name:"service",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"startCommand",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"port",storageKey:null},{alias:null,args:null,concreteType:"ModelHealthCheck",kind:"LinkedField",name:"healthCheck",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"initialDelay",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxRetries",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"interval",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"maxWaitTime",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[t,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"9937abd2651a163d2a80b2b0ce10161a",id:null,metadata:{},name:"DeploymentListPageQuery",operationKind:"query",text:`query DeploymentListPageQuery(
  $filter: DeploymentFilter
  $orderBy: [DeploymentOrderBy!]
  $limit: Int
  $offset: Int
) {
  myDeployments(filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    ...DeploymentList_modelDeploymentConnection
  }
}

fragment DeploymentList_modelDeploymentConnection on ModelDeploymentConnection {
  count
  edges {
    node {
      id
      metadata {
        name
        status
        createdAt
        updatedAt
        domainName
        projectId
        projectV2 @since(version: "26.4.3") {
          basicInfo {
            name
          }
          id
        }
        resourceGroupName
        ...DeploymentTagChips_metadata
      }
      networkAccess {
        endpointUrl
        openToPublic
      }
      replicaState {
        desiredReplicaCount
      }
      ...DeploymentSettingModal_deployment
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
        ...DeploymentRevisionDetail_revision
      }
      ...DeploymentOwnerInfo_deployment
    }
  }
}

fragment DeploymentOwnerInfo_deployment on ModelDeployment {
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

fragment DeploymentTagChips_metadata on ModelDeploymentMetadata {
  tags
}

fragment FolderLink_vfolderNode on VirtualFolderNode {
  row_id
  name
}
`}}}();fe.hash="50f6f6b4035dc52329cd996125c886ea";const Be=()=>{"use memo";const e=ge.c(82),{t:o}=ye(),n=ve(),[u,d]=De(!1),{setLeft:r,setRight:t}=d,[i,V]=Y.useState(null);let p;e[0]===Symbol.for("react.memo_cache_sentinel")?(p={current:1,pageSize:10},e[0]=p):p=e[0];const{baiPaginationOption:c,tablePaginationOption:f,setTablePaginationOption:m}=Ce(p);let A,B;e[1]===Symbol.for("react.memo_cache_sentinel")?(A={filter:Le(Oe),order:me(je),statusCategory:me(["running","finished"]).withDefault("running")},B={history:"replace"},e[1]=A,e[2]=B):(A=e[1],B=e[2]);const[l,g]=be(A,B),[J,Z]=he("table_column_overrides.DeploymentListPage"),[P,y]=Te(),O=Ne();let E;e[3]!==l.order?(E=xe(l.order),e[3]=l.order,e[4]=E):E=e[4];const x=E;let w;e[5]!==x?(w=x?[{field:x.field,direction:x.order}]:void 0,e[5]=x,e[6]=w):w=e[6];const ee=w;let q;e[7]===Symbol.for("react.memo_cache_sentinel")?(q=["STOPPED"],e[7]=q):q=e[7];const ue=q;let $;e[8]!==l.statusCategory?($=l.statusCategory==="finished"?{status:{in:ue}}:{status:{notIn:ue}},e[8]=l.statusCategory,e[9]=$):$=e[9];const le=$;let Q;e[10]!==O.id?(Q=O.id?{projectId:{equals:O.id}}:{},e[10]=O.id,e[11]=Q):Q=e[11];const ne=Q;let U;e[12]!==l.filter?(U=l.filter??{},e[12]=l.filter,e[13]=U):U=e[13];const ae=U;let k;e[14]!==ne||e[15]!==le||e[16]!==ae?(k={...ae,...le,...ne},e[14]=ne,e[15]=le,e[16]=ae,e[17]=k):k=e[17];let G;e[18]!==c.limit||e[19]!==c.offset||e[20]!==ee||e[21]!==k?(G={filter:k,orderBy:ee,limit:c.limit,offset:c.offset},e[18]=c.limit,e[19]=c.offset,e[20]=ee,e[21]=k,e[22]=G):G=e[22];const de=G,ce=Y.useDeferredValue(de),j=Y.useDeferredValue(P);let z;e[23]===Symbol.for("react.memo_cache_sentinel")?(z=fe,e[23]=z):z=e[23];const te=j===_e?"store-and-network":"network-only";let W;e[24]!==j||e[25]!==te?(W={fetchPolicy:te,fetchKey:j},e[24]=j,e[25]=te,e[26]=W):W=e[26];const{myDeployments:ie}=Ie.useLazyLoadQuery(z,ce,W),F=ce!==de||j!==P,se=l.filter??void 0;let K;e[27]!==g||e[28]!==m?(K=a=>{g({filter:a??null}),m({current:1})},e[27]=g,e[28]=m,e[29]=K):K=e[29];const re=l.order??void 0;let S;e[30]!==g?(S=a=>{g({order:a??null})},e[30]=g,e[31]=S):S=e[31];const ke=l.statusCategory;let v;e[32]!==g||e[33]!==m?(v=a=>{g({statusCategory:a}),m({current:1})},e[32]=g,e[33]=m,e[34]=v):v=e[34];let D;e[35]!==m?(D=(a,Fe)=>{m({current:a,pageSize:Fe})},e[35]=m,e[36]=D):D=e[36];let C;e[37]!==D||e[38]!==f?(C={...f,onChange:D},e[37]=D,e[38]=f,e[39]=C):C=e[39];let L;e[40]!==J||e[41]!==Z?(L={columnOverrides:J,onColumnOverridesChange:Z},e[40]=J,e[41]=Z,e[42]=L):L=e[42];let b;e[43]!==n?(b=a=>{n(`/deployments/${Re(a)}`)},e[43]=n,e[44]=b):b=e[44];let H;e[45]===Symbol.for("react.memo_cache_sentinel")?(H=a=>V(a),e[45]=H):H=e[45];let h;e[46]!==P||e[47]!==F||e[48]!==y?(h=s.jsx(Me,{autoUpdateDelay:15e3,value:P,onChange:y,loading:F}),e[46]=P,e[47]=F,e[48]=y,e[49]=h):h=e[49];let T;e[50]!==o?(T=o("deployment.CreateDeployment"),e[50]=o,e[51]=T):T=e[51];let N;e[52]!==t||e[53]!==T?(N=s.jsx(Ve,{type:"primary",onClick:t,children:T}),e[52]=t,e[53]=T,e[54]=N):N=e[54];let I;e[55]!==h||e[56]!==N?(I=s.jsxs(pe,{gap:"xs",align:"center",children:[h,N]}),e[55]=h,e[56]=N,e[57]=I):I=e[57];let _;e[58]!==F||e[59]!==ie||e[60]!==l.statusCategory||e[61]!==se||e[62]!==K||e[63]!==re||e[64]!==S||e[65]!==v||e[66]!==C||e[67]!==L||e[68]!==b||e[69]!==I||e[70]!==y?(_=s.jsx(Ae,{deploymentsFrgmt:ie,filter:se,setFilter:K,order:re,onChangeOrder:S,statusCategory:ke,onStatusCategoryChange:v,pagination:C,tableSettings:L,mode:"user",loading:F,onRowClick:b,onEditClick:H,onDeleteComplete:y,toolbarEnd:I}),e[58]=F,e[59]=ie,e[60]=l.statusCategory,e[61]=se,e[62]=K,e[63]=re,e[64]=S,e[65]=v,e[66]=C,e[67]=L,e[68]=b,e[69]=I,e[70]=y,e[71]=_):_=e[71];const oe=u||!!i;let R;e[72]!==r||e[73]!==y?(R=a=>{r(),V(null),a&&y()},e[72]=r,e[73]=y,e[74]=R):R=e[74];let M;e[75]!==i||e[76]!==oe||e[77]!==R?(M=s.jsx(Pe,{open:oe,deploymentFrgmt:i,onRequestClose:R}),e[75]=i,e[76]=oe,e[77]=R,e[78]=M):M=e[78];let X;return e[79]!==_||e[80]!==M?(X=s.jsxs(s.Fragment,{children:[_,M]}),e[79]=_,e[80]=M,e[81]=X):X=e[81],X},Ge=()=>{"use memo";const e=ge.c(6),{t:o}=ye();let n;e[0]!==o?(n=o("webui.menu.Deployments"),e[0]=o,e[1]=n):n=e[1];let u;e[2]===Symbol.for("react.memo_cache_sentinel")?(u={body:{paddingTop:0}},e[2]=u):u=e[2];let d;e[3]===Symbol.for("react.memo_cache_sentinel")?(d=s.jsx(Y.Suspense,{fallback:s.jsx(Ke,{active:!0}),children:s.jsx(Be,{})}),e[3]=d):d=e[3];let r;return e[4]!==n?(r=s.jsx(pe,{direction:"column",align:"stretch",gap:"md",children:s.jsx(Se,{variant:"borderless",title:n,styles:u,children:d})}),e[4]=n,e[5]=r):r=e[5],r};function Oe(e){return typeof e=="object"&&e!==null&&!Array.isArray(e)?e:{}}export{Ge as default};
//# sourceMappingURL=DeploymentListPage-XawXFXOe.js.map
