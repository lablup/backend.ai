import{i as Mn,u as Rn,a as Dn,a7 as xn,l as xe,bD as pn,bE as Pn,af as an,ae as On,cj as Bn,e3 as jn,r as wn,al as Pe,ah as $n,j as r,c9 as hn,hD as qn,q as Gn,K as Qn,a$ as Un,aS as Nn,bL as Vn,au as zn,as as bn,g as Hn,aa as Wn,cC as Yn,b0 as Jn,d4 as yn,cz as Xn,P as Zn,at as el,ew as nl,hE as ll,ak as al,hF as tl,d as rl,hG as sl,hH as il,Q as ol}from"./index-DPebpL40.js";const vn=(function(){var g={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},n={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},f={defaultValue:null,kind:"LocalArgument",name:"first"},b={defaultValue:null,kind:"LocalArgument",name:"offset"},v={defaultValue:null,kind:"LocalArgument",name:"order"},N={defaultValue:null,kind:"LocalArgument",name:"permission"},s={kind:"Variable",name:"permission",variableName:"permission"},m=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"},s],S={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},Oe={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"permissions",storageKey:null},V={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},Be={kind:"Literal",name:"first",value:0},y={kind:"Literal",name:"offset",value:0},K=[V],je={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"},Be,y,s],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:K,storageKey:null},_={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"},Be,y,s],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:K,storageKey:null},C={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null};return{fragment:{argumentDefinitions:[g,e,n,f,b,v,N],kind:"Fragment",metadata:null,name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:m,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:S,action:"THROW"},Oe,F,{args:null,kind:"FragmentSpread",name:"VFolderNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalFragment"},{args:null,kind:"FragmentSpread",name:"EditableVFolderNameFragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalFragment"},{args:null,kind:"FragmentSpread",name:"VFolderNodeIdenticonFragment"},{args:null,kind:"FragmentSpread",name:"SharedFolderPermissionInfoModalFragment"},{args:null,kind:"FragmentSpread",name:"BAIVFolderDeleteButtonFragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},V],storageKey:null},je,_],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[b,f,g,v,N,e,n],kind:"Operation",name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:m,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[S,Oe,F,C,{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownership_type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"last_used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"num_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cur_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null},F,k,{alias:null,args:null,kind:"ScalarField",name:"creator",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[o,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},S,k,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[C,S],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[o,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[C],storageKey:null}],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[o],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},V],storageKey:null},je,_]},params:{cacheID:"d8850204541e90e662e6da1b08462675",id:null,metadata:{},name:"AdminVFolderNodeListPageQuery",operationKind:"query",text:`query AdminVFolderNodeListPageQuery(
  $offset: Int
  $first: Int
  $filter: String
  $order: String
  $permission: VFolderPermissionValueField
  $filterForActiveCount: String
  $filterForDeletedCount: String
) {
  vfolder_nodes(offset: $offset, first: $first, filter: $filter, order: $order, permission: $permission) {
    edges {
      node {
        id
        status
        permissions
        ...VFolderNodesFragment
        ...DeleteVFolderModalFragment
        ...EditableVFolderNameFragment
        ...RestoreVFolderModalFragment
        ...VFolderNodeIdenticonFragment
        ...SharedFolderPermissionInfoModalFragment
        ...BAIVFolderDeleteButtonFragment
      }
    }
    count
  }
  active: vfolder_nodes(first: 0, offset: 0, filter: $filterForActiveCount, permission: $permission) {
    count
  }
  deleted: vfolder_nodes(first: 0, offset: 0, filter: $filterForDeletedCount, permission: $permission) {
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
  ...SessionStatusTagFragment
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

fragment BAIVFolderDeleteButtonFragment on VirtualFolderNode {
  permissions
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

fragment DeleteVFolderModalFragment on VirtualFolderNode {
  id
  name
  permissions
}

fragment EditableVFolderNameFragment on VirtualFolderNode {
  id
  name
  user
  group
  status
}

fragment RestoreVFolderModalFragment on VirtualFolderNode {
  id
  name
}

fragment SFTPConnectionInfoModalFragment on ComputeSessionNode {
  row_id
  vfolder_nodes @since(version: "25.4.0") {
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

fragment SessionStatusTagFragment on ComputeSessionNode {
  id
  status
  status_info
  status_data
  queue_position @since(version: "25.13.0")
}

fragment SharedFolderPermissionInfoModalFragment on VirtualFolderNode {
  id
  name
  row_id
  creator
  ownership_type
  user_email
  permission
  ...VFolderPermissionCellFragment
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

fragment VFolderNodeIdenticonFragment on VirtualFolderNode {
  id
}

fragment VFolderNodesFragment on VirtualFolderNode {
  id
  status
  name
  host
  quota_scope_id
  ownership_type
  user
  user_email
  group
  group_name
  usage_mode
  max_files
  max_size
  created_at
  last_used
  num_files
  cur_size
  cloneable
  permissions @since(version: "24.09.0")
  ...VFolderPermissionCellFragment
  ...VFolderNodeIdenticonFragment
  ...SharedFolderPermissionInfoModalFragment
  ...BAINodeNotificationItemFragment
}

fragment VFolderPermissionCellFragment on VirtualFolderNode {
  permissions
}

fragment useBackendAIAppLauncherFragment on ComputeSessionNode {
  name
  row_id
  vfolder_mounts
  scaling_group
  project_id
  service_ports
}
`}}})();vn.hash="61335271ca378f8ff80cff73517798c7";const dl=["READY","PERFORMING","CLONING","MOUNTED","ERROR","DELETE_PENDING","DELETE_ONGOING","DELETE_COMPLETE","DELETE_ERROR"],tn={active:'status != "DELETE_PENDING" & status != "DELETE_ONGOING" & status != "DELETE_ERROR" & status != "DELETE_COMPLETE"',deleted:'status in ["DELETE_PENDING", "DELETE_ONGOING", "DELETE_ERROR"]'},fl=g=>{"use memo";var kn;const e=Mn.c(228),{t:n}=Rn(),f=Dn(),[b,v]=xn("table_column_overrides.AdminVFolderNodeListPage");let N;e[0]===Symbol.for("react.memo_cache_sentinel")?(N=[],e[0]=N):N=e[0];const[s,m]=xe.useState(N),[S,Oe]=pn(!1),{toggle:F}=Oe,[V,Be]=pn(!1),{toggle:y}=Be,[K,je]=pn(!1),{toggle:_}=je;let C;e[1]===Symbol.for("react.memo_cache_sentinel")?(C={current:1,pageSize:10},e[1]=C):C=e[1];const{baiPaginationOption:k,tablePaginationOption:o,setTablePaginationOption:c}=Pn(C);let we;e[2]===Symbol.for("react.memo_cache_sentinel")?(we=an.withDefault("-created_at"),e[2]=we):we=e[2];let $e,qe;e[3]===Symbol.for("react.memo_cache_sentinel")?($e={order:we,filter:an,statusCategory:an.withDefault("active"),mode:an.withDefault("all")},qe={history:"replace"},e[3]=$e,e[4]=qe):($e=e[3],qe=e[4]);const[l,u]=On($e,qe);let L;e[5]!==l||e[6]!==o?(L={queryParams:l,tablePaginationOption:o},e[5]=l,e[6]=o,e[7]=L):L=e[7];let Ge;e[8]!==l.statusCategory||e[9]!==L?(Ge={[l.statusCategory]:L},e[8]=l.statusCategory,e[9]=L,e[10]=Ge):Ge=e[10];const _n=xe.useRef(Ge);let Qe,Ue;e[11]!==l||e[12]!==o?(Qe=()=>{_n.current[l.statusCategory]={queryParams:l,tablePaginationOption:o}},Ue=[l,o],e[11]=l,e[12]=o,e[13]=Qe,e[14]=Ue):(Qe=e[13],Ue=e[14]),xe.useEffect(Qe,Ue);let ze;e[15]===Symbol.for("react.memo_cache_sentinel")?(ze=function(i){switch(i){case"all":case void 0:return;case"general":return`(! name ilike ".%")&(usage_mode == "${i}")`;case"pipeline":return'usage_mode == "data"';case"automount":return'name ilike ".%"';default:return`usage_mode == "${i}"`}},e[15]=ze):ze=e[15];const Kn=ze(l.mode),[De,d]=Bn("initial-fetch"),Ln=k.offset,An=k.first,rn=jn([l.statusCategory==="active"||l.statusCategory===void 0?tn.active:tn.deleted,l.filter,Kn]);let He;e[16]!==k.first||e[17]!==k.offset||e[18]!==l.order||e[19]!==rn?(He={offset:Ln,first:An,filter:rn,order:l.order,permission:"read_attribute",filterForActiveCount:tn.active,filterForDeletedCount:tn.deleted},e[16]=k.first,e[17]=k.offset,e[18]=l.order,e[19]=rn,e[20]=He):He=e[20];const sn=He,on=xe.useDeferredValue(sn),We=xe.useDeferredValue(De);let Ye;e[21]===Symbol.for("react.memo_cache_sentinel")?(Ye=vn,e[21]=Ye):Ye=e[21];const dn=We==="initial-fetch"?"store-and-network":"network-only",un=We==="initial-fetch"?void 0:We;let Je;e[22]!==dn||e[23]!==un?(Je={fetchPolicy:dn,fetchKey:un},e[22]=dn,e[23]=un,e[24]=Je):Je=e[24];const mn=wn.useLazyLoadQuery(Ye,on,Je);let h,t;e[25]!==mn?({vfolder_nodes:t,...h}=mn,e[25]=mn,e[26]=h,e[27]=t):(h=e[26],t=e[27]);let A;e[28]!==n?(A=n("data.Folders"),e[28]=n,e[29]=A):A=e[29];const En=l.statusCategory;let E;e[30]!==u||e[31]!==c?(E=a=>{const i=_n.current[a]||{};u(null),u({...i.queryParams,statusCategory:a}),c(i.tablePaginationOption||{current:1}),m([])},e[30]=u,e[31]=c,e[32]=E):E=e[32];let I;if(e[33]!==h||e[34]!==l.statusCategory||e[35]!==n){let a;e[37]!==h||e[38]!==l.statusCategory?(a=(i,p)=>{var Cn;const Sn=((Cn=h[p])==null?void 0:Cn.count)??0;return{key:p,label:i,endContent:Sn>0?r.jsx(Hn,{label:Sn,variant:l.statusCategory===p?"info":"neutral"}):void 0}},e[37]=h,e[38]=l.statusCategory,e[39]=a):a=e[39],I=Pe({active:n("data.Active"),deleted:n("data.folders.TrashBin")},a),e[33]=h,e[34]=l.statusCategory,e[35]=n,e[36]=I}else I=e[36];let T;e[40]!==l.statusCategory||e[41]!==E||e[42]!==I?(T=r.jsx(Wn,{activeKey:En,onChange:E,items:I}),e[40]=l.statusCategory,e[41]=E,e[42]=I,e[43]=T):T=e[43];let Xe;e[44]===Symbol.for("react.memo_cache_sentinel")?(Xe={flexShrink:1},e[44]=Xe):Xe=e[44];const In=l.mode;let M;e[45]!==u||e[46]!==c?(M=a=>{u({mode:a.target.value}),c({current:1}),m([])},e[45]=u,e[46]=c,e[47]=M):M=e[47];let R;e[48]!==f._config.enableModelFolders||e[49]!==f._config.fasttrackEndpoint||e[50]!==n?(R=$n([{label:n("data.All"),value:"all"},{label:n("data.General"),value:"general"},((kn=f==null?void 0:f._config)==null?void 0:kn.fasttrackEndpoint)&&{label:n("data.Pipeline"),value:"data"},{label:n("data.AutoMount"),value:"automount"},f._config.enableModelFolders&&{label:n("data.Models"),value:"model"}]),e[48]=f._config.enableModelFolders,e[49]=f._config.fasttrackEndpoint,e[50]=n,e[51]=R):R=e[51];let D;e[52]!==l.mode||e[53]!==M||e[54]!==R?(D=r.jsx(Yn,{optionType:"button",value:In,onChange:M,options:R}),e[52]=l.mode,e[53]=M,e[54]=R,e[55]=D):D=e[55];let Ze;e[56]===Symbol.for("react.memo_cache_sentinel")?(Ze={minWidth:320,flex:1},e[56]=Ze):Ze=e[56];let x;e[57]!==n?(x=n("settings.SearchPlaceholder"),e[57]=n,e[58]=x):x=e[58];let P;e[59]!==n?(P=n("data.SearchByName"),e[59]=n,e[60]=P):P=e[60];let O;e[61]!==n?(O=n("button.Apply"),e[61]=n,e[62]=O):O=e[62];let B;e[63]!==n?(B=n("data.folders.Name"),e[63]=n,e[64]=B):B=e[64];let j;e[65]!==B?(j={key:"name",propertyLabel:B,type:"string"},e[65]=B,e[66]=j):j=e[66];let w;e[67]!==n?(w=n("data.folders.Status"),e[67]=n,e[68]=w):w=e[68];let en;e[69]===Symbol.for("react.memo_cache_sentinel")?(en=Pe(dl,ul),e[69]=en):en=e[69];let $;e[70]!==w?($={key:"status",propertyLabel:w,type:"string",strictSelection:!0,defaultOperator:"==",options:en},e[70]=w,e[71]=$):$=e[71];let q;e[72]!==n?(q=n("data.folders.Location"),e[72]=n,e[73]=q):q=e[73];let G;e[74]!==q?(G={key:"host",propertyLabel:q,type:"string"},e[74]=q,e[75]=G):G=e[75];let Q;e[76]!==n?(Q=n("data.Type"),e[76]=n,e[77]=Q):Q=e[77];let U;e[78]!==n?(U=n("data.User"),e[78]=n,e[79]=U):U=e[79];let z;e[80]!==U?(z={label:U,value:"user"},e[80]=U,e[81]=z):z=e[81];let H;e[82]!==n?(H=n("data.Project"),e[82]=n,e[83]=H):H=e[83];let W;e[84]!==H?(W={label:H,value:"group"},e[84]=H,e[85]=W):W=e[85];let Y;e[86]!==z||e[87]!==W?(Y=[z,W],e[86]=z,e[87]=W,e[88]=Y):Y=e[88];let J;e[89]!==Q||e[90]!==Y?(J={key:"ownership_type",propertyLabel:Q,type:"string",strictSelection:!0,defaultOperator:"==",options:Y},e[89]=Q,e[90]=Y,e[91]=J):J=e[91];let X;e[92]!==n?(X=n("data.Permission"),e[92]=n,e[93]=X):X=e[93];let Z;e[94]!==n?(Z=n("data.ReadOnly"),e[94]=n,e[95]=Z):Z=e[95];let ee;e[96]!==Z?(ee={label:Z,value:"ro"},e[96]=Z,e[97]=ee):ee=e[97];let ne;e[98]!==n?(ne=n("data.ReadWrite"),e[98]=n,e[99]=ne):ne=e[99];let le;e[100]!==ne?(le={label:ne,value:"rw"},e[100]=ne,e[101]=le):le=e[101];let ae;e[102]!==ee||e[103]!==le?(ae=[ee,le],e[102]=ee,e[103]=le,e[104]=ae):ae=e[104];let te;e[105]!==X||e[106]!==ae?(te={key:"permission",propertyLabel:X,type:"string",strictSelection:!0,defaultOperator:"==",options:ae},e[105]=X,e[106]=ae,e[107]=te):te=e[107];let re;e[108]!==j||e[109]!==$||e[110]!==G||e[111]!==J||e[112]!==te?(re=[j,$,G,J,te],e[108]=j,e[109]=$,e[110]=G,e[111]=J,e[112]=te,e[113]=re):re=e[113];const cn=l.filter??void 0;let se;e[114]!==u||e[115]!==c?(se=a=>{u({filter:a??null}),c({current:1}),m([])},e[114]=u,e[115]=c,e[116]=se):se=e[116];let ie;e[117]!==x||e[118]!==P||e[119]!==O||e[120]!==re||e[121]!==cn||e[122]!==se?(ie=r.jsx(Jn,{"data-testid":"vfolder-filter",style:Ze,label:x,placeholder:P,applyLabel:O,contentSearchFieldKey:"name",filterProperties:re,value:cn,onChange:se}),e[117]=x,e[118]=P,e[119]=O,e[120]=re,e[121]=cn,e[122]=se,e[123]=ie):ie=e[123];let oe;e[124]!==D||e[125]!==ie?(oe=r.jsxs(yn,{gap:3,align:"start",style:Xe,wrap:"wrap",children:[D,ie]}),e[124]=D,e[125]=ie,e[126]=oe):oe=e[126];let de;e[127]!==l.statusCategory||e[128]!==s||e[129]!==n||e[130]!==F?(de=s.length>0&&l.statusCategory==="active"&&r.jsxs(r.Fragment,{children:[r.jsx(hn,{count:s.length,onClearSelection:()=>m([])}),r.jsx(qn,{vfolderFrgmt:s,label:n("data.folders.MoveToTrash"),onClick:()=>{F()}})]}),e[127]=l.statusCategory,e[128]=s,e[129]=n,e[130]=F,e[131]=de):de=e[131];let ue;e[132]!==l.statusCategory||e[133]!==s.length||e[134]!==n||e[135]!==y?(ue=s.length>0&&l.statusCategory==="deleted"&&r.jsxs(r.Fragment,{children:[r.jsx(hn,{count:s.length,onClearSelection:()=>m([])}),r.jsx(Gn,{content:n("data.folders.Restore"),children:r.jsx(Qn,{label:n("data.folders.Restore"),icon:r.jsx(Un,{}),onClick:()=>{y()}})})]}),e[132]=l.statusCategory,e[133]=s.length,e[134]=n,e[135]=y,e[136]=ue):ue=e[136];const gn=on!==sn||We!==De;let me;e[137]!==d?(me=a=>{d(a)},e[137]=d,e[138]=me):me=e[138];let ce;e[139]!==De||e[140]!==gn||e[141]!==me?(ce=r.jsx(Xn,{settingId:"admin-vfolder-list",loading:gn,value:De,onChange:me}),e[139]=De,e[140]=gn,e[141]=me,e[142]=ce):ce=e[142];let nn;e[143]===Symbol.for("react.memo_cache_sentinel")?(nn=r.jsx(Zn,{}),e[143]=nn):nn=e[143];let ge;e[144]!==n?(ge=n("data.CreateFolder"),e[144]=n,e[145]=ge):ge=e[145];let fe;e[146]!==_?(fe=()=>{_()},e[146]=_,e[147]=fe):fe=e[147];let Fe;e[148]!==ge||e[149]!==fe?(Fe=r.jsx(el,{variant:"primary",icon:nn,label:ge,onClick:fe}),e[148]=ge,e[149]=fe,e[150]=Fe):Fe=e[150];let pe;e[151]!==de||e[152]!==ue||e[153]!==ce||e[154]!==Fe?(pe=r.jsxs(yn,{gap:2,children:[de,ue,ce,Fe]}),e[151]=de,e[152]=ue,e[153]=ce,e[154]=Fe,e[155]=pe):pe=e[155];let ye;e[156]!==oe||e[157]!==pe?(ye=r.jsxs(yn,{justify:"between",wrap:"wrap",gap:3,children:[oe,pe]}),e[156]=oe,e[157]=pe,e[158]=ye):ye=e[158];const Tn=l.order,fn=on!==sn;let _e;e[159]!==n?(_e=n("data.folders.CannotDeployFromAdminMenu"),e[159]=n,e[160]=_e):_e=e[160];let ke;e[161]!==(t==null?void 0:t.edges)?(ke=Nn(Pe(t==null?void 0:t.edges,"node")),e[161]=t==null?void 0:t.edges,e[162]=ke):ke=e[162];let Se;if(e[163]!==s||e[164]!==(t==null?void 0:t.edges)){let a;e[166]!==(t==null?void 0:t.edges)?(a=p=>{nl(p,Nn(Pe(t==null?void 0:t.edges,"node")),m)},e[166]=t==null?void 0:t.edges,e[167]=a):a=e[167];let i;e[168]!==s?(i=Pe(s,ml),e[168]=s,e[169]=i):i=e[169],Se={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(p){return{disabled:ll(p.status)&&p.status!=="delete-pending"}},onChange:a,selectedRowKeys:i},e[163]=s,e[164]=t==null?void 0:t.edges,e[165]=Se}else Se=e[165];const Fn=(t==null?void 0:t.count)??0;let Ce;e[170]!==c||e[171]!==Fn||e[172]!==o.current||e[173]!==o.pageSize?(Ce={pageSize:o.pageSize,current:o.current,total:Fn,onChange(a,i){Vn(a)&&Vn(i)&&c({current:a,pageSize:i})}},e[170]=c,e[171]=Fn,e[172]=o.current,e[173]=o.pageSize,e[174]=Ce):Ce=e[174];let he;e[175]!==u?(he=a=>{u({order:a??null})},e[175]=u,e[176]=he):he=e[176];let Ne;e[177]!==d?(Ne=a=>{m(i=>al(i,p=>p.id!==a)),d()},e[177]=d,e[178]=Ne):Ne=e[178];let Ve;e[179]!==b||e[180]!==v?(Ve={columnOverrides:b,onColumnOverridesChange:v},e[179]=b,e[180]=v,e[181]=Ve):Ve=e[181];let be;e[182]!==l.order||e[183]!==fn||e[184]!==_e||e[185]!==ke||e[186]!==Se||e[187]!==Ce||e[188]!==he||e[189]!==Ne||e[190]!==Ve?(be=r.jsx(tl,{order:Tn,loading:fn,project:null,noDeployTooltip:_e,vfoldersFrgmt:ke,rowSelection:Se,pagination:Ce,onChangeOrder:he,onRemoveRow:Ne,tableSettings:Ve}),e[182]=l.order,e[183]=fn,e[184]=_e,e[185]=ke,e[186]=Se,e[187]=Ce,e[188]=he,e[189]=Ne,e[190]=Ve,e[191]=be):be=e[191];let ve;e[192]!==ye||e[193]!==be?(ve=r.jsxs(bn,{align:"stretch",gap:3,children:[ye,be]}),e[192]=ye,e[193]=be,e[194]=ve):ve=e[194];let Ke;e[195]!==A||e[196]!==T||e[197]!==ve?(Ke=r.jsxs(rl,{title:A,children:[T,ve]}),e[195]=A,e[196]=T,e[197]=ve,e[198]=Ke):Ke=e[198];let Le;e[199]!==F||e[200]!==d?(Le=a=>{a&&(d(),m([])),F()},e[199]=F,e[200]=d,e[201]=Le):Le=e[201];let Ae;e[202]!==S||e[203]!==s||e[204]!==Le?(Ae=r.jsx(sl,{vfolderFrgmts:s,open:S,onRequestClose:Le}),e[202]=S,e[203]=s,e[204]=Le,e[205]=Ae):Ae=e[205];let Ee;e[206]!==y||e[207]!==d?(Ee=a=>{a&&(d(),m([])),y()},e[206]=y,e[207]=d,e[208]=Ee):Ee=e[208];let Ie;e[209]!==V||e[210]!==s||e[211]!==Ee?(Ie=r.jsx(il,{vfolderFrgmts:s,open:V,onRequestClose:Ee}),e[209]=V,e[210]=s,e[211]=Ee,e[212]=Ie):Ie=e[212];let Te;e[213]!==n?(Te=n("data.folders.AdminDataPageAlert"),e[213]=n,e[214]=Te):Te=e[214];let Me;e[215]!==_||e[216]!==d?(Me=a=>{_(),a&&d()},e[215]=_,e[216]=d,e[217]=Me):Me=e[217];let Re;e[218]!==K||e[219]!==Te||e[220]!==Me?(Re=r.jsx(ol,{open:K,project:null,folderType:"project",alertMessage:Te,onRequestClose:Me}),e[218]=K,e[219]=Te,e[220]=Me,e[221]=Re):Re=e[221];let ln;return e[222]!==g||e[223]!==Ke||e[224]!==Ae||e[225]!==Ie||e[226]!==Re?(ln=r.jsx(zn,{children:r.jsxs(bn,{align:"stretch",gap:5,...g,children:[Ke,Ae,Ie,Re]})}),e[222]=g,e[223]=Ke,e[224]=Ae,e[225]=Ie,e[226]=Re,e[227]=ln):ln=e[227],ln};function ul(g){return{label:g,value:g}}function ml(g){return g.id}export{fl as default};
//# sourceMappingURL=AdminVFolderNodeListPage-CR6tuS82.js.map
