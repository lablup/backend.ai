"use strict";(self.webpackChunkbackend_ai_webui_react=self.webpackChunkbackend_ai_webui_react||[]).push([[7472],{95091:(e,t,n)=>{n.r(t),n.d(t,{default:()=>L});var s=n(72375),i=n(23441),r=n(69949),l=n(72338),a=n(81654),o=n(68260),c=n(30788),u=n(72932),h=n(61110),d=n(65489),f=n(25913),_=n(55093),g=n(33364),m=n(79569);const b=e=>{let{status:t="default"}=e;const{t:n}=(0,g.Bd)();return(0,m.jsx)(_.Suspense,{fallback:(0,m.jsx)(d.A,{indicator:(0,m.jsx)(o.A,{spin:!0})}),children:(0,m.jsx)(f.A,{color:(e=>{switch(e){case"default":case"finished":default:return"default";case"processing":return"processing";case"error":return"error";case"success":return"success"}})(t),icon:"processing"===t?(0,m.jsx)(o.A,{spin:!0}):"finished"===t?(0,m.jsx)(c.A,{}):"error"===t?(0,m.jsx)(u.A,{}):(0,m.jsx)(h.A,{}),children:n("processing"===t?"modelService.Processing":"finished"===t?"modelService.Finished":"error"===t?"modelService.Error":"modelService.Ready")})})};var p,x,S,v,y=function(e,t){return Object.defineProperty?Object.defineProperty(e,"raw",{value:t}):e.raw=t,e};!function(e){e[e.EOS=0]="EOS",e[e.Text=1]="Text",e[e.Incomplete=2]="Incomplete",e[e.ESC=3]="ESC",e[e.Unknown=4]="Unknown",e[e.SGR=5]="SGR",e[e.OSCURL=6]="OSCURL"}(p||(p={}));class k{constructor(){this.VERSION="6.0.2",this.setup_palettes(),this._use_classes=!1,this.bold=!1,this.faint=!1,this.italic=!1,this.underline=!1,this.fg=this.bg=null,this._buffer="",this._url_allowlist={http:1,https:1},this._escape_html=!0,this.boldStyle="font-weight:bold",this.faintStyle="opacity:0.7",this.italicStyle="font-style:italic",this.underlineStyle="text-decoration:underline"}set use_classes(e){this._use_classes=e}get use_classes(){return this._use_classes}set url_allowlist(e){this._url_allowlist=e}get url_allowlist(){return this._url_allowlist}set escape_html(e){this._escape_html=e}get escape_html(){return this._escape_html}set boldStyle(e){this._boldStyle=e}get boldStyle(){return this._boldStyle}set faintStyle(e){this._faintStyle=e}get faintStyle(){return this._faintStyle}set italicStyle(e){this._italicStyle=e}get italicStyle(){return this._italicStyle}set underlineStyle(e){this._underlineStyle=e}get underlineStyle(){return this._underlineStyle}setup_palettes(){this.ansi_colors=[[{rgb:[0,0,0],class_name:"ansi-black"},{rgb:[187,0,0],class_name:"ansi-red"},{rgb:[0,187,0],class_name:"ansi-green"},{rgb:[187,187,0],class_name:"ansi-yellow"},{rgb:[0,0,187],class_name:"ansi-blue"},{rgb:[187,0,187],class_name:"ansi-magenta"},{rgb:[0,187,187],class_name:"ansi-cyan"},{rgb:[255,255,255],class_name:"ansi-white"}],[{rgb:[85,85,85],class_name:"ansi-bright-black"},{rgb:[255,85,85],class_name:"ansi-bright-red"},{rgb:[0,255,0],class_name:"ansi-bright-green"},{rgb:[255,255,85],class_name:"ansi-bright-yellow"},{rgb:[85,85,255],class_name:"ansi-bright-blue"},{rgb:[255,85,255],class_name:"ansi-bright-magenta"},{rgb:[85,255,255],class_name:"ansi-bright-cyan"},{rgb:[255,255,255],class_name:"ansi-bright-white"}]],this.palette_256=[],this.ansi_colors.forEach((e=>{e.forEach((e=>{this.palette_256.push(e)}))}));let e=[0,95,135,175,215,255];for(let n=0;n<6;++n)for(let t=0;t<6;++t)for(let s=0;s<6;++s){let i={rgb:[e[n],e[t],e[s]],class_name:"truecolor"};this.palette_256.push(i)}let t=8;for(let n=0;n<24;++n,t+=10){let e={rgb:[t,t,t],class_name:"truecolor"};this.palette_256.push(e)}}escape_txt_for_html(e){return this._escape_html?e.replace(/[&<>"']/gm,(e=>"&"===e?"&amp;":"<"===e?"&lt;":">"===e?"&gt;":'"'===e?"&quot;":"'"===e?"&#x27;":void 0)):e}append_buffer(e){var t=this._buffer+e;this._buffer=t}get_next_packet(){var e={kind:p.EOS,text:"",url:""},t=this._buffer.length;if(0==t)return e;var n=this._buffer.indexOf("\x1b");if(-1==n)return e.kind=p.Text,e.text=this._buffer,this._buffer="",e;if(n>0)return e.kind=p.Text,e.text=this._buffer.slice(0,n),this._buffer=this._buffer.slice(n),e;if(0==n){if(t<3)return e.kind=p.Incomplete,e;var s=this._buffer.charAt(1);if("["!=s&&"]"!=s&&"("!=s)return e.kind=p.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;if("["==s){this._csi_regex||(this._csi_regex=w(x||(x=y(["\n                        ^                           # beginning of line\n                                                    #\n                                                    # First attempt\n                        (?:                         # legal sequence\n                          \x1b[                      # CSI\n                          ([<-?]?)              # private-mode char\n                          ([d;]*)                    # any digits or semicolons\n                          ([ -/]?               # an intermediate modifier\n                          [@-~])                # the command\n                        )\n                        |                           # alternate (second attempt)\n                        (?:                         # illegal sequence\n                          \x1b[                      # CSI\n                          [ -~]*                # anything legal\n                          ([\0-\x1f:])              # anything illegal\n                        )\n                    "],["\n                        ^                           # beginning of line\n                                                    #\n                                                    # First attempt\n                        (?:                         # legal sequence\n                          \\x1b\\[                      # CSI\n                          ([\\x3c-\\x3f]?)              # private-mode char\n                          ([\\d;]*)                    # any digits or semicolons\n                          ([\\x20-\\x2f]?               # an intermediate modifier\n                          [\\x40-\\x7e])                # the command\n                        )\n                        |                           # alternate (second attempt)\n                        (?:                         # illegal sequence\n                          \\x1b\\[                      # CSI\n                          [\\x20-\\x7e]*                # anything legal\n                          ([\\x00-\\x1f:])              # anything illegal\n                        )\n                    "]))));let t=this._buffer.match(this._csi_regex);if(null===t)return e.kind=p.Incomplete,e;if(t[4])return e.kind=p.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;""!=t[1]||"m"!=t[3]?e.kind=p.Unknown:e.kind=p.SGR,e.text=t[2];var i=t[0].length;return this._buffer=this._buffer.slice(i),e}if("]"==s){if(t<4)return e.kind=p.Incomplete,e;if("8"!=this._buffer.charAt(2)||";"!=this._buffer.charAt(3))return e.kind=p.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;this._osc_st||(this._osc_st=function(e){let t=e.raw[0],n=/^\s+|\s+\n|\s*#[\s\S]*?\n|\n/gm,s=t.replace(n,"");return new RegExp(s,"g")}(S||(S=y(["\n                        (?:                         # legal sequence\n                          (\x1b\\)                    # ESC                           |                           # alternate\n                          (\x07)                      # BEL (what xterm did)\n                        )\n                        |                           # alternate (second attempt)\n                        (                           # illegal sequence\n                          [\0-\x06]                 # anything illegal\n                          |                           # alternate\n                          [\b-\x1a]                 # anything illegal\n                          |                           # alternate\n                          [\x1c-\x1f]                 # anything illegal\n                        )\n                    "],["\n                        (?:                         # legal sequence\n                          (\\x1b\\\\)                    # ESC \\\n                          |                           # alternate\n                          (\\x07)                      # BEL (what xterm did)\n                        )\n                        |                           # alternate (second attempt)\n                        (                           # illegal sequence\n                          [\\x00-\\x06]                 # anything illegal\n                          |                           # alternate\n                          [\\x08-\\x1a]                 # anything illegal\n                          |                           # alternate\n                          [\\x1c-\\x1f]                 # anything illegal\n                        )\n                    "])))),this._osc_st.lastIndex=0;{let t=this._osc_st.exec(this._buffer);if(null===t)return e.kind=p.Incomplete,e;if(t[3])return e.kind=p.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e}{let t=this._osc_st.exec(this._buffer);if(null===t)return e.kind=p.Incomplete,e;if(t[3])return e.kind=p.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e}this._osc_regex||(this._osc_regex=w(v||(v=y(["\n                        ^                           # beginning of line\n                                                    #\n                        \x1b]8;                    # OSC Hyperlink\n                        [ -:<-~]*       # params (excluding ;)\n                        ;                           # end of params\n                        ([!-~]{0,512})        # URL capture\n                        (?:                         # ST\n                          (?:\x1b\\)                  # ESC                           |                           # alternate\n                          (?:\x07)                    # BEL (what xterm did)\n                        )\n                        ([ -~]+)              # TEXT capture\n                        \x1b]8;;                   # OSC Hyperlink End\n                        (?:                         # ST\n                          (?:\x1b\\)                  # ESC                           |                           # alternate\n                          (?:\x07)                    # BEL (what xterm did)\n                        )\n                    "],["\n                        ^                           # beginning of line\n                                                    #\n                        \\x1b\\]8;                    # OSC Hyperlink\n                        [\\x20-\\x3a\\x3c-\\x7e]*       # params (excluding ;)\n                        ;                           # end of params\n                        ([\\x21-\\x7e]{0,512})        # URL capture\n                        (?:                         # ST\n                          (?:\\x1b\\\\)                  # ESC \\\n                          |                           # alternate\n                          (?:\\x07)                    # BEL (what xterm did)\n                        )\n                        ([\\x20-\\x7e]+)              # TEXT capture\n                        \\x1b\\]8;;                   # OSC Hyperlink End\n                        (?:                         # ST\n                          (?:\\x1b\\\\)                  # ESC \\\n                          |                           # alternate\n                          (?:\\x07)                    # BEL (what xterm did)\n                        )\n                    "]))));let n=this._buffer.match(this._osc_regex);if(null===n)return e.kind=p.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;e.kind=p.OSCURL,e.url=n[1],e.text=n[2];i=n[0].length;return this._buffer=this._buffer.slice(i),e}if("("==s)return e.kind=p.Unknown,this._buffer=this._buffer.slice(3),e}}ansi_to_html(e){this.append_buffer(e);for(var t=[];;){var n=this.get_next_packet();if(n.kind==p.EOS||n.kind==p.Incomplete)break;n.kind!=p.ESC&&n.kind!=p.Unknown&&(n.kind==p.Text?t.push(this.transform_to_html(this.with_state(n))):n.kind==p.SGR?this.process_ansi(n):n.kind==p.OSCURL&&t.push(this.process_hyperlink(n)))}return t.join("")}with_state(e){return{bold:this.bold,faint:this.faint,italic:this.italic,underline:this.underline,fg:this.fg,bg:this.bg,text:e.text}}process_ansi(e){let t=e.text.split(";");for(;t.length>0;){let e=t.shift(),n=parseInt(e,10);if(isNaN(n)||0===n)this.fg=null,this.bg=null,this.bold=!1,this.faint=!1,this.italic=!1,this.underline=!1;else if(1===n)this.bold=!0;else if(2===n)this.faint=!0;else if(3===n)this.italic=!0;else if(4===n)this.underline=!0;else if(21===n)this.bold=!1;else if(22===n)this.faint=!1,this.bold=!1;else if(23===n)this.italic=!1;else if(24===n)this.underline=!1;else if(39===n)this.fg=null;else if(49===n)this.bg=null;else if(n>=30&&n<38)this.fg=this.ansi_colors[0][n-30];else if(n>=40&&n<48)this.bg=this.ansi_colors[0][n-40];else if(n>=90&&n<98)this.fg=this.ansi_colors[1][n-90];else if(n>=100&&n<108)this.bg=this.ansi_colors[1][n-100];else if((38===n||48===n)&&t.length>0){let e=38===n,s=t.shift();if("5"===s&&t.length>0){let n=parseInt(t.shift(),10);n>=0&&n<=255&&(e?this.fg=this.palette_256[n]:this.bg=this.palette_256[n])}if("2"===s&&t.length>2){let n=parseInt(t.shift(),10),s=parseInt(t.shift(),10),i=parseInt(t.shift(),10);if(n>=0&&n<=255&&s>=0&&s<=255&&i>=0&&i<=255){let t={rgb:[n,s,i],class_name:"truecolor"};e?this.fg=t:this.bg=t}}}}}transform_to_html(e){let t=e.text;if(0===t.length)return t;if(t=this.escape_txt_for_html(t),!e.bold&&!e.italic&&!e.underline&&null===e.fg&&null===e.bg)return t;let n=[],s=[],i=e.fg,r=e.bg;e.bold&&n.push(this._boldStyle),e.faint&&n.push(this._faintStyle),e.italic&&n.push(this._italicStyle),e.underline&&n.push(this._underlineStyle),this._use_classes?(i&&("truecolor"!==i.class_name?s.push(`${i.class_name}-fg`):n.push(`color:rgb(${i.rgb.join(",")})`)),r&&("truecolor"!==r.class_name?s.push(`${r.class_name}-bg`):n.push(`background-color:rgb(${r.rgb.join(",")})`))):(i&&n.push(`color:rgb(${i.rgb.join(",")})`),r&&n.push(`background-color:rgb(${r.rgb})`));let l="",a="";return s.length&&(l=` class="${s.join(" ")}"`),n.length&&(a=` style="${n.join(";")}"`),`<span${a}${l}>${t}</span>`}process_hyperlink(e){let t=e.url.split(":");return t.length<1?"":this._url_allowlist[t[0]]?`<a href="${this.escape_txt_for_html(e.url)}">${this.escape_txt_for_html(e.text)}</a>`:""}}function w(e){let t=e.raw[0].replace(/^\s+|\s+\n|\s*#[\s\S]*?\n|\n/gm,"");return new RegExp(t)}var E=n(66596),C=n(67089),j=n(78502),T=n.n(j),A=n(46976),I=n.n(A);const L=e=>{let{serviceData:t}=e;const{t:n}=(0,g.Bd)(),{token:o}=E.A.useToken(),{message:c}=C.A.useApp(),[u,h]=(0,_.useState)(""),[d,p]=(0,_.useState)(""),[x,S]=(0,_.useState)("Before validation"),v=(0,i.CX)(),y=(0,i.eZ)();async function w(e){return v.get_logs(e,v._config.accessKey,0).then((e=>(new k).ansi_to_html(e.result.logs)))}const j=(0,r.ET)({mutationFn:e=>{var t,n,i,r;const l=`${null===(t=e.environments.image)||void 0===t?void 0:t.registry}/${null===(n=e.environments.image)||void 0===n?void 0:n.name}:${null===(i=e.environments.image)||void 0===i?void 0:i.tag}`,a={name:e.serviceName,desired_session_count:e.desiredRoutingCount,image:l,runtime_variant:e.runtimeVariant,architecture:null===(r=e.environments.image)||void 0===r?void 0:r.architecture,group:v.current_group,domain:y,cluster_size:e.cluster_size,cluster_mode:e.cluster_mode,open_to_public:e.openToPublic,config:{model:e.vFolderID,model_version:1,...v.supports("endpoint-extra-mounts")&&{extra_mounts:I().reduce(e.mounts,((t,n)=>(t[n]={...e.vfoldersAliasMap[n]&&{mount_destination:e.vfoldersAliasMap[n]},type:"bind"},t)),{})},model_definition_path:e.modelDefinitionPath,model_mount_destination:v.supports("endpoint-extra-mounts")?e.modelMountDestination:"/models",environ:{},scaling_group:e.resourceGroup,resources:{cpu:e.resource.cpu.toString(),mem:e.resource.mem,...e.resource.accelerator>0?{[e.resource.acceleratorType]:e.resource.accelerator}:void 0},resource_opts:{shmem:(0,s.Mh)(e.resource.mem,"4g")>0&&(0,s.Mh)(e.resource.shmem,"1g")<0?"1g":e.resource.shmem}}};return(0,s.hu)({method:"POST",url:"/services/_/try",body:a,client:v})}}),A=(0,_.useRef)(!1);return(0,_.useEffect)((()=>{if(A.current)return;const e=T()().format("LLL");let s;return j.mutateAsync(t).then((t=>{var i,r,l,a;S(e);const o=t;s=v.maintenance.attach_background_task(o.task_id);const u=setTimeout((()=>{var e;null===(e=s)||void 0===e||e.close(),h("error"),c.error(n("modelService.CannotValidateNow"))}),1e4);null===(i=s)||void 0===i||i.addEventListener("bgtask_updated",(async e=>{const t=JSON.parse(e.data),n=JSON.parse(t.message);if(["session_started","session_terminated"].includes(n.event)){const e=await w(n.session_id);var i;if(p(e),clearTimeout(u),"session_terminated"===n.event)return void(null===(i=s)||void 0===i||i.close())}h("processing")})),null===(r=s)||void 0===r||r.addEventListener("bgtask_done",(async e=>{var t;h("finished"),clearTimeout(u),null===(t=s)||void 0===t||t.close()})),null===(l=s)||void 0===l||l.addEventListener("bgtask_failed",(async e=>{var t;const n=JSON.parse(e.data),i=JSON.parse(n.message),r=await w(i.session_id);throw p(r),h("error"),null===(t=s)||void 0===t||t.close(),new Error(e.data)})),null===(a=s)||void 0===a||a.addEventListener("bgtask_cancelled",(async e=>{var t;throw h("error"),null===(t=s)||void 0===t||t.close(),new Error(e.data)}))})).catch((e=>{c.error(null!==e&&void 0!==e&&e.message?I().truncate(null===e||void 0===e?void 0:e.message,{length:200}):n("modelService.FormValidationFailed"))})).finally((()=>{A.current=!1})),A.current=!0,()=>{var e;null===(e=s)||void 0===e||e.close()}}),[]),(0,m.jsxs)(_.Suspense,{fallback:(0,m.jsx)(a.A,{}),children:[(0,m.jsxs)(l.A,{direction:"row",justify:"between",align:"center",children:[(0,m.jsx)("h3",{children:n("modelService.Result")}),(0,m.jsx)(b,{status:u})]}),(0,m.jsxs)(l.A,{direction:"row",justify:"between",align:"center",children:[(0,m.jsx)("h3",{children:n("modelService.TimeStamp")}),(0,m.jsx)(f.A,{children:x})]}),(0,m.jsx)("h3",{children:n("modelService.SeeContainerLogs")}),(0,m.jsx)(l.A,{direction:"column",justify:"start",align:"start",style:{overflowX:"scroll",color:"white",backgroundColor:"black",padding:o.paddingSM,borderRadius:o.borderRadius},children:(0,m.jsx)("pre",{dangerouslySetInnerHTML:{__html:d}})})]})}}}]);
//# sourceMappingURL=7472.99728d45.chunk.js.map