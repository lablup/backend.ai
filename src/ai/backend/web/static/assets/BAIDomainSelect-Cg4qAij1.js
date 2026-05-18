import{ad as c,aE as u,i as m,j as d,aS as y,a6 as f}from"./index-M9a7wauv.js";const t=function(){var n=[{defaultValue:null,kind:"LocalArgument",name:"is_active"}],a=[{alias:null,args:[{kind:"Variable",name:"is_active",variableName:"is_active"}],concreteType:"Domain",kind:"LinkedField",name:"domains",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:n,kind:"Fragment",metadata:null,name:"BAIDomainSelectQuery",selections:a,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:n,kind:"Operation",name:"BAIDomainSelectQuery",selections:a},params:{cacheID:"57d026d6fa8a04c20ffa280feacb762f",id:null,metadata:{},name:"BAIDomainSelectQuery",operationKind:"query",text:`query BAIDomainSelectQuery(
  $is_active: Boolean
) {
  domains(is_active: $is_active) {
    name
  }
}
`}}}();t.hash="dc51af30271ef1276b6aba8998bb5c1b";const v=({activeOnly:n=!0,...a})=>{const{t:l}=c(),[i,s]=u(a),{domains:r}=m.useLazyLoadQuery(t,{is_active:n},{fetchPolicy:"store-and-network"});return d.jsx(y,{placeholder:l("comp:BAIDomainSelect.SelectDomain"),...a,value:i,onChange:(e,o)=>{s(e,o)},options:f(r,e=>({label:e==null?void 0:e.name,value:e==null?void 0:e.name}))})};export{v as B};
//# sourceMappingURL=BAIDomainSelect-Cg4qAij1.js.map
