import{_ as e,n as t,e as i,t as s,B as a,b as o,I as r,a as n,u as l,c as d,i as c,g as m,d as p,f as u,p as h,x as g}from"./backend-ai-webui-dvRyOX_e.js";import"./lablup-grid-sort-filter-column-C2aexclr.js";import"./lablup-loading-spinner-DTpOeT_t.js";import"./vaadin-grid-selection-column-DHR7-_MG.js";import"./vaadin-grid-DjH0sPLR.js";import"./vaadin-grid-filter-column-Bstvob6v.js";import"./vaadin-grid-sort-column-Bkfboj4k.js";import"./mwc-switch-C1VxcxVe.js";import"./backend-ai-list-status-CpZuh1nO.js";import"./vaadin-item-FWhoAebV.js";import"./lablup-activity-panel-CUzA1T9h.js";import"./mwc-tab-bar-RQBvmmHz.js";import"./active-mixin-_JOWYQWx.js";import"./dir-utils-BTQok0yH.js";import"./vaadin-item-mixin-Eeh1qf5y.js";let v=class extends a{constructor(){super(),this.selectedImages=[],this.modifiedImage=Object(),this.alias=Object(),this.indicator=Object(),this.deleteAppInfo=Object(),this.deleteAppRow=Object(),this.openManageAppModal=!1,this.openManageImageResourceModal=!1,this.installImageResource=Object(),this.selectedCheckbox=Object(),this._grid=Object(),this.servicePortsMsg="",this.cpuValue=0,this.listCondition="loading",this._boundRequirementsRenderer=this.requirementsRenderer.bind(this),this._boundControlsRenderer=this.controlsRenderer.bind(this),this._boundInstallRenderer=this.installRenderer.bind(this),this._boundBaseImageRenderer=this.baseImageRenderer.bind(this),this._boundConstraintRenderer=this.constraintRenderer.bind(this),this._boundDigestRenderer=this.digestRenderer.bind(this),this.installImageNameList=[],this.deleteImageNameList=[],this.images=[],this.allowed_registries=[],this.servicePorts=[],this.modifiedImage={}}static get styles(){return[o,r,n,l,d,c`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 199px);
          /* height: calc(100vh - 229px); */
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
          font-family: var(--token-fontFamily);
          text-align: left;
          width: 70px;
        }
        backend-ai-dialog {
          --component-min-width: 350px;
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
        mwc-button.operation {
          margin: auto 10px;
          padding: auto 10px;
        }
        mwc-button[outlined] {
          width: 100%;
          margin: 10px auto;
          background-image: none;
          --mdc-button-outline-width: 2px;
        }
        mwc-button[disabled] {
          background-image: var(--general-sidebar-color);
        }
        mwc-button[disabled].range-value {
          --mdc-button-disabled-ink-color: var(
            --token-colorTextDisabled,
            --general-sidebar-color
          );
        }
        mwc-select {
          --mdc-menu-item-height: auto;
        }
        mwc-textfield {
          width: 100%;
          --mdc-text-field-fill-color: transparent;
          --mdc-theme-primary: var(--general-textfield-selected-color);
          --mdc-typography-font-family: var(--token-fontFamily);
        }
        mwc-slider {
          width: 150px;
          margin: auto 10px;
          --mdc-theme-primary: var(--general-slider-color);
          --mdc-theme-text-primary-on-dark: var(
            --token-colorSecondary,
            #ffffff
          );
        }
      `]}firstUpdated(){var e;this.indicator=globalThis.lablupIndicator,this.notification=globalThis.lablupNotification,this.resourceBroker=globalThis.resourceBroker,void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._getImages()}),!0):this._getImages(),this._grid=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#testgrid"),this._grid.addEventListener("sorter-changed",(e=>{this._refreshSorter(e)})),document.addEventListener("image-rescanned",(()=>{this._getImages()})),this.installImageDialog.addEventListener("didHide",(()=>{this._uncheckSelectedRow()})),this.deleteImageDialog.addEventListener("didHide",(()=>{this._uncheckSelectedRow()}))}_removeRow(){this.deleteAppRow.remove(),this.deleteAppInfoDialog.hide(),this.notification.text=m("environment.AppInfoDeleted"),this.notification.show()}_checkDeleteAppInfo(e){var t;this.deleteAppRow=e.target.parentNode;const i=[...this.deleteAppRow.children].filter((e=>"MWC-TEXTFIELD"===e.tagName)).map((e=>e.value));(null===(t=i.filter((e=>""===e)))||void 0===t?void 0:t.length)===i.length?this._removeRow():(this.deleteAppInfo=i,this.deleteAppInfoDialog.show())}_uncheckSelectedRow(){this._grid.selectedItems=[]}_refreshSorter(e){const t=e.target,i=t.path.toString();t.direction&&("asc"===t.direction?this._grid.items.sort(((e,t)=>e[i]<t[i]?-1:e[i]>t[i]?1:0)):this._grid.items.sort(((e,t)=>e[i]>t[i]?-1:e[i]<t[i]?1:0)))}async _viewStateChanged(e){await this.updateComplete}_getImages(){var e;this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.domain.get(globalThis.backendaiclient._config.domainName,["allowed_docker_registries"]).then((e=>(this.allowed_registries=e.domain.allowed_docker_registries,globalThis.backendaiclient.image.list(["name","tag","registry","architecture","digest","installed","labels { key value }","resource_limits { key min max }"],!1,!0)))).then((e=>{var t;const i=e.images,s=[];i.forEach((e=>{var t,i;if("registry"in e&&this.allowed_registries.includes(e.registry)){const a=e.tag.split("-");if(void 0!==a[1]){let s,o;e.baseversion=a[0],e.baseimage=a[1],void 0!==a[2]&&(s=this._humanizeName(a.slice(2,a.indexOf("customized_")).join("-")),o=null===(i=null===(t=e.labels)||void 0===t?void 0:t.find((e=>"ai.backend.customized-image.name"===e.key)))||void 0===i?void 0:i.value,e.constraint=[s,null!=o?o:void 0])}else void 0!==e.tag?e.baseversion=e.tag:e.baseversion="";const o=e.name.split("/");void 0!==o[1]?(e.namespace=o[0],e.lang=o.slice(1).join("")):(e.namespace="",e.lang=o[0]);const r=e.lang.split("-");let n;n=void 0!==e.baseimage?[this._humanizeName(e.baseimage)]:[],void 0!==r[1]&&("r"===r[0]?(e.lang=r[0],n.push(this._humanizeName(r[0]))):(e.lang=r[1],n.push(this._humanizeName(r[0])))),e.baseimage=n,e.lang=this._humanizeName(e.lang);e.resource_limits.forEach((t=>{0==t.max&&(t.max="∞"),"cuda.device"==t.key&&(t.key="cuda_device"),"cuda.shares"==t.key&&(t.key="cuda_shares"),"rocm.device"==t.key&&(t.key="rocm_device"),"tpu.device"==t.key&&(t.key="tpu_device"),"ipu.device"==t.key&&(t.key="ipu_device"),"atom.device"==t.key&&(t.key="atom_device"),"atom.device+"==t.key&&(t.key="atom_device_plus"),"warboy.device"==t.key&&(t.key="warboy_device"),"hyperaccel-lpu.device"==t.key&&(t.key="hyperaccel_lpu_device"),null!==t.min&&void 0!==t.min&&(e[t.key+"_limit_min"]=this._addUnit(t.min)),null!==t.max&&void 0!==t.max?e[t.key+"_limit_max"]=this._addUnit(t.max):e[t.key+"_limit_max"]=1/0})),e.labels=e.labels.reduce(((e,t)=>({...e,[t.key]:t.value})),{}),s.push(e)}}));const a=s.sort(((e,t)=>t.installed-e.installed));this.images=a,0==this.images.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide()})).catch((e=>{var t;console.log(e),void 0!==e.message?(this.notification.text=p.relieve(e.title),this.notification.detail=e.message):this.notification.text=p.relieve("Problem occurred during image metadata loading."),this.notification.show(!0,e),null===(t=this._listStatus)||void 0===t||t.hide()}))}_addUnit(e){const t=e.substr(-1);return"m"==t?e.slice(0,-1)+"MiB":"g"==t?e.slice(0,-1)+"GiB":"t"==t?e.slice(0,-1)+"TiB":e}_symbolicUnit(e){const t=e.substr(-2);return"MB"==t?e.slice(0,-2)+"m":"GB"==t?e.slice(0,-2)+"g":"TB"==t?e.slice(0,-2)+"t":e}_humanizeName(e){this.alias=this.resourceBroker.imageTagAlias;const t=this.resourceBroker.imageTagReplace;for(const[i,s]of Object.entries(t)){const t=new RegExp(i);if(t.test(e))return e.replace(t,s)}return e in this.alias?this.alias[e]:e}_markIfUnlimited(e){return["-",0,"Unlimited",1/0,"Infinity"].includes(e)?"∞":e}_hideDialogById(e){var t;return(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(e)).hide()}_launchDialogById(e){var t;return(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(e)).show()}openInstallImageDialog(){this.selectedImages=this._grid.selectedItems.filter((e=>!e.installed)),this.installImageNameList=this.selectedImages.map((e=>(Object.keys(e).map((t=>{["registry","name","tag"].includes(t)&&t in e&&(e[t]=e[t].replace(/\s/g,""))})),e.registry+"/"+e.name+":"+e.tag))),this.selectedImages.length>0?this.installImageDialog.show():(this.notification.text=m("environment.SelectedImagesAlreadyInstalled"),this.notification.show())}_installImage(){this.installImageDialog.hide(),this.selectedImages.forEach((async e=>{const t='[id="'+e.registry.replace(/\./gi,"-")+"-"+e.name.replace("/","-")+"-"+e.tag.replace(/\./gi,"-")+'"]';this._grid.querySelector(t).setAttribute("style","display:block;");const i=e.registry+"/"+e.name+":"+e.tag;let s=!1;const a=Object();"resource_limits"in e&&e.resource_limits.forEach((e=>{a[e.key.replace("_",".")]=e.min})),"cuda.device"in a&&"cuda.shares"in a?(s=!0,a.gpu=0,a.fgpu=a["cuda.shares"]):"cuda.device"in a?(a.gpu=a["cuda.device"],s=!0):s=!1,a.mem.endsWith("g")?a.mem=a.mem.replace("g",".5g"):a.mem.endsWith("m")&&(a.mem=Number(a.mem.slice(0,-1))+256+"m"),a.domain=globalThis.backendaiclient._config.domainName,a.group_name=globalThis.backendaiclient.current_group;const o=await globalThis.backendaiclient.get_resource_slots();s&&("cuda.device"in o||"cuda.shares"in o||(delete a.gpu,delete a.fgpu,delete a["cuda.shares"],delete a["cuda.device"])),"cuda.device"in o&&"cuda.shares"in o?"fgpu"in a&&"gpu"in a&&(delete a.gpu,delete a["cuda.device"]):"cuda.device"in o?(delete a.fgpu,delete a["cuda.shares"]):"cuda.shares"in o&&(delete a.gpu,delete a["cuda.device"]),a.enqueueOnly=!0,a.type="batch",a.startupCommand='echo "Image is installed"',this.notification.text=m("environment.InstallingImage")+i+m("environment.TakesTime"),this.notification.show();const r=await this.indicator.start("indeterminate");r.set(10,m("import.Downloading")),globalThis.backendaiclient.image.install(i,e.architecture,a).then((()=>{r.end(1e3)})).catch((e=>{this._grid.querySelector(t).className=m("environment.Installing"),this._grid.querySelector(t).setAttribute("style","display:none;"),this._uncheckSelectedRow(),this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e),r.set(100,u("environment.DescProblemOccurred")),r.end(1e3)}))}))}openDeleteImageDialog(){this.selectedImages=this._grid.selectedItems.filter((e=>e.installed)),this.deleteImageNameList=this.selectedImages.map((e=>e.registry+"/"+e.name+":"+e.tag)),this.selectedImages.length>0?this.deleteImageDialog.show():(this.notification.text=m("environment.SelectedImagesNotInstalled"),this.notification.show())}_deleteImage(){}_decodeServicePort(){""===this.modifiedImage.labels["ai.backend.service-ports"]?this.servicePorts=[]:this.servicePorts=this.modifiedImage.labels["ai.backend.service-ports"].split(",").map((e=>{const t=e.split(":");return{app:t[0],protocol:t[1],port:t[2]}}))}requirementsRenderer(e,t,i){h(g`
        <div class="layout horizontal center flex">
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green indicator">developer_board</mwc-icon>
            <span>${i.item.cpu_limit_min}</span>
            ~
            <span>${this._markIfUnlimited(i.item.cpu_limit_max)}</span>
            <span class="indicator">${u("general.cores")}</span>
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
                    src="/resources/icons/rocm.svg"
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
                  <mwc-icon class="fg green indicator">view_module</mwc-icon>
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
                  <mwc-icon class="fg green indicator">view_module</mwc-icon>
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
                  <img
                    class="indicator-icon fg green"
                    src="/resources/icons/rebel.svg"
                  />
                  <span>${i.item.atom_device_limit_min}</span>
                  ~
                  <span>
                    ${this._markIfUnlimited(i.item.atom_device_limit_max)}
                  </span>
                  <span class="indicator">ATOM</span>
                </div>
              </div>
            `:g``}
        ${i.item.atom_plus_device_limit_min?g`
              <div class="layout horizontal center flex">
                <div class="layout horizontal configuration">
                  <img
                    class="indicator-icon fg green"
                    src="/resources/icons/rebel.svg"
                  />
                  <span>${i.item.atom_plus_device_limit_min}</span>
                  ~
                  <span>
                    ${this._markIfUnlimited(i.item.atom_plus_device_limit_max)}
                  </span>
                  <span class="indicator">ATOM+</span>
                </div>
              </div>
            `:g``}
        ${i.item.warboy_device_limit_min?g`
              <div class="layout horizontal center flex">
                <div class="layout horizontal configuration">
                  <img
                    class="indicator-icon fg green"
                    src="/resources/icons/furiosa.svg"
                  />
                  <span>${i.item.warboy_device_limit_min}</span>
                  ~
                  <span>
                    ${this._markIfUnlimited(i.item.warboy_device_limit_max)}
                  </span>
                  <span class="indicator">Warboy</span>
                </div>
              </div>
            `:g``}
        ${i.item.hyperaccel_lpu_device_limit_min?g`
              <div class="layout horizontal center flex">
                <div class="layout horizontal configuration">
                  <img
                    class="indicator-icon fg green"
                    src="/resources/icons/npu_generic.svg"
                  />
                  <span>${i.item.hyperaccel_lpu_device_limit_min}</span>
                  ~
                  <span>
                    ${this._markIfUnlimited(i.item.hyperaccel_lpu_device_limit_max)}
                  </span>
                  <span class="indicator">Hyperaccel LPU</span>
                </div>
              </div>
            `:g``}
      `,e)}controlsRenderer(e,t,i){h(g`
        <div id="controls" class="layout horizontal flex center">
          <mwc-icon-button
            class="fg controls-running blue"
            icon="settings"
            @click=${()=>{this.modifiedImage=i.item,this.openManageImageResourceModal=!0,this.requestUpdate()}}
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg controls-running pink"
            icon="apps"
            @click=${()=>{this.modifiedImage=i.item,this._decodeServicePort(),this.openManageAppModal=!0,this.requestUpdate()}}
          ></mwc-icon-button>
        </div>
      `,e)}installRenderer(e,t,i){h(g`
        <div class="layout horizontal center center-justified">
          ${i.item.installed?g`
                <lablup-shields
                  class="installed"
                  description="${u("environment.Installed")}"
                  color="darkgreen"
                  id="${i.item.registry.replace(/\./gi,"-")+"-"+i.item.name.replace("/","-")+"-"+i.item.tag.replace(/\./gi,"-")}"
                ></lablup-shields>
              `:g`
                <lablup-shields
                  class="installing"
                  description="${u("environment.Installing")}"
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
      `,e)}constraintRenderer(e,t,i){var s;h(g`
        ${i.item.constraint?g`
              <lablup-shields
                app=""
                color="green"
                ui="round"
                description="${i.item.constraint[0]}"
              ></lablup-shields>
              ${void 0!==(null===(s=i.item.constraint)||void 0===s?void 0:s[1])?g`
                    <lablup-shields
                      app="Customized"
                      color="cyan"
                      ui="round"
                      description="${i.item.constraint[1]}"
                    ></lablup-shields>
                  `:g``}
            `:g``}
      `,e)}digestRenderer(e,t,i){h(g`
        <div class="layout vertical">
          <span class="indicator monospace">${i.item.digest}</span>
        </div>
      `,e)}render(){return g`
      <h4 class="horizontal flex center center-justified layout">
        <span>${u("environment.Images")}</span>
        <span class="flex"></span>
        <mwc-button
          raised
          label="${u("environment.Install")}"
          class="operation"
          id="install-image"
          icon="get_app"
          @click="${this.openInstallImageDialog}"
        ></mwc-button>
        <mwc-button
          disabled
          label="${u("environment.Delete")}"
          class="operation temporarily-hide"
          id="delete-image"
          icon="delete"
          @click="${this.openDeleteImageDialog}"
        ></mwc-button>
      </h4>
      <div class="list-wrapper">
        <vaadin-grid
          theme="row-stripes column-borders compact dark"
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
            header="${u("environment.Status")}"
            .renderer="${this._boundInstallRenderer}"
          ></vaadin-grid-sort-column>
          <lablup-grid-sort-filter-column
            path="registry"
            width="80px"
            resizable
            header="${u("environment.Registry")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="architecture"
            width="80px"
            resizable
            header="${u("environment.Architecture")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="namespace"
            width="60px"
            resizable
            header="${u("environment.Namespace")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="lang"
            resizable
            header="${u("environment.Language")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="baseversion"
            resizable
            header="${u("environment.Version")}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="baseimage"
            resizable
            width="110px"
            header="${u("environment.Base")}"
            .renderer="${this._boundBaseImageRenderer}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="constraint"
            width="50px"
            resizable
            header="${u("environment.Constraint")}"
            .renderer="${this._boundConstraintRenderer}"
          ></lablup-grid-sort-filter-column>
          <lablup-grid-sort-filter-column
            path="digest"
            resizable
            header="${u("environment.Digest")}"
            .renderer="${this._boundDigestRenderer}"
          ></lablup-grid-sort-filter-column>
          <vaadin-grid-column
            width="150px"
            flex-grow="0"
            resizable
            header="${u("environment.ResourceLimit")}"
            .renderer="${this._boundRequirementsRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            frozen-to-end
            width="110px"
            resizable
            header="${u("general.Control")}"
            .renderer=${this._boundControlsRenderer}
          ></vaadin-grid-column>
        </vaadin-grid>
        <backend-ai-list-status
          id="list-status"
          statusCondition="${this.listCondition}"
          message="${m("environment.NoImageToDisplay")}"
        ></backend-ai-list-status>
      </div>
      <backend-ai-dialog id="install-image-dialog" fixed backdrop persistent>
        <span slot="title">${u("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${u("environment.DescDownloadImage")}</p>
          <p style="margin:auto; ">
            <span style="color:blue;">
              ${this.installImageNameList.map((e=>g`
                  ${e}
                  <br />
                `))}
            </span>
          </p>
          <p>
            ${u("environment.DescSignificantDownloadTime")}
            ${u("dialog.ask.DoYouWantToProceed")}
          </p>
        </div>
        <div slot="footer" class="horizontal flex layout">
          <div class="flex"></div>
          <mwc-button
            class="operation"
            label="${u("button.Cancel")}"
            @click="${e=>{this._hideDialog(e),this._uncheckSelectedRow()}}"
          ></mwc-button>
          <mwc-button
            unelevated
            class="operation"
            label="${u("button.Okay")}"
            @click="${()=>this._installImage()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-image-dialog" fixed backdrop persistent>
        <span slot="title">${u("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${u("environment.DescDeleteImage")}</p>
          <p style="margin:auto; ">
            <span style="color:blue;">
              ${this.deleteImageNameList.map((e=>g`
                  ${e}
                  <br />
                `))}
            </span>
          </p>
          <p>${u("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal flex layout">
          <div class="flex"></div>
          <mwc-button
            class="operation"
            label="${u("button.Cancel")}"
            @click="${e=>{this._hideDialog(e),this._uncheckSelectedRow()}}"
          ></mwc-button>
          <mwc-button
            unelevated
            class="operation"
            label="${u("button.Okay")}"
            @click="${()=>this._deleteImage()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-app-info-dialog" fixed backdrop persistent>
        <span slot="title">${u("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${u("environment.DescDeleteAppInfo")}</p>
          <div class="horizontal layout">
            <p>${u("environment.AppName")}</p>
            <p style="color:blue;">: ${this.deleteAppInfo[0]}</p>
          </div>
          <div class="horizontal layout">
            <p>${u("environment.Protocol")}</p>
            <p style="color:blue;">: ${this.deleteAppInfo[1]}</p>
          </div>
          <div class="horizontal layout">
            <p>${u("environment.Port")}</p>
            <p style="color:blue;">: ${this.deleteAppInfo[2]}</p>
          </div>
          <p>${u("dialog.ask.DoYouWantToProceed")}</p>
        </div>
        <div slot="footer" class="horizontal flex layout">
          <div class="flex"></div>
          <mwc-button
            class="operation"
            label="${u("button.Cancel")}"
            @click="${e=>this._hideDialog(e)}"
          ></mwc-button>
          <mwc-button
            unelevated
            class="operation"
            label="${u("button.Okay")}"
            @click="${()=>this._removeRow()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-react-manage-app-dialog
        value="${JSON.stringify({image:this.modifiedImage,servicePorts:this.servicePorts,open:this.openManageAppModal})}"
        @cancel="${()=>this.openManageAppModal=!1}"
        @ok="${()=>(this.openManageAppModal=!1,this._getImages())}"
      ></backend-ai-react-manage-app-dialog>
      <backend-ai-react-manage-resource-dialog
        value="${JSON.stringify({image:this.modifiedImage,open:this.openManageImageResourceModal})}"
        @cancel="${()=>this.openManageImageResourceModal=!1}"
        @ok="${()=>(this.openManageImageResourceModal=!1,this._getImages())}"
      ></backend-ai-react-manage-resource-dialog>
    `}};var y;e([t({type:Array})],v.prototype,"images",void 0),e([t({type:Object})],v.prototype,"resourceBroker",void 0),e([t({type:Array})],v.prototype,"allowed_registries",void 0),e([t({type:Array})],v.prototype,"servicePorts",void 0),e([t({type:Array})],v.prototype,"selectedImages",void 0),e([t({type:Object})],v.prototype,"modifiedImage",void 0),e([t({type:Object})],v.prototype,"alias",void 0),e([t({type:Object})],v.prototype,"indicator",void 0),e([t({type:Array})],v.prototype,"installImageNameList",void 0),e([t({type:Array})],v.prototype,"deleteImageNameList",void 0),e([t({type:Object})],v.prototype,"deleteAppInfo",void 0),e([t({type:Object})],v.prototype,"deleteAppRow",void 0),e([t({type:Boolean})],v.prototype,"openManageAppModal",void 0),e([t({type:Boolean})],v.prototype,"openManageImageResourceModal",void 0),e([t({type:Object})],v.prototype,"installImageResource",void 0),e([t({type:Object})],v.prototype,"selectedCheckbox",void 0),e([t({type:Object})],v.prototype,"_grid",void 0),e([t({type:String})],v.prototype,"servicePortsMsg",void 0),e([t({type:Number})],v.prototype,"cpuValue",void 0),e([t({type:String})],v.prototype,"listCondition",void 0),e([t({type:Object})],v.prototype,"_boundRequirementsRenderer",void 0),e([t({type:Object})],v.prototype,"_boundControlsRenderer",void 0),e([t({type:Object})],v.prototype,"_boundInstallRenderer",void 0),e([t({type:Object})],v.prototype,"_boundBaseImageRenderer",void 0),e([t({type:Object})],v.prototype,"_boundConstraintRenderer",void 0),e([t({type:Object})],v.prototype,"_boundDigestRenderer",void 0),e([i("#loading-spinner")],v.prototype,"spinner",void 0),e([i("#modify-image-cpu")],v.prototype,"modifyImageCpu",void 0),e([i("#modify-image-mem")],v.prototype,"modifyImageMemory",void 0),e([i("#modify-image-cuda-gpu")],v.prototype,"modifyImageCudaGpu",void 0),e([i("#modify-image-cuda-fgpu")],v.prototype,"modifyImageCudaFGpu",void 0),e([i("#modify-image-rocm-gpu")],v.prototype,"modifyImageRocmGpu",void 0),e([i("#modify-image-tpu")],v.prototype,"modifyImageTpu",void 0),e([i("#modify-image-ipu")],v.prototype,"modifyImageIpu",void 0),e([i("#modify-image-atom")],v.prototype,"modifyImageAtom",void 0),e([i("#modify-image-atom-plus")],v.prototype,"modifyImageAtomPlus",void 0),e([i("#modify-image-warboy")],v.prototype,"modifyImageWarboy",void 0),e([i("#modify-image-hyperaccel-lpu")],v.prototype,"modifyImageHyperaccelLPU",void 0),e([i("#delete-app-info-dialog")],v.prototype,"deleteAppInfoDialog",void 0),e([i("#delete-image-dialog")],v.prototype,"deleteImageDialog",void 0),e([i("#install-image-dialog")],v.prototype,"installImageDialog",void 0),e([i("#modify-app-container")],v.prototype,"modifyAppContainer",void 0),e([i("#list-status")],v.prototype,"_listStatus",void 0),v=e([s("backend-ai-environment-list")],v);let b=y=class extends a{constructor(){super(),this._listCondition="loading",this._editMode=!1,this._registryType="docker",this._selectedIndex=-1,this._boundIsEnabledRenderer=this._isEnabledRenderer.bind(this),this._boundControlsRenderer=this._controlsRenderer.bind(this),this._boundPasswordRenderer=this._passwordRenderer.bind(this),this._allowed_registries=[],this._editMode=!1,this._hostnames=[],this._registryList=[]}static get styles(){return[o,r,n,c`
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
          --mdc-typography-font-family: var(--token-fontFamily);
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification,this._indicator=globalThis.lablupIndicator,this._projectNameInput.validityTransform=(e,t)=>this._checkValidationMsgOnProjectNameInput(e,t)}_parseRegistryList(e){return Object.keys(e).map((t=>{return"string"==typeof(i=e[t])||i instanceof String?{"":e[t],hostname:t}:{...e[t],hostname:t};var i}))}_refreshRegistryList(){var e;this._listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.domain.get(globalThis.backendaiclient._config.domainName,["allowed_docker_registries"]).then((e=>(this._allowed_registries=e.domain.allowed_docker_registries,globalThis.backendaiclient.registry.list()))).then((({result:e})=>{var t;this._registryList=this._parseRegistryList(e),0==this._registryList.length?this._listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide(),this._hostnames=this._registryList.map((e=>e.hostname)),this.requestUpdate()}))}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._refreshRegistryList()}),!0):this._refreshRegistryList())}_addRegistry(){const e=this._hostnameInput.value,t=this._urlInput.value,i=this._usernameInput.value,s=this._passwordInput.value,a=this._selectedRegistryTypeInput.value,o=this._projectNameInput.value.replace(/\s/g,"");if(!this._hostnameInput.validity.valid)return;if(!this._urlInput.validity.valid)return;const r={};if(r[""]=t,""!==i&&""!==s&&(r.username=i,r.password=s),r.type=a,["harbor","harbor2"].includes(a)){if(!o||""===o)return;r.project=o}else r.project="";if(!this._editMode&&this._hostnames.includes(e))return this.notification.text=m("registry.RegistryHostnameAlreadyExists"),void this.notification.show();globalThis.backendaiclient.registry.set(e,r).then((({result:t})=>{"ok"===t?(this._editMode?this.notification.text=m("registry.RegistrySuccessfullyModified"):(this.notification.text=m("registry.RegistrySuccessfullyAdded"),this._hostnames.push(e),this._resetRegistryField()),this._refreshRegistryList()):this.notification.text=m("dialog.ErrorOccurred"),this._hideDialogById("#configure-registry-dialog"),this.notification.show()}))}_deleteRegistry(){var e;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#delete-registry"),i=t.value;this._registryList[this._selectedIndex].hostname===i?globalThis.backendaiclient.registry.delete(t.value).then((({result:e})=>{"ok"===e?(this.notification.text=m("registry.RegistrySuccessfullyDeleted"),this._hostnames.includes(i)&&this._hostnames.splice(this._hostnames.indexOf(i)),this._refreshRegistryList()):this.notification.text=m("dialog.ErrorOccurred"),this._hideDialogById("#delete-registry-dialog"),this.notification.show()})):(this.notification.text=m("registry.HostnameDoesNotMatch"),this.notification.show()),t.value=""}async _rescanImage(){const e=await this._indicator.start("indeterminate");e.set(10,m("registry.UpdatingRegistryInfo")),globalThis.backendaiclient.maintenance.rescan_images(this._registryList[this._selectedIndex].hostname).then((({rescan_images:t})=>{if(t.ok){e.set(0,m("registry.RescanImages"));const i=globalThis.backendaiclient.maintenance.attach_background_task(t.task_id);i.addEventListener("bgtask_updated",(t=>{const i=JSON.parse(t.data),s=i.current_progress/i.total_progress;e.set(100*s,m("registry.RescanImages"))})),i.addEventListener("bgtask_done",(()=>{const t=new CustomEvent("image-rescanned");document.dispatchEvent(t),e.set(100,m("registry.RegistryUpdateFinished")),i.close()})),i.addEventListener("bgtask_failed",(e=>{throw console.log("bgtask_failed",e.data),i.close(),new Error("Background Image scanning task has failed")})),i.addEventListener("bgtask_cancelled",(()=>{throw i.close(),new Error("Background Image scanning task has been cancelled")}))}else e.set(50,m("registry.RegistryUpdateFailed")),e.end(1e3),this.notification.text=p.relieve(t.msg),this.notification.detail=t.msg,this.notification.show()})).catch((t=>{console.log(t),e.set(50,m("registry.RescanFailed")),e.end(1e3),t&&t.message&&(this.notification.text=p.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))}))}_launchDialogById(e){var t;null===(t=this.shadowRoot)||void 0===t||t.querySelector(e).show()}_hideDialogById(e){var t;null===(t=this.shadowRoot)||void 0===t||t.querySelector(e).hide()}_openCreateRegistryDialog(){this._editMode=!1,this._selectedIndex=-1,this._registryType="docker",this.requestUpdate(),this._launchDialogById("#configure-registry-dialog")}_openEditRegistryDialog(e){var t;let i;this._editMode=!0;for(let t=0;t<this._registryList.length;t++)if(this._registryList[t].hostname===e){i=this._registryList[t];break}i?(this._registryList[this._selectedIndex]=i,this._registryType=null===(t=this._registryList[this._selectedIndex])||void 0===t?void 0:t.type,this.requestUpdate(),this._launchDialogById("#configure-registry-dialog")):globalThis.notification.show(`No such registry hostname: ${e}`)}_checkValidationMsgOnRegistryUrlInput(e){try{const t=new URL(this._urlInput.value);"http:"===t.protocol||"https:"===t.protocol?e.target.setCustomValidity(""):e.target.setCustomValidity(u("registry.DescURLStartString"))}catch(t){e.target.setCustomValidity(u("import.WrongURLType"))}}_checkValidationMsgOnProjectNameInput(e,t){return this._projectNameInput.value=this._projectNameInput.value.replace(/\s/g,""),["harbor","harbor2"].includes(this._registryType)?(this._projectNameInput.value||(this._projectNameInput.validationMessage=m("registry.ProjectNameIsRequired")),this._projectNameInput.disabled=!1):(this._projectNameInput.validationMessage=m("registry.ForHarborOnly"),this._projectNameInput.disabled=!0),{}}_toggleRegistryEnabled(e,t){e.target.selected?this._changeRegistryState(t,!0):this._changeRegistryState(t,!1)}_toggleProjectNameInput(){this._registryType=this._selectedRegistryTypeInput.value,this._checkValidationMsgOnProjectNameInput(!0,!0)}_resetRegistryField(){this._hostnameInput.value="",this._urlInput.value="",this._usernameInput.value="",this._passwordInput.value="",this._selectedRegistryTypeInput.value="",this._projectNameInput.value="",this.requestUpdate()}_changeRegistryState(e,t){if(!0===t)this._allowed_registries.push(e),this.notification.text=m("registry.RegistryTurnedOn");else{const t=this._allowed_registries.indexOf(e);1!==t&&this._allowed_registries.splice(t,1),this.notification.text=m("registry.RegistryTurnedOff")}globalThis.backendaiclient.domain.update(globalThis.backendaiclient._config.domainName,{allowed_docker_registries:this._allowed_registries}).then((e=>{this.notification.show()}))}_indexRenderer(e,t,i){const s=i.index+1;h(g`
        <div>${s}</div>
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
      `,e)}render(){var e,t,i,s,a,o;return g`
      <h4 class="horizontal flex center center-justified layout">
        <span>${u("registry.Registries")}</span>
        <span class="flex"></span>
        <mwc-button
          raised
          id="add-registry"
          label="${u("registry.AddRegistry")}"
          icon="add"
          @click=${()=>this._openCreateRegistryDialog()}
        ></mwc-button>
      </h4>
      <div class="list-wrapper">
        <vaadin-grid
          theme="row-stripes column-borders compact dark"
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
            header="${u("registry.Hostname")}"
            .renderer=${this._hostNameRenderer}
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="2"
            auto-width
            header="${u("registry.RegistryURL")}"
            resizable
            .renderer=${this._registryUrlRenderer}
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="0"
            auto-width
            resizable
            header="${u("registry.Type")}"
            path="type"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="0"
            auto-width
            resizable
            header="${u("registry.HarborProject")}"
            path="project"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${u("registry.Username")}"
            path="username"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="1"
            header="${u("registry.Password")}"
            .renderer="${this._boundPasswordRenderer}"
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            flex-grow="0"
            width="60px"
            header="${u("general.Enabled")}"
            .renderer=${this._boundIsEnabledRenderer}
            resizable
          ></vaadin-grid-column>
          <vaadin-grid-column
            frozen-to-end
            width="150px"
            resizable
            header="${u("general.Control")}"
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
          ${this._editMode?u("registry.ModifyRegistry"):u("registry.AddRegistry")}
        </span>
        <div slot="content" class="login-panel intro centered">
          <div class="horizontal center-justified layout flex">
            <mwc-textfield
              id="configure-registry-hostname"
              type="text"
              class="hostname"
              label="${u("registry.RegistryHostname")}"
              required
              ?disabled="${this._editMode}"
              pattern="^.+$"
              value="${(null===(e=this._registryList[this._selectedIndex])||void 0===e?void 0:e.hostname)||""}"
              validationMessage="${u("registry.DescHostnameIsEmpty")}"
            ></mwc-textfield>
          </div>
          <div class="horizontal layout flex">
            <mwc-textfield
              id="configure-registry-url"
              type="url"
              class="hostname"
              label="${u("registry.RegistryURL")}"
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
              label="${u("registry.UsernameOptional")}"
              style="padding-right:10px;"
              value="${(null===(i=this._registryList[this._selectedIndex])||void 0===i?void 0:i.username)||""}"
            ></mwc-textfield>
            <mwc-textfield
              id="configure-registry-password"
              type="password"
              label="${u("registry.PasswordOptional")}"
              style="padding-left:10px;"
              value="${(null===(s=this._registryList[this._selectedIndex])||void 0===s?void 0:s.password)||""}"
            ></mwc-textfield>
          </div>
          <mwc-select
            id="select-registry-type"
            label="${u("registry.RegistryType")}"
            @change=${this._toggleProjectNameInput}
            required
            validationMessage="${u("registry.PleaseSelectOption")}"
            value="${(null===(a=this._registryList[this._selectedIndex])||void 0===a?void 0:a.type)||this._registryType}"
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
              label="${u("registry.ProjectName")}"
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
            label=${this._editMode?u("button.Save"):u("button.Add")}
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
        <span slot="title">${u("dialog.warning.CannotBeUndone")}</span>
        <div slot="content">
          <mwc-textfield
            id="delete-registry"
            type="text"
            label="${u("registry.TypeRegistryNameToDelete")}"
          ></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            icon="delete"
            label="${u("button.Delete")}"
            @click=${()=>this._deleteRegistry()}
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};b._registryTypes=["docker","harbor","harbor2"],e([i("#list-status")],b.prototype,"_listStatus",void 0),e([i("#configure-registry-hostname")],b.prototype,"_hostnameInput",void 0),e([i("#configure-registry-password")],b.prototype,"_passwordInput",void 0),e([i("#configure-project-name")],b.prototype,"_projectNameInput",void 0),e([i("#select-registry-type")],b.prototype,"_selectedRegistryTypeInput",void 0),e([i("#configure-registry-url")],b.prototype,"_urlInput",void 0),e([i("#configure-registry-username")],b.prototype,"_usernameInput",void 0),b=y=e([s("backend-ai-registry-list")],b);let _=class extends a{constructor(){super(),this.resourcePolicy={},this.is_admin=!1,this.active=!1,this.gpu_allocatable=!1,this.gpuAllocationMode="device",this.condition="",this.presetName="",this.listCondition="loading",this._boundResourceRenderer=this.resourceRenderer.bind(this),this._boundControlRenderer=this.controlRenderer.bind(this)}static get styles(){return[o,r,n,c`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 199px);
          /* height: calc(100vh - 229px); */
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
        }

        mwc-textfield.yellow {
          --mdc-theme-primary: var(--paper-yellow-600) !important;
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
          border-bottom: 1px solid var(--token-colorBorder, #ddd);
        }
      `]}resourceRenderer(e,t,i){h(g`
        <div class="layout horizontal wrap center">
          <div class="layout horizontal configuration">
            <mwc-icon class="fg green">developer_board</mwc-icon>
            <span>
              ${this._markIfUnlimited(i.item.resource_slots.cpu)}
            </span>
            <span class="indicator">${u("general.cores")}</span>
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
      `,e)}_indexRenderer(e,t,i){const s=i.index+1;h(g`
        <div>${s}</div>
      `,e)}render(){return g`
      <div style="margin:0px;">
        <h4 class="horizontal flex center center-justified layout">
          <span>${u("resourcePreset.ResourcePresets")}</span>
          <span class="flex"></span>
          <mwc-button
            raised
            id="add-resource-preset"
            icon="add"
            label="${u("resourcePreset.CreatePreset")}"
            @click="${()=>this._launchPresetAddDialog()}"
          ></mwc-button>
        </h4>
        <div class="list-wrapper">
          <vaadin-grid
            theme="row-stripes column-borders compact dark"
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
              header="${u("resourcePreset.Name")}"
            ></vaadin-grid-sort-column>
            <vaadin-grid-column
              width="150px"
              resizable
              header="${u("resourcePreset.Resources")}"
              .renderer="${this._boundResourceRenderer}"
            ></vaadin-grid-column>
            <vaadin-grid-column
              resizable
              header="${u("general.Control")}"
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
        <span slot="title">${u("resourcePreset.ModifyResourcePreset")}</span>
        <div slot="content">
          <form id="login-form">
            <fieldset>
              <mwc-textfield
                type="text"
                name="preset_name"
                class="modify"
                id="id-preset-name"
                label="${u("resourcePreset.PresetName")}"
                auto-validate
                required
                disabled
                error-message="${u("data.Allowslettersnumbersand-_dot")}"
              ></mwc-textfield>
              <h4>${u("resourcePreset.ResourcePreset")}</h4>
              <div class="horizontal center layout">
                <mwc-textfield
                  id="cpu-resource"
                  class="modify"
                  type="number"
                  label="CPU"
                  min="1"
                  value="1"
                  required
                  validationMessage="${u("resourcePreset.MinimumCPUUnit")}"
                ></mwc-textfield>
                <mwc-textfield
                  id="ram-resource"
                  class="modify"
                  type="number"
                  label="${u("resourcePreset.RAM")}"
                  min="1"
                  value="1"
                  required
                  validationMessage="${u("resourcePreset.MinimumMemUnit")}"
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
                  label="${u("resourcePreset.SharedMemory")}"
                  min="0"
                  step="0.01"
                  validationMessage="${u("resourcePreset.MinimumShmemUnit")}"
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
            label="${u("button.SaveChanges")}"
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
        <span slot="title">${u("resourcePreset.CreateResourcePreset")}</span>
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
            placeholder="${u("maxLength.255chars")}"
            error-message="${u("data.Allowslettersnumbersand-_")}"
          ></mwc-textfield>
          <h4>${u("resourcePreset.ResourcePreset")}</h4>
          <div class="horizontal center layout">
            <mwc-textfield
              id="create-cpu-resource"
              class="create"
              type="number"
              label="CPU"
              min="1"
              value="1"
              required
              validationMessage="${u("resourcePreset.MinimumCPUUnit")}"
            ></mwc-textfield>
            <mwc-textfield
              id="create-ram-resource"
              class="create"
              type="number"
              label="${u("resourcePreset.RAM")}"
              min="1"
              value="1"
              required
              validationMessage="${u("resourcePreset.MinimumMemUnit")}"
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
              label="${u("resourcePreset.SharedMemory")}"
              min="0"
              step="0.01"
              validationMessage="${u("resourcePreset.MinimumShmemUnit")}"
            ></mwc-textfield>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            id="create-policy-button"
            icon="add"
            label="${u("button.Add")}"
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
        <span slot="title">${u("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${u("resourcePreset.AboutToDeletePreset")}</p>
          <p style="text-align:center;">${this.presetName}</p>
          <p>
            ${u("dialog.warning.CannotBeUndone")}
            ${u("dialog.ask.DoYouWantToProceed")}
          </p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            class="operation"
            label="${u("button.Cancel")}"
            @click="${e=>this._hideDialog(e)}"
          ></mwc-button>
          <mwc-button
            unelevated
            class="operation"
            label="${u("button.Okay")}"
            @click="${()=>this._deleteResourcePresetWithCheck()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}firstUpdated(){var e;this.notification=globalThis.lablupNotification;const t=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll("mwc-textfield");null==t||t.forEach((e=>{this._addInputValidator(e)}))}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._refreshTemplateData(),this.is_admin=globalThis.backendaiclient.is_admin}),!0):(this._refreshTemplateData(),this.is_admin=globalThis.backendaiclient.is_admin,globalThis.backendaiclient.get_resource_slots().then((e=>{this.gpu_allocatable=2!==Object.keys(e).length,Object.keys(e).includes("cuda.shares")?this.gpuAllocationMode="fractional":this.gpuAllocationMode="device"}))))}_launchPresetAddDialog(){this.createPresetDialog.show()}_launchResourcePresetDialog(e){this.updateCurrentPresetToDialog(e),this.modifyTemplateDialog.show()}_launchDeleteResourcePresetDialog(e){const t=e.target.closest("#controls")["preset-name"];this.presetName=t,this.deleteResourcePresetDialog.show()}_deleteResourcePresetWithCheck(){globalThis.backendaiclient.resourcePreset.delete(this.presetName).then((e=>{this.deleteResourcePresetDialog.hide(),this.notification.text=m("resourcePreset.Deleted"),this.notification.show(),this._refreshTemplateData()})).catch((e=>{console.log(e),e&&e.message&&(this.deleteResourcePresetDialog.hide(),this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}updateCurrentPresetToDialog(e){const t=e.target.closest("#controls")["preset-name"],i=globalThis.backendaiclient.utils.gqlToObject(this.resourcePresets,"name")[t];this.presetNameInput.value=t,this.cpuResourceInput.value=i.resource_slots.cpu,this.gpuResourceInput.value="cuda.device"in i.resource_slots?i.resource_slots["cuda.device"]:"",this.fgpuResourceInput.value="cuda.shares"in i.resource_slots?i.resource_slots["cuda.shares"]:"",this.ramResourceInput.value=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(i.resource_slots.mem,"g")).toString(),this.sharedMemoryResourceInput.value=i.shared_memory?parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(i.shared_memory,"g")).toFixed(2):""}_refreshTemplateData(){var e;const t={group:globalThis.backendaiclient.current_group};return this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.resourcePreset.check(t).then((e=>{var t;const i=e.presets;Object.keys(i).map(((e,t)=>{const s=i[e];s.resource_slots.mem_gib=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(s.resource_slots.mem,"g")),s.shared_memory?s.shared_memory_gib=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(s.shared_memory,"g")).toFixed(2):s.shared_memory_gib=null})),this.resourcePresets=i,0==this.resourcePresets.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}refresh(){this._refreshTemplateData()}_isActive(){return"active"===this.condition}_readResourcePresetInput(){const e=e=>void 0!==e&&e.includes("Unlimited")?"Infinity":e,t=e(this.cpuResourceInput.value),i=e(this.ramResourceInput.value+"g"),s=e(this.gpuResourceInput.value),a=e(this.fgpuResourceInput.value);let o=this.sharedMemoryResourceInput.value;o&&(o+="g");const r={cpu:t,mem:i};null!=s&&""!==s&&"0"!==s&&(r["cuda.device"]=parseInt(s)),null!=a&&""!==a&&"0"!==a&&(r["cuda.shares"]=parseFloat(a));return{resource_slots:JSON.stringify(r),shared_memory:o}}_modifyResourceTemplate(){if(!this._checkFieldValidity("modify"))return;const e=this.presetNameInput.value,t=void 0!==(i=this.ramResourceInput.value+"g")&&i.includes("Unlimited")?"Infinity":i;var i;if(!e)return this.notification.text=m("resourcePreset.NoPresetName"),void this.notification.show();const s=this._readResourcePresetInput();if(parseInt(s.shared_memory)>=parseInt(t))return this.notification.text=m("resourcePreset.MemoryShouldBeLargerThanSHMEM"),void this.notification.show();globalThis.backendaiclient.resourcePreset.mutate(e,s).then((e=>{this.modifyTemplateDialog.hide(),this.notification.text=m("resourcePreset.Updated"),this.notification.show(),this._refreshTemplateData()})).catch((e=>{console.log(e),e&&e.message&&(this.modifyTemplateDialog.hide(),this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_deleteKey(e){const t=e.target.closest("#controls").accessKey;globalThis.backendaiclient.keypair.delete(t).then((e=>{this.refresh()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=p.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_findKeyItem(e){return e.access_key=this}_elapsed(e,t){const i=new Date(e);let s;s=(this.condition,new Date);const a=Math.floor((s.getTime()-i.getTime())/1e3);return Math.floor(a/86400)}_humanReadableTime(e){return(e=new Date(e)).toUTCString()}_indexFrom1(e){return e+1}_markIfUnlimited(e){return["-",0,"Unlimited",1/0,"Infinity"].includes(e)?"∞":e}_checkFieldValidity(e=""){var t;const i='mwc-textfield[class^="'.concat(e).concat('"]'),s=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(i);let a=!0;for(const e of Array.from(s))if(a=e.checkValidity(),!a)return e.checkValidity();return a}_createPreset(){if(!this._checkFieldValidity("create"))return;const e=e=>void 0!==(e=e.toString())&&e.includes("Unlimited")?"Infinity":e,t=e(this.createPresetNameInput.value),i=e(this.createCpuResourceInput.value),s=e(this.createRamResourceInput.value+"g"),a=e(this.createGpuResourceInput.value),o=e(this.createFGpuResourceInput.value);let r=this.createSharedMemoryResourceInput.value;if(r&&(r+="g"),!t)return this.notification.text=m("resourcePreset.NoPresetName"),void this.notification.show();if(parseInt(r)>=parseInt(s))return this.notification.text=m("resourcePreset.MemoryShouldBeLargerThanSHMEM"),void this.notification.show();const n={cpu:i,mem:s};null!=a&&""!==a&&"0"!==a&&(n["cuda.device"]=parseInt(a)),null!=o&&""!==o&&"0"!==o&&(n["cuda.shares"]=parseFloat(o));const l={resource_slots:JSON.stringify(n),shared_memory:r};globalThis.backendaiclient.resourcePreset.add(t,l).then((e=>{this.createPresetDialog.hide(),e.create_resource_preset.ok?(this.notification.text=m("resourcePreset.Created"),this.refresh(),this.createPresetNameInput.value="",this.createCpuResourceInput.value="1",this.createRamResourceInput.value="1",this.createGpuResourceInput.value="0",this.createFGpuResourceInput.value="0",this.createSharedMemoryResourceInput.value=""):this.notification.text=p.relieve(e.create_resource_preset.msg),this.notification.show()}))}};e([t({type:Array})],_.prototype,"resourcePolicy",void 0),e([t({type:Boolean})],_.prototype,"is_admin",void 0),e([t({type:Boolean,reflect:!0})],_.prototype,"active",void 0),e([t({type:Boolean})],_.prototype,"gpu_allocatable",void 0),e([t({type:String})],_.prototype,"gpuAllocationMode",void 0),e([t({type:String})],_.prototype,"condition",void 0),e([t({type:String})],_.prototype,"presetName",void 0),e([t({type:Object})],_.prototype,"resourcePresets",void 0),e([t({type:String})],_.prototype,"listCondition",void 0),e([t({type:Array})],_.prototype,"_boundResourceRenderer",void 0),e([t({type:Array})],_.prototype,"_boundControlRenderer",void 0),e([i("#create-preset-name")],_.prototype,"createPresetNameInput",void 0),e([i("#create-cpu-resource")],_.prototype,"createCpuResourceInput",void 0),e([i("#create-ram-resource")],_.prototype,"createRamResourceInput",void 0),e([i("#create-gpu-resource")],_.prototype,"createGpuResourceInput",void 0),e([i("#create-fgpu-resource")],_.prototype,"createFGpuResourceInput",void 0),e([i("#create-shmem-resource")],_.prototype,"createSharedMemoryResourceInput",void 0),e([i("#cpu-resource")],_.prototype,"cpuResourceInput",void 0),e([i("#ram-resource")],_.prototype,"ramResourceInput",void 0),e([i("#gpu-resource")],_.prototype,"gpuResourceInput",void 0),e([i("#fgpu-resource")],_.prototype,"fgpuResourceInput",void 0),e([i("#shmem-resource")],_.prototype,"sharedMemoryResourceInput",void 0),e([i("#id-preset-name")],_.prototype,"presetNameInput",void 0),e([i("#create-preset-dialog")],_.prototype,"createPresetDialog",void 0),e([i("#modify-template-dialog")],_.prototype,"modifyTemplateDialog",void 0),e([i("#delete-resource-preset-dialog")],_.prototype,"deleteResourcePresetDialog",void 0),e([i("#list-status")],_.prototype,"_listStatus",void 0),_=e([s("backend-ai-resource-preset-list")],_);let f=class extends a{constructor(){super(...arguments),this.images=Object(),this.is_superadmin=!1,this.isSupportContainerRegistryGraphQL=!1,this._activeTab="image-lists"}static get styles(){return[o,r,n,c`
        div h4 {
          margin: 0;
          font-weight: 100;
          font-size: 16px;
          padding-left: 20px;
          border-bottom: 1px solid var(--token-colorBorder, #ccc);
          width: 100%;
        }

        @media screen and (max-width: 805px) {
          mwc-tab,
          mwc-button {
            --mdc-typography-button-font-size: 10px;
          }
        }
      `]}static get properties(){return{active:{type:Boolean},_activeTab:{type:String}}}async _viewStateChanged(e){var t;return await this.updateComplete,!1===e||(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{var e;this.is_superadmin=globalThis.backendaiclient.is_superadmin,this.isSupportContainerRegistryGraphQL=null===(e=globalThis.backendaiclient)||void 0===e?void 0:e.supports("container-registry-gql")}),!0):(this.is_superadmin=globalThis.backendaiclient.is_superadmin,this.isSupportContainerRegistryGraphQL=null===(t=globalThis.backendaiclient)||void 0===t?void 0:t.supports("container-registry-gql")),!1)}_showTab(e){var t,i;const s=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(let e=0;e<s.length;e++)s[e].style.display="none";this._activeTab=e.title,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e.title)).style.display="block"}render(){return g`
      <link rel="stylesheet" href="resources/custom.css" />
      <lablup-activity-panel noheader narrow autowidth>
        <div slot="message">
          <h3 class="tab horizontal center layout">
            <mwc-tab-bar>
              <mwc-tab
                title="image-lists"
                label="${u("environment.Images")}"
                @click="${e=>this._showTab(e.target)}"
              ></mwc-tab>
              <mwc-tab
                title="resource-template-lists"
                label="${u("environment.ResourcePresets")}"
                @click="${e=>this._showTab(e.target)}"
              ></mwc-tab>
              ${this.is_superadmin?g`
                    <mwc-tab
                      title="registry-lists"
                      label="${u("environment.Registries")}"
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
            ${this.isSupportContainerRegistryGraphQL&&"registry-lists"===this._activeTab?g`
                  <div class="flex" style="height:calc(100vh - 183px);">
                    <backend-ai-react-container-registry-list></backend-ai-react-container-registry-list>
                  </div>
                `:g`
                  <backend-ai-registry-list
                    ?active="${"registry-lists"===this._activeTab}"
                  ></backend-ai-registry-list>
                `}
          </div>
        </div>
      </lablup-activity-panel>
    `}};e([t({type:String})],f.prototype,"images",void 0),e([t({type:Boolean})],f.prototype,"is_superadmin",void 0),e([t({type:Boolean})],f.prototype,"isSupportContainerRegistryGraphQL",void 0),e([t({type:String})],f.prototype,"_activeTab",void 0),f=e([s("backend-ai-environment-view")],f);
