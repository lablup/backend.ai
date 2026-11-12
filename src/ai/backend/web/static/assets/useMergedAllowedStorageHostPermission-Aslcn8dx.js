import{H as e,mt as t}from"./helper-BWFKT_2Y.js";import{t as n}from"./react-relay-BfoHYpUf.js";var r=(function(){var e={defaultValue:null,kind:`LocalArgument`,name:`accessKey`},t={defaultValue:null,kind:`LocalArgument`,name:`domainName`},n=[{kind:`Variable`,name:`access_key`,variableName:`accessKey`},{kind:`Variable`,name:`domain_name`,variableName:`domainName`}],r={alias:null,args:null,kind:`ScalarField`,name:`resource_policy`,storageKey:null};return{fragment:{argumentDefinitions:[e,t],kind:`Fragment`,metadata:null,name:`useMergedAllowedStorageHostPermission_KeypairQuery`,selections:[{kind:`RequiredField`,field:{alias:null,args:n,concreteType:`KeyPair`,kind:`LinkedField`,name:`keypair`,plural:!1,selections:[{kind:`RequiredField`,field:r,action:`THROW`}],storageKey:null},action:`THROW`}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:[t,e],kind:`Operation`,name:`useMergedAllowedStorageHostPermission_KeypairQuery`,selections:[{alias:null,args:n,concreteType:`KeyPair`,kind:`LinkedField`,name:`keypair`,plural:!1,selections:[r,{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null}],storageKey:null}]},params:{cacheID:`05bd7db7ab185940108fba3f2cadc989`,id:null,metadata:{},name:`useMergedAllowedStorageHostPermission_KeypairQuery`,operationKind:`query`,text:`query useMergedAllowedStorageHostPermission_KeypairQuery(
  $domainName: String
  $accessKey: String
) {
  keypair(domain_name: $domainName, access_key: $accessKey) {
    resource_policy
    id
  }
}
`}}})();r.hash=`bca5af88ccf1508389ec648bf31c4965`;var i=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`domainName`},{defaultValue:null,kind:`LocalArgument`,name:`projectId`},{defaultValue:null,kind:`LocalArgument`,name:`resourcePolicyName`},{defaultValue:null,kind:`LocalArgument`,name:`skipProjectScope`}],t=[{alias:null,args:null,kind:`ScalarField`,name:`allowed_vfolder_hosts`,storageKey:null}],n=[{alias:null,args:[{kind:`Variable`,name:`name`,variableName:`domainName`}],concreteType:`Domain`,kind:`LinkedField`,name:`domain`,plural:!1,selections:t,storageKey:null},{condition:`skipProjectScope`,kind:`Condition`,passingValue:!1,selections:[{alias:null,args:[{kind:`Variable`,name:`domain_name`,variableName:`domainName`},{kind:`Variable`,name:`id`,variableName:`projectId`}],concreteType:`Group`,kind:`LinkedField`,name:`group`,plural:!1,selections:t,storageKey:null}]},{alias:null,args:[{kind:`Variable`,name:`name`,variableName:`resourcePolicyName`}],concreteType:`KeyPairResourcePolicy`,kind:`LinkedField`,name:`keypair_resource_policy`,plural:!1,selections:t,storageKey:null}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`useMergedAllowedStorageHostPermission_AllowedVFolderHostsQuery`,selections:n,type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`useMergedAllowedStorageHostPermission_AllowedVFolderHostsQuery`,selections:n},params:{cacheID:`d7039e705450efc38a646cd5cdc70184`,id:null,metadata:{},name:`useMergedAllowedStorageHostPermission_AllowedVFolderHostsQuery`,operationKind:`query`,text:`query useMergedAllowedStorageHostPermission_AllowedVFolderHostsQuery(
  $domainName: String
  $projectId: UUID!
  $resourcePolicyName: String
  $skipProjectScope: Boolean!
) {
  domain(name: $domainName) {
    allowed_vfolder_hosts
  }
  group(id: $projectId, domain_name: $domainName) @skip(if: $skipProjectScope) {
    allowed_vfolder_hosts
  }
  keypair_resource_policy(name: $resourcePolicyName) {
    allowed_vfolder_hosts
  }
}
`}}})();i.hash=`ad7ef1c40361740cddc3f40566121f8c`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.
*/
var a=n(),o=`00000000-0000-0000-0000-000000000000`,s=(n,s,c)=>{var l,u,d;let f=e(),{keypair:p}=(0,a.useLazyLoadQuery)(r,{domainName:n,accessKey:c},{fetchPolicy:`store-or-network`}),m=(0,a.useLazyLoadQuery)(i,{domainName:n,projectId:s??o,resourcePolicyName:p==null?void 0:p.resource_policy,skipProjectScope:s===null},{fetchPolicy:`store-or-network`}),h=JSON.parse((m==null||(l=m.domain)==null?void 0:l.allowed_vfolder_hosts)||`{}`),g=JSON.parse((m==null||(u=m.group)==null?void 0:u.allowed_vfolder_hosts)||`{}`),_=JSON.parse((m==null||(d=m.keypair_resource_policy)==null?void 0:d.allowed_vfolder_hosts)||`{}`),v=e=>[...new Set([].concat(...e.filter(Boolean)))],{data:y}=t({queryKey:[`vhostInfo`],queryFn:async()=>await f.vfolder.list_hosts(),staleTime:3e5,gcTime:0});return{StorageHostPermissionByDomain:h,StorageHostPermissionByGroup:g,StorageHostPermissionByResourcePolicy:_,unitedAllowedPermissionByVolume:Object.assign({},...y.allowed.map(e=>({[e]:v([h[e],g[e],_[e]])})))}};export{s as t};
