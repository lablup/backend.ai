"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[855],{82855:function(e,n,a){a.r(n);var l,i=a(1413),r=a(29439),s=a(44925),t=a(40406),c=a(1839),o=a(50164),u=a(77758),d=a(99277),y=a(38812),m=a(3597),k=a(70389),f=a(82548),p=(a(4519),a(81748)),g=a(16980),K=a(2556),_=["onRequestClose"];n.default=function(e){var n=e.onRequestClose,h=(0,s.Z)(e,_),x=(0,p.$G)().t,b=(0,c.jC)(),v=(0,r.Z)(b,1)[0],C=(0,t.Dj)(),Z=(0,o.h)({queryKey:["baiClient.keypair.list",h.open],queryFn:function(){return h.open?C.keypair.list(v.email,["access_key","secret_key","is_active"],!0).then((function(e){return e.keypairs})):null},suspense:!1,staleTime:0,cacheTime:0}).data,j=null===C||void 0===C?void 0:C.supports("main-access-key"),w=(0,g.useLazyLoadQuery)(void 0!==l?l:l=a(94167),{email:v.email}).user;return(0,K.jsx)(u.Z,(0,i.Z)((0,i.Z)({},h),{},{title:x("usersettings.MyKeypairInfo"),centered:!0,onCancel:n,destroyOnClose:!0,width:"auto",footer:[(0,K.jsx)(y.ZP,{onClick:function(){n()},children:x("button.Close")},"keypairInfoClose")],children:(0,K.jsx)(m.Z,{scroll:{x:"max-content"},rowKey:"access_key",dataSource:Z,columns:[{title:"#",fixed:"left",render:function(e,n,a){return++a},showSorterTooltip:!1,rowScope:"row"},{title:x("general.AccessKey"),key:"accessKey",dataIndex:"access_key",fixed:"left",render:function(e){return(0,K.jsxs)(d.Z,{direction:"column",align:"start",children:[(0,K.jsx)(k.Z.Text,{ellipsis:!0,copyable:!0,children:e}),j&&e===(null===w||void 0===w?void 0:w.main_access_key)&&(0,K.jsx)(f.Z,{color:"red",children:x("credential.MainAccessKey")})]})}},{title:x("general.SecretKey"),key:"secretKey",dataIndex:"secret_key",fixed:"left",render:function(e){return(0,K.jsx)(k.Z.Text,{ellipsis:!0,copyable:!0,children:e})}}]})}))}},94167:function(e,n,a){a.r(n);var l=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"email"}],n=[{kind:"Variable",name:"email",variableName:"email"}],a={alias:null,args:null,kind:"ScalarField",name:"email",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"main_access_key",storageKey:null};return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"KeypairInfoModalQuery",selections:[{alias:null,args:n,concreteType:"User",kind:"LinkedField",name:"user",plural:!1,selections:[a,l],storageKey:null}],type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"KeypairInfoModalQuery",selections:[{alias:null,args:n,concreteType:"User",kind:"LinkedField",name:"user",plural:!1,selections:[a,l,{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}]},params:{cacheID:"352a943226b02e137a3fcd32fa0ae22a",id:null,metadata:{},name:"KeypairInfoModalQuery",operationKind:"query",text:'query KeypairInfoModalQuery(\n  $email: String\n) {\n  user(email: $email) {\n    email\n    main_access_key @since(version: "23.09.7")\n    id\n  }\n}\n'}}}();l.hash="70097c005c8abc07e233048a68db1273",n.default=l}}]);
//# sourceMappingURL=855.9888df3c.chunk.js.map