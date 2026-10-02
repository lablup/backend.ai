import{i as Yn,u as Jn,a as Xn,a7 as Zn,l as He,bG as Mn,bH as el,ao as Sn,ae as nl,co as ll,dV as al,r as tl,ak as Je,ag as sl,j as t,cc as On,hF as rl,q as il,K as ol,b0 as dl,aT as jn,bO as Bn,au as ul,as as wn,aQ as cl,aa as ml,di as gl,cY as fl,b1 as pl,cI as Rn,dG as Fl,P as yl,at as _l,aV as kl,eG as Sl,hG as Cl,aj as hl,hH as bl,d as Nl,hI as Vl,hJ as vl,Q as Ll}from"./index-BQcmV02I.js";import{B as Al}from"./BAIAdminProjectSelect-sFQRmMl8.js";const $n=(function(){var f={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},n={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},p={defaultValue:null,kind:"LocalArgument",name:"first"},V={defaultValue:null,kind:"LocalArgument",name:"offset"},v={defaultValue:null,kind:"LocalArgument",name:"order"},h={defaultValue:null,kind:"LocalArgument",name:"permission"},r={kind:"Variable",name:"permission",variableName:"permission"},c=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"},r],S={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},We={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"permissions",storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},Xe={kind:"Literal",name:"first",value:0},_={kind:"Literal",name:"offset",value:0},L=[b],Ze={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"},Xe,_,r],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:L,storageKey:null},k={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"},Xe,_,r],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:L,storageKey:null},N={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null};return{fragment:{argumentDefinitions:[f,e,n,p,V,v,h],kind:"Fragment",metadata:null,name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:c,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:S,action:"THROW"},We,F,{args:null,kind:"FragmentSpread",name:"VFolderNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalFragment"},{args:null,kind:"FragmentSpread",name:"EditableVFolderNameFragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalFragment"},{args:null,kind:"FragmentSpread",name:"VFolderNodeIdenticonFragment"},{args:null,kind:"FragmentSpread",name:"SharedFolderPermissionInfoModalFragment"},{args:null,kind:"FragmentSpread",name:"BAIVFolderDeleteButtonFragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},b],storageKey:null},Ze,k],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[V,p,f,v,h,e,n],kind:"Operation",name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:c,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[S,We,F,N,y,{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownership_type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creator",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"last_used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"num_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cur_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null},F,{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[o,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},S,N,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null},We],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[y,S],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[o,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[y],storageKey:null}],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[o],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},b],storageKey:null},Ze,k]},params:{cacheID:"7cc6132f5ec88147571a94c85c85ef52",id:null,metadata:{},name:"AdminVFolderNodeListPageQuery",operationKind:"query",text:`query AdminVFolderNodeListPageQuery(
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
  ...SessionStatusBadgeFragment
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

fragment SessionStatusBadgeFragment on ComputeSessionNode {
  id
  status
  status_info
  status_data
  queue_position @since(version: "25.13.0")
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
  row_id
  status
  name
  host
  quota_scope_id
  ownership_type
  user
  user_email
  group
  group_name
  creator
  permission
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
`}}})();$n.hash="61335271ca378f8ff80cff73517798c7";const Kl=["READY","PERFORMING","CLONING","MOUNTED","ERROR","DELETE_PENDING","DELETE_ONGOING","DELETE_COMPLETE","DELETE_ERROR"],El="-created_at",Cn={active:'status != "DELETE_PENDING" & status != "DELETE_ONGOING" & status != "DELETE_ERROR" & status != "DELETE_COMPLETE"',deleted:'status in ["DELETE_PENDING", "DELETE_ONGOING", "DELETE_ERROR", "DELETE_COMPLETE"]'},Pl=f=>{"use memo";var Pn;const e=Yn.c(262),{t:n}=Jn(),p=Xn(),[V,v]=Zn("table_column_overrides.AdminVFolderNodeListPage");let h;e[0]===Symbol.for("react.memo_cache_sentinel")?(h=[],e[0]=h):h=e[0];const[r,c]=He.useState(h),[S,We]=Mn(!1),{toggle:F}=We,[b,Xe]=Mn(!1),{toggle:_}=Xe,[L,Ze]=Mn(!1),{toggle:k}=Ze;let N;e[1]===Symbol.for("react.memo_cache_sentinel")?(N={current:1,pageSize:10},e[1]=N):N=e[1];const{baiPaginationOption:y,tablePaginationOption:o,setTablePaginationOption:m}=el(N);let en,nn;e[2]===Symbol.for("react.memo_cache_sentinel")?(en={order:Sn,filter:Sn,statusCategory:Sn.withDefault("active"),mode:Sn.withDefault("all")},nn={history:"replace"},e[2]=en,e[3]=nn):(en=e[2],nn=e[3]);const[l,u]=nl(en,nn);let A;e[4]!==l||e[5]!==o?(A={queryParams:l,tablePaginationOption:o},e[4]=l,e[5]=o,e[6]=A):A=e[6];let ln;e[7]!==l.statusCategory||e[8]!==A?(ln={[l.statusCategory]:A},e[7]=l.statusCategory,e[8]=A,e[9]=ln):ln=e[9];const xn=He.useRef(ln);let an,tn;e[10]!==l||e[11]!==o?(tn=()=>{xn.current[l.statusCategory]={queryParams:l,tablePaginationOption:o}},an=[l,o],e[10]=l,e[11]=o,e[12]=an,e[13]=tn):(an=e[12],tn=e[13]),He.useEffect(tn,an);let sn;e[14]===Symbol.for("react.memo_cache_sentinel")?(sn=function(i){switch(i){case"all":case void 0:return;case"general":return`(! name ilike ".%")&(usage_mode == "${i}")`;case"pipeline":return'usage_mode == "data"';case"automount":return'name ilike ".%"';default:return`usage_mode == "${i}"`}},e[14]=sn):sn=e[14];const qn=sn(l.mode),[Ye,d]=ll("initial-fetch"),Gn=y.offset,zn=y.first,hn=al([l.statusCategory==="active"||l.statusCategory===void 0?Cn.active:Cn.deleted,l.filter,qn]),bn=l.order||El;let rn;e[15]!==y.first||e[16]!==y.offset||e[17]!==hn||e[18]!==bn?(rn={offset:Gn,first:zn,filter:hn,order:bn,permission:"read_attribute",filterForActiveCount:Cn.active,filterForDeletedCount:Cn.deleted},e[15]=y.first,e[16]=y.offset,e[17]=hn,e[18]=bn,e[19]=rn):rn=e[19];const Nn=rn,Vn=He.useDeferredValue(Nn),on=He.useDeferredValue(Ye);let dn;e[20]===Symbol.for("react.memo_cache_sentinel")?(dn=$n,e[20]=dn):dn=e[20];const vn=on==="initial-fetch"?"store-and-network":"network-only",Ln=on==="initial-fetch"?void 0:on;let un;e[21]!==vn||e[22]!==Ln?(un={fetchPolicy:vn,fetchKey:Ln},e[21]=vn,e[22]=Ln,e[23]=un):un=e[23];const An=tl.useLazyLoadQuery(dn,Vn,un);let C,s;e[24]!==An?({vfolder_nodes:s,...C}=An,e[24]=An,e[25]=C,e[26]=s):(C=e[25],s=e[26]);let K;e[27]!==n?(K=n("data.Folders"),e[27]=n,e[28]=K):K=e[28];const Un=l.statusCategory;let E;e[29]!==u||e[30]!==m?(E=a=>{const i=xn.current[a]||{};u(null),u({...i.queryParams,statusCategory:a}),m(i.tablePaginationOption||{current:1}),c([])},e[29]=u,e[30]=m,e[31]=E):E=e[31];let I;if(e[32]!==C||e[33]!==l.statusCategory||e[34]!==n){let a;e[36]!==C||e[37]!==l.statusCategory?(a=(i,g)=>{var kn;const _n=((kn=C[g])==null?void 0:kn.count)??0;return{key:g,label:i,endContent:_n>0?t.jsx(cl,{label:_n,variant:l.statusCategory===g?"info":"neutral"}):void 0}},e[36]=C,e[37]=l.statusCategory,e[38]=a):a=e[38],I=Je({active:n("data.Active"),deleted:n("data.folders.TrashBin")},a),e[32]=C,e[33]=l.statusCategory,e[34]=n,e[35]=I}else I=e[35];let T;e[39]!==l.statusCategory||e[40]!==E||e[41]!==I?(T=t.jsx(ml,{activeKey:Un,onChange:E,items:I}),e[39]=l.statusCategory,e[40]=E,e[41]=I,e[42]=T):T=e[42];let cn;e[43]===Symbol.for("react.memo_cache_sentinel")?(cn={flexShrink:1},e[43]=cn):cn=e[43];const Qn=l.mode;let M;e[44]!==u||e[45]!==m?(M=a=>{u({mode:a.target.value}),m({current:1}),c([])},e[44]=u,e[45]=m,e[46]=M):M=e[46];let R;e[47]!==p._config.enableModelFolders||e[48]!==p._config.fasttrackEndpoint||e[49]!==n?(R=sl([{label:n("data.All"),value:"all"},{label:n("data.General"),value:"general"},((Pn=p==null?void 0:p._config)==null?void 0:Pn.fasttrackEndpoint)&&{label:n("data.Pipeline"),value:"data"},{label:n("data.AutoMount"),value:"automount"},p._config.enableModelFolders&&{label:n("data.Models"),value:"model"}]),e[47]=p._config.enableModelFolders,e[48]=p._config.fasttrackEndpoint,e[49]=n,e[50]=R):R=e[50];let x;e[51]!==l.mode||e[52]!==M||e[53]!==R?(x=t.jsx(gl,{optionType:"button",value:Qn,onChange:M,options:R}),e[51]=l.mode,e[52]=M,e[53]=R,e[54]=x):x=e[54];let mn;e[55]===Symbol.for("react.memo_cache_sentinel")?(mn={minWidth:320,flex:1},e[55]=mn):mn=e[55];let P;e[56]!==n?(P=n("settings.SearchPlaceholder"),e[56]=n,e[57]=P):P=e[57];let D;e[58]!==n?(D=n("data.SearchByName"),e[58]=n,e[59]=D):D=e[59];let O;e[60]!==n?(O=n("button.Apply"),e[60]=n,e[61]=O):O=e[61];let j;e[62]!==n?(j=n("data.folders.Name"),e[62]=n,e[63]=j):j=e[63];let B;e[64]!==j?(B={key:"name",propertyLabel:j,type:"string"},e[64]=j,e[65]=B):B=e[65];let w;e[66]!==n?(w=n("data.Project"),e[66]=n,e[67]=w):w=e[67];let $;e[68]!==n?($=a=>{const{onAddCondition:i,value:g,isDisabled:_n}=a;return t.jsx(Al,{label:n("data.Project"),isLabelHidden:!0,value:g,isDisabled:_n,onChange:(kn,Wn)=>{var Dn;i(kn,(Dn=fl(Wn??[])[0])==null?void 0:Dn.label)}})},e[68]=n,e[69]=$):$=e[69];let q;e[70]!==w||e[71]!==$?(q={key:"group",propertyLabel:w,type:"string",defaultOperator:"==",renderInput:$},e[70]=w,e[71]=$,e[72]=q):q=e[72];let G;e[73]!==n?(G=n("data.folders.Creator"),e[73]=n,e[74]=G):G=e[74];let z;e[75]!==G?(z={key:"creator",propertyLabel:G,type:"string"},e[75]=G,e[76]=z):z=e[76];let U;e[77]!==n?(U=n("data.folders.Status"),e[77]=n,e[78]=U):U=e[78];let gn;e[79]===Symbol.for("react.memo_cache_sentinel")?(gn=Je(Kl,Il),e[79]=gn):gn=e[79];let Q;e[80]!==U?(Q={key:"status",propertyLabel:U,type:"string",strictSelection:!0,defaultOperator:"==",options:gn},e[80]=U,e[81]=Q):Q=e[81];let H;e[82]!==n?(H=n("data.folders.Location"),e[82]=n,e[83]=H):H=e[83];let W;e[84]!==H?(W={key:"host",propertyLabel:H,type:"string"},e[84]=H,e[85]=W):W=e[85];let Y;e[86]!==n?(Y=n("data.Type"),e[86]=n,e[87]=Y):Y=e[87];let J;e[88]!==n?(J=n("data.User"),e[88]=n,e[89]=J):J=e[89];let X;e[90]!==J?(X={label:J,value:"user"},e[90]=J,e[91]=X):X=e[91];let Z;e[92]!==n?(Z=n("data.Project"),e[92]=n,e[93]=Z):Z=e[93];let ee;e[94]!==Z?(ee={label:Z,value:"group"},e[94]=Z,e[95]=ee):ee=e[95];let ne;e[96]!==X||e[97]!==ee?(ne=[X,ee],e[96]=X,e[97]=ee,e[98]=ne):ne=e[98];let le;e[99]!==Y||e[100]!==ne?(le={key:"ownership_type",propertyLabel:Y,type:"string",strictSelection:!0,defaultOperator:"==",options:ne},e[99]=Y,e[100]=ne,e[101]=le):le=e[101];let ae;e[102]!==n?(ae=n("data.Permission"),e[102]=n,e[103]=ae):ae=e[103];let te;e[104]!==n?(te=n("data.ReadOnly"),e[104]=n,e[105]=te):te=e[105];let se;e[106]!==te?(se={label:te,value:"ro"},e[106]=te,e[107]=se):se=e[107];let re;e[108]!==n?(re=n("data.ReadWrite"),e[108]=n,e[109]=re):re=e[109];let ie;e[110]!==re?(ie={label:re,value:"rw"},e[110]=re,e[111]=ie):ie=e[111];let oe;e[112]!==se||e[113]!==ie?(oe=[se,ie],e[112]=se,e[113]=ie,e[114]=oe):oe=e[114];let de;e[115]!==ae||e[116]!==oe?(de={key:"permission",propertyLabel:ae,type:"string",strictSelection:!0,defaultOperator:"==",options:oe},e[115]=ae,e[116]=oe,e[117]=de):de=e[117];let ue;e[118]!==n?(ue=n("data.folders.CreatedAt"),e[118]=n,e[119]=ue):ue=e[119];let ce;e[120]!==ue?(ce={key:"created_at",propertyLabel:ue,type:"datetime"},e[120]=ue,e[121]=ce):ce=e[121];let me;e[122]!==n?(me=n("credential.LastUsed"),e[122]=n,e[123]=me):me=e[123];let ge;e[124]!==me?(ge={key:"last_used",propertyLabel:me,type:"datetime"},e[124]=me,e[125]=ge):ge=e[125];let fe;e[126]!==n?(fe=n("data.folders.MaxSize"),e[126]=n,e[127]=fe):fe=e[127];let pe;e[128]!==fe?(pe={key:"max_size",propertyLabel:fe,type:"number"},e[128]=fe,e[129]=pe):pe=e[129];let Fe;e[130]!==n?(Fe=n("data.folders.Cloneable"),e[130]=n,e[131]=Fe):Fe=e[131];let ye;e[132]!==Fe?(ye={key:"cloneable",propertyLabel:Fe,type:"boolean"},e[132]=Fe,e[133]=ye):ye=e[133];let _e;e[134]!==B||e[135]!==q||e[136]!==z||e[137]!==Q||e[138]!==W||e[139]!==le||e[140]!==de||e[141]!==ce||e[142]!==ge||e[143]!==pe||e[144]!==ye?(_e=[B,q,z,Q,W,le,de,ce,ge,pe,ye],e[134]=B,e[135]=q,e[136]=z,e[137]=Q,e[138]=W,e[139]=le,e[140]=de,e[141]=ce,e[142]=ge,e[143]=pe,e[144]=ye,e[145]=_e):_e=e[145];const Kn=l.filter??void 0;let ke;e[146]!==u||e[147]!==m?(ke=a=>{u({filter:a??null}),m({current:1}),c([])},e[146]=u,e[147]=m,e[148]=ke):ke=e[148];let Se;e[149]!==P||e[150]!==D||e[151]!==O||e[152]!==_e||e[153]!==Kn||e[154]!==ke?(Se=t.jsx(pl,{"data-testid":"vfolder-filter",style:mn,label:P,placeholder:D,applyLabel:O,contentSearchFieldKey:"name",filterProperties:_e,value:Kn,onChange:ke}),e[149]=P,e[150]=D,e[151]=O,e[152]=_e,e[153]=Kn,e[154]=ke,e[155]=Se):Se=e[155];let Ce;e[156]!==x||e[157]!==Se?(Ce=t.jsxs(Rn,{gap:3,align:"start",style:cn,wrap:"wrap",children:[x,Se]}),e[156]=x,e[157]=Se,e[158]=Ce):Ce=e[158];let he;e[159]!==l.statusCategory||e[160]!==r||e[161]!==n||e[162]!==F?(he=r.length>0&&l.statusCategory==="active"&&t.jsxs(t.Fragment,{children:[t.jsx(On,{count:r.length,onClearSelection:()=>c([])}),t.jsx(rl,{vfolderFrgmt:r,label:n("data.folders.MoveToTrash"),onClick:()=>{F()}})]}),e[159]=l.statusCategory,e[160]=r,e[161]=n,e[162]=F,e[163]=he):he=e[163];let be;e[164]!==l.statusCategory||e[165]!==r.length||e[166]!==n||e[167]!==_?(be=r.length>0&&l.statusCategory==="deleted"&&t.jsxs(t.Fragment,{children:[t.jsx(On,{count:r.length,onClearSelection:()=>c([])}),t.jsx(il,{content:n("data.folders.Restore"),children:t.jsx(ol,{label:n("data.folders.Restore"),icon:t.jsx(dl,{}),onClick:()=>{_()}})})]}),e[164]=l.statusCategory,e[165]=r.length,e[166]=n,e[167]=_,e[168]=be):be=e[168];const En=Vn!==Nn||on!==Ye;let Ne;e[169]!==d?(Ne=a=>{d(a)},e[169]=d,e[170]=Ne):Ne=e[170];let Ve;e[171]!==Ye||e[172]!==En||e[173]!==Ne?(Ve=t.jsx(Fl,{settingId:"admin-vfolder-list",loading:En,value:Ye,onChange:Ne}),e[171]=Ye,e[172]=En,e[173]=Ne,e[174]=Ve):Ve=e[174];let fn;e[175]===Symbol.for("react.memo_cache_sentinel")?(fn=t.jsx(yl,{}),e[175]=fn):fn=e[175];let ve;e[176]!==n?(ve=n("data.CreateFolder"),e[176]=n,e[177]=ve):ve=e[177];let Le;e[178]!==k?(Le=()=>{k()},e[178]=k,e[179]=Le):Le=e[179];let Ae;e[180]!==ve||e[181]!==Le?(Ae=t.jsx(_l,{variant:"primary",icon:fn,label:ve,onClick:Le}),e[180]=ve,e[181]=Le,e[182]=Ae):Ae=e[182];let Ke;e[183]!==he||e[184]!==be||e[185]!==Ve||e[186]!==Ae?(Ke=t.jsxs(Rn,{gap:2,children:[he,be,Ve,Ae]}),e[183]=he,e[184]=be,e[185]=Ve,e[186]=Ae,e[187]=Ke):Ke=e[187];let Ee;e[188]!==Ce||e[189]!==Ke?(Ee=t.jsxs(Rn,{justify:"between",wrap:"wrap",gap:3,children:[Ce,Ke]}),e[188]=Ce,e[189]=Ke,e[190]=Ee):Ee=e[190];let pn;e[191]===Symbol.for("react.memo_cache_sentinel")?(pn=t.jsx(kl,{rows:4}),e[191]=pn):pn=e[191];const Hn=l.order,In=Vn!==Nn;let Ie;e[192]!==n?(Ie=n("data.folders.CannotDeployFromAdminMenu"),e[192]=n,e[193]=Ie):Ie=e[193];let Te;e[194]!==(s==null?void 0:s.edges)?(Te=jn(Je(s==null?void 0:s.edges,"node")),e[194]=s==null?void 0:s.edges,e[195]=Te):Te=e[195];let Me;if(e[196]!==r||e[197]!==(s==null?void 0:s.edges)){let a;e[199]!==(s==null?void 0:s.edges)?(a=g=>{Sl(g,jn(Je(s==null?void 0:s.edges,"node")),c)},e[199]=s==null?void 0:s.edges,e[200]=a):a=e[200];let i;e[201]!==r?(i=Je(r,Tl),e[201]=r,e[202]=i):i=e[202],Me={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(g){return{disabled:Cl(g.status)&&g.status!=="delete-pending"}},onChange:a,selectedRowKeys:i},e[196]=r,e[197]=s==null?void 0:s.edges,e[198]=Me}else Me=e[198];const Tn=(s==null?void 0:s.count)??0;let Re;e[203]!==m||e[204]!==Tn||e[205]!==o.current||e[206]!==o.pageSize?(Re={pageSize:o.pageSize,current:o.current,total:Tn,onChange(a,i){Bn(a)&&Bn(i)&&m({current:a,pageSize:i})}},e[203]=m,e[204]=Tn,e[205]=o.current,e[206]=o.pageSize,e[207]=Re):Re=e[207];let xe;e[208]!==u?(xe=a=>{u({order:a??null})},e[208]=u,e[209]=xe):xe=e[209];let Pe;e[210]!==d?(Pe=a=>{c(i=>hl(i,g=>g.id!==a)),d()},e[210]=d,e[211]=Pe):Pe=e[211];let Fn;e[212]===Symbol.for("react.memo_cache_sentinel")?(Fn={creator:{hidden:!1},cur_size:{hidden:!1},max_size:{hidden:!1},created_at:{hidden:!1}},e[212]=Fn):Fn=e[212];let De;e[213]!==V||e[214]!==v?(De={columnOverrides:V,defaultColumnOverrides:Fn,onColumnOverridesChange:v},e[213]=V,e[214]=v,e[215]=De):De=e[215];let Oe;e[216]!==l.order||e[217]!==In||e[218]!==Ie||e[219]!==Te||e[220]!==Me||e[221]!==Re||e[222]!==xe||e[223]!==Pe||e[224]!==De?(Oe=t.jsx(He.Suspense,{fallback:pn,children:t.jsx(bl,{order:Hn,loading:In,project:null,noDeployTooltip:Ie,vfoldersFrgmt:Te,rowSelection:Me,pagination:Re,onChangeOrder:xe,onRemoveRow:Pe,tableSettings:De})}),e[216]=l.order,e[217]=In,e[218]=Ie,e[219]=Te,e[220]=Me,e[221]=Re,e[222]=xe,e[223]=Pe,e[224]=De,e[225]=Oe):Oe=e[225];let je;e[226]!==Ee||e[227]!==Oe?(je=t.jsxs(wn,{align:"stretch",gap:3,children:[Ee,Oe]}),e[226]=Ee,e[227]=Oe,e[228]=je):je=e[228];let Be;e[229]!==K||e[230]!==T||e[231]!==je?(Be=t.jsxs(Nl,{title:K,children:[T,je]}),e[229]=K,e[230]=T,e[231]=je,e[232]=Be):Be=e[232];let we;e[233]!==F||e[234]!==d?(we=a=>{a&&(d(),c([])),F()},e[233]=F,e[234]=d,e[235]=we):we=e[235];let $e;e[236]!==S||e[237]!==r||e[238]!==we?($e=t.jsx(Vl,{vfolderFrgmts:r,open:S,onRequestClose:we}),e[236]=S,e[237]=r,e[238]=we,e[239]=$e):$e=e[239];let qe;e[240]!==_||e[241]!==d?(qe=a=>{a&&(d(),c([])),_()},e[240]=_,e[241]=d,e[242]=qe):qe=e[242];let Ge;e[243]!==b||e[244]!==r||e[245]!==qe?(Ge=t.jsx(vl,{vfolderFrgmts:r,open:b,onRequestClose:qe}),e[243]=b,e[244]=r,e[245]=qe,e[246]=Ge):Ge=e[246];let ze;e[247]!==n?(ze=n("data.folders.AdminDataPageAlert"),e[247]=n,e[248]=ze):ze=e[248];let Ue;e[249]!==k||e[250]!==d?(Ue=a=>{k(),a&&d()},e[249]=k,e[250]=d,e[251]=Ue):Ue=e[251];let Qe;e[252]!==L||e[253]!==ze||e[254]!==Ue?(Qe=t.jsx(Ll,{open:L,project:null,folderType:"project",alertMessage:ze,onRequestClose:Ue}),e[252]=L,e[253]=ze,e[254]=Ue,e[255]=Qe):Qe=e[255];let yn;return e[256]!==f||e[257]!==Be||e[258]!==$e||e[259]!==Ge||e[260]!==Qe?(yn=t.jsx(ul,{children:t.jsxs(wn,{align:"stretch",gap:5,...f,children:[Be,$e,Ge,Qe]})}),e[256]=f,e[257]=Be,e[258]=$e,e[259]=Ge,e[260]=Qe,e[261]=yn):yn=e[261],yn};function Il(f){return{label:f,value:f}}function Tl(f){return f.id}export{Pl as default};
//# sourceMappingURL=AdminVFolderNodeListPage-D5SQbH_0.js.map
