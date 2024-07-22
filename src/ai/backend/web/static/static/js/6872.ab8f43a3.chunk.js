"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[6872],{1225:(e,l,n)=>{n.r(l),n.d(l,{default:()=>R});var a=n(30032),i=n(83468),r=n(57857),o=n(34103),s=n(5516),t=n(29871),d=n(36009),u=n(85676),c=n(35832),m=n(44183),g=n(25575),v=n(96495),p=n(78074),_=n(45901),y=n.n(_),h=n(76998),S=n(23446);const k=e=>{var l,n;let{filter:o,autoSelectDefault:s,valuePropName:t="name",...d}=e;const u=(0,v.hd)(),c=(0,a.QE)(),[m,g]=(0,i.Tw)("first"),{data:_}=(0,r.n)({queryKey:["VFolderSelectQuery",m],queryFn:()=>{const e=new URLSearchParams;return e.set("group_id",u.id),c({method:"GET",url:"/folders?".concat(e.toString())})},staleTime:0}),k=o?y().filter(_,o):_,f=y().first(k)?{label:null===(l=y().first(k))||void 0===l?void 0:l.name,value:null===(n=y().first(k))||void 0===n?void 0:n[t]}:void 0;return(0,h.useEffect)((()=>{var e;s&&f&&(null===(e=d.onChange)||void 0===e||e.call(d,f.value,f))}),[s]),(0,S.jsx)(p.A,{showSearch:!0,...d,onDropdownVisibleChange:e=>{e&&(0,h.startTransition)((()=>{g()}))},options:y().map(k,(e=>({label:null===e||void 0===e?void 0:e.name,value:null===e||void 0===e?void 0:e[t]})))})};var f=n(22089),F=n(58168);const b={icon:{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M872 474H152c-4.4 0-8 3.6-8 8v60c0 4.4 3.6 8 8 8h720c4.4 0 8-3.6 8-8v-60c0-4.4-3.6-8-8-8z"}}]},name:"minus",theme:"outlined"};var K=n(13410),x=function(e,l){return h.createElement(K.A,(0,F.A)({},e,{ref:l,icon:b}))};const j=h.forwardRef(x);var A,T,C=n(50840),M=n(78969),w=n(7121),I=n(29475),D=n(63284),L=n(82745),N=n(35184),P=n(6932),V=n(77678),z=n(3606),E=n(58346);const O=h.lazy((()=>n.e(3356).then(n.bind(n,63356)))),R=e=>{var l,v,_,F,b,K,x,R,q,U,J,G,Q;let{endpointFrgmt:$=null}=e;const{token:B}=C.A.useToken(),{message:W}=M.A.useApp(),{t:H}=(0,V.Bd)(),[{model:X}]=(0,E.useQueryParams)({model:E.StringParam}),Z=(0,i.f0)(),Y=(0,i.CX)(),ee=(0,a.QE)(),le=(0,i.eZ)(),[ne,ae]=(0,h.useState)(!1),[ie]=w.A.useForm(),re=(0,z.useFragment)(void 0!==A?A:A=n(79170),$),{data:oe}=(0,r.n)({queryKey:["baiClient.modelService.runtime.list"],queryFn:()=>Y.isManagerVersionCompatibleWith("24.03.5")?ee({method:"GET",url:"/services/_/runtimes"}):Promise.resolve({runtimes:[{name:"custom",human_readable_name:"Custom (Default)"}]}),staleTime:1e3,suspense:!0}),se=function(){let e=arguments.length>1&&void 0!==arguments[1]?arguments[1]:"";return arguments.length>0&&void 0!==arguments[0]&&arguments[0]&&e&&!y().isEmpty(e)},te=function(){var e,l,n,a,i;let r=arguments.length>0&&void 0!==arguments[0]&&arguments[0],o=arguments.length>1?arguments[1]:void 0;return{image:{name:r?null===(e=o.environments.manual)||void 0===e?void 0:e.split("@")[0]:o.environments.version.split("@")[0],architecture:r?null===(l=o.environments.manual)||void 0===l?void 0:l.split("@")[1]:null===(n=o.environments.image)||void 0===n?void 0:n.architecture,registry:r?null===(a=o.environments.manual)||void 0===a?void 0:a.split("/")[0]:null===(i=o.environments.image)||void 0===i?void 0:i.registry}}},de=function(){var e,l,n,a,i,r;let o=arguments.length>0&&void 0!==arguments[0]&&arguments[0],s=arguments.length>1?arguments[1]:void 0;return{image:o?null===(e=s.environments.manual)||void 0===e?void 0:e.split("@")[0]:"".concat(null===(l=s.environments.image)||void 0===l?void 0:l.registry,"/").concat(null===(n=s.environments.image)||void 0===n?void 0:n.name,":").concat(null===(a=s.environments.image)||void 0===a?void 0:a.tag),architecture:o?null===(i=s.environments.manual)||void 0===i?void 0:i.split("@")[1]:null===(r=s.environments.image)||void 0===r?void 0:r.architecture}},ue=(0,r.E)({mutationFn:e=>{const l={to:e.desiredRoutingCount};return(0,a.hu)({method:"POST",url:"/services/".concat(null===re||void 0===re?void 0:re.endpoint_id,"/scale"),body:l,client:Y})}}),ce=(0,r.E)({mutationFn:e=>{var l;const n={};e.envvars&&e.envvars.forEach((e=>n[e.variable]=e.value));const i={name:e.serviceName,desired_session_count:e.desiredRoutingCount,...de(se(Y._config.allow_manual_image_name_for_session,null===(l=e.environments)||void 0===l?void 0:l.manual),e),runtime_variant:e.runtimeVariant,group:Y.current_group,domain:le,cluster_size:e.cluster_size,cluster_mode:e.cluster_mode,open_to_public:e.openToPublic,config:{model:e.vFolderID,model_version:1,...Y.supports("endpoint-extra-mounts")&&{extra_mounts:y().reduce(e.mounts,((l,n)=>(l[n]={...e.vfoldersAliasMap[n]&&{mount_destination:e.vfoldersAliasMap[n]},type:"bind"},l)),{}),model_definition_path:e.modelDefinitionPath},model_mount_destination:Y.supports("endpoint-extra-mounts")&&""!==e.modelMountDestination?e.modelMountDestination:"/models",environ:n,scaling_group:e.resourceGroup,resources:{cpu:e.resource.cpu.toString(),mem:e.resource.mem,...e.resource.accelerator>0?{[e.resource.acceleratorType]:e.resource.accelerator.toString()}:void 0},resource_opts:{shmem:(0,a.Mh)(e.resource.mem,"4g")>0&&(0,a.Mh)(e.resource.shmem,"1g")<0?"1g":e.resource.shmem}}};return(0,a.hu)({method:"POST",url:"/services",body:i,client:Y})}}),[me]=(0,z.useMutation)(void 0!==T?T:T=n(97115)),[ge,ve]=(0,h.useState)(),pe=re?{serviceName:null===re||void 0===re?void 0:re.name,resourceGroup:null===re||void 0===re?void 0:re.resource_group,desiredRoutingCount:(null===re||void 0===re?void 0:re.desired_session_count)||0,resource:{cpu:parseInt(null===(l=JSON.parse(null===re||void 0===re?void 0:re.resource_slots))||void 0===l?void 0:l.cpu),mem:null===(v=(0,a.Js)((null===(_=JSON.parse(null===re||void 0===re?void 0:re.resource_slots))||void 0===_?void 0:_.mem)+"b","g",3,!0))||void 0===v?void 0:v.numberUnit,shmem:null===(F=(0,a.Js)((null===(b=JSON.parse(null===re||void 0===re?void 0:re.resource_opts))||void 0===b?void 0:b.shmem)||m.t2,"g",3,!0))||void 0===F?void 0:F.numberUnit,...(e=>{if(Object.keys(e).length<=0)return;const l=Object.keys(e)[0];return{acceleratorType:l,accelerator:"string"===typeof e[l]?"cuda.shares"===l?parseFloat(e[l]):parseInt(e[l]):e[l]}})(y().omit(JSON.parse(null===re||void 0===re?void 0:re.resource_slots),["cpu","mem"]))},cluster_mode:"MULTI_NODE"===(null===re||void 0===re?void 0:re.cluster_mode)?"multi-node":"single-node",cluster_size:null===re||void 0===re?void 0:re.cluster_size,openToPublic:null===re||void 0===re?void 0:re.open_to_public,environments:{environment:null===re||void 0===re||null===(K=re.image_object)||void 0===K?void 0:K.name,version:"".concat(null===re||void 0===re||null===(x=re.image_object)||void 0===x?void 0:x.registry,"/").concat(null===re||void 0===re||null===(R=re.image_object)||void 0===R?void 0:R.name,":").concat(null===re||void 0===re||null===(q=re.image_object)||void 0===q?void 0:q.tag,"@").concat(null===re||void 0===re||null===(U=re.image_object)||void 0===U?void 0:U.architecture),image:null===re||void 0===re?void 0:re.image_object},vFolderID:null===re||void 0===re?void 0:re.model,mounts:y().map(null===re||void 0===re?void 0:re.extra_mounts,(e=>{var l;return null===e||void 0===e||null===(l=e.row_id)||void 0===l?void 0:l.replaceAll("-","")})),modelMountDestination:null===re||void 0===re?void 0:re.model_mount_destination,modelDefinitionPath:null===re||void 0===re?void 0:re.model_definition_path,runtimeVariant:null===re||void 0===re||null===(J=re.runtime_variant)||void 0===J?void 0:J.name,envvars:y().map(JSON.parse((null===re||void 0===re?void 0:re.environ)||"{}"),((e,l)=>({variable:l,value:e})))}:{desiredRoutingCount:1,runtimeVariant:"custom",...m.jh,...(null===(G=Y._config)||void 0===G?void 0:G.default_session_environment)&&{environments:{environment:null===(Q=Y._config)||void 0===Q?void 0:Q.default_session_environment}},vFolderID:X||void 0};return(0,S.jsxs)(S.Fragment,{children:[(0,S.jsx)(t.A,{direction:"column",align:"stretch",style:{justifyContent:"revert"},children:(0,S.jsx)(t.A,{direction:"row",gap:"md",align:"start",children:(0,S.jsx)(t.A,{direction:"column",align:"stretch",style:{flex:1,maxWidth:700},wrap:"nowrap",children:(0,S.jsx)(h.Suspense,{fallback:(0,S.jsx)(d.A,{}),children:(0,S.jsx)(w.A,{form:ie,disabled:ce.isLoading,layout:"vertical",labelCol:{span:12},initialValues:pe,requiredMark:"optional",children:(0,S.jsxs)(t.A,{direction:"column",gap:"md",align:"stretch",children:[(0,S.jsxs)(I.A,{children:[(Y.supports("modify-endpoint")||!re)&&(0,S.jsxs)(S.Fragment,{children:[(0,S.jsx)(w.A.Item,{label:H("modelService.ServiceName"),name:"serviceName",rules:[{pattern:/^(?=.{4,24}$)\w[\w.-]*\w$/,message:H("modelService.ServiceNameRule")},{required:!0}],children:(0,S.jsx)(D.A,{disabled:!!re})}),(0,S.jsx)(w.A.Item,{name:"openToPublic",label:H("modelService.OpenToPublic"),valuePropName:"checked",children:(0,S.jsx)(L.A,{disabled:!!re})}),re?(null===re||void 0===re?void 0:re.model)&&(0,S.jsx)(w.A.Item,{name:"vFolderID",label:H("session.launcher.ModelStorageToMount"),required:!0,children:(0,S.jsx)(h.Suspense,{fallback:(0,S.jsx)(N.A.Input,{active:!0}),children:(0,S.jsx)(g.A,{uuid:null===re||void 0===re?void 0:re.model})})}):(0,S.jsx)(w.A.Item,{name:"vFolderID",label:H("session.launcher.ModelStorageToMount"),rules:[{required:!0}],children:(0,S.jsx)(k,{filter:e=>"model"===e.usage_mode&&"ready"===e.status,valuePropName:"id",autoSelectDefault:!X,disabled:!!re})}),Y.supports("endpoint-runtime-variant")?(0,S.jsx)(w.A.Item,{name:"runtimeVariant",required:!0,label:H("modelService.RuntimeVariant"),children:(0,S.jsx)(p.A,{defaultActiveFirstOption:!0,showSearch:!0,options:y().map(null===oe||void 0===oe?void 0:oe.runtimes,(e=>({value:e.name,label:e.human_readable_name})))})}):null,(0,S.jsx)(w.A.Item,{dependencies:["runtimeVariant"],noStyle:!0,children:e=>{let{getFieldValue:l}=e;return"custom"===l("runtimeVariant")&&Y.supports("endpoint-extra-mounts")?(0,S.jsx)(S.Fragment,{children:(0,S.jsxs)(t.A,{direction:"row",gap:"xxs",align:"stretch",justify:"between",children:[(0,S.jsx)(w.A.Item,{name:"modelMountDestination",label:H("modelService.ModelMountDestination"),style:{width:"50%"},labelCol:{style:{flex:1}},children:(0,S.jsx)(D.A,{allowClear:!0,placeholder:"/models",disabled:!!re})}),(0,S.jsx)(j,{style:{fontSize:B.fontSizeXL,color:B.colorTextDisabled},rotate:290}),(0,S.jsx)(w.A.Item,{name:"modelDefinitionPath",label:H("modelService.ModelDefinitionPath"),style:{width:"50%"},labelCol:{style:{flex:1}},children:(0,S.jsx)(D.A,{allowClear:!0,placeholder:null!==re&&void 0!==re&&re.model_definition_path?null===re||void 0===re?void 0:re.model_definition_path:"model-definition.yaml"})})]})}):null}}),Y.supports("endpoint-extra-mounts")?(0,S.jsx)(S.Fragment,{children:(0,S.jsx)(w.A.Item,{noStyle:!0,dependencies:["vFolderID"],children:e=>{let{getFieldValue:l}=e;return(0,S.jsx)(f.A,{rowKey:"id",label:H("modelService.AdditionalMounts"),filter:e=>{var n;return e.name!==l("vFolderID")&&"ready"===e.status&&"model"!==e.usage_mode&&!(null!==(n=e.name)&&void 0!==n&&n.startsWith("."))},tableProps:{size:"small"}})}})}):null]}),(0,S.jsx)(w.A.Item,{label:H("modelService.DesiredRoutingCount"),name:"desiredRoutingCount",rules:[{required:!0,min:0,max:10,type:"number"}],children:(0,S.jsx)(c.A,{min:0,max:10,inputNumberProps:{addonAfter:"#"},step:1})}),(Y.supports("modify-endpoint")||!re)&&(0,S.jsxs)(S.Fragment,{children:[(0,S.jsx)(u.A,{}),(0,S.jsx)(m.Ay,{}),(0,S.jsx)(w.A.Item,{label:H("session.launcher.EnvironmentVariable"),children:(0,S.jsx)(s.A,{name:"envvars",formItemProps:{validateTrigger:["onChange","onBlur"]}})})]})]}),(0,S.jsxs)(t.A,{direction:"row",justify:"between",align:"end",gap:"xs",children:[(0,S.jsx)(t.A,{children:Y.supports("model-service-validation")?(0,S.jsx)(P.Ay,{onClick:()=>{ie.validateFields().then((e=>{ve(e),ae(!0)})).catch((e=>{console.log(e.message),W.error(H("modelService.FormValidationFailed"))}))},children:H("modelService.Validate")}):null}),(0,S.jsx)(t.A,{gap:"sm",children:(0,S.jsx)(P.Ay,{type:"primary",onClick:()=>{ie.validateFields().then((e=>{if(re)if(Y.supports("modify-endpoint")){var l;const n={endpoint_id:(null===re||void 0===re?void 0:re.endpoint_id)||"",props:{resource_slots:JSON.stringify({cpu:e.resource.cpu,mem:e.resource.mem,...e.resource.accelerator>0?{[e.resource.acceleratorType]:e.resource.accelerator}:void 0}),resource_opts:JSON.stringify({shmem:e.resource.shmem}),cluster_mode:"single-node"===e.cluster_mode?"SINGLE_NODE":"MULTI_NODE",cluster_size:e.cluster_size,desired_session_count:e.desiredRoutingCount,...te(se(Y._config.allow_manual_image_name_for_session,null===(l=e.environments)||void 0===l?void 0:l.manual),e),extra_mounts:(e.mounts||[]).map((l=>({vfolder_id:l,...e.vfoldersAliasMap[l]&&{mount_destination:e.vfoldersAliasMap[l]}}))),name:e.serviceName,resource_group:e.resourceGroup,model_definition_path:e.modelDefinitionPath,runtime_variant:e.runtimeVariant}};if(Y.supports("modify-endpoint-environ")){const l={};e.envvars&&e.envvars.forEach((e=>l[e.variable]=e.value)),n.props.environ=JSON.stringify(l)}me({variables:n,onCompleted:(e,l)=>{var n,a;if(null!==(n=e.modify_endpoint)&&void 0!==n&&n.ok)if(l&&(null===l||void 0===l?void 0:l.length)>0){const e=l.map((e=>e.message));for(let l of e)W.error(l,2.5)}else{var i;const l=null===(i=e.modify_endpoint)||void 0===i?void 0:i.endpoint;W.success(H("modelService.ServiceUpdated",{name:null===l||void 0===l?void 0:l.name})),Z("/serving")}else W.error(null===(a=e.modify_endpoint)||void 0===a?void 0:a.msg)},onError:e=>{e.message?W.error(e.message):W.error(H("modelService.FailedToUpdateService"))}})}else ue.mutate(e,{onSuccess:()=>{W.success(H("modelService.ServiceUpdated",{name:re.name})),Z("/serving")},onError:e=>{console.log(e),W.error(H("modelService.FailedToUpdateService"))}});else ce.mutate(e,{onSuccess:()=>{W.success(H("modelService.ServiceCreated",{name:e.serviceName})),Z("/serving")},onError:e=>{null!==e&&void 0!==e&&e.message?W.error(y().truncate(null===e||void 0===e?void 0:e.message,{length:200})):re?W.error(H("modelService.FailedToUpdateService")):W.error(H("modelService.FailedToStartService"))}})})).catch((e=>{var l;(null===(l=e.errorFields)||void 0===l?void 0:l.length)>0?e.errorFields.forEach((e=>{W.error(e.errors)})):e.message?W.error(e.message):W.error(H("modelService.FormValidationFailed"))}))},children:H(re?"button.Update":"button.Create")})})]})]})})})})})}),Y.supports("model-service-validation")?(0,S.jsx)(o.A,{zIndex:o.z+1,width:1e3,title:H("modelService.ValidationInfo"),open:ne,destroyOnClose:!0,onCancel:()=>{ae(!ne)},okButtonProps:{style:{display:"none"}},cancelText:H("button.Close"),maskClosable:!1,children:(0,S.jsx)(O,{serviceData:ge})}):null]})}},25575:(e,l,n)=>{n.d(l,{A:()=>u});var a=n(30032),i=n(83468),r=n(57857),o=n(96495),s=n(99814),t=n(97080),d=(n(76998),n(23446));const u=e=>{let{uuid:l,clickable:n}=e;const u=(0,o.hd)(),c=(0,a.QE)(),m=(0,i.f0)(),{data:g}=(0,r.n)({queryKey:["VFolderSelectQuery"],queryFn:()=>{const e=new URLSearchParams;return e.set("group_id",u.id),c({method:"GET",url:"/folders?".concat(e.toString())})},staleTime:1e3,suspense:!0}),v=null===g||void 0===g?void 0:g.find((e=>e.id===l.replaceAll("-","")));return v&&(n?(0,d.jsxs)(t.A.Link,{onClick:()=>{m({pathname:"/data",search:"?folder=".concat(v.id)})},children:[(0,d.jsx)(s.A,{})," ",v.name]}):(0,d.jsxs)("div",{children:[(0,d.jsx)(s.A,{})," ",v.name]}))}},79170:(e,l,n)=>{n.r(l),n.d(l,{default:()=>i});const a=function(){var e={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},l={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null};return{argumentDefinitions:[],kind:"Fragment",metadata:null,name:"ServiceLauncherPageContentFragment",selections:[{alias:null,args:null,kind:"ScalarField",name:"endpoint_id",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"desired_session_count",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_slots",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"open_to_public",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"model",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"model_mount_destination",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"model_definition_path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"environ",storageKey:null},{alias:null,args:null,concreteType:"RuntimeVariantInfo",kind:"LinkedField",name:"runtime_variant",plural:!1,selections:[e,{alias:null,args:null,kind:"ScalarField",name:"human_readable_name",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"extra_mounts",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"row_id",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image_object",plural:!1,selections:[e,{alias:null,args:null,kind:"ScalarField",name:"humanized_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"is_local",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"digest",storageKey:null},{alias:null,args:null,concreteType:"ResourceLimit",kind:"LinkedField",name:"resource_limits",plural:!0,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"min",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:[l,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"size_bytes",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"supported_accelerators",storageKey:null}],storageKey:null},e],type:"Endpoint",abstractKey:null}}();a.hash="15afafa90c5e47be5a52c672e0251ad3";const i=a},97115:(e,l,n)=>{n.r(l),n.d(l,{default:()=>i});const a=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"endpoint_id"},{defaultValue:null,kind:"LocalArgument",name:"props"}],l=[{kind:"Variable",name:"endpoint_id",variableName:"endpoint_id"},{kind:"Variable",name:"props",variableName:"props"}],n={alias:null,args:null,kind:"ScalarField",name:"ok",storageKey:null},a={alias:null,args:null,kind:"ScalarField",name:"msg",storageKey:null},i={alias:null,args:null,kind:"ScalarField",name:"endpoint_id",storageKey:null},r={alias:null,args:null,kind:"ScalarField",name:"desired_session_count",storageKey:null},o={alias:null,args:null,kind:"ScalarField",name:"resource_group",storageKey:null},s={alias:null,args:null,kind:"ScalarField",name:"resource_slots",storageKey:null},t={alias:null,args:null,kind:"ScalarField",name:"resource_opts",storageKey:null},d={alias:null,args:null,kind:"ScalarField",name:"cluster_mode",storageKey:null},u={alias:null,args:null,kind:"ScalarField",name:"cluster_size",storageKey:null},c={alias:null,args:null,kind:"ScalarField",name:"open_to_public",storageKey:null},m={alias:null,args:null,kind:"ScalarField",name:"model",storageKey:null},g={alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},v={alias:null,args:null,kind:"ScalarField",name:"humanized_name",storageKey:null},p={alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},_={alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},y={alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},h={alias:null,args:null,kind:"ScalarField",name:"is_local",storageKey:null},S={alias:null,args:null,kind:"ScalarField",name:"digest",storageKey:null},k={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},f={alias:null,args:null,concreteType:"ResourceLimit",kind:"LinkedField",name:"resource_limits",plural:!0,selections:[k,{alias:null,args:null,kind:"ScalarField",name:"min",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max",storageKey:null}],storageKey:null},F={alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:[k,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null},b={alias:null,args:null,kind:"ScalarField",name:"size_bytes",storageKey:null},K={alias:null,args:null,kind:"ScalarField",name:"supported_accelerators",storageKey:null},x={alias:null,args:null,kind:"ScalarField",name:"model_definition_path",storageKey:null},j={alias:null,args:null,kind:"ScalarField",name:"model_mount_destination",storageKey:null},A={alias:null,args:null,kind:"ScalarField",name:"id",storageKey:null},T={alias:null,args:null,concreteType:"VirtualFolderNode",kind:"LinkedField",name:"extra_mounts",plural:!0,selections:[A,{alias:null,args:null,kind:"ScalarField",name:"host",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"quota_scope_id",storageKey:null},g,{alias:null,args:null,kind:"ScalarField",name:"user",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"user_email",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"group_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"creator",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"unmanaged_path",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"usage_mode",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"ownership_type",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"created_at",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"last_used",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"num_files",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cur_size",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"cloneable",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"status",storageKey:null}],storageKey:null},C={alias:null,args:null,concreteType:"RuntimeVariantInfo",kind:"LinkedField",name:"runtime_variant",plural:!1,selections:[g,{alias:null,args:null,kind:"ScalarField",name:"human_readable_name",storageKey:null}],storageKey:null};return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"ServiceLauncherPageContentModifyMutation",selections:[{alias:null,args:l,concreteType:"ModifyEndpoint",kind:"LinkedField",name:"modify_endpoint",plural:!1,selections:[n,a,{alias:null,args:null,concreteType:"Endpoint",kind:"LinkedField",name:"endpoint",plural:!1,selections:[i,r,o,s,t,d,u,c,m,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image_object",plural:!1,selections:[g,v,p,_,y,h,S,f,F,b,K],storageKey:null},g,x,j,T,C],storageKey:null}],storageKey:null}],type:"Mutations",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"ServiceLauncherPageContentModifyMutation",selections:[{alias:null,args:l,concreteType:"ModifyEndpoint",kind:"LinkedField",name:"modify_endpoint",plural:!1,selections:[n,a,{alias:null,args:null,concreteType:"Endpoint",kind:"LinkedField",name:"endpoint",plural:!1,selections:[i,r,o,s,t,d,u,c,m,{alias:null,args:null,concreteType:"ImageNode",kind:"LinkedField",name:"image_object",plural:!1,selections:[g,v,p,_,y,h,S,f,F,b,K,A],storageKey:null},g,x,j,T,C,A],storageKey:null}],storageKey:null}]},params:{cacheID:"f8b453283800445a79fbf812d1f4e57c",id:null,metadata:{},name:"ServiceLauncherPageContentModifyMutation",operationKind:"mutation",text:'mutation ServiceLauncherPageContentModifyMutation(\n  $endpoint_id: UUID!\n  $props: ModifyEndpointInput!\n) {\n  modify_endpoint(endpoint_id: $endpoint_id, props: $props) {\n    ok\n    msg\n    endpoint {\n      endpoint_id\n      desired_session_count\n      resource_group\n      resource_slots\n      resource_opts\n      cluster_mode\n      cluster_size\n      open_to_public\n      model\n      image_object @since(version: "23.09.9") {\n        name\n        humanized_name\n        tag\n        registry\n        architecture\n        is_local\n        digest\n        resource_limits {\n          key\n          min\n          max\n        }\n        labels {\n          key\n          value\n        }\n        size_bytes\n        supported_accelerators\n        id\n      }\n      name\n      model_definition_path\n      model_mount_destination\n      extra_mounts @since(version: "24.03.4") {\n        id\n        host\n        quota_scope_id\n        name\n        user\n        user_email\n        group\n        group_name\n        creator\n        unmanaged_path\n        usage_mode\n        permission\n        ownership_type\n        max_files\n        max_size\n        created_at\n        last_used\n        num_files\n        cur_size\n        cloneable\n        status\n      }\n      runtime_variant @since(version: "24.03.5") {\n        name\n        human_readable_name\n      }\n      id\n    }\n  }\n}\n'}}}();a.hash="8327827df6f67cb9d419ac1d8ddbb4b9";const i=a},94080:(e,l,n)=>{n.d(l,{A:()=>t});var a=n(58168),i=n(76998);const r={icon:{tag:"svg",attrs:{viewBox:"64 64 896 896",focusable:"false"},children:[{tag:"path",attrs:{d:"M696 480H328c-4.4 0-8 3.6-8 8v48c0 4.4 3.6 8 8 8h368c4.4 0 8-3.6 8-8v-48c0-4.4-3.6-8-8-8z"}},{tag:"path",attrs:{d:"M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z"}}]},name:"minus-circle",theme:"outlined"};var o=n(13410),s=function(e,l){return i.createElement(o.A,(0,a.A)({},e,{ref:l,icon:r}))};const t=i.forwardRef(s)}}]);
//# sourceMappingURL=6872.ab8f43a3.chunk.js.map