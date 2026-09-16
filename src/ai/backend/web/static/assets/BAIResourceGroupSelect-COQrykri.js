import{aA as t,r as o,j as l,H as c,al as s,ff as i}from"./index-DPebpL40.js";const n=(function(){var a=[{alias:null,args:null,concreteType:"ScalingGroup",kind:"LinkedField",name:"scaling_groups",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"BAIResourceGroupSelectQuery",selections:a,type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[],kind:"Operation",name:"BAIResourceGroupSelectQuery",selections:a},params:{cacheID:"e0e2315cadb2e8aa35586ebe588cd9d1",id:null,metadata:{},name:"BAIResourceGroupSelectQuery",operationKind:"query",text:`query BAIResourceGroupSelectQuery {
  scaling_groups {
    name
  }
}
`}}})();n.hash="835aef9b1b8293b5cb6fa2e775e8945c";const m=({...a})=>{const{t:r}=t(),{scaling_groups:u}=o.useLazyLoadQuery(n,{},{});return l.jsx(c,{options:s(i(u,"name"),e=>({label:e==null?void 0:e.name,value:e==null?void 0:e.name,resourceGroup:e==null?void 0:e.name})),showSearch:!0,placeholder:r("comp:BAIResourceGroupSelect.SelectResourceGroup"),...a})};export{m as B};
//# sourceMappingURL=BAIResourceGroupSelect-COQrykri.js.map
