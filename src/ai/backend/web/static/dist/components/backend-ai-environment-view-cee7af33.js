import{_ as e,e as t,c as i,a,B as s,d as o,I as r,b as l,x as n,f as d,i as c,g as u,h as p,t as m,A as h,y as g}from"./backend-ai-webui-efd2500f.js";import"./tab-group-b2aae4b1.js";import"./mwc-tab-bar-553aafc2.js";import"./lablup-activity-panel-b5a6a642.js";import"./lablup-grid-sort-filter-column-84561833.js";import"./lablup-loading-spinner-1e8034f9.js";import"./vaadin-grid-af1e810c.js";import"./vaadin-grid-selection-column-5177358f.js";import"./vaadin-grid-filter-column-2949b887.js";import"./vaadin-grid-sort-column-46341c17.js";import"./select-ea0f7a77.js";import"./textfield-8bcb1235.js";import"./label-06f60db1.js";import"./slider-9a7c3779.js";import"./vaadin-icons-de1a8491.js";import"./vaadin-item-styles-0bc384b2.js";import"./vaadin-item-42ec2f48.js";import"./backend-ai-list-status-9346ef68.js";import"./mwc-switch-f419f24b.js";import"./radio-behavior-98d80f7f.js";import"./progress-spinner-c23af7f1.js";import"./input-behavior-1a3ba72d.js";import"./dom-repeat-e7d7736f.js";let v=class extends s{constructor(){super(),this.selectedIndex=0,this.selectedImages=[],this._cuda_gpu_disabled=!1,this._cuda_fgpu_disabled=!1,this._rocm_gpu_disabled=!1,this._tpu_disabled=!1,this.alias=Object(),this.indicator=Object(),this.deleteAppInfo=Object(),this.deleteAppRow=Object(),this.installImageResource=Object(),this.selectedCheckbox=Object(),this._grid=Object(),this.servicePortsMsg="",this._range={cpu:["1","2","3","4","5","6","7","8"],mem:["64MB","128MB","256MB","512MB","1GB","2GB","4GB","8GB","16GB","32GB","256GB","512GB"],"cuda-gpu":["0","1","2","3","4","5","6","7"],"cuda-fgpu":["0","0.1","0.2","0.5","1.0","2.0"],"rocm-gpu":["0","1","2","3","4","5","6","7"],tpu:["0","1","2"]},this.cpuValue=0,this.listCondition="loading",this._boundRequirementsRenderer=this.requirementsRenderer.bind(this),this._boundControlsRenderer=this.controlsRenderer.bind(this),this._boundInstallRenderer=this.installRenderer.bind(this),this._boundBaseImageRenderer=this.baseImageRenderer.bind(this),this._boundConstraintRenderer=this.constraintRenderer.bind(this),this._boundDigestRenderer=this.digestRenderer.bind(this),this.installImageNameList=[],this.deleteImageNameList=[],this.images=[],this.allowed_registries=[],this.servicePorts=[]}static get styles(){return[o,r,l,n,d,c`
         vaadin-grid {
           border: 0;
           font-size: 14px;
           height: calc(100vh - 225px);
         }
         h4 {
          font-weight: 200;
          font-size: 14px;
          margin: 0px;
          padding: 5px 15px 5px 20px;
        }
         wl-button > wl-icon {
           --icon-size: 24px;
           padding: 0;
         }
         wl-icon {
           --icon-size: 16px;
           padding: 0;
         }
         wl-label {
           --label-font-size: 13px;
           --label-font-family: 'Ubuntu', Roboto;
           -webkit-border-radius: 3px;
           -moz-border-radius: 3px;
           border-radius: 3px;
           -moz-background-clip: padding;
           -webkit-background-clip: padding-box;
           background-clip: padding-box;
           border: 1px solid #ccc;
           background-color: #f9f9f9;
           padding: 0 3px;
           display: inline-block;
           margin: 0;
         }
         wl-label.installed {
           --label-color: #52595d;
         }
         wl-label.installing {
           --label-color: var(--paper-orange-700);
         }
         img.indicator-icon {
           width: 16px;
           height: 16px;
         }
         div.indicator,
         span.indicator {
           font-size: 9px;
           margin-right: 5px;
         }
         span.resource-limit-title {
           font-size: 14px;
           font-family: var(--general-font-family);
           text-align: left;
           width: 70px;
         }
         wl-button {
           --button-bg: var(--paper-orange-50);
           --button-bg-hover: var(--paper-orange-100);
           --button-bg-active: var(--paper-orange-600);
           --button-color: #242424;
           color: var(--paper-orange-900);
         }
         wl-button.operation {
           margin: auto 10px;
           padding: auto 10px;
         }
         backend-ai-dialog {
           --component-min-width: 350px;
         }
         backend-ai-dialog#modify-image-dialog wl-select,
         backend-ai-dialog#modify-image-dialog wl-textfield {
           margin-bottom: 20px;
         }
         wl-select, wl-textfield {
           --input-font-family: var(--general-font-family);
         }
         backend-ai-dialog wl-textfield {
           --input-font-size: 14px;
         }
         #modify-app-dialog {
           --component-max-height: 550px;
         }
         backend-ai-dialog vaadin-grid {
           margin: 0px 20px;
         }
         .gutterBottom {
           margin-bottom: 20px;
         }
         div.container {
           display: flex;
           flex-direction: column;
           padding: 0px 30px;
         }
         div.row {
           display: grid;
           grid-template-columns: 4fr 4fr 4fr 1fr;
           margin-bottom: 10px;
         }
         mwc-button.operation {
           margin: auto 10px;
           padding: auto 10px;
         }
         mwc-button[outlined] {
           width: 100%;
           margin: 10px auto;
           background-image: none;
           --mdc-button-outline-width: 2px;
           --mdc-button-disabled-outline-color: var(--general-sidebar-color);
           --mdc-button-disabled-ink-color: var(--general-sidebar-color);
           --mdc-theme-primary: #38bd73;
           --mdc-theme-on-primary: #38bd73;
         }
         mwc-button, mwc-button[unelevated] {
           background-image: none;
           --mdc-theme-primary: var(--general-button-background-color);
           --mdc-theme-on-primary: var(--general-button-color);
         }
         mwc-button[disabled] {
           background-image: var(--general-sidebar-color);
         }
         mwc-button[disabled].range-value {
           --mdc-button-disabled-ink-color: var(--general-sidebar-color);
         }
         mwc-select {
           --mdc-theme-primary: var(--general-sidebar-color);
           --mdc-menu-item-height: auto;
         }
         mwc-textfield {
           width: 100%;
           --mdc-text-field-fill-color: transparent;
           --mdc-theme-primary: var(--general-textfield-selected-color);
           --mdc-typography-font-family: var(--general-font-family);
         }
         mwc-slider {
           width: 100%;
           margin: auto 10px;
           --mdc-theme-secondary: var(--general-slider-color);
           --mdc-theme-text-primary-on-dark: #ffffff;
         }
       `]}firstUpdated(){var e;this.indicator=globalThis.lablupIndicator,this.notification=globalThis.lablupNotification,this.resourceBroker=globalThis.resourceBroker,void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._getImages()}),!0):this._getImages(),this._grid=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#testgrid"),this._grid.addEventListener("sorter-changed",(e=>{this._refreshSorter(e)})),document.addEventListener("image-rescanned",(()=>{this._getImages()})),this.installImageDialog.addEventListener("didHide",(()=>{this._uncheckSelectedRow()})),this.deleteImageDialog.addEventListener("didHide",(()=>{this._uncheckSelectedRow()}))}_removeRow(){this.deleteAppRow.remove(),this.deleteAppInfoDialog.hide(),this.notification.text=u("environment.AppInfoDeleted"),this.notification.show()}_addRow(){const e=this.modifyAppContainer.children[this.modifyAppContainer.children.length-1],t=this._createRow();this.modifyAppContainer.insertBefore(t,e)}_createRow(){const e=document.createElement("div");e.setAttribute("class","row extra");const t=document.createElement("wl-textfield");t.setAttribute("type","text");const i=document.createElement("wl-textfield");t.setAttribute("type","text");const a=document.createElement("wl-textfield");t.setAttribute("type","number");const s=document.createElement("wl-button");s.setAttribute("class","fg pink"),s.setAttribute("fab",""),s.setAttribute("flat",""),s.addEventListener("click",(e=>this._checkDeleteAppInfo(e)));const o=document.createElement("wl-icon");return o.innerHTML="remove",s.appendChild(o),e.appendChild(a),e.appendChild(i),e.appendChild(t),e.appendChild(s),e}_checkDeleteAppInfo(e){var t;this.deleteAppRow=e.target.parentNode;const i=[...this.deleteAppRow.children].filter((e=>"WL-TEXTFIELD"===e.tagName)).map((e=>e.value));(null===(t=i.filter((e=>""===e)))||void 0===t?void 0:t.length)===i.length?this._removeRow():(this.deleteAppInfo=i,this.deleteAppInfoDialog.show())}_clearRows(){const e=this.modifyAppContainer.querySelectorAll(".row");e[e.length-1].querySelectorAll("wl-textfield").forEach((e=>{e.value=""})),this.modifyAppContainer.querySelectorAll(".row.extra").forEach((e=>{e.remove()}))}_uncheckSelectedRow(){this._grid.selectedItems=[]}_refreshSorter(e){const t=e.target,i=t.path.toString();t.direction&&("asc"===t.direction?this._grid.items.sort(((e,t)=>e[i]<t[i]?-1:e[i]>t[i]?1:0)):this._grid.items.sort(((e,t)=>e[i]>t[i]?-1:e[i]<t[i]?1:0)))}async _viewStateChanged(e){await this.updateComplete}_getImages(){var e;this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.domain.get(globalThis.backendaiclient._config.domainName,["allowed_docker_registries"]).then((e=>(this.allowed_registries=e.domain.allowed_docker_registries,globalThis.backendaiclient.image.list(["name","tag","registry","architecture","digest","installed","labels { key value }","resource_limits { key min max }"],!1,!0)))).then((e=>{var t;const i=e.images,a=[];i.forEach((e=>{if("registry"in e&&this.allowed_registries.includes(e.registry)){const t=e.tag.split("-");void 0!==t[1]?(e.baseversion=t[0],e.baseimage=t[1],void 0!==t[2]&&(e.additional_req=this._humanizeName(t.slice(2).join("-")))):void 0!==e.tag?e.baseversion=e.tag:e.baseversion="";const i=e.name.split("/");void 0!==i[1]?(e.namespace=i[0],e.lang=i.slice(1).join("")):(e.namespace="",e.lang=i[0]);const s=e.lang.split("-");let o;o=void 0!==e.baseimage?[this._humanizeName(e.baseimage)]:[],void 0!==s[1]&&("r"===s[0]?(e.lang=s[0],o.push(this._humanizeName(s[0]))):(e.lang=s[1],o.push(this._humanizeName(s[0])))),e.baseimage=o,e.lang=this._humanizeName(e.lang);e.resource_limits.forEach((t=>{0==t.max&&(t.max="∞"),"cuda.device"==t.key&&(t.key="cuda_device"),"cuda.shares"==t.key&&(t.key="cuda_shares"),"rocm.device"==t.key&&(t.key="rocm_device"),"tpu.device"==t.key&&(t.key="tpu_device"),null!==t.min&&void 0!==t.min&&(e[t.key+"_limit_min"]=this._addUnit(t.min)),null!==t.max&&void 0!==t.max&&(e[t.key+"_limit_max"]=this._addUnit(t.max))})),e.labels=e.labels.reduce(((e,t)=>({...e,[t.key]:t.value})),{}),a.push(e)}})),this.images=a,0==this.images.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide()})).catch((e=>{var t;console.log(e),void 0!==e.message?(this.notification.text=p.relieve(e.title),this.notification.detail=e.message):this.notification.text=p.relieve("Problem occurred during image metadata loading."),this.notification.show(!0,e),null===(t=this._listStatus)||void 0===t||t.hide()}))}_addUnit(e){const t=e.substr(-1);return"m"==t?e.slice(0,-1)+"MB":"g"==t?e.slice(0,-1)+"GB":"t"==t?e.slice(0,-1)+"TB":e}_symbolicUnit(e){const t=e.substr(-2);return"MB"==t?e.slice(0,-2)+"m":"GB"==t?e.slice(0,-2)+"g":"TB"==t?e.slice(0,-2)+"t":e}_humanizeName(e){this.alias=this.resourceBroker.imageTagAlias;const t=this.resourceBroker.imageTagReplace;for(const[i,a]of Object.entries(t)){const t=new RegExp(i);if(t.test(e))return e.replace(t,a)}return e in this.alias?this.alias[e]:e}_changeSliderValue(e){var t,i;const a=this._range[e.id].filter(((t,i)=>i===e.value));(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#modify-image-"+e.id)).label=a[0],(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#modify-image-"+e.id)).value=a[0]}_markIfUnlimited(e){return["-",0,"Unlimited",1/0,"Infinity"].includes(e)?"∞":e}_hideDialogById(e){var t;return(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(e)).hide()}_launchDialogById(e){var t;return(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(e)).show()}modifyImage(){const e=this.modifyImageCpu.label,t=this.modifyImageMemory.label,i=this.modifyImageCudaGpu.label,a=this.modifyImageCudaFGpu.label,s=this.modifyImageRocmGpu.label,o=this.modifyImageTpu.label,{resource_limits:r}=this.images[this.selectedIndex],l={},n=this._cuda_gpu_disabled?this._cuda_fgpu_disabled?1:2:this._cuda_fgpu_disabled?2:3;e!==r[0].min&&(l.cpu={min:e});const d=this._symbolicUnit(t);d!==r[n].min&&(l.mem={min:d}),this._cuda_gpu_disabled||i===r[1].min||(l["cuda.device"]={min:i}),this._cuda_fgpu_disabled||a===r[2].min||(l["cuda.shares"]={min:a}),this._rocm_gpu_disabled||s===r[3].min||(l["rocm.device"]={min:s}),this._tpu_disabled||o===r[4].min||(l["tpu.device"]={min:o});const c=this.images[this.selectedIndex];if(0===Object.keys(l).length)return this.notification.text=u("environment.NoChangeMade"),this.notification.show(),void this._hideDialogById("#modify-image-dialog");globalThis.backendaiclient.image.modifyResource(c.registry,c.name,c.tag,l).then((e=>{e.reduce(((e,t)=>e&&"ok"===t.result),!0)?(this._getImages(),this.requestUpdate(),this.notification.text=u("environment.SuccessfullyModified")):this.notification.text=u("environment.ProblemOccurred"),this.notification.show(),this._hideDialogById("#modify-image-dialog")}))}openInstallImageDialog(){this.selectedImages=this._grid.selectedItems.filter((e=>!e.installed)),this.installImageNameList=this.selectedImages.map((e=>(Object.keys(e).map((t=>{["registry","name","tag"].includes(t)&&t in e&&(e[t]=e[t].replace(/\s/g,""))})),e.registry+"/"+e.name+":"+e.tag))),this.selectedImages.length>0?this.installImageDialog.show():(this.notification.text=u("environment.SelectedImagesAlreadyInstalled"),this.notification.show())}_installImage(){this.installImageDialog.hide(),this.selectedImages.forEach((async e=>{const t='[id="'+e.registry.replace(/\./gi,"-")+"-"+e.name.replace("/","-")+"-"+e.tag.replace(/\./gi,"-")+'"]';this._grid.querySelector(t).setAttribute("style","display:block;");const i=e.registry+"/"+e.name+":"+e.tag;let a=!1;const s=Object();"resource_limits"in e&&e.resource_limits.forEach((e=>{s[e.key.replace("_",".")]=e.min})),"cuda.device"in s&&"cuda.shares"in s?(a=!0,s.gpu=0,s.fgpu=s["cuda.shares"]):"cuda.device"in s?(s.gpu=s["cuda.device"],a=!0):a=!1,s.mem.endsWith("g")?s.mem=s.mem.replace("g",".5g"):s.mem.endsWith("m")&&(s.mem=Number(s.mem.slice(0,-1))+256+"m"),s.domain=globalThis.backendaiclient._config.domainName,s.group_name=globalThis.backendaiclient.current_group;const o=await globalThis.backendaiclient.get_resource_slots();a&&("cuda.device"in o||"cuda.shares"in o||(delete s.gpu,delete s.fgpu,delete s["cuda.shares"],delete s["cuda.device"])),"cuda.device"in o&&"cuda.shares"in o?"fgpu"in s&&"gpu"in s&&(delete s.gpu,delete s["cuda.device"]):"cuda.device"in o?(delete s.fgpu,delete s["cuda.shares"]):"cuda.shares"in o&&(delete s.gpu,delete s["cuda.device"]),this.notification.text=u("environment.InstallingImage")+i+u("environment.TakesTime"),this.notification.show();const r=await this.indicator.start("indeterminate");r.set(10,u("import.Downloading")),globalThis.backendaiclient.image.install(i,e.architecture,s).then((e=>{r.set(100,u("import.Installed")),r.end(1e3),this._grid.querySelector(t).className="installed",this._grid.querySelector(t).innerHTML=u("environment.Installed")})).catch((e=>{this._grid.querySelector(t).className=u("environment.Installing"),this._grid.querySelector(t).setAttribute("style","display:none;"),this._uncheckSelectedRow(),this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e),r.set(100,m("environment.DescProblemOccurred")),r.end(1e3)}))}))}openDeleteImageDialog(){this.selectedImages=this._grid.selectedItems.filter((e=>e.installed)),this.deleteImageNameList=this.selectedImages.map((e=>e.registry+"/"+e.name+":"+e.tag)),this.selectedImages.length>0?this.deleteImageDialog.show():(this.notification.text=u("environment.SelectedImagesNotInstalled"),this.notification.show())}_deleteImage(){}_setPulldownDefaults(e){var t,i,a,s,o,r,l,n,d,c;this._cuda_gpu_disabled=0===e.filter((e=>"cuda_device"===e.key)).length,this._cuda_fgpu_disabled=0===e.filter((e=>"cuda_shares"===e.key)).length,this._rocm_gpu_disabled=0===e.filter((e=>"rocm_device"===e.key)).length,this._tpu_disabled=0===e.filter((e=>"tpu_device"===e.key)).length,this.modifyImageCpu.label=e[0].min,this._cuda_gpu_disabled?(this.modifyImageCudaGpu.label=m("environment.Disabled"),(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("mwc-slider#cuda-gpu")).value=0):(this.modifyImageCudaGpu.label=e[1].min,(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("mwc-slider#cuda-gpu")).value=this._range["cuda-gpu"].indexOf(this._range.cpu.filter((t=>t===e[0].min))[0])),this._cuda_fgpu_disabled?(this.modifyImageCudaFGpu.label=m("environment.Disabled"),(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("mwc-slider#cuda-gpu")).value=0):(this.modifyImageCudaFGpu.label=e[2].min,(null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("mwc-slider#cuda-fgpu")).value=this._range["cuda-fgpu"].indexOf(this._range.cpu.filter((t=>t===e[0].min))[0])),this._rocm_gpu_disabled?(this.modifyImageRocmGpu.label=m("environment.Disabled"),(null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("mwc-slider#rocm-gpu")).value=0):(this.modifyImageRocmGpu.label=e[3].min,(null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("mwc-slider#rocm-gpu")).value=this._range["rocm-gpu"].indexOf(this._range.cpu.filter((t=>t===e[0].min))[0])),this._tpu_disabled?(this.modifyImageTpu.label=m("environment.Disabled"),(null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("mwc-slider#tpu")).value=0):(this.modifyImageTpu.label=e[4].min,(null===(l=this.shadowRoot)||void 0===l?void 0:l.querySelector("mwc-slider#tpu")).value=this._range.tpu.indexOf(this._range.cpu.filter((t=>t===e[0].min))[0]));const u=this._cuda_gpu_disabled?this._cuda_fgpu_disabled?1:2:this._cuda_fgpu_disabled?2:3;this.modifyImageMemory.label=this._addUnit(e[u].min),(null===(d=this.shadowRoot)||void 0===d?void 0:d.querySelector("mwc-slider#cpu")).value=this._range.cpu.indexOf(this._range.cpu.filter((t=>t===e[0].min))[0]),(null===(c=this.shadowRoot)||void 0===c?void 0:c.querySelector("mwc-slider#mem")).value=this._range.mem.indexOf(this._range.mem.filter((t=>t===this._addUnit(e[u].min)))[0]),this._updateSliderLayout()}_updateSliderLayout(){var e;null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("mwc-slider").forEach((e=>{e.layout()}))}_decodeServicePort(){""===this.images[this.selectedIndex].labels["ai.backend.service-ports"]?this.servicePorts=[]:this.servicePorts=this.images[this.selectedIndex].labels["ai.backend.service-ports"].split(",").map((e=>{const t=e.split(":");return{app:t[0],protocol:t[1],port:t[2]}}))}_isServicePortValid(){var e;const t=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#modify-app-container")).querySelectorAll(".row:not(.header)"),i=new Set;for(const e of Array.from(t)){const t=e.querySelectorAll("wl-textfield");if(Array.prototype.every.call(t,(e=>""===e.value)))continue;const a=t[0].value,s=t[1].value,o=parseInt(t[2].value);if(""===a)return this.servicePortsMsg=u("environment.AppNameMustNotBeEmpty"),!1;if(!["http","tcp","pty","preopen"].includes(s))return this.servicePortsMsg=u("environment.ProtocolMustBeOneOfSupported"),!1;if(i.has(o))return this.servicePortsMsg=u("environment.PortMustBeUnique"),!1;if(o>=66535||o<0)return this.servicePortsMsg=u("environment.PortMustBeInRange"),!1;if([2e3,2001,2002,2003,2200,7681].includes(o))return this.servicePortsMsg=u("environment.PortReservedForInternalUse"),!1;i.add(o)}return!0}_parseServicePort(){var e;const t=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#modify-app-container")).querySelectorAll(".row:not(.header)");return Array.prototype.filter.call(t,(e=>(e=>0===Array.prototype.filter.call(e.querySelectorAll("wl-textfield"),((e,t)=>""===e.value)).length)(e))).map((e=>(e=>Array.prototype.map.call(e.querySelectorAll("wl-textfield"),(e=>e.value)).join(":"))(e))).join(",")}modifyServicePort(){if(this._isServicePortValid()){const e=this._parseServicePort(),t=this.images[this.selectedIndex];this.servicePortsMsg="",globalThis.backendaiclient.image.modifyLabel(t.registry,t.name,t.tag,"ai.backend.service-ports",e).then((({result:e})=>{this.notification.text=u("ok"===e?"environment.DescServicePortModified":"dialog.ErrorOccurred"),this._getImages(),this.requestUpdate(),this._clearRows(),this.notification.show(),this._hideDialogById("#modify-app-dialog")}))}}requirementsRenderer(e,t,i){h(g`
             <div class="layout horizontal center flex">
               <div class="layout horizontal configuration">
                 <wl-icon class="fg green">developer_board</wl-icon>
                 <span>${i.item.cpu_limit_min}</span> ~
                 <span>${this._markIfUnlimited(i.item.cpu_limit_max)}</span>
                 <span class="indicator">${m("general.cores")}</span>
               </div>
             </div>
             <div class="layout horizontal center flex">
               <div class="layout horizontal configuration">
                 <wl-icon class="fg green">memory</wl-icon>
                 <span>${i.item.mem_limit_min}</span> ~
                 <span>${this._markIfUnlimited(i.item.mem_limit_max)}</span>
               </div>
             </div>
           ${i.item.cuda_device_limit_min?g`
              <div class="layout horizontal center flex">
                 <div class="layout horizontal configuration">
                   <img class="indicator-icon fg green" src="/resources/icons/file_type_cuda.svg" />
                   <span>${i.item.cuda_device_limit_min}</span> ~
                   <span>${this._markIfUnlimited(i.item.cuda_device_limit_max)}</span>
                   <span class="indicator">CUDA GPU</span>
                 </div>
               </div>
               `:g``}
           ${i.item.cuda_shares_limit_min?g`
               <div class="layout horizontal center flex">
                 <div class="layout horizontal configuration">
                   <wl-icon class="fg green">apps</wl-icon>
                   <span>${i.item.cuda_shares_limit_min}</span> ~
                   <span>${this._markIfUnlimited(i.item.cuda_shares_limit_max)}</span>
                   <span class="indicator">CUDA fGPU</span>
                 </div>
               </div>
               `:g``}
           ${i.item.rocm_device_limit_min?g`
              <div class="layout horizontal center flex">
                 <div class="layout horizontal configuration">
                   <img class="indicator-icon fg green" src="/resources/icons/ROCm.png" />
                   <span>${i.item.rocm_device_limit_min}</span> ~
                   <span>${this._markIfUnlimited(i.item.rocm_device_limit_max)}</span>
                   <span class="indicator">ROCm GPU</span>
                 </div>
               </div>
               `:g``}
           ${i.item.tpu_device_limit_min?g`
              <div class="layout horizontal center flex">
                 <div class="layout horizontal configuration">
                   <img class="indicator-icon fg green" src="/resources/icons/tpu.svg" />
                   <span>${i.item.tpu_device_limit_min}</span> ~
                   <span>${this._markIfUnlimited(i.item.tpu_device_limit_max)}</span>
                   <span class="indicator">TPU</span>
                 </div>
               </div>
               `:g``}
         `,e)}controlsRenderer(e,t,i){h(g`
         <div id="controls" class="layout horizontal flex center">
           <wl-button fab flat inverted
             class="fg blue controls-running"
             @click=${()=>{this.selectedIndex=i.index,this._setPulldownDefaults(this.images[this.selectedIndex].resource_limits),this._launchDialogById("#modify-image-dialog"),this.requestUpdate()}}>
             <wl-icon>settings</wl-icon>
           </wl-button>
           <wl-button fab flat inverted
             class="fg pink controls-running"
             @click=${()=>{this.selectedIndex!==i.index&&this._clearRows(),this.selectedIndex=i.index,this._decodeServicePort(),this._launchDialogById("#modify-app-dialog"),this.requestUpdate()}}>
             <wl-icon>apps</wl-icon>
           </wl-button>
         </div>
       `,e)}installRenderer(e,t,i){h(g`
         <div class="layout horizontal center center-justified">
           ${i.item.installed?g`
           <wl-label class="installed"
               id="${i.item.registry.replace(/\./gi,"-")+"-"+i.item.name.replace("/","-")+"-"+i.item.tag.replace(/\./gi,"-")}">
             ${m("environment.Installed")}
           </wl-label>
           `:g`
           <wl-label class="installing"
             id="${i.item.registry.replace(/\./gi,"-")+"-"+i.item.name.replace("/","-")+"-"+i.item.tag.replace(/\./gi,"-")}"
             style="display:none">
             ${m("environment.Installing")}
             </wl-label>
           `}
         </div>
       `,e)}baseImageRenderer(e,t,i){h(g`
         ${i.item.baseimage.map((e=>g`
             <lablup-shields app="" color="blue" ui="round" description="${e}"></lablup-shields>
         `))}
         `,e)}constraintRenderer(e,t,i){h(g`
         ${i.item.additional_req?g`
           <lablup-shields app="" color="green" ui="round" description="${i.item.additional_req}"></lablup-shields>
         `:g``}
       `,e)}digestRenderer(e,t,i){h(g`
       <div class="layout vertical">
         <span class="indicator monospace">${i.item.digest}</span>
       </div>
       `,e)}render(){return g`
      <h4 class="horizontal flex center center-justified layout">
        <span>${m("environment.Images")}</span>
        <span class="flex"></span>
        <mwc-button raised label="${m("environment.Install")}" class="operation" id="install-image" icon="get_app" @click="${this.openInstallImageDialog}"></mwc-button>
        <mwc-button disabled label="${m("environment.Delete")}" class="operation temporarily-hide" id="delete-image" icon="delete" @click="${this.openDeleteImageDialog}"></mwc-button>
      </h4>
      <div class="list-wrapper">
        <vaadin-grid theme="row-stripes column-borders compact" aria-label="Environments" id="testgrid" .items="${this.images}">
          <vaadin-grid-selection-column flex-grow="0" text-align="center" auto-select>
          </vaadin-grid-selection-column>
          <vaadin-grid-sort-column path="installed" flex-grow="0" header="${m("environment.Status")}" .renderer="${this._boundInstallRenderer}">
          </vaadin-grid-sort-column>
          <lablup-grid-sort-filter-column path="registry" width="80px" resizable
              header="${m("environment.Registry")}"></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column path="architecture" width="80px" resizable
              header="${m("environment.Architecture")}"></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column path="namespace" width="60px" resizable
              header="${m("environment.Namespace")}"></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column path="lang" resizable
              header="${m("environment.Language")}"></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column path="baseversion" resizable
              header="${m("environment.Version")}"></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column path="baseimage" resizable width="110px" header="${m("environment.Base")}" .renderer="${this._boundBaseImageRenderer}">
          </lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column path="additional_req" width="50px" resizable header="${m("environment.Constraint")}" .renderer="${this._boundConstraintRenderer}">
          </lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column path="digest" resizable header="${m("environment.Digest")}" .renderer="${this._boundDigestRenderer}">
          </lablup-grid-sort-filter-column>
          <vaadin-grid-column width="150px" flex-grow="0" resizable header="${m("environment.ResourceLimit")}" .renderer="${this._boundRequirementsRenderer}">
          </vaadin-grid-column>
          <vaadin-grid-column resizable header="${m("general.Control")}" .renderer=${this._boundControlsRenderer}>
          </vaadin-grid-column>
        </vaadin-grid>
        <backend-ai-list-status id="list-status" statusCondition="${this.listCondition}" message="${u("environment.NoImageToDisplay")}"></backend-ai-list-status>
      </div>
       <backend-ai-dialog id="modify-image-dialog" fixed backdrop blockscrolling>
         <span slot="title">${m("environment.ModifyImageResourceLimit")}</span>
         <div slot="content">
           <div class="vertical layout flex">
             <div class="horizontal layout flex center">
               <span class="resource-limit-title">CPU</span>
               <mwc-slider
                   id="cpu"
                   step="1"
                   markers
                   max="7"
                   @change="${e=>this._changeSliderValue(e.target)}"></mwc-slider>
               <mwc-button class="range-value" id="modify-image-cpu" disabled></mwc-button>
             </div>
             <div class="horizontal layout flex center">
               <span class="resource-limit-title">MEM</span>
               <mwc-slider
                   id="mem"
                   markers
                   step="1"
                   max="11"
                   @change="${e=>this._changeSliderValue(e.target)}"></mwc-slider>
               <mwc-button class="range-value" id="modify-image-mem" disabled></mwc-button>
             </div>
             <div class="horizontal layout flex center">
               <span class="resource-limit-title">cuda GPU</span>
               <mwc-slider
                   ?disabled="${this._cuda_gpu_disabled}"
                   id="cuda-gpu"
                   markers
                   step="1"
                   max="7"
                   @change="${e=>this._changeSliderValue(e.target)}"></mwc-slider>
               <mwc-button class="range-value" id="modify-image-cuda-gpu" disabled></mwc-button>
             </div>
             <div class="horizontal layout flex center">
               <span class="resource-limit-title">cuda FGPU</span>
               <mwc-slider
                   ?disabled="${this._cuda_fgpu_disabled}"
                   id="cuda-fgpu"
                   markers
                   step="1"
                   max="5"
                   @change="${e=>this._changeSliderValue(e.target)}"></mwc-slider>
               <mwc-button class="range-value" id="modify-image-cuda-fgpu" disabled></mwc-button>
             </div>
             <div class="horizontal layout flex center">
               <span class="resource-limit-title">rocm GPU</span>
               <mwc-slider
                   ?disabled="${this._rocm_gpu_disabled}"
                   id="rocm-gpu"
                   markers
                   step="1"
                   max="2"
                   @change="${e=>this._changeSliderValue(e.target)}"></mwc-slider>
               <mwc-button class="range-value" id="modify-image-rocm-gpu" disabled></mwc-button>
             </div>
             <div class="horizontal layout flex center">
               <span class="resource-limit-title">TPU</span>
               <mwc-slider
                   ?disabled="${this._tpu_disabled}"
                   id="tpu"
                   markers
                   step="1"
                   max="11"
                   @change="${e=>this._changeSliderValue(e.target)}"></mwc-slider>
               <mwc-button class="range-value" id="modify-image-tpu" disabled></mwc-button>
             </div>
           </div>
         </div>
         <div slot="footer" class="horizontal center-justified flex layout">
           <mwc-button
               unelevated
               fullwidth
               icon="check"
               label="${m("button.SaveChanges")}"
               @click="${()=>this.modifyImage()}"></mwc-button>
         </div>
       </backend-ai-dialog>
       <backend-ai-dialog id="modify-app-dialog" fixed backdrop>
         <span slot="title">${m("environment.ManageApps")}</span>
         <div slot="content" id="modify-app-container">
           <div class="row header">
             <div> ${m("environment.AppName")} </div>
             <div> ${m("environment.Protocol")} </div>
             <div> ${m("environment.Port")} </div>
             <div> ${m("environment.Action")} </div>
           </div>
           ${this.servicePorts.map(((e,t)=>g`
           <div class="row">
             <wl-textfield
               type="text"
               value=${e.app}
             ></wl-textfield>
             <wl-textfield
               type="text"
               value=${e.protocol}
             ></wl-textfield>
             <wl-textfield
               type="number"
               value=${e.port}
             ></wl-textfield>
             <wl-button
               fab flat
               class="fg pink"
               @click=${e=>this._checkDeleteAppInfo(e)}
             >
               <wl-icon>remove</wl-icon>
             </wl-button>
           </div>
           `))}
           <div class="row">
             <wl-textfield type="text"></wl-textfield>
             <wl-textfield type="text"></wl-textfield>
             <wl-textfield type="number"></wl-textfield>
             <wl-button
               fab flat
               class="fg pink"
               @click=${this._addRow}
             >
               <wl-icon>add</wl-icon>
             </wl-button>
           </div>
           <span style="color:red;">${this.servicePortsMsg}</span>
         </div>
         <div slot="footer" class="horizontal end-justified flex layout">
           <mwc-button
               unelevated
               slot="footer"
               icon="check"
               label="${m("button.Finish")}"
               @click="${this.modifyServicePort}"></mwc-button>
         </div>
       </backend-ai-dialog>
       <backend-ai-dialog id="install-image-dialog" fixed backdrop persistent>
         <span slot="title">${m("dialog.title.LetsDouble-Check")}</span>
         <div slot="content">
           <p>${m("environment.DescDownloadImage")}</p>
           <p style="margin:auto; "><span style="color:blue;">
           ${this.installImageNameList.map((e=>g`${e}<br />`))}
           </span></p>
           <p>${m("environment.DescSignificantDownloadTime")} ${m("dialog.ask.DoYouWantToProceed")}</p>
         </div>
         <div slot="footer" class="horizontal flex layout">
           <div class="flex"></div>
           <mwc-button
               class="operation"
               label="${m("button.Cancel")}"
               @click="${e=>{this._hideDialog(e),this._uncheckSelectedRow()}}"></mwc-button>
           <mwc-button
               unelevated
               class="operation"
               label="${m("button.Okay")}"
               @click="${()=>this._installImage()}"></mwc-button>
         </div>
       </backend-ai-dialog>
       <backend-ai-dialog id="delete-image-dialog" fixed backdrop persistent>
         <span slot="title">${m("dialog.title.LetsDouble-Check")}</span>
         <div slot="content">
           <p>${m("environment.DescDeleteImage")}</p>
           <p style="margin:auto; "><span style="color:blue;">
           ${this.deleteImageNameList.map((e=>g`${e}<br />`))}
           </span></p>
           <p>${m("dialog.ask.DoYouWantToProceed")}</p>
         </div>
         <div slot="footer" class="horizontal flex layout">
           <div class="flex"></div>
           <mwc-button
               class="operation"
               label="${m("button.Cancel")}"
               @click="${e=>{this._hideDialog(e),this._uncheckSelectedRow()}}"></mwc-button>
           <mwc-button
               unelevated
               class="operation"
               label="${m("button.Okay")}"
               @click="${()=>this._deleteImage()}"></mwc-button>
         </div>
       </backend-ai-dialog>
       <backend-ai-dialog id="delete-app-info-dialog" fixed backdrop persistent>
         <span slot="title">${m("dialog.title.LetsDouble-Check")}</span>
         <div slot="content">
           <p>${m("environment.DescDeleteAppInfo")}</p>
           <div class="horizontal layout">
               <p>${m("environment.AppName")}</p>
               <p style="color:blue;">: ${this.deleteAppInfo[0]}</p>
             </div>
             <div class="horizontal layout">
               <p>${m("environment.Protocol")}</p>
               <p style="color:blue;">: ${this.deleteAppInfo[1]}</p>
             </div>
             <div class="horizontal layout">
               <p>${m("environment.Port")}</p>
               <p style="color:blue;">: ${this.deleteAppInfo[2]}</p>
             </div>
           <p>${m("dialog.ask.DoYouWantToProceed")}</p>
         </div>
         <div slot="footer" class="horizontal flex layout">
           <div class="flex"></div>
           <mwc-button
               class="operation"
               label="${m("button.Cancel")}"
               @click="${e=>this._hideDialog(e)}"></mwc-button>
           <mwc-button
               unelevated
               class="operation"
               label="${m("button.Okay")}"
               @click="${()=>this._removeRow()}"></mwc-button>
         </div>
       </backend-ai-dialog>
     `}};e([t({type:Array})],v.prototype,"images",void 0),e([t({type:Object})],v.prototype,"resourceBroker",void 0),e([t({type:Array})],v.prototype,"allowed_registries",void 0),e([t({type:Array})],v.prototype,"servicePorts",void 0),e([t({type:Number})],v.prototype,"selectedIndex",void 0),e([t({type:Array})],v.prototype,"selectedImages",void 0),e([t({type:Boolean})],v.prototype,"_cuda_gpu_disabled",void 0),e([t({type:Boolean})],v.prototype,"_cuda_fgpu_disabled",void 0),e([t({type:Boolean})],v.prototype,"_rocm_gpu_disabled",void 0),e([t({type:Boolean})],v.prototype,"_tpu_disabled",void 0),e([t({type:Object})],v.prototype,"alias",void 0),e([t({type:Object})],v.prototype,"indicator",void 0),e([t({type:Array})],v.prototype,"installImageNameList",void 0),e([t({type:Array})],v.prototype,"deleteImageNameList",void 0),e([t({type:Object})],v.prototype,"deleteAppInfo",void 0),e([t({type:Object})],v.prototype,"deleteAppRow",void 0),e([t({type:Object})],v.prototype,"installImageResource",void 0),e([t({type:Object})],v.prototype,"selectedCheckbox",void 0),e([t({type:Object})],v.prototype,"_grid",void 0),e([t({type:String})],v.prototype,"servicePortsMsg",void 0),e([t({type:Object})],v.prototype,"_range",void 0),e([t({type:Number})],v.prototype,"cpuValue",void 0),e([t({type:String})],v.prototype,"listCondition",void 0),e([t({type:Object})],v.prototype,"_boundRequirementsRenderer",void 0),e([t({type:Object})],v.prototype,"_boundControlsRenderer",void 0),e([t({type:Object})],v.prototype,"_boundInstallRenderer",void 0),e([t({type:Object})],v.prototype,"_boundBaseImageRenderer",void 0),e([t({type:Object})],v.prototype,"_boundConstraintRenderer",void 0),e([t({type:Object})],v.prototype,"_boundDigestRenderer",void 0),e([i("#loading-spinner")],v.prototype,"spinner",void 0),e([i("#modify-image-cpu")],v.prototype,"modifyImageCpu",void 0),e([i("#modify-image-mem")],v.prototype,"modifyImageMemory",void 0),e([i("#modify-image-cuda-gpu")],v.prototype,"modifyImageCudaGpu",void 0),e([i("#modify-image-cuda-fgpu")],v.prototype,"modifyImageCudaFGpu",void 0),e([i("#modify-image-rocm-gpu")],v.prototype,"modifyImageRocmGpu",void 0),e([i("#modify-image-tpu")],v.prototype,"modifyImageTpu",void 0),e([i("#delete-app-info-dialog")],v.prototype,"deleteAppInfoDialog",void 0),e([i("#delete-image-dialog")],v.prototype,"deleteImageDialog",void 0),e([i("#install-image-dialog")],v.prototype,"installImageDialog",void 0),e([i("#modify-app-container")],v.prototype,"modifyAppContainer",void 0),e([i("#list-status")],v.prototype,"_listStatus",void 0),v=e([a("backend-ai-environment-list")],v);
/**
 @license
 Copyright (c) 2015-2022 Lablup Inc. All rights reserved.
 */
let b=class extends s{constructor(){super(),this.resourcePolicy={},this.is_admin=!1,this.active=!1,this.gpu_allocatable=!1,this.gpuAllocationMode="device",this.condition="",this.presetName="",this.listCondition="loading",this._boundResourceRenderer=this.resourceRenderer.bind(this),this._boundControlRenderer=this.controlRenderer.bind(this)}static get styles(){return[o,r,l,c`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 225px);
        }

        wl-button > wl-icon {
          --icon-size: 24px;
          padding: 0;
        }

        wl-icon {
          --icon-size: 16px;
          padding: 0;
        }

        vaadin-item {
          font-size: 13px;
          font-weight: 100;
        }

        div.indicator,
        span.indicator {
          font-size: 9px;
          margin-right: 5px;
        }

        div.configuration {
          width: 70px !important;
        }

        div.configuration wl-icon {
          padding-right: 5px;
        }

        mwc-textfield {
          width: 100%;
          --mdc-theme-primary: #242424;
          --mdc-text-field-fill-color: transparent;
        }

        mwc-textfield.yellow {
          --mdc-theme-primary: var(--paper-yellow-600) !important;
        }

        mwc-button, mwc-button[unelevated] {
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
          --mdc-typography-font-family: var(--general-font-family);
        }

        h4 {
          font-weight: 200;
          font-size: 14px;
          margin: 0px;
          padding: 5px 15px 5px 20px;
        }

        backend-ai-dialog h4 {
          font-size: 14px;
          padding: 5px 15px 5px 12px;
          margin: 0 0 10px 0;
          display: block;
          height: 20px;
          border-bottom: 1px solid #DDD;
        }

      `]}resourceRenderer(e,t,i){h(g`
        <div class="layout horizontal wrap center">
          <div class="layout horizontal configuration">
            <wl-icon class="fg green">developer_board</wl-icon>
            <span>${this._markIfUnlimited(i.item.resource_slots.cpu)}</span>
            <span class="indicator">${m("general.cores")}</span>
          </div>
          <div class="layout horizontal configuration">
            <wl-icon class="fg green">memory</wl-icon>
            <span>${this._markIfUnlimited(i.item.resource_slots.mem_gb)}</span>
            <span class="indicator">GB</span>
          </div>
        </div>
        <div class="layout horizontal wrap center">
        ${i.item.resource_slots["cuda.device"]?g`
          <div class="layout horizontal configuration">
            <wl-icon class="fg green">view_module</wl-icon>
            <span>${this._markIfUnlimited(i.item.resource_slots["cuda.device"])}</span>
            <span class="indicator">GPU</span>
          </div>
        `:g``}
        ${i.item.resource_slots["cuda.shares"]?g`
          <div class="layout horizontal configuration">
            <wl-icon class="fg green">view_module</wl-icon>
            <span>${this._markIfUnlimited(i.item.resource_slots["cuda.shares"])}</span>
            <span class="indicator">GPU</span>
          </div>
        `:g``}
        ${i.item.shared_memory?g`
          <div class="layout horizontal configuration">
            <wl-icon class="fg blue">memory</wl-icon>
            <span>${i.item.shared_memory_gb}</span>
            <span class="indicator">GB</span>
          </div>
        `:g``}
        </div>
      `,e)}controlRenderer(e,t,i){h(g`
        <div id="controls" class="layout horizontal flex center"
            .preset-name="${i.item.name}">
          ${this.is_admin?g`
            <wl-button class="fg blue controls-running" fab flat inverted
              @click="${e=>this._launchResourcePresetDialog(e)}">
                <wl-icon>settings</wl-icon>
            </wl-button>
            <wl-button class="fg red controls-running" fab flat inverted
              @click="${e=>this._launchDeleteResourcePresetDialog(e)}">
                <wl-icon>delete</wl-icon>
            </wl-button>
          `:g``}
        </div>
      `,e)}_indexRenderer(e,t,i){const a=i.index+1;h(g`
        <div>${a}</div>
      `,e)}render(){return g`
      <div style="margin:0px;">
        <h4 class="horizontal flex center center-justified layout">
          <span>${m("resourcePreset.ResourcePresets")}</span>
          <span class="flex"></span>
          <mwc-button raised id="add-resource-preset" icon="add" label="${m("resourcePreset.CreatePreset")}" @click="${()=>this._launchPresetAddDialog()}"></mwc-button>
        </h4>
        <div class="list-wrapper">
          <vaadin-grid theme="row-stripes column-borders compact" height-by-rows aria-label="Resource Policy list"
                      .items="${this.resourcePresets}">
            <vaadin-grid-column width="40px" flex-grow="0" header="#" text-align="center" .renderer="${this._indexRenderer}"></vaadin-grid-column>
            <vaadin-grid-sort-column resizable path="name" header="${m("resourcePreset.Name")}">
            </vaadin-grid-sort-column>
            <vaadin-grid-column width="150px" resizable header="${m("resourcePreset.Resources")}" .renderer="${this._boundResourceRenderer}">
            </vaadin-grid-column>
            <vaadin-grid-column resizable header="${m("general.Control")}" .renderer="${this._boundControlRenderer}">
            </vaadin-grid-column>
          </vaadin-grid>
          <backend-ai-list-status id="list-status" statusCondition="${this.listCondition}" message="${u("resourcePreset.NoResourcePresetToDisplay")}"></backend-ai-list-status>
        </div>
      </div>
      <backend-ai-dialog id="modify-template-dialog" fixed backdrop blockscrolling narrowLayout>
        <span slot="title">${m("resourcePreset.ModifyResourcePreset")}</span>
        <div slot="content">
          <form id="login-form">
            <fieldset>
              <mwc-textfield type="text" name="preset_name" class="modify" id="id-preset-name"
                          label="${m("resourcePreset.PresetName")}"
                          auto-validate required
                          disabled
                          error-message="${m("data.Allowslettersnumbersand-_dot")}"></mwc-textfield>
              <h4>${m("resourcePreset.ResourcePreset")}</h4>
              <div class="horizontal center layout">
                <mwc-textfield id="cpu-resource" class="modify" type="number" label="CPU"
                    min="1" value="1" required validationMessage="${m("resourcePreset.MinimumCPUUnit")}"></mwc-textfield>
                <mwc-textfield id="ram-resource" class="modify" type="number" label="${m("resourcePreset.RAM")}"
                    min="1" value="1" required validationMessage="${m("resourcePreset.MinimumMemUnit")}"></mwc-textfield>
              </div>
              <div class="horizontal center layout">
                <mwc-textfield id="gpu-resource" class="modify" type="number" label="GPU"
                    min="0" value="0" ?disabled=${"fractional"===this.gpuAllocationMode}></mwc-textfield>
                <mwc-textfield id="fgpu-resource" class="modify" type="number" label="fGPU"
                    min="0" value="0" step="0.01" ?disabled=${"fractional"!==this.gpuAllocationMode}></mwc-textfield>
              </div>
              <div class="horizontal center layout">
                <mwc-textfield id="shmem-resource" class="modify" type="number"
                    label="${m("resourcePreset.SharedMemory")}" min="0" step="0.01"
                    validationMessage="${m("resourcePreset.MinimumShmemUnit")}"></mwc-textfield>
              </div>
            </fieldset>
          </form>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout distancing">
          <mwc-button
              unelevated
              fullwidth
              icon="check"
              label="${m("button.SaveChanges")}"
              @click="${()=>this._modifyResourceTemplate()}">
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="create-preset-dialog" fixed backdrop blockscrolling narrowLayout>
        <span slot="title">${m("resourcePreset.CreateResourcePreset")}</span>
        <div slot="content">
          <mwc-textfield
            type="text"
            name="preset_name"
            id="create-preset-name"
            class="create"
            label="Preset Name"
            auto-validate
            required
            maxLength="255"
            placeholder="${m("maxLength.255chars")}"
            error-message="${m("data.Allowslettersnumbersand-_")}"
          ></mwc-textfield>
          <h4>${m("resourcePreset.ResourcePreset")}</h4>
          <div class="horizontal center layout">
            <mwc-textfield id="create-cpu-resource" class="create" type="number" label="CPU"
                min="1" value="1" required validationMessage="${m("resourcePreset.MinimumCPUUnit")}"></mwc-textfield>
            <mwc-textfield id="create-ram-resource" class="create" type="number" label="${m("resourcePreset.RAM")}"
                min="1" value="1" required validationMessage="${m("resourcePreset.MinimumMemUnit")}"></mwc-textfield>
          </div>
          <div class="horizontal center layout">
            <mwc-textfield id="create-gpu-resource" class="create" type="number" label="GPU"
                min="0" value="0" ?disabled=${"fractional"===this.gpuAllocationMode}></mwc-textfield>
            <mwc-textfield id="create-fgpu-resource" class="create" type="number" label="fGPU"
                min="0" value="0" step="0.01" ?disabled=${"fractional"!==this.gpuAllocationMode}></mwc-textfield>
          </div>
          <div class="horizontal center layout">
            <mwc-textfield id="create-shmem-resource" class="create" type="number"
                label="${m("resourcePreset.SharedMemory")}" min="0" step="0.01"
                validationMessage="${m("resourcePreset.MinimumShmemUnit")}"></mwc-textfield>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout distancing">
          <mwc-button
              unelevated
              fullwidth
              id="create-policy-button"
              icon="add"
              label="${m("button.Add")}"
              @click="${this._createPreset}">
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-resource-preset-dialog" fixed backdrop blockscrolling>
         <span slot="title">${m("dialog.title.LetsDouble-Check")}</span>
         <div slot="content">
            <p>${m("resourcePreset.AboutToDeletePreset")}</p>
            <p style="text-align:center;">${this.presetName}</p>
            <p>${m("dialog.warning.CannotBeUndone")} ${m("dialog.ask.DoYouWantToProceed")}</p>
         </div>
         <div slot="footer" class="horizontal end-justified flex layout">
         <mwc-button
              class="operation"
              label="${m("button.Cancel")}"
              @click="${e=>this._hideDialog(e)}"></mwc-button>
          <mwc-button
              unelevated
              class="operation"
              label="${m("button.Okay")}"
              @click="${()=>this._deleteResourcePresetWithCheck()}"></mwc-button>
         </div>
      </backend-ai-dialog>
    `}firstUpdated(){var e;this.notification=globalThis.lablupNotification;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("mwc-textfield");null==t||t.forEach((e=>{this._addInputValidator(e)}))}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._refreshTemplateData(),this.is_admin=globalThis.backendaiclient.is_admin}),!0):(this._refreshTemplateData(),this.is_admin=globalThis.backendaiclient.is_admin,globalThis.backendaiclient.get_resource_slots().then((e=>{this.gpu_allocatable=2!==Object.keys(e).length,Object.keys(e).includes("cuda.shares")?this.gpuAllocationMode="fractional":this.gpuAllocationMode="device"}))))}_launchPresetAddDialog(){this.createPresetDialog.show()}_launchResourcePresetDialog(e){this.updateCurrentPresetToDialog(e),this.modifyTemplateDialog.show()}_launchDeleteResourcePresetDialog(e){const t=e.target.closest("#controls")["preset-name"];this.presetName=t,this.deleteResourcePresetDialog.show()}_deleteResourcePresetWithCheck(){globalThis.backendaiclient.resourcePreset.delete(this.presetName).then((e=>{this.deleteResourcePresetDialog.hide(),this.notification.text=u("resourcePreset.Deleted"),this.notification.show(),this._refreshTemplateData()})).catch((e=>{console.log(e),e&&e.message&&(this.deleteResourcePresetDialog.hide(),this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}updateCurrentPresetToDialog(e){const t=e.target.closest("#controls")["preset-name"],i=globalThis.backendaiclient.utils.gqlToObject(this.resourcePresets,"name")[t];this.presetNameInput.value=t,this.cpuResourceInput.value=i.resource_slots.cpu,this.gpuResourceInput.value="cuda.device"in i.resource_slots?i.resource_slots["cuda.device"]:"",this.fgpuResourceInput.value="cuda.shares"in i.resource_slots?i.resource_slots["cuda.shares"]:"",this.ramResourceInput.value=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(i.resource_slots.mem,"g")).toString(),this.sharedMemoryResourceInput.value=i.shared_memory?parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(i.shared_memory,"g")).toFixed(2):""}_refreshTemplateData(){var e;const t={group:globalThis.backendaiclient.current_group};return this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.resourcePreset.check(t).then((e=>{var t;const i=e.presets;Object.keys(i).map(((e,t)=>{const a=i[e];a.resource_slots.mem_gb=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(a.resource_slots.mem,"g")),a.shared_memory?a.shared_memory_gb=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(a.shared_memory,"g")).toFixed(2):a.shared_memory_gb=null})),this.resourcePresets=i,0==this.resourcePresets.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}refresh(){this._refreshTemplateData()}_isActive(){return"active"===this.condition}_readResourcePresetInput(){const e=e=>void 0!==e&&e.includes("Unlimited")?"Infinity":e,t=e(this.cpuResourceInput.value),i=e(this.ramResourceInput.value+"g"),a=e(this.gpuResourceInput.value),s=e(this.fgpuResourceInput.value);let o=this.sharedMemoryResourceInput.value;o&&(o+="g");const r={cpu:t,mem:i};null!=a&&""!==a&&"0"!==a&&(r["cuda.device"]=parseInt(a)),null!=s&&""!==s&&"0"!==s&&(r["cuda.shares"]=parseFloat(s));return{resource_slots:JSON.stringify(r),shared_memory:o}}_modifyResourceTemplate(){if(!this._checkFieldValidity("modify"))return;const e=this.presetNameInput.value,t=void 0!==(i=this.ramResourceInput.value+"g")&&i.includes("Unlimited")?"Infinity":i;var i;if(!e)return this.notification.text=u("resourcePreset.NoPresetName"),void this.notification.show();const a=this._readResourcePresetInput();if(parseInt(a.shared_memory)>=parseInt(t))return this.notification.text=u("resourcePreset.MemoryShouldBeLargerThanSHMEM"),void this.notification.show();globalThis.backendaiclient.resourcePreset.mutate(e,a).then((e=>{this.modifyTemplateDialog.hide(),this.notification.text=u("resourcePreset.Updated"),this.notification.show(),this._refreshTemplateData()})).catch((e=>{console.log(e),e&&e.message&&(this.modifyTemplateDialog.hide(),this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_deleteKey(e){const t=e.target.closest("#controls").accessKey;globalThis.backendaiclient.keypair.delete(t).then((e=>{this.refresh()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_findKeyItem(e){return e.access_key=this}_elapsed(e,t){const i=new Date(e);let a;a=(this.condition,new Date);const s=Math.floor((a.getTime()-i.getTime())/1e3);return Math.floor(s/86400)}_humanReadableTime(e){return(e=new Date(e)).toUTCString()}_indexFrom1(e){return e+1}_markIfUnlimited(e){return["-",0,"Unlimited",1/0,"Infinity"].includes(e)?"∞":e}_checkFieldValidity(e=""){var t;const i='mwc-textfield[class^="'.concat(e).concat('"]'),a=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(i);let s=!0;for(const e of Array.from(a))if(s=e.checkValidity(),!s)return e.checkValidity();return s}_createPreset(){if(!this._checkFieldValidity("create"))return;const e=e=>void 0!==(e=e.toString())&&e.includes("Unlimited")?"Infinity":e,t=e(this.createPresetNameInput.value),i=e(this.createCpuResourceInput.value),a=e(this.createRamResourceInput.value+"g"),s=e(this.createGpuResourceInput.value),o=e(this.createFGpuResourceInput.value);let r=this.createSharedMemoryResourceInput.value;if(r&&(r+="g"),!t)return this.notification.text=u("resourcePreset.NoPresetName"),void this.notification.show();if(parseInt(r)>=parseInt(a))return this.notification.text=u("resourcePreset.MemoryShouldBeLargerThanSHMEM"),void this.notification.show();const l={cpu:i,mem:a};null!=s&&""!==s&&"0"!==s&&(l["cuda.device"]=parseInt(s)),null!=o&&""!==o&&"0"!==o&&(l["cuda.shares"]=parseFloat(o));const n={resource_slots:JSON.stringify(l),shared_memory:r};globalThis.backendaiclient.resourcePreset.add(t,n).then((e=>{this.createPresetDialog.hide(),e.create_resource_preset.ok?(this.notification.text=u("resourcePreset.Created"),this.refresh(),this.createPresetNameInput.value="",this.createCpuResourceInput.value="1",this.createRamResourceInput.value="1",this.createGpuResourceInput.value="0",this.createFGpuResourceInput.value="0",this.createSharedMemoryResourceInput.value=""):this.notification.text=p.relieve(e.create_resource_preset.msg),this.notification.show()}))}};var y;e([t({type:Array})],b.prototype,"resourcePolicy",void 0),e([t({type:Boolean})],b.prototype,"is_admin",void 0),e([t({type:Boolean})],b.prototype,"active",void 0),e([t({type:Boolean})],b.prototype,"gpu_allocatable",void 0),e([t({type:String})],b.prototype,"gpuAllocationMode",void 0),e([t({type:String})],b.prototype,"condition",void 0),e([t({type:String})],b.prototype,"presetName",void 0),e([t({type:Object})],b.prototype,"resourcePresets",void 0),e([t({type:String})],b.prototype,"listCondition",void 0),e([t({type:Array})],b.prototype,"_boundResourceRenderer",void 0),e([t({type:Array})],b.prototype,"_boundControlRenderer",void 0),e([i("#create-preset-name")],b.prototype,"createPresetNameInput",void 0),e([i("#create-cpu-resource")],b.prototype,"createCpuResourceInput",void 0),e([i("#create-ram-resource")],b.prototype,"createRamResourceInput",void 0),e([i("#create-gpu-resource")],b.prototype,"createGpuResourceInput",void 0),e([i("#create-fgpu-resource")],b.prototype,"createFGpuResourceInput",void 0),e([i("#create-shmem-resource")],b.prototype,"createSharedMemoryResourceInput",void 0),e([i("#cpu-resource")],b.prototype,"cpuResourceInput",void 0),e([i("#ram-resource")],b.prototype,"ramResourceInput",void 0),e([i("#gpu-resource")],b.prototype,"gpuResourceInput",void 0),e([i("#fgpu-resource")],b.prototype,"fgpuResourceInput",void 0),e([i("#shmem-resource")],b.prototype,"sharedMemoryResourceInput",void 0),e([i("#id-preset-name")],b.prototype,"presetNameInput",void 0),e([i("#create-preset-dialog")],b.prototype,"createPresetDialog",void 0),e([i("#modify-template-dialog")],b.prototype,"modifyTemplateDialog",void 0),e([i("#delete-resource-preset-dialog")],b.prototype,"deleteResourcePresetDialog",void 0),e([i("#list-status")],b.prototype,"_listStatus",void 0),b=e([a("backend-ai-resource-preset-list")],b);let f=y=class extends s{constructor(){super(),this._listCondition="loading",this._editMode=!1,this._registryType="docker",this._selectedIndex=-1,this._boundIsEnabledRenderer=this._isEnabledRenderer.bind(this),this._boundControlsRenderer=this._controlsRenderer.bind(this),this._boundPasswordRenderer=this._passwordRenderer.bind(this),this._allowed_registries=[],this._editMode=!1,this._hostnames=[],this._registryList=[]}static get styles(){return[o,r,l,c`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 225px);
        }

        h4 {
          font-weight: 200;
          font-size: 14px;
          margin: 0px;
          padding: 5px 15px 5px 20px;
        }

        wl-button {
          --button-bg: var(--paper-yellow-50);
          --button-bg-hover: var(--paper-yellow-100);
          --button-bg-active: var(--paper-yellow-600);
        }

        wl-button.delete {
          --button-bg: var(--paper-red-50);
          --button-bg-hover: var(--paper-red-100);
          --button-bg-active: var(--paper-red-600);
        }

        backend-ai-dialog wl-textfield {
          --input-font-family: var(--general-font-family);
          --input-state-color-invalid: #b00020;
          margin-bottom: 20px;
        }

        backend-ai-dialog {
          --component-min-width: 350px;
        }

        wl-textfield.helper-text {
          margin-bottom: 0px;
        }

        wl-textfield#configure-project-name {
          --input-label-space: 20px;
        }

        wl-label.helper-text {
          --label-color: #b00020;
          --label-font-family: 'Ubuntu', Roboto;
          --label-font-size: 11px;
        }

        mwc-select#select-registry-type {
          width: 100%;
          --mdc-select-fill-color: transparent;
          --mdc-theme-primary: var(--general-textfield-selected-color);
          --mdc-menu-max-width: 362px;
          --mdc-menu-min-width: 362px;
        }

        mwc-list-item {
          height: 30px;
          --mdc-list-item-graphic-margin: 0px;
        }

        input#registry-password {
          border: none;
          background: none;
          pointer-events: none;
        }

        mwc-button, mwc-button[unelevated] {
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
          --mdc-typography-font-family: var(--general-font-family);
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification,this._indicator=globalThis.lablupIndicator}_parseRegistryList(e){return Object.keys(e).map((t=>{return"string"==typeof(i=e[t])||i instanceof String?{"":e[t],hostname:t}:{...e[t],hostname:t};var i}))}_refreshRegistryList(){var e;this._listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.domain.get(globalThis.backendaiclient._config.domainName,["allowed_docker_registries"]).then((e=>(this._allowed_registries=e.domain.allowed_docker_registries,globalThis.backendaiclient.registry.list()))).then((({result:e})=>{var t;this._registryList=this._parseRegistryList(e),0==this._registryList.length?this._listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide(),this._hostnames=this._registryList.map((e=>e.hostname)),this.requestUpdate()}))}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._refreshRegistryList()}),!0):this._refreshRegistryList())}_addRegistry(){const e=this._hostnameInput.value,t=this._urlInput.value,i=this._usernameInput.value,a=this._passwordInput.value,s=this._selectedRegistryTypeInput.value,o=this._projectNameInput.value.replace(/\s/g,"");if(!this._hostnameInput.valid)return void(this._registryHostnameValidationMsg&&(this._registryHostnameValidationMsg.style.display="block"));if(!this._urlInput.valid)return void(this._registryUrlValidationMsg&&(this._registryUrlValidationMsg.style.display="block"));const r={};if(r[""]=t,""!==i&&""!==a&&(r.username=i,r.password=a),r.type=s,["harbor","harbor2"].includes(s)){if(!o||""===o)return;r.project=o}else r.project="";if(!this._editMode&&this._hostnames.includes(e))return this.notification.text=u("registry.RegistryHostnameAlreadyExists"),void this.notification.show();globalThis.backendaiclient.registry.set(e,r).then((({result:t})=>{"ok"===t?(this._editMode?this.notification.text=u("registry.RegistrySuccessfullyModified"):(this.notification.text=u("registry.RegistrySuccessfullyAdded"),this._hostnames.push(e),this._resetRegistryField()),this._refreshRegistryList()):this.notification.text=u("dialog.ErrorOccurred"),this._hideDialogById("#configure-registry-dialog"),this.notification.show()}))}_deleteRegistry(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#delete-registry"),i=t.value;this._registryList[this._selectedIndex].hostname===i?globalThis.backendaiclient.registry.delete(t.value).then((({result:e})=>{"ok"===e?(this.notification.text=u("registry.RegistrySuccessfullyDeleted"),this._hostnames.includes(i)&&this._hostnames.splice(this._hostnames.indexOf(i)),this._refreshRegistryList()):this.notification.text=u("dialog.ErrorOccurred"),this._hideDialogById("#delete-registry-dialog"),this.notification.show()})):(this.notification.text=u("registry.HostnameDoesNotMatch"),this.notification.show()),t.value=""}async _rescanImage(){const e=await this._indicator.start("indeterminate");e.set(10,u("registry.UpdatingRegistryInfo")),globalThis.backendaiclient.maintenance.rescan_images(this._registryList[this._selectedIndex].hostname).then((({rescan_images:t})=>{if(t.ok){e.set(0,u("registry.RescanImages"));const i=globalThis.backendaiclient.maintenance.attach_background_task(t.task_id);i.addEventListener("bgtask_updated",(t=>{const i=JSON.parse(t.data),a=i.current_progress/i.total_progress;e.set(100*a,u("registry.RescanImages"))})),i.addEventListener("bgtask_done",(()=>{const t=new CustomEvent("image-rescanned");document.dispatchEvent(t),e.set(100,u("registry.RegistryUpdateFinished")),i.close()})),i.addEventListener("bgtask_failed",(e=>{throw console.log("bgtask_failed",e.data),i.close(),new Error("Background Image scanning task has failed")})),i.addEventListener("bgtask_cancelled",(()=>{throw i.close(),new Error("Background Image scanning task has been cancelled")}))}else e.set(50,u("registry.RegistryUpdateFailed")),e.end(1e3),this.notification.text=p.relieve(t.msg),this.notification.detail=t.msg,this.notification.show()})).catch((t=>{console.log(t),e.set(50,u("registry.RescanFailed")),e.end(1e3),t&&t.message&&(this.notification.text=p.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))}))}_launchDialogById(e){var t;null===(t=this.shadowRoot)||void 0===t||t.querySelector(e).show()}_hideDialogById(e){var t;null===(t=this.shadowRoot)||void 0===t||t.querySelector(e).hide()}_openCreateRegistryDialog(){this._editMode=!1,this._selectedIndex=-1,this._registryType="docker",this.requestUpdate(),this._launchDialogById("#configure-registry-dialog")}_resetValidationMessage(){this._registryHostnameValidationMsg.style.display="none",this._registryUrlValidationMsg.style.display="none",this._projectNameValidationMsg.style.display="none"}_openEditRegistryDialog(e){var t;let i;this._editMode=!0;for(let t=0;t<this._registryList.length;t++)if(this._registryList[t].hostname===e){i=this._registryList[t];break}i?(this._registryList[this._selectedIndex]=i,this._registryType=null===(t=this._registryList[this._selectedIndex])||void 0===t?void 0:t.type,this.requestUpdate(),this._resetValidationMessage(),this._launchDialogById("#configure-registry-dialog")):globalThis.notification.show(`No such registry hostname: ${e}`)}_toggleValidationMsgOnUrlInput(){this._registryUrlValidationMsg.style.display=this._urlInput.valid?"none":"block"}_toggleValidationMsgOnHostnameInput(){const e=this._hostnameInput.value;this._registryHostnameValidationMsg.style.display=e&&""!==e?"none":"block"}_toggleValidationMsgOnProjectNameInput(){this._projectNameInput.value=this._projectNameInput.value.replace(/\s/g,""),this._projectNameValidationMsg.style.display="block",["harbor","harbor2"].includes(this._registryType)?(this._projectNameInput.value?this._projectNameValidationMsg.style.display="none":this._projectNameValidationMsg.textContent=u("registry.ProjectNameIsRequired"),this._projectNameInput.disabled=!1):(this._projectNameValidationMsg.textContent=u("registry.ForHarborOnly"),this._projectNameInput.disabled=!0)}_toggleRegistryEnabled(e,t){e.target.selected?this._changeRegistryState(t,!0):this._changeRegistryState(t,!1)}_toggleProjectNameInput(){this._registryType=this._selectedRegistryTypeInput.value,this._toggleValidationMsgOnProjectNameInput()}_resetRegistryField(){this._hostnameInput.value="",this._urlInput.value="",this._usernameInput.value="",this._passwordInput.value="",this._selectedRegistryTypeInput.value="",this._projectNameInput.value="",this.requestUpdate()}_changeRegistryState(e,t){if(!0===t)this._allowed_registries.push(e),this.notification.text=u("registry.RegistryTurnedOn");else{const t=this._allowed_registries.indexOf(e);1!==t&&this._allowed_registries.splice(t,1),this.notification.text=u("registry.RegistryTurnedOff")}globalThis.backendaiclient.domain.update(globalThis.backendaiclient._config.domainName,{allowed_docker_registries:this._allowed_registries}).then((e=>{this.notification.show()}))}_indexRenderer(e,t,i){const a=i.index+1;h(g`
        <div>${a}</div>
      `,e)}_hostNameRenderer(e,t,i){h(g`
        <div>
          ${decodeURIComponent(i.item.hostname)}
        </div>
      `,e)}_registryUrlRenderer(e,t,i){h(g`
        <div>
          ${i.item[""]}
        </div>
      `,e)}_passwordRenderer(e,t,i){h(g`
        <div>
          <input type="password" id="registry-password" readonly value="${i.item.password}"/>
        </div>
      `,e)}_isEnabledRenderer(e,t,i){h(g`
        <div>
          <mwc-switch
              @click="${e=>this._toggleRegistryEnabled(e,i.item.hostname)}"
              ?selected="${this._allowed_registries.includes(i.item.hostname)}"></mwc-switch>
        </div>
      `,e)}_controlsRenderer(e,t,i){h(g`
        <div icon="settings" id="controls" class="layout horizontal flex center">
          <wl-button fab flat inverted
            class="fg blue"
            @click=${()=>{this._selectedIndex=i.index,this._openEditRegistryDialog(i.item.hostname)}}>
            <wl-icon>settings</wl-icon>
          </wl-button>
          <wl-button fab flat inverted
            icon="delete"
            class="fg red"
            @click=${()=>{this._selectedIndex=i.index,this._launchDialogById("#delete-registry-dialog")}}>
            <wl-icon>delete</wl-icon>
          </wl-button>
          <wl-button fab flat inverted
            icon="refresh"
            class="fg green"
            @click=${()=>{this._selectedIndex=i.index,this._rescanImage()}}>
            <wl-icon>refresh</wl-icon>
          </wl-button>
        </div>
      `,e)}render(){var e,t,i,a,s,o;return g`
      <h4 class="horizontal flex center center-justified layout">
        <span>${m("registry.Registries")}</span>
        <span class="flex"></span>
        <mwc-button raised id="add-registry" label="${m("registry.AddRegistry")}" icon="add"
            @click=${()=>this._openCreateRegistryDialog()}></mwc-button>
      </h4>
      <div class="list-wrapper">
        <vaadin-grid theme="row-stripes column-borders compact" aria-label="Registry list" .items="${this._registryList}">
          <vaadin-grid-column flex-grow="0" width="40px" header="#" text-align="center" .renderer=${this._indexRenderer}>
          </vaadin-grid-column>
          <vaadin-grid-column flex-grow="1" auto-width header="${m("registry.Hostname")}" .renderer=${this._hostNameRenderer}>
          </vaadin-grid-column>
          <vaadin-grid-column flex-grow="2" auto-width header="${m("registry.RegistryURL")}" resizable .renderer=${this._registryUrlRenderer}>
          </vaadin-grid-column>
          <vaadin-grid-column flex-grow="0" auto-width resizable header="${m("registry.Type")}" path="type">
          </vaadin-grid-column>
          <vaadin-grid-column flex-grow="0" auto-width resizable header="${m("registry.HarborProject")}" path="project">
          </vaadin-grid-column>
          <vaadin-grid-column flex-grow="1" header="${m("registry.Username")}" path="username">
          </vaadin-grid-column>
          <vaadin-grid-column flex-grow="1" header="${m("registry.Password")}" .renderer="${this._boundPasswordRenderer}">
          </vaadin-grid-column>
          <vaadin-grid-column flex-grow="0" width="60px" header="${m("general.Enabled")}" .renderer=${this._boundIsEnabledRenderer}></vaadin-grid-column>
          <vaadin-grid-column flex-grow="1" header="${m("general.Control")}" .renderer=${this._boundControlsRenderer}>
          </vaadin-grid-column>
        </vaadin-grid>
        <backend-ai-list-status id="list-status" statusCondition="${this._listCondition}" message="${u("registry.NoRegistryToDisplay")}"></backend-ai-list-status>
      </div>
      <backend-ai-dialog id="configure-registry-dialog" fixed backdrop blockscrolling>
        <span slot="title">${this._editMode?m("registry.ModifyRegistry"):m("registry.AddRegistry")}</span>
        <div slot="content" class="login-panel intro centered">
          <wl-textfield
            id="configure-registry-hostname"
            class="helper-text"
            type="text"
            label="${m("registry.RegistryHostname")}"
            required
            ?disabled="${this._editMode}"
            value="${(null===(e=this._registryList[this._selectedIndex])||void 0===e?void 0:e.hostname)||""}"
            @click=${()=>this._toggleValidationMsgOnHostnameInput()}
            @change=${()=>this._toggleValidationMsgOnHostnameInput()}
          ></wl-textfield>
          <wl-label class="helper-text" id="registry-hostname-validation" style="display:none;">${m("registry.DescHostnameIsEmpty")}</wl-label>
          <wl-textfield
            id="configure-registry-url"
            class="helper-text"
            label="${m("registry.RegistryURL")}"
            required
            pattern="^(https?):\/\/(([a-zA-Z\d\.]{2,})\.([a-zA-Z]{2,})|(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3})(:((6553[0-5])|(655[0-2])|(65[0-4][0-9]{2})|(6[0-4][0-9]{3})|([1-5][0-9]{4})|([0-5]{0,5})|([0-9]{1,4})))?$"
            value="${(null===(t=this._registryList[this._selectedIndex])||void 0===t?void 0:t[""])||""}"
            @click=${()=>this._toggleValidationMsgOnUrlInput()}
            @change=${()=>this._toggleValidationMsgOnUrlInput()}
          ></wl-textfield>
          <wl-label class="helper-text" id="registry-url-validation" style="display:none;">${m("registry.DescURLStartString")}</wl-label>
         <div class="horizontal layout flex">
          <wl-textfield
            id="configure-registry-username"
            type="text"
            label="${m("registry.UsernameOptional")}"
            style="padding-right:10px;"
            value="${(null===(i=this._registryList[this._selectedIndex])||void 0===i?void 0:i.username)||""}"
          ></wl-textfield>
          <wl-textfield
            id="configure-registry-password"
            type="password"
            label="${m("registry.PasswordOptional")}"
            style="padding-left:10px;"
            value="${(null===(a=this._registryList[this._selectedIndex])||void 0===a?void 0:a.password)||""}"
          ></wl-textfield>
        </div>
        <mwc-select
          id="select-registry-type"
          label="${m("registry.RegistryType")}"
          @change=${this._toggleProjectNameInput}
          required
          validationMessage="${m("registry.PleaseSelectOption")}"
          value="${(null===(s=this._registryList[this._selectedIndex])||void 0===s?void 0:s.type)||this._registryType}">
          ${y._registryTypes.map((e=>{var t;return g`
            <mwc-list-item
              value="${e}"
              ?selected="${this._editMode?e===(null===(t=this._registryList[this._selectedIndex])||void 0===t?void 0:t.type):"docker"===e}">
              ${e}
            </mwc-list-item>
          `}))}
        </mwc-select>
        <div class="vertical layout end-justified">
          <wl-textfield
            id="configure-project-name"
            class="helper-text"
            type="text"
            label="${m("registry.ProjectName")}"
            required
            value="${(null===(o=this._registryList[this._selectedIndex])||void 0===o?void 0:o.project)||""}"
            ?disabled="${"docker"===this._registryType}"
            @change=${this._toggleValidationMsgOnProjectNameInput}
          ></wl-textfield>
          <wl-label class="helper-text" id="project-name-validation">
            ${this._editMode?g``:m("registry.ForHarborOnly")}
          </wl-label>
         </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button unelevated fullwidth icon="add"
            label=${this._editMode?m("button.Save"):m("button.Add")}
            @click=${()=>this._addRegistry()}></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-registry-dialog" fixed backdrop blockscrolling>
        <span slot="title">${m("dialog.warning.CannotBeUndone")}</span>
        <div slot="content">
          <wl-textfield
            id="delete-registry"
            type="text"
            label="${m("registry.TypeRegistryNameToDelete")}"
          ></wl-textfield>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button unelevated fullwidth icon="delete" label="${m("button.Delete")}"
              @click=${()=>this._deleteRegistry()}></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};f._registryTypes=["docker","harbor","harbor2"],e([i("#list-status")],f.prototype,"_listStatus",void 0),e([i("#configure-registry-hostname")],f.prototype,"_hostnameInput",void 0),e([i("#configure-registry-password")],f.prototype,"_passwordInput",void 0),e([i("#configure-project-name")],f.prototype,"_projectNameInput",void 0),e([i("#select-registry-type")],f.prototype,"_selectedRegistryTypeInput",void 0),e([i("#configure-registry-url")],f.prototype,"_urlInput",void 0),e([i("#configure-registry-username")],f.prototype,"_usernameInput",void 0),e([i("#registry-url-validation")],f.prototype,"_registryUrlValidationMsg",void 0),e([i("#registry-hostname-validation")],f.prototype,"_registryHostnameValidationMsg",void 0),e([i("#project-name-validation")],f.prototype,"_projectNameValidationMsg",void 0),f=y=e([a("backend-ai-registry-list")],f);
