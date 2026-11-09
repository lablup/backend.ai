import{c as xn,u as jn,a as Rn,e as Pn,g as On,h as an,i as yn,j as wn,k as qn,l as Un,m as zn,r as $n,o as Gn,n as t,H as xe,I as Fn,q as Ln,F as Qn,V as vn,s as Hn,B as Wn,aU as Yn,w as Jn,v as Xn,x as Zn,y as el,z as nl}from"./index-CwWAznqi.js";import{r as Ne,T as ll,R as al,a as tl,P as rl}from"./icons-BgdBQS0N.js";import{A as ol}from"./AutoUpdateFetchKeyButton-MZ4HY-Ai.js";import{B as sl}from"./BAITabs-C13WiJ9B.js";import{i as il,V as dl,D as ul,a as ml}from"./VFolderNodesV2-B6vONTw8.js";import{D as cl,R as gl}from"./RestoreVFolderModalV2-DBHCawrl.js";import{F as fl}from"./FolderCreateModalV2-C_WEsabC.js";import{u as pl}from"./reactPaginationQueryOptions-Bt4rkB5i.js";import"./useVFolderInvitations-DE3QPtQJ.js";import{m as je,i as bn,f as yl}from"./lodash-RhKGq0BF.js";import{B as hn}from"./BAISelectionLabel-DSve7JI4.js";import{B as Fl}from"./BAIEntityLabelBulkEditButton-DDExm9cf.js";import{B as kl}from"./BAIGraphQLPropertyFilter-BwM0Jjll.js";import{t as Sl}from"./BAIEntityLabelTokens-BWz7hwXT.js";import"./BAIFetchKeyButton-DApd5OLT.js";import"./useControllableValue-BmgV_ECW.js";import"./ButtonGroup-DPQvGHtt.js";import"./BAIDeleteConfirmModal-CUutQ4aO.js";import"./Token-B6wppFPd.js";import"./BAIBulkErrorModal-B1rud_RV.js";import"./BAITable-BJsxYyy0.js";import"./Table-SIAPvWUk.js";import"./characters-DWaYg7k3.js";import"./MenuBottomSheetActionList-DfgiyqqP.js";import"./useScrollableArea-Bsuw_xFk.js";import"./Pagination-cBiGXF8Y.js";import"./NumberInput-BAShrYzU.js";import"./useLocale-tF6sKPhr.js";import"./BAIQuestionIconWithTooltip-BVwNHmCw.js";import"./astryxPlacement-BxR6_qos.js";import"./BAIPopconfirm-CMiztY0m.js";import"./QuotaPerStorageVolumePanelCard-BltXhuPq.js";import"./StorageSelect-DHmmTxOm.js";import"./BAIBadge-9d3LJqR4.js";import"./BAITextHighlighter-9-PRKuKt.js";import"./Grid-BAKellpz.js";import"./GridSpan-CXov5J6d.js";import"./BAIMetadataList-BYZUwKjA.js";import"./DeploymentPresetDetailModal-ChOjaL2h.js";import"./usePaginatedQuery-D34XeqI8.js";import"./BAIComplexSelect-D8NzXrV7.js";import"./ResourceNumbersOfSession-BGRYlXto.js";import"./unifiedAcceleratorSlot-DvOww2Yq.js";import"./BAIResourceNumberWithIcon-jmo0jZh2.js";import"./useBAIIconPath-kZbqwXZ-.js";import"./BAIProjectResourceGroupSelect-CKRGsOXh.js";import"./VFolderNodeIdenticonV2-CDYH4mMW.js";import"./BAIVFolderIdenticon-PgyEX4dv.js";import"./BAIEntityLabelCell-DciPKo0X.js";import"./BAINameActionCell-BZc0os_M.js";import"./BAIEntityLabelSettingModal-zXhyYD10.js";import"./BAIAlertIconWithTooltip-DQhwoX4P.js";import"./astryxTagVariant-CibgwVXb.js";import"./BAIListAlert-C94F7Q9C.js";import"./ProjectSelectForAdminPage-CZSHPq9X.js";import"./index-D3rBwsRJ.js";import"./Switch-D0ZtHaH2.js";import"./BAIPowerSearchAdapters-Cpa0dtdE.js";import"./Tokenizer-Czn8bbzO.js";import"./groupItems-BfxkhRY8.js";import"./DateRangeInput-BafIu0I7.js";import"./BottomSheet-C7Cy7dyi.js";const Kn=(function(){var i={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},n={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},v={defaultValue:null,kind:"LocalArgument",name:"limit"},p={defaultValue:null,kind:"LocalArgument",name:"offset"},b={defaultValue:null,kind:"LocalArgument",name:"orderBy"},h=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],f={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},m={alias:"vfolderStatus",args:null,kind:"ScalarField",name:"status",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},Re=[S],y={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},V=[y],Pe={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"}],concreteType:"VFolderConnection",kind:"LinkedField",name:"adminVfoldersV2",plural:!1,selections:V,storageKey:null},_={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"}],concreteType:"VFolderConnection",kind:"LinkedField",name:"adminVfoldersV2",plural:!1,selections:V,storageKey:null},I=[{alias:null,args:null,kind:"ScalarField",name:"expr",storageKey:null}],Me={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},L={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null};return{fragment:{argumentDefinitions:[i,e,n,v,p,b],kind:"Fragment",metadata:null,name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:h,concreteType:"VFolderConnection",kind:"LinkedField",name:"adminVfoldersV2",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:f,action:"THROW"},o,m,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:Re,storageKey:null},{args:null,kind:"FragmentSpread",name:"VFolderNodesV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"DeleteForeverVFolderModalV2Fragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalV2Fragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},y],storageKey:null},Pe,_],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[p,v,i,b,e,n],kind:"Operation",name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:h,concreteType:"VFolderConnection",kind:"LinkedField",name:"adminVfoldersV2",plural:!1,selections:[{alias:null,args:null,concreteType:"VFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VFolder",kind:"LinkedField",name:"node",plural:!1,selections:[f,o,m,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[S,{alias:null,args:null,kind:"ScalarField",name:"usageMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quotaScopeId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"lastUsed",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"unmanagedPath",storageKey:null},{alias:null,args:null,concreteType:"VFolderUsageInfo",kind:"LinkedField",name:"usage",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"numFiles",storageKey:null},{alias:null,args:null,concreteType:"BinarySizeInfo",kind:"LinkedField",name:"usedBytes",plural:!1,selections:I,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderAccessControlInfo",kind:"LinkedField",name:"accessControl",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownershipType",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"permissions",storageKey:null},{alias:null,args:null,concreteType:"VFolderQuotaInfo",kind:"LinkedField",name:"quota",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"maxFiles",storageKey:null},{alias:null,args:null,concreteType:"BinarySizeInfo",kind:"LinkedField",name:"maxSize",plural:!1,selections:I,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VFolderOwnershipInfo",kind:"LinkedField",name:"ownership",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"userId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creatorEmail",storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null},f],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:Re,storageKey:null},f],storageKey:null}],storageKey:null},{alias:null,args:[{kind:"Literal",name:"limit",value:100}],concreteType:"EntityLabelConnection",kind:"LinkedField",name:"entityLabels",plural:!1,selections:[{alias:null,args:null,concreteType:"EntityLabelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"EntityLabel",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},f,{alias:null,args:null,kind:"ScalarField",name:"fieldId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:"entityLabels(limit:100)"},{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[Me,F,S,L,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},f,L,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},F],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[S,f],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[Me],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[Me,F,L,S],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},y],storageKey:null},Pe,_]},params:{cacheID:"843e70ef09d965e48d24b83543f4eaf9",id:null,metadata:{},name:"AdminVFolderNodeListPageQuery",operationKind:"query",text:`query AdminVFolderNodeListPageQuery(
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
  entityId
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
  entityId
  metadata {
    name
  }
}

fragment DeleteVFolderModalV2Fragment on VFolder {
  id
  entityId
  metadata {
    name
  }
  permissions @since(version: "26.9.0rc1")
}

fragment RestoreVFolderModalV2Fragment on VFolder {
  id
  entityId
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
  entityId
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
`}}})();Kn.hash="92e6f71c20673fc29f11689016aa1dd5";const Tn=["DELETE_PENDING","DELETE_ONGOING","DELETE_ERROR","DELETE_COMPLETE"],Vn={status:{notIn:Tn}},In={status:{in:Tn}},_l="-created_at",Cl=["active","deleted"],Ll=["all","general","data","automount","model"],vl={general:{AND:[{name:{iNotStartsWith:"."}},{usageMode:{equals:"GENERAL"}}]},data:{usageMode:{equals:"DATA"}},automount:{name:{iStartsWith:"."}},model:{usageMode:{equals:"MODEL"}}},bl=["READY","CLONING","DELETE_PENDING","DELETE_ONGOING","DELETE_COMPLETE","DELETE_ERROR"],Ra=i=>{"use memo";var Sn;const e=xn.c(225),{t:n}=jn(),v=Rn("vfolder"),p=Pn(),[b,h]=On("table_column_overrides.AdminVFolderNodeListPage");let f;e[0]===Symbol.for("react.memo_cache_sentinel")?(f=[],e[0]=f):f=e[0];const[o,m]=Ne.useState(f),[S,Re]=an(!1),{toggle:y}=Re,[V,Pe]=an(!1),{toggle:_}=Pe,[I,Me]=an(!1),{toggle:F}=Me,[L,En]=an(!1),{toggle:K}=En;let Oe;e[1]===Symbol.for("react.memo_cache_sentinel")?(Oe={current:1,pageSize:10},e[1]=Oe):Oe=e[1];const{baiPaginationOption:T,tablePaginationOption:g,setTablePaginationOption:u}=pl(Oe);let we,qe;e[2]===Symbol.for("react.memo_cache_sentinel")?(we={order:yn(ml),filter:wn(hl),statusCategory:yn(Cl).withDefault("active"),mode:yn(Ll).withDefault("all")},qe={history:"replace"},e[2]=we,e[3]=qe):(we=e[2],qe=e[3]);const[l,d]=qn(we,qe);let E;e[4]!==l||e[5]!==g?(E={queryParams:l,tablePaginationOption:g},e[4]=l,e[5]=g,e[6]=E):E=e[6];let Ue;e[7]!==l.statusCategory||e[8]!==E?(Ue={[l.statusCategory]:E},e[7]=l.statusCategory,e[8]=E,e[9]=Ue):Ue=e[9];const kn=Ne.useRef(Ue);let ze,$e;e[10]!==l||e[11]!==g?(ze=()=>{kn.current[l.statusCategory]={queryParams:l,tablePaginationOption:g}},$e=[l,g],e[10]=l,e[11]=g,e[12]=ze,e[13]=$e):(ze=e[12],$e=e[13]),Ne.useEffect(ze,$e);const Ge=vl[l.mode],[Be,s]=Un(),tn=l.statusCategory==="deleted"?In:Vn;let A;e[14]!==Ge?(A=Ge?[Ge]:[],e[14]=Ge,e[15]=A):A=e[15];let N;e[16]!==l.filter?(N=l.filter?[l.filter]:[],e[16]=l.filter,e[17]=N):N=e[17];let Qe;e[18]!==tn||e[19]!==A||e[20]!==N?(Qe={AND:[tn,...A,...N]},e[18]=tn,e[19]=A,e[20]=N,e[21]=Qe):Qe=e[21];const rn=Qe,An=T.offset,Nn=T.limit,on=l.order||_l;let M;e[22]!==on?(M=zn(on),e[22]=on,e[23]=M):M=e[23];let He;e[24]!==T.limit||e[25]!==T.offset||e[26]!==rn||e[27]!==M?(He={offset:An,limit:Nn,filter:rn,orderBy:M,filterForActiveCount:Vn,filterForDeletedCount:In},e[24]=T.limit,e[25]=T.offset,e[26]=rn,e[27]=M,e[28]=He):He=e[28];const sn=He,dn=Ne.useDeferredValue(sn),De=Ne.useDeferredValue(Be);let We;e[29]===Symbol.for("react.memo_cache_sentinel")?(We=Kn,e[29]=We):We=e[29];const un=De===Hn?"store-and-network":"network-only";let Ye;e[30]!==De||e[31]!==un?(Ye={fetchPolicy:un,fetchKey:De},e[30]=De,e[31]=un,e[32]=Ye):Ye=e[32];const mn=$n.useLazyLoadQuery(We,dn,Ye);let r,C;e[33]!==mn?({adminVfoldersV2:r,...C}=mn,e[33]=mn,e[34]=r,e[35]=C):(r=e[34],C=e[35]);let B;e[36]!==n?(B=n("data.Folders"),e[36]=n,e[37]=B):B=e[37];const Mn=l.statusCategory;let D;e[38]!==d||e[39]!==u?(D=a=>{const c=kn.current[a]||{};d(null),d({...c.queryParams,statusCategory:a},{history:"replace"}),u(c.tablePaginationOption||{current:1}),m([])},e[38]=d,e[39]=u,e[40]=D):D=e[40];let x;if(e[41]!==C||e[42]!==l.statusCategory||e[43]!==n){let a;e[45]!==C||e[46]!==l.statusCategory?(a=(c,k)=>{var Cn;const _n=((Cn=C[k])==null?void 0:Cn.count)??0;return{key:k,label:c,endContent:_n>0?t.jsx(Yn,{label:_n,variant:l.statusCategory===k?"info":"neutral"}):void 0}},e[45]=C,e[46]=l.statusCategory,e[47]=a):a=e[47],x=je({active:n("data.Active"),deleted:n("data.folders.TrashBin")},a),e[41]=C,e[42]=l.statusCategory,e[43]=n,e[44]=x}else x=e[44];let j;e[48]!==l.statusCategory||e[49]!==D||e[50]!==x?(j=t.jsx(sl,{activeKey:Mn,onChange:D,items:x}),e[48]=l.statusCategory,e[49]=D,e[50]=x,e[51]=j):j=e[51];let Je;e[52]===Symbol.for("react.memo_cache_sentinel")?(Je={flexShrink:1},e[52]=Je):Je=e[52];const Bn=l.mode;let R;e[53]!==d||e[54]!==u?(R=a=>{d({mode:a}),u({current:1}),m([])},e[53]=d,e[54]=u,e[55]=R):R=e[55];let P;e[56]!==p._config.enableModelFolders||e[57]!==p._config.fasttrackEndpoint||e[58]!==n?(P=Gn([{label:n("data.All"),value:"all"},{label:n("data.General"),value:"general"},((Sn=p==null?void 0:p._config)==null?void 0:Sn.fasttrackEndpoint)&&{label:n("data.Pipeline"),value:"data"},{label:n("data.AutoMount"),value:"automount"},p._config.enableModelFolders&&{label:n("data.Models"),value:"model"}]).map(Vl),e[56]=p._config.enableModelFolders,e[57]=p._config.fasttrackEndpoint,e[58]=n,e[59]=P):P=e[59];let O;e[60]!==l.mode||e[61]!==R||e[62]!==P?(O=t.jsx(Jn,{value:Bn,onChange:R,children:P}),e[60]=l.mode,e[61]=R,e[62]=P,e[63]=O):O=e[63];let w;e[64]!==n?(w=n("data.folders.Name"),e[64]=n,e[65]=w):w=e[65];let q;e[66]!==w?(q={key:"name",propertyLabel:w,type:"string"},e[66]=w,e[67]=q):q=e[67];let U;e[68]!==n?(U=n("data.folders.Location"),e[68]=n,e[69]=U):U=e[69];let z;e[70]!==U?(z={key:"host",propertyLabel:U,type:"string"},e[70]=U,e[71]=z):z=e[71];let $;e[72]!==n?($=n("data.folders.Status"),e[72]=n,e[73]=$):$=e[73];let Xe;e[74]===Symbol.for("react.memo_cache_sentinel")?(Xe=je([...bl],Il),e[74]=Xe):Xe=e[74];let G;e[75]!==$?(G={key:"status",propertyLabel:$,type:"enum",strictSelection:!0,options:Xe},e[75]=$,e[76]=G):G=e[76];let Q;e[77]!==n?(Q=n("data.folders.CreatedAt"),e[77]=n,e[78]=Q):Q=e[78];let H;e[79]!==Q?(H={key:"createdAt",propertyLabel:Q,type:"datetime"},e[79]=Q,e[80]=H):H=e[80];let W;e[81]!==n?(W=n("data.folders.Cloneable"),e[81]=n,e[82]=W):W=e[82];let Y;e[83]!==W?(Y={key:"cloneable",propertyLabel:W,type:"boolean"},e[83]=W,e[84]=Y):Y=e[84];let J;e[85]!==v||e[86]!==n?(J=v?[{key:"labels.some.key",propertyLabel:n("entityLabel.LabelKey"),type:"string"},{key:"labels.some.value",propertyLabel:n("entityLabel.LabelValue"),type:"string"}]:[],e[85]=v,e[86]=n,e[87]=J):J=e[87];let X;e[88]!==q||e[89]!==z||e[90]!==G||e[91]!==H||e[92]!==Y||e[93]!==J?(X=[q,z,G,H,Y,...J],e[88]=q,e[89]=z,e[90]=G,e[91]=H,e[92]=Y,e[93]=J,e[94]=X):X=e[94];const cn=l.filter??void 0;let Z;e[95]!==d||e[96]!==u?(Z=a=>{d({filter:a??null}),u({current:1}),m([])},e[95]=d,e[96]=u,e[97]=Z):Z=e[97];let ee;e[98]!==X||e[99]!==cn||e[100]!==Z?(ee=t.jsx(kl,{"data-testid":"vfolder-filter",filterProperties:X,value:cn,onChange:Z}),e[98]=X,e[99]=cn,e[100]=Z,e[101]=ee):ee=e[101];let ne;e[102]!==O||e[103]!==ee?(ne=t.jsxs(xe,{gap:3,align:"start",style:Je,wrap:"wrap",children:[O,ee]}),e[102]=O,e[103]=ee,e[104]=ne):ne=e[104];let le;e[105]!==l.statusCategory||e[106]!==o||e[107]!==n||e[108]!==y||e[109]!==s?(le=o.length>0&&l.statusCategory==="active"&&t.jsxs(xe,{gap:1,align:"center",children:[t.jsx(hn,{count:o.length,onClearSelection:()=>m([])}),t.jsx(Fl,{entityType:"vfolder",targets:o.map(Kl),onLabelsChanged:()=>s()}),t.jsx(Fn,{label:n("data.folders.MoveToTrash"),tooltip:n("data.folders.MoveToTrash"),icon:t.jsx(ll,{color:"var(--color-error)"}),variant:"ghost",onClick:()=>{y()}})]}),e[105]=l.statusCategory,e[106]=o,e[107]=n,e[108]=y,e[109]=s,e[110]=le):le=e[110];let ae;e[111]!==l.statusCategory||e[112]!==o.length||e[113]!==n||e[114]!==K||e[115]!==_?(ae=o.length>0&&l.statusCategory==="deleted"&&t.jsxs(xe,{gap:1,align:"center",children:[t.jsx(hn,{count:o.length,onClearSelection:()=>m([])}),t.jsx(Fn,{label:n("data.folders.Restore"),tooltip:n("data.folders.Restore"),icon:t.jsx(al,{}),variant:"ghost",onClick:()=>{_()}}),t.jsx(Fn,{label:n("data.folders.Delete"),tooltip:n("data.folders.Delete"),icon:t.jsx(tl,{color:"var(--color-error)"}),variant:"ghost",onClick:()=>{K()}})]}),e[111]=l.statusCategory,e[112]=o.length,e[113]=n,e[114]=K,e[115]=_,e[116]=ae):ae=e[116];const gn=dn!==sn||De!==Be;let te;e[117]!==s?(te=a=>{s(a)},e[117]=s,e[118]=te):te=e[118];let re;e[119]!==Be||e[120]!==gn||e[121]!==te?(re=t.jsx(ol,{settingId:"admin-vfolder-list",loading:gn,value:Be,onChange:te}),e[119]=Be,e[120]=gn,e[121]=te,e[122]=re):re=e[122];let Ze;e[123]===Symbol.for("react.memo_cache_sentinel")?(Ze=t.jsx(rl,{}),e[123]=Ze):Ze=e[123];let oe;e[124]!==n?(oe=n("data.CreateFolder"),e[124]=n,e[125]=oe):oe=e[125];let se;e[126]!==F?(se=()=>{F()},e[126]=F,e[127]=se):se=e[127];let ie;e[128]!==oe||e[129]!==se?(ie=t.jsx(Xn,{variant:"primary",icon:Ze,label:oe,onClick:se}),e[128]=oe,e[129]=se,e[130]=ie):ie=e[130];let de;e[131]!==le||e[132]!==ae||e[133]!==re||e[134]!==ie?(de=t.jsxs(xe,{gap:2,children:[le,ae,re,ie]}),e[131]=le,e[132]=ae,e[133]=re,e[134]=ie,e[135]=de):de=e[135];let ue;e[136]!==ne||e[137]!==de?(ue=t.jsxs(xe,{justify:"between",wrap:"wrap",gap:3,children:[ne,de]}),e[136]=ne,e[137]=de,e[138]=ue):ue=e[138];let en;e[139]===Symbol.for("react.memo_cache_sentinel")?(en=t.jsx(Zn,{rows:4}),e[139]=en):en=e[139];const Dn=l.order,fn=dn!==sn;let me;e[140]!==n?(me=n("data.folders.CannotDeployFromAdminMenu"),e[140]=n,e[141]=me):me=e[141];let ce;e[142]!==(r==null?void 0:r.edges)?(ce=Ln(je(r==null?void 0:r.edges,"node")),e[142]=r==null?void 0:r.edges,e[143]=ce):ce=e[143];let ge;if(e[144]!==(r==null?void 0:r.edges)||e[145]!==o){let a;e[147]!==(r==null?void 0:r.edges)?(a=k=>{el(k,Ln(je(r==null?void 0:r.edges,"node")),m)},e[147]=r==null?void 0:r.edges,e[148]=a):a=e[148];let c;e[149]!==o?(c=je(o,Tl),e[149]=o,e[150]=c):c=e[150],ge={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(k){return{disabled:il(k.vfolderStatus)&&k.vfolderStatus!=="DELETE_PENDING"}},onChange:a,selectedRowKeys:c},e[144]=r==null?void 0:r.edges,e[145]=o,e[146]=ge}else ge=e[146];const pn=(r==null?void 0:r.count)??0;let fe;e[151]!==u||e[152]!==pn||e[153]!==g.current||e[154]!==g.pageSize?(fe={pageSize:g.pageSize,current:g.current,total:pn,onChange(a,c){bn(a)&&bn(c)&&u({current:a,pageSize:c})}},e[151]=u,e[152]=pn,e[153]=g.current,e[154]=g.pageSize,e[155]=fe):fe=e[155];let pe;e[156]!==d?(pe=a=>{d({order:a??null})},e[156]=d,e[157]=pe):pe=e[157];let ye;e[158]!==s?(ye=()=>s(),e[158]=s,e[159]=ye):ye=e[159];let Fe;e[160]!==d||e[161]!==u?(Fe=a=>{d({filter:Sl(a)}),u({current:1}),m([])},e[160]=d,e[161]=u,e[162]=Fe):Fe=e[162];let ke;e[163]!==s?(ke=a=>{m(c=>yl(c,k=>k.id!==a)),s()},e[163]=s,e[164]=ke):ke=e[164];let nn;e[165]===Symbol.for("react.memo_cache_sentinel")?(nn={cur_size:{hidden:!1},max_size:{hidden:!1},created_at:{hidden:!1}},e[165]=nn):nn=e[165];let Se;e[166]!==b||e[167]!==h?(Se={columnOverrides:b,defaultColumnOverrides:nn,onColumnOverridesChange:h},e[166]=b,e[167]=h,e[168]=Se):Se=e[168];let _e;e[169]!==l.order||e[170]!==fn||e[171]!==me||e[172]!==ce||e[173]!==ge||e[174]!==fe||e[175]!==pe||e[176]!==ye||e[177]!==Fe||e[178]!==ke||e[179]!==Se?(_e=t.jsx(Ne.Suspense,{fallback:en,children:t.jsx(dl,{order:Dn,loading:fn,project:null,noDeployTooltip:me,vfoldersFrgmt:ce,rowSelection:ge,pagination:fe,onChangeOrder:pe,onLabelsChanged:ye,showLabelsByDefault:!0,onLabelClick:Fe,onRemoveRow:ke,tableSettings:Se})}),e[169]=l.order,e[170]=fn,e[171]=me,e[172]=ce,e[173]=ge,e[174]=fe,e[175]=pe,e[176]=ye,e[177]=Fe,e[178]=ke,e[179]=Se,e[180]=_e):_e=e[180];let Ce;e[181]!==ue||e[182]!==_e?(Ce=t.jsxs(vn,{align:"stretch",gap:3,children:[ue,_e]}),e[181]=ue,e[182]=_e,e[183]=Ce):Ce=e[183];let Le;e[184]!==B||e[185]!==j||e[186]!==Ce?(Le=t.jsxs(nl,{title:B,children:[j,Ce]}),e[184]=B,e[185]=j,e[186]=Ce,e[187]=Le):Le=e[187];let ve;e[188]!==y||e[189]!==s?(ve=a=>{a&&(s(),m([])),y()},e[188]=y,e[189]=s,e[190]=ve):ve=e[190];let be;e[191]!==S||e[192]!==o||e[193]!==ve?(be=t.jsx(cl,{vfolderFrgmts:o,open:S,onRequestClose:ve}),e[191]=S,e[192]=o,e[193]=ve,e[194]=be):be=e[194];let he;e[195]!==_||e[196]!==s?(he=a=>{a&&(s(),m([])),_()},e[195]=_,e[196]=s,e[197]=he):he=e[197];let Ve;e[198]!==V||e[199]!==o||e[200]!==he?(Ve=t.jsx(gl,{vfolderFrgmts:o,open:V,onRequestClose:he}),e[198]=V,e[199]=o,e[200]=he,e[201]=Ve):Ve=e[201];let Ie;e[202]!==K||e[203]!==s?(Ie=a=>{a&&(s(),m([])),K()},e[202]=K,e[203]=s,e[204]=Ie):Ie=e[204];let Ke;e[205]!==L||e[206]!==o||e[207]!==Ie?(Ke=t.jsx(ul,{vfolderFrgmts:o,open:L,onRequestClose:Ie}),e[205]=L,e[206]=o,e[207]=Ie,e[208]=Ke):Ke=e[208];let Te;e[209]!==n?(Te=n("data.folders.AdminDataPageAlert"),e[209]=n,e[210]=Te):Te=e[210];let Ee;e[211]!==F||e[212]!==s?(Ee=a=>{F(),a&&s()},e[211]=F,e[212]=s,e[213]=Ee):Ee=e[213];let Ae;e[214]!==I||e[215]!==Te||e[216]!==Ee?(Ae=t.jsx(fl,{open:I,project:null,folderType:"project",alertMessage:Te,onRequestClose:Ee}),e[214]=I,e[215]=Te,e[216]=Ee,e[217]=Ae):Ae=e[217];let ln;return e[218]!==i||e[219]!==Le||e[220]!==be||e[221]!==Ve||e[222]!==Ke||e[223]!==Ae?(ln=t.jsx(Qn,{children:t.jsxs(vn,{align:"stretch",gap:5,...i,children:[Le,be,Ve,Ke,Ae]})}),e[218]=i,e[219]=Le,e[220]=be,e[221]=Ve,e[222]=Ke,e[223]=Ae,e[224]=ln):ln=e[224],ln};function hl(i){return i}function Vl(i){return t.jsx(Wn,{value:i.value,label:i.label},i.value)}function Il(i){return{label:i,value:i}}function Kl(i){var e;return{entityId:i.entityId,name:((e=i.metadata)==null?void 0:e.name)??void 0}}function Tl(i){return i.id}export{Ra as default};
//# sourceMappingURL=AdminVFolderNodeListPage-BZur0Lcm.js.map
