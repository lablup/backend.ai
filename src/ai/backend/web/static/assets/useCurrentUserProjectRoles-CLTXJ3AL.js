import{t as e}from"./compiler-runtime-CZQb2eIb.js";import{Mt as t,St as n,T as r,bt as i,s as a,vt as o,w as s}from"./lodash-ClfL87UH.js";import{H as c,it as l}from"./helper-BWFKT_2Y.js";import{t as u}from"./react-relay-BfoHYpUf.js";import{t as d}from"./useAccessibleProjects-gzoxrvLz.js";import{t as f}from"./useCurrentProject-BaleCvMA.js";var p=e(),m=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`targets`}],t={alias:`projectAdminPermissions`,args:[{fields:[{kind:`Variable`,name:`targets`,variableName:`targets`}],kind:`ObjectValue`,name:`input`}],concreteType:`MyAtomicBulkScopePermissionsPayload`,kind:`LinkedField`,name:`myAtomicBulkScopePermissions`,plural:!1,selections:[{alias:null,args:null,concreteType:`ScopeEntityPermission`,kind:`LinkedField`,name:`items`,plural:!0,selections:[{alias:null,args:null,kind:`ScalarField`,name:`scopeId`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`permissions`,storageKey:null}],storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useCurrentUserProjectRolesQuery`,selections:[{kind:`CatchField`,field:t,to:`RESULT`}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useCurrentUserProjectRolesQuery`,selections:[t]},params:{cacheID:`b9fc0da4b7cedf1483612e12c5374484`,id:null,metadata:{},name:`useCurrentUserProjectRolesQuery`,operationKind:`query`,text:`query useCurrentUserProjectRolesQuery(
  $targets: [PermissionTarget!]!
) {
  projectAdminPermissions: myAtomicBulkScopePermissions(input: {targets: $targets}) {
    items {
      scopeId
      permissions
    }
  }
}
`}}})();m.hash=`ef8755038c81acbab86bac59692baa88`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var h=()=>{"use memo";let e=(0,p.c)(15),{accessibleProjects:n,personalProject:a}=d(),c;e[0]!==n||e[1]!==a?(c=a&&!r(n,{id:a.id})?[...n??[],a]:n,e[0]=n,e[1]=a,e[2]=c):c=e[2];let u=c,f=l(),m;if(e[3]!==f){for(let e=f.length-1;e>=0;e--){var h;let t=(h=f[e])==null?void 0:h.params;if(t!=null&&t.projectName){m=t.projectName;break}}e[3]=f,e[4]=m}else m=e[4];let _;e[5]===u?_=e[6]:(_=s(t(o(u,g))),e[5]=u,e[6]=_);let v=_,y;if(e[7]!==u||e[8]!==m){var b;y=m?((b=i(u,e=>(e==null?void 0:e.name)===m))==null?void 0:b.id)??void 0:void 0,e[7]=u,e[8]=m,e[9]=y}else y=e[9];let x=y,S=!!m&&!x,C;return e[10]!==v||e[11]!==S||e[12]!==x||e[13]!==m?(C={urlProjectName:m,isInvalid:S,resolvedId:x,groups:v},e[10]=v,e[11]=S,e[12]=x,e[13]=m,e[14]=C):C=e[14],C};function g(e){return e==null?void 0:e.name}
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var _=u(),v=100,y=()=>{"use memo";let e=(0,p.c)(15),r=c(),{accessibleProjects:i,personalProject:s}=d(),l,u,f,h;e[0]!==i||e[1]!==(s==null?void 0:s.id)?(l=a(t([...o(i,S),s==null?void 0:s.id])).sort().slice(0,v),f=_.useLazyLoadQuery,h=m,u=o(l,C),e[0]=i,e[1]=s==null?void 0:s.id,e[2]=l,e[3]=u,e[4]=f,e[5]=h):(l=e[2],u=e[3],f=e[4],h=e[5]);let g;e[6]===u?g=e[7]:(g={targets:u},e[6]=u,e[7]=g);let y=l.length>0?`store-or-network`:`store-only`,b;e[8]===y?b=e[9]:(b={fetchPolicy:y},e[8]=y,e[9]=b);let x=f(h,g,b),T;if(e[10]!==x.projectAdminPermissions){var E,D;T=((E=x.projectAdminPermissions)==null?void 0:E.ok)===!0?a(o(n((D=x.projectAdminPermissions.value)==null?void 0:D.items,w),`scopeId`)).sort():[],e[10]=x.projectAdminPermissions,e[11]=T}else T=e[11];let O=T,k=!!(r!=null&&r.is_superadmin),A;return e[12]!==k||e[13]!==O?(A={isSuperAdmin:k,projectAdminIds:O},e[12]=k,e[13]=O,e[14]=A):A=e[14],A},b=()=>{let{isSuperAdmin:e}=y(),t=x();return e?`superadmin`:t?`currentProjectAdmin`:`none`},x=()=>{var e;let{projectAdminIds:t}=y(),{urlProjectName:n,resolvedId:r}=h(),i=(e=f())==null?void 0:e.id,a=n?r:i;return!!a&&t.includes(a)};function S(e){return e==null?void 0:e.id}function C(e){return{scopeType:`project`,scopeId:e,entityType:`scope_admin`}}function w(e){return e.permissions.length>0}export{h as i,b as n,x as r,y as t};
