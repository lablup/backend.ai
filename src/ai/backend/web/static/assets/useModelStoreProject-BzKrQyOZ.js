import{a as s,b$ as d,i as u,N as c}from"./index-M9a7wauv.js";const o=function(){var l=[{defaultValue:null,kind:"LocalArgument",name:"domainName"}],n=[{kind:"Variable",name:"domainName",variableName:"domainName"}],e={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},a={alias:null,args:[{kind:"Literal",name:"filter",value:{isActive:!0,type:{equals:"MODEL_STORE"}}}],concreteType:"ProjectV2Connection",kind:"LinkedField",name:"projects",plural:!1,selections:[{alias:null,args:null,concreteType:"ProjectV2Edge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ProjectV2",kind:"LinkedField",name:"node",plural:!1,selections:[e,{alias:null,args:null,concreteType:"ProjectBasicInfo",kind:"LinkedField",name:"basicInfo",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}],storageKey:'projects(filter:{"isActive":true,"type":{"equals":"MODEL_STORE"}})'};return{fragment:{argumentDefinitions:l,kind:"Fragment",metadata:null,name:"useModelStoreProjectQuery",selections:[{alias:null,args:n,concreteType:"DomainV2",kind:"LinkedField",name:"domainV2",plural:!1,selections:[a],storageKey:null}],type:"Query",abstractKey:null},kind:"Request",operation:{argumentDefinitions:l,kind:"Operation",name:"useModelStoreProjectQuery",selections:[{alias:null,args:n,concreteType:"DomainV2",kind:"LinkedField",name:"domainV2",plural:!1,selections:[a,e],storageKey:null}]},params:{cacheID:"f25d7d141d4fd27e5938a63e66a9cd3f",id:null,metadata:{},name:"useModelStoreProjectQuery",operationKind:"query",text:`query useModelStoreProjectQuery(
  $domainName: String!
) {
  domainV2(domainName: $domainName) {
    projects(filter: {type: {equals: MODEL_STORE}, isActive: true}) {
      edges {
        node {
          id
          basicInfo {
            name
          }
        }
      }
    }
    id
  }
}
`}}}();o.hash="b7c7bda37035dd1f39bf80a9e4caeb1b";const y=()=>{var a,i,t,r;s();const l=d(),{domainV2:n}=u.useLazyLoadQuery(o,{domainName:l},{fetchPolicy:"store-or-network"}),e=((t=(i=(a=n==null?void 0:n.projects)==null?void 0:a.edges)==null?void 0:i[0])==null?void 0:t.node)??null;return{id:e?c(e.id):null,name:((r=e==null?void 0:e.basicInfo)==null?void 0:r.name)??null}};export{y as u};
//# sourceMappingURL=useModelStoreProject-BzKrQyOZ.js.map
