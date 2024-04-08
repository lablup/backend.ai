"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[310],{23623:(e,s,n)=>{n.d(s,{A:()=>r});var t=n(76998);const l=(e,s,n)=>{const[l,r]=(0,t.useState)(e());return(0,t.useEffect)((()=>{n&&r(e())}),[n]),function(e,s){const n=(0,t.useRef)();(0,t.useEffect)((()=>{n.current=e})),(0,t.useEffect)((()=>{if(null!==s){let e=setInterval((function(){var e;null===(e=n.current)||void 0===e||e.call(n)}),s);return()=>clearInterval(e)}}),[s])}((()=>{const s=e();s!==l&&r(s)}),s),l},r=e=>{let{callback:s,delay:n,triggerKey:t}=e;return l(s,n,t)}},42989:(e,s,n)=>{n.d(s,{A:()=>d});var t=n(66464),l=n(60708),r=n(14455),a=n.n(r),o=n(45901),i=n.n(o),c=(n(76998),n(23446));const d=e=>{let{value:s,onChange:n,localFormat:r,...o}=e;const[,d]=(0,t.A)({value:s,onChange:n});return(0,c.jsx)(l.A,{value:s?a()(s):void 0,onChange:e=>{var s,n,t;i().isArray(e)&&(e=e[0]);const l=r?null===(s=e)||void 0===s?void 0:s.format():null===(n=e)||void 0===n||null===(t=n.tz())||void 0===t?void 0:t.toISOString();d(l)},...o})}},55256:(e,s,n)=>{n.d(s,{Ay:()=>A,Kk:()=>p,p3:()=>x,sT:()=>h,vB:()=>m});var t=n(83468),l=n(5621),r=n(29871),a=n(48713),o=n(45901),i=n.n(o),c=n(76998),d=n(23446);const u=e=>{let{image:s,...n}=e;s=s||"";const[,{getImageAliasName:r,getBaseVersion:a,tagAlias:o}]=(0,t.Gj)();return(0,d.jsx)(l.A,{values:[{label:o(r(s)),color:"blue"},{label:a(s),color:"green"}],...n})},m=e=>{let{image:s,...n}=e;s=s||"";const[,{getBaseVersion:l,tagAlias:r}]=(0,t.Gj)();return(0,d.jsx)(a.A,{color:"green",...n,children:r(l(s))})},h=e=>{let{image:s,...n}=e;s=s||"";const[,{getBaseImage:l,tagAlias:r}]=(0,t.Gj)();return(0,d.jsx)(a.A,{color:"green",...n,children:r(l(s))})},g=e=>{let{image:s,...n}=e;s=s||"";const[,{getArchitecture:l,tagAlias:r}]=(0,t.Gj)();return(0,d.jsx)(a.A,{color:"green",...n,children:r(l(s))})},p=e=>{let{image:s,...n}=e;s=s||"";const[,{getImageLang:l,tagAlias:r}]=(0,t.Gj)();return(0,d.jsx)(a.A,{color:"green",...n,children:r(l(s))})},x=e=>{let{image:s,labels:n,...o}=e;s=s||"",n=n||[];const[,{getFilteredRequirementsTags:c,getCustomTag:u,tagAlias:m}]=(0,t.Gj)();return(0,d.jsxs)(r.A,{children:[i().map(c(s),((e,s)=>(0,d.jsx)(a.A,{color:"blue",...o,children:m(e||"")},s))),(0,d.jsx)(l.A,{color:"cyan",values:[{label:"Customized",color:"cyan"},{label:u(n),color:"cyan"}],...o})]})},v=(e,s)=>{let{image:n,style:t={}}=e;return n=n||"",(0,d.jsxs)(d.Fragment,{children:[(0,d.jsx)(u,{image:n}),(0,d.jsx)(h,{image:n}),(0,d.jsx)(g,{image:n})]})},A=c.memo(v)},26165:(e,s,n)=>{n.r(s),n.d(s,{default:()=>l});const t={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"VFolderPermissionTag_VFolder",selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null}],type:"VirtualFolder",abstractKey:null,hash:"d3b0f85629ac8c6f45ef363938f66067"},l=t},83310:(e,s,n)=>{n.r(s),n.d(s,{default:()=>Ie});var t=n(25344),l=n(82156),r=n(50840),a=n(6932),o=n(29475),i=n(45901),c=n.n(i),d=n(76998),u=n(23446);const m=e=>{let{status:s="default",extraButtonTitle:n,onClickExtraButton:i,extra:d,style:m,...h}=e;const{token:g}=r.A.useToken(),p=d||n&&(0,u.jsx)(a.Ay,{type:"link",icon:"error"===s?(0,u.jsx)(t.A,{twoToneColor:g.colorError}):"warning"===s?(0,u.jsx)(l.A,{twoToneColor:g.colorWarning}):void 0,onClick:i,children:n})||void 0;return(0,u.jsx)(o.A,{style:c().extend(m,{borderColor:"error"===s?g.colorError:"warning"===s?g.colorWarning:"success"===s?g.colorSuccess:null===m||void 0===m?void 0:m.borderColor}),extra:p,...h})};var h=n(23623),g=n(42989),p=n(5621),x=n(29871),v=n(94080),A=n(5336),j=n(65080),y=n(82028),b=n(77678);const f=e=>{let{formItemProps:s,...n}=e;const t=(0,d.useRef)(null),{t:l}=(0,b.Bd)(),r=j.A.useFormInstance();return(0,u.jsx)(j.A.List,{...n,children:(e,o)=>{let{add:i,remove:d}=o;return(0,u.jsxs)(x.A,{direction:"column",gap:"xs",align:"stretch",children:[e.map(((a,o)=>{let{key:i,name:m,...h}=a;return(0,u.jsxs)(x.A,{direction:"row",align:"baseline",gap:"xs",children:[(0,u.jsx)(j.A.Item,{...h,style:{marginBottom:0,flex:1},name:[m,"variable"],rules:[{required:!0,message:l("session.launcher.EnterEnvironmentVariable")},{pattern:/^[a-zA-Z_][a-zA-Z0-9_]*$/,message:l("session.launcher.EnvironmentVariableNamePatternError")},e=>{let{getFieldValue:s}=e;return{validator(e,t){const r=c().map(s(n.name),(e=>null===e||void 0===e?void 0:e.variable));return!c().isEmpty(t)&&r.length>0&&c().filter(r,(e=>e===t)).length>1?Promise.reject(l("session.launcher.EnvironmentVariableDuplicateName")):Promise.resolve()}}}],...s,children:(0,u.jsx)(y.A,{ref:o===e.length-1?t:null,placeholder:"Variable",onChange:()=>{const s=e.map(((e,s)=>[n.name,s,"variable"]));r.validateFields(s)}})}),(0,u.jsx)(j.A.Item,{...h,name:[m,"value"],style:{marginBottom:0,flex:1},rules:[{required:!0,message:l("session.launcher.EnvironmentVariableValueRequired")}],validateTrigger:["onChange","onBlur"],children:(0,u.jsx)(y.A,{placeholder:"Value"})}),(0,u.jsx)(v.A,{onClick:()=>d(m)})]},i)})),(0,u.jsx)(j.A.Item,{noStyle:!0,children:(0,u.jsx)(a.Ay,{type:"dashed",onClick:()=>{i(),setTimeout((()=>{t.current&&t.current.focus()}),0)},icon:(0,u.jsx)(A.A,{}),block:!0,children:l("session.launcher.AddEnvironmentVariable")})})]})}})};var F=n(85676),w=n(35051),k=n(55256),C=n(16788),V=n(83468),T=n(30217),S=n(48713);const I=e=>{let{value:s,...n}=e;const t=parseInt(s),l=t>=1024&&t<=65535;return(0,u.jsx)(S.A,{color:l?void 0:"red",...n})},P=e=>{let{...s}=e;const{t:n}=(0,b.Bd)(),t=(0,V.CX)();return(0,u.jsx)(j.A.Item,{label:n("session.launcher.PreOpenPortTitle"),name:"ports",tooltip:(0,u.jsx)(b.x6,{i18nKey:"session.launcher.DescSetPreOpenPort"}),extra:n("session.launcher.PreOpenPortRangeGuide"),rules:[{max:t._config.maxCountForPreopenPorts,type:"array",message:n("session.launcher.PreOpenPortMaxCountLimit",{count:t._config.maxCountForPreopenPorts})},e=>{let{getFieldValue:s}=e;return{validator:(e,s)=>c().every(s,(e=>{const s=parseInt(e);return s>=1024&&s<=65535}))?Promise.resolve():Promise.reject(new Error(n("session.launcher.PreOpenPortRange")))}}],...s,children:(0,u.jsx)(T.A,{mode:"tags",tagRender:e=>(0,u.jsx)(I,{closable:e.closable,onClose:e.onClose,onMouseDown:e=>{e.preventDefault(),e.stopPropagation()},value:e.value,children:e.label}),style:{width:"100%"},suffixIcon:null,open:!1,tokenSeparators:[","," "]})})};var E=n(97443),N=n(8469);const _=e=>{let{...s}=e;const{t:n}=(0,b.Bd)();return(0,u.jsx)(j.A.Item,{label:n("session.launcher.SessionName"),name:"sessionName",rules:[{min:4,message:n("session.Validation.SessionNameTooShort")},{max:64,message:n("session.Validation.SessionNameTooLong64")},{validator:(e,s)=>c().isEmpty(s)?Promise.resolve():/^\w/.test(s)?/^[\w.-]*$/.test(s)?!/\w$/.test(s)&&s.length>=4?Promise.reject(n("session.Validation.SessionNameShouldEndWith")):Promise.resolve():Promise.reject(n("session.Validation.SessionNameInvalidCharacter")):Promise.reject(n("session.Validation.SessionNameShouldStartWith"))}],...s,children:(0,u.jsx)(y.A,{allowClear:!0,autoComplete:"off"})})};var M,D=n(30032),O=n(57857),z=n(91412),B=n(81638),R=n(3606);const K=e=>{let{vFolderFrgmt:s=null,permission:t}=e;const l=(0,R.useFragment)(void 0!==M?M:M=n(26165),s),r=c().chain({r:"green",w:"blue",d:"red"}).map(((e,s)=>{if(((e,s)=>!(null===e||void 0===e||!e.includes(s))||!(null===e||void 0===e||!e.includes("w")||"r"!==s))((null===l||void 0===l?void 0:l.permission)||t,s))return{label:s.toUpperCase(),color:e}})).compact().value();return(0,u.jsx)(p.A,{values:r})};var L=n(71155),W=n(8925),q=n(93792),G=n(66464),U=n(13279),H=n(20307),J=n(14862),Z=n(14455),Q=n.n(Z);const $=/^[a-zA-Z0-9_/-]*$/,X=e=>{let{filter:s,showAliasInput:n=!1,selectedRowKeys:t=[],onChangeSelectedRowKeys:l,aliasBasePath:r="/home/work/",aliasMap:o,onChangeAliasMap:i,rowKey:m="name",...h}=e;const g=d.useMemo((()=>e=>e&&e[m]),[m]),[p,v]=(0,G.A)({value:t,onChange:l},{defaultValue:[]}),[A,f]=(0,G.A)({value:o,onChange:i},{defaultValue:{}}),[F]=j.A.useForm();(0,d.useEffect)((()=>{A&&(F.setFieldsValue(c().mapValues(A,(e=>e.startsWith(r)?e.slice(r.length):e))),F.validateFields())}),[A,F,r]);const{t:w}=(0,b.Bd)(),k=(0,D.QE)(),C=(0,V.hd)(),[T,S]=(0,V.Tw)("first"),[I,P]=(0,d.useTransition)(),{data:E}=(0,O.n)({queryKey:["VFolderSelectQuery",T,C.id],queryFn:()=>k({method:"GET",url:"/folders?group_id=".concat(C.id)}),staleTime:0}),[N,_]=(0,d.useState)(""),M=c().chain(E).filter((e=>!s||s(e))).filter((e=>!!p.includes(g(e))||(!N||e.name.includes(N)))).value(),R=e=>{null===e||void 0===e||e.preventDefault(),F.validateFields().then((e=>{})).catch((()=>{})).finally((()=>{f(c().mapValues(c().pickBy(F.getFieldsValue(),(e=>!!e)),((e,s)=>Z(s,e))))}))},Z=(e,s)=>c().isEmpty(s)?"".concat(r).concat(e):null!==s&&void 0!==s&&s.startsWith("/")?s:"".concat(r).concat(s),X=(0,z.useShadowRoot)(),Y=[{title:(0,u.jsxs)(x.A,{direction:"row",gap:"xxs",children:[(0,u.jsx)(U.A.Text,{children:w("data.folders.Name")}),n&&(0,u.jsx)(u.Fragment,{children:(0,u.jsxs)(U.A.Text,{type:"secondary",style:{fontWeight:"normal"},children:["(",w("session.launcher.FolderAlias")," ",(0,u.jsx)(H.A,{title:(0,u.jsx)(b.x6,{i18nKey:"session.launcher.DescFolderAlias"}),getPopupContainer:()=>X,children:(0,u.jsx)(L.A,{})}),")"]})})]}),dataIndex:"name",sorter:(e,s)=>e.name.localeCompare(s.name),render:(e,s)=>{const t=p.includes(g(s));return(0,u.jsxs)(x.A,{direction:"column",align:"stretch",gap:"xxs",style:n&&t?{display:"inline-flex",height:70,width:"100%"}:{maxWidth:200},children:[(0,u.jsx)(B.A,{keyword:N,children:e}),n&&t&&(0,u.jsx)(j.A.Item,{noStyle:!0,shouldUpdate:(e,n)=>e[g(s)]!==n[g(s)],children:()=>{const e=c()(p).reduce(((e,s)=>(e[s]=(null===A||void 0===A?void 0:A[s])||Z(s,void 0),e)),{});return(0,u.jsx)(j.A.Item,{name:g(s),rules:[{type:"string",pattern:$,message:w("session.launcher.FolderAliasInvalid")},{type:"string",validator:async(n,t)=>t&&c().some(e,((e,n)=>n!==g(s)&&e===Z(g(s),t)))?Promise.reject(w("session.launcher.FolderAliasOverlapping")):Promise.resolve()}],extra:Z(s.name,F.getFieldValue(g(s))),children:(0,u.jsx)(y.A,{onClick:e=>{e.stopPropagation()},placeholder:w("session.launcher.FolderAlias"),onChange:R,allowClear:!0})})}})]})}},{title:w("data.UsageMode"),dataIndex:"usage_mode",sorter:(e,s)=>e.usage_mode.localeCompare(s.usage_mode)},{title:w("data.Host"),dataIndex:"host"},{title:w("data.Type"),dataIndex:"type",sorter:(e,s)=>e.type.localeCompare(s.type),render:(e,s)=>(0,u.jsxs)(x.A,{direction:"column",children:["user"===s.type?(0,u.jsx)(W.A,{title:"User"}):(0,u.jsx)("div",{children:"Group"}),"group"===s.type&&"(".concat(s.group_name,")")]})},{title:w("data.Permission"),dataIndex:"permission",sorter:(e,s)=>e.permission.localeCompare(s.permission),render:(e,s)=>(0,u.jsx)(K,{permission:s.permission})},{title:w("data.Created"),dataIndex:"created_at",sorter:(e,s)=>e.created_at.localeCompare(s.created_at),render:(e,s)=>Q()(e).format("L")}];return(0,u.jsxs)(x.A,{direction:"column",align:"stretch",gap:"xs",children:[(0,u.jsxs)(x.A,{direction:"row",gap:"xs",justify:"between",children:[(0,u.jsx)(y.A,{value:N,onChange:e=>_(e.target.value),allowClear:!0,placeholder:w("data.SearchByName")}),(0,u.jsx)(a.Ay,{loading:I,icon:(0,u.jsx)(q.A,{}),onClick:()=>{P((()=>{S()}))}})]}),(0,u.jsx)(j.A,{form:F,component:!1,children:(0,u.jsx)(J.A,{scroll:{x:"max-content"},rowKey:g,rowSelection:{selectedRowKeys:p,onChange:e=>{v(e),R()}},showSorterTooltip:!1,columns:Y,dataSource:M,onRow:(e,s)=>({onClick:s=>{var n;const t=s.target;null!==t&&void 0!==t&&null!==(n=t.classList)&&void 0!==n&&n.contains("ant-table-selection-column")&&(s.stopPropagation(),p.includes(g(e))?v(p.filter((s=>s!==g(e)))):v([...p,g(e)]))}}),...h})})]})},Y=e=>{let{filter:s,...n}=e;const t=j.A.useFormInstance(),{t:l}=(0,b.Bd)();return j.A.useWatch("vfoldersAliasMap",t),(0,u.jsxs)(u.Fragment,{children:[(0,u.jsx)(j.A.Item,{hidden:!0,name:"vfoldersAliasMap",rules:[{validator(e,s){const n=c().chain(t.getFieldValue("mounts")).reduce(((e,n)=>(e[n]=s[n]||"/home/work/"+n,e)),{}).values().value();return c().uniq(n).length!==n.length?Promise.reject(l("session.launcher.FolderAliasOverlapping")):c().some(n,(e=>!$.test(e)))?Promise.reject(l("session.launcher.FolderAliasInvalid")):Promise.resolve()}}],children:(0,u.jsx)(y.A,{})}),(0,u.jsx)(j.A.Item,{name:"mounts",...n,valuePropName:"selectedRowKeys",trigger:"onChangeSelectedRowKeys",children:(0,u.jsx)(X,{rowKey:"name",showAliasInput:!0,aliasMap:t.getFieldValue("vfoldersAliasMap"),onChangeAliasMap:e=>{t.setFieldValue("vfoldersAliasMap",e),t.validateFields(["vfoldersAliasMap"])},pagination:!1,filter:s})})]})};var ee=n(21454),se=n(90660);var ne=n(21186),te=n(15618),le=n(78474),re=n(42290),ae=n(40718),oe=n(76108),ie=n(12620),ce=n(33554),de=n(41814),ue=n(17480),me=n(87627),he=n(82745),ge=n(7518),pe=n(9788),xe=n(91409),ve=n(22307),Ae=n(41856),je=n(59065),ye=n(67970),be=n(34515),fe=n(81365),Fe=n(6592),we=n(52276),ke=n(44442),Ce=n(58346);const Ve=e=>{let{form:s,containerCount:n=1}=e;return(0,u.jsxs)(u.Fragment,{children:[c().map(c().omit(s.getFieldsValue().resource,"shmem","accelerator","acceleratorType"),((e,t)=>{var l,r;return(0,u.jsx)(N.Ay,{type:t,value:"mem"===t?((null===(l=(0,D.Js)(e,"b"))||void 0===l?void 0:l.number)||0)*n+"":c().toNumber(e)*n+"",opts:{shmem:s.getFieldValue("resource").shmem?((null===(r=(0,D.Js)(s.getFieldValue("resource").shmem,"b"))||void 0===r?void 0:r.number)||0)*n:void 0}},t)})),c().isNumber(s.getFieldValue(["resource","accelerator"]))&&s.getFieldValue(["resource","acceleratorType"])&&(0,u.jsx)(N.Ay,{type:s.getFieldValue(["resource","acceleratorType"]),value:c().toString(s.getFieldValue(["resource","accelerator"])*n)})]})},Te=()=>{let e="";const s="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";for(let n=0;n<8;n++)e+=s.charAt(Math.floor(62*Math.random()));return e+"-session"},Se=()=>{let e=Math.floor(52*Math.random()*52*52);let s="";for(let t=0;t<3;t++)s+=(n=e%52)<26?String.fromCharCode(65+n):String.fromCharCode(97+n-26),e=Math.floor(e/52);var n;return s},Ie=()=>{var e,s,n,t,l,i,v,A,N,M,O,z,B,R,K,W;const q=ie.A.useApp();let G="normal";const Z=(0,ke.vc)(C.i7),$=(0,V.CX)(),[X,Ie]=(0,d.useState)(!1),Pe={sessionType:"interactive",allocationPreset:"auto-preset",hpcOptimization:{autoEnabled:!0,OMP_NUM_THREADS:"1",OPENBLAS_NUM_THREADS:"1"},batch:{enabled:!1,command:void 0,scheduleDate:void 0},envvars:[],...(null===(e=$._config)||void 0===e?void 0:e.default_session_environment)&&{environments:{environment:null===(s=$._config)||void 0===s?void 0:s.default_session_environment}},...E.jh},Ee=(0,Ce.withDefault)(Ce.NumberParam,0),Ne=(0,Ce.withDefault)(Ce.JsonParam,Pe),[{step:_e,formValues:Me,redirectTo:De},Oe]=(0,Ce.useQueryParams)({step:Ee,formValues:Ne,redirectTo:Ce.StringParam}),{isDarkMode:ze}=(0,se.e)(),Be=(0,fe.Zp)(),Re=(0,V.f0)(),Ke=(0,V.hd)(),{upsertNotification:Le}=(0,ee.js)(),{run:We}=(0,oe.A)((()=>{Oe({formValues:c().omit(Je.getFieldsValue(),["environments.image"],["environments.customizedTag"])},"replaceIn")}),{leading:!1,wait:500,trailing:!0}),qe=e=>{Oe({step:e},"pushIn")},{token:Ge}=r.A.useToken(),{t:Ue}=(0,b.Bd)(),He=ce.Ay.useBreakpoint(),[Je]=j.A.useForm();(0,d.useEffect)((()=>{JSON.stringify(Pe)!==JSON.stringify(Me)&&(Je.setFieldsValue(Me),Je.validateFields().catch((e=>{})))}),[]),(0,d.useEffect)((()=>{var e;null===(e=Z.current)||void 0===e||e.scrollTo(0,0)}),[_e]);const Ze=j.A.useWatch("sessionType",{form:Je,preserve:!0})||Je.getFieldValue("sessionType")||Me.sessionType,Qe=c().filter([{title:Ue("session.launcher.SessionType"),key:"sessionType"},{title:"".concat(Ue("session.launcher.Environments")," & ").concat(Ue("session.launcher.ResourceAllocation")," "),key:"environment"},"inference"!==Ze&&{title:Ue("webui.menu.Data&Storage"),key:"storage"},{title:Ue("session.launcher.Network"),key:"network"},{title:Ue("session.launcher.ConfirmAndLaunch"),icon:(0,u.jsx)(ne.A,{}),key:"review"}],(e=>!!e)),$e=null===(n=Qe[_e])||void 0===n?void 0:n.key,Xe=c().some(Je.getFieldsError(),(e=>e.errors.length>0)),[,Ye]=(0,V.Tw)("first");(0,d.useEffect)((()=>{_e===Qe.length-1&&Je.validateFields().catch((e=>Ye()))}),[_e,Je,Ye,Qe.length]);return(0,u.jsxs)(x.A,{direction:"column",align:"stretch",style:{justifyContent:"revert"},gap:"md",children:[(0,u.jsx)("style",{children:".session-type-radio-group .ant-radio {\n  align-self: flex-start;\n  margin-top: 2px;\n}\n"}),De&&(0,u.jsx)(de.A,{items:[{title:Ue("webui.menu.Sessions"),onClick:e=>{e.preventDefault(),Re(De)},href:De},{title:Ue("session.launcher.StartNewSession")}]}),(0,u.jsxs)(x.A,{direction:"row",gap:"md",align:"start",children:[(0,u.jsx)(x.A,{direction:"column",align:"stretch",style:{flex:1,maxWidth:700},children:(0,u.jsx)(j.A.Provider,{onFormChange:(e,s)=>{We()},children:(0,u.jsx)(j.A,{form:Je,layout:"vertical",requiredMark:"optional",initialValues:Pe,children:(0,u.jsxs)(x.A,{direction:"column",align:"stretch",gap:"md",children:[(0,u.jsxs)(o.A,{title:Ue("session.launcher.SessionType"),style:{display:"sessionType"===$e?"block":"none"},children:[(0,u.jsx)(j.A.Item,{name:"sessionType",children:(0,u.jsx)(ue.Ay.Group,{className:"session-type-radio-group",options:[{label:(0,u.jsxs)(u.Fragment,{children:[(0,u.jsx)(U.A.Text,{code:!0,children:Ue("session.launcher.InteractiveMode")})," ",(0,u.jsx)(U.A.Text,{type:"secondary",children:Ue("session.launcher.InteractiveModeDesc")})]}),value:"interactive"},{label:(0,u.jsxs)(u.Fragment,{children:[(0,u.jsx)(U.A.Text,{code:!0,children:Ue("session.launcher.BatchMode")})," ",(0,u.jsx)(U.A.Text,{type:"secondary",children:Ue("session.launcher.BatchModeDesc")})]}),value:"batch"}]})}),(0,u.jsx)(_,{})]}),"batch"===Ze&&(0,u.jsxs)(o.A,{title:Ue("session.launcher.BatchModeConfig"),style:{display:"sessionType"===$e?"block":"none"},children:[(0,u.jsx)(j.A.Item,{label:Ue("session.launcher.StartUpCommand"),name:["batch","command"],rules:[{required:!0,type:"string"}],children:(0,u.jsx)(y.A.TextArea,{autoSize:!0})}),(0,u.jsx)(j.A.Item,{label:Ue("session.launcher.SessionStartTime"),extra:(0,u.jsx)(j.A.Item,{noStyle:!0,shouldUpdate:(e,s)=>e.batch.scheduleDate!==s.batch.scheduleDate,children:()=>{const e=Je.getFieldValue(["batch","scheduleDate"]);return(0,u.jsx)(h.A,{delay:1e3,callback:()=>{const e=Je.getFieldValue(["batch","scheduleDate"]);return e?Q()(e).isBefore(Q()())?void(0===Je.getFieldError(["batch","scheduleDate"]).length&&Je.validateFields([["batch","scheduleDate"]])):Q()(e).fromNow():void 0},triggerKey:e||"none"})}}),children:(0,u.jsxs)(x.A,{direction:"row",gap:"xs",children:[(0,u.jsx)(j.A.Item,{noStyle:!0,name:["batch","enabled"],valuePropName:"checked",children:(0,u.jsx)(me.A,{onChange:e=>{e.target.checked&&c().isEmpty(Je.getFieldValue(["batch","scheduleDate"]))?Je.setFieldValue(["batch","scheduleDate"],Q()().add(2,"minutes").toISOString()):!1===e.target.checked&&Je.setFieldValue(["batch","scheduleDate"],void 0),Je.validateFields([["batch","scheduleDate"]])},children:Ue("session.launcher.Enable")})}),(0,u.jsx)(j.A.Item,{noStyle:!0,shouldUpdate:(e,s)=>{var n,t;return(null===(n=e.batch)||void 0===n?void 0:n.enabled)!==(null===(t=s.batch)||void 0===t?void 0:t.enabled)},children:()=>{var e;const s=!0!==(null===(e=Je.getFieldValue("batch"))||void 0===e?void 0:e.enabled);return(0,u.jsx)(u.Fragment,{children:(0,u.jsx)(j.A.Item,{name:["batch","scheduleDate"],noStyle:!0,rules:[{validator:async(e,s)=>s&&Q()(s).isBefore(Q()())?Promise.reject(Ue("session.launcher.StartTimeMustBeInTheFuture")):Promise.resolve()}],children:(0,u.jsx)(g.A,{disabled:s,showTime:!0,localFormat:!0,disabledDate:e=>e.isBefore(Q()().startOf("day"))})})})}})]})})]}),"inference"===Ze&&(0,u.jsx)(o.A,{title:"Inference Mode Configuration",children:(0,u.jsx)(j.A.Item,{name:["inference","vFolderName"],label:Ue("session.launcher.ModelStorageToMount"),rules:[{required:!0}],children:(0,u.jsx)(T.A,{})})}),(0,u.jsxs)(o.A,{title:Ue("session.launcher.Environments"),style:{display:"environment"===$e?"block":"none"},children:[(0,u.jsx)(be.tH,{fallbackRender:e=>(console.log(e),null),children:(0,u.jsx)(F.A,{})}),(0,u.jsx)(j.A.Item,{label:Ue("session.launcher.EnvironmentVariable"),children:(0,u.jsx)(f,{name:"envvars",formItemProps:{validateTrigger:["onChange","onBlur"]}})})]}),(0,u.jsx)(o.A,{title:Ue("session.launcher.ResourceAllocation"),style:{display:"environment"===$e?"block":"none"},children:(0,u.jsx)(E.Ay,{enableNumOfSessions:!0,enableResourcePresets:!0})}),(0,u.jsxs)(o.A,{title:Ue("session.launcher.HPCOptimization"),style:{display:"environment"===$e?"block":"none"},children:[(0,u.jsx)(j.A.Item,{noStyle:!0,children:(0,u.jsxs)(x.A,{direction:"row",gap:"sm",children:[(0,u.jsx)(U.A.Text,{children:Ue("session.launcher.SwitchOpenMPoptimization")}),(0,u.jsx)(j.A.Item,{label:Ue("session.launcher.SwitchOpenMPoptimization"),name:["hpcOptimization","autoEnabled"],valuePropName:"checked",required:!0,noStyle:!0,children:(0,u.jsx)(he.A,{checkedChildren:"ON",unCheckedChildren:"OFF",onChange:e=>{e&&Je.setFieldsValue(c().pick(Pe,["hpcOptimization"]))}})})]})}),(0,u.jsx)(j.A.Item,{noStyle:!0,shouldUpdate:(e,s)=>{var n,t;return(null===(n=e.hpcOptimization)||void 0===n?void 0:n.autoEnabled)!==(null===(t=s.hpcOptimization)||void 0===t?void 0:t.autoEnabled)},children:()=>{const e=Je.getFieldValue(["hpcOptimization","autoEnabled"]);return(0,u.jsxs)(ge.A,{gutter:Ge.marginMD,style:{display:e?"none":void 0,marginTop:Ge.marginMD},children:[(0,u.jsx)(pe.A,{xs:24,sm:12,children:(0,u.jsx)(j.A.Item,{style:{flex:1},label:Ue("session.launcher.NumOpenMPthreads"),name:["hpcOptimization","OMP_NUM_THREADS"],tooltip:(0,u.jsxs)(u.Fragment,{children:[Ue("session.launcher.OpenMPOptimization"),(0,u.jsx)(b.x6,{i18nKey:"session.launcher.DescOpenMPOptimization"})]}),required:!0,children:(0,u.jsx)(xe.A,{min:0,max:1e3,step:1,stringMode:!0,style:{width:"100%"}})})}),(0,u.jsx)(pe.A,{xs:24,sm:12,children:(0,u.jsx)(j.A.Item,{style:{flex:1},label:Ue("session.launcher.NumOpenBLASthreads"),name:["hpcOptimization","OPENBLAS_NUM_THREADS"],tooltip:(0,u.jsxs)(u.Fragment,{children:[Ue("session.launcher.OpenMPOptimization"),(0,u.jsx)(b.x6,{i18nKey:"session.launcher.DescOpenMPOptimization"})]}),required:!0,children:(0,u.jsx)(xe.A,{min:0,max:1e3,step:1,stringMode:!0,style:{width:"100%"}})})})]})}})]}),(0,u.jsx)(o.A,{title:Ue("webui.menu.Data&Storage"),style:{display:"storage"===$e?"block":"none"},children:(0,u.jsx)(Y,{filter:e=>{var s;return"ready"===e.status&&!(null!==(s=e.name)&&void 0!==s&&s.startsWith("."))}})}),(0,u.jsx)(o.A,{title:Ue("session.launcher.Network"),style:{display:"network"===$e?"block":"none"},children:(0,u.jsx)(P,{})}),"review"===$e&&(0,u.jsxs)(u.Fragment,{children:[(0,u.jsx)(m,{title:Ue("session.launcher.SessionType"),size:"small",status:Je.getFieldError("sessionName").length>0||Je.getFieldError(["batch","command"]).length>0||Je.getFieldError(["batch","scheduleDate"]).length>0?"error":void 0,extraButtonTitle:Ue("button.Edit"),onClickExtraButton:()=>{qe(Qe.findIndex((e=>"sessionType"===e.key)))},children:(0,u.jsxs)(ve.A,{size:"small",column:1,children:[(0,u.jsx)(ve.A.Item,{label:Ue("session.SessionType"),children:Je.getFieldValue("sessionType")}),!c().isEmpty(Je.getFieldValue("sessionName"))&&(0,u.jsx)(ve.A.Item,{label:Ue("session.launcher.SessionName"),children:Je.getFieldValue("sessionName")}),"batch"===Ze&&(0,u.jsxs)(u.Fragment,{children:[(0,u.jsx)(ve.A.Item,{label:Ue("session.launcher.StartUpCommand"),children:Je.getFieldValue(["batch","command"])?(0,u.jsx)(Fe.A,{style:ze?we.A:void 0,language:"shell",customStyle:{margin:0,width:"100%"},children:Je.getFieldValue(["batch","command"])}):(0,u.jsx)(U.A.Text,{type:"secondary",children:Ue("general.None")})}),(0,u.jsx)(ve.A.Item,{label:Ue("session.launcher.ScheduleTimeSimple"),children:Je.getFieldValue(["batch","scheduleDate"])?Q()(Je.getFieldValue(["batch","scheduleDate"])).format("LLL (Z)"):(0,u.jsx)(U.A.Text,{type:"secondary",children:Ue("general.None")})})]})]})}),(0,u.jsx)(m,{title:Ue("session.launcher.Environments"),size:"small",status:c().some(Je.getFieldValue("envvars"),((e,s)=>Je.getFieldError(["envvars",s,"variable"]).length>0||Je.getFieldError(["envvars",s,"value"]).length>0))?"error":void 0,extraButtonTitle:Ue("button.Edit"),onClickExtraButton:()=>{qe(Qe.findIndex((e=>"environment"===e.key)))},children:(0,u.jsxs)(ve.A,{size:"small",column:1,children:[(0,u.jsx)(ve.A.Item,{label:Ue("session.launcher.Project"),children:Ke.name}),(0,u.jsx)(ve.A.Item,{label:Ue("general.Image"),children:(0,u.jsxs)(x.A,{direction:"row",gap:"xs",style:{flex:1},children:[(0,u.jsx)(w.A,{image:(null===(t=Je.getFieldValue("environments"))||void 0===t?void 0:t.version)||(null===(l=Je.getFieldValue("environments"))||void 0===l?void 0:l.manual)}),(0,u.jsx)(x.A,{direction:"row",children:null!==(i=Je.getFieldValue("environments"))&&void 0!==i&&i.manual?(0,u.jsx)(U.A.Text,{copyable:!0,code:!0,children:null===(v=Je.getFieldValue("environments"))||void 0===v?void 0:v.manual}):(0,u.jsxs)(u.Fragment,{children:[(0,u.jsx)(k.Ay,{image:null===(A=Je.getFieldValue("environments"))||void 0===A?void 0:A.version}),null!==(N=Je.getFieldValue("environments"))&&void 0!==N&&N.customizedTag?(0,u.jsx)(p.A,{values:[{label:"Customized",color:"cyan"},{label:null===(M=Je.getFieldValue("environments"))||void 0===M?void 0:M.customizedTag,color:"cyan"}]}):null,(0,u.jsx)(U.A.Text,{copyable:{text:null===(O=Je.getFieldValue("environments"))||void 0===O?void 0:O.version}})]})})]})}),(null===(z=Je.getFieldValue("envvars"))||void 0===z?void 0:z.length)>0&&(0,u.jsx)(ve.A.Item,{label:Ue("session.launcher.EnvironmentVariable"),children:null!==(B=Je.getFieldValue("envvars"))&&void 0!==B&&B.length?(0,u.jsx)(Fe.A,{style:ze?we.A:void 0,codeTagProps:{style:{}},customStyle:{margin:0,width:"100%"},children:c().map(Je.getFieldValue("envvars"),(e=>"".concat((null===e||void 0===e?void 0:e.variable)||"",'="').concat((null===e||void 0===e?void 0:e.value)||"",'"'))).join("\n")}):(0,u.jsx)(U.A.Text,{type:"secondary",children:"-"})})]})}),(0,u.jsx)(m,{title:Ue("session.launcher.ResourceAllocation"),status:c().some(Je.getFieldValue("resource"),((e,s)=>Je.getFieldError(["resource",s]).length>0))||Je.getFieldError(["num_of_sessions"]).length>0||Je.getFieldError("resourceGroup").length>0?"error":void 0,size:"small",extraButtonTitle:Ue("button.Edit"),onClickExtraButton:()=>{qe(Qe.findIndex((e=>"environment"===e.key)))},children:(0,u.jsxs)(x.A,{direction:"column",align:"stretch",children:[c().some(null===(R=Je.getFieldValue("resource"))||void 0===R?void 0:R.resource,((e,s)=>Je.getFieldWarning(["resource",s]).length>0))&&(0,u.jsx)(Ae.A,{type:"warning",showIcon:!0,message:Ue("session.launcher.EnqueueComputeSessionWarning")}),(0,u.jsxs)(ve.A,{column:2,children:[(0,u.jsx)(ve.A.Item,{label:Ue("general.ResourceGroup"),span:2,children:Je.getFieldValue("resourceGroup")||(0,u.jsx)(U.A.Text,{type:"secondary",children:Ue("general.None")})}),(0,u.jsx)(ve.A.Item,{label:Ue("session.launcher.ResourceAllocationPerContainer"),span:2,children:(0,u.jsxs)(x.A,{direction:"row",align:"start",gap:"sm",wrap:"wrap",style:{flex:1},children:["custom"===Je.getFieldValue("allocationPreset")?"":(0,u.jsx)(S.A,{children:Je.getFieldValue("allocationPreset")}),(0,u.jsx)(Ve,{form:Je})]})}),(0,u.jsx)(ve.A.Item,{label:Ue("session.launcher.NumberOfContainer"),children:1===Je.getFieldValue("cluster_size")?Je.getFieldValue("num_of_sessions"):Je.getFieldValue("cluster_size")}),(0,u.jsx)(ve.A.Item,{label:Ue("session.launcher.ClusterMode"),children:"single-node"===Je.getFieldValue("cluster_mode")?Ue("session.launcher.SingleNode"):Ue("session.launcher.MultiNode")})]}),(0,u.jsx)(o.A,{size:"small",type:"inner",title:Ue("session.launcher.TotalAllocation"),children:(0,u.jsx)(x.A,{direction:"row",gap:"xxs",children:(0,u.jsx)(Ve,{form:Je,containerCount:1===Je.getFieldValue("cluster_size")?Je.getFieldValue("num_of_sessions"):Je.getFieldValue("cluster_size")})})})]})}),(0,u.jsx)(m,{title:Ue("webui.menu.Data&Storage"),size:"small",status:Je.getFieldError("vfoldersAliasMap").length>0?"error":void 0,extraButtonTitle:Ue("button.Edit"),onClickExtraButton:()=>{qe(Qe.findIndex((e=>"storage"===e.key)))},children:(null===(K=Je.getFieldValue("mounts"))||void 0===K?void 0:K.length)>0?(0,u.jsx)(J.A,{rowKey:"name",size:"small",pagination:!1,columns:[{dataIndex:"name",title:Ue("data.folders.Name")},{dataIndex:"alias",title:Ue("session.launcher.FolderAlias"),render:(e,s)=>c().isEmpty(e)?(0,u.jsx)(U.A.Text,{type:"secondary",style:{opacity:.7},children:"/home/work/".concat(s.name)}):e}],dataSource:c().map(Je.getFieldValue("mounts"),(e=>{var s;return{name:e,alias:null===(s=Je.getFieldValue("vfoldersAliasMap"))||void 0===s?void 0:s[e]}}))}):(0,u.jsx)(Ae.A,{type:"warning",showIcon:!0,message:Ue("session.launcher.NoFolderMounted")})}),(0,u.jsx)(m,{title:"Network",size:"small",status:Je.getFieldError("ports").length>0?"error":void 0,extraButtonTitle:Ue("button.Edit"),onClickExtraButton:()=>{qe(Qe.findIndex((e=>"network"===e.key)))},children:(0,u.jsx)(ve.A,{size:"small",children:(0,u.jsx)(ve.A.Item,{label:Ue("session.launcher.PreOpenPortTitle"),children:(0,u.jsxs)(x.A,{direction:"row",gap:"xs",style:{flex:1},wrap:"wrap",children:[c().sortBy(Je.getFieldValue("ports"),(e=>parseInt(e))).map((e=>(0,u.jsx)(I,{value:e,style:{margin:0},children:e}))),c().isArray(Je.getFieldValue("ports"))&&0!==(null===(W=Je.getFieldValue("ports"))||void 0===W?void 0:W.length)?null:(0,u.jsx)(U.A.Text,{type:"secondary",children:Ue("general.None")})]})})})})]}),(0,u.jsxs)(x.A,{direction:"row",justify:"between",children:[(0,u.jsx)(x.A,{gap:"sm",children:(0,u.jsx)(je.A,{title:Ue("button.Reset"),description:Ue("session.launcher.ResetFormConfirm"),onConfirm:()=>{Je.resetFields(),Be("/session/start")},icon:(0,u.jsx)(L.A,{style:{color:Ge.colorError}}),okText:Ue("button.Reset"),okButtonProps:{danger:!0},children:(0,u.jsx)(a.Ay,{danger:!0,type:"link",style:{paddingRight:0,paddingLeft:0},children:Ue("button.Reset")})})}),(0,u.jsxs)(x.A,{direction:"row",gap:"sm",children:[_e>0&&(0,u.jsx)(a.Ay,{onClick:()=>{qe(_e-1)},icon:(0,u.jsx)(te.A,{}),disabled:X,children:Ue("button.Previous")}),_e===Qe.length-1?(0,u.jsx)(H.A,{title:Xe?Ue("session.launcher.PleaseCompleteForm"):void 0,children:(0,u.jsx)(a.Ay,{type:"primary",icon:(0,u.jsx)(le.A,{}),disabled:Xe,onClick:()=>{Ie(!0),Je.validateFields().then((async e=>{if(c().isEmpty(e.mounts)||0===e.mounts.length){if(!await new Promise((e=>{q.modal.confirm({title:Ue("session.launcher.NoFolderMounted"),content:(0,u.jsxs)(u.Fragment,{children:[Ue("session.launcher.HomeDirectoryDeletionDialog"),(0,u.jsx)("br",{}),(0,u.jsx)("br",{}),Ue("session.launcher.LaunchConfirmationDialog"),(0,u.jsx)("br",{}),(0,u.jsx)("br",{}),Ue("dialog.ask.DoYouWantToProceed")]}),onOk:()=>{e(!0)},okText:Ue("session.launcher.Start"),onCancel:()=>{e(!1)},closable:!0})})))return}const s=e.environments.manual||e.environments.version;let[n,t]=s?s.split("@"):["",""];const l=c().isEmpty(e.sessionName)?Te():e.sessionName,r={kernelName:n,architecture:t,sessionName:l,config:{type:e.sessionType,..."batch"===e.sessionType?{startsAt:e.batch.enabled?e.batch.scheduleDate:void 0,startupCommand:e.batch.command}:{},group_name:Ke.name,domain:$._config.domainName,scaling_group:e.resourceGroup,cluster_mode:e.cluster_mode,cluster_size:e.cluster_size,maxWaitSeconds:15,cpu:e.resource.cpu,mem:e.resource.mem,shmem:(0,D.Mh)(e.resource.mem,"4g")>0&&(0,D.Mh)(e.resource.shmem,"1g")<0?"1g":e.resource.shmem,...e.resource.accelerator>0?{[e.resource.acceleratorType]:e.resource.accelerator}:void 0,mounts:e.mounts,mount_map:e.vfoldersAliasMap,env:{...c().fromPairs(e.envvars.map((e=>[e.variable,e.value]))),...c().omit(e.hpcOptimization,"autoEnabled")},preopen_ports:c().map(e.ports,(e=>parseInt(e)))}},a=c().map(c().range(e.num_of_sessions||1),(s=>{const n=(e.num_of_sessions||1)>1?"".concat(r.sessionName,"-").concat(Se(),"-").concat(s):r.sessionName;return $.createIfNotExists(r.kernelName,n,r.config,2e4,r.architecture).then((e=>{if(null===e||void 0===e||!e.created)throw new Error(Ue("session.launcher.SessionAlreadyExists"));return e})).catch((e=>{throw e}))}));Re(De||"/job"),Le({key:"session-launcher:"+l,backgroundTask:{promise:Promise.all(a),status:"pending",statusDescriptions:{pending:Ue("session.PreparingSession"),resolved:Ue("eduapi.ComputeSessionPrepared")}},duration:0,message:Ue("general.Session")+": "+l,open:!0}),await Promise.all(a).then((s=>{let[n]=s;if(1===e.num_of_sessions&&"batch"!==e.sessionType){const e=n;let s;s="kernelId"in e?{"session-name":e.kernelId,"access-key":"",mode:G}:{"session-uuid":e.sessionId,"session-name":e.sessionName,"access-key":"",mode:G};const t=e.servicePorts;!0===Array.isArray(t)?s["app-services"]=t.map((e=>e.name)):s["app-services"]=[],t.length>0&&globalThis.appLauncher.showLauncher(s)}})).catch((()=>{}))})).catch((e=>{console.log("validation errors",e)})).finally((()=>{Ie(!1)}))},loading:X,children:Ue("session.launcher.Launch")})}):(0,u.jsxs)(a.Ay,{type:"primary",ghost:!0,onClick:()=>{qe(_e+1)},children:[Ue("button.Next")," ",(0,u.jsx)(re.A,{})]}),_e!==Qe.length-1&&(0,u.jsxs)(a.Ay,{onClick:()=>{qe(Qe.length-1)},children:[Ue("session.launcher.SkipToConfirmAndLaunch"),(0,u.jsx)(ae.A,{})]})]})]})]})})})}),He.lg&&(0,u.jsx)(x.A,{style:{position:"sticky",top:80},children:(0,u.jsx)(ye.A,{size:"small",direction:"vertical",current:_e,onChange:e=>{qe(e)},items:c().map(Qe,((e,s)=>({...e,status:s===_e?"process":"wait"})))})})]})]})}}}]);
//# sourceMappingURL=310.90232733.chunk.js.map