import{i as Wn,u as Yn,a as Jn,a8 as Xn,l as We,bF as Tn,bG as Zn,ag as kn,af as el,cn as nl,dL as ll,r as tl,am as Ye,ai as al,j as r,cb as Pn,hC as rl,s as sl,N as il,b0 as ol,aT as On,bN as jn,av as dl,at as Bn,g as ul,ab as cl,de as ml,cU as gl,b1 as fl,cI as Mn,dx as pl,P as Fl,au as yl,ej as _l,hD as kl,al as Sl,hE as Cl,d as bl,hF as hl,hG as Nl,U as Vl}from"./index-Dd8bt51s.js";import{B as vl}from"./BAIAdminProjectSelect-DrMbp3Kk.js";const wn=(function(){var f={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"filterForActiveCount"},n={defaultValue:null,kind:"LocalArgument",name:"filterForDeletedCount"},p={defaultValue:null,kind:"LocalArgument",name:"first"},V={defaultValue:null,kind:"LocalArgument",name:"offset"},v={defaultValue:null,kind:"LocalArgument",name:"order"},b={defaultValue:null,kind:"LocalArgument",name:"permission"},s={kind:"Variable",name:"permission",variableName:"permission"},c=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"},s],S={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},Je={alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},F={alias:null,args:null,kind:"ScalarField",name:"permissions",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},Xe={kind:"Literal",name:"first",value:0},_={kind:"Literal",name:"offset",value:0},L=[h],Ze={alias:"active",args:[{kind:"Variable",name:"filter",variableName:"filterForActiveCount"},Xe,_,s],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:L,storageKey:null},k={alias:"deleted",args:[{kind:"Variable",name:"filter",variableName:"filterForDeletedCount"},Xe,_,s],concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:L,storageKey:null},N={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"__typename",storageKey:null};return{fragment:{argumentDefinitions:[f,e,n,p,V,v,b],kind:"Fragment",metadata:null,name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:c,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{kind:"RequiredField",field:{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[{kind:"RequiredField",field:S,action:"THROW"},Je,F,{args:null,kind:"FragmentSpread",name:"VFolderNodesFragment"},{args:null,kind:"FragmentSpread",name:"DeleteVFolderModalFragment"},{args:null,kind:"FragmentSpread",name:"EditableVFolderNameFragment"},{args:null,kind:"FragmentSpread",name:"RestoreVFolderModalFragment"},{args:null,kind:"FragmentSpread",name:"VFolderNodeIdenticonFragment"},{args:null,kind:"FragmentSpread",name:"SharedFolderPermissionInfoModalFragment"},{args:null,kind:"FragmentSpread",name:"BAIVFolderDeleteButtonFragment"}],storageKey:null},action:"THROW"}],storageKey:null},action:"THROW"},h],storageKey:null},Ze,k],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[V,p,f,v,b,e,n],kind:"Operation",name:"AdminVFolderNodeListPageQuery",selections:[{alias:null,args:c,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[S,Je,F,N,y,{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownership_type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creator",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"last_used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"num_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cur_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null},F,{kind:"InlineFragment",selections:[{kind:"InlineFragment",selections:[o,{alias:null,args:null,kind:"ScalarField",name:"status_info",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status_data",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"access_key",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"service_ports",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"commit_status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"scaling_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project_id",storageKey:null},{alias:null,args:null,concreteType:"KernelConnection",kind:"LinkedField",name:"kernel_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelNode",kind:"LinkedField",name:"node",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"container_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"agent_id",storageKey:null},S,N,{alias:null,args:null,kind:"ScalarField",name:"cluster_idx",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_role",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_hostname",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"vfolder_mounts",storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderConnection",kind:"LinkedField",name:"vfolder_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"node",plural:!1,selections:[y,S],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"queue_position",storageKey:null}],type:"ComputeSessionNode",abstractKey:null},{kind:"InlineFragment",selections:[o,{alias:null,args:null,concreteType:"VFolderMetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[y],storageKey:null}],type:"VFolder",abstractKey:null},{kind:"InlineFragment",selections:[o],type:"VirtualFolderNode",abstractKey:null}],type:"Node",abstractKey:"__isNode"}],storageKey:null}],storageKey:null},h],storageKey:null},Ze,k]},params:{cacheID:"8f4996dcf33e2e3b3f07b55d1452f63f",id:null,metadata:{},name:"AdminVFolderNodeListPageQuery",operationKind:"query",text:`query AdminVFolderNodeListPageQuery(
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
`}}})();wn.hash="61335271ca378f8ff80cff73517798c7";const Ll=["READY","PERFORMING","CLONING","MOUNTED","ERROR","DELETE_PENDING","DELETE_ONGOING","DELETE_COMPLETE","DELETE_ERROR"],Al="-created_at",Sn={active:'status != "DELETE_PENDING" & status != "DELETE_ONGOING" & status != "DELETE_ERROR" & status != "DELETE_COMPLETE"',deleted:'status in ["DELETE_PENDING", "DELETE_ONGOING", "DELETE_ERROR", "DELETE_COMPLETE"]'},Rl=f=>{"use memo";var xn;const e=Wn.c(261),{t:n}=Yn(),p=Jn(),[V,v]=Xn("table_column_overrides.AdminVFolderNodeListPage");let b;e[0]===Symbol.for("react.memo_cache_sentinel")?(b=[],e[0]=b):b=e[0];const[s,c]=We.useState(b),[S,Je]=Tn(!1),{toggle:F}=Je,[h,Xe]=Tn(!1),{toggle:_}=Xe,[L,Ze]=Tn(!1),{toggle:k}=Ze;let N;e[1]===Symbol.for("react.memo_cache_sentinel")?(N={current:1,pageSize:10},e[1]=N):N=e[1];const{baiPaginationOption:y,tablePaginationOption:o,setTablePaginationOption:m}=Zn(N);let en,nn;e[2]===Symbol.for("react.memo_cache_sentinel")?(en={order:kn,filter:kn,statusCategory:kn.withDefault("active"),mode:kn.withDefault("all")},nn={history:"replace"},e[2]=en,e[3]=nn):(en=e[2],nn=e[3]);const[l,u]=el(en,nn);let A;e[4]!==l||e[5]!==o?(A={queryParams:l,tablePaginationOption:o},e[4]=l,e[5]=o,e[6]=A):A=e[6];let ln;e[7]!==l.statusCategory||e[8]!==A?(ln={[l.statusCategory]:A},e[7]=l.statusCategory,e[8]=A,e[9]=ln):ln=e[9];const Rn=We.useRef(ln);let tn,an;e[10]!==l||e[11]!==o?(an=()=>{Rn.current[l.statusCategory]={queryParams:l,tablePaginationOption:o}},tn=[l,o],e[10]=l,e[11]=o,e[12]=tn,e[13]=an):(tn=e[12],an=e[13]),We.useEffect(an,tn);let rn;e[14]===Symbol.for("react.memo_cache_sentinel")?(rn=function(i){switch(i){case"all":case void 0:return;case"general":return`(! name ilike ".%")&(usage_mode == "${i}")`;case"pipeline":return'usage_mode == "data"';case"automount":return'name ilike ".%"';default:return`usage_mode == "${i}"`}},e[14]=rn):rn=e[14];const $n=rn(l.mode),[He,d]=nl("initial-fetch"),qn=y.offset,Gn=y.first,Cn=ll([l.statusCategory==="active"||l.statusCategory===void 0?Sn.active:Sn.deleted,l.filter,$n]),bn=l.order||Al;let sn;e[15]!==y.first||e[16]!==y.offset||e[17]!==Cn||e[18]!==bn?(sn={offset:qn,first:Gn,filter:Cn,order:bn,permission:"read_attribute",filterForActiveCount:Sn.active,filterForDeletedCount:Sn.deleted},e[15]=y.first,e[16]=y.offset,e[17]=Cn,e[18]=bn,e[19]=sn):sn=e[19];const hn=sn,Nn=We.useDeferredValue(hn),on=We.useDeferredValue(He);let dn;e[20]===Symbol.for("react.memo_cache_sentinel")?(dn=wn,e[20]=dn):dn=e[20];const Vn=on==="initial-fetch"?"store-and-network":"network-only",vn=on==="initial-fetch"?void 0:on;let un;e[21]!==Vn||e[22]!==vn?(un={fetchPolicy:Vn,fetchKey:vn},e[21]=Vn,e[22]=vn,e[23]=un):un=e[23];const Ln=tl.useLazyLoadQuery(dn,Nn,un);let C,a;e[24]!==Ln?({vfolder_nodes:a,...C}=Ln,e[24]=Ln,e[25]=C,e[26]=a):(C=e[25],a=e[26]);let E;e[27]!==n?(E=n("data.Folders"),e[27]=n,e[28]=E):E=e[28];const Un=l.statusCategory;let K;e[29]!==u||e[30]!==m?(K=t=>{const i=Rn.current[t]||{};u(null),u({...i.queryParams,statusCategory:t}),m(i.tablePaginationOption||{current:1}),c([])},e[29]=u,e[30]=m,e[31]=K):K=e[31];let I;if(e[32]!==C||e[33]!==l.statusCategory||e[34]!==n){let t;e[36]!==C||e[37]!==l.statusCategory?(t=(i,g)=>{var _n;const yn=((_n=C[g])==null?void 0:_n.count)??0;return{key:g,label:i,endContent:yn>0?r.jsx(ul,{label:yn,variant:l.statusCategory===g?"info":"neutral"}):void 0}},e[36]=C,e[37]=l.statusCategory,e[38]=t):t=e[38],I=Ye({active:n("data.Active"),deleted:n("data.folders.TrashBin")},t),e[32]=C,e[33]=l.statusCategory,e[34]=n,e[35]=I}else I=e[35];let T;e[39]!==l.statusCategory||e[40]!==K||e[41]!==I?(T=r.jsx(cl,{activeKey:Un,onChange:K,items:I}),e[39]=l.statusCategory,e[40]=K,e[41]=I,e[42]=T):T=e[42];let cn;e[43]===Symbol.for("react.memo_cache_sentinel")?(cn={flexShrink:1},e[43]=cn):cn=e[43];const zn=l.mode;let M;e[44]!==u||e[45]!==m?(M=t=>{u({mode:t.target.value}),m({current:1}),c([])},e[44]=u,e[45]=m,e[46]=M):M=e[46];let R;e[47]!==p._config.enableModelFolders||e[48]!==p._config.fasttrackEndpoint||e[49]!==n?(R=al([{label:n("data.All"),value:"all"},{label:n("data.General"),value:"general"},((xn=p==null?void 0:p._config)==null?void 0:xn.fasttrackEndpoint)&&{label:n("data.Pipeline"),value:"data"},{label:n("data.AutoMount"),value:"automount"},p._config.enableModelFolders&&{label:n("data.Models"),value:"model"}]),e[47]=p._config.enableModelFolders,e[48]=p._config.fasttrackEndpoint,e[49]=n,e[50]=R):R=e[50];let x;e[51]!==l.mode||e[52]!==M||e[53]!==R?(x=r.jsx(ml,{optionType:"button",value:zn,onChange:M,options:R}),e[51]=l.mode,e[52]=M,e[53]=R,e[54]=x):x=e[54];let mn;e[55]===Symbol.for("react.memo_cache_sentinel")?(mn={minWidth:320,flex:1},e[55]=mn):mn=e[55];let D;e[56]!==n?(D=n("settings.SearchPlaceholder"),e[56]=n,e[57]=D):D=e[57];let P;e[58]!==n?(P=n("data.SearchByName"),e[58]=n,e[59]=P):P=e[59];let O;e[60]!==n?(O=n("button.Apply"),e[60]=n,e[61]=O):O=e[61];let j;e[62]!==n?(j=n("data.folders.Name"),e[62]=n,e[63]=j):j=e[63];let B;e[64]!==j?(B={key:"name",propertyLabel:j,type:"string"},e[64]=j,e[65]=B):B=e[65];let w;e[66]!==n?(w=n("data.Project"),e[66]=n,e[67]=w):w=e[67];let $;e[68]!==n?($=t=>{const{onAddCondition:i,value:g,isDisabled:yn}=t;return r.jsx(vl,{label:n("data.Project"),isLabelHidden:!0,value:g,isDisabled:yn,onChange:(_n,Hn)=>{var Dn;i(_n,(Dn=gl(Hn??[])[0])==null?void 0:Dn.label)}})},e[68]=n,e[69]=$):$=e[69];let q;e[70]!==w||e[71]!==$?(q={key:"group",propertyLabel:w,type:"string",defaultOperator:"==",renderInput:$},e[70]=w,e[71]=$,e[72]=q):q=e[72];let G;e[73]!==n?(G=n("data.folders.Creator"),e[73]=n,e[74]=G):G=e[74];let U;e[75]!==G?(U={key:"creator",propertyLabel:G,type:"string"},e[75]=G,e[76]=U):U=e[76];let z;e[77]!==n?(z=n("data.folders.Status"),e[77]=n,e[78]=z):z=e[78];let gn;e[79]===Symbol.for("react.memo_cache_sentinel")?(gn=Ye(Ll,El),e[79]=gn):gn=e[79];let Q;e[80]!==z?(Q={key:"status",propertyLabel:z,type:"string",strictSelection:!0,defaultOperator:"==",options:gn},e[80]=z,e[81]=Q):Q=e[81];let H;e[82]!==n?(H=n("data.folders.Location"),e[82]=n,e[83]=H):H=e[83];let W;e[84]!==H?(W={key:"host",propertyLabel:H,type:"string"},e[84]=H,e[85]=W):W=e[85];let Y;e[86]!==n?(Y=n("data.Type"),e[86]=n,e[87]=Y):Y=e[87];let J;e[88]!==n?(J=n("data.User"),e[88]=n,e[89]=J):J=e[89];let X;e[90]!==J?(X={label:J,value:"user"},e[90]=J,e[91]=X):X=e[91];let Z;e[92]!==n?(Z=n("data.Project"),e[92]=n,e[93]=Z):Z=e[93];let ee;e[94]!==Z?(ee={label:Z,value:"group"},e[94]=Z,e[95]=ee):ee=e[95];let ne;e[96]!==X||e[97]!==ee?(ne=[X,ee],e[96]=X,e[97]=ee,e[98]=ne):ne=e[98];let le;e[99]!==Y||e[100]!==ne?(le={key:"ownership_type",propertyLabel:Y,type:"string",strictSelection:!0,defaultOperator:"==",options:ne},e[99]=Y,e[100]=ne,e[101]=le):le=e[101];let te;e[102]!==n?(te=n("data.Permission"),e[102]=n,e[103]=te):te=e[103];let ae;e[104]!==n?(ae=n("data.ReadOnly"),e[104]=n,e[105]=ae):ae=e[105];let re;e[106]!==ae?(re={label:ae,value:"ro"},e[106]=ae,e[107]=re):re=e[107];let se;e[108]!==n?(se=n("data.ReadWrite"),e[108]=n,e[109]=se):se=e[109];let ie;e[110]!==se?(ie={label:se,value:"rw"},e[110]=se,e[111]=ie):ie=e[111];let oe;e[112]!==re||e[113]!==ie?(oe=[re,ie],e[112]=re,e[113]=ie,e[114]=oe):oe=e[114];let de;e[115]!==te||e[116]!==oe?(de={key:"permission",propertyLabel:te,type:"string",strictSelection:!0,defaultOperator:"==",options:oe},e[115]=te,e[116]=oe,e[117]=de):de=e[117];let ue;e[118]!==n?(ue=n("data.folders.CreatedAt"),e[118]=n,e[119]=ue):ue=e[119];let ce;e[120]!==ue?(ce={key:"created_at",propertyLabel:ue,type:"datetime"},e[120]=ue,e[121]=ce):ce=e[121];let me;e[122]!==n?(me=n("credential.LastUsed"),e[122]=n,e[123]=me):me=e[123];let ge;e[124]!==me?(ge={key:"last_used",propertyLabel:me,type:"datetime"},e[124]=me,e[125]=ge):ge=e[125];let fe;e[126]!==n?(fe=n("data.folders.MaxSize"),e[126]=n,e[127]=fe):fe=e[127];let pe;e[128]!==fe?(pe={key:"max_size",propertyLabel:fe,type:"number"},e[128]=fe,e[129]=pe):pe=e[129];let Fe;e[130]!==n?(Fe=n("data.folders.Cloneable"),e[130]=n,e[131]=Fe):Fe=e[131];let ye;e[132]!==Fe?(ye={key:"cloneable",propertyLabel:Fe,type:"boolean"},e[132]=Fe,e[133]=ye):ye=e[133];let _e;e[134]!==B||e[135]!==q||e[136]!==U||e[137]!==Q||e[138]!==W||e[139]!==le||e[140]!==de||e[141]!==ce||e[142]!==ge||e[143]!==pe||e[144]!==ye?(_e=[B,q,U,Q,W,le,de,ce,ge,pe,ye],e[134]=B,e[135]=q,e[136]=U,e[137]=Q,e[138]=W,e[139]=le,e[140]=de,e[141]=ce,e[142]=ge,e[143]=pe,e[144]=ye,e[145]=_e):_e=e[145];const An=l.filter??void 0;let ke;e[146]!==u||e[147]!==m?(ke=t=>{u({filter:t??null}),m({current:1}),c([])},e[146]=u,e[147]=m,e[148]=ke):ke=e[148];let Se;e[149]!==D||e[150]!==P||e[151]!==O||e[152]!==_e||e[153]!==An||e[154]!==ke?(Se=r.jsx(fl,{"data-testid":"vfolder-filter",style:mn,label:D,placeholder:P,applyLabel:O,contentSearchFieldKey:"name",filterProperties:_e,value:An,onChange:ke}),e[149]=D,e[150]=P,e[151]=O,e[152]=_e,e[153]=An,e[154]=ke,e[155]=Se):Se=e[155];let Ce;e[156]!==x||e[157]!==Se?(Ce=r.jsxs(Mn,{gap:3,align:"start",style:cn,wrap:"wrap",children:[x,Se]}),e[156]=x,e[157]=Se,e[158]=Ce):Ce=e[158];let be;e[159]!==l.statusCategory||e[160]!==s||e[161]!==n||e[162]!==F?(be=s.length>0&&l.statusCategory==="active"&&r.jsxs(r.Fragment,{children:[r.jsx(Pn,{count:s.length,onClearSelection:()=>c([])}),r.jsx(rl,{vfolderFrgmt:s,label:n("data.folders.MoveToTrash"),onClick:()=>{F()}})]}),e[159]=l.statusCategory,e[160]=s,e[161]=n,e[162]=F,e[163]=be):be=e[163];let he;e[164]!==l.statusCategory||e[165]!==s.length||e[166]!==n||e[167]!==_?(he=s.length>0&&l.statusCategory==="deleted"&&r.jsxs(r.Fragment,{children:[r.jsx(Pn,{count:s.length,onClearSelection:()=>c([])}),r.jsx(sl,{content:n("data.folders.Restore"),children:r.jsx(il,{label:n("data.folders.Restore"),icon:r.jsx(ol,{}),onClick:()=>{_()}})})]}),e[164]=l.statusCategory,e[165]=s.length,e[166]=n,e[167]=_,e[168]=he):he=e[168];const En=Nn!==hn||on!==He;let Ne;e[169]!==d?(Ne=t=>{d(t)},e[169]=d,e[170]=Ne):Ne=e[170];let Ve;e[171]!==He||e[172]!==En||e[173]!==Ne?(Ve=r.jsx(pl,{settingId:"admin-vfolder-list",loading:En,value:He,onChange:Ne}),e[171]=He,e[172]=En,e[173]=Ne,e[174]=Ve):Ve=e[174];let fn;e[175]===Symbol.for("react.memo_cache_sentinel")?(fn=r.jsx(Fl,{}),e[175]=fn):fn=e[175];let ve;e[176]!==n?(ve=n("data.CreateFolder"),e[176]=n,e[177]=ve):ve=e[177];let Le;e[178]!==k?(Le=()=>{k()},e[178]=k,e[179]=Le):Le=e[179];let Ae;e[180]!==ve||e[181]!==Le?(Ae=r.jsx(yl,{variant:"primary",icon:fn,label:ve,onClick:Le}),e[180]=ve,e[181]=Le,e[182]=Ae):Ae=e[182];let Ee;e[183]!==be||e[184]!==he||e[185]!==Ve||e[186]!==Ae?(Ee=r.jsxs(Mn,{gap:2,children:[be,he,Ve,Ae]}),e[183]=be,e[184]=he,e[185]=Ve,e[186]=Ae,e[187]=Ee):Ee=e[187];let Ke;e[188]!==Ce||e[189]!==Ee?(Ke=r.jsxs(Mn,{justify:"between",wrap:"wrap",gap:3,children:[Ce,Ee]}),e[188]=Ce,e[189]=Ee,e[190]=Ke):Ke=e[190];const Qn=l.order,Kn=Nn!==hn;let Ie;e[191]!==n?(Ie=n("data.folders.CannotDeployFromAdminMenu"),e[191]=n,e[192]=Ie):Ie=e[192];let Te;e[193]!==(a==null?void 0:a.edges)?(Te=On(Ye(a==null?void 0:a.edges,"node")),e[193]=a==null?void 0:a.edges,e[194]=Te):Te=e[194];let Me;if(e[195]!==s||e[196]!==(a==null?void 0:a.edges)){let t;e[198]!==(a==null?void 0:a.edges)?(t=g=>{_l(g,On(Ye(a==null?void 0:a.edges,"node")),c)},e[198]=a==null?void 0:a.edges,e[199]=t):t=e[199];let i;e[200]!==s?(i=Ye(s,Kl),e[200]=s,e[201]=i):i=e[201],Me={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(g){return{disabled:kl(g.status)&&g.status!=="delete-pending"}},onChange:t,selectedRowKeys:i},e[195]=s,e[196]=a==null?void 0:a.edges,e[197]=Me}else Me=e[197];const In=(a==null?void 0:a.count)??0;let Re;e[202]!==m||e[203]!==In||e[204]!==o.current||e[205]!==o.pageSize?(Re={pageSize:o.pageSize,current:o.current,total:In,onChange(t,i){jn(t)&&jn(i)&&m({current:t,pageSize:i})}},e[202]=m,e[203]=In,e[204]=o.current,e[205]=o.pageSize,e[206]=Re):Re=e[206];let xe;e[207]!==u?(xe=t=>{u({order:t??null})},e[207]=u,e[208]=xe):xe=e[208];let De;e[209]!==d?(De=t=>{c(i=>Sl(i,g=>g.id!==t)),d()},e[209]=d,e[210]=De):De=e[210];let pn;e[211]===Symbol.for("react.memo_cache_sentinel")?(pn={creator:{hidden:!1},cur_size:{hidden:!1},max_size:{hidden:!1},created_at:{hidden:!1}},e[211]=pn):pn=e[211];let Pe;e[212]!==V||e[213]!==v?(Pe={columnOverrides:V,defaultColumnOverrides:pn,onColumnOverridesChange:v},e[212]=V,e[213]=v,e[214]=Pe):Pe=e[214];let Oe;e[215]!==l.order||e[216]!==Kn||e[217]!==Ie||e[218]!==Te||e[219]!==Me||e[220]!==Re||e[221]!==xe||e[222]!==De||e[223]!==Pe?(Oe=r.jsx(Cl,{order:Qn,loading:Kn,project:null,noDeployTooltip:Ie,vfoldersFrgmt:Te,rowSelection:Me,pagination:Re,onChangeOrder:xe,onRemoveRow:De,tableSettings:Pe}),e[215]=l.order,e[216]=Kn,e[217]=Ie,e[218]=Te,e[219]=Me,e[220]=Re,e[221]=xe,e[222]=De,e[223]=Pe,e[224]=Oe):Oe=e[224];let je;e[225]!==Ke||e[226]!==Oe?(je=r.jsxs(Bn,{align:"stretch",gap:3,children:[Ke,Oe]}),e[225]=Ke,e[226]=Oe,e[227]=je):je=e[227];let Be;e[228]!==E||e[229]!==T||e[230]!==je?(Be=r.jsxs(bl,{title:E,children:[T,je]}),e[228]=E,e[229]=T,e[230]=je,e[231]=Be):Be=e[231];let we;e[232]!==F||e[233]!==d?(we=t=>{t&&(d(),c([])),F()},e[232]=F,e[233]=d,e[234]=we):we=e[234];let $e;e[235]!==S||e[236]!==s||e[237]!==we?($e=r.jsx(hl,{vfolderFrgmts:s,open:S,onRequestClose:we}),e[235]=S,e[236]=s,e[237]=we,e[238]=$e):$e=e[238];let qe;e[239]!==_||e[240]!==d?(qe=t=>{t&&(d(),c([])),_()},e[239]=_,e[240]=d,e[241]=qe):qe=e[241];let Ge;e[242]!==h||e[243]!==s||e[244]!==qe?(Ge=r.jsx(Nl,{vfolderFrgmts:s,open:h,onRequestClose:qe}),e[242]=h,e[243]=s,e[244]=qe,e[245]=Ge):Ge=e[245];let Ue;e[246]!==n?(Ue=n("data.folders.AdminDataPageAlert"),e[246]=n,e[247]=Ue):Ue=e[247];let ze;e[248]!==k||e[249]!==d?(ze=t=>{k(),t&&d()},e[248]=k,e[249]=d,e[250]=ze):ze=e[250];let Qe;e[251]!==L||e[252]!==Ue||e[253]!==ze?(Qe=r.jsx(Vl,{open:L,project:null,folderType:"project",alertMessage:Ue,onRequestClose:ze}),e[251]=L,e[252]=Ue,e[253]=ze,e[254]=Qe):Qe=e[254];let Fn;return e[255]!==f||e[256]!==$e||e[257]!==Ge||e[258]!==Qe||e[259]!==Be?(Fn=r.jsx(dl,{children:r.jsxs(Bn,{align:"stretch",gap:5,...f,children:[Be,$e,Ge,Qe]})}),e[255]=f,e[256]=$e,e[257]=Ge,e[258]=Qe,e[259]=Be,e[260]=Fn):Fn=e[260],Fn};function El(f){return{label:f,value:f}}function Kl(f){return f.id}export{Rl as default};
//# sourceMappingURL=AdminVFolderNodeListPage--EMTGSkT.js.map
