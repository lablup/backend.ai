import{c as Ge,u as We,A as Fn,bb as In,a2 as Tn,q as mn,r as ze,n as l,ba as hn,C as Ae,R as gn,z as Qe,T as rn,b as Ln,bu as Kn,x as on,a as Vn,j as jn,i as dn,k as An,l as vn,e as Bn,g as Cn,m as xn,I as En,s as Pn,B as un,w as Mn,ay as _n,y as Nn,o as Rn}from"./index-CwWAznqi.js";import{A as On}from"./AutoUpdateFetchKeyButton-MZ4HY-Ai.js";import{r as v,b as $n,y as cn}from"./icons-BgdBQS0N.js";import{a1 as Dn,e as wn,R as qn,m as Un}from"./lodash-RhKGq0BF.js";import{a as zn}from"./CheckboxInput-Dvbz8RhO.js";import{g as Qn,B as Gn,a as Wn,s as Hn}from"./sessionStatusBuckets-3TcKSv6v.js";import{u as Jn}from"./reactPaginationQueryOptions-Bt4rkB5i.js";import{B as Yn}from"./BAISelectionLabel-DSve7JI4.js";import{B as Xn}from"./BAIEntityLabelBulkEditButton-DDExm9cf.js";import{B as Zn}from"./BAIScopedUserSelect-kPspQnY9.js";import{B as el}from"./BAIGraphQLPropertyFilter-BwM0Jjll.js";import{B as nl}from"./BAINameActionCell-BZc0os_M.js";import{B as ll}from"./BAIEntityLabelSettingModal-zXhyYD10.js";import{t as al}from"./BAIEntityLabelTokens-BWz7hwXT.js";import"./BAIFetchKeyButton-DApd5OLT.js";import"./useControllableValue-BmgV_ECW.js";import"./ButtonGroup-DPQvGHtt.js";import"./BAIEntityLabelCell-DciPKo0X.js";import"./BAITable-BJsxYyy0.js";import"./Table-SIAPvWUk.js";import"./characters-DWaYg7k3.js";import"./MenuBottomSheetActionList-DfgiyqqP.js";import"./useScrollableArea-Bsuw_xFk.js";import"./Pagination-cBiGXF8Y.js";import"./NumberInput-BAShrYzU.js";import"./useLocale-tF6sKPhr.js";import"./BAIId-C7PlhBcJ.js";import"./astryxTagVariant-CibgwVXb.js";import"./BAIImageNodeSimpleTagV2-grs0QBeV.js";import"./BAIDoubleToken-DmnYFlRB.js";import"./BAITextHighlighter-9-PRKuKt.js";import"./Token-B6wppFPd.js";import"./useBAIIconPath-kZbqwXZ-.js";import"./sessionTypeLabel-DAMPaqv3.js";import"./usePaginatedQuery-D34XeqI8.js";import"./BAIComplexSelect-D8NzXrV7.js";import"./combineFilters-CraaN1TU.js";import"./BAIPowerSearchAdapters-Cpa0dtdE.js";import"./Tokenizer-Czn8bbzO.js";import"./groupItems-BfxkhRY8.js";import"./DateRangeInput-BafIu0I7.js";import"./BottomSheet-C7Cy7dyi.js";import"./BAIBulkErrorModal-B1rud_RV.js";const fn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"filter"},e={defaultValue:null,kind:"LocalArgument",name:"limit"},i={defaultValue:null,kind:"LocalArgument",name:"offset"},a={defaultValue:null,kind:"LocalArgument",name:"orderBy"},u={defaultValue:null,kind:"LocalArgument",name:"projectId"},t=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"limit",variableName:"limit"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"orderBy",variableName:"orderBy"},{fields:[{items:[{fields:[{kind:"Variable",name:"value",variableName:"projectId"}],kind:"ObjectValue",name:"project.0"}],kind:"ListValue",name:"project"}],kind:"ObjectValue",name:"scope"}],g={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},B={alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},L=[f],T=[{alias:null,args:null,concreteType:"ResourceSlotEntry",kind:"LinkedField",name:"entries",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceType",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quantity",storageKey:null}],storageKey:null}],p={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null},M=[p,c];return{fragment:{argumentDefinitions:[n,e,i,a,u],kind:"Fragment",metadata:null,name:"ProjectAdminSessionPageQuery",selections:[{alias:null,args:t,concreteType:"SessionV2Connection",kind:"LinkedField",name:"scopedSessionsV2",plural:!1,selections:[g,{alias:null,args:null,concreteType:"SessionV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,B,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:L,storageKey:null},{args:null,kind:"FragmentSpread",name:"BAISessionNodesV2Fragment"},{args:null,kind:"FragmentSpread",name:"TerminateSessionModalForProjectAdminFragment"}],storageKey:null}],storageKey:null}],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[u,n,a,e,i],kind:"Operation",name:"ProjectAdminSessionPageQuery",selections:[{alias:null,args:t,concreteType:"SessionV2Connection",kind:"LinkedField",name:"scopedSessionsV2",plural:!1,selections:[g,{alias:null,args:null,concreteType:"SessionV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"SessionV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,B,{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[f,{alias:null,args:null,kind:"ScalarField",name:"sessionType",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterMode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"clusterSize",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"project",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:L,storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"SessionV2LifecycleInfo",kind:"LinkedField",name:"lifecycle",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"createdAt",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminatedAt",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"SessionV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"resourceGroupName",storageKey:null},{alias:null,args:null,concreteType:"ResourceAllocation",kind:"LinkedField",name:"allocation",plural:!1,selections:[{alias:null,args:null,concreteType:"ResourceSlot",kind:"LinkedField",name:"requested",plural:!1,selections:T,storageKey:null},{alias:null,args:null,concreteType:"ResourceSlot",kind:"LinkedField",name:"used",plural:!1,selections:T,storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2Connection",kind:"LinkedField",name:"images",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ImageV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,{alias:null,args:null,concreteType:"ImageV2IdentityInfo",kind:"LinkedField",name:"identity",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"canonicalName",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,concreteType:"ImageV2TagEntry",kind:"LinkedField",name:"tags",plural:!0,selections:M,storageKey:null},{alias:null,args:null,concreteType:"ImageV2LabelEntry",kind:"LinkedField",name:"labels",plural:!0,selections:M,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"UserV2",kind:"LinkedField",name:"user",plural:!1,selections:[r,{alias:null,args:null,concreteType:"UserV2BasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null}],storageKey:null}],storageKey:null},{alias:null,args:[{kind:"Literal",name:"limit",value:100}],concreteType:"EntityLabelConnection",kind:"LinkedField",name:"entityLabels",plural:!1,selections:[{alias:null,args:null,concreteType:"EntityLabelEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"EntityLabel",kind:"LinkedField",name:"node",plural:!1,selections:[p,c,r,{alias:null,args:null,kind:"ScalarField",name:"fieldId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:"entityLabels(limit:100)"},{alias:null,args:null,concreteType:"KernelV2Connection",kind:"LinkedField",name:"kernels",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelV2",kind:"LinkedField",name:"node",plural:!1,selections:[r,{alias:null,args:null,concreteType:"KernelV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"agentId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"containerId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:"34c9d9ad1370e504253cc173852247e6",id:null,metadata:{},name:"ProjectAdminSessionPageQuery",operationKind:"query",text:`query ProjectAdminSessionPageQuery(
  $projectId: UUID!
  $filter: SessionV2Filter
  $orderBy: [SessionV2OrderBy!]
  $limit: Int
  $offset: Int
) {
  scopedSessionsV2(scope: {project: [{value: $projectId}]}, filter: $filter, orderBy: $orderBy, limit: $limit, offset: $offset) {
    count
    edges {
      node {
        id
        entityId
        metadata {
          name
        }
        ...BAISessionNodesV2Fragment
        ...TerminateSessionModalForProjectAdminFragment
      }
    }
  }
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

fragment BAISessionClusterModeV2Fragment on SessionV2MetadataInfo {
  clusterMode
  clusterSize
}

fragment BAISessionNodesV2Fragment on SessionV2 {
  id
  entityId
  project {
    id
    basicInfo {
      name
    }
  }
  metadata {
    name
    ...BAISessionTypeTokenV2Fragment
    ...BAISessionClusterModeV2Fragment
  }
  lifecycle {
    status
    createdAt
    terminatedAt
  }
  resource {
    resourceGroupName
    allocation {
      requested {
        entries {
          resourceType
          quantity
        }
      }
      used {
        entries {
          resourceType
          quantity
        }
      }
    }
  }
  images {
    edges {
      node {
        id
        ...BAIImageNodeSimpleTagV2Fragment
      }
    }
  }
  user {
    id
    basicInfo {
      email
    }
  }
  entityLabels(limit: 100) {
    ...BAIEntityLabelTokensFragment
    ...BAIEntityLabelSettingModalFragment
  }
}

fragment BAISessionTypeTokenV2Fragment on SessionV2MetadataInfo {
  sessionType
}

fragment TerminateSessionModalForProjectAdminFragment on SessionV2 {
  id
  entityId
  metadata {
    name
  }
  kernels {
    edges {
      node {
        id
        resource {
          agentId
          containerId
        }
      }
    }
  }
}
`}}})();fn.hash="dffdafc4db1a23f3470e7b6f8aa0dcd1";const pn=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"forced"},e={defaultValue:null,kind:"LocalArgument",name:"sessionIds"},i=[{alias:null,args:[{kind:"Variable",name:"forced",variableName:"forced"},{kind:"Variable",name:"sessionIds",variableName:"sessionIds"}],concreteType:"TerminateSessionsPayload",kind:"LinkedField",name:"terminateSessionsV2",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"cancelled",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"terminating",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"forceTerminated",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"skipped",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[n,e],kind:"Fragment",metadata:null,name:"TerminateSessionModalForProjectAdminMutation",selections:i,type:"Mutation",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,n],kind:"Operation",name:"TerminateSessionModalForProjectAdminMutation",selections:i},params:{cacheID:"be4736b37ff54351dd17b8f5d312c2bd",id:null,metadata:{},name:"TerminateSessionModalForProjectAdminMutation",operationKind:"mutation",text:`mutation TerminateSessionModalForProjectAdminMutation(
  $sessionIds: [ID!]!
  $forced: Boolean!
) {
  terminateSessionsV2(sessionIds: $sessionIds, forced: $forced) {
    cancelled
    terminating
    forceTerminated
    skipped
  }
}
`}}})();pn.hash="8c1ab011f362b60cae0d0e3b7c59bf7e";const yn=(function(){var n={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:{plural:!0},name:"TerminateSessionModalForProjectAdminFragment",selections:[n,{alias:null,args:null,kind:"ScalarField",name:"entityId",storageKey:null},{alias:null,args:null,concreteType:"SessionV2MetadataInfo",kind:"LinkedField",name:"metadata",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"KernelV2Connection",kind:"LinkedField",name:"kernels",plural:!1,selections:[{alias:null,args:null,concreteType:"KernelV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"KernelV2",kind:"LinkedField",name:"node",plural:!1,selections:[n,{alias:null,args:null,concreteType:"KernelV2ResourceInfo",kind:"LinkedField",name:"resource",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"agentId",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"containerId",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],type:"SessionV2",abstractKey:null}})();yn.hash="7012eaf26b1804672778ddb998dd1c1e";const tl=n=>{"use memo";var $,D;const e=Ge.c(27);let i,a,u;e[0]!==n?({sessionsFrgmt:u,onRequestClose:a,...i}=n,e[0]=n,e[1]=i,e[2]=a,e[3]=u):(i=e[1],a=e[2],u=e[3]);const{t}=We(),{token:g}=Fn(),{message:r}=In.useApp(),B=Tn(),[f,L]=v.useState(!1);let T;e[4]===Symbol.for("react.memo_cache_sentinel")?(T=yn,e[4]=T):T=e[4];const p=mn(ze.useFragment(T,u));let c;e[5]===Symbol.for("react.memo_cache_sentinel")?(c=pn,e[5]=c):c=e[5];const[M,O]=ze.useMutation(c);let b;e[6]!==a?(b=F=>{L(!1),a(F)},e[6]=a,e[7]=b):b=e[7];const k=b,y=Dn(wn(qn(p,il)),rl);let K;e[8]!==t?(K=t("session.TerminateSession"),e[8]=t,e[9]=K):K=e[9];let V;e[10]!==f||e[11]!==t?(V=t(f?"button.ForceTerminate":"session.Terminate"),e[10]=f,e[11]=t,e[12]=V):V=e[12];const d=f?"primary":"default";let m;e[13]!==d?(m={type:d},e[13]=d,e[14]=m):m=e[14];let h;e[15]!==k?(h=()=>k(!1),e[15]=k,e[16]=h):h=e[16];let o;e[17]!==t?(o=t("userSettings.SessionTerminationDialog"),e[17]=t,e[18]=o):o=e[18];let C;e[19]!==o?(C=l.jsx(rn,{children:o}),e[19]=o,e[20]=C):C=e[20];let j;e[21]===Symbol.for("react.memo_cache_sentinel")?(j=F=>L(F),e[21]=j):j=e[21];let x;e[22]!==t?(x=t("button.ForceTerminate"),e[22]=t,e[23]=x):x=e[23];let E;return e[24]!==f||e[25]!==x?(E=l.jsx(zn,{value:f,onChange:j,children:x}),e[24]=f,e[25]=x,e[26]=E):E=e[26],l.jsx(hn,{centered:!0,title:K,okText:V,okType:"danger",okButtonProps:m,confirmLoading:O,onOk:()=>{if(p.length===0){k(!1);return}M({variables:{sessionIds:p.map(ol),forced:f},onCompleted:(F,_)=>{var A;if(_&&_.length>0){r.error(((A=_[0])==null?void 0:A.message)??t("general.ErrorOccurred"));return}r.success(t("session.SessionTerminated")),k(!0)},onError:F=>{r.error(F.message)}})},onCancel:h,...i,children:l.jsxs(Ae,{className:"terminate-session-modal-admin-list",direction:"column",align:"stretch",gap:"xs",children:[C,l.jsx(gn,{mark:!0,children:p.length===1?((D=($=p[0])==null?void 0:$.metadata)==null?void 0:D.name)??"":`${p.length} sessions`}),E,f&&l.jsxs(Qe,{styles:{body:{padding:g("--spacing-4")}},children:[l.jsx(rn,{as:"p",display:"block",color:"danger",children:t("session.ForceTerminateWarningMsg")}),l.jsxs("ul",{children:[l.jsx("li",{children:t("session.ForceTerminateWarningMsg2")}),l.jsx("li",{children:t("session.ForceTerminateWarningMsg3")})]}),B==="superadmin"&&l.jsx(Qe,{type:"inner",title:t("session.ContainerToCleanUp"),children:Un(y,ul)})]})]})})};function sl(n){return n==null?void 0:n.node}function il(n){var e,i;return(i=(e=n.kernels)==null?void 0:e.edges)==null?void 0:i.map(sl)}function rl(n){var e;return((e=n==null?void 0:n.resource)==null?void 0:e.agentId)??"-"}function ol(n){return n.entityId}function dl(n){var e;return l.jsx("li",{children:l.jsx(gn,{copyable:!0,children:((e=n==null?void 0:n.resource)==null?void 0:e.containerId)??""})},n==null?void 0:n.id)}function ul(n,e){return l.jsxs($n.Fragment,{children:[e,l.jsx("ul",{children:n.map(dl)})]},e)}const cl=n=>{"use memo";var Xe,Ze,en,nn,ln,an;const e=Ge.c(149),{projectId:i}=n,{t:a}=We();let u;e[0]===Symbol.for("react.memo_cache_sentinel")?(u=[],e[0]=u):u=e[0];const[t,g]=v.useState(u);let r;e[1]===Symbol.for("react.memo_cache_sentinel")?(r=[],e[1]=r):r=e[1];const[B,f]=v.useState(r),[L,T]=v.useState(!1),p=Vn("session"),[c,M]=v.useState(null);let O;e[2]===Symbol.for("react.memo_cache_sentinel")?(O={current:1,pageSize:10},e[2]=O):O=e[2];const{baiPaginationOption:b,tablePaginationOption:k,setTablePaginationOption:y}=Jn(O);let K,V;e[3]===Symbol.for("react.memo_cache_sentinel")?(K={statusCategory:dn(Hn).withDefault("running"),order:dn(Wn),filter:jn(ml)},V={history:"replace"},e[3]=K,e[4]=V):(K=e[3],V=e[4]);const[d,m]=An(K,V),[h,o]=vn(),C=Bn();let j;e[5]!==C?(j=Qn(C.isManagerVersionCompatibleWith("26.8.0")),e[5]=C,e[6]=j):j=e[6];const x=j,[E,$]=Cn("table_column_overrides.ProjectAdminSessionPage"),D=x[d.statusCategory];let F;e[7]!==D?(F={in:D},e[7]=D,e[8]=F):F=e[8];const _=F;let A;e[9]!==d.filter?(A=d.filter??{},e[9]=d.filter,e[10]=A):A=e[10];let w;e[11]!==_||e[12]!==A?(w={...A,status:_},e[11]=_,e[12]=A,e[13]=w):w=e[13];let q;e[14]!==d.order?(q=xn(d.order)??[{field:"CREATED_AT",direction:"DESC"}],e[14]=d.order,e[15]=q):q=e[15];let ve;e[16]!==b.limit||e[17]!==b.offset||e[18]!==i||e[19]!==w||e[20]!==q?(ve={projectId:i,filter:w,orderBy:q,limit:b.limit,offset:b.offset},e[16]=b.limit,e[17]=b.offset,e[18]=i,e[19]=w,e[20]=q,e[21]=ve):ve=e[21];const He=ve,Je=v.useDeferredValue(He),je=v.useDeferredValue(h);let Be;e[22]===Symbol.for("react.memo_cache_sentinel")?(Be=fn,e[22]=Be):Be=e[22];const Oe=je===Pn?"store-and-network":"network-only";let Ce;e[23]!==je||e[24]!==Oe?(Ce={fetchKey:je,fetchPolicy:Oe},e[23]=je,e[24]=Oe,e[25]=Ce):Ce=e[25];const xe=ze.useLazyLoadQuery(Be,Je,Ce);let Ee;e[26]!==((Xe=xe.scopedSessionsV2)==null?void 0:Xe.edges)?(Ee=mn((en=(Ze=xe.scopedSessionsV2)==null?void 0:Ze.edges)==null?void 0:en.map(gl)),e[26]=(nn=xe.scopedSessionsV2)==null?void 0:nn.edges,e[27]=Ee):Ee=e[27];const I=Ee,$e=((ln=xe.scopedSessionsV2)==null?void 0:ln.count)??0;let Pe;e[28]===Symbol.for("react.memo_cache_sentinel")?(Pe=s=>{f(s),T(!0)},e[28]=Pe):Pe=e[28];const Ye=Pe,U=Je!==He||je!==h;let Me;e[29]===Symbol.for("react.memo_cache_sentinel")?(Me={flexShrink:1},e[29]=Me):Me=e[29];const kn=d.statusCategory;let z;e[30]!==m||e[31]!==y?(z=s=>{m({statusCategory:s}),y({current:1})},e[30]=m,e[31]=y,e[32]=z):z=e[32];let Q;e[33]!==a?(Q=a("session.Running"),e[33]=a,e[34]=Q):Q=e[34];let G;e[35]!==Q?(G=l.jsx(un,{value:"running",label:Q}),e[35]=Q,e[36]=G):G=e[36];let W;e[37]!==a?(W=a("session.Finished"),e[37]=a,e[38]=W):W=e[38];let H;e[39]!==W?(H=l.jsx(un,{value:"finished",label:W}),e[39]=W,e[40]=H):H=e[40];let J;e[41]!==d.statusCategory||e[42]!==z||e[43]!==G||e[44]!==H?(J=l.jsxs(Mn,{value:kn,onChange:z,children:[G,H]}),e[41]=d.statusCategory,e[42]=z,e[43]=G,e[44]=H,e[45]=J):J=e[45];let _e;e[46]===Symbol.for("react.memo_cache_sentinel")?(_e={key:"id",propertyLabel:"ID",type:"uuid"},e[46]=_e):_e=e[46];let Y;e[47]!==a?(Y=a("session.SessionName"),e[47]=a,e[48]=Y):Y=e[48];let X;e[49]!==Y?(X={key:"name",propertyLabel:Y,type:"string"},e[49]=Y,e[50]=X):X=e[50];let Z;e[51]!==a?(Z=a("session.Owner"),e[51]=a,e[52]=Z):Z=e[52];let ee;e[53]!==i||e[54]!==a?(ee=s=>{const{onAddCondition:S,value:Ke,isDisabled:P}=s;return l.jsx(v.Suspense,{fallback:l.jsx(_n,{disabled:!0,loading:!0}),children:l.jsx(Zn,{scope:{project:[{value:i}]},valuePropName:"id",label:a("session.Owner"),isLabelHidden:!0,value:Ke,isDisabled:P,onChange:(N,R)=>{var Ve;return S(N,Array.isArray(R)?(Ve=R[0])==null?void 0:Ve.label:R==null?void 0:R.label)}})})},e[53]=i,e[54]=a,e[55]=ee):ee=e[55];let ne;e[56]!==Z||e[57]!==ee?(ne={key:"userUuid",propertyLabel:Z,type:"uuid",renderInput:ee},e[56]=Z,e[57]=ee,e[58]=ne):ne=e[58];let le;e[59]!==p||e[60]!==a?(le=p?[{key:"labels.some.key",propertyLabel:a("entityLabel.LabelKey"),type:"string"},{key:"labels.some.value",propertyLabel:a("entityLabel.LabelValue"),type:"string"}]:[],e[59]=p,e[60]=a,e[61]=le):le=e[61];let ae;e[62]!==X||e[63]!==ne||e[64]!==le?(ae=[_e,X,ne,...le],e[62]=X,e[63]=ne,e[64]=le,e[65]=ae):ae=e[65];const De=d.filter??void 0;let te;e[66]!==m||e[67]!==y?(te=s=>{m({filter:s??null}),y({current:1})},e[66]=m,e[67]=y,e[68]=te):te=e[68];let se;e[69]!==ae||e[70]!==De||e[71]!==te?(se=l.jsx(el,{filterProperties:ae,value:De,onChange:te}),e[69]=ae,e[70]=De,e[71]=te,e[72]=se):se=e[72];let ie;e[73]!==J||e[74]!==se?(ie=l.jsxs(Ae,{gap:"sm",align:"start",wrap:"wrap",style:Me,children:[J,se]}),e[73]=J,e[74]=se,e[75]=ie):ie=e[75];let re;e[76]!==t||e[77]!==a||e[78]!==o?(re=t.length>0&&l.jsxs(l.Fragment,{children:[l.jsx(Yn,{count:t.length,onClearSelection:()=>g([])}),l.jsx(Xn,{entityType:"session",targets:t.map(fl),onLabelsChanged:()=>o()}),l.jsx(En,{label:a("session.TerminateSession"),tooltip:a("session.TerminateSession"),icon:l.jsx(cn,{color:"var(--color-error)"}),onClick:()=>Ye(t)})]}),e[76]=t,e[77]=a,e[78]=o,e[79]=re):re=e[79];let oe;e[80]!==o?(oe=s=>o(s),e[80]=o,e[81]=oe):oe=e[81];let de;e[82]!==h||e[83]!==U||e[84]!==oe?(de=l.jsx(On,{settingId:"project-admin-session",defaultAutoUpdateDelay:15e3,loading:U,value:h,onChange:oe}),e[82]=h,e[83]=U,e[84]=oe,e[85]=de):de=e[85];let ue;e[86]!==re||e[87]!==de?(ue=l.jsxs(Ae,{gap:"xs",children:[re,de]}),e[86]=re,e[87]=de,e[88]=ue):ue=e[88];let ce;e[89]!==ie||e[90]!==ue?(ce=l.jsxs(Ae,{direction:"row",justify:"between",wrap:"wrap",gap:"sm",children:[ie,ue]}),e[89]=ie,e[90]=ue,e[91]=ce):ce=e[91];const we=p?M:void 0;let me;e[92]!==m||e[93]!==y?(me=s=>{m({filter:al(s)}),y({current:1})},e[92]=m,e[93]=y,e[94]=me):me=e[94];const Sn=d.order;let ge;e[95]!==m?(ge=s=>{m({order:s})},e[95]=m,e[96]=ge):ge=e[96];let fe;if(e[97]!==t||e[98]!==I){let s;e[100]!==I?(s=Ke=>{Nn(Ke,I,g)},e[100]=I,e[101]=s):s=e[101];let S;e[102]!==t?(S=t.map(pl),e[102]=t,e[103]=S):S=e[103],fe={type:"checkbox",preserveSelectedRowKeys:!0,getCheckboxProps(Ke){var N;const P=(N=Ke.lifecycle)==null?void 0:N.status;return{disabled:!!P&&["TERMINATED","CANCELLED","TERMINATING"].includes(P)}},onChange:s,selectedRowKeys:S},e[97]=t,e[98]=I,e[99]=fe}else fe=e[99];let pe;e[104]!==I||e[105]!==a?(pe=s=>s.map(S=>S.key!=="name"?S:{...S,render:(Ke,P)=>{var tn,sn;const N=(tn=P.lifecycle)==null?void 0:tn.status,R=!!N&&["TERMINATED","CANCELLED","TERMINATING"].includes(N),Ve=I.find(bn=>bn.id===P.id);return l.jsx(nl,{title:((sn=P.metadata)==null?void 0:sn.name)??"-",showActions:"always",actions:Rn([{key:"terminate",title:a("session.TerminateSession"),icon:l.jsx(cn,{}),type:"danger",disabled:R||!Ve,onClick:()=>Ve&&Ye([Ve])}])})}}),e[104]=I,e[105]=a,e[106]=pe):pe=e[106];let ye;e[107]!==y?(ye=(s,S)=>{y({current:s,pageSize:S})},e[107]=y,e[108]=ye):ye=e[108];let ke;e[109]!==ye||e[110]!==k.current||e[111]!==k.pageSize||e[112]!==$e?(ke={current:k.current,pageSize:k.pageSize,total:$e,onChange:ye},e[109]=ye,e[110]=k.current,e[111]=k.pageSize,e[112]=$e,e[113]=ke):ke=e[113];let Ne;e[114]===Symbol.for("react.memo_cache_sentinel")?(Ne={environment:{hidden:!1},resourceGroup:{hidden:!1},sessionType:{hidden:!1},clusterMode:{hidden:!1},createdAt:{hidden:!1}},e[114]=Ne):Ne=e[114];let Se;e[115]!==E||e[116]!==$?(Se={columnOverrides:E,defaultColumnOverrides:Ne,onColumnOverridesChange:$},e[115]=E,e[116]=$,e[117]=Se):Se=e[117];let be;e[118]!==U||e[119]!==d.order||e[120]!==I||e[121]!==we||e[122]!==me||e[123]!==ge||e[124]!==fe||e[125]!==pe||e[126]!==ke||e[127]!==Se?(be=l.jsx(Gn,{onEditLabels:we,showLabelsByDefault:!0,onLabelClick:me,sessionsFrgmt:I,loading:U,order:Sn,onChangeOrder:ge,rowSelection:fe,customizeColumns:pe,pagination:ke,tableSettings:Se}),e[118]=U,e[119]=d.order,e[120]=I,e[121]=we,e[122]=me,e[123]=ge,e[124]=fe,e[125]=pe,e[126]=ke,e[127]=Se,e[128]=be):be=e[128];const qe=!!c;let Fe;e[129]!==c?(Fe=c?[{entityId:c.entityId,name:((an=c.metadata)==null?void 0:an.name)??void 0}]:[],e[129]=c,e[130]=Fe):Fe=e[130];const Ue=c==null?void 0:c.entityLabels;let Ie;e[131]!==o?(Ie=s=>{M(null),s&&o()},e[131]=o,e[132]=Ie):Ie=e[132];let Te;e[133]!==qe||e[134]!==Fe||e[135]!==Ue||e[136]!==Ie?(Te=l.jsx(ll,{open:qe,entityType:"session",targets:Fe,entityLabelsFrgmt:Ue,onRequestClose:Ie}),e[133]=qe,e[134]=Fe,e[135]=Ue,e[136]=Ie,e[137]=Te):Te=e[137];let he;e[138]!==o?(he=s=>{T(!1),s&&(g([]),o())},e[138]=o,e[139]=he):he=e[139];let Le;e[140]!==L||e[141]!==he||e[142]!==B?(Le=l.jsx(tl,{open:L,sessionsFrgmt:B,onRequestClose:he}),e[140]=L,e[141]=he,e[142]=B,e[143]=Le):Le=e[143];let Re;return e[144]!==ce||e[145]!==be||e[146]!==Te||e[147]!==Le?(Re=l.jsxs(Ae,{direction:"column",align:"stretch",gap:"sm",children:[ce,be,Te,Le]}),e[144]=ce,e[145]=be,e[146]=Te,e[147]=Le,e[148]=Re):Re=e[148],Re},sa=()=>{"use memo";const n=Ge.c(9),{t:e}=We(),i=Ln();let a;n[0]!==e?(a=e("webui.menu.ProjectSessions"),n[0]=e,n[1]=a):a=n[1];let u;n[2]===Symbol.for("react.memo_cache_sentinel")?(u={header:{borderBottom:"none"},body:{paddingTop:0}},n[2]=u):u=n[2];let t;n[3]===Symbol.for("react.memo_cache_sentinel")?(t=l.jsx(on,{}),n[3]=t):t=n[3];let g;n[4]!==i.id?(g=l.jsx(Kn,{children:l.jsx(v.Suspense,{fallback:t,children:i.id?l.jsx(cl,{projectId:i.id}):l.jsx(on,{})})}),n[4]=i.id,n[5]=g):g=n[5];let r;return n[6]!==a||n[7]!==g?(r=l.jsx(l.Fragment,{children:l.jsx(Qe,{variant:"borderless",title:a,styles:u,children:g})}),n[6]=a,n[7]=g,n[8]=r):r=n[8],r};function ml(n){return n}function gl(n){return n==null?void 0:n.node}function fl(n){var e;return{entityId:n.entityId,name:((e=n.metadata)==null?void 0:e.name)??void 0}}function pl(n){return n.id}export{sa as default};
//# sourceMappingURL=ProjectAdminSessionPage-AmKso7_G.js.map
