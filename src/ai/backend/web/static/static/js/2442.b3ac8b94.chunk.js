"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[2442],{32461:(e,n,l)=>{l.d(n,{A:()=>g});var a=l(89130),i=l(67318),t=l(4342),r=l(23702),o=l(67378),s=l(60822),d=l(89608),u=l.n(d),m=l(43373),c=l(56762),v=l(73689);const g=e=>{let{formItemProps:n,...l}=e;const d=(0,m.useRef)(null),{t:g}=(0,c.Bd)(),p=r.A.useFormInstance();return(0,v.jsx)(r.A.List,{...l,children:(e,m)=>{let{add:c,remove:h}=m;return(0,v.jsxs)(a.A,{direction:"column",gap:"xs",align:"stretch",children:[e.map(((t,s)=>{let{key:m,name:c,...f}=t;return(0,v.jsxs)(a.A,{direction:"row",align:"baseline",gap:"xs",children:[(0,v.jsx)(r.A.Item,{...f,style:{marginBottom:0,flex:1},name:[c,"variable"],rules:[{required:!0,message:g("session.launcher.EnterEnvironmentVariable")},{pattern:/^[a-zA-Z_][a-zA-Z0-9_]*$/,message:g("session.launcher.EnvironmentVariableNamePatternError")},e=>{let{getFieldValue:n}=e;return{validator(e,a){const i=u().map(n(l.name),(e=>null===e||void 0===e?void 0:e.variable));return!u().isEmpty(a)&&i.length>0&&u().filter(i,(e=>e===a)).length>1?Promise.reject(g("session.launcher.EnvironmentVariableDuplicateName")):Promise.resolve()}}}],...n,children:(0,v.jsx)(o.A,{ref:s===e.length-1?d:null,placeholder:"Variable",onChange:()=>{const n=e.map(((e,n)=>[l.name,n,"variable"]));p.validateFields(n)}})}),(0,v.jsx)(r.A.Item,{...f,name:[c,"value"],style:{marginBottom:0,flex:1},rules:[{required:!0,message:g("session.launcher.EnvironmentVariableValueRequired")}],validateTrigger:["onChange","onBlur"],children:(0,v.jsx)(o.A,{placeholder:"Value"})}),(0,v.jsx)(i.A,{onClick:()=>h(c)})]},m)})),(0,v.jsx)(r.A.Item,{noStyle:!0,children:(0,v.jsx)(s.Ay,{type:"dashed",onClick:()=>{c(),setTimeout((()=>{d.current&&d.current.focus()}),0)},icon:(0,v.jsx)(t.A,{}),block:!0,children:g("session.launcher.AddEnvironmentVariable")})})]})}})}},98957:(e,n,l)=>{l.d(n,{A:()=>k});var a=l(58879),i=l(51593),t=l(84553),r=l(98401),o=l(89130);var s,d=l(16272),u=l(6597),m=l(23702),c=l(50868),v=l(69056),g=l(15934),p=l(96799),h=l(67378),f=l(89608),y=l.n(f),x=l(43373),A=l(56762),_=l(88522),j=l(73689);const k=e=>{var n;let{filter:f,showPrivate:k}=e;const w=m.A.useFormInstance(),F=m.A.useWatch("environments",{form:w,preserve:!0}),b=(0,i.CX)(),[V,S]=(0,x.useState)(""),[I,N]=(0,x.useState)(""),{t:C}=(0,A.Bd)(),[K,{getImageMeta:M}]=(0,i.Gj)(),{token:P}=c.A.useToken(),{isDarkMode:E}=(0,t.e)(),T=(0,x.useRef)(null),L=(0,x.useRef)(null),R=null!==b&&void 0!==b&&null!==(n=b._config)&&void 0!==n&&n.showNonInstalledImages?{}:{installed:!0},{images:$}=(0,_.useLazyLoadQuery)(void 0!==s?s:s=l(38044),R,{fetchPolicy:"store-and-network"});(0,x.useEffect)((()=>{var e,n,l;if(!y().isEmpty(null===F||void 0===F?void 0:F.manual))return void((F.environment||F.version)&&w.setFieldsValue({environments:{environment:void 0,version:void 0,image:void 0}}));let i,t,r,o,s=null===(e=w.getFieldValue("environments"))||void 0===e?void 0:e.version;var d,u;(s&&s.indexOf("@")<0&&(s+="@x86_64"),s&&y().find(B,(e=>(i=y().find(e.environmentGroups,(e=>(t=y().find(e.images,(e=>(0,a.A_)(e)===s)),!!t))),!!i))),i?(r=i,o=t):w.getFieldValue(["environments","environment"])&&y().find(B,(e=>{var n;return r=y().find(e.environmentGroups,(e=>e.environmentName===w.getFieldValue(["environments","environment"]))),o=null===(n=r)||void 0===n?void 0:n.images[0],!!r})),r&&o)||(r=null===(d=B[0])||void 0===d?void 0:d.environmentGroups[0],o=null===(u=r)||void 0===u?void 0:u.images[0]);const m=null===(n=y().find(null===(l=o)||void 0===l?void 0:l.labels,(e=>null!==e&&"ai.backend.customized-image.name"===(null===e||void 0===e?void 0:e.key))))||void 0===n?void 0:n.value;o?!i&&b._config.allow_manual_image_name_for_session&&s?w.setFieldsValue({environments:{environment:void 0,version:void 0,image:void 0,manual:s,customizedTag:null!==m&&void 0!==m?m:void 0}}):w.setFieldsValue({environments:{environment:r.environmentName,version:(0,a.A_)(o),image:o,customizedTag:null!==m&&void 0!==m?m:void 0}}):b._config.allow_manual_image_name_for_session&&w.setFieldValue(["environments","manual"],s)}),[null===F||void 0===F?void 0:F.version,null===F||void 0===F?void 0:F.manual]);const B=(0,x.useMemo)((()=>y().chain($).filter((e=>(!!k||!(e=>y().some(null===e||void 0===e?void 0:e.labels,(e=>{var n;return"ai.backend.features"===(null===e||void 0===e?void 0:e.key)&&(null===e||void 0===e||null===(n=e.value)||void 0===n?void 0:n.split(" ").includes("private"))})))(e))&&(!f||f(e)))).groupBy((e=>{var n;return(null===K||void 0===K||null===(n=K.imageInfo[M((0,a.A_)(e)||"").key])||void 0===n?void 0:n.group)||"Custom Environments"})).map(((e,n)=>({groupName:n,environmentGroups:y().chain(e).groupBy((e=>(null===e||void 0===e?void 0:e.registry)+"/"+(null===e||void 0===e?void 0:e.name))).map(((e,n)=>{var l,i;const t=null===(l=n.split("/"))||void 0===l?void 0:l[2];return{environmentName:n,displayName:t&&(null===K||void 0===K||null===(i=K.imageInfo[t])||void 0===i?void 0:i.name)||y().last(n.split("/")),prefix:y().chain(n).split("/").drop(1).dropRight(1).join("/").value(),images:e.sort(((e,n)=>{var l,i,t,r,o,s;return function(e,n){const l=e.split(".").map(Number),a=n.split(".").map(Number);for(let i=0;i<Math.max(l.length,a.length);i++){const e=l[i]||0,n=a[i]||0;if(e>n)return 1;if(e<n)return-1}return 0}(null!==(l=null===n||void 0===n||null===(i=n.tag)||void 0===i||null===(t=i.split("-"))||void 0===t?void 0:t[0])&&void 0!==l?l:"",null!==(r=null===e||void 0===e||null===(o=e.tag)||void 0===o||null===(s=o.split("-"))||void 0===s?void 0:s[0])&&void 0!==r?r:"")||(0,a._f)(null===e||void 0===e?void 0:e.architecture,null===n||void 0===n?void 0:n.architecture)}))}})).sortBy((e=>e.displayName)).value()}))).sortBy((e=>e.groupName)).value()),[$,K,f,k]),{fullNameMatchedImage:O}=(0,x.useMemo)((()=>{let e,n;return V.length&&y().chain(B.flatMap((e=>e.environmentGroups)).find((l=>(n=l,e=y().find(l.images,(e=>(0,a.A_)(e)===V)),!!e)))).value(),{fullNameMatchedImage:e,fullNameMatchedImageGroup:n}}),[V,B]);return(0,j.jsxs)(j.Fragment,{children:[(0,j.jsx)("style",{children:"/* Change the image and tags of the select option when the selection is opened  */\ndiv.image-environment-select-form-item\n  div.ant-select-open\n  span.ant-select-selection-item\n  div\n  img,\ndiv.image-environment-select-form-item\n  div.ant-select-open\n  span.ant-select-selection-item\n  div\n  span.ant-tag {\n  opacity: 0.5;\n}\n\ndiv.image-environment-select-form-item\n  div.ant-select-item-option-content\n  div.tag-wrap-light {\n  /* flex: 1 !important; */\n  flex-wrap: wrap !important;\n}\n\ndiv.image-environment-select-form-item\n  div.ant-select-item-option-content\n  div.tag-wrap-dark {\n  /* flex: 1 !important; */\n  flex-wrap: wrap !important;\n}\n\ndiv.image-environment-select-form-item\n  span.ant-select-selection-item\n  div.tag-wrap-light {\n  overflow: hidden;\n}\n\ndiv.image-environment-select-form-item\n  span.ant-select-selection-item\n  div.tag-wrap-dark {\n  overflow: hidden;\n}\n\ndiv.image-environment-select-form-item\n  span.ant-select-selection-item\n  div.tag-wrap-light::after {\n  content: '';\n  position: absolute;\n  top: 0;\n  right: 0;\n  bottom: 0;\n  width: 10px; /* Width of the transparent gradient area */\n  background: linear-gradient(\n    to right,\n    rgba(255, 255, 255, 0),\n    rgba(255, 255, 255, 1)\n  );\n}\n\ndiv.image-environment-select-form-item\n  span.ant-select-selection-item\n  div.tag-wrap-dark::after {\n  content: '';\n  position: absolute;\n  top: 0;\n  right: 0;\n  bottom: 0;\n  width: 10px;\n  background: linear-gradient(\n    to right,\n    rgba(20, 20, 20, 0),\n    rgba(20, 20, 20, 1)\n  );\n}\n"}),(0,j.jsx)(m.A.Item,{className:"image-environment-select-form-item",name:["environments","environment"],label:`${C("session.launcher.Environments")} / ${C("session.launcher.Version")}`,rules:[{required:y().isEmpty(null===F||void 0===F?void 0:F.manual)}],style:{marginBottom:10},children:(0,j.jsx)(v.A,{ref:T,showSearch:!0,searchValue:V,onSearch:S,defaultActiveFirstOption:!0,optionFilterProp:"filterValue",onChange:e=>{if(O)w.setFieldsValue({environments:{environment:(null===O||void 0===O?void 0:O.name)||"",version:(0,a.A_)(O),image:O}});else{const n=B.flatMap((e=>e.environmentGroups)).filter((n=>n.environmentName===e))[0].images[0];w.setFieldsValue({environments:{environment:(null===n||void 0===n?void 0:n.name)||"",version:(0,a.A_)(n),image:n}})}},disabled:b._config.allow_manual_image_name_for_session&&!y().isEmpty(null===F||void 0===F?void 0:F.manual),children:O?(0,j.jsx)(v.A.Option,{value:null===O||void 0===O?void 0:O.name,filterValue:(0,a.A_)(O),children:(0,j.jsxs)(o.A,{direction:"row",align:"center",gap:"xs",style:{display:"inline-flex"},children:[(0,j.jsx)(d.A,{image:(0,a.A_)(O)||"",style:{width:15,height:15}}),(0,a.A_)(O)]})}):y().map(B,(e=>(0,j.jsx)(v.A.OptGroup,{label:e.groupName,children:y().map(e.environmentGroups,(e=>{var n;const l=e.images[0],i=null===K||void 0===K?void 0:K.imageInfo[null===(n=e.environmentName.split("/"))||void 0===n?void 0:n[2]],t=[];let r=null;e.prefix&&!["lablup","cloud","stable"].includes(e.prefix)&&(t.push(e.prefix),r=(0,j.jsx)(g.A,{color:"purple",children:(0,j.jsx)(u.A,{keyword:V,children:e.prefix})}));const s=y().map(null===i||void 0===i?void 0:i.label,(e=>y().isUndefined(e.category)&&e.tag&&e.color?(t.push(e.tag),(0,j.jsx)(g.A,{color:e.color,children:(0,j.jsx)(u.A,{keyword:V,children:e.tag},e.tag)},e.tag)):null));return(0,j.jsx)(v.A.Option,{value:e.environmentName,filterValue:e.displayName+"\t"+t.join("\t"),children:(0,j.jsxs)(o.A,{direction:"row",justify:"between",children:[(0,j.jsxs)(o.A,{direction:"row",align:"center",gap:"xs",children:[(0,j.jsx)(d.A,{image:(0,a.A_)(l)||"",style:{width:15,height:15}}),(0,j.jsx)(u.A,{keyword:V,children:e.displayName})]}),(0,j.jsxs)(o.A,{direction:"row",className:E?"tag-wrap-dark":"tag-wrap-light",style:{marginLeft:P.marginXS,flexShrink:1},children:[r,s]})]})},e.environmentName)}))},e.groupName)))})}),(0,j.jsx)(m.A.Item,{noStyle:!0,shouldUpdate:(e,n)=>{var l,a;return(null===(l=e.environments)||void 0===l?void 0:l.environment)!==(null===(a=n.environments)||void 0===a?void 0:a.environment)},children:e=>{var n;let l,{getFieldValue:i}=e;return y().find(B,(e=>y().find(e.environmentGroups,(e=>{var n;return e.environmentName===(null===(n=i("environments"))||void 0===n?void 0:n.environment)&&(l=e,!0)})))),(0,j.jsx)(m.A.Item,{className:"image-environment-select-form-item",name:["environments","version"],rules:[{required:y().isEmpty(null===F||void 0===F?void 0:F.manual)}],children:(0,j.jsx)(v.A,{ref:L,onChange:e=>{const n=y().find($,(n=>(0,a.A_)(n)===e));w.setFieldValue(["environments","image"],n)},showSearch:!0,searchValue:I,onSearch:N,optionFilterProp:"filterValue",dropdownRender:e=>(0,j.jsxs)(j.Fragment,{children:[(0,j.jsxs)(o.A,{style:{fontWeight:P.fontWeightStrong,paddingLeft:P.paddingSM},children:[C("session.launcher.Version"),(0,j.jsx)(p.A,{type:"vertical"}),C("session.launcher.Base"),(0,j.jsx)(p.A,{type:"vertical"}),C("session.launcher.Architecture"),(0,j.jsx)(p.A,{type:"vertical"}),C("session.launcher.Requirements")]}),(0,j.jsx)(p.A,{style:{margin:"8px 0"}}),e]}),disabled:b._config.allow_manual_image_name_for_session&&!y().isEmpty(null===F||void 0===F?void 0:F.manual),children:y().map(y().uniqBy(null===(n=l)||void 0===n?void 0:n.images,"digest"),(e=>{var n;const[l,i,...t]=(null===e||void 0===e||null===(n=e.tag)||void 0===n?void 0:n.split("-"))||["","",""];let s=null===K||void 0===K?void 0:K.tagAlias[i];if(!s){for(const[e,n]of Object.entries((null===K||void 0===K?void 0:K.tagReplace)||{})){const l=new RegExp(e);l.test(i)&&(s=null===i||void 0===i?void 0:i.replace(l,n))}s||(s=i)}const d=[],m=y().chain(t).filter((e=>!e.startsWith("customized_"))).map(((e,n)=>(0,j.jsx)(r.A,{values:y().split((null===K||void 0===K?void 0:K.tagAlias[e])||e,":").map((e=>(d.push(e),(0,j.jsx)(u.A,{keyword:I,children:e},e))))},n))).value(),c=null===e||void 0===e?void 0:e.labels;if(c){const e=y().findIndex(c,(e=>null!==e&&"ai.backend.customized-image.name"===(null===e||void 0===e?void 0:e.key)));if(e&&c[e]){var g;const n=(null===(g=c[e])||void 0===g?void 0:g.value)||"";d.push("Customized"),d.push(n),m.push((0,j.jsx)(r.A,{values:[{label:(0,j.jsx)(u.A,{keyword:I,children:"Customized"},"Customized"),color:"cyan"},{label:(0,j.jsx)(u.A,{keyword:I,children:n},n),color:"cyan"}]},m.length+1))}}return(0,j.jsx)(v.A.Option,{value:(0,a.A_)(e),filterValue:[l,s,null===e||void 0===e?void 0:e.architecture,...d].join("\t"),children:(0,j.jsxs)(o.A,{direction:"row",justify:"between",children:[(0,j.jsxs)(o.A,{direction:"row",children:[(0,j.jsx)(u.A,{keyword:I,children:l}),(0,j.jsx)(p.A,{type:"vertical"}),(0,j.jsx)(u.A,{keyword:I,children:s}),(0,j.jsx)(p.A,{type:"vertical"}),(0,j.jsx)(u.A,{keyword:I,children:null===e||void 0===e?void 0:e.architecture})]}),(0,j.jsx)(o.A,{direction:"row",className:E?"tag-wrap-dark":"tag-wrap-light",style:{marginLeft:P.marginXS,flexShrink:1},children:m||"-"})]})},null===e||void 0===e?void 0:e.digest)}))})})}}),(0,j.jsx)(m.A.Item,{label:C("session.launcher.ManualImageName"),name:["environments","manual"],style:{display:b._config.allow_manual_image_name_for_session?"block":"none"},children:(0,j.jsx)(h.A,{allowClear:!0,onChange:e=>{y().isEmpty(e)||w.setFieldsValue({environments:{environment:void 0,version:void 0,image:void 0}})}})}),(0,j.jsx)(m.A.Item,{noStyle:!0,hidden:!0,name:["environments","image"],children:(0,j.jsx)(h.A,{})})]})}},71786:(e,n,l)=>{l.d(n,{A:()=>$});var a,i=l(58879),t=l(51593),r=l(68190),o=l(60881),s=l(7194),d=l(15634),u=l(60266),m=l(45719),c=l(89130),v=l(6597),g=l(98401),p=l(89608),h=l.n(p),f=l(43373),y=l(88522),x=l(73689);const A=e=>{let{vFolderFrgmt:n=null,permission:i}=e;const t=(0,y.useFragment)(void 0!==a?a:a=l(34790),n),r=h().chain({r:"green",w:"blue",d:"red"}).map(((e,n)=>{if(((e,n)=>!(null===e||void 0===e||!e.includes(n))||!(null===e||void 0===e||!e.includes("w")||"r"!==n))((null===t||void 0===t?void 0:t.permission)||i,n))return{label:n.toUpperCase(),color:e}})).compact().value();return(0,x.jsx)(g.A,{values:r})};var _,j=l(65666),k=l(58457),w=l(40567),F=l(23702),b=l(85690),V=l(33789),S=l(67378),I=l(60822),N=l(77731),C=l(45679),K=l(15934),M=l(12731),P=l.n(M),E=l(56762);const T=/^[a-zA-Z0-9_/.-]*$/,L="/home/work/",R=e=>{let{filter:n,showAliasInput:a=!1,selectedRowKeys:g=[],onChangeSelectedRowKeys:p,aliasBasePath:M=L,aliasMap:R,onChangeAliasMap:$,rowKey:B="name",onChangeAutoMountedFolders:O,showAutoMountedFoldersSection:q,...z}=e;const G=f.useMemo((()=>e=>e&&e[B]),[B]),[Q,D]=(0,s.A)({value:g,onChange:p},{defaultValue:[]}),[W,U]=(0,s.A)({value:R,onChange:$},{defaultValue:{}}),J=(0,t.CX)(),[X]=(0,r.x)(null===J||void 0===J?void 0:J._config.accessKey),[Z]=F.A.useForm();(0,f.useEffect)((()=>{W&&(Z.setFieldsValue(h().mapValues(W,(e=>e.startsWith(M)?e.slice(M.length):e))),Z.validateFields())}),[W,Z,M]);const{t:H}=(0,E.Bd)(),Y=(0,i.QE)(),ee=(0,d.hd)(),[ne,le]=(0,t.Tw)("first"),[ae,ie]=(0,f.useTransition)(),{data:te}=(0,o.nj)({queryKey:["VFolderSelectQuery",ne,ee.id],queryFn:()=>{const e=new URLSearchParams;return e.set("group_id",ee.id),Y({method:"GET",url:`/folders?${e.toString()}`})},staleTime:1e3}),{domain:re,group:oe,keypair_resource_policy:se}=(0,y.useLazyLoadQuery)(void 0!==_?_:_=l(46385),{domain_name:J._config.domainName,group_id:ee.id,keypair_resource_policy_name:(null===X||void 0===X?void 0:X.resource_policy)||""},{fetchPolicy:"store-and-network",fetchKey:ne}),de=(0,f.useMemo)((()=>{const e=JSON.parse((null===re||void 0===re?void 0:re.allowed_vfolder_hosts)||"{}"),n=JSON.parse((null===oe||void 0===oe?void 0:oe.allowed_vfolder_hosts)||"{}"),l=JSON.parse((null===se||void 0===se?void 0:se.allowed_vfolder_hosts)||"{}"),a=h().merge({},e,n,l),i=Object.keys(a).filter((e=>a[e].includes("mount-in-session")));return null===te||void 0===te?void 0:te.filter((e=>i.includes(e.host)))}),[re,oe,se,te]),ue=(0,f.useMemo)((()=>h().chain(de).filter((e=>{var n;return"ready"===e.status&&(null===(n=e.name)||void 0===n?void 0:n.startsWith("."))})).map((e=>e.name)).value()),[de]);(0,f.useEffect)((()=>{h().isFunction(O)&&O(ue)}),[ue]);const[me,ce]=(0,f.useState)(""),ve=h().chain(de).filter((e=>!n||n(e))).filter((e=>!!Q.includes(G(e))||(!me||e.name.includes(me)))).value(),ge=(0,u.E)(((e,n)=>h().isEmpty(n)?`${M}${e}`:null!==n&&void 0!==n&&n.startsWith("/")?n:`${M}${n}`)),pe=(0,u.E)((()=>{U(h().mapValues(h().pickBy(Z.getFieldsValue(),(e=>!!e)),((e,n)=>ge(n,e)))),Z.validateFields().catch((()=>{}))}));(0,f.useEffect)((()=>{pe()}),[JSON.stringify(Q),pe]);const he=(0,m.useShadowRoot)(),fe=[{title:(0,x.jsxs)(c.A,{direction:"row",gap:"xxs",children:[(0,x.jsx)(b.A.Text,{children:H("data.folders.Name")}),a&&(0,x.jsx)(x.Fragment,{children:(0,x.jsxs)(b.A.Text,{type:"secondary",style:{fontWeight:"normal"},children:["(",H("session.launcher.FolderAlias")," ",(0,x.jsx)(V.A,{title:(0,x.jsx)(E.x6,{i18nKey:"session.launcher.DescFolderAlias"}),getPopupContainer:()=>he,children:(0,x.jsx)(j.A,{})}),")"]})})]}),dataIndex:"name",sorter:(e,n)=>e.name.localeCompare(n.name),render:(e,n)=>{const l=Q.includes(G(n));return(0,x.jsxs)(c.A,{direction:"column",align:"stretch",gap:"xxs",style:a&&l?{display:"inline-flex",height:70,width:"100%"}:{maxWidth:200},children:[(0,x.jsx)(v.A,{keyword:me,children:e}),a&&l&&(0,x.jsx)(F.A.Item,{noStyle:!0,shouldUpdate:(e,l)=>e[G(n)]!==l[G(n)],children:()=>{const e=h()(Q).reduce(((e,n)=>(e[n]=(null===W||void 0===W?void 0:W[n])||ge(n,void 0),e)),{});return(0,x.jsx)(F.A.Item,{name:G(n),rules:[{type:"string",pattern:T,message:H("session.launcher.FolderAliasInvalid")},{type:"string",validator:async(l,a)=>a&&h().some(e,((e,l)=>l!==G(n)&&e===ge(G(n),a)))?Promise.reject(H("session.launcher.FolderAliasOverlapping")):Promise.resolve()},{type:"string",validator:async(e,l)=>{const a=ge(G(n),l);return l&&h().map(ue,(e=>ge("",e))).includes(a)?Promise.reject(H("session.launcher.FolderAliasOverlappingToAutoMount")):Promise.resolve()}}],extra:ge(n.name,Z.getFieldValue(G(n))),children:(0,x.jsx)(S.A,{onClick:e=>{e.stopPropagation()},placeholder:H("session.launcher.FolderAlias"),allowClear:!0,onChange:()=>{pe()}})})}})]})}},{title:H("data.UsageMode"),dataIndex:"usage_mode",sorter:(e,n)=>e.usage_mode.localeCompare(n.usage_mode)},{title:H("data.Host"),dataIndex:"host"},{title:H("data.Type"),dataIndex:"type",sorter:(e,n)=>e.type.localeCompare(n.type),render:(e,n)=>(0,x.jsxs)(c.A,{direction:"column",children:["user"===n.type?(0,x.jsx)(k.A,{title:"User"}):(0,x.jsx)("div",{children:"Group"}),"group"===n.type&&`(${n.group_name})`]})},{title:H("data.Permission"),dataIndex:"permission",sorter:(e,n)=>e.permission.localeCompare(n.permission),render:(e,n)=>(0,x.jsx)(A,{permission:n.permission})},{title:H("data.Created"),dataIndex:"created_at",sorter:(e,n)=>e.created_at.localeCompare(n.created_at),render:(e,n)=>P()(e).format("L")}];return(0,x.jsxs)(c.A,{direction:"column",align:"stretch",gap:"xs",children:[(0,x.jsxs)(c.A,{direction:"row",gap:"xs",justify:"between",children:[(0,x.jsx)(S.A,{value:me,onChange:e=>ce(e.target.value),allowClear:!0,placeholder:H("data.SearchByName")}),(0,x.jsx)(I.Ay,{loading:ae,icon:(0,x.jsx)(w.A,{}),onClick:()=>{ie((()=>{le()}))}})]}),(0,x.jsx)(F.A,{form:Z,component:!1,children:(0,x.jsx)(N.A,{scroll:{x:"max-content"},rowKey:G,rowSelection:{selectedRowKeys:Q,onChange:e=>{D(e)}},showSorterTooltip:!1,columns:fe,dataSource:ve,onRow:(e,n)=>({onClick:n=>{var l;const a=n.target;null!==a&&void 0!==a&&null!==(l=a.classList)&&void 0!==l&&l.contains("ant-table-selection-column")&&(n.stopPropagation(),Q.includes(G(e))?D(Q.filter((n=>n!==G(e)))):D([...Q,G(e)]))}}),...z})}),q&&ue.length>0?(0,x.jsx)(x.Fragment,{children:(0,x.jsx)(C.A,{size:"small",children:(0,x.jsx)(C.A.Item,{label:H("data.AutomountFolders"),children:h().map(ue,(e=>(0,x.jsx)(K.A,{children:e},e)))})})}):null]})},$=e=>{let{filter:n,rowKey:l="name",tableProps:a,...i}=e;const t=F.A.useFormInstance(),{t:r}=(0,E.Bd)();return F.A.useWatch("vfoldersAliasMap",t),(0,x.jsxs)(x.Fragment,{children:[(0,x.jsx)(F.A.Item,{hidden:!0,name:"vfoldersAliasMap",rules:[{validator(e,n){const l=h().chain(t.getFieldValue("mounts")).reduce(((e,l)=>(e[l]=n[l]||"/home/work/"+l,e)),{}).values().value();return h().uniq(l).length!==l.length?Promise.reject(r("session.launcher.FolderAliasOverlapping")):h().some(l,(e=>!T.test(e)))?Promise.reject(r("session.launcher.FolderAliasInvalid")):h().some(t.getFieldValue("autoMountedFolderNames"),(e=>l.includes(L+e)))?Promise.reject(r("session.launcher.FolderAliasOverlappingToAutoMount")):Promise.resolve()}}],children:(0,x.jsx)(S.A,{})}),(0,x.jsx)(F.A.Item,{hidden:!0,name:"autoMountedFolderNames"}),(0,x.jsx)(F.A.Item,{name:"mounts",...i,valuePropName:"selectedRowKeys",trigger:"onChangeSelectedRowKeys",children:(0,x.jsx)(R,{rowKey:l,showAliasInput:!0,aliasMap:t.getFieldValue("vfoldersAliasMap"),onChangeAliasMap:e=>{t.setFieldValue("vfoldersAliasMap",e),t.validateFields(["vfoldersAliasMap"])},pagination:!1,filter:n,showAutoMountedFoldersSection:!0,onChangeAutoMountedFolders:e=>{t.setFieldValue("autoMountedFolderNames",e)},...a})})]})}},38044:(e,n,l)=>{l.r(n),l.d(n,{default:()=>i});const a=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"installed"}],n={alias:null,args:null,kind:"ScalarField",name:"key",storageKey:null},l=[{alias:null,args:[{kind:"Variable",name:"is_installed",variableName:"installed"}],concreteType:"Image",kind:"LinkedField",name:"images",plural:!0,selections:[{alias:null,args:null,kind:"ScalarField",name:"name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"humanized_name",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"tag",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"registry",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"architecture",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"digest",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"installed",storageKey:null},{alias:null,args:null,concreteType:"ResourceLimit",kind:"LinkedField",name:"resource_limits",plural:!0,selections:[n,{alias:null,args:null,kind:"ScalarField",name:"min",storageKey:null},{alias:null,args:null,kind:"ScalarField",name:"max",storageKey:null}],storageKey:null},{alias:null,args:null,concreteType:"KVPair",kind:"LinkedField",name:"labels",plural:!0,selections:[n,{alias:null,args:null,kind:"ScalarField",name:"value",storageKey:null}],storageKey:null}],storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"ImageEnvironmentSelectFormItemsQuery",selections:l,type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"ImageEnvironmentSelectFormItemsQuery",selections:l},params:{cacheID:"ea71f4a3948d4742dd6bb11ef80a8300",id:null,metadata:{},name:"ImageEnvironmentSelectFormItemsQuery",operationKind:"query",text:"query ImageEnvironmentSelectFormItemsQuery(\n  $installed: Boolean\n) {\n  images(is_installed: $installed) {\n    name\n    humanized_name\n    tag\n    registry\n    architecture\n    digest\n    installed\n    resource_limits {\n      key\n      min\n      max\n    }\n    labels {\n      key\n      value\n    }\n  }\n}\n"}}}();a.hash="33367bd6e1532b42b61629ef9d3dc46b";const i=a},34790:(e,n,l)=>{l.r(n),l.d(n,{default:()=>i});const a={argumentDefinitions:[],kind:"Fragment",metadata:null,name:"VFolderPermissionTag_VFolder",selections:[{alias:null,args:null,kind:"ScalarField",name:"permission",storageKey:null}],type:"VirtualFolder",abstractKey:null,hash:"d3b0f85629ac8c6f45ef363938f66067"},i=a},46385:(e,n,l)=>{l.r(n),l.d(n,{default:()=>i});const a=function(){var e=[{defaultValue:null,kind:"LocalArgument",name:"domain_name"},{defaultValue:null,kind:"LocalArgument",name:"group_id"},{defaultValue:null,kind:"LocalArgument",name:"keypair_resource_policy_name"}],n=[{alias:null,args:null,kind:"ScalarField",name:"allowed_vfolder_hosts",storageKey:null}],l=[{alias:null,args:[{kind:"Variable",name:"name",variableName:"domain_name"}],concreteType:"Domain",kind:"LinkedField",name:"domain",plural:!1,selections:n,storageKey:null},{alias:null,args:[{kind:"Variable",name:"domain_name",variableName:"domain_name"},{kind:"Variable",name:"id",variableName:"group_id"}],concreteType:"Group",kind:"LinkedField",name:"group",plural:!1,selections:n,storageKey:null},{alias:null,args:[{kind:"Variable",name:"name",variableName:"keypair_resource_policy_name"}],concreteType:"KeyPairResourcePolicy",kind:"LinkedField",name:"keypair_resource_policy",plural:!1,selections:n,storageKey:null}];return{fragment:{argumentDefinitions:e,kind:"Fragment",metadata:null,name:"VFolderTableProjectQuery",selections:l,type:"Queries",abstractKey:null},kind:"Request",operation:{argumentDefinitions:e,kind:"Operation",name:"VFolderTableProjectQuery",selections:l},params:{cacheID:"2c2ce905afd89e93c6d761f22ed59f3d",id:null,metadata:{},name:"VFolderTableProjectQuery",operationKind:"query",text:"query VFolderTableProjectQuery(\n  $domain_name: String!\n  $group_id: UUID!\n  $keypair_resource_policy_name: String!\n) {\n  domain(name: $domain_name) {\n    allowed_vfolder_hosts\n  }\n  group(id: $group_id, domain_name: $domain_name) {\n    allowed_vfolder_hosts\n  }\n  keypair_resource_policy(name: $keypair_resource_policy_name) {\n    allowed_vfolder_hosts\n  }\n}\n"}}}();a.hash="ccdbaa52a63c2ea005423e7c541eff80";const i=a}}]);
//# sourceMappingURL=2442.b3ac8b94.chunk.js.map