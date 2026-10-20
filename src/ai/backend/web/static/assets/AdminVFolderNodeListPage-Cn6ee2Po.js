import{i as xn,u as jn,dd as Rn,a as Pn,a7 as On,l as Ne,bI as an,bJ as wn,ce as yn,af as qn,ae as Un,aM as Qn,aS as zn,r as Gn,ak as xe,ag as $n,j as t,bA as je,cf as bn,di as Wn,J as pn,c5 as Hn,b0 as Jn,aL as Yn,aT as Ln,bQ as vn,au as Xn,as as hn,bk as Zn,aQ as el,aa as nl,dj as ll,b2 as al,dJ as tl,P as sl,at as rl,aV as ol,eO as il,hU as dl,dh as ul,aj as cl,hV as gl,d as ml,hW as fl,hX as Fl,hY as yl,O as pl,hZ as kl}from"./index-4XAoWQdC.js";const Kn=(function(){var i={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},n={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},L={defaultValue:null,kind:"LocalArgument",name:"limit"},F={defaultValue:null,kind:"LocalArgument",name:"offset"},v={defaultValue:null,kind:"LocalArgument",name:"orderBy"},h=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],f={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},c={alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},Re=[S],y={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},V=[y],Pe={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"}],concreteType:"VFolderConnection",kind:"LinkedField",name:"adminVfoldersV2",plural:!1,selections:V,storageKey:null},_={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"}],concreteType:"VFolderConnection",kind:"LinkedField",name:"adminVfoldersV2",plural:!1,selections:V,storageKey:null},I=[{alias:null,args:null,kind:"ScalarField",name:"expr",storageKey:null}],Me={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:[i,e,n,L,F,v],kind:"Fragment",metadata:null,name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:h,concreteType:"VFolderConnection",kind:"LinkedField",name:"adminVfoldersV2",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:f,action:"THROW"},r,c,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:Re,storageKey:null},{args:null,kind:"FragmentSpread",name:"VFolderNodesV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteForeverVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalV2Fragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},y],storageKey:null},Pe,_],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[F,L,i,v,e,n],kind:"Operation",name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:h,concreteType:"VFolderConnection",kind:"LinkedField",name:"adminVfoldersV2",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[f,r,c,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[S,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastUsed",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"unmanagedPath",storageKey:null},{alias:null,args:null,concreteType:"VFolderUsageInfo",kind:"LinkedField",name:"usage",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"numFiles",storageKey:null},{alias:null,args:null,concreteType:"BinarySizeInfo",kind:"LinkedField",name:"usedBytes",plural:!1,selections:I,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"permissions",storageKey:null},{alias:null,args:null,concreteType:"VFolderQuotaInfo",kind:"LinkedField",name:"quota",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"maxFiles",storageKey:null},{alias:null,args:null,concreteType:"BinarySizeInfo",kind:"LinkedField",name:"maxSize",plural:!1,selections:I,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},f],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:Re,storageKey:null},f],storageKey:null}],storageKey:null},{alias:null,args:[{kind:"Literal",name:"limit",value:100}],concreteType:"EntityLabelConnection",kind:"LinkedField",name:"entityLabels",plural:!1,selections:[{alias:null,args:null,concreteType:"EntityLabelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"EntityLabel",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},f,{alias:null,args:null,kind:"ScalarField",name:"fieldId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:"entityLabels(limit:100)"},{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[Me,p,S,b,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},f,b,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},p],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[S,f],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[Me],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[Me,p,b,S],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},y],storageKey:null},Pe,_]},params:{cacheID:"65739f25b86ab624c0dd5b860b82714e",id:null,metadata:{},name:"AdminVFolderNodeListPageQuery",operationKind:"query",text:`query AdminVFolderNodeListPageQuery(
  $offset: Int
  $limit: Int
  $filter: VFolderFilter
  $orderBy: [VFolderOrderBy!]
  $filterForActiveCount: VFolderFilter
  $filterForDeletedCount: VFolderFilter
) {
  adminVfoldersV2(offset: $offset, limit: $limit, filter: $filter, orderBy: $orderBy) {
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
  active: adminVfoldersV2(filter: $filterForActiveCount) {
    count
  }
  deleted: adminVfoldersV2(filter: $filterForDeletedCount) {
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
`}}})();Kn.hash="92e6f71c20673fc29f11689016aa1dd5";const Tn=["DELETE_PENDING","DELETE_ONGOING","DELETE_ERROR","DELETE_COMPLETE"],Vn={status:{notIn:Tn}},In={status:{in:Tn}},Sl="-created_at",_l=["active","deleted"],Cl=["all","general","data","automount","model"],bl={general:{AND:[{name:{iNotStartsWith:"."}},{usageMode:{equals:"GENERAL"}}]},data:{usageMode:{equals:"DATA"}},automount:{name:{iStartsWith:"."}},model:{usageMode:{equals:"MODEL"}}},Ll=["READY","CLONING","DELETE_PENDING","DELETE_ONGOING","DELETE_COMPLETE","DELETE_ERROR"],Tl=i=>{"use memo";var Sn;const e=xn.c(225),{t:n}=jn(),L=Rn("vfolder"),F=Pn(),[v,h]=On("table_column_overrides.AdminVFolderNodeListPage");let f;e[0]===Symbol.for("react.memo_cache_sentinel")?(f=[],e[0]=f):f=e[0];const[r,c]=Ne.useState(f),[S,Re]=an(!1),{toggle:y}=Re,[V,Pe]=an(!1),{toggle:_}=Pe,[I,Me]=an(!1),{toggle:p}=Me,[b,En]=an(!1),{toggle:K}=En;let Oe;e[1]===Symbol.for("react.memo_cache_sentinel")?(Oe={current:1,pageSize:10},e[1]=Oe):Oe=e[1];const{baiPaginationOption:T,tablePaginationOption:m,setTablePaginationOption:u}=wn(Oe);let we,qe;e[2]===Symbol.for("react.memo_cache_sentinel")?(we={order:yn(kl),filter:qn(vl),statusCategory:yn(_l).withDefault("active"),mode:yn(Cl).withDefault("all")},qe={history:"replace"},e[2]=we,e[3]=qe):(we=e[2],qe=e[3]);const[l,d]=Un(we,qe);let E;e[4]!==l||e[5]!==m?(E={queryParams:l,tablePaginationOption:m},e[4]=l,e[5]=m,e[6]=E):E=e[6];let Ue;e[7]!==l.statusCategory||e[8]!==E?(Ue={[l.statusCategory]:E},e[7]=l.statusCategory,e[8]=E,e[9]=Ue):Ue=e[9];const kn=Ne.useRef(Ue);let Qe,ze;e[10]!==l||e[11]!==m?(Qe=()=>{kn.current[l.statusCategory]={queryParams:l,tablePaginationOption:m}},ze=[l,m],e[10]=l,e[11]=m,e[12]=Qe,e[13]=ze):(Qe=e[12],ze=e[13]),Ne.useEffect(Qe,ze);const Ge=bl[l.mode],[De,o]=Qn(),tn=l.statusCategory==="deleted"?In:Vn;let A;e[14]!==Ge?(A=Ge?[Ge]:[],e[14]=Ge,e[15]=A):A=e[15];let N;e[16]!==l.filter?(N=l.filter?[l.filter]:[],e[16]=l.filter,e[17]=N):N=e[17];let $e;e[18]!==tn||e[19]!==A||e[20]!==N?($e={AND:[tn,...A,...N]},e[18]=tn,e[19]=A,e[20]=N,e[21]=$e):$e=e[21];const sn=$e,An=T.offset,Nn=T.limit,rn=l.order||Sl;let M;e[22]!==rn?(M=zn(rn),e[22]=rn,e[23]=M):M=e[23];let We;e[24]!==T.limit||e[25]!==T.offset||e[26]!==sn||e[27]!==M?(We={offset:An,limit:Nn,filter:sn,orderBy:M,filterForActiveCount:Vn,filterForDeletedCount:In},e[24]=T.limit,e[25]=T.offset,e[26]=sn,e[27]=M,e[28]=We):We=e[28];const on=We,dn=Ne.useDeferredValue(on),Be=Ne.useDeferredValue(De);let He;e[29]===Symbol.for("react.memo_cache_sentinel")?(He=Kn,e[29]=He):He=e[29];const un=Be===Zn?"store-and-network":"network-only";let Je;e[30]!==Be||e[31]!==un?(Je={fetchPolicy:un,fetchKey:Be},e[30]=Be,e[31]=un,e[32]=Je):Je=e[32];const cn=Gn.useLazyLoadQuery(He,dn,Je);let s,C;e[33]!==cn?({adminVfoldersV2:s,...C}=cn,e[33]=cn,e[34]=s,e[35]=C):(s=e[34],C=e[35]);let D;e[36]!==n?(D=n("data.Folders"),e[36]=n,e[37]=D):D=e[37];const Mn=l.statusCategory;let B;e[38]!==d||e[39]!==u?(B=a=>{const g=kn.current[a]||{};d(null),d({...g.queryParams,statusCategory:a},{history:"replace"}),u(g.tablePaginationOption||{current:1}),c([])},e[38]=d,e[39]=u,e[40]=B):B=e[40];let x;if(e[41]!==C||e[42]!==l.statusCategory||e[43]!==n){let a;e[45]!==C||e[46]!==l.statusCategory?(a=(g,k)=>{var Cn;const _n=((Cn=C[k])==null?void 0:Cn.count)??0;return{key:k,label:g,endContent:_n>0?t.jsx(el,{label:_n,variant:l.statusCategory===k?"info":"neutral"}):void 0}},e[45]=C,e[46]=l.statusCategory,e[47]=a):a=e[47],x=xe({active:n("data.Active"),deleted:n("data.folders.TrashBin")},a),e[41]=C,e[42]=l.statusCategory,e[43]=n,e[44]=x}else x=e[44];let j;e[48]!==l.statusCategory||e[49]!==B||e[50]!==x?(j=t.jsx(nl,{activeKey:Mn,onChange:B,items:x}),e[48]=l.statusCategory,e[49]=B,e[50]=x,e[51]=j):j=e[51];let Ye;e[52]===Symbol.for("react.memo_cache_sentinel")?(Ye={flexShrink:1},e[52]=Ye):Ye=e[52];const Dn=l.mode;let R;e[53]!==d||e[54]!==u?(R=a=>{d({mode:a.target.value}),u({current:1}),c([])},e[53]=d,e[54]=u,e[55]=R):R=e[55];let P;e[56]!==F._config.enableModelFolders||e[57]!==F._config.fasttrackEndpoint||e[58]!==n?(P=$n([{label:n("data.All"),value:"all"},{label:n("data.General"),value:"general"},((Sn=F==null?void 0:F._config)==null?void 0:Sn.fasttrackEndpoint)&&{label:n("data.Pipeline"),value:"data"},{label:n("data.AutoMount"),value:"automount"},F._config.enableModelFolders&&{label:n("data.Models"),value:"model"}]),e[56]=F._config.enableModelFolders,e[57]=F._config.fasttrackEndpoint,e[58]=n,e[59]=P):P=e[59];let O;e[60]!==l.mode||e[61]!==R||e[62]!==P?(O=t.jsx(ll,{optionType:"button",value:Dn,onChange:R,options:P}),e[60]=l.mode,e[61]=R,e[62]=P,e[63]=O):O=e[63];let w;e[64]!==n?(w=n("data.folders.Name"),e[64]=n,e[65]=w):w=e[65];let q;e[66]!==w?(q={key:"name",propertyLabel:w,type:"string"},e[66]=w,e[67]=q):q=e[67];let U;e[68]!==n?(U=n("data.folders.Location"),e[68]=n,e[69]=U):U=e[69];let Q;e[70]!==U?(Q={key:"host",propertyLabel:U,type:"string"},e[70]=U,e[71]=Q):Q=e[71];let z;e[72]!==n?(z=n("data.folders.Status"),e[72]=n,e[73]=z):z=e[73];let Xe;e[74]===Symbol.for("react.memo_cache_sentinel")?(Xe=xe([...Ll],hl),e[74]=Xe):Xe=e[74];let G;e[75]!==z?(G={key:"status",propertyLabel:z,type:"enum",strictSelection:!0,options:Xe},e[75]=z,e[76]=G):G=e[76];let $;e[77]!==n?($=n("data.folders.CreatedAt"),e[77]=n,e[78]=$):$=e[78];let W;e[79]!==$?(W={key:"createdAt",propertyLabel:$,type:"datetime"},e[79]=$,e[80]=W):W=e[80];let H;e[81]!==n?(H=n("data.folders.Cloneable"),e[81]=n,e[82]=H):H=e[82];let J;e[83]!==H?(J={key:"cloneable",propertyLabel:H,type:"boolean"},e[83]=H,e[84]=J):J=e[84];let Y;e[85]!==L||e[86]!==n?(Y=L?[{key:"labels.some.key",propertyLabel:n("entityLabel.LabelKey"),type:"string"},{key:"labels.some.value",propertyLabel:n("entityLabel.LabelValue"),type:"string"}]:[],e[85]=L,e[86]=n,e[87]=Y):Y=e[87];let X;e[88]!==q||e[89]!==Q||e[90]!==G||e[91]!==W||e[92]!==J||e[93]!==Y?(X=[q,Q,G,W,J,...Y],e[88]=q,e[89]=Q,e[90]=G,e[91]=W,e[92]=J,e[93]=Y,e[94]=X):X=e[94];const gn=l.filter??void 0;let Z;e[95]!==d||e[96]!==u?(Z=a=>{d({filter:a??null}),u({current:1}),c([])},e[95]=d,e[96]=u,e[97]=Z):Z=e[97];let ee;e[98]!==X||e[99]!==gn||e[100]!==Z?(ee=t.jsx(al,{"data-testid":"vfolder-filter",filterProperties:X,value:gn,onChange:Z}),e[98]=X,e[99]=gn,e[100]=Z,e[101]=ee):ee=e[101];let ne;e[102]!==O||e[103]!==ee?(ne=t.jsxs(je,{gap:3,align:"start",style:Ye,wrap:"wrap",children:[O,ee]}),e[102]=O,e[103]=ee,e[104]=ne):ne=e[104];let le;e[105]!==l.statusCategory||e[106]!==r||e[107]!==n||e[108]!==y||e[109]!==o?(le=r.length>0&&l.statusCategory==="active"&&t.jsxs(je,{gap:1,align:"center",children:[t.jsx(bn,{count:r.length,onClearSelection:()=>c([])}),t.jsx(Wn,{entityType:"vfolder",targets:r.map(Vl),onLabelsChanged:()=>o()}),t.jsx(pn,{label:n("data.folders.MoveToTrash"),tooltip:n("data.folders.MoveToTrash"),icon:t.jsx(Hn,{color:"var(--color-error)"}),variant:"ghost",onClick:()=>{y()}})]}),e[105]=l.statusCategory,e[106]=r,e[107]=n,e[108]=y,e[109]=o,e[110]=le):le=e[110];let ae;e[111]!==l.statusCategory||e[112]!==r.length||e[113]!==n||e[114]!==K||e[115]!==_?(ae=r.length>0&&l.statusCategory==="deleted"&&t.jsxs(je,{gap:1,align:"center",children:[t.jsx(bn,{count:r.length,onClearSelection:()=>c([])}),t.jsx(pn,{label:n("data.folders.Restore"),tooltip:n("data.folders.Restore"),icon:t.jsx(Jn,{}),variant:"ghost",onClick:()=>{_()}}),t.jsx(pn,{label:n("data.folders.Delete"),tooltip:n("data.folders.Delete"),icon:t.jsx(Yn,{color:"var(--color-error)"}),variant:"ghost",onClick:()=>{K()}})]}),e[111]=l.statusCategory,e[112]=r.length,e[113]=n,e[114]=K,e[115]=_,e[116]=ae):ae=e[116];const mn=dn!==on||Be!==De;let te;e[117]!==o?(te=a=>{o(a)},e[117]=o,e[118]=te):te=e[118];let se;e[119]!==De||e[120]!==mn||e[121]!==te?(se=t.jsx(tl,{settingId:"admin-vfolder-list",loading:mn,value:De,onChange:te}),e[119]=De,e[120]=mn,e[121]=te,e[122]=se):se=e[122];let Ze;e[123]===Symbol.for("react.memo_cache_sentinel")?(Ze=t.jsx(sl,{}),e[123]=Ze):Ze=e[123];let re;e[124]!==n?(re=n("data.CreateFolder"),e[124]=n,e[125]=re):re=e[125];let oe;e[126]!==p?(oe=()=>{p()},e[126]=p,e[127]=oe):oe=e[127];let ie;e[128]!==re||e[129]!==oe?(ie=t.jsx(rl,{variant:"primary",icon:Ze,label:re,onClick:oe}),e[128]=re,e[129]=oe,e[130]=ie):ie=e[130];let de;e[131]!==le||e[132]!==ae||e[133]!==se||e[134]!==ie?(de=t.jsxs(je,{gap:2,children:[le,ae,se,ie]}),e[131]=le,e[132]=ae,e[133]=se,e[134]=ie,e[135]=de):de=e[135];let ue;e[136]!==ne||e[137]!==de?(ue=t.jsxs(je,{justify:"between",wrap:"wrap",gap:3,children:[ne,de]}),e[136]=ne,e[137]=de,e[138]=ue):ue=e[138];let en;e[139]===Symbol.for("react.memo_cache_sentinel")?(en=t.jsx(ol,{rows:4}),e[139]=en):en=e[139];const Bn=l.order,fn=dn!==on;let ce;e[140]!==n?(ce=n("data.folders.CannotDeployFromAdminMenu"),e[140]=n,e[141]=ce):ce=e[141];let ge;e[142]!==(s==null?void 0:s.edges)?(ge=Ln(xe(s==null?void 0:s.edges,"node")),e[142]=s==null?void 0:s.edges,e[143]=ge):ge=e[143];let me;if(e[144]!==(s==null?void 0:s.edges)||e[145]!==r){let a;e[147]!==(s==null?void 0:s.edges)?(a=k=>{il(k,Ln(xe(s==null?void 0:s.edges,"node")),c)},e[147]=s==null?void 0:s.edges,e[148]=a):a=e[148];let g;e[149]!==r?(g=xe(r,Il),e[149]=r,e[150]=g):g=e[150],me={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(k){return{disabled:dl(k.vfolderStatus)&&k.vfolderStatus!=="DELETE_PENDING"}},onChange:a,selectedRowKeys:g},e[144]=s==null?void 0:s.edges,e[145]=r,e[146]=me}else me=e[146];const Fn=(s==null?void 0:s.count)??0;let fe;e[151]!==u||e[152]!==Fn||e[153]!==m.current||e[154]!==m.pageSize?(fe={pageSize:m.pageSize,current:m.current,total:Fn,onChange(a,g){vn(a)&&vn(g)&&u({current:a,pageSize:g})}},e[151]=u,e[152]=Fn,e[153]=m.current,e[154]=m.pageSize,e[155]=fe):fe=e[155];let Fe;e[156]!==d?(Fe=a=>{d({order:a??null})},e[156]=d,e[157]=Fe):Fe=e[157];let ye;e[158]!==o?(ye=()=>o(),e[158]=o,e[159]=ye):ye=e[159];let pe;e[160]!==d||e[161]!==u?(pe=a=>{d({filter:ul(a)}),u({current:1}),c([])},e[160]=d,e[161]=u,e[162]=pe):pe=e[162];let ke;e[163]!==o?(ke=a=>{c(g=>cl(g,k=>k.id!==a)),o()},e[163]=o,e[164]=ke):ke=e[164];let nn;e[165]===Symbol.for("react.memo_cache_sentinel")?(nn={cur_size:{hidden:!1},max_size:{hidden:!1},created_at:{hidden:!1}},e[165]=nn):nn=e[165];let Se;e[166]!==v||e[167]!==h?(Se={columnOverrides:v,defaultColumnOverrides:nn,onColumnOverridesChange:h},e[166]=v,e[167]=h,e[168]=Se):Se=e[168];let _e;e[169]!==l.order||e[170]!==fn||e[171]!==ce||e[172]!==ge||e[173]!==me||e[174]!==fe||e[175]!==Fe||e[176]!==ye||e[177]!==pe||e[178]!==ke||e[179]!==Se?(_e=t.jsx(Ne.Suspense,{fallback:en,children:t.jsx(gl,{order:Bn,loading:fn,project:null,noDeployTooltip:ce,vfoldersFrgmt:ge,rowSelection:me,pagination:fe,onChangeOrder:Fe,onLabelsChanged:ye,showLabelsByDefault:!0,onLabelClick:pe,onRemoveRow:ke,tableSettings:Se})}),e[169]=l.order,e[170]=fn,e[171]=ce,e[172]=ge,e[173]=me,e[174]=fe,e[175]=Fe,e[176]=ye,e[177]=pe,e[178]=ke,e[179]=Se,e[180]=_e):_e=e[180];let Ce;e[181]!==ue||e[182]!==_e?(Ce=t.jsxs(hn,{align:"stretch",gap:3,children:[ue,_e]}),e[181]=ue,e[182]=_e,e[183]=Ce):Ce=e[183];let be;e[184]!==D||e[185]!==j||e[186]!==Ce?(be=t.jsxs(ml,{title:D,children:[j,Ce]}),e[184]=D,e[185]=j,e[186]=Ce,e[187]=be):be=e[187];let Le;e[188]!==y||e[189]!==o?(Le=a=>{a&&(o(),c([])),y()},e[188]=y,e[189]=o,e[190]=Le):Le=e[190];let ve;e[191]!==S||e[192]!==r||e[193]!==Le?(ve=t.jsx(fl,{vfolderFrgmts:r,open:S,onRequestClose:Le}),e[191]=S,e[192]=r,e[193]=Le,e[194]=ve):ve=e[194];let he;e[195]!==_||e[196]!==o?(he=a=>{a&&(o(),c([])),_()},e[195]=_,e[196]=o,e[197]=he):he=e[197];let Ve;e[198]!==V||e[199]!==r||e[200]!==he?(Ve=t.jsx(Fl,{vfolderFrgmts:r,open:V,onRequestClose:he}),e[198]=V,e[199]=r,e[200]=he,e[201]=Ve):Ve=e[201];let Ie;e[202]!==K||e[203]!==o?(Ie=a=>{a&&(o(),c([])),K()},e[202]=K,e[203]=o,e[204]=Ie):Ie=e[204];let Ke;e[205]!==b||e[206]!==r||e[207]!==Ie?(Ke=t.jsx(yl,{vfolderFrgmts:r,open:b,onRequestClose:Ie}),e[205]=b,e[206]=r,e[207]=Ie,e[208]=Ke):Ke=e[208];let Te;e[209]!==n?(Te=n("data.folders.AdminDataPageAlert"),e[209]=n,e[210]=Te):Te=e[210];let Ee;e[211]!==p||e[212]!==o?(Ee=a=>{p(),a&&o()},e[211]=p,e[212]=o,e[213]=Ee):Ee=e[213];let Ae;e[214]!==I||e[215]!==Te||e[216]!==Ee?(Ae=t.jsx(pl,{open:I,project:null,folderType:"project",alertMessage:Te,onRequestClose:Ee}),e[214]=I,e[215]=Te,e[216]=Ee,e[217]=Ae):Ae=e[217];let ln;return e[218]!==i||e[219]!==be||e[220]!==ve||e[221]!==Ve||e[222]!==Ke||e[223]!==Ae?(ln=t.jsx(Xn,{children:t.jsxs(hn,{align:"stretch",gap:5,...i,children:[be,ve,Ve,Ke,Ae]})}),e[218]=i,e[219]=be,e[220]=ve,e[221]=Ve,e[222]=Ke,e[223]=Ae,e[224]=ln):ln=e[224],ln};function vl(i){return i}function hl(i){return{label:i,value:i}}function Vl(i){var e;return{entityId:i.entityId,name:((e=i.metadata)==null?void 0:e.name)??void 0}}function Il(i){return i.id}export{Tl as default};
//# sourceMappingURL=AdminVFolderNodeListPage-Cn6ee2Po.js.map
