"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[4703],{4703:(e,n,r)=>{r.r(n),r.d(n,{default:()=>Y});var a,i,t,l=r(58879),s=r(51593),o=r(16522),d=r(3643),u=r(34357),c=r(94126),m=r(10546),g=r(69144),y=r(44733),p=r(23702),f=r(67378),k=r(9833),v=r(69056),h=r(89608),b=r.n(h),_=r(43373),A=r(56762),C=r(88522),x=r(73689);const w=e=>{let{containerRegistryFrgmt:n=null,onOk:l,...s}=e;const{t:o}=(0,A.Bd)(),d=(0,_.useRef)(null),{message:u,modal:m}=y.A.useApp(),h=(0,C.useFragment)(void 0!==a?a:a=r(49766),n),[w,R]=(0,C.useMutation)(void 0!==i?i:i=r(52777)),[j,S]=(0,C.useMutation)(void 0!==t?t:t=r(447)),F=async()=>{var e;return null===(e=d.current)||void 0===e?void 0:e.validateFields().then((e=>{let n={id:b().isEmpty(e.row_id)?void 0:e.row_id,registry_name:e.registry_name,url:e.url,type:e.type,project:"docker"===e.type?"library":e.project,username:b().isEmpty(e.username)?null:e.username,password:e.isChangedPassword?b().isEmpty(e.password)?null:e.password:void 0};h?(e.isChangedPassword||delete n.password,n=b().omitBy(n,b().isNil),j({variables:n,onCompleted:(e,n)=>{var r;if(b().isEmpty(null===(r=e.modify_container_registry_node)||void 0===r?void 0:r.container_registry))u.error(o("dialog.ErrorOccurred"));else if(n&&n.length>0){const e=b().map(n,(e=>e.message));for(const n of e)u.error(n,2.5)}else l&&l("modify")},onError:e=>{u.error(o("dialog.ErrorOccurred"))}})):(n=b().omitBy(n,b().isNil),w({variables:n,onCompleted:(e,n)=>{var r;if(b().isEmpty(null===e||void 0===e||null===(r=e.create_container_registry_node)||void 0===r?void 0:r.container_registry))u.error(o("dialog.ErrorOccurred"));else if(n&&(null===n||void 0===n?void 0:n.length)>0){const e=b().map(n,(e=>e.message));for(const n of e)u.error(n,2.5)}else l&&l("create")},onError(e){u.error(o("dialog.ErrorOccurred"))}}))})).catch((e=>{}))};return(0,x.jsx)(c.A,{title:o(h?"registry.ModifyRegistry":"registry.AddRegistry"),okText:o(h?"button.Save":"button.Add"),confirmLoading:R||S,onOk:()=>{var e;null===(e=d.current)||void 0===e||e.validateFields().then((e=>{b().includes(null===e||void 0===e?void 0:e.type,"harbor")&&(b().isEmpty(e.username)||(h?e.isChangedPassword&&b().isEmpty(e.password):b().isEmpty(e.password)))?m.confirm({title:o("button.Confirm"),content:o("registry.ConfirmNoUserName"),onOk:()=>{F()}}):F()})).catch((()=>{}))},...s,destroyOnClose:!0,children:(0,x.jsxs)(p.A,{ref:d,layout:"vertical",requiredMark:"optional",initialValues:h?{...h}:{type:"docker",project:"library"},preserve:!1,children:[h&&(0,x.jsx)(g.A,{name:"row_id",value:h.row_id}),(0,x.jsx)(p.A.Item,{label:o("registry.RegistryName"),name:"registry_name",required:!0,rules:[{required:!0,message:o("registry.DescRegistryNameIsEmpty"),pattern:new RegExp("^.+$")},{type:"string",max:50,message:o("maxLength.50chars")}],children:(0,x.jsx)(f.A,{disabled:!!h,value:(null===h||void 0===h?void 0:h.registry_name)||void 0})}),(0,x.jsx)(p.A.Item,{name:"url",label:o("registry.RegistryURL"),required:!0,rules:[{required:!0},{validator:(e,n)=>{if(n){if(!n.startsWith("http://")&&!n.startsWith("https://"))return Promise.reject(o("registry.DescURLStartString"));try{new URL(n)}catch(r){return Promise.reject(o("registry.DescURLFormat"))}}return Promise.resolve()}},{type:"string",max:512,message:o("maxLength.512chars")}],children:(0,x.jsx)(f.A,{})}),(0,x.jsx)(p.A.Item,{noStyle:!0,shouldUpdate:(e,n)=>b().isEmpty(null===e||void 0===e?void 0:e.password)!==b().isEmpty(null===n||void 0===n?void 0:n.password),children:e=>{let{validateFields:n,getFieldValue:r}=e;return n(["username"]),(0,x.jsx)(p.A.Item,{name:"username",label:o("registry.Username"),rules:[{required:!b().isEmpty(r("password"))},{type:"string",max:255,message:o("maxLength.255chars")}],children:(0,x.jsx)(f.A,{})})}}),(0,x.jsxs)(p.A.Item,{label:o("registry.Password"),children:[(0,x.jsx)(p.A.Item,{noStyle:!0,shouldUpdate:(e,n)=>e.isChangedPassword!==n.isChangedPassword,children:e=>{let{getFieldValue:n}=e;return(0,x.jsx)(p.A.Item,{noStyle:!0,name:"password",children:(0,x.jsx)(f.A.Password,{disabled:!b().isEmpty(h)&&!n("isChangedPassword")})})}}),!b().isEmpty(h)&&(0,x.jsx)(p.A.Item,{noStyle:!0,name:"isChangedPassword",valuePropName:"checked",children:(0,x.jsx)(k.A,{onChange:e=>{var n;e.target.checked||(null===(n=d.current)||void 0===n||n.setFieldValue("password",""))},children:o("webui.menu.ChangePassword")})})]}),(0,x.jsx)(p.A.Item,{name:"type",label:o("registry.RegistryType"),required:!0,rules:[{required:!0,message:o("registry.PleaseSelectOption")}],children:(0,x.jsx)(v.A,{options:[{value:"docker"},{value:"harbor"},{value:"harbor2"}],onChange:e=>{var n,r;"docker"===e&&(null===(n=d.current)||void 0===n||n.setFieldValue("project","library"),null===(r=d.current)||void 0===r||r.validateFields(["project"]))}})}),(0,x.jsx)(p.A.Item,{shouldUpdate:(e,n)=>(null===e||void 0===e?void 0:e.type)!==(null===n||void 0===n?void 0:n.type),noStyle:!0,children:e=>{let{getFieldValue:n}=e;return(0,x.jsx)(p.A.Item,{name:"project",label:o("registry.ProjectName"),required:!0,rules:[{required:!0,message:o("registry.ProjectNameIsRequired")},{type:"string",max:255,message:o("maxLength.255chars")}],children:(0,x.jsx)(f.A,{disabled:"docker"===n("type"),allowClear:!0})})}})]})})};var R,j,S,F=r(89130),L=r(30957),N=r(81850),V=r(64703),K=r(84197),T=r(40567),E=r(4342),M=r(44954),$=r(53566),I=r(55731),D=r(55429),q=r(50868),P=r(15934),O=r(15480),U=r(33789),B=r(60822),z=r(77731),Q=r(85690);const Y=e=>{var n;let{style:a}=e;const i=(0,s.CX)(),[t,g]=(0,s.Tw)("initial-fetch"),[k,v]=(0,_.useTransition)(),h=(0,u.b)(),{message:Y}=y.A.useApp(),{upsertNotification:H}=(0,d.js)(),[W,X]=(0,_.useTransition)(),[G,J]=(0,_.useTransition)(),[Z,ee]=(0,_.useState)(),[ne,{toggle:re}]=(0,I.A)(),{baiPaginationOption:ae,tablePaginationOption:ie,setTablePaginationOption:te}=(0,o.w4)({current:1,pageSize:20}),[le,se]=(0,_.useState)(),{container_registry_nodes:oe,domain:de}=(0,C.useLazyLoadQuery)(void 0!==R?R:R=r(23680),{domain:i._config.domainName,filter:Z,order:le,first:ae.limit,offset:ae.offset},{fetchPolicy:"store-and-network",fetchKey:t}),ue=b().map(null===oe||void 0===oe?void 0:oe.edges,"node"),[ce,me]=(0,C.useMutation)(void 0!==j?j:j=r(42308)),[ge,ye]=(0,C.useMutation)(void 0!==S?S:S=r(89703)),{t:pe}=(0,A.Bd)(),{token:fe}=q.A.useToken(),[ke,ve]=(0,_.useState)(),[he,be]=(0,_.useState)(),[_e,Ae]=(0,_.useState)(""),[Ce,xe]=(0,_.useState)(!1),[we,Re]=(0,_.useState)(),je=[{key:"registry_name",title:pe("registry.RegistryName"),dataIndex:"registry_name",sorter:!0},{key:"url",title:pe("registry.RegistryURL"),dataIndex:"url"},{key:"type",title:pe("registry.Type"),dataIndex:"type"},{key:"project",title:pe("registry.Project"),dataIndex:"project",render:e=>(0,x.jsx)(P.A,{children:e||""},e||"")},{key:"username",title:pe("registry.Username"),dataIndex:"username"},{key:"password",title:pe("registry.Password"),dataIndex:"password"},{key:"enabled",title:pe("general.Enabled"),render:(e,n)=>{const r=b().includes(null===de||void 0===de?void 0:de.allowed_docker_registries,n.registry_name);return(0,x.jsx)(O.A,{checked:we===n.id+t?!r:r,disabled:k||ye,loading:(k||ye)&&we===n.id+t,onChange:e=>{if(!b().isString(n.registry_name))return;let r=b().clone((null===de||void 0===de?void 0:de.allowed_docker_registries)||[]);e?r.push(n.registry_name):r=b().without(r,n.registry_name),Re(n.id+t),ge({variables:{domain:i._config.domainName,allowed_docker_registries:r},onCompleted:(n,r)=>{var a;if(null!==n&&void 0!==n&&null!==(a=n.modify_domain)&&void 0!==a&&a.ok){if(r&&(null===r||void 0===r?void 0:r.length)>0){const e=b().map(r,(e=>e.message));for(const n of e)Y.error(n,2.5)}else v((()=>{g()}));Y.info({key:"registry-enabled",content:pe(e?"registry.RegistryTurnedOn":"registry.RegistryTurnedOff")})}else{var i;Y.error(null===n||void 0===n||null===(i=n.modify_domain)||void 0===i?void 0:i.msg)}}})}})}},{title:pe("general.Control"),fixed:"right",render:(e,n,r)=>(0,x.jsxs)(F.A,{children:[(0,x.jsx)(U.A,{title:pe("button.Edit"),children:(0,x.jsx)(B.Ay,{size:"large",style:{color:fe.colorInfo},type:"text",icon:(0,x.jsx)(N.A,{}),onClick:()=>{ve(n)}})}),(0,x.jsx)(U.A,{title:pe("button.Delete"),children:(0,x.jsx)(B.Ay,{size:"large",danger:!0,type:"text",icon:(0,x.jsx)(V.A,{}),onClick:()=>{be(n)}})}),(0,x.jsx)(U.A,{title:pe("maintenance.RescanImages"),children:(0,x.jsx)(B.Ay,{size:"large",type:"text",icon:(0,x.jsx)(K.A,{onClick:()=>{n.registry_name&&(async e=>{const n=H({message:`${e} ${pe("maintenance.RescanImages")}`,description:pe("registry.UpdatingRegistryInfo"),open:!0,backgroundTask:{status:"pending"},duration:0});i.maintenance.rescan_images(e).then((e=>{let{rescan_images:r}=e;r.ok?H({key:n,backgroundTask:{status:"pending",percent:0,taskId:r.task_id,statusDescriptions:{pending:pe("registry.RescanImages"),resolved:pe("registry.RegistryUpdateFinished"),rejected:pe("registry.RegistryUpdateFailed")}}}):H({key:n,backgroundTask:{status:"rejected"},duration:1})})).catch((e=>{console.log(e),H({key:n,backgroundTask:{status:"rejected"},duration:1}),e&&e.message&&(globalThis.lablupNotification.text=h.relieve(e.title),globalThis.lablupNotification.detail=e.message,globalThis.lablupNotification.show(!0,e))}))})(n.registry_name)}})})})]})}],[Se,Fe]=(0,D.A)("backendaiwebui.ContainerRegistryList.displayedColumnKeys",{defaultValue:b().map(je,(e=>b().toString(e.key)))});return(0,x.jsxs)(F.A,{direction:"column",align:"stretch",style:{flex:1,...a},children:[(0,x.jsxs)(F.A,{direction:"row",justify:"end",gap:"sm",style:{padding:fe.paddingContentVertical,paddingLeft:fe.paddingContentHorizontalSM,paddingRight:fe.paddingContentHorizontalSM},children:[(0,x.jsx)(m.A,{filterProperties:[{key:"registry_name",propertyLabel:pe("registry.RegistryName"),type:"string"}],value:Z,onChange:e=>{X((()=>{ee(e)}))}}),(0,x.jsx)(U.A,{title:pe("button.Refresh"),children:(0,x.jsx)(B.Ay,{loading:k,icon:(0,x.jsx)(T.A,{}),onClick:()=>{v((()=>{g()}))}})}),(0,x.jsx)(B.Ay,{type:"primary",icon:(0,x.jsx)(E.A,{}),onClick:()=>{xe(!0)},children:pe("registry.AddRegistry")})]}),(0,x.jsx)(z.A,{rowKey:e=>e.id,scroll:{x:"max-content"},showSorterTooltip:!1,pagination:{pageSize:ie.pageSize,showSizeChanger:!0,total:null!==(n=null===oe||void 0===oe?void 0:oe.count)&&void 0!==n?n:0,current:ie.current,showTotal:(e,n)=>`${n[0]}-${n[1]} of ${e} items`,pageSizeOptions:["10","20","50"],style:{marginRight:fe.marginXS}},onChange:(e,n,r)=>{let{pageSize:a,current:i}=e;J((()=>{b().isNumber(i)&&b().isNumber(a)&&te({current:i,pageSize:a}),se((0,l.Wh)(r))}))},loading:{spinning:G||W,indicator:(0,x.jsx)(M.A,{})},dataSource:(0,l.tS)(ue),columns:b().filter(je,(e=>b().includes(Se,b().toString(e.key))))}),(0,x.jsx)(w,{containerRegistryFrgmt:ke,open:!!ke||Ce,onOk:e=>{"create"===e?Y.info({key:"registry-added",content:pe("registry.RegistrySuccessfullyAdded")}):"modify"===e&&Y.info({key:"registry-modified",content:pe("registry.RegistrySuccessfullyModified")}),g(),ve(null),xe(!1)},onCancel:()=>{ve(null),xe(!1)},centered:!1}),(0,x.jsx)(c.A,{title:(0,x.jsxs)(x.Fragment,{children:[(0,x.jsx)($.A,{style:{color:fe.colorWarning}})," ",pe("dialog.warning.CannotBeUndone")]}),okText:pe("button.Delete"),okButtonProps:{danger:!0,disabled:_e!==(null===he||void 0===he?void 0:he.registry_name)},onOk:()=>{he?ce({variables:{id:he.id},onCompleted:(e,n)=>{n?(be(null),Y.error({key:"registry-deletion-failed",content:pe("dialog.ErrorOccurred")})):(v((()=>{g()})),Y.info({key:"registry-deleted",content:pe("registry.RegistrySuccessfullyDeleted")}),be(null))},onError:e=>{Y.error({key:"registry-deletion-failed",content:pe("dialog.ErrorOccurred")})}}):be(null)},confirmLoading:me,onCancel:()=>{be(null)},destroyOnClose:!0,open:!!he,children:(0,x.jsxs)(F.A,{direction:"column",align:"stretch",gap:"sm",style:{marginTop:fe.marginMD},children:[(0,x.jsxs)(Q.A.Text,{children:[(0,x.jsx)(Q.A.Text,{code:!0,children:null===he||void 0===he?void 0:he.registry_name})," ",pe("registry.TypeRegistryNameToDelete")]}),(0,x.jsx)(p.A,{children:(0,x.jsx)(p.A.Item,{name:"confirmText",rules:[{required:!0,message:pe("registry.HostnameDoesNotMatch"),validator:()=>_e===(null===he||void 0===he?void 0:he.registry_name)?Promise.resolve():Promise.reject()}],children:(0,x.jsx)(f.A,{autoComplete:"off",value:_e,onChange:e=>Ae(e.target.value)})})})]})}),(0,x.jsx)(F.A,{justify:"end",style:{padding:fe.paddingXXS},children:(0,x.jsx)(B.Ay,{type:"text",icon:(0,x.jsx)(N.A,{}),onClick:()=>{re()}})}),(0,x.jsx)(L.A,{open:ne,onRequestClose:e=>{(null===e||void 0===e?void 0:e.selectedColumnKeys)&&Fe(null===e||void 0===e?void 0:e.selectedColumnKeys),re()},columns:je,displayedColumnKeys:Se||[]})]})}},69144:(e,n,r)=>{r.d(n,{A:()=>l});var a=r(23702),i=r(43373),t=r(73689);const l=e=>{let{value:n,...r}=e;const l=a.A.useFormInstance();return(0,i.useEffect)((()=>{l.setFieldValue(r.name,n)}),[n,l,r.name]),(0,t.jsx)(a.A.Item,{...r,hidden:!0})}},52777:(e,n,r)=>{r.r(n),r.d(n,{default:()=>i});const a=function(){var e={defaultValue:null,kind:"LocalArgument",name:"is_global"},n={defaultValue:null,kind:"LocalArgument",name:"password"},r={defaultValue:null,kind:"LocalArgument",name:"project"},a={defaultValue:null,kind:"LocalArgument",name:"registry_name"},i={defaultValue:null,kind:"LocalArgument",name:"ssl_verify"},t={defaultValue:null,kind:"LocalArgument",name:"type"},l={defaultValue:null,kind:"LocalArgument",name:"url"},s={defaultValue:null,kind:"LocalArgument",name:"username"},o=[{alias:null,args:[{kind:"Variable",name:"is_global",variableName:"is_global"},{kind:"Variable",name:"password",variableName:"password"},{kind:"Variable",name:"project",variableName:"project"},{kind:"Variable",name:"registry_name",variableName:"registry_name"},{kind:"Variable",name:"ssl_verify",variableName:"ssl_verify"},{kind:"Variable",name:"type",variableName:"type"},{kind:"Variable",name:"url",variableName:"url"},{kind:"Variable",name:"username",variableName:"username"}],concreteType:"CreateContainerRegistryNode",kind:"LinkedField",name:"create_container_registry_node",plural:!1,selections:[{alias:null,args:null,concreteType:"ContainerRegistryNode",kind:"LinkedField",name:"container_registry",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,n,r,a,i,t,l,s],kind:"Fragment",metadata:null,name:"ContainerRegistryEditorModalCreateMutation",selections:o,type:"Mutations",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[a,t,l,e,n,r,i,s],kind:"Operation",name:"ContainerRegistryEditorModalCreateMutation",selections:o},params:{cacheID:"7458f3eef662a95974ab0aac3461ac89",id:null,metadata:{},name:"ContainerRegistryEditorModalCreateMutation",operationKind:"mutation",text:"mutation ContainerRegistryEditorModalCreateMutation(\n  $registry_name: String!\n  $type: ContainerRegistryTypeField!\n  $url: String!\n  $is_global: Boolean\n  $password: String\n  $project: String\n  $ssl_verify: Boolean\n  $username: String\n) {\n  create_container_registry_node(registry_name: $registry_name, type: $type, url: $url, is_global: $is_global, password: $password, project: $project, ssl_verify: $ssl_verify, username: $username) {\n    container_registry {\n      id\n    }\n  }\n}\n"}}}();a.hash="70687206bb7ec96287917f8064081993";const i=a},49766:(e,n,r)=>{r.r(n),r.d(n,{default:()=>i});const a={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"ContainerRegistryEditorModalFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"url",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"project",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ssl_verify",storageKey:null}],type:"ContainerRegistryNode",abstractKey:null,hash:"888dea41eb402b791928d6de6dfb52be"},i=a},447:(e,n,r)=>{r.r(n),r.d(n,{default:()=>i});const a=function(){var e={defaultValue:null,kind:"LocalArgument",name:"id"},n={defaultValue:null,kind:"LocalArgument",name:"is_global"},r={defaultValue:null,kind:"LocalArgument",name:"password"},a={defaultValue:null,kind:"LocalArgument",name:"project"},i={defaultValue:null,kind:"LocalArgument",name:"registry_name"},t={defaultValue:null,kind:"LocalArgument",name:"ssl_verify"},l={defaultValue:null,kind:"LocalArgument",name:"type"},s={defaultValue:null,kind:"LocalArgument",name:"url"},o={defaultValue:null,kind:"LocalArgument",name:"username"},d=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"},{kind:"Variable",name:"is_global",variableName:"is_global"},{kind:"Variable",name:"password",variableName:"password"},{kind:"Variable",name:"project",variableName:"project"},{kind:"Variable",name:"registry_name",variableName:"registry_name"},{kind:"Variable",name:"ssl_verify",variableName:"ssl_verify"},{kind:"Variable",name:"type",variableName:"type"},{kind:"Variable",name:"url",variableName:"url"},{kind:"Variable",name:"username",variableName:"username"}],concreteType:"ModifyContainerRegistryNode",kind:"LinkedField",name:"modify_container_registry_node",plural:!1,selections:[{alias:null,args:null,concreteType:"ContainerRegistryNode",kind:"LinkedField",name:"container_registry",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,n,r,a,i,t,l,s,o],kind:"Fragment",metadata:null,name:"ContainerRegistryEditorModalModifyMutation",selections:d,type:"Mutations",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,i,l,s,n,r,a,t,o],kind:"Operation",name:"ContainerRegistryEditorModalModifyMutation",selections:d},params:{cacheID:"f361ca0b011bec4b168e98868073a224",id:null,metadata:{},name:"ContainerRegistryEditorModalModifyMutation",operationKind:"mutation",text:"mutation ContainerRegistryEditorModalModifyMutation(\n  $id: String!\n  $registry_name: String\n  $type: ContainerRegistryTypeField\n  $url: String\n  $is_global: Boolean\n  $password: String\n  $project: String\n  $ssl_verify: Boolean\n  $username: String\n) {\n  modify_container_registry_node(id: $id, registry_name: $registry_name, type: $type, url: $url, is_global: $is_global, password: $password, project: $project, ssl_verify: $ssl_verify, username: $username) {\n    container_registry {\n      id\n    }\n  }\n}\n"}}}();a.hash="0a51080ee0af91cd67e9e341b4fd354f";const i=a},42308:(e,n,r)=>{r.r(n),r.d(n,{default:()=>i});const a=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"id"}],n=[{alias:null,args:[{kind:"Variable",name:"id",variableName:"id"}],concreteType:"DeleteContainerRegistryNode",kind:"LinkedField",name:"delete_container_registry_node",plural:!1,selections:[{alias:null,args:null,concreteType:"ContainerRegistryNode",kind:"LinkedField",name:"container_registry",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"ContainerRegistryListDeleteMutation",selections:n,type:"Mutations",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"ContainerRegistryListDeleteMutation",selections:n},params:{cacheID:"93b0914bb07fb84611809dc34af76686",id:null,metadata:{},name:"ContainerRegistryListDeleteMutation",operationKind:"mutation",text:"mutation ContainerRegistryListDeleteMutation(\n  $id: String!\n) {\n  delete_container_registry_node(id: $id) {\n    container_registry {\n      id\n    }\n  }\n}\n"}}}();a.hash="d75e15de7a3ff3cff9778c52f6907ff3";const i=a},89703:(e,n,r)=>{r.r(n),r.d(n,{default:()=>i});const a=function(){var e={defaultValue:null,kind:"LocalArgument",name:"allowed_docker_registries"},n={defaultValue:null,kind:"LocalArgument",name:"domain"},r=[{alias:null,args:[{kind:"Variable",name:"name",variableName:"domain"},{fields:[{kind:"Variable",name:"allowed_docker_registries",variableName:"allowed_docker_registries"}],kind:"ObjectValue",name:"props"}],concreteType:"ModifyDomain",kind:"LinkedField",name:"modify_domain",plural:!1,selections:[{alias:null,args:null,kind:"ScalarField",name:"ok",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"msg",storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:[e,n],kind:"Fragment",metadata:null,name:"ContainerRegistryListDomainMutation",selections:r,type:"Mutations",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[n,e],kind:"Operation",name:"ContainerRegistryListDomainMutation",selections:r},params:{cacheID:"5ea7ebdd79d15e15b23a9fb2d8568d34",id:null,metadata:{},name:"ContainerRegistryListDomainMutation",operationKind:"mutation",text:"mutation ContainerRegistryListDomainMutation(\n  $domain: String!\n  $allowed_docker_registries: [String]!\n) {\n  modify_domain(name: $domain, props: {allowed_docker_registries: $allowed_docker_registries}) {\n    ok\n    msg\n  }\n}\n"}}}();a.hash="647ec7cdf3bcffc8cc1d8cd3cced159f";const i=a},23680:(e,n,r)=>{r.r(n),r.d(n,{default:()=>i});const a=function(){var e={defaultValue:null,kind:"LocalArgument",name:"domain"},n={defaultValue:null,kind:"LocalArgument",name:"filter"},r={defaultValue:null,kind:"LocalArgument",name:"first"},a={defaultValue:null,kind:"LocalArgument",name:"offset"},i={defaultValue:null,kind:"LocalArgument",name:"order"},t=[{kind:"Variable",name:"filter",variableName:"filter"},{kind:"Variable",name:"first",variableName:"first"},{kind:"Variable",name:"offset",variableName:"offset"},{kind:"Variable",name:"order",variableName:"order"}],l={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"registry_name",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"url",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"type",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"project",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"username",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"password",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"ssl_verify",storageKey:null},f={alias:null,args:null,kind:"ScalarField",name:"count",storageKey:null},k={alias:null,args:[{kind:"Variable",name:"name",variableName:"domain"}],concreteType:"Domain",kind:"LinkedField",name:"domain",plural:!1,selections:[d,{alias:null,args:null,kind:"ScalarField",name:"allowed_docker_registries",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:[e,n,r,a,i],kind:"Fragment",metadata:null,name:"ContainerRegistryListQuery",selections:[{alias:null,args:t,concreteType:"ContainerRegistryConnection",kind:"LinkedField",name:"container_registry_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ContainerRegistryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ContainerRegistryNode",kind:"LinkedField",name:"node",plural:!1,selections:[{args:null,kind:"FragmentSpread",name:"ContainerRegistryEditorModalFragment"},l,s,o,d,u,c,m,g,y,p],storageKey:null}],storageKey:null},f],storageKey:null},k],type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:[e,n,i,r,a],kind:"Operation",name:"ContainerRegistryListQuery",selections:[{alias:null,args:t,concreteType:"ContainerRegistryConnection",kind:"LinkedField",name:"container_registry_nodes",plural:!1,selections:[{alias:null,args:null,concreteType:"ContainerRegistryEdge",kind:"LinkedField",name:"edges",plural:!0,selections:[{alias:null,args:null,concreteType:"ContainerRegistryNode",kind:"LinkedField",name:"node",plural:!1,selections:[l,s,d,o,u,c,m,g,p,y],storageKey:null}],storageKey:null},f],storageKey:null},k]},params:{cacheID:"e9dd4625e53cac51f451db82c9ce44c1",id:null,metadata:{},name:"ContainerRegistryListQuery",operationKind:"query",text:'query ContainerRegistryListQuery(\n  $domain: String!\n  $filter: String\n  $order: String\n  $first: Int\n  $offset: Int\n) {\n  container_registry_nodes(filter: $filter, order: $order, first: $first, offset: $offset) @since(version: "24.09.0") {\n    edges {\n      node {\n        ...ContainerRegistryEditorModalFragment\n        id\n        row_id\n        registry_name\n        name\n        url\n        type\n        project\n        username\n        password\n        ssl_verify\n      }\n    }\n    count\n  }\n  domain(name: $domain) {\n    name\n    allowed_docker_registries\n  }\n}\n\nfragment ContainerRegistryEditorModalFragment on ContainerRegistryNode {\n  id\n  row_id\n  name\n  registry_name\n  url\n  type\n  project\n  username\n  ssl_verify\n}\n'}}}();a.hash="83d2445a2d783eb91f99f02f22559918";const i=a},34357:(e,n,r)=>{r.d(n,{b:()=>l});var a=r(56762);const i={"Cannot read property 'map' of null":"error.APINotSupported","TypeError: NetworkError when attempting to fetch resource.":"error.NetworkConnectionFailed","Login failed. Check login information.":"error.LoginFailed","User credential mismatch.":"error.LoginFailed","Authentication failed. Check information and manager status.":"error.AuthenticationFailed","Too many failed login attempts":"error.TooManyLoginFailures","server responded failure: 400 Bad Request - The virtual folder already exists with the same name.":"error.VirtualFolderAlreadyExist","400 Bad Request - The virtual folder already exists with the same name.":"error.VirtualFolderAlreadyExist","server responded failure: 400 Bad Request - One of your accessible vfolders already has the name you requested.":"error.VirtualFolderAlreadyExist","server responded failure: 400 Bad Request - You cannot create more vfolders.":"error.MaximumVfolderCreation","server responded failure: 400 Bad Request - Missing or invalid API parameters. (You cannot create more vfolders.)":"error.MaximumVfolderCreation","server responded failure: 400 Bad Request - Cannot change the options of a vfolder that is not owned by myself.":"error.CannotChangeVirtualFolderOption","server responded failure: 403 Forbidden - Cannot share private dot-prefixed vfolders.":"error.CannotSharePrivateAutomountFolder","server responded failure: 404 Not Found - No such vfolder invitation.":"error.FolderSharingNotAvailableToUser","server responded failure: 404 Not Found - No such user.":"error.FolderSharingNotAvailableToUser","server responded failure: 412 Precondition Failed - You have reached your resource limit.":"error.ReachedResourceLimit","Cannot read property 'split' of undefined":"error.UserHasNoGroup"},t={"\\w*not found matched token with email\\w*":"error.InvalidSignupToken","\\w*Access key not found\\w*":"error.LoginInformationMismatch","\\w*401 Unauthorized - Credential/signature mismatch\\w*":"error.LoginInformationMismatch",'integrity error: duplicate key value violates unique constraint "pk_resource_presets"[\\n]DETAIL:  Key \\(name\\)=\\([\\w]+\\) already exists.[\\n]':"error.ResourcePolicyAlreadyExist",'integrity error: duplicate key value violates unique constraint "pk_scaling_groups"[\\n]DETAIL:  Key \\(name\\)=\\([\\w]+\\) already exists.[\\n]':"error.ScalingGroupAlreadyExist",'integrity error: duplicate key value violates unique constraint "uq_users_username"[\\n]DETAIL:  Key \\(username\\)=\\([\\w]+\\) already exists.[\\n]':"error.UserNameAlreadyExist","server responded failure: 400 Bad Request - Missing or invalid API parameters. (Your resource quota is exceeded. (cpu=24 mem=512g cuda.shares=80))":"error.ResourceLimitExceed",'\\w*Key \\(name\\)=\\(.+\\) is still referenced from table "keypairs"\\.\\w*':"error.ResourcePolicyStillReferenced","Your resource request is smaller than the minimum required by the image. (\\w*)":"error.SmallerResourceThenImageRequires"},l=()=>{const{t:e}=(0,a.Bd)();return{relieve:n=>{if("undefined"===typeof n)return void 0===globalThis.backendaiclient||null===globalThis.backendaiclient?"_DISCONNECTED":"Problem occurred.";if(!0===globalThis.backendaiwebui.debug)return n;if({}.hasOwnProperty.call(i,n))return e(i[n]);for(const r of Object.keys(t))if(RegExp(r).test(n))return e(t[r]);return n}}}},84197:(e,n,r)=>{r.d(n,{A:()=>o});var a=r(40991),i=r(43373);const t={icon:{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M168 504.2c1-43.7 10-86.1 26.9-126 17.3-41 42.1-77.7 73.7-109.4S337 212.3 378 195c42.4-17.9 87.4-27 133.9-27s91.5 9.1 133.8 27A341.5 341.5 0 01755 268.8c9.9 9.9 19.2 20.4 27.8 31.4l-60.2 47a8 8 0 003 14.1l175.7 43c5 1.2 9.9-2.6 9.9-7.7l.8-180.9c0-6.7-7.7-10.5-12.9-6.3l-56.4 44.1C765.8 155.1 646.2 92 511.8 92 282.7 92 96.3 275.6 92 503.8a8 8 0 008 8.2h60c4.4 0 7.9-3.5 8-7.8zm756 7.8h-60c-4.4 0-7.9 3.5-8 7.8-1 43.7-10 86.1-26.9 126-17.3 41-42.1 77.8-73.7 109.4A342.45 342.45 0 01512.1 856a342.24 342.24 0 01-243.2-100.8c-9.9-9.9-19.2-20.4-27.8-31.4l60.2-47a8 8 0 00-3-14.1l-175.7-43c-5-1.2-9.9 2.6-9.9 7.7l-.7 181c0 6.7 7.7 10.5 12.9 6.3l56.4-44.1C258.2 868.9 377.8 932 512.2 932c229.2 0 415.5-183.7 419.8-411.8a8 8 0 00-8-8.2z"}}]},name:"sync",theme:"outlined"};var l=r(64098),s=function(e,n){return i.createElement(l.A,(0,a.A)({},e,{ref:n,icon:t}))};const o=i.forwardRef(s)}}]);
//# sourceMappingURL=4703.cb1c7259.chunk.js.map