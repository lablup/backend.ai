import{_ as e,n as t,b as i,e as a,B as s,c as o,I as r,a as n,m as l,d,i as c,g as m,f as u,t as p,l as h,x as g}from"./backend-ai-webui-75df15ed.js";import"./lablup-grid-sort-filter-column-54638b7b.js";import"./lablup-loading-spinner-02aea3b9.js";import"./slider-3f740add.js";import"./vaadin-grid-461d199a.js";import"./vaadin-grid-filter-column-2b22f222.js";import"./vaadin-grid-selection-column-29a490b5.js";import"./vaadin-grid-sort-column-d722536e.js";import"./mwc-switch-13f7c132.js";import"./backend-ai-list-status-fa13c15b.js";import"./vaadin-item-19772d96.js";import"./lablup-activity-panel-86e1deef.js";import"./mwc-tab-bar-45ba859c.js";import"./dir-utils-f5050166.js";import"./vaadin-item-mixin-57783787.js";let v=class extends s{constructor(){super(),this.selectedIndex=0,this.selectedImages=[],this._cuda_gpu_disabled=!1,this._cuda_fgpu_disabled=!1,this._rocm_gpu_disabled=!1,this._tpu_disabled=!1,this._ipu_disabled=!1,this._atom_disabled=!1,this._warboy_disabled=!1,this.alias=Object(),this.indicator=Object(),this.deleteAppInfo=Object(),this.deleteAppRow=Object(),this.installImageResource=Object(),this.selectedCheckbox=Object(),this._grid=Object(),this.servicePortsMsg="",this._range={cpu:["1","2","3","4","5","6","7","8"],mem:["64MB","128MB","256MB","512MB","1GB","2GB","4GB","8GB","16GB","32GB","256GB","512GB"],"cuda-gpu":["0","1","2","3","4","5","6","7"],"cuda-fgpu":["0","0.1","0.2","0.5","1.0","2.0","4.0","8.0"],"rocm-gpu":["0","1","2","3","4","5","6","7"],tpu:["0","1","2","3","4"],ipu:["0","1","2","3","4"],atom:["0","1","2","3","4"],warboy:["0","1","2","3","4"]},this.cpuValue=0,this.listCondition="loading",this._boundRequirementsRenderer=this.requirementsRenderer.bind(this),this._boundControlsRenderer=this.controlsRenderer.bind(this),this._boundInstallRenderer=this.installRenderer.bind(this),this._boundBaseImageRenderer=this.baseImageRenderer.bind(this),this._boundConstraintRenderer=this.constraintRenderer.bind(this),this._boundDigestRenderer=this.digestRenderer.bind(this),this.installImageNameList=[],this.deleteImageNameList=[],this.images=[],this.allowed_registries=[],this.servicePorts=[]}static get styles(){return[o,r,n,l,d,c`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 229px);
        }
        h4 {
          font-weight: 200;
          font-size: 14px;
          margin: 0px;
          padding: 5px 15px 5px 20px;
        }
        mwc-icon.indicator {
          --mdc-icon-size: 16px;
          padding: 0;
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
        backend-ai-dialog {
          --component-min-width: 350px;
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
        mwc-button,
        mwc-button[unelevated] {
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
          width: 150px;
          margin: auto 10px;
          --mdc-theme-primary: var(--general-slider-color);
          --mdc-theme-text-primary-on-dark: #ffffff;
        }
      `]}firstUpdated(){var e;this.indicator=globalThis.lablupIndicator,this.notification=globalThis.lablupNotification,this.resourceBroker=globalThis.resourceBroker,void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._getImages()}),!0):this._getImages(),this._grid=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#testgrid"),this._grid.addEventListener("sorter-changed",(e=>{this._refreshSorter(e)})),document.addEventListener("image-rescanned",(()=>{this._getImages()})),this.installImageDialog.addEventListener("didHide",(()=>{this._uncheckSelectedRow()})),this.deleteImageDialog.addEventListener("didHide",(()=>{this._uncheckSelectedRow()}))}_removeRow(){this.deleteAppRow.remove(),this.deleteAppInfoDialog.hide(),this.notification.text=m("environment.AppInfoDeleted"),this.notification.show()}_addRow(){const e=this.modifyAppContainer.children[this.modifyAppContainer.children.length-1],t=this._createRow();this.modifyAppContainer.insertBefore(t,e)}_createRow(){const e=document.createElement("div");e.setAttribute("class","row extra");const t=document.createElement("mwc-textfield");t.setAttribute("type","text");const i=document.createElement("mwc-textfield");t.setAttribute("type","text");const a=document.createElement("mwc-textfield");t.setAttribute("type","number");const s=document.createElement("mwc-icon-button");return s.setAttribute("class","fg pink"),s.setAttribute("icon","remove"),s.addEventListener("click",(e=>this._checkDeleteAppInfo(e))),e.appendChild(a),e.appendChild(i),e.appendChild(t),e.appendChild(s),e}_checkDeleteAppInfo(e){var t;this.deleteAppRow=e.target.parentNode;const i=[...this.deleteAppRow.children].filter((e=>"MWC-TEXTFIELD"===e.tagName)).map((e=>e.value));(null===(t=i.filter((e=>""===e)))||void 0===t?void 0:t.length)===i.length?this._removeRow():(this.deleteAppInfo=i,this.deleteAppInfoDialog.show())}_clearRows(){const e=this.modifyAppContainer.querySelectorAll(".row");e[e.length-1].querySelectorAll("mwc-textfield").forEach((e=>{e.value=""})),this.modifyAppContainer.querySelectorAll(".row.extra").forEach((e=>{e.remove()}))}_uncheckSelectedRow(){this._grid.selectedItems=[]}_refreshSorter(e){const t=e.target,i=t.path.toString();t.direction&&("asc"===t.direction?this._grid.items.sort(((e,t)=>e[i]<t[i]?-1:e[i]>t[i]?1:0)):this._grid.items.sort(((e,t)=>e[i]>t[i]?-1:e[i]<t[i]?1:0)))}async _viewStateChanged(e){await this.updateComplete}_getImages(){var e;this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.domain.get(globalThis.backendaiclient._config.domainName,["allowed_docker_registries"]).then((e=>(this.allowed_registries=e.domain.allowed_docker_registries,globalThis.backendaiclient.image.list(["name","tag","registry","architecture","digest","installed","labels { key value }","resource_limits { key min max }"],!1,!0)))).then((e=>{var t;const i=e.images,a=[];i.forEach((e=>{if("registry"in e&&this.allowed_registries.includes(e.registry)){const t=e.tag.split("-");void 0!==t[1]?(e.baseversion=t[0],e.baseimage=t[1],void 0!==t[2]&&(e.additional_req=this._humanizeName(t.slice(2).join("-")))):void 0!==e.tag?e.baseversion=e.tag:e.baseversion="";const i=e.name.split("/");void 0!==i[1]?(e.namespace=i[0],e.lang=i.slice(1).join("")):(e.namespace="",e.lang=i[0]);const s=e.lang.split("-");let o;o=void 0!==e.baseimage?[this._humanizeName(e.baseimage)]:[],void 0!==s[1]&&("r"===s[0]?(e.lang=s[0],o.push(this._humanizeName(s[0]))):(e.lang=s[1],o.push(this._humanizeName(s[0])))),e.baseimage=o,e.lang=this._humanizeName(e.lang);e.resource_limits.forEach((t=>{0==t.max&&(t.max="∞"),"cuda.device"==t.key&&(t.key="cuda_device"),"cuda.shares"==t.key&&(t.key="cuda_shares"),"rocm.device"==t.key&&(t.key="rocm_device"),"tpu.device"==t.key&&(t.key="tpu_device"),"ipu.device"==t.key&&(t.key="ipu_device"),"atom.device"==t.key&&(t.key="atom_device"),"warboy.device"==t.key&&(t.key="warboy_device"),null!==t.min&&void 0!==t.min&&(e[t.key+"_limit_min"]=this._addUnit(t.min)),null!==t.max&&void 0!==t.max?e[t.key+"_limit_max"]=this._addUnit(t.max):e[t.key+"_limit_max"]=1/0})),e.labels=e.labels.reduce(((e,t)=>({...e,[t.key]:t.value})),{}),a.push(e)}}));const s=a.sort(((e,t)=>t.installed-e.installed));this.images=s,0==this.images.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide()})).catch((e=>{var t;console.log(e),void 0!==e.message?(this.notification.text=u.relieve(e.title),this.notification.detail=e.message):this.notification.text=u.relieve("Problem occurred during image metadata loading."),this.notification.show(!0,e),null===(t=this._listStatus)||void 0===t||t.hide()}))}_addUnit(e){const t=e.substr(-1);return"m"==t?e.slice(0,-1)+"MiB":"g"==t?e.slice(0,-1)+"GiB":"t"==t?e.slice(0,-1)+"TiB":e}_symbolicUnit(e){const t=e.substr(-2);return"MB"==t?e.slice(0,-2)+"m":"GB"==t?e.slice(0,-2)+"g":"TB"==t?e.slice(0,-2)+"t":e}_humanizeName(e){this.alias=this.resourceBroker.imageTagAlias;const t=this.resourceBroker.imageTagReplace;for(const[i,a]of Object.entries(t)){const t=new RegExp(i);if(t.test(e))return e.replace(t,a)}return e in this.alias?this.alias[e]:e}_changeSliderValue(e){var t,i;const a=this._range[e.id].filter(((t,i)=>i===e.value));(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#modify-image-"+e.id)).label=a[0],(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#modify-image-"+e.id)).value=a[0]}_markIfUnlimited(e){return["-",0,"Unlimited",1/0,"Infinity"].includes(e)?"∞":e}_hideDialogById(e){var t;return(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(e)).hide()}_launchDialogById(e){var t;return(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(e)).show()}modifyImage(){const e=this.modifyImageCpu.label,t=this.modifyImageMemory.label,i=this.modifyImageCudaGpu.label,a=this.modifyImageCudaFGpu.label,s=this.modifyImageRocmGpu.label,o=this.modifyImageTpu.label,r=this.modifyImageIpu.label,n=this.modifyImageAtom.label,l=this.modifyImageWarboy.label,{resource_limits:d}=this.images[this.selectedIndex],c={},u=this._cuda_gpu_disabled?this._cuda_fgpu_disabled?1:2:this._cuda_fgpu_disabled?2:3;e!==d[0].min&&(c.cpu={min:e});const p=this._symbolicUnit(t);p!==d[u].min&&(c.mem={min:p}),this._cuda_gpu_disabled||i===d[1].min||(c["cuda.device"]={min:i}),this._cuda_fgpu_disabled||a===d[2].min||(c["cuda.shares"]={min:a}),this._rocm_gpu_disabled||s===d[3].min||(c["rocm.device"]={min:s}),this._tpu_disabled||o===d[4].min||(c["tpu.device"]={min:o}),this._ipu_disabled||r===d[5].min||(c["ipu.device"]={min:r}),this._atom_disabled||n===d[6].min||(c["atom.device"]={min:n}),this._warboy_disabled||l===d[6].min||(c["warboy.device"]={min:l});const h=this.images[this.selectedIndex];if(0===Object.keys(c).length)return this.notification.text=m("environment.NoChangeMade"),this.notification.show(),void this._hideDialogById("#modify-image-dialog");globalThis.backendaiclient.image.modifyResource(h.registry,h.name,h.tag,c).then((e=>{e.reduce(((e,t)=>e&&"ok"===t.result),!0)?(this._getImages(),this.requestUpdate(),this.notification.text=m("environment.SuccessfullyModified")):this.notification.text=m("environment.ProblemOccurred"),this.notification.show(),this._hideDialogById("#modify-image-dialog")}))}openInstallImageDialog(){this.selectedImages=this._grid.selectedItems.filter((e=>!e.installed)),this.installImageNameList=this.selectedImages.map((e=>(Object.keys(e).map((t=>{["registry","name","tag"].includes(t)&&t in e&&(e[t]=e[t].replace(/\s/g,""))})),e.registry+"/"+e.name+":"+e.tag))),this.selectedImages.length>0?this.installImageDialog.show():(this.notification.text=m("environment.SelectedImagesAlreadyInstalled"),this.notification.show())}_installImage(){this.installImageDialog.hide(),this.selectedImages.forEach((async e=>{const t='[id="'+e.registry.replace(/\./gi,"-")+"-"+e.name.replace("/","-")+"-"+e.tag.replace(/\./gi,"-")+'"]';this._grid.querySelector(t).setAttribute("style","display:block;");const i=e.registry+"/"+e.name+":"+e.tag;let a=!1;const s=Object();"resource_limits"in e&&e.resource_limits.forEach((e=>{s[e.key.replace("_",".")]=e.min})),"cuda.device"in s&&"cuda.shares"in s?(a=!0,s.gpu=0,s.fgpu=s["cuda.shares"]):"cuda.device"in s?(s.gpu=s["cuda.device"],a=!0):a=!1,s.mem.endsWith("g")?s.mem=s.mem.replace("g",".5g"):s.mem.endsWith("m")&&(s.mem=Number(s.mem.slice(0,-1))+256+"m"),s.domain=globalThis.backendaiclient._config.domainName,s.group_name=globalThis.backendaiclient.current_group;const o=await globalThis.backendaiclient.get_resource_slots();a&&("cuda.device"in o||"cuda.shares"in o||(delete s.gpu,delete s.fgpu,delete s["cuda.shares"],delete s["cuda.device"])),"cuda.device"in o&&"cuda.shares"in o?"fgpu"in s&&"gpu"in s&&(delete s.gpu,delete s["cuda.device"]):"cuda.device"in o?(delete s.fgpu,delete s["cuda.shares"]):"cuda.shares"in o&&(delete s.gpu,delete s["cuda.device"]),s.enqueueOnly=!0,s.type="batch",s.startupCommand='echo "Image is installed"',this.notification.text=m("environment.InstallingImage")+i+m("environment.TakesTime"),this.notification.show();const r=await this.indicator.start("indeterminate");r.set(10,m("import.Downloading")),globalThis.backendaiclient.image.install(i,e.architecture,s).then((()=>{r.end(1e3)})).catch((e=>{this._grid.querySelector(t).className=m("environment.Installing"),this._grid.querySelector(t).setAttribute("style","display:none;"),this._uncheckSelectedRow(),this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e),r.set(100,p("environment.DescProblemOccurred")),r.end(1e3)}))}))}openDeleteImageDialog(){this.selectedImages=this._grid.selectedItems.filter((e=>e.installed)),this.deleteImageNameList=this.selectedImages.map((e=>e.registry+"/"+e.name+":"+e.tag)),this.selectedImages.length>0?this.deleteImageDialog.show():(this.notification.text=m("environment.SelectedImagesNotInstalled"),this.notification.show())}_deleteImage(){}_setPulldownDefaults(e){var t,i,a,s,o,r,n,l,d,c,m,u,h,g,v,y;this._cuda_gpu_disabled=0===e.filter((e=>"cuda_device"===e.key)).length,this._cuda_fgpu_disabled=0===e.filter((e=>"cuda_shares"===e.key)).length,this._rocm_gpu_disabled=0===e.filter((e=>"rocm_device"===e.key)).length,this._tpu_disabled=0===e.filter((e=>"tpu_device"===e.key)).length,this._ipu_disabled=0===e.filter((e=>"ipu_device"===e.key)).length,this._atom_disabled=0===e.filter((e=>"atom_device"===e.key)).length,this._warboy_disabled=0===e.filter((e=>"warboy_device"===e.key)).length;const b=e.reduce(((e,t)=>{const{key:i,...a}=t,s=a;return e[t.key]=s,e}),{});this.modifyImageCpu.label=b.cpu.min,this._cuda_gpu_disabled?(this.modifyImageCudaGpu.label=p("environment.Disabled"),(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("mwc-slider#cuda-gpu")).value=0):(this.modifyImageCudaGpu.label=b.cuda_device.min,(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("mwc-slider#cuda-gpu")).value=this._range["cuda-gpu"].indexOf(this._range["cuda-gpu"].filter((e=>e===b.cuda_device.min))[0])),this._cuda_fgpu_disabled?(this.modifyImageCudaFGpu.label=p("environment.Disabled"),(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("mwc-slider#cuda-gpu")).value=0):(this.modifyImageCudaFGpu.label=b.cuda_shares.min,(null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("mwc-slider#cuda-fgpu")).value=this._range["cuda-fgpu"].indexOf(this._range["cuda-fgpu"].filter((e=>e===b.cuda_shares.min))[0])),this._rocm_gpu_disabled?(this.modifyImageRocmGpu.label=p("environment.Disabled"),(null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("mwc-slider#rocm-gpu")).value=0):(this.modifyImageRocmGpu.label=b.rocm_device.min,(null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("mwc-slider#rocm-gpu")).value=this._range["rocm-gpu"].indexOf(this._range["rocm-gpu"].filter((e=>e===b.rocm_device.min))[0])),this._tpu_disabled?(this.modifyImageTpu.label=p("environment.Disabled"),(null===(l=this.shadowRoot)||void 0===l?void 0:l.querySelector("mwc-slider#tpu")).value=0):(this.modifyImageTpu.label=b.tpu_device.min,(null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("mwc-slider#tpu")).value=this._range.tpu.indexOf(this._range.tpu.filter((e=>e===b.tpu_device.min))[0])),this._ipu_disabled?(this.modifyImageTpu.label=p("environment.Disabled"),(null===(c=this.shadowRoot)||void 0===c?void 0:c.querySelector("mwc-slider#ipu")).value=0):(this.modifyImageIpu.label=b.ipu_device.min,(null===(d=this.shadowRoot)||void 0===d?void 0:d.querySelector("mwc-slider#ipu")).value=this._range.ipu.indexOf(this._range.ipu.filter((e=>e===b.ipu_device.min))[0])),this._atom_disabled?(this.modifyImageAtom.label=p("environment.Disabled"),(null===(u=this.shadowRoot)||void 0===u?void 0:u.querySelector("mwc-slider#atom")).value=0):(this.modifyImageAtom.label=b.atom_device.min,(null===(m=this.shadowRoot)||void 0===m?void 0:m.querySelector("mwc-slider#atom")).value=this._range.atom.indexOf(this._range.atom.filter((e=>e===b.atom_device.min))[0])),this._warboy_disabled?(this.modifyImageWarboy.label=p("environment.Disabled"),(null===(g=this.shadowRoot)||void 0===g?void 0:g.querySelector("mwc-slider#warboy")).value=0):(this.modifyImageWarboy.label=b.warboy_device.min,(null===(h=this.shadowRoot)||void 0===h?void 0:h.querySelector("mwc-slider#warboy")).value=this._range.warboy.indexOf(this._range.warboy.filter((e=>e===b.warboy_device.min))[0])),this.modifyImageMemory.label=this._addUnit(b.mem.min),(null===(v=this.shadowRoot)||void 0===v?void 0:v.querySelector("mwc-slider#cpu")).value=this._range.cpu.indexOf(this._range.cpu.filter((e=>e===b.cpu.min))[0]),(null===(y=this.shadowRoot)||void 0===y?void 0:y.querySelector("mwc-slider#mem")).value=this._range.mem.indexOf(this._range.mem.filter((e=>e===this._addUnit(b.mem.min)))[0]),this._updateSliderLayout()}_updateSliderLayout(){var e;null===(e=this.shadowRoot)||void 0===e||e.querySelectorAll("mwc-slider").forEach((e=>{e.layout()}))}_decodeServicePort(){""===this.images[this.selectedIndex].labels["ai.backend.service-ports"]?this.servicePorts=[]:this.servicePorts=this.images[this.selectedIndex].labels["ai.backend.service-ports"].split(",").map((e=>{const t=e.split(":");return{app:t[0],protocol:t[1],port:t[2]}}))}_isServicePortValid(){var e;const t=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#modify-app-container")).querySelectorAll(".row:not(.header)"),i=new Set;for(const e of Array.from(t)){const t=e.querySelectorAll("mwc-textfield");if(Array.prototype.every.call(t,(e=>""===e.value)))continue;const a=t[0].value,s=t[1].value,o=parseInt(t[2].value);if(""===a)return this.servicePortsMsg=m("environment.AppNameMustNotBeEmpty"),!1;if(!["http","tcp","pty","preopen"].includes(s))return this.servicePortsMsg=m("environment.ProtocolMustBeOneOfSupported"),!1;if(i.has(o))return this.servicePortsMsg=m("environment.PortMustBeUnique"),!1;if(o>=66535||o<0)return this.servicePortsMsg=m("environment.PortMustBeInRange"),!1;if([2e3,2001,2002,2003,2200,7681].includes(o))return this.servicePortsMsg=m("environment.PortReservedForInternalUse"),!1;i.add(o)}return!0}_parseServicePort(){var e;const t=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#modify-app-container")).querySelectorAll(".row:not(.header)");return Array.prototype.filter.call(t,(e=>(e=>0===Array.prototype.filter.call(e.querySelectorAll("mwc-textfield"),((e,t)=>""===e.value)).length)(e))).map((e=>(e=>Array.prototype.map.call(e.querySelectorAll("mwc-textfield"),(e=>e.value)).join(":"))(e))).join(",")}modifyServicePort(){if(this._isServicePortValid()){const e=this._parseServicePort(),t=this.images[this.selectedIndex];this.servicePortsMsg="",globalThis.backendaiclient.image.modifyLabel(t.registry,t.name,t.tag,"ai.backend.service-ports",e).then((({result:e})=>{this.notification.text=m("ok"===e?"environment.DescServicePortModified":"dialog.ErrorOccurred"),this._getImages(),this.requestUpdate(),this._clearRows(),this.notification.show(),this._hideDialogById("#modify-app-dialog")}))}}requirementsRenderer(e,t,i){h(g`
        <div class="layout horizontal center flex">
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green indicator">developer_board</mwc-icon>
            <span>${i.item.cpu_limit_min}</span>
            ~
            <span>${this._markIfUnlimited(i.item.cpu_limit_max)}</span>
            <span class="indicator">${p("general.cores")}</span>
          </div>
        </div>
        <div class="layout horizontal center flex">
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green indicator">memory</mwc-icon>
            <span>${i.item.mem_limit_min}</span>
            ~
            <span>${this._markIfUnlimited(i.item.mem_limit_max)}</span>
          </div>
        </div>
        ${i.item.cuda_device_limit_min?g`
              <div class="layout horizontal center flex">
                <div class="layout horizontal configuration">
                  <img
                    class="indicator-icon fg green"
                    src="/resources/icons/file_type_cuda.svg"
                  />
                  <span>${i.item.cuda_device_limit_min}</span>
                  ~
                  <span>
                    ${this._markIfUnlimited(i.item.cuda_device_limit_max)}
                  </span>
                  <span class="indicator">CUDA GPU</span>
                </div>
              </div>
            `:g``}
        ${i.item.cuda_shares_limit_min?g`
              <div class="layout horizontal center flex">
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green indicator">apps</mwc-icon>
                  <span>${i.item.cuda_shares_limit_min}</span>
                  ~
                  <span>
                    ${this._markIfUnlimited(i.item.cuda_shares_limit_max)}
                  </span>
                  <span class="indicator">CUDA FGPU</span>
                </div>
              </div>
            `:g``}
        ${i.item.rocm_device_limit_min?g`
              <div class="layout horizontal center flex">
                <div class="layout horizontal configuration">
                  <img
                    class="indicator-icon fg green"
                    src="/resources/icons/ROCm.png"
                  />
                  <span>${i.item.rocm_device_limit_min}</span>
                  ~
                  <span>
                    ${this._markIfUnlimited(i.item.rocm_device_limit_max)}
                  </span>
                  <span class="indicator">ROCm GPU</span>
                </div>
              </div>
            `:g``}
        ${i.item.tpu_device_limit_min?g`
              <div class="layout horizontal center flex">
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green indicator">apps</mwc-icon>
                  <span>${i.item.tpu_device_limit_min}</span>
                  ~
                  <span>
                    ${this._markIfUnlimited(i.item.tpu_device_limit_max)}
                  </span>
                  <span class="indicator">TPU</span>
                </div>
              </div>
            `:g``}
        ${i.item.ipu_device_limit_min?g`
              <div class="layout horizontal center flex">
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green indicator">apps</mwc-icon>
                  <span>${i.item.ipu_device_limit_min}</span>
                  ~
                  <span>
                    ${this._markIfUnlimited(i.item.ipu_device_limit_max)}
                  </span>
                  <span class="indicator">IPU</span>
                </div>
              </div>
            `:g``}
        ${i.item.atom_device_limit_min?g`
              <div class="layout horizontal center flex">
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green indicator">apps</mwc-icon>
                  <span>${i.item.atom_device_limit_min}</span>
                  ~
                  <span>
                    ${this._markIfUnlimited(i.item.atom_device_limit_max)}
                  </span>
                  <span class="indicator">ATOM</span>
                </div>
              </div>
            `:g``}
        ${i.item.warboy_device_limit_min?g`
              <div class="layout horizontal center flex">
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green indicator">apps</mwc-icon>
                  <span>${i.item.warboy_device_limit_min}</span>
                  ~
                  <span>
                    ${this._markIfUnlimited(i.item.warboy_device_limit_max)}
                  </span>
                  <span class="indicator">Warboy</span>
                </div>
              </div>
            `:g``}
      `,e)}controlsRenderer(e,t,i){h(g`
        <div id="controls" class="layout horizontal flex center">
          <mwc-icon-button
            class="fg controls-running blue"
            icon="settings"
            @click=${()=>{this.selectedIndex=i.index,this._setPulldownDefaults(this.images[this.selectedIndex].resource_limits),this._launchDialogById("#modify-image-dialog"),this.requestUpdate()}}
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg controls-running pink"
            icon="apps"
            @click=${()=>{this.selectedIndex!==i.index&&this._clearRows(),this.selectedIndex=i.index,this._decodeServicePort(),this._launchDialogById("#modify-app-dialog"),this.requestUpdate()}}
          ></mwc-icon-button>
        </div>
      `,e)}installRenderer(e,t,i){h(g`
        <div class="layout horizontal center center-justified">
          ${i.item.installed?g`
                <lablup-shields
                  class="installed"
                  description="${p("environment.Installed")}"
                  color="darkgreen"
                  id="${i.item.registry.replace(/\./gi,"-")+"-"+i.item.name.replace("/","-")+"-"+i.item.tag.replace(/\./gi,"-")}"
                ></lablup-shields>
              `:g`
                <lablup-shields
                  class="installing"
                  description="${p("environment.Installing")}"
                  color="green"
                  id="${i.item.registry.replace(/\./gi,"-")+"-"+i.item.name.replace("/","-")+"-"+i.item.tag.replace(/\./gi,"-")}"
                  style="display:none"
                ></lablup-shields>
              `}
        </div>
      `,e)}baseImageRenderer(e,t,i){h(g`
        ${i.item.baseimage.map((e=>g`
            <lablup-shields
              app=""
              color="blue"
              ui="round"
              description="${e}"
            ></lablup-shields>
          `))}
      `,e)}constraintRenderer(e,t,i){h(g`
        ${i.item.additional_req?g`
              <lablup-shields
                app=""
                color="green"
                ui="round"
                description="${i.item.additional_req}"
              ></lablup-shields>
            `:g``}
      `,e)}digestRenderer(e,t,i){h(g`
        <div class="layout vertical">
          <span class="indicator monospace">${i.item.digest}</span>
        </div>
      `,e)}render(){return g`
      <h4 class="horizontal flex center center-justified layout">
        <span>${p("environment.Images")}</span>
        <span class="flex"></span>
        <mwc-button
          raised
          label="${p("environment.Install")}"
          class="operation"
          id="install-image"
          icon="get_app"
          @click="${this.openInstallImageDialog}"
        ></mwc-button>
        <mwc-button
          disabled
          label="${p("environment.Delete")}"
          class="operation temporarily-hide"
          id="delete-image"
          icon="delete"
          @click="${this.openDeleteImageDialog}"
        ></mwc-button>
      </h4>
      <div class="list-wrapper">
        <vaadin-grid
          theme="row-stripes column-borders compact"
          aria-label="Environments"
          id="testgrid"
          .items="${this.images}"
        >
          <vaadin-grid-selection-column
            frozen
            flex-grow="0"
            text-align="center"
            auto-select
          ></vaadin-grid-selection-column>
          <vaadin-grid-sort-column
            path="installed"
            flex-grow="0"
            header="${p("environment.Status")}"
            .renderer="${this._boundInstallRenderer}"
          ></vaadin-grid-sort-column>
          <lablup-grid-sort-filter-column
            path="registry"
            width="80px"
            resizable
            header="${p("environment.Registry")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="architecture"
            width="80px"
            resizable
            header="${p("environment.Architecture")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="namespace"
            width="60px"
            resizable
            header="${p("environment.Namespace")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="lang"
            resizable
            header="${p("environment.Language")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="baseversion"
            resizable
            header="${p("environment.Version")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="baseimage"
            resizable
            width="110px"
            header="${p("environment.Base")}"
            .renderer="${this._boundBaseImageRenderer}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="additional_req"
            width="50px"
            resizable
            header="${p("environment.Constraint")}"
            .renderer="${this._boundConstraintRenderer}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="digest"
            resizable
            header="${p("environment.Digest")}"
            .renderer="${this._boundDigestRenderer}"
          ></lablup-grid-sort-filter-column>
          <vaadin-grid-column
            width="150px"
            flex-grow="0"
            resizable
            header="${p("environment.ResourceLimit")}"
            .renderer="${this._boundRequirementsRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            frozen-to-end
            width="110px"
            resizable
            header="${p("general.Control")}"
            .renderer=${this._boundControlsRenderer}
          ></vaadin-grid-column>
        </vaadin-grid>
        <backend-ai-list-status
          id="list-status"
          statusCondition="${this.listCondition}"
          message="${m("environment.NoImageToDisplay")}"
        ></backend-ai-list-status>
      </div>
      <backend-ai-dialog id="modify-image-dialog" fixed backdrop blockscrolling>
        <span slot="title">${p("environment.ModifyImageResourceLimit")}</span>
        <div slot="content">
          <div class="vertical layout flex">
            <div class="horizontal layout flex center">
              <span class="resource-limit-title">CPU</span>
              <mwc-slider
                id="cpu"
                step="1"
                markers
                max="8"
                @change="${e=>this._changeSliderValue(e.target)}"
              ></mwc-slider>
              <mwc-button
                class="range-value"
                id="modify-image-cpu"
                disabled
              ></mwc-button>
            </div>
            <div class="horizontal layout flex center">
              <span class="resource-limit-title">MEM</span>
              <mwc-slider
                id="mem"
                markers
                step="1"
                max="12"
                @change="${e=>this._changeSliderValue(e.target)}"
              ></mwc-slider>
              <mwc-button
                class="range-value"
                id="modify-image-mem"
                disabled
              ></mwc-button>
            </div>
            <div class="horizontal layout flex center">
              <span class="resource-limit-title">CUDA GPU</span>
              <mwc-slider
                ?disabled="${this._cuda_gpu_disabled}"
                id="cuda-gpu"
                markers
                step="1"
                max="8"
                @change="${e=>this._changeSliderValue(e.target)}"
              ></mwc-slider>
              <mwc-button
                class="range-value"
                id="modify-image-cuda-gpu"
                disabled
              ></mwc-button>
            </div>
            <div class="horizontal layout flex center">
              <span class="resource-limit-title">CUDA FGPU</span>
              <mwc-slider
                ?disabled="${this._cuda_fgpu_disabled}"
                id="cuda-fgpu"
                markers
                step="1"
                max="8"
                @change="${e=>this._changeSliderValue(e.target)}"
              ></mwc-slider>
              <mwc-button
                class="range-value"
                id="modify-image-cuda-fgpu"
                disabled
              ></mwc-button>
            </div>
            <div class="horizontal layout flex center">
              <span class="resource-limit-title">ROCm GPU</span>
              <mwc-slider
                ?disabled="${this._rocm_gpu_disabled}"
                id="rocm-gpu"
                markers
                step="1"
                max="8"
                @change="${e=>this._changeSliderValue(e.target)}"
              ></mwc-slider>
              <mwc-button
                class="range-value"
                id="modify-image-rocm-gpu"
                disabled
              ></mwc-button>
            </div>
            <div class="horizontal layout flex center">
              <span class="resource-limit-title">TPU</span>
              <mwc-slider
                ?disabled="${this._tpu_disabled}"
                id="tpu"
                markers
                step="1"
                max="5"
                @change="${e=>this._changeSliderValue(e.target)}"
              ></mwc-slider>
              <mwc-button
                class="range-value"
                id="modify-image-tpu"
                disabled
              ></mwc-button>
            </div>
            <div class="horizontal layout flex center">
              <span class="resource-limit-title">IPU</span>
              <mwc-slider
                ?disabled="${this._ipu_disabled}"
                id="ipu"
                markers
                step="1"
                max="5"
                @change="${e=>this._changeSliderValue(e.target)}"
              ></mwc-slider>
              <mwc-button
                class="range-value"
                id="modify-image-ipu"
                disabled
              ></mwc-button>
            </div>
            <div class="horizontal layout flex center">
              <span class="resource-limit-title">ATOM</span>
              <mwc-slider
                ?disabled="${this._atom_disabled}"
                id="atom"
                markers
                step="1"
                max="5"
                @change="${e=>this._changeSliderValue(e.target)}"
              ></mwc-slider>
              <mwc-button
                class="range-value"
                id="modify-image-atom"
                disabled
              ></mwc-button>
            </div>
            <div class="horizontal layout flex center">
              <span class="resource-limit-title">Warboy</span>
              <mwc-slider
                ?disabled="${this._warboy_disabled}"
                id="warboy"
                markers
                step="1"
                max="5"
                @change="${e=>this._changeSliderValue(e.target)}"
              ></mwc-slider>
              <mwc-button
                class="range-value"
                id="modify-image-warboy"
                disabled
              ></mwc-button>
            </div>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            icon="check"
            label="${p("button.SaveChanges")}"
            @click="${()=>this.modifyImage()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="modify-app-dialog" fixed backdrop>
        <span slot="title">${p("environment.ManageApps")}</span>
        <div slot="content" id="modify-app-container">
          <div class="row header">
            <div>${p("environment.AppName")}</div>
            <div>${p("environment.Protocol")}</div>
            <div>${p("environment.Port")}</div>
            <div>${p("environment.Action")}</div>
          </div>
          ${this.servicePorts.map(((e,t)=>g`
              <div class="row">
                <mwc-textfield type="text" value=${e.app}></mwc-textfield>
                <mwc-textfield
                  type="text"
                  value=${e.protocol}
                ></mwc-textfield>
                <mwc-textfield type="number" value=${e.port}></mwc-textfield>
                <mwc-icon-button
                  class="fg pink"
                  icon="remove"
                  @click=${e=>this._checkDeleteAppInfo(e)}
                ></mwc-icon-button>
              </div>
            `))}
          <div class="row">
            <mwc-textfield type="text"></mwc-textfield>
            <mwc-textfield type="text"></mwc-textfield>
            <mwc-textfield type="number"></mwc-textfield>
            <mwc-icon-button
              class="fg pink"
              icon="add"
              @click=${()=>this._addRow()}
            ></mwc-icon-button>
          </div>
          <span style="color:red;">${this.servicePortsMsg}</span>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            slot="footer"
            icon="check"
            label="${p("button.Finish")}"
            @click="${this.modifyServicePort}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="install-image-dialog" fixed backdrop persistent>
        <span slot="title">${p("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${p("environment.DescDownloadImage")}</p>
          <p style="margin:auto; ">
            <span style="color:blue;">
              ${this.installImageNameList.map((e=>g`
                  ${e}
                  <br />
                `))}
            </span>
          </p>
          <p>
            ${p("environment.DescSignificantDownloadTime")}
            ${p("dialog.ask.DoYouWantToProceed")}
          </p>
        </div>
        <div slot="footer" class="horizontal flex layout">
          <div class="flex"></div>
          <mwc-button
            class="operation"
            label="${p("button.Cancel")}"
            @click="${e=>{this._hideDialog(e),this._uncheckSelectedRow()}}"
          ></mwc-button>
          <mwc-button
            unelevated
            class="operation"
            label="${p("button.Okay")}"
            @click="${()=>this._installImage()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-image-dialog" fixed backdrop persistent>
        <span slot="title">${p("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${p("environment.DescDeleteImage")}</p>
          <p style="margin:auto; ">
            <span style="color:blue;">
              ${this.deleteImageNameList.map((e=>g`
                  ${e}
                  <br />
                `))}
            </span>
          </p>
          <p>${p("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal flex layout">
          <div class="flex"></div>
          <mwc-button
            class="operation"
            label="${p("button.Cancel")}"
            @click="${e=>{this._hideDialog(e),this._uncheckSelectedRow()}}"
          ></mwc-button>
          <mwc-button
            unelevated
            class="operation"
            label="${p("button.Okay")}"
            @click="${()=>this._deleteImage()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-app-info-dialog" fixed backdrop persistent>
        <span slot="title">${p("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${p("environment.DescDeleteAppInfo")}</p>
          <div class="horizontal layout">
            <p>${p("environment.AppName")}</p>
            <p style="color:blue;">: ${this.deleteAppInfo[0]}</p>
          </div>
          <div class="horizontal layout">
            <p>${p("environment.Protocol")}</p>
            <p style="color:blue;">: ${this.deleteAppInfo[1]}</p>
          </div>
          <div class="horizontal layout">
            <p>${p("environment.Port")}</p>
            <p style="color:blue;">: ${this.deleteAppInfo[2]}</p>
          </div>
          <p>${p("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal flex layout">
          <div class="flex"></div>
          <mwc-button
            class="operation"
            label="${p("button.Cancel")}"
            @click="${e=>this._hideDialog(e)}"
          ></mwc-button>
          <mwc-button
            unelevated
            class="operation"
            label="${p("button.Okay")}"
            @click="${()=>this._removeRow()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};var y;e([t({type:Array})],v.prototype,"images",void 0),e([t({type:Object})],v.prototype,"resourceBroker",void 0),e([t({type:Array})],v.prototype,"allowed_registries",void 0),e([t({type:Array})],v.prototype,"servicePorts",void 0),e([t({type:Number})],v.prototype,"selectedIndex",void 0),e([t({type:Array})],v.prototype,"selectedImages",void 0),e([t({type:Boolean})],v.prototype,"_cuda_gpu_disabled",void 0),e([t({type:Boolean})],v.prototype,"_cuda_fgpu_disabled",void 0),e([t({type:Boolean})],v.prototype,"_rocm_gpu_disabled",void 0),e([t({type:Boolean})],v.prototype,"_tpu_disabled",void 0),e([t({type:Boolean})],v.prototype,"_ipu_disabled",void 0),e([t({type:Boolean})],v.prototype,"_atom_disabled",void 0),e([t({type:Boolean})],v.prototype,"_warboy_disabled",void 0),e([t({type:Object})],v.prototype,"alias",void 0),e([t({type:Object})],v.prototype,"indicator",void 0),e([t({type:Array})],v.prototype,"installImageNameList",void 0),e([t({type:Array})],v.prototype,"deleteImageNameList",void 0),e([t({type:Object})],v.prototype,"deleteAppInfo",void 0),e([t({type:Object})],v.prototype,"deleteAppRow",void 0),e([t({type:Object})],v.prototype,"installImageResource",void 0),e([t({type:Object})],v.prototype,"selectedCheckbox",void 0),e([t({type:Object})],v.prototype,"_grid",void 0),e([t({type:String})],v.prototype,"servicePortsMsg",void 0),e([t({type:Object})],v.prototype,"_range",void 0),e([t({type:Number})],v.prototype,"cpuValue",void 0),e([t({type:String})],v.prototype,"listCondition",void 0),e([t({type:Object})],v.prototype,"_boundRequirementsRenderer",void 0),e([t({type:Object})],v.prototype,"_boundControlsRenderer",void 0),e([t({type:Object})],v.prototype,"_boundInstallRenderer",void 0),e([t({type:Object})],v.prototype,"_boundBaseImageRenderer",void 0),e([t({type:Object})],v.prototype,"_boundConstraintRenderer",void 0),e([t({type:Object})],v.prototype,"_boundDigestRenderer",void 0),e([i("#loading-spinner")],v.prototype,"spinner",void 0),e([i("#modify-image-cpu")],v.prototype,"modifyImageCpu",void 0),e([i("#modify-image-mem")],v.prototype,"modifyImageMemory",void 0),e([i("#modify-image-cuda-gpu")],v.prototype,"modifyImageCudaGpu",void 0),e([i("#modify-image-cuda-fgpu")],v.prototype,"modifyImageCudaFGpu",void 0),e([i("#modify-image-rocm-gpu")],v.prototype,"modifyImageRocmGpu",void 0),e([i("#modify-image-tpu")],v.prototype,"modifyImageTpu",void 0),e([i("#modify-image-ipu")],v.prototype,"modifyImageIpu",void 0),e([i("#modify-image-atom")],v.prototype,"modifyImageAtom",void 0),e([i("#modify-image-warboy")],v.prototype,"modifyImageWarboy",void 0),e([i("#delete-app-info-dialog")],v.prototype,"deleteAppInfoDialog",void 0),e([i("#delete-image-dialog")],v.prototype,"deleteImageDialog",void 0),e([i("#install-image-dialog")],v.prototype,"installImageDialog",void 0),e([i("#modify-app-container")],v.prototype,"modifyAppContainer",void 0),e([i("#list-status")],v.prototype,"_listStatus",void 0),v=e([a("backend-ai-environment-list")],v);let b=y=class extends s{constructor(){super(),this._listCondition="loading",this._editMode=!1,this._registryType="docker",this._selectedIndex=-1,this._boundIsEnabledRenderer=this._isEnabledRenderer.bind(this),this._boundControlsRenderer=this._controlsRenderer.bind(this),this._boundPasswordRenderer=this._passwordRenderer.bind(this),this._allowed_registries=[],this._editMode=!1,this._hostnames=[],this._registryList=[]}static get styles(){return[o,r,n,c`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 229px);
        }

        h4 {
          font-weight: 200;
          font-size: 14px;
          margin: 0px;
          padding: 5px 15px 5px 20px;
        }

        backend-ai-dialog {
          --component-min-width: 350px;
        }
        mwc-textfield.hostname {
          width: 100%;
        }
        mwc-textfield.helper-text {
          margin-bottom: 0;
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

        mwc-button,
        mwc-button[unelevated] {
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
          --mdc-typography-font-family: var(--general-font-family);
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification,this._indicator=globalThis.lablupIndicator,this._projectNameInput.validityTransform=(e,t)=>this._checkValidationMsgOnProjectNameInput(e,t)}_parseRegistryList(e){return Object.keys(e).map((t=>{return"string"==typeof(i=e[t])||i instanceof String?{"":e[t],hostname:t}:{...e[t],hostname:t};var i}))}_refreshRegistryList(){var e;this._listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.domain.get(globalThis.backendaiclient._config.domainName,["allowed_docker_registries"]).then((e=>(this._allowed_registries=e.domain.allowed_docker_registries,globalThis.backendaiclient.registry.list()))).then((({result:e})=>{var t;this._registryList=this._parseRegistryList(e),0==this._registryList.length?this._listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide(),this._hostnames=this._registryList.map((e=>e.hostname)),this.requestUpdate()}))}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._refreshRegistryList()}),!0):this._refreshRegistryList())}_addRegistry(){const e=this._hostnameInput.value,t=this._urlInput.value,i=this._usernameInput.value,a=this._passwordInput.value,s=this._selectedRegistryTypeInput.value,o=this._projectNameInput.value.replace(/\s/g,"");if(!this._hostnameInput.validity.valid)return;if(!this._urlInput.validity.valid)return;const r={};if(r[""]=t,""!==i&&""!==a&&(r.username=i,r.password=a),r.type=s,["harbor","harbor2"].includes(s)){if(!o||""===o)return;r.project=o}else r.project="";if(!this._editMode&&this._hostnames.includes(e))return this.notification.text=m("registry.RegistryHostnameAlreadyExists"),void this.notification.show();globalThis.backendaiclient.registry.set(e,r).then((({result:t})=>{"ok"===t?(this._editMode?this.notification.text=m("registry.RegistrySuccessfullyModified"):(this.notification.text=m("registry.RegistrySuccessfullyAdded"),this._hostnames.push(e),this._resetRegistryField()),this._refreshRegistryList()):this.notification.text=m("dialog.ErrorOccurred"),this._hideDialogById("#configure-registry-dialog"),this.notification.show()}))}_deleteRegistry(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#delete-registry"),i=t.value;this._registryList[this._selectedIndex].hostname===i?globalThis.backendaiclient.registry.delete(t.value).then((({result:e})=>{"ok"===e?(this.notification.text=m("registry.RegistrySuccessfullyDeleted"),this._hostnames.includes(i)&&this._hostnames.splice(this._hostnames.indexOf(i)),this._refreshRegistryList()):this.notification.text=m("dialog.ErrorOccurred"),this._hideDialogById("#delete-registry-dialog"),this.notification.show()})):(this.notification.text=m("registry.HostnameDoesNotMatch"),this.notification.show()),t.value=""}async _rescanImage(){const e=await this._indicator.start("indeterminate");e.set(10,m("registry.UpdatingRegistryInfo")),globalThis.backendaiclient.maintenance.rescan_images(this._registryList[this._selectedIndex].hostname).then((({rescan_images:t})=>{if(t.ok){e.set(0,m("registry.RescanImages"));const i=globalThis.backendaiclient.maintenance.attach_background_task(t.task_id);i.addEventListener("bgtask_updated",(t=>{const i=JSON.parse(t.data),a=i.current_progress/i.total_progress;e.set(100*a,m("registry.RescanImages"))})),i.addEventListener("bgtask_done",(()=>{const t=new CustomEvent("image-rescanned");document.dispatchEvent(t),e.set(100,m("registry.RegistryUpdateFinished")),i.close()})),i.addEventListener("bgtask_failed",(e=>{throw console.log("bgtask_failed",e.data),i.close(),new Error("Background Image scanning task has failed")})),i.addEventListener("bgtask_cancelled",(()=>{throw i.close(),new Error("Background Image scanning task has been cancelled")}))}else e.set(50,m("registry.RegistryUpdateFailed")),e.end(1e3),this.notification.text=u.relieve(t.msg),this.notification.detail=t.msg,this.notification.show()})).catch((t=>{console.log(t),e.set(50,m("registry.RescanFailed")),e.end(1e3),t&&t.message&&(this.notification.text=u.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))}))}_launchDialogById(e){var t;null===(t=this.shadowRoot)||void 0===t||t.querySelector(e).show()}_hideDialogById(e){var t;null===(t=this.shadowRoot)||void 0===t||t.querySelector(e).hide()}_openCreateRegistryDialog(){this._editMode=!1,this._selectedIndex=-1,this._registryType="docker",this.requestUpdate(),this._launchDialogById("#configure-registry-dialog")}_openEditRegistryDialog(e){var t;let i;this._editMode=!0;for(let t=0;t<this._registryList.length;t++)if(this._registryList[t].hostname===e){i=this._registryList[t];break}i?(this._registryList[this._selectedIndex]=i,this._registryType=null===(t=this._registryList[this._selectedIndex])||void 0===t?void 0:t.type,this.requestUpdate(),this._launchDialogById("#configure-registry-dialog")):globalThis.notification.show(`No such registry hostname: ${e}`)}_checkValidationMsgOnRegistryUrlInput(e){try{const t=new URL(this._urlInput.value);"http:"===t.protocol||"https:"===t.protocol?e.target.setCustomValidity(""):e.target.setCustomValidity(p("registry.DescURLStartString"))}catch(t){e.target.setCustomValidity(p("import.WrongURLType"))}}_checkValidationMsgOnProjectNameInput(e,t){return this._projectNameInput.value=this._projectNameInput.value.replace(/\s/g,""),["harbor","harbor2"].includes(this._registryType)?(this._projectNameInput.value||(this._projectNameInput.validationMessage=m("registry.ProjectNameIsRequired")),this._projectNameInput.disabled=!1):(this._projectNameInput.validationMessage=m("registry.ForHarborOnly"),this._projectNameInput.disabled=!0),{}}_toggleRegistryEnabled(e,t){e.target.selected?this._changeRegistryState(t,!0):this._changeRegistryState(t,!1)}_toggleProjectNameInput(){this._registryType=this._selectedRegistryTypeInput.value,this._checkValidationMsgOnProjectNameInput(!0,!0)}_resetRegistryField(){this._hostnameInput.value="",this._urlInput.value="",this._usernameInput.value="",this._passwordInput.value="",this._selectedRegistryTypeInput.value="",this._projectNameInput.value="",this.requestUpdate()}_changeRegistryState(e,t){if(!0===t)this._allowed_registries.push(e),this.notification.text=m("registry.RegistryTurnedOn");else{const t=this._allowed_registries.indexOf(e);1!==t&&this._allowed_registries.splice(t,1),this.notification.text=m("registry.RegistryTurnedOff")}globalThis.backendaiclient.domain.update(globalThis.backendaiclient._config.domainName,{allowed_docker_registries:this._allowed_registries}).then((e=>{this.notification.show()}))}_indexRenderer(e,t,i){const a=i.index+1;h(g`
        <div>${a}</div>
      `,e)}_hostNameRenderer(e,t,i){h(g`
        <div>${decodeURIComponent(i.item.hostname)}</div>
      `,e)}_registryUrlRenderer(e,t,i){h(g`
        <div>${i.item[""]}</div>
      `,e)}_passwordRenderer(e,t,i){h(g`
        <div>
          <input
            type="password"
            id="registry-password"
            readonly
            value="${i.item.password}"
          />
        </div>
      `,e)}_isEnabledRenderer(e,t,i){h(g`
        <div>
          <mwc-switch
            @click="${e=>this._toggleRegistryEnabled(e,i.item.hostname)}"
            ?selected="${this._allowed_registries.includes(i.item.hostname)}"
          ></mwc-switch>
        </div>
      `,e)}_controlsRenderer(e,t,i){h(g`
        <div
          icon="settings"
          id="controls"
          class="layout horizontal flex center"
        >
          <mwc-icon-button
            class="fg blue"
            icon="settings"
            @click=${()=>{this._selectedIndex=i.index,this._openEditRegistryDialog(i.item.hostname)}}
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg red"
            icon="delete"
            @click=${()=>{this._selectedIndex=i.index,this._launchDialogById("#delete-registry-dialog")}}
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg green"
            icon="refresh"
            @click=${()=>{this._selectedIndex=i.index,this._rescanImage()}}
          ></mwc-icon-button>
        </div>
      `,e)}render(){var e,t,i,a,s,o;return g`
      <h4 class="horizontal flex center center-justified layout">
        <span>${p("registry.Registries")}</span>
        <span class="flex"></span>
        <mwc-button
          raised
          id="add-registry"
          label="${p("registry.AddRegistry")}"
          icon="add"
          @click=${()=>this._openCreateRegistryDialog()}
        ></mwc-button>
      </h4>
      <div class="list-wrapper">
        <vaadin-grid
          theme="row-stripes column-borders compact"
          aria-label="Registry list"
          .items="${this._registryList}"
        >
          <vaadin-grid-column
            flex-grow="0"
            width="40px"
            header="#"
            text-align="center"
            .renderer=${this._indexRenderer}
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            auto-width
            header="${p("registry.Hostname")}"
            .renderer=${this._hostNameRenderer}
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="2"
            auto-width
            header="${p("registry.RegistryURL")}"
            resizable
            .renderer=${this._registryUrlRenderer}
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="0"
            auto-width
            resizable
            header="${p("registry.Type")}"
            path="type"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="0"
            auto-width
            resizable
            header="${p("registry.HarborProject")}"
            path="project"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${p("registry.Username")}"
            path="username"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${p("registry.Password")}"
            .renderer="${this._boundPasswordRenderer}"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="0"
            width="60px"
            header="${p("general.Enabled")}"
            .renderer=${this._boundIsEnabledRenderer}
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${p("general.Control")}"
            .renderer=${this._boundControlsRenderer}
          ></vaadin-grid-column>
        </vaadin-grid>
        <backend-ai-list-status
          id="list-status"
          statusCondition="${this._listCondition}"
          message="${m("registry.NoRegistryToDisplay")}"
        ></backend-ai-list-status>
      </div>
      <backend-ai-dialog
        id="configure-registry-dialog"
        fixed
        backdrop
        blockscrolling
      >
        <span slot="title">
          ${this._editMode?p("registry.ModifyRegistry"):p("registry.AddRegistry")}
        </span>
        <div slot="content" class="login-panel intro centered">
          <div class="horizontal center-justified layout flex">
            <mwc-textfield
              id="configure-registry-hostname"
              type="text"
              class="hostname"
              label="${p("registry.RegistryHostname")}"
              required
              ?disabled="${this._editMode}"
              pattern="^.+$"
              value="${(null===(e=this._registryList[this._selectedIndex])||void 0===e?void 0:e.hostname)||""}"
              validationMessage="${p("registry.DescHostnameIsEmpty")}"
            ></mwc-textfield>
          </div>
          <div class="horizontal layout flex">
            <mwc-textfield
              id="configure-registry-url"
              type="url"
              class="hostname"
              label="${p("registry.RegistryURL")}"
              required
              value="${(null===(t=this._registryList[this._selectedIndex])||void 0===t?void 0:t[""])||""}"
              @change=${this._checkValidationMsgOnRegistryUrlInput}
              @click=${this._checkValidationMsgOnRegistryUrlInput}
            ></mwc-textfield>
          </div>
          <div class="horizontal layout flex">
            <mwc-textfield
              id="configure-registry-username"
              type="text"
              label="${p("registry.UsernameOptional")}"
              style="padding-right:10px;"
              value="${(null===(i=this._registryList[this._selectedIndex])||void 0===i?void 0:i.username)||""}"
            ></mwc-textfield>
            <mwc-textfield
              id="configure-registry-password"
              type="password"
              label="${p("registry.PasswordOptional")}"
              style="padding-left:10px;"
              value="${(null===(a=this._registryList[this._selectedIndex])||void 0===a?void 0:a.password)||""}"
            ></mwc-textfield>
          </div>
          <mwc-select
            id="select-registry-type"
            label="${p("registry.RegistryType")}"
            @change=${this._toggleProjectNameInput}
            required
            validationMessage="${p("registry.PleaseSelectOption")}"
            value="${(null===(s=this._registryList[this._selectedIndex])||void 0===s?void 0:s.type)||this._registryType}"
          >
            ${y._registryTypes.map((e=>{var t;return g`
                <mwc-list-item
                  value="${e}"
                  ?selected="${this._editMode?e===(null===(t=this._registryList[this._selectedIndex])||void 0===t?void 0:t.type):"docker"===e}"
                >
                  ${e}
                </mwc-list-item>
              `}))}
          </mwc-select>
          <div class="vertical layout end-justified">
            <mwc-textfield
              id="configure-project-name"
              class="helper-text"
              type="text"
              label="${p("registry.ProjectName")}"
              required
              value="${(null===(o=this._registryList[this._selectedIndex])||void 0===o?void 0:o.project)||""}"
              ?disabled="${"docker"===this._registryType}"
            ></mwc-textfield>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            icon="add"
            label=${this._editMode?p("button.Save"):p("button.Add")}
            @click=${()=>this._addRegistry()}
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="delete-registry-dialog"
        fixed
        backdrop
        blockscrolling
      >
        <span slot="title">${p("dialog.warning.CannotBeUndone")}</span>
        <div slot="content">
          <mwc-textfield
            id="delete-registry"
            type="text"
            label="${p("registry.TypeRegistryNameToDelete")}"
          ></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            icon="delete"
            label="${p("button.Delete")}"
            @click=${()=>this._deleteRegistry()}
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};b._registryTypes=["docker","harbor","harbor2"],e([i("#list-status")],b.prototype,"_listStatus",void 0),e([i("#configure-registry-hostname")],b.prototype,"_hostnameInput",void 0),e([i("#configure-registry-password")],b.prototype,"_passwordInput",void 0),e([i("#configure-project-name")],b.prototype,"_projectNameInput",void 0),e([i("#select-registry-type")],b.prototype,"_selectedRegistryTypeInput",void 0),e([i("#configure-registry-url")],b.prototype,"_urlInput",void 0),e([i("#configure-registry-username")],b.prototype,"_usernameInput",void 0),b=y=e([a("backend-ai-registry-list")],b);let _=class extends s{constructor(){super(),this.resourcePolicy={},this.is_admin=!1,this.active=!1,this.gpu_allocatable=!1,this.gpuAllocationMode="device",this.condition="",this.presetName="",this.listCondition="loading",this._boundResourceRenderer=this.resourceRenderer.bind(this),this._boundControlRenderer=this.controlRenderer.bind(this)}static get styles(){return[o,r,n,c`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 229px);
        }

        mwc-icon {
          --mdc-icon-size: 16px;
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

        div.configuration mwc-icon {
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

        mwc-button,
        mwc-button[unelevated] {
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
          border-bottom: 1px solid #ddd;
        }
      `]}resourceRenderer(e,t,i){h(g`
        <div class="layout horizontal wrap center">
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green">developer_board</mwc-icon>
            <span>
              ${this._markIfUnlimited(i.item.resource_slots.cpu)}
            </span>
            <span class="indicator">${p("general.cores")}</span>
          </div>
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green">memory</mwc-icon>
            <span>
              ${this._markIfUnlimited(i.item.resource_slots.mem_gib)}
            </span>
            <span class="indicator">GiB</span>
          </div>
        </div>
        <div class="layout horizontal wrap center">
          ${i.item.resource_slots["cuda.device"]?g`
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green">view_module</mwc-icon>
                  <span>
                    ${this._markIfUnlimited(i.item.resource_slots["cuda.device"])}
                  </span>
                  <span class="indicator">GPU</span>
                </div>
              `:g``}
          ${i.item.resource_slots["cuda.shares"]?g`
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg green">view_module</mwc-icon>
                  <span>
                    ${this._markIfUnlimited(i.item.resource_slots["cuda.shares"])}
                  </span>
                  <span class="indicator">FGPU</span>
                </div>
              `:g``}
          ${i.item.shared_memory?g`
                <div class="layout horizontal configuration">
                  <mwc-icon class="fg blue">memory</mwc-icon>
                  <span>${i.item.shared_memory_gib}</span>
                  <span class="indicator">GiB</span>
                </div>
              `:g``}
        </div>
      `,e)}controlRenderer(e,t,i){h(g`
        <div
          id="controls"
          class="layout horizontal flex center"
          .preset-name="${i.item.name}"
        >
          ${this.is_admin?g`
                <mwc-icon-button
                  class="fg blue controls-running"
                  icon="settings"
                  @click="${e=>this._launchResourcePresetDialog(e)}"
                ></mwc-icon-button>
                <mwc-icon-button
                  class="fg red controls-running"
                  icon="delete"
                  @click="${e=>this._launchDeleteResourcePresetDialog(e)}"
                ></mwc-icon-button>
              `:g``}
        </div>
      `,e)}_indexRenderer(e,t,i){const a=i.index+1;h(g`
        <div>${a}</div>
      `,e)}render(){return g`
      <div style="margin:0px;">
        <h4 class="horizontal flex center center-justified layout">
          <span>${p("resourcePreset.ResourcePresets")}</span>
          <span class="flex"></span>
          <mwc-button
            raised
            id="add-resource-preset"
            icon="add"
            label="${p("resourcePreset.CreatePreset")}"
            @click="${()=>this._launchPresetAddDialog()}"
          ></mwc-button>
        </h4>
        <div class="list-wrapper">
          <vaadin-grid
            theme="row-stripes column-borders compact"
            height-by-rows
            aria-label="Resource Policy list"
            .items="${this.resourcePresets}"
          >
            <vaadin-grid-column
              width="40px"
              flex-grow="0"
              header="#"
              text-align="center"
              .renderer="${this._indexRenderer}"
            ></vaadin-grid-column>
            <vaadin-grid-sort-column
              resizable
              path="name"
              header="${p("resourcePreset.Name")}"
            ></vaadin-grid-sort-column>
            <vaadin-grid-column
              width="150px"
              resizable
              header="${p("resourcePreset.Resources")}"
              .renderer="${this._boundResourceRenderer}"
            ></vaadin-grid-column>
            <vaadin-grid-column
              resizable
              header="${p("general.Control")}"
              .renderer="${this._boundControlRenderer}"
            ></vaadin-grid-column>
          </vaadin-grid>
          <backend-ai-list-status
            id="list-status"
            statusCondition="${this.listCondition}"
            message="${m("resourcePreset.NoResourcePresetToDisplay")}"
          ></backend-ai-list-status>
        </div>
      </div>
      <backend-ai-dialog
        id="modify-template-dialog"
        fixed
        backdrop
        blockscrolling
      >
        <span slot="title">${p("resourcePreset.ModifyResourcePreset")}</span>
        <div slot="content">
          <form id="login-form">
            <fieldset>
              <mwc-textfield
                type="text"
                name="preset_name"
                class="modify"
                id="id-preset-name"
                label="${p("resourcePreset.PresetName")}"
                auto-validate
                required
                disabled
                error-message="${p("data.Allowslettersnumbersand-_dot")}"
              ></mwc-textfield>
              <h4>${p("resourcePreset.ResourcePreset")}</h4>
              <div class="horizontal center layout">
                <mwc-textfield
                  id="cpu-resource"
                  class="modify"
                  type="number"
                  label="CPU"
                  min="1"
                  value="1"
                  required
                  validationMessage="${p("resourcePreset.MinimumCPUUnit")}"
                ></mwc-textfield>
                <mwc-textfield
                  id="ram-resource"
                  class="modify"
                  type="number"
                  label="${p("resourcePreset.RAM")}"
                  min="1"
                  value="1"
                  required
                  validationMessage="${p("resourcePreset.MinimumMemUnit")}"
                ></mwc-textfield>
              </div>
              <div class="horizontal center layout">
                <mwc-textfield
                  id="gpu-resource"
                  class="modify"
                  type="number"
                  label="GPU"
                  min="0"
                  value="0"
                  ?disabled=${"fractional"===this.gpuAllocationMode}
                ></mwc-textfield>
                <mwc-textfield
                  id="fgpu-resource"
                  class="modify"
                  type="number"
                  label="fGPU"
                  min="0"
                  value="0"
                  step="0.01"
                  ?disabled=${"fractional"!==this.gpuAllocationMode}
                ></mwc-textfield>
              </div>
              <div class="horizontal center layout">
                <mwc-textfield
                  id="shmem-resource"
                  class="modify"
                  type="number"
                  label="${p("resourcePreset.SharedMemory")}"
                  min="0"
                  step="0.01"
                  validationMessage="${p("resourcePreset.MinimumShmemUnit")}"
                ></mwc-textfield>
              </div>
            </fieldset>
          </form>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            icon="check"
            label="${p("button.SaveChanges")}"
            @click="${()=>this._modifyResourceTemplate()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="create-preset-dialog"
        fixed
        backdrop
        blockscrolling
      >
        <span slot="title">${p("resourcePreset.CreateResourcePreset")}</span>
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
            placeholder="${p("maxLength.255chars")}"
            error-message="${p("data.Allowslettersnumbersand-_")}"
          ></mwc-textfield>
          <h4>${p("resourcePreset.ResourcePreset")}</h4>
          <div class="horizontal center layout">
            <mwc-textfield
              id="create-cpu-resource"
              class="create"
              type="number"
              label="CPU"
              min="1"
              value="1"
              required
              validationMessage="${p("resourcePreset.MinimumCPUUnit")}"
            ></mwc-textfield>
            <mwc-textfield
              id="create-ram-resource"
              class="create"
              type="number"
              label="${p("resourcePreset.RAM")}"
              min="1"
              value="1"
              required
              validationMessage="${p("resourcePreset.MinimumMemUnit")}"
            ></mwc-textfield>
          </div>
          <div class="horizontal center layout">
            <mwc-textfield
              id="create-gpu-resource"
              class="create"
              type="number"
              label="GPU"
              min="0"
              value="0"
              ?disabled=${"fractional"===this.gpuAllocationMode}
            ></mwc-textfield>
            <mwc-textfield
              id="create-fgpu-resource"
              class="create"
              type="number"
              label="fGPU"
              min="0"
              value="0"
              step="0.01"
              ?disabled=${"fractional"!==this.gpuAllocationMode}
            ></mwc-textfield>
          </div>
          <div class="horizontal center layout">
            <mwc-textfield
              id="create-shmem-resource"
              class="create"
              type="number"
              label="${p("resourcePreset.SharedMemory")}"
              min="0"
              step="0.01"
              validationMessage="${p("resourcePreset.MinimumShmemUnit")}"
            ></mwc-textfield>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            id="create-policy-button"
            icon="add"
            label="${p("button.Add")}"
            @click="${this._createPreset}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="delete-resource-preset-dialog"
        fixed
        backdrop
        blockscrolling
      >
        <span slot="title">${p("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${p("resourcePreset.AboutToDeletePreset")}</p>
          <p style="text-align:center;">${this.presetName}</p>
          <p>
            ${p("dialog.warning.CannotBeUndone")}
            ${p("dialog.ask.DoYouWantToProceed")}
          </p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            class="operation"
            label="${p("button.Cancel")}"
            @click="${e=>this._hideDialog(e)}"
          ></mwc-button>
          <mwc-button
            unelevated
            class="operation"
            label="${p("button.Okay")}"
            @click="${()=>this._deleteResourcePresetWithCheck()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}firstUpdated(){var e;this.notification=globalThis.lablupNotification;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("mwc-textfield");null==t||t.forEach((e=>{this._addInputValidator(e)}))}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._refreshTemplateData(),this.is_admin=globalThis.backendaiclient.is_admin}),!0):(this._refreshTemplateData(),this.is_admin=globalThis.backendaiclient.is_admin,globalThis.backendaiclient.get_resource_slots().then((e=>{this.gpu_allocatable=2!==Object.keys(e).length,Object.keys(e).includes("cuda.shares")?this.gpuAllocationMode="fractional":this.gpuAllocationMode="device"}))))}_launchPresetAddDialog(){this.createPresetDialog.show()}_launchResourcePresetDialog(e){this.updateCurrentPresetToDialog(e),this.modifyTemplateDialog.show()}_launchDeleteResourcePresetDialog(e){const t=e.target.closest("#controls")["preset-name"];this.presetName=t,this.deleteResourcePresetDialog.show()}_deleteResourcePresetWithCheck(){globalThis.backendaiclient.resourcePreset.delete(this.presetName).then((e=>{this.deleteResourcePresetDialog.hide(),this.notification.text=m("resourcePreset.Deleted"),this.notification.show(),this._refreshTemplateData()})).catch((e=>{console.log(e),e&&e.message&&(this.deleteResourcePresetDialog.hide(),this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}updateCurrentPresetToDialog(e){const t=e.target.closest("#controls")["preset-name"],i=globalThis.backendaiclient.utils.gqlToObject(this.resourcePresets,"name")[t];this.presetNameInput.value=t,this.cpuResourceInput.value=i.resource_slots.cpu,this.gpuResourceInput.value="cuda.device"in i.resource_slots?i.resource_slots["cuda.device"]:"",this.fgpuResourceInput.value="cuda.shares"in i.resource_slots?i.resource_slots["cuda.shares"]:"",this.ramResourceInput.value=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(i.resource_slots.mem,"g")).toString(),this.sharedMemoryResourceInput.value=i.shared_memory?parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(i.shared_memory,"g")).toFixed(2):""}_refreshTemplateData(){var e;const t={group:globalThis.backendaiclient.current_group};return this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.resourcePreset.check(t).then((e=>{var t;const i=e.presets;Object.keys(i).map(((e,t)=>{const a=i[e];a.resource_slots.mem_gib=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(a.resource_slots.mem,"g")),a.shared_memory?a.shared_memory_gib=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(a.shared_memory,"g")).toFixed(2):a.shared_memory_gib=null})),this.resourcePresets=i,0==this.resourcePresets.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}refresh(){this._refreshTemplateData()}_isActive(){return"active"===this.condition}_readResourcePresetInput(){const e=e=>void 0!==e&&e.includes("Unlimited")?"Infinity":e,t=e(this.cpuResourceInput.value),i=e(this.ramResourceInput.value+"g"),a=e(this.gpuResourceInput.value),s=e(this.fgpuResourceInput.value);let o=this.sharedMemoryResourceInput.value;o&&(o+="g");const r={cpu:t,mem:i};null!=a&&""!==a&&"0"!==a&&(r["cuda.device"]=parseInt(a)),null!=s&&""!==s&&"0"!==s&&(r["cuda.shares"]=parseFloat(s));return{resource_slots:JSON.stringify(r),shared_memory:o}}_modifyResourceTemplate(){if(!this._checkFieldValidity("modify"))return;const e=this.presetNameInput.value,t=void 0!==(i=this.ramResourceInput.value+"g")&&i.includes("Unlimited")?"Infinity":i;var i;if(!e)return this.notification.text=m("resourcePreset.NoPresetName"),void this.notification.show();const a=this._readResourcePresetInput();if(parseInt(a.shared_memory)>=parseInt(t))return this.notification.text=m("resourcePreset.MemoryShouldBeLargerThanSHMEM"),void this.notification.show();globalThis.backendaiclient.resourcePreset.mutate(e,a).then((e=>{this.modifyTemplateDialog.hide(),this.notification.text=m("resourcePreset.Updated"),this.notification.show(),this._refreshTemplateData()})).catch((e=>{console.log(e),e&&e.message&&(this.modifyTemplateDialog.hide(),this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_deleteKey(e){const t=e.target.closest("#controls").accessKey;globalThis.backendaiclient.keypair.delete(t).then((e=>{this.refresh()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_findKeyItem(e){return e.access_key=this}_elapsed(e,t){const i=new Date(e);let a;a=(this.condition,new Date);const s=Math.floor((a.getTime()-i.getTime())/1e3);return Math.floor(s/86400)}_humanReadableTime(e){return(e=new Date(e)).toUTCString()}_indexFrom1(e){return e+1}_markIfUnlimited(e){return["-",0,"Unlimited",1/0,"Infinity"].includes(e)?"∞":e}_checkFieldValidity(e=""){var t;const i='mwc-textfield[class^="'.concat(e).concat('"]'),a=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(i);let s=!0;for(const e of Array.from(a))if(s=e.checkValidity(),!s)return e.checkValidity();return s}_createPreset(){if(!this._checkFieldValidity("create"))return;const e=e=>void 0!==(e=e.toString())&&e.includes("Unlimited")?"Infinity":e,t=e(this.createPresetNameInput.value),i=e(this.createCpuResourceInput.value),a=e(this.createRamResourceInput.value+"g"),s=e(this.createGpuResourceInput.value),o=e(this.createFGpuResourceInput.value);let r=this.createSharedMemoryResourceInput.value;if(r&&(r+="g"),!t)return this.notification.text=m("resourcePreset.NoPresetName"),void this.notification.show();if(parseInt(r)>=parseInt(a))return this.notification.text=m("resourcePreset.MemoryShouldBeLargerThanSHMEM"),void this.notification.show();const n={cpu:i,mem:a};null!=s&&""!==s&&"0"!==s&&(n["cuda.device"]=parseInt(s)),null!=o&&""!==o&&"0"!==o&&(n["cuda.shares"]=parseFloat(o));const l={resource_slots:JSON.stringify(n),shared_memory:r};globalThis.backendaiclient.resourcePreset.add(t,l).then((e=>{this.createPresetDialog.hide(),e.create_resource_preset.ok?(this.notification.text=m("resourcePreset.Created"),this.refresh(),this.createPresetNameInput.value="",this.createCpuResourceInput.value="1",this.createRamResourceInput.value="1",this.createGpuResourceInput.value="0",this.createFGpuResourceInput.value="0",this.createSharedMemoryResourceInput.value=""):this.notification.text=u.relieve(e.create_resource_preset.msg),this.notification.show()}))}};e([t({type:Array})],_.prototype,"resourcePolicy",void 0),e([t({type:Boolean})],_.prototype,"is_admin",void 0),e([t({type:Boolean,reflect:!0})],_.prototype,"active",void 0),e([t({type:Boolean})],_.prototype,"gpu_allocatable",void 0),e([t({type:String})],_.prototype,"gpuAllocationMode",void 0),e([t({type:String})],_.prototype,"condition",void 0),e([t({type:String})],_.prototype,"presetName",void 0),e([t({type:Object})],_.prototype,"resourcePresets",void 0),e([t({type:String})],_.prototype,"listCondition",void 0),e([t({type:Array})],_.prototype,"_boundResourceRenderer",void 0),e([t({type:Array})],_.prototype,"_boundControlRenderer",void 0),e([i("#create-preset-name")],_.prototype,"createPresetNameInput",void 0),e([i("#create-cpu-resource")],_.prototype,"createCpuResourceInput",void 0),e([i("#create-ram-resource")],_.prototype,"createRamResourceInput",void 0),e([i("#create-gpu-resource")],_.prototype,"createGpuResourceInput",void 0),e([i("#create-fgpu-resource")],_.prototype,"createFGpuResourceInput",void 0),e([i("#create-shmem-resource")],_.prototype,"createSharedMemoryResourceInput",void 0),e([i("#cpu-resource")],_.prototype,"cpuResourceInput",void 0),e([i("#ram-resource")],_.prototype,"ramResourceInput",void 0),e([i("#gpu-resource")],_.prototype,"gpuResourceInput",void 0),e([i("#fgpu-resource")],_.prototype,"fgpuResourceInput",void 0),e([i("#shmem-resource")],_.prototype,"sharedMemoryResourceInput",void 0),e([i("#id-preset-name")],_.prototype,"presetNameInput",void 0),e([i("#create-preset-dialog")],_.prototype,"createPresetDialog",void 0),e([i("#modify-template-dialog")],_.prototype,"modifyTemplateDialog",void 0),e([i("#delete-resource-preset-dialog")],_.prototype,"deleteResourcePresetDialog",void 0),e([i("#list-status")],_.prototype,"_listStatus",void 0),_=e([a("backend-ai-resource-preset-list")],_);let f=class extends s{constructor(){super(...arguments),this.images=Object(),this.is_superadmin=!1,this._activeTab="image-lists"}static get styles(){return[o,r,n,c`
        h3.tab {
          background-color: var(--general-tabbar-background-color);
          border-radius: 5px 5px 0px 0px;
          margin: 0px auto;
        }

        mwc-tab-bar {
          --mdc-theme-primary: var(--general-sidebar-selected-color);
          --mdc-text-transform: none;
          --mdc-tab-color-default: var(--general-tabbar-background-color);
          --mdc-tab-text-label-color-default: var(
            --general-tabbar-tab-disabled-color
          );
        }

        div h4 {
          margin: 0;
          font-weight: 100;
          font-size: 16px;
          padding-left: 20px;
          border-bottom: 1px solid #ccc;
          width: 100%;
        }

        @media screen and (max-width: 805px) {
          mwc-tab,
          mwc-button {
            --mdc-typography-button-font-size: 10px;
          }
        }
      `]}static get properties(){return{active:{type:Boolean},_activeTab:{type:String}}}async _viewStateChanged(e){return await this.updateComplete,!1===e||(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_superadmin=globalThis.backendaiclient.is_superadmin}),!0):this.is_superadmin=globalThis.backendaiclient.is_superadmin,!1)}_showTab(e){var t,i;const a=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(let e=0;e<a.length;e++)a[e].style.display="none";this._activeTab=e.title,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e.title)).style.display="block"}render(){return g`
      <link rel="stylesheet" href="resources/custom.css" />
      <lablup-activity-panel noheader narrow autowidth>
        <div slot="message">
          <h3 class="tab horizontal center layout">
            <mwc-tab-bar>
              <mwc-tab
                title="image-lists"
                label="${p("environment.Images")}"
                @click="${e=>this._showTab(e.target)}"
              ></mwc-tab>
              <mwc-tab
                title="resource-template-lists"
                label="${p("environment.ResourcePresets")}"
                @click="${e=>this._showTab(e.target)}"
              ></mwc-tab>
              ${this.is_superadmin?g`
                    <mwc-tab
                      title="registry-lists"
                      label="${p("environment.Registries")}"
                      @click="${e=>this._showTab(e.target)}"
                    ></mwc-tab>
                  `:g``}
            </mwc-tab-bar>
            <div class="flex"></div>
          </h3>
          <div id="image-lists" class="tab-content">
            <backend-ai-environment-list
              ?active="${"image-lists"===this._activeTab}"
            ></backend-ai-environment-list>
          </div>
          <backend-ai-resource-preset-list
            id="resource-template-lists"
            class="admin item tab-content"
            style="display: none"
            ?active="${"resource-template-lists"===this._activeTab}"
          ></backend-ai-resource-preset-list>
          <div id="registry-lists" class="tab-content">
            <backend-ai-registry-list
              ?active="${"registry-lists"===this._activeTab}"
            ></backend-ai-registry-list>
          </div>
        </div>
      </lablup-activity-panel>
    `}};e([t({type:String})],f.prototype,"images",void 0),e([t({type:Boolean})],f.prototype,"is_superadmin",void 0),e([t({type:String})],f.prototype,"_activeTab",void 0),f=e([a("backend-ai-environment-view")],f);
