import{e as P,r as y,ct as S}from"./index-CwWAznqi.js";const p=(function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"domainName"},{defaultValue:null,kind:"LocalArgument",name:"projectId"},{defaultValue:null,kind:"LocalArgument",name:"resourcePolicyName"},{defaultValue:null,kind:"LocalArgument",name:"skipProjectScope"}],e=[{alias:null,args:null,kind:"ScalarField",name:"allowed_vfolder_hosts",storageKey:null}],o=[{alias:null,args:[{kind:"Variable",name:"name",variableName:"domainName"}],concreteType:"Domain",kind:"LinkedField",name:"domain",plural:!1,selections:e,storageKey:null},{condition:"skipProjectScope",kind:"Condition",passingValue:!1,selections:[{alias:null,args:[{kind:"Variable",name:"domain_name",variableName:"domainName"},{kind:"Variable",name:"id",variableName:"projectId"}],concreteType:"Group",kind:"LinkedField",name:"group",plural:!1,selections:e,storageKey:null}]},{alias:null,args:[{kind:"Variable",name:"name",variableName:"resourcePolicyName"}],concreteType:"KeyPairResourcePolicy",kind:"LinkedField",name:"keypair_resource_policy",plural:!1,selections:e,storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"useMergedAllowedStorageHostPermission_AllowedVFolderHostsQuery",selections:o,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"useMergedAllowedStorageHostPermission_AllowedVFolderHostsQuery",selections:o},params:{cacheID:"d7039e705450efc38a646cd5cdc70184",id:null,metadata:{},name:"useMergedAllowedStorageHostPermission_AllowedVFolderHostsQuery",operationKind:"query",text:`query useMergedAllowedStorageHostPermission_AllowedVFolderHostsQuery(
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
`}}})();p.hash="ad7ef1c40361740cddc3f40566121f8c";const g=(function(){var n={defaultValue:null,kind:"LocalArgument",name:"accessKey"},e={defaultValue:null,kind:"LocalArgument",name:"domainName"},o=[{kind:"Variable",name:"access_key",variableName:"accessKey"},{kind:"Variable",name:"domain_name",variableName:"domainName"}],l={alias:null,args:null,kind:"ScalarField",name:"resource_policy",storageKey:null};return{fragment:{argumentDefinitions:[n,e],kind:"Fragment",metadata:null,name:"useMergedAllowedStorageHostPermission_KeypairQuery",selections:[{kind:"RequiredField",field:{alias:null,args:o,concreteType:"KeyPair",kind:"LinkedField",name:"keypair",plural:!1,selections:[{kind:"RequiredField",field:l,action:"THROW"}],storageKey:null},action:"THROW"}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,n],kind:"Operation",name:"useMergedAllowedStorageHostPermission_KeypairQuery",selections:[{alias:null,args:o,concreteType:"KeyPair",kind:"LinkedField",name:"keypair",plural:!1,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"05bd7db7ab185940108fba3f2cadc989",id:null,metadata:{},name:"useMergedAllowedStorageHostPermission_KeypairQuery",operationKind:"query",text:`query useMergedAllowedStorageHostPermission_KeypairQuery(
  $domainName: String
  $accessKey: String
) {
  keypair(domain_name: $domainName, access_key: $accessKey) {
    resource_policy
    id
  }
}
`}}})();g.hash="bca5af88ccf1508389ec648bf31c4965";const N="00000000-0000-0000-0000-000000000000",w=(n,e,o)=>{var c,u,m;const l=P(),{keypair:r}=y.useLazyLoadQuery(g,{domainName:n,accessKey:o},{fetchPolicy:"store-or-network"}),a=y.useLazyLoadQuery(p,{domainName:n,projectId:e??N,resourcePolicyName:r==null?void 0:r.resource_policy,skipProjectScope:e===null},{fetchPolicy:"store-or-network"}),s=JSON.parse(((c=a==null?void 0:a.domain)==null?void 0:c.allowed_vfolder_hosts)||"{}"),t=JSON.parse(((u=a==null?void 0:a.group)==null?void 0:u.allowed_vfolder_hosts)||"{}"),d=JSON.parse(((m=a==null?void 0:a.keypair_resource_policy)==null?void 0:m.allowed_vfolder_hosts)||"{}"),k=i=>[...new Set([].concat(...i.filter(Boolean)))],{data:f}=S({queryKey:["vhostInfo"],queryFn:async()=>await l.vfolder.list_hosts(),staleTime:1e3*60*5,gcTime:0}),_=Object.assign({},...f.allowed.map(i=>({[i]:k([s[i],t[i],d[i]])})));return{StorageHostPermissionByDomain:s,StorageHostPermissionByGroup:t,StorageHostPermissionByResourcePolicy:d,unitedAllowedPermissionByVolume:_}};export{w as u};
//# sourceMappingURL=useMergedAllowedStorageHostPermission-79PKn5Ce.js.map
