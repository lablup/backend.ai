import{i as In,u as Ln,z as Mn,V as Dn,j as a,aV as Fn,cu as Bn,l as h,d as xn,dd as Pn,a as Rn,a7 as wn,bI as Xe,bJ as On,ce as gn,af as qn,ae as $n,aM as Un,aS as Qn,r as zn,aQ as Gn,ag as Wn,bA as je,cf as _n,di as Hn,J as mn,c5 as Jn,b0 as Yn,aL as Xn,aT as Cn,ak as fn,bQ as bn,bk as Zn,hZ as el,aa as nl,dj as ll,b2 as al,dJ as tl,P as sl,at as rl,eO as ol,hU as il,dh as dl,aj as ul,hV as cl,as as gl,hW as ml,hX as fl,hY as Fl,O as yl}from"./index-4XAoWQdC.js";const hn=(function(){var t={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},u={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},n={defaultValue:null,kind:"LocalArgument",name:"limit"},k={defaultValue:null,kind:"LocalArgument",name:"offset"},d={defaultValue:null,kind:"LocalArgument",name:"orderBy"},S={defaultValue:null,kind:"LocalArgument",name:"projectId"},f={kind:"Variable",name:"projectId",variableName:"projectId"},p=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},f],r={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},K={alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},C=[v],I={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},Me=[I],b={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"},f],concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:Me,storageKey:null},T={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"},f],concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:Me,storageKey:null},De=[{alias:null,args:null,kind:"ScalarField",name:"expr",storageKey:null}],_={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},Ee={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:[t,e,u,n,k,d,S],kind:"Fragment",metadata:null,name:"ProjectAdminDataPageQuery",selections:[{alias:null,args:p,concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:r,action:"THROW"},F,K,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:C,storageKey:null},{args:null,kind:"FragmentSpread",name:"VFolderNodesV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteForeverVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalV2Fragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},I],storageKey:null},b,T],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[S,k,n,t,d,e,u],kind:"Operation",name:"ProjectAdminDataPageQuery",selections:[{alias:null,args:p,concreteType:"VFolderConnection",kind:"LinkedField",name:"projectVfolders",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[r,F,K,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[v,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastUsed",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"unmanagedPath",storageKey:null},{alias:null,args:null,concreteType:"VFolderUsageInfo",kind:"LinkedField",name:"usage",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"numFiles",storageKey:null},{alias:null,args:null,concreteType:"BinarySizeInfo",kind:"LinkedField",name:"usedBytes",plural:!1,selections:De,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"permissions",storageKey:null},{alias:null,args:null,concreteType:"VFolderQuotaInfo",kind:"LinkedField",name:"quota",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"maxFiles",storageKey:null},{alias:null,args:null,concreteType:"BinarySizeInfo",kind:"LinkedField",name:"maxSize",plural:!1,selections:De,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},r],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:C,storageKey:null},r],storageKey:null}],storageKey:null},{alias:null,args:[{kind:"Literal",name:"limit",value:100}],concreteType:"EntityLabelConnection",kind:"LinkedField",name:"entityLabels",plural:!1,selections:[{alias:null,args:null,concreteType:"EntityLabelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"EntityLabel",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},r,{alias:null,args:null,kind:"ScalarField",name:"fieldId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:"entityLabels(limit:100)"},{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[_,L,v,Ee,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},r,Ee,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},L],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[v,r],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[_],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[_,L,Ee,v],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},I],storageKey:null},b,T]},params:{cacheID:"8b64165f36594cf9f81df30772297a7a",id:null,metadata:{},name:"ProjectAdminDataPageQuery",operationKind:"query",text:`query ProjectAdminDataPageQuery(
  $projectId: UUID!
  $offset: Int
  $limit: Int
  $filter: VFolderFilter
  $orderBy: [VFolderOrderBy!]
  $filterForActiveCount: VFolderFilter
  $filterForDeletedCount: VFolderFilter
) {
  projectVfolders(projectId: $projectId, offset: $offset, limit: $limit, filter: $filter, orderBy: $orderBy) {
    edges {
      node {
        id
        entityId
        vfolderStatus: status
        metadata {
          name
        }
        ...VFolderNodesV2Fragment
        ...DeleteVFolderModalV2Fragment
        ...DeleteForeverVFolderModalV2Fragment
        ...RestoreVFolderModalV2Fragment
      }
    }
    count
  }
  active: projectVfolders(projectId: $projectId, filter: $filterForActiveCount) {
    count
  }
  deleted: projectVfolders(projectId: $projectId, filter: $filterForDeletedCount) {
    count
  }
}

fragment AppLaunchConfirmationModalFragment on ComputeSessionNode {
  id
  row_id
  name
  ...useBackendAIAppLauncherFragment
}

fragment AppLauncherModalFragment on ComputeSessionNode {
  id
  row_id
  name
  service_ports
  access_key
  ...useBackendAIAppLauncherFragment
  ...SFTPConnectionInfoModalFragment
  ...TensorboardPathModalFragment
  ...AppLaunchConfirmationModalFragment
}

fragment BAIComputeSessionNodeNotificationItemFragment on ComputeSessionNode {
  id
  name
  status
  status_info
  status_data
  ...SessionActionButtonsFragment
  ...SessionStatusBadgeFragment
}

fragment BAIEntityLabelSettingModalFragment on EntityLabelConnection {
  edges {
    node {
      fieldId
      key
      value
      id
    }
  }
}

fragment BAIEntityLabelTokensFragment on EntityLabelConnection {
  edges {
    node {
      key
      value
      id
    }
  }
}

fragment BAINodeNotificationItemFragment on Node {
  __isNode: __typename
  ... on ComputeSessionNode {
    __typename
    status
    name
    row_id
    ...BAIComputeSessionNodeNotificationItemFragment
  }
  ... on VFolder {
    __typename
    ...BAIVirtualFolderNodeNotificationItemV2Fragment
  }
  ... on VirtualFolderNode {
    __typename
    status
    ...BAIVirtualFolderNodeNotificationItemFragment
  }
  id
}

fragment BAIVirtualFolderNodeNotificationItemFragment on VirtualFolderNode {
  row_id
  id
  name
  status
}

fragment BAIVirtualFolderNodeNotificationItemV2Fragment on VFolder {
  id
  metadata {
    name
  }
}

fragment ContainerCommitModalFragment on ComputeSessionNode {
  id
  name
  row_id
}

fragment ContainerLogModalFragment on ComputeSessionNode {
  id
  row_id
  name
  status
  access_key
  kernel_nodes {
    edges {
      node {
        id
        row_id
        container_id
        cluster_idx
        cluster_role
        cluster_hostname
      }
    }
  }
}

fragment DeleteForeverVFolderModalV2Fragment on VFolder {
  id
  metadata {
    name
  }
}

fragment DeleteVFolderModalV2Fragment on VFolder {
  id
  metadata {
    name
  }
  permissions @since(version: "26.9.0rc1")
}

fragment RestoreVFolderModalV2Fragment on VFolder {
  id
  metadata {
    name
  }
}

fragment SFTPConnectionInfoModalFragment on ComputeSessionNode {
  row_id
  vfolder_nodes {
    edges {
      node {
        name
        id
      }
    }
  }
}

fragment SessionActionButtonsFragment on ComputeSessionNode {
  id
  name
  row_id
  type
  status
  access_key
  service_ports
  commit_status
  user_id
  ...TerminateSessionModalFragment
  ...ContainerLogModalFragment
  ...ContainerCommitModalFragment
  ...AppLauncherModalFragment
  ...SFTPConnectionInfoModalFragment
  ...useBackendAIAppLauncherFragment
}

fragment SessionStatusBadgeFragment on ComputeSessionNode {
  id
  status
  status_info
  queue_position
  cluster_size
  kernel_nodes {
    edges {
      node {
        id
        status
      }
    }
  }
}

fragment SharedFolderPermissionInfoModalV2Fragment on VFolder {
  id
  metadata {
    name
  }
  accessControl {
    ownershipType
  }
  ownership {
    creatorEmail
    user {
      basicInfo {
        email
      }
      id
    }
  }
  ...VFolderPermissionCellV2Fragment
}

fragment TensorboardPathModalFragment on ComputeSessionNode {
  id
  row_id
  name
  ...useBackendAIAppLauncherFragment
}

fragment TerminateSessionModalFragment on ComputeSessionNode {
  id
  row_id
  name
  scaling_group
  access_key
  project_id
  kernel_nodes {
    edges {
      node {
        container_id
        agent_id
        id
      }
    }
  }
}

fragment VFolderNodeIdenticonV2Fragment on VFolder {
  id
}

fragment VFolderNodesV2Fragment on VFolder {
  id
  entityId
  vfolderStatus: status
  host
  unmanagedPath
  usage {
    numFiles
    usedBytes {
      expr @since(version: "26.8.0")
    }
  }
  metadata {
    name
    usageMode
    quotaScopeId
    createdAt
    lastUsed
    cloneable
  }
  accessControl {
    permission
    ownershipType
  }
  permissions @since(version: "26.9.0rc1")
  quota {
    maxFiles
    maxSize {
      expr @since(version: "26.8.0")
    }
  }
  ownership {
    userId
    projectId
    creatorEmail
    user {
      basicInfo {
        email
      }
      id
    }
    project {
      basicInfo {
        name
      }
      id
    }
  }
  entityLabels(limit: 100) {
    ...BAIEntityLabelTokensFragment
    ...BAIEntityLabelSettingModalFragment
  }
  ...VFolderPermissionCellV2Fragment
  ...VFolderNodeIdenticonV2Fragment
  ...SharedFolderPermissionInfoModalV2Fragment
  ...DeleteForeverVFolderModalV2Fragment
  ...BAINodeNotificationItemFragment
}

fragment VFolderPermissionCellV2Fragment on VFolder {
  accessControl {
    permission
  }
}

fragment useBackendAIAppLauncherFragment on ComputeSessionNode {
  name
  row_id
  vfolder_mounts
  scaling_group
  project_id
  service_ports
}
`}}})();hn.hash="8c5a755caaf30e84151bc5c88ac4a136";const pl=["DELETE_PENDING","DELETE_ONGOING","DELETE_ERROR","DELETE_COMPLETE"],kl=["DELETE_PENDING","DELETE_ONGOING","DELETE_ERROR"],Vn={status:{notIn:pl}},vn={status:{in:kl}},Sl="-created_at",_l=["active","deleted"],Cl=["all","general","data","automount","model"],bl={general:{AND:[{name:{iNotStartsWith:"."}},{usageMode:{equals:"GENERAL"}}]},data:{usageMode:{equals:"DATA"}},automount:{name:{iStartsWith:"."}},model:{usageMode:{equals:"MODEL"}}},Vl=t=>{"use memo";var pn;const e=In.c(210),{project:u}=t,{t:n}=Ln(),k=Pn("vfolder"),d=Rn(),[S,f]=wn("table_column_overrides.ProjectAdminDataPage");let p;e[0]===Symbol.for("react.memo_cache_sentinel")?(p=[],e[0]=p):p=e[0];const[r,F]=h.useState(p),[K,v]=Xe(!1),{toggle:C}=v,[I,Me]=Xe(!1),{toggle:b}=Me,[T,De]=Xe(!1),{toggle:_}=De,[L,Ee]=Xe(!1),{toggle:E}=Ee;let Be;e[1]===Symbol.for("react.memo_cache_sentinel")?(Be={current:1,pageSize:10},e[1]=Be):Be=e[1];const{baiPaginationOption:A,tablePaginationOption:y,setTablePaginationOption:m}=On(Be);let xe,Pe;e[2]===Symbol.for("react.memo_cache_sentinel")?(xe={order:gn(el),filter:qn(vl),statusCategory:gn(_l).withDefault("active"),mode:gn(Cl).withDefault("all")},Pe={history:"replace"},e[2]=xe,e[3]=Pe):(xe=e[2],Pe=e[3]);const[l,c]=$n(xe,Pe);let N;e[4]!==l||e[5]!==y?(N={queryParams:l,tablePaginationOption:y},e[4]=l,e[5]=y,e[6]=N):N=e[6];let Re;e[7]!==l.statusCategory||e[8]!==N?(Re={[l.statusCategory]:N},e[7]=l.statusCategory,e[8]=N,e[9]=Re):Re=e[9];const yn=h.useRef(Re);let we,Oe;e[10]!==l||e[11]!==y?(we=()=>{yn.current[l.statusCategory]={queryParams:l,tablePaginationOption:y}},Oe=[l,y],e[10]=l,e[11]=y,e[12]=we,e[13]=Oe):(we=e[12],Oe=e[13]),h.useEffect(we,Oe);const qe=bl[l.mode],[Ae,i]=Un(),Ze=l.statusCategory==="deleted"?vn:Vn;let j;e[14]!==qe?(j=qe?[qe]:[],e[14]=qe,e[15]=j):j=e[15];let M;e[16]!==l.filter?(M=l.filter?[l.filter]:[],e[16]=l.filter,e[17]=M):M=e[17];let $e;e[18]!==Ze||e[19]!==j||e[20]!==M?($e={AND:[Ze,...j,...M]},e[18]=Ze,e[19]=j,e[20]=M,e[21]=$e):$e=e[21];const en=$e,Kn=u.id,Tn=A.offset,En=A.first,nn=l.order||Sl;let D;e[22]!==nn?(D=Qn(nn),e[22]=nn,e[23]=D):D=e[23];let Ue;e[24]!==A.first||e[25]!==A.offset||e[26]!==en||e[27]!==u.id||e[28]!==D?(Ue={projectId:Kn,offset:Tn,limit:En,filter:en,orderBy:D,filterForActiveCount:Vn,filterForDeletedCount:vn},e[24]=A.first,e[25]=A.offset,e[26]=en,e[27]=u.id,e[28]=D,e[29]=Ue):Ue=e[29];const ln=Ue,an=h.useDeferredValue(ln),Ne=h.useDeferredValue(Ae);let Qe;e[30]===Symbol.for("react.memo_cache_sentinel")?(Qe=hn,e[30]=Qe):Qe=e[30];const tn=Ne===Zn?"store-and-network":"network-only";let ze;e[31]!==Ne||e[32]!==tn?(ze={fetchPolicy:tn,fetchKey:Ne},e[31]=Ne,e[32]=tn,e[33]=ze):ze=e[33];const sn=zn.useLazyLoadQuery(Qe,an,ze);let B,o;e[34]!==sn?({projectVfolders:o,...B}=sn,e[34]=sn,e[35]=B,e[36]=o):(B=e[35],o=e[36]);const An=l.statusCategory;let x;e[37]!==c||e[38]!==m?(x=s=>{const g=yn.current[s]||{};c(null),c({...g.queryParams,statusCategory:s},{history:"replace"}),m(g.tablePaginationOption||{current:1,pageSize:10}),F([])},e[37]=c,e[38]=m,e[39]=x):x=e[39];let P;e[40]!==n?(P=n("data.Active"),e[40]=n,e[41]=P):P=e[41];let R;e[42]!==P?(R=["active",P],e[42]=P,e[43]=R):R=e[43];let w;e[44]!==n?(w=n("data.folders.TrashBin"),e[44]=n,e[45]=w):w=e[45];let O;e[46]!==w?(O=["deleted",w],e[46]=w,e[47]=O):O=e[47];let Ge;e[48]!==R||e[49]!==O?(Ge=[R,O],e[48]=R,e[49]=O,e[50]=Ge):Ge=e[50];const rn=Ge;let q;e[51]!==B||e[52]!==l.statusCategory||e[53]!==rn?(q=rn.map(s=>{var Sn;const[g,V]=s,kn=((Sn=B[g])==null?void 0:Sn.count)??0;return{key:g,label:V,endContent:kn>0?a.jsx(Gn,{label:kn,variant:l.statusCategory===g?"info":"neutral"}):void 0}}),e[51]=B,e[52]=l.statusCategory,e[53]=rn,e[54]=q):q=e[54];let $;e[55]!==l.statusCategory||e[56]!==x||e[57]!==q?($=a.jsx(nl,{activeKey:An,onChange:x,items:q}),e[55]=l.statusCategory,e[56]=x,e[57]=q,e[58]=$):$=e[58];let We;e[59]===Symbol.for("react.memo_cache_sentinel")?(We={flexShrink:1},e[59]=We):We=e[59];const Nn=l.mode;let U;e[60]!==c||e[61]!==m?(U=s=>{c({mode:s.target.value}),m({current:1}),F([])},e[60]=c,e[61]=m,e[62]=U):U=e[62];let Q;e[63]!==d._config.enableModelFolders||e[64]!==d._config.fasttrackEndpoint||e[65]!==n?(Q=Wn([{label:n("data.All"),value:"all"},{label:n("data.General"),value:"general"},((pn=d==null?void 0:d._config)==null?void 0:pn.fasttrackEndpoint)&&{label:n("data.Pipeline"),value:"data"},{label:n("data.AutoMount"),value:"automount"},d._config.enableModelFolders&&{label:n("data.Models"),value:"model"}]),e[63]=d._config.enableModelFolders,e[64]=d._config.fasttrackEndpoint,e[65]=n,e[66]=Q):Q=e[66];let z;e[67]!==l.mode||e[68]!==U||e[69]!==Q?(z=a.jsx(ll,{optionType:"button",value:Nn,onChange:U,options:Q}),e[67]=l.mode,e[68]=U,e[69]=Q,e[70]=z):z=e[70];let G;e[71]!==n?(G=n("data.folders.Name"),e[71]=n,e[72]=G):G=e[72];let W;e[73]!==G?(W={key:"name",propertyLabel:G,type:"string"},e[73]=G,e[74]=W):W=e[74];let H;e[75]!==n?(H=n("data.folders.Location"),e[75]=n,e[76]=H):H=e[76];let J;e[77]!==H?(J={key:"host",propertyLabel:H,type:"string"},e[77]=H,e[78]=J):J=e[78];let Y;e[79]!==k||e[80]!==n?(Y=k?[{key:"labels.some.key",propertyLabel:n("entityLabel.LabelKey"),type:"string"},{key:"labels.some.value",propertyLabel:n("entityLabel.LabelValue"),type:"string"}]:[],e[79]=k,e[80]=n,e[81]=Y):Y=e[81];let X;e[82]!==W||e[83]!==J||e[84]!==Y?(X=[W,J,...Y],e[82]=W,e[83]=J,e[84]=Y,e[85]=X):X=e[85];const on=l.filter??void 0;let Z;e[86]!==c||e[87]!==m?(Z=s=>{c({filter:s??null}),m({current:1}),F([])},e[86]=c,e[87]=m,e[88]=Z):Z=e[88];let ee;e[89]!==X||e[90]!==on||e[91]!==Z?(ee=a.jsx(al,{"data-testid":"vfolder-filter",filterProperties:X,value:on,onChange:Z}),e[89]=X,e[90]=on,e[91]=Z,e[92]=ee):ee=e[92];let ne;e[93]!==z||e[94]!==ee?(ne=a.jsxs(je,{gap:3,align:"start",style:We,wrap:"wrap",children:[z,ee]}),e[93]=z,e[94]=ee,e[95]=ne):ne=e[95];let le;e[96]!==l.statusCategory||e[97]!==r||e[98]!==n||e[99]!==C||e[100]!==i?(le=r.length>0&&l.statusCategory==="active"&&a.jsxs(je,{gap:1,align:"center",children:[a.jsx(_n,{count:r.length,onClearSelection:()=>F([])}),a.jsx(Hn,{entityType:"vfolder",targets:r.map(Il),onLabelsChanged:()=>i()}),a.jsx(mn,{label:n("data.folders.MoveToTrash"),tooltip:n("data.folders.MoveToTrash"),icon:a.jsx(Jn,{color:"var(--color-error)"}),variant:"ghost",onClick:()=>{C()}})]}),e[96]=l.statusCategory,e[97]=r,e[98]=n,e[99]=C,e[100]=i,e[101]=le):le=e[101];let ae;e[102]!==l.statusCategory||e[103]!==r.length||e[104]!==n||e[105]!==E||e[106]!==b?(ae=r.length>0&&l.statusCategory==="deleted"&&a.jsxs(je,{gap:1,align:"center",children:[a.jsx(_n,{count:r.length,onClearSelection:()=>F([])}),a.jsx(mn,{label:n("data.folders.Restore"),tooltip:n("data.folders.Restore"),icon:a.jsx(Yn,{}),variant:"ghost",onClick:()=>{b()}}),a.jsx(mn,{label:n("data.folders.Delete"),tooltip:n("data.folders.Delete"),icon:a.jsx(Xn,{color:"var(--color-error)"}),variant:"ghost",onClick:()=>{E()}})]}),e[102]=l.statusCategory,e[103]=r.length,e[104]=n,e[105]=E,e[106]=b,e[107]=ae):ae=e[107];const dn=an!==ln||Ne!==Ae;let te;e[108]!==i?(te=s=>{i(s)},e[108]=i,e[109]=te):te=e[109];let se;e[110]!==Ae||e[111]!==dn||e[112]!==te?(se=a.jsx(tl,{settingId:"project-admin-data",loading:dn,value:Ae,onChange:te}),e[110]=Ae,e[111]=dn,e[112]=te,e[113]=se):se=e[113];let He;e[114]===Symbol.for("react.memo_cache_sentinel")?(He=a.jsx(sl,{}),e[114]=He):He=e[114];let re;e[115]!==n?(re=n("data.CreateFolder"),e[115]=n,e[116]=re):re=e[116];let oe;e[117]!==_?(oe=()=>{_()},e[117]=_,e[118]=oe):oe=e[118];let ie;e[119]!==re||e[120]!==oe?(ie=a.jsx(rl,{variant:"primary",icon:He,label:re,onClick:oe}),e[119]=re,e[120]=oe,e[121]=ie):ie=e[121];let de;e[122]!==le||e[123]!==ae||e[124]!==se||e[125]!==ie?(de=a.jsxs(je,{gap:2,children:[le,ae,se,ie]}),e[122]=le,e[123]=ae,e[124]=se,e[125]=ie,e[126]=de):de=e[126];let ue;e[127]!==ne||e[128]!==de?(ue=a.jsxs(je,{justify:"between",wrap:"wrap",gap:3,children:[ne,de]}),e[127]=ne,e[128]=de,e[129]=ue):ue=e[129];let Je;e[130]===Symbol.for("react.memo_cache_sentinel")?(Je=a.jsx(Fn,{rows:4}),e[130]=Je):Je=e[130];const jn=l.order,un=an!==ln;let ce;e[131]!==(o==null?void 0:o.edges)?(ce=Cn(fn(o==null?void 0:o.edges,"node")),e[131]=o==null?void 0:o.edges,e[132]=ce):ce=e[132];let ge;if(e[133]!==(o==null?void 0:o.edges)||e[134]!==r){let s;e[136]!==(o==null?void 0:o.edges)?(s=V=>{ol(V,Cn(fn(o==null?void 0:o.edges,"node")),F)},e[136]=o==null?void 0:o.edges,e[137]=s):s=e[137];let g;e[138]!==r?(g=fn(r,Ll),e[138]=r,e[139]=g):g=e[139],ge={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(V){return{disabled:il(V.vfolderStatus)&&V.vfolderStatus!=="DELETE_PENDING"}},onChange:s,selectedRowKeys:g},e[133]=o==null?void 0:o.edges,e[134]=r,e[135]=ge}else ge=e[135];const cn=(o==null?void 0:o.count)??0;let me;e[140]!==m||e[141]!==cn||e[142]!==y.current||e[143]!==y.pageSize?(me={pageSize:y.pageSize,current:y.current,total:cn,onChange(s,g){bn(s)&&bn(g)&&m({current:s,pageSize:g})}},e[140]=m,e[141]=cn,e[142]=y.current,e[143]=y.pageSize,e[144]=me):me=e[144];let fe;e[145]!==c?(fe=s=>{c({order:s??null})},e[145]=c,e[146]=fe):fe=e[146];let Fe;e[147]!==i?(Fe=()=>i(),e[147]=i,e[148]=Fe):Fe=e[148];let ye;e[149]!==c||e[150]!==m?(ye=s=>{c({filter:dl(s)}),m({current:1}),F([])},e[149]=c,e[150]=m,e[151]=ye):ye=e[151];let pe;e[152]!==i?(pe=s=>{F(g=>ul(g,V=>V.id!==s)),i()},e[152]=i,e[153]=pe):pe=e[153];let ke;e[154]!==S||e[155]!==f?(ke={columnOverrides:S,onColumnOverridesChange:f},e[154]=S,e[155]=f,e[156]=ke):ke=e[156];let Se;e[157]!==u||e[158]!==l.order||e[159]!==un||e[160]!==ce||e[161]!==ge||e[162]!==me||e[163]!==fe||e[164]!==Fe||e[165]!==ye||e[166]!==pe||e[167]!==ke?(Se=a.jsx(h.Suspense,{fallback:Je,children:a.jsx(cl,{order:jn,loading:un,project:u,vfoldersFrgmt:ce,rowSelection:ge,pagination:me,onChangeOrder:fe,onLabelsChanged:Fe,showLabelsByDefault:!0,onLabelClick:ye,onRemoveRow:pe,tableSettings:ke})}),e[157]=u,e[158]=l.order,e[159]=un,e[160]=ce,e[161]=ge,e[162]=me,e[163]=fe,e[164]=Fe,e[165]=ye,e[166]=pe,e[167]=ke,e[168]=Se):Se=e[168];let _e;e[169]!==ue||e[170]!==Se?(_e=a.jsxs(gl,{align:"stretch",gap:3,children:[ue,Se]}),e[169]=ue,e[170]=Se,e[171]=_e):_e=e[171];let Ce;e[172]!==C||e[173]!==i?(Ce=s=>{s&&(i(),F([])),C()},e[172]=C,e[173]=i,e[174]=Ce):Ce=e[174];let be;e[175]!==K||e[176]!==r||e[177]!==Ce?(be=a.jsx(ml,{vfolderFrgmts:r,open:K,onRequestClose:Ce}),e[175]=K,e[176]=r,e[177]=Ce,e[178]=be):be=e[178];let Ve;e[179]!==b||e[180]!==i?(Ve=s=>{s&&(i(),F([])),b()},e[179]=b,e[180]=i,e[181]=Ve):Ve=e[181];let ve;e[182]!==I||e[183]!==r||e[184]!==Ve?(ve=a.jsx(fl,{vfolderFrgmts:r,open:I,onRequestClose:Ve}),e[182]=I,e[183]=r,e[184]=Ve,e[185]=ve):ve=e[185];let Ie;e[186]!==E||e[187]!==i?(Ie=s=>{s&&(i(),F([])),E()},e[186]=E,e[187]=i,e[188]=Ie):Ie=e[188];let Le;e[189]!==L||e[190]!==r||e[191]!==Ie?(Le=a.jsx(Fl,{vfolderFrgmts:r,open:L,onRequestClose:Ie}),e[189]=L,e[190]=r,e[191]=Ie,e[192]=Le):Le=e[192];let he;e[193]!==n?(he=n("data.folders.ProjectAdminDataPageAlert"),e[193]=n,e[194]=he):he=e[194];let Ke;e[195]!==_||e[196]!==i?(Ke=s=>{_(),s&&i()},e[195]=_,e[196]=i,e[197]=Ke):Ke=e[197];let Te;e[198]!==T||e[199]!==u||e[200]!==he||e[201]!==Ke?(Te=a.jsx(yl,{open:T,project:u,folderType:"project",alertMessage:he,onRequestClose:Ke}),e[198]=T,e[199]=u,e[200]=he,e[201]=Ke,e[202]=Te):Te=e[202];let Ye;return e[203]!==$||e[204]!==_e||e[205]!==be||e[206]!==ve||e[207]!==Le||e[208]!==Te?(Ye=a.jsxs(a.Fragment,{children:[$,_e,be,ve,Le,Te]}),e[203]=$,e[204]=_e,e[205]=be,e[206]=ve,e[207]=Le,e[208]=Te,e[209]=Ye):Ye=e[209],Ye},Kl=()=>{"use memo";const t=In.c(10),{t:e}=Ln(),u=Mn();let n;t[0]!==u?(n=Dn(u),t[0]=u,t[1]=n):n=t[1];const k=n;let d;t[2]!==e?(d=e("data.ProjectFolders"),t[2]=e,t[3]=d):d=t[3];let S;t[4]===Symbol.for("react.memo_cache_sentinel")?(S=a.jsx(Fn,{rows:4}),t[4]=S):S=t[4];let f;t[5]!==k?(f=a.jsx(Bn,{children:a.jsx(h.Suspense,{fallback:S,children:k?a.jsx(Vl,{project:k}):a.jsx(Fn,{rows:4})})}),t[5]=k,t[6]=f):f=t[6];let p;return t[7]!==d||t[8]!==f?(p=a.jsx(xn,{title:d,children:f}),t[7]=d,t[8]=f,t[9]=p):p=t[9],p};function vl(t){return t}function Il(t){var e;return{entityId:t.entityId,name:((e=t.metadata)==null?void 0:e.name)??void 0}}function Ll(t){return t.id}export{Kl as default};
//# sourceMappingURL=ProjectAdminDataPage-CXyw47FR.js.map