/**
 @license
 Copyright (c) 2015-2022 Lablup Inc. All rights reserved.
 */
let _=class extends s{constructor(){super(...arguments),this.images=Object(),this.is_superadmin=!1,this._activeTab="image-lists"}static get styles(){return[o,r,l,c`
          wl-tab-group {
              --tab-group-indicator-bg: var(--paper-yellow-600);
          }

          wl-tab {
              --tab-color: #666;
              --tab-color-hover: #222;
              --tab-color-hover-filled: #222;
              --tab-color-active: var(--paper-yellow-900);
              --tab-color-active-hover: var(--paper-yellow-900);
              --tab-color-active-filled: #ccc;
              --tab-bg-active: var(--paper-yellow-200);
              --tab-bg-filled: var(--paper-yellow-200);
              --tab-bg-active-hover: var(--paper-yellow-200);
          }

          h3.tab {
            background-color: var(--general-tabbar-background-color);
            border-radius: 5px 5px 0px 0px;
            margin: 0px auto;
          }

          mwc-tab-bar {
            --mdc-theme-primary: var(--general-sidebar-selected-color);
            --mdc-text-transform: none;
            --mdc-tab-color-default: var(--general-tabbar-background-color);
            --mdc-tab-text-label-color-default: var(--general-tabbar-tab-disabled-color);
          }

          div h4 {
              margin: 0;
              font-weight: 100;
              font-size: 16px;
              padding-left: 20px;
              border-bottom: 1px solid #ccc;
              width: 100%;
          }

          wl-card wl-card {
              margin: 0;
              padding: 0;
              --card-elevation: 0;
          }

          @media screen and (max-width: 805px) {
            mwc-tab, mwc-button {
              --mdc-typography-button-font-size: 10px;
            }

            wl-tab {
              width: 5px;
            }
          }
      `]}static get properties(){return{active:{type:Boolean},_activeTab:{type:String}}}async _viewStateChanged(e){return await this.updateComplete,!1===e||(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_superadmin=globalThis.backendaiclient.is_superadmin}),!0):this.is_superadmin=globalThis.backendaiclient.is_superadmin,!1)}_showTab(e){var t,i;const a=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(let e=0;e<a.length;e++)a[e].style.display="none";this._activeTab=e.title,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e.title)).style.display="block"}render(){return g`
      <link rel="stylesheet" href="resources/custom.css">
      <lablup-activity-panel noheader narrow autowidth>
        <div slot="message">
          <h3 class="tab horizontal center layout">
            <mwc-tab-bar>
              <mwc-tab title="image-lists" label="${m("environment.Images")}" @click="${e=>this._showTab(e.target)}"></mwc-tab>
              <mwc-tab title="resource-template-lists" label="${m("environment.ResourcePresets")}" @click="${e=>this._showTab(e.target)}"></mwc-tab>
              ${this.is_superadmin?g`
                <mwc-tab title="registry-lists" label="${m("environment.Registries")}" @click="${e=>this._showTab(e.target)}"></mwc-tab>
              `:g``}
            </mwc-tab-bar>
            <div class="flex"></div>
          </h3>
          <div id="image-lists" class="tab-content">
            <backend-ai-environment-list ?active="${"image-lists"===this._activeTab}"></backend-ai-environment-list>
          </div>
          <backend-ai-resource-preset-list id="resource-template-lists" class="admin item tab-content" style="display: none" ?active="${"resource-template-lists"===this._activeTab}"></backend-ai-resource-preset-list>
          <div id="registry-lists" class="tab-content">
            <backend-ai-registry-list ?active="${"registry-lists"===this._activeTab}"> </backend-ai-registry-list>
          </div>
        </div>
      </lablup-activity-panel>
    `}};e([t({type:String})],_.prototype,"images",void 0),e([t({type:Boolean})],_.prototype,"is_superadmin",void 0),e([t({type:String})],_.prototype,"_activeTab",void 0),_=e([a("backend-ai-environment-view")],_);var w=_;export{w as default};
