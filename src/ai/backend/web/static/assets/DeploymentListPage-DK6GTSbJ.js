import{h as ue,u as ce,j as a,r as z,ax as fe,B as me,bJ as ke,p as De,aW as Ce,bs as be,bt as de,cW as Fe,bu as Se,a2 as he,as as Ke,i as Le,av as ve,aL as _e,aB as Te,b2 as Ie}from"./index-Cd_TYquF.js";import{t as Re,a as Me,D as Ne}from"./DeploymentList-Dy91Wy_s.js";import{D as xe}from"./DeploymentSettingModal-C8ed-TNP.js";import"./BAIGraphQLPropertyFilter-ChBo7W0r.js";const ye=function(){var e={defaultValue:null,kind:"LocalArgument",name:"filter"},i={defaultValue:null,kind:"LocalArgument",name:"limit"},n={defaultValue:null,kind:"LocalArgument",name:"offset"},o={defaultValue:null,kind:"LocalArgument",name:"orderBy"},r=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"}],s={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},M=[s];return{fragment:{argumentDefinitions:[e,i,n,o],kind:"Fragment",metadata:null,name:"DeploymentListPageQuery",selections:[{alias:null,args:r,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"DeploymentList_modelDeploymentConnection"}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,o,i,n],kind:"Operation",name:"DeploymentListPageQuery",selections:[{alias:null,args:r,concreteType:"ModelDeploymentConnection",kind:"LinkedField",name:"myDeployments",plural:!1,selections:[s,{alias:null,args:null,concreteType:"ModelDeploymentEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ModelDeployment",kind:"LinkedField",name:"node",plural:!1,selections:[m,{alias:null,args:null,concreteType:"ModelDeploymentMetadata",kind:"LinkedField",name:"metadata",plural:!1,selections:[y,{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"domainName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"projectId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tags",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ModelDeploymentNetworkAccess",kind:"LinkedField",name:"networkAccess",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"endpointUrl",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"openToPublic",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ReplicaState",kind:"LinkedField",name:"replicaState",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"desiredReplicaCount",storageKey:null}],storageKey:null},{alias:"totalReplicas",args:null,concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:M,storageKey:null},{alias:"runningReplicas",args:[{kind:"Literal",name:"filter",value:{status:{equals:"RUNNING"}}}],concreteType:"ModelReplicaConnection",kind:"LinkedField",name:"replicas",plural:!1,selections:M,storageKey:'replicas(filter:{"status":{"equals":"RUNNING"}})'},{alias:null,args:null,concreteType:"ModelRevision",kind:"LinkedField",name:"currentRevision",plural:!1,selections:[m,{alias:null,args:null,concreteType:"ModelMountConfig",kind:"LinkedField",name:"modelMountConfig",plural:!1,selections:[{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"vfolder",plural:!1,selections:[m,y],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"creator",plural:!1,selections:[m,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"fullName",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"c8a99223ab94622740985956ca48b0e8",id:null,metadata:{},name:"DeploymentListPageQuery",operationKind:"query",text:`query DeploymentListPageQuery(
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
        domainName
        projectId
        ...DeploymentTagChips_metadata
      }
      networkAccess {
        endpointUrl
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
        modelMountConfig {
          vfolder {
            id
            name
          }
        }
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

fragment DeploymentSettingModal_deployment on ModelDeployment {
  id
  metadata {
    name
    tags
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
`}}}();ye.hash="50f6f6b4035dc52329cd996125c886ea";const Ae=()=>{"use memo";const e=ue.c(79),{t:i}=ce(),n=De(),[o,r]=Ce(!1),{setLeft:s,setRight:m}=r,[y,M]=z.useState(null);let P;e[0]===Symbol.for("react.memo_cache_sentinel")?(P={current:1,pageSize:10},e[0]=P):P=e[0];const{baiPaginationOption:p,tablePaginationOption:J,setTablePaginationOption:d}=be(P);let B,j;e[1]===Symbol.for("react.memo_cache_sentinel")?(B={filter:Fe(Pe),order:de(Me),statusCategory:de(["running","finished"]).withDefault("running")},j={history:"replace"},e[1]=B,e[2]=j):(B=e[1],j=e[2]);const[l,u]=Se(B,j),[H,Y]=he("table_column_overrides.DeploymentListPage"),[N,c]=Ke();let O;e[3]!==l.order?(O=Re(l.order),e[3]=l.order,e[4]=O):O=e[4];const x=O;let V;e[5]!==x?(V=x?[{field:x.field,direction:x.order}]:void 0,e[5]=x,e[6]=V):V=e[6];const X=V;let w;e[7]===Symbol.for("react.memo_cache_sentinel")?(w=["STOPPED"],e[7]=w):w=e[7];const ie=w;let E;e[8]!==l.statusCategory?(E=l.statusCategory==="finished"?{status:{in:ie}}:{status:{notIn:ie}},e[8]=l.statusCategory,e[9]=E):E=e[9];const Z=E;let $;e[10]!==l.filter?($=l.filter??{},e[10]=l.filter,e[11]=$):$=e[11];const ee=$;let g;e[12]!==Z||e[13]!==ee?(g={...ee,...Z},e[12]=Z,e[13]=ee,e[14]=g):g=e[14];let q;e[15]!==p.limit||e[16]!==p.offset||e[17]!==X||e[18]!==g?(q={filter:g,orderBy:X,limit:p.limit,offset:p.offset},e[15]=p.limit,e[16]=p.offset,e[17]=X,e[18]=g,e[19]=q):q=e[19];const oe=q,re=z.useDeferredValue(oe),A=z.useDeferredValue(N);let Q;e[20]===Symbol.for("react.memo_cache_sentinel")?(Q=ye,e[20]=Q):Q=e[20];const le=A===ve?"store-and-network":"network-only";let U;e[21]!==A||e[22]!==le?(U={fetchPolicy:le,fetchKey:A},e[21]=A,e[22]=le,e[23]=U):U=e[23];const{myDeployments:ne}=Le.useLazyLoadQuery(Q,re,U),f=re!==oe||A!==N,te=l.filter??void 0;let k;e[24]!==u||e[25]!==d?(k=t=>{u({filter:t??null}),d({current:1})},e[24]=u,e[25]=d,e[26]=k):k=e[26];const ae=l.order??void 0;let D;e[27]!==u?(D=t=>{u({order:t??null})},e[27]=u,e[28]=D):D=e[28];const pe=l.statusCategory;let C;e[29]!==u||e[30]!==d?(C=t=>{u({statusCategory:t}),d({current:1})},e[29]=u,e[30]=d,e[31]=C):C=e[31];let b;e[32]!==d?(b=(t,ge)=>{d({current:t,pageSize:ge})},e[32]=d,e[33]=b):b=e[33];let F;e[34]!==b||e[35]!==J?(F={...J,onChange:b},e[34]=b,e[35]=J,e[36]=F):F=e[36];let S;e[37]!==H||e[38]!==Y?(S={columnOverrides:H,onColumnOverridesChange:Y},e[37]=H,e[38]=Y,e[39]=S):S=e[39];let h;e[40]!==n?(h=t=>{n(`/deployments/${_e(t)}`)},e[40]=n,e[41]=h):h=e[41];let G;e[42]===Symbol.for("react.memo_cache_sentinel")?(G=t=>M(t),e[42]=G):G=e[42];let K;e[43]!==N||e[44]!==f||e[45]!==c?(K=a.jsx(Te,{value:N,onChange:c,loading:f}),e[43]=N,e[44]=f,e[45]=c,e[46]=K):K=e[46];let L;e[47]!==i?(L=i("deployment.CreateDeployment"),e[47]=i,e[48]=L):L=e[48];let v;e[49]!==m||e[50]!==L?(v=a.jsx(Ie,{type:"primary",onClick:m,children:L}),e[49]=m,e[50]=L,e[51]=v):v=e[51];let _;e[52]!==K||e[53]!==v?(_=a.jsxs(me,{gap:"xs",align:"center",children:[K,v]}),e[52]=K,e[53]=v,e[54]=_):_=e[54];let T;e[55]!==f||e[56]!==ne||e[57]!==l.statusCategory||e[58]!==te||e[59]!==k||e[60]!==ae||e[61]!==D||e[62]!==C||e[63]!==F||e[64]!==S||e[65]!==h||e[66]!==_||e[67]!==c?(T=a.jsx(Ne,{deploymentsFrgmt:ne,filter:te,setFilter:k,order:ae,onChangeOrder:D,statusCategory:pe,onStatusCategoryChange:C,pagination:F,tableSettings:S,mode:"user",loading:f,onRowClick:h,onEditClick:G,onDeleteComplete:c,toolbarEnd:_}),e[55]=f,e[56]=ne,e[57]=l.statusCategory,e[58]=te,e[59]=k,e[60]=ae,e[61]=D,e[62]=C,e[63]=F,e[64]=S,e[65]=h,e[66]=_,e[67]=c,e[68]=T):T=e[68];const se=o||!!y;let I;e[69]!==s||e[70]!==c?(I=t=>{s(),M(null),t&&c()},e[69]=s,e[70]=c,e[71]=I):I=e[71];let R;e[72]!==y||e[73]!==se||e[74]!==I?(R=a.jsx(xe,{open:se,deploymentFrgmt:y,onRequestClose:I}),e[72]=y,e[73]=se,e[74]=I,e[75]=R):R=e[75];let W;return e[76]!==T||e[77]!==R?(W=a.jsxs(a.Fragment,{children:[T,R]}),e[76]=T,e[77]=R,e[78]=W):W=e[78],W},we=()=>{"use memo";const e=ue.c(6),{t:i}=ce();let n;e[0]!==i?(n=i("webui.menu.Deployments"),e[0]=i,e[1]=n):n=e[1];let o;e[2]===Symbol.for("react.memo_cache_sentinel")?(o={body:{paddingTop:0}},e[2]=o):o=e[2];let r;e[3]===Symbol.for("react.memo_cache_sentinel")?(r=a.jsx(z.Suspense,{fallback:a.jsx(fe,{active:!0}),children:a.jsx(Ae,{})}),e[3]=r):r=e[3];let s;return e[4]!==n?(s=a.jsx(me,{direction:"column",align:"stretch",gap:"md",children:a.jsx(ke,{variant:"borderless",title:n,styles:o,children:r})}),e[4]=n,e[5]=s):s=e[5],s};function Pe(e){return typeof e=="object"&&e!==null&&!Array.isArray(e)?e:{}}export{we as default};
//# sourceMappingURL=DeploymentListPage-DK6GTSbJ.js.map
