import{_ as e,n as t,b as s,e as r,B as i,c as o,I as a,a as c,m as l,d as n,i as p,g as d,f as u,x as _,t as h}from"./backend-ai-webui-75df15ed.js";import"./lablup-progress-bar-b230f3e3.js";import"./backend-ai-session-launcher-676818a7.js";import"./mwc-switch-13f7c132.js";let g=class extends i{constructor(){super(),this.is_connected=!1,this.direction="horizontal",this.location="",this.aliases=Object(),this.aggregate_updating=!1,this.project_resource_monitor=!1,this.active=!1,this.resourceBroker=globalThis.resourceBroker,this.notification=globalThis.lablupNotification,this.init_resource()}static get is(){return"backend-ai-resource-monitor"}static get styles(){return[o,a,c,l,n,p`
        mwc-linear-progress {
          height: 5px;
          --mdc-theme-primary: #98be5a;
        }

        .horizontal-panel lablup-progress-bar {
          --progress-bar-width: 90px;
        }

        .vertical-panel lablup-progress-bar {
          --progress-bar-width: 186px;
        }

        .horizontal-card {
          width: auto;
        }

        .horizontal-panel mwc-linear-progress {
          width: 90px;
        }

        .vertical-panel mwc-linear-progress {
          width: 186px;
        }

        #scaling-group-select-box.horizontal {
          min-height: 80px;
          min-width: 252px;
          margin: 0;
          padding: 0;
        }

        #scaling-group-select-box.vertical {
          padding: 10px 20px;
          min-height: 83px; /* 103px-20px */
          background-color: #f6f6f6;
        }

        #scaling-group-select-box.horizontal mwc-select {
          width: 250px;
          height: 58px;
        }

        #scaling-group-select-box.vertical mwc-select {
          width: 305px;
          height: 58px;
        }

        .vertical-panel #resource-gauges {
          min-height: 200px;
        }

        mwc-linear-progress.project-bar {
          height: 15px;
        }

        mwc-linear-progress.start-bar {
          border-top-left-radius: 3px;
          border-top-right-radius: 3px;
          --mdc-theme-primary: #3677eb;
        }

        mwc-linear-progress.middle-bar {
          --mdc-theme-primary: #4f8b46;
        }

        mwc-linear-progress.end-bar {
          border-bottom-left-radius: 3px;
          border-bottom-right-radius: 3px;
          --mdc-theme-primary: #98be5a;
        }

        mwc-linear-progress.full-bar {
          border-radius: 3px;
          height: 10px;
        }

        .resources.horizontal .short-indicator mwc-linear-progress {
          width: 50px;
        }

        .resources.horizontal .short-indicator {
          width: 50px;
        }
        span.caption {
          width: 30px;
          display: block;
          font-size: 12px;
          padding-left: 10px;
        }

        div.caption {
          font-size: 12px;
          width: 100px;
        }

        #resource-gauges.horizontal {
          /* left: 160px; */
          /* width: 420px; */
          width: auto;
          height: auto;
          background-color: transparent;
        }

        mwc-icon {
          --icon-size: 24px;
        }

        img.resource-type-icon {
          width: 24px;
          height: 24px;
        }

        @media screen and (max-width: 749px) {
          #resource-gauge-toggle.horizontal {
            display: flex;
          }

          #resource-gauge-toggle.vertical {
            display: none;
          }

          #resource-gauges.horizontal {
            display: none;
          }

          #resource-gauges.vertical {
            display: flex;
          }
        }

        @media screen and (min-width: 750px) {
          #resource-gauge-toggle {
            display: none;
          }

          #resource-gauges.horizontal,
          #resource-gauges.vertical {
            display: flex;
          }
        }

        .indicator {
          font-family: monospace;
        }

        .resource-button {
          height: 140px;
          width: 120px;
          margin: 5px;
          padding: 0;
          font-size: 14px;
        }

        #new-session-dialog {
          z-index: 100;
        }

        #scaling-group-select-box mwc-select {
          border: 0.1em solid #ccc;
          font-family: var(--general-font-family);
          --mdc-typography-subtitle1-font-family: var(--general-font-family);
          --mdc-typography-subtitle1-font-size: 14px;
          --mdc-typography-subtitle1-font-color: rgb(24, 24, 24);
          --mdc-typography-subtitle1-font-weight: 400;
          --mdc-typography-subtitle1-line-height: 16px;
          --mdc-select-fill-color: rgba(255, 255, 255, 1);
          --mdc-select-label-ink-color: rgba(24, 24, 24, 1);
          --mdc-select-disabled-ink-color: rgba(24, 24, 24, 1);
          --mdc-select-dropdown-icon-color: rgba(24, 24, 24, 1);
          --mdc-select-focused-dropdown-icon-color: rgba(24, 24, 24, 0.87);
          --mdc-select-disabled-dropdown-icon-color: rgba(24, 24, 24, 0.87);
          --mdc-select-idle-line-color: transparent;
          --mdc-select-hover-line-color: transparent;
          --mdc-select-ink-color: rgb(24, 24, 24);
          --mdc-select-outlined-idle-border-color: rgba(24, 24, 24, 0.42);
          --mdc-select-outlined-hover-border-color: rgba(24, 24, 24, 0.87);
          --mdc-theme-surface: white;
          --mdc-list-vertical-padding: 5px;
          --mdc-list-side-padding: 10px;
          --mdc-menu-item-height: 28px;
          --mdc-list-item__primary-text: {
            height: 20px;
            color: #222222;
          };
          margin-bottom: 5px;
        }

        #scaling-group-select {
          width: 305px;
          height: 55px;
          --mdc-select-outlined-idle-border-color: #dddddd;
          --mdc-select-outlined-hover-border-color: #dddddd;
          background-color: white !important;
          border-radius: 5px;
        }

        .resource-button h4 {
          padding: 5px 0;
          margin: 0;
          font-weight: 400;
        }

        .resource-button ul {
          padding: 0;
          list-style-type: none;
        }

        .resources .monitor {
          margin-bottom: 15px;
        }

        .resources.vertical .monitor,
        .resources.horizontal .monitor {
          margin-bottom: 10px;
        }

        mwc-select {
          width: 100%;
          font-family: var(--general-font-family);
          --mdc-typography-subtitle1-font-family: var(--general-font-family);
          --mdc-theme-primary: var(--general-sidebar-color);
          --mdc-select-fill-color: transparent;
          --mdc-select-label-ink-color: rgba(0, 0, 0, 0.75);
          --mdc-select-dropdown-icon-color: rgba(255, 0, 0, 0.87);
          --mdc-select-focused-dropdown-icon-color: rgba(255, 0, 0, 0.42);
          --mdc-select-disabled-dropdown-icon-color: rgba(255, 0, 0, 0.87);
          --mdc-select-idle-line-color: rgba(0, 0, 0, 0.42);
          --mdc-select-hover-line-color: rgba(255, 0, 0, 0.87);
          --mdc-select-outlined-idle-border-color: rgba(255, 0, 0, 0.42);
          --mdc-select-outlined-hover-border-color: rgba(255, 0, 0, 0.87);
          --mdc-theme-surface: white;
          --mdc-list-vertical-padding: 5px;
          --mdc-list-side-padding: 25px;
          --mdc-list-item__primary-text: {
            height: 20px;
          };
        }

        div.mdc-select__anchor {
          background-color: white !important;
        }

        mwc-textfield {
          width: 100%;
          --mdc-text-field-idle-line-color: rgba(0, 0, 0, 0.42);
          --mdc-text-field-hover-line-color: rgba(255, 0, 0, 0.87);
          --mdc-text-field-fill-color: transparent;
          --mdc-theme-primary: var(--paper-red-600);
        }

        mwc-textfield#session-name {
          width: 50%;
          padding-top: 20px;
          padding-left: 0;
          margin-left: 0;
          margin-bottom: 1px;
        }

        .vertical-card > #resource-gauges > .monitor > .resource-name {
          width: 60px;
        }

        .horizontal-card > #resource-gauges {
          display: grid !important;
          grid-auto-flow: row;
          grid-template-columns: repeat(auto-fill, 320px);
          justify-content: center;
        }

        @media screen and (min-width: 750px) {
          div#resource-gauges {
            display: flex !important;
          }
        }

        @media screen and (max-width: 1015px) {
          .horizontal-panel lablup-progress-bar {
            --progress-bar-width: 8rem;
          }

          div#resource-gauges {
            justify-content: center;
          }
        }
      `]}init_resource(){this.total_slot={},this.total_resource_group_slot={},this.total_project_slot={},this.used_slot={},this.used_resource_group_slot={},this.used_project_slot={},this.available_slot={},this.used_slot_percent={},this.used_resource_group_slot_percent={},this.used_project_slot_percent={},this.concurrency_used=0,this.concurrency_max=0,this.concurrency_limit=0,this._status="inactive",this.scaling_groups=[{name:""}],this.scaling_group="",this.sessions_list=[],this.metric_updating=!1,this.metadata_updating=!1}firstUpdated(){new ResizeObserver((()=>{this._updateToggleResourceMonitorDisplay()})).observe(this.resourceGauge),document.addEventListener("backend-ai-group-changed",(e=>{this.scaling_group="",this._updatePageVariables(!0)})),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_connected=!0,setInterval((()=>{this._periodicUpdateResourcePolicy()}),2e4)}),{once:!0}):this.is_connected=!0,document.addEventListener("backend-ai-session-list-refreshed",(()=>{this._updatePageVariables(!0)}))}async _periodicUpdateResourcePolicy(){return this.active?(await this._refreshResourcePolicy(),this.aggregateResource("refresh-resource-policy"),Promise.resolve(!0)):Promise.resolve(!1)}async updateScalingGroup(e=!1,t){await this.resourceBroker.updateScalingGroup(e,t.target.value),this.active&&("vertical"===this.direction&&this.scalingGroupSelectBox.firstChild&&(this.scalingGroupSelectBox.firstChild.value=this.resourceBroker.scaling_group),!0===e&&(await this._refreshResourcePolicy(),this.aggregateResource("update-scaling-group")))}async _viewStateChanged(e){await this.updateComplete,this.active&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,this._updatePageVariables(!0)}),{once:!0}):(this.project_resource_monitor=this.resourceBroker.allow_project_resource_monitor,await this._updatePageVariables(!0)))}async _updatePageVariables(e){return this.active&&!1===this.metadata_updating?(this.metadata_updating=!0,await this.resourceBroker._updatePageVariables(e),setTimeout((()=>{this._updateScalingGroupSelector()}),1e3),this.sessions_list=this.resourceBroker.sessions_list,await this._refreshResourcePolicy(),this.aggregateResource("update-page-variable"),this.metadata_updating=!1,Promise.resolve(!0)):Promise.resolve(!1)}_updateToggleResourceMonitorDisplay(){var e,t;const s=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#resource-legend"),r=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#resource-gauge-toggle-button");document.body.clientWidth>750&&"horizontal"==this.direction?(s.style.display="flex",Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="flex"}))):r.selected?(s.style.display="flex",document.body.clientWidth<750&&(this.resourceGauge.style.left="20px",this.resourceGauge.style.right="20px"),Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="flex"}))):(Array.from(this.resourceGauge.children).forEach((e=>{e.style.display="none"})),s.style.display="none")}_updateScalingGroupSelector(){this.scalingGroupSelectBox.hasChildNodes()&&this.scalingGroupSelectBox.firstChild&&this.scalingGroupSelectBox.removeChild(this.scalingGroupSelectBox.firstChild);const e=document.createElement("mwc-select");e.label=d("session.launcher.ResourceGroup"),e.id="scaling-group-select",e.value=this.scaling_group,e.setAttribute("fullwidth","true"),e.style.margin="1px solid #ccc",e.addEventListener("selected",this.updateScalingGroup.bind(this,!0));let t=document.createElement("mwc-list-item");t.setAttribute("disabled","true"),t.innerHTML=d("session.launcher.SelectResourceGroup"),t.style.borderBottom="1px solid #ccc",e.appendChild(t);const s=e.value?e.value:this.resourceBroker.scaling_group;this.resourceBroker.scaling_groups.map((r=>{t=document.createElement("mwc-list-item"),t.value=r.name,t.setAttribute("graphic","icon"),s===r.name?t.selected=!0:t.selected=!1,t.innerHTML=r.name,e.appendChild(t)})),this.scalingGroupSelectBox.appendChild(e)}async _refreshResourcePolicy(e=!1){return this.active?this.resourceBroker._refreshResourcePolicy().then((()=>(this.concurrency_used=this.resourceBroker.concurrency_used,this.concurrency_max=this.concurrency_used>this.resourceBroker.concurrency_max?this.concurrency_used:this.resourceBroker.concurrency_max,Promise.resolve(!0)))).catch((e=>(this.metadata_updating=!1,e&&e.message?(this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=u.relieve(e.title),this.notification.show(!0,e)),Promise.resolve(!1)))):Promise.resolve(!0)}_aliasName(e){const t=this.resourceBroker.imageTagAlias,s=this.resourceBroker.imageTagReplace;for(const[t,r]of Object.entries(s)){const s=new RegExp(t);if(s.test(e))return e.replace(s,r)}return e in t?t[e]:e}async _aggregateResourceUse(e=""){return this.resourceBroker._aggregateCurrentResource(e).then((t=>!1===t?setTimeout((()=>{this._aggregateResourceUse(e)}),1e3):(this.concurrency_used=this.resourceBroker.concurrency_used,this.scaling_group=this.resourceBroker.scaling_group,this.scaling_groups=this.resourceBroker.scaling_groups,this.total_slot=this.resourceBroker.total_slot,this.total_resource_group_slot=this.resourceBroker.total_resource_group_slot,this.total_project_slot=this.resourceBroker.total_project_slot,this.used_slot=this.resourceBroker.used_slot,this.used_resource_group_slot=this.resourceBroker.used_resource_group_slot,this.used_project_slot=this.resourceBroker.used_project_slot,this.used_project_slot_percent=this.resourceBroker.used_project_slot_percent,this.concurrency_limit=this.resourceBroker.concurrency_limit,this.available_slot=this.resourceBroker.available_slot,this.used_slot_percent=this.resourceBroker.used_slot_percent,this.used_resource_group_slot_percent=this.resourceBroker.used_resource_group_slot_percent,Promise.resolve(!0)))).then((()=>Promise.resolve(!0))).catch((e=>(e&&e.message&&(console.log(e),this.notification.text=u.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)),Promise.resolve(!1))))}aggregateResource(e=""){void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._aggregateResourceUse(e)}),!0):this._aggregateResourceUse(e)}_numberWithPostfix(e,t=""){return isNaN(parseInt(e))?"":parseInt(e)+t}render(){return _`
      <link rel="stylesheet" href="resources/custom.css">
      <div class="layout ${this.direction} justified flex wrap">
      <div id="scaling-group-select-box" class="layout horizontal center-justified ${this.direction}"></div>
      <div class="layout ${this.direction}-card flex wrap">
        <div id="resource-gauges" class="layout ${this.direction} ${this.direction}-panel resources flex wrap">
          <div class="layout horizontal center-justified monitor">
            <div class="layout vertical center center-justified resource-name">
              <div class="gauge-name">CPU</div>
            </div>
            <div class="layout vertical start-justified wrap">
              <lablup-progress-bar id="cpu-usage-bar" class="start"
                progress="${this.used_resource_group_slot_percent.cpu/100}"
                description="${this.used_resource_group_slot.cpu}/${this.total_resource_group_slot.cpu}"></lablup-progress-bar>
              <lablup-progress-bar id="cpu-usage-bar-2" class="end"
                progress="${this.used_slot_percent.cpu/100}"
                description="${this.used_slot.cpu}/${this.total_slot.cpu}"></lablup-progress-bar>
            </div>
            <div class="layout vertical center center-justified">
              <span class="percentage start-bar">${this._numberWithPostfix(this.used_resource_group_slot_percent.cpu,"%")}</span>
              <span class="percentage end-bar">${this._numberWithPostfix(this.used_slot_percent.cpu,"%")}</span>
            </div>
          </div>
          <div class="layout horizontal center-justified monitor">
            <div class="layout vertical center center-justified resource-name">
              <span class="gauge-name">RAM</span>
            </div>
            <div class="layout vertical start-justified wrap">
              <lablup-progress-bar id="mem-usage-bar" class="start"
                progress="${this.used_resource_group_slot_percent.mem/100}"
                description="${this.used_resource_group_slot.mem}/${this.total_resource_group_slot.mem}GiB"></lablup-progress-bar>
              <lablup-progress-bar id="mem-usage-bar-2" class="end"
                progress="${this.used_slot_percent.mem/100}"
                description="${this.used_slot.mem}/${this.total_slot.mem}GiB"
              ></lablup-progress-bar>
            </div>
            <div class="layout vertical center center-justified">
              <span class="percentage start-bar">${this._numberWithPostfix(this.used_resource_group_slot_percent.mem,"%")}</span>
              <span class="percentage end-bar">${this._numberWithPostfix(this.used_slot_percent.mem,"%")}</span>
            </div>
          </div>
          ${this.total_slot.cuda_device?_`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">GPU</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="gpu-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot.cuda_device/this.total_resource_group_slot.cuda_device}"
                        description="${this.used_resource_group_slot.cuda_device}/${this.total_resource_group_slot.cuda_device}"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="gpu-usage-bar-2"
                        class="end"
                        progress="${this.used_slot.cuda_device}/${this.total_slot.cuda_device}"
                        description="${this.used_slot.cuda_device}/${this.total_slot.cuda_device}"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this.used_resource_group_slot_percent.cuda_device,"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this.used_slot_percent.cuda_device,"%")}
                      </span>
                    </div>
                  </div>
                `:_``}
          ${this.resourceBroker.total_slot.cuda_shares&&this.resourceBroker.total_slot.cuda_shares>0?_`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">FGPU</span>
                    </div>
                    <div class="layout vertical start-justified wrap">
                      <lablup-progress-bar
                        id="fgpu-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot.cuda_shares/this.total_resource_group_slot.cuda_shares}"
                        description="${this.used_resource_group_slot.cuda_shares}/${this.total_resource_group_slot.cuda_shares}"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="fgpu-usage-bar-2"
                        class="end"
                        progress="${this.used_slot.cuda_shares/this.total_slot.cuda_shares}"
                        description="${this.used_slot.cuda_shares}/${this.total_slot.cuda_shares}"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this.used_resource_group_slot_percent.cuda_shares,"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this.used_slot_percent.cuda_shares,"%")}
                      </span>
                    </div>
                  </div>
                `:_``}
          ${this.total_slot.rocm_device?_`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <img
                        class="resource-type-icon fg green"
                        src="/resources/icons/ROCm.png"
                      />
                      <span class="gauge-name">
                        ROCm
                        <br />
                        GPU
                      </span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="rocm-gpu-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.rocm_device/100}"
                        description="${this.used_resource_group_slot.rocm_device}/${this.total_resource_group_slot.rocm_device}"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="rocm-gpu-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.rocm_device_slot/100}"
                        buffer="${this.used_slot_percent.rocm_device_slot/100}"
                        description="${this.used_slot.rocm_device_slot}/${this.total_slot.rocm_device_slot}"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this.used_resource_group_slot_percent.rocm_device_slot,"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this.used_slot_percent.rocm_device_slot,"%")}
                      </span>
                    </div>
                  </div>
                `:_``}
          ${this.total_slot.tpu_device?_`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">TPU</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="tpu-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.tpu_device/100}"
                        description="${this.used_resource_group_slot.tpu_device}/${this.total_resource_group_slot.tpu_device}"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="tpu-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.tpu_device/100}"
                        buffer="${this.used_slot_percent.tpu_device/100}"
                        description="${this.used_slot.tpu_device}/${this.total_slot.tpu_device}"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this.used_resource_group_slot_percent.tpu_device,"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this.used_slot_percent.tpu_device,"%")}
                      </span>
                    </div>
                  </div>
                `:_``}
          ${this.total_slot.ipu_device?_`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">IPU</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="ipu-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.ipu_device/100}"
                        description="${this.used_resource_group_slot.ipu_device}/${this.total_resource_group_slot.ipu_device}"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="ipu-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.ipu_device/100}"
                        buffer="${this.used_slot_percent.ipu_device/100}"
                        description="${this.used_slot.ipu_device}/${this.total_slot.ipu_device}"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this.used_resource_group_slot_percent.ipu_device,"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this.used_slot_percent.ipu_device,"%")}
                      </span>
                    </div>
                  </div>
                `:_``}
          ${this.total_slot.atom_device?_`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">ATOM</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="atom-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.atom_device/100}"
                        description="${this.used_resource_group_slot.atom_device}/${this.total_resource_group_slot.atom_device}"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="atom-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.atom_device/100}"
                        buffer="${this.used_slot_percent.atom_device/100}"
                        description="${this.used_slot.atom_device}/${this.total_slot.atom_device}"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this.used_resource_group_slot_percent.atom_device,"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this.used_slot_percent.atom_device,"%")}
                      </span>
                    </div>
                  </div>
                `:_``}
          ${this.total_slot.warboy_device?_`
                  <div class="layout horizontal center-justified monitor">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <span class="gauge-name">Warboy</span>
                    </div>
                    <div class="layout vertical center-justified wrap">
                      <lablup-progress-bar
                        id="warboy-usage-bar"
                        class="start"
                        progress="${this.used_resource_group_slot_percent.warboy_device/100}"
                        description="${this.used_resource_group_slot.warboy_device}/${this.total_resource_group_slot.warboy_device}"
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="warboy-usage-bar-2"
                        class="end"
                        progress="${this.used_slot_percent.warboy_device/100}"
                        buffer="${this.used_slot_percent.warboy_device/100}"
                        description="${this.used_slot.warboy_device}/${this.total_slot.warboy_device}"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this._numberWithPostfix(this.used_resource_group_slot_percent.warboy_device,"%")}
                      </span>
                      <span class="percentage end-bar">
                        ${this._numberWithPostfix(this.used_slot_percent.warboy_device,"%")}
                      </span>
                    </div>
                  </div>
                `:_``}
          <div class="layout horizontal center-justified monitor">
            <div class="layout vertical center center-justified resource-name">
              <span class="gauge-name">${h("session.launcher.Sessions")}</span>
            </div>
            <div class="layout vertical center-justified wrap">
              <lablup-progress-bar id="concurrency-usage-bar" class="start"
                progress="${this.used_slot_percent.concurrency/100}"
                description="${this.concurrency_used}/${1e6===this.concurrency_max?"∞":parseInt(this.concurrency_max)}"
                ></lablup-progress-bar>
            </div>
            <div class="layout vertical center center-justified">
              <span class="percentage end-bar" style="margin-top:0px;">${this._numberWithPostfix(this.used_slot_percent.concurrency,"%")}</span>
            </div>
          </div>
        </div>
        <div class="layout horizontal center end-justified" id="resource-gauge-toggle">
          <p style="font-size:12px;color:#242424;margin-right:10px;">
            ${h("session.launcher.ResourceMonitorToggle")}
          </p>
          <mwc-switch selected class="${this.direction}" id="resource-gauge-toggle-button" @click="${()=>this._updateToggleResourceMonitorDisplay()}">
          </mwc-switch>
        </div>
      </div>
      </div>
      <div class="vertical start-justified layout ${this.direction}-card" id="resource-legend">
        <div class="layout horizontal center ${"vertical"===this.direction?"start-justified":"end-justified"}
                    resource-legend-stack">
          <div class="resource-legend-icon start"></div>
          <span class="resource-legend">${h("session.launcher.CurrentResourceGroup")} (${this.scaling_group})</span>
        </div>
        <div class="layout horizontal center ${"vertical"===this.direction?"start-justified":"end-justified"}"">
          <div class="resource-legend-icon end"></div>
          <span class="resource-legend">${h("session.launcher.UserResourceLimit")}</span>
        </div>
      </div>
      ${"vertical"===this.direction&&!0===this.project_resource_monitor&&(this.total_project_slot.cpu>0||this.total_project_slot.cpu===1/0)?_`
              <hr />
              <div class="vertical start-justified layout">
                <div class="flex"></div>
                <div class="layout horizontal center-justified monitor">
                  <div
                    class="layout vertical center center-justified"
                    style="margin-right:5px;"
                  >
                    <mwc-icon class="fg blue">group_work</mwc-icon>
                    <span class="gauge-name">
                      ${h("session.launcher.Project")}
                    </span>
                  </div>
                  <div
                    class="layout vertical start-justified wrap short-indicator"
                  >
                    <div class="layout horizontal">
                      <span
                        style="width:35px; margin-left:5px; margin-right:5px;"
                      >
                        CPU
                      </span>
                      <lablup-progress-bar
                        id="cpu-project-usage-bar"
                        class="start"
                        progress="${this.used_project_slot_percent.cpu/100}"
                        description="${this.used_project_slot.cpu}/${this.total_project_slot.cpu===1/0?"∞":this.total_project_slot.cpu}"
                      ></lablup-progress-bar>
                      <div class="layout vertical center center-justified">
                        <span class="percentage start-bar">
                          ${this._numberWithPostfix(this.used_project_slot_percent.cpu,"%")}
                        </span>
                        <span class="percentage end-bar">
                          ${this._numberWithPostfix(this.total_project_slot.cpu,"%")}
                        </span>
                      </div>
                    </div>
                    <div class="layout horizontal">
                      <span
                        style="width:35px;margin-left:5px; margin-right:5px;"
                      >
                        RAM
                      </span>
                      <lablup-progress-bar
                        id="mem-project-usage-bar"
                        class="end"
                        progress="${this.used_project_slot_percent.mem/100}"
                        description=">${this.used_project_slot.mem}/${this.total_project_slot.mem===1/0?"∞":this.total_project_slot.mem}"
                      ></lablup-progress-bar>
                      <div class="layout vertical center center-justified">
                        <span class="percentage start-bar">
                          ${this._numberWithPostfix(this.used_project_slot_percent.mem,"%")}
                        </span>
                        <span class="percentage end-bar">
                          ${this._numberWithPostfix(this.total_project_slot.mem,"%")}
                        </span>
                      </div>
                    </div>
                    ${this.total_project_slot.cuda_device?_`
                          <div class="layout horizontal">
                            <span
                              style="width:35px;margin-left:5px; margin-right:5px;"
                            >
                              GPU
                            </span>
                            <lablup-progress-bar
                              id="gpu-project-usage-bar"
                              class="end"
                              progress="${this.used_project_slot_percent.cuda_device/100}"
                              description="${this.used_project_slot.cuda_device}/${"Infinity"===this.total_project_slot.cuda_device?"∞":this.total_project_slot.cuda_device}"
                            ></lablup-progress-bar>
                            <div
                              class="layout vertical center center-justified"
                            >
                              <span class="percentage start-bar">
                                ${this._numberWithPostfix(this.used_project_slot_percent.cuda_device,"%")}
                              </span>
                              <span class="percentage end-bar">
                                ${this._numberWithPostfix(this.total_project_slot.cuda_device,"%")}
                              </span>
                            </div>
                          </div>
                        `:_``}
                    ${this.total_project_slot.cuda_shares?_`
                          <div class="layout horizontal">
                            <span
                              style="width:35px;margin-left:5px; margin-right:5px;"
                            >
                              FGPU
                            </span>
                            <lablup-progress-bar
                              id="fgpu-project-usage-bar"
                              class="end"
                              progress="${this.used_project_slot_percent.cuda_shares/100}"
                              description="${this.used_project_slot.cuda_shares}/${"Infinity"===this.total_project_slot.cuda_shares?"∞":this.total_project_slot.cuda_shares}"
                            ></lablup-progress-bar>
                            <div
                              class="layout vertical center center-justified"
                            >
                              <span class="percentage start-bar">
                                ${this._numberWithPostfix(this.used_project_slot_percent.cuda_shares,"%")}
                              </span>
                              <span class="percentage end-bar">
                                ${this._numberWithPostfix(this.total_project_slot.cuda_shares,"%")}
                              </span>
                            </div>
                          </div>
                        `:_``}
                    ${this.total_project_slot.rocm_device?_`
                          <div class="layout horizontal">
                            <span
                              style="width:35px;margin-left:5px; margin-right:5px;"
                            >
                              GPU
                            </span>
                            <lablup-progress-bar
                              id="rocm-project-usage-bar"
                              class="end"
                              progress="${this.used_project_slot_percent.rocm_device/100}"
                              description="${this.used_project_slot.rocm_device}/${"Infinity"===this.total_project_slot.rocm_device?"∞":this.total_project_slot.rocm_device}"
                            ></lablup-progress-bar>
                            <div
                              class="layout vertical center center-justified"
                            >
                              <span class="percentage start-bar">
                                ${this._numberWithPostfix(this.used_project_slot_percent.rocm_device,"%")}
                              </span>
                              <span class="percentage end-bar">
                                ${this._numberWithPostfix(this.total_project_slot.rocm_device,"%")}
                              </span>
                            </div>
                          </div>
                        `:_``}
                    ${this.total_project_slot.tpu_device?_`
                          <div class="layout horizontal">
                            <span
                              style="width:35px;margin-left:5px; margin-right:5px;"
                            >
                              GPU
                            </span>
                            <lablup-progress-bar
                              id="tpu-project-usage-bar"
                              class="end"
                              progress="${this.used_project_slot_percent.tpu_device/100}"
                              description="${this.used_project_slot.tpu_device}/${"Infinity"===this.total_project_slot.tpu_device?"∞":this.total_project_slot.tpu_device}"
                            ></lablup-progress-bar>
                            <div
                              class="layout vertical center center-justified"
                            >
                              <span class="percentage start-bar">
                                ${this._numberWithPostfix(this.used_project_slot_percent.tpu_device,"%")}
                              </span>
                              <span class="percentage end-bar">
                                ${this._numberWithPostfix(this.total_project_slot.tpu_device,"%")}
                              </span>
                            </div>
                          </div>
                        `:_``}
                    ${this.total_project_slot.ipu_device?_`
                          <div class="layout horizontal">
                            <span
                              style="width:35px;margin-left:5px; margin-right:5px;"
                            >
                              IPU
                            </span>
                            <lablup-progress-bar
                              id="ipu-project-usage-bar"
                              class="end"
                              progress="${this.used_project_slot_percent.ipu_device/100}"
                              description="${this.used_project_slot.ipu_device}/${"Infinity"===this.total_project_slot.ipu_device?"∞":this.total_project_slot.ipu_device}"
                            ></lablup-progress-bar>
                            <div
                              class="layout vertical center center-justified"
                            >
                              <span class="percentage start-bar">
                                ${this._numberWithPostfix(this.used_project_slot_percent.ipu_device,"%")}
                              </span>
                              <span class="percentage end-bar">
                                ${this._numberWithPostfix(this.total_project_slot.ipu_device,"%")}
                              </span>
                            </div>
                          </div>
                        `:_``}
                    ${this.total_project_slot.atom_device?_`
                          <div class="layout horizontal">
                            <span
                              style="width:35px;margin-left:5px; margin-right:5px;"
                            >
                              ATOM
                            </span>
                            <lablup-progress-bar
                              id="tpu-project-usage-bar"
                              class="end"
                              progress="${this.used_project_slot_percent.atom_device/100}"
                              description="${this.used_project_slot.atom_device}/${"Infinity"===this.total_project_slot.atom_device?"∞":this.total_project_slot.atom_device}"
                            ></lablup-progress-bar>
                            <div
                              class="layout vertical center center-justified"
                            >
                              <span class="percentage start-bar">
                                ${this._numberWithPostfix(this.used_project_slot_percent.atom_device,"%")}
                              </span>
                              <span class="percentage end-bar">
                                ${this._numberWithPostfix(this.total_project_slot.atom_device,"%")}
                              </span>
                            </div>
                          </div>
                        `:_``}
                    ${this.total_project_slot.warboy_device?_`
                          <div class="layout horizontal">
                            <span
                              style="width:35px;margin-left:5px; margin-right:5px;"
                            >
                              Warboy
                            </span>
                            <lablup-progress-bar
                              id="tpu-project-usage-bar"
                              class="end"
                              progress="${this.used_project_slot_percent.warboy_device/100}"
                              description="${this.used_project_slot.warboy_device}/${"Infinity"===this.total_project_slot.warboy_device?"∞":this.total_project_slot.warboy_device}"
                            ></lablup-progress-bar>
                            <div
                              class="layout vertical center center-justified"
                            >
                              <span class="percentage start-bar">
                                ${this._numberWithPostfix(this.used_project_slot_percent.warboy_device,"%")}
                              </span>
                              <span class="percentage end-bar">
                                ${this._numberWithPostfix(this.total_project_slot.warboy_device,"%")}
                              </span>
                            </div>
                          </div>
                        `:_``}
                  </div>
                  <div class="flex"></div>
                </div>
              </div>
            `:_``}
`}};e([t({type:Boolean})],g.prototype,"is_connected",void 0),e([t({type:String})],g.prototype,"direction",void 0),e([t({type:String})],g.prototype,"location",void 0),e([t({type:Object})],g.prototype,"aliases",void 0),e([t({type:Object})],g.prototype,"total_slot",void 0),e([t({type:Object})],g.prototype,"total_resource_group_slot",void 0),e([t({type:Object})],g.prototype,"total_project_slot",void 0),e([t({type:Object})],g.prototype,"used_slot",void 0),e([t({type:Object})],g.prototype,"used_resource_group_slot",void 0),e([t({type:Object})],g.prototype,"used_project_slot",void 0),e([t({type:Object})],g.prototype,"available_slot",void 0),e([t({type:Number})],g.prototype,"concurrency_used",void 0),e([t({type:Number})],g.prototype,"concurrency_max",void 0),e([t({type:Number})],g.prototype,"concurrency_limit",void 0),e([t({type:Object})],g.prototype,"used_slot_percent",void 0),e([t({type:Object})],g.prototype,"used_resource_group_slot_percent",void 0),e([t({type:Object})],g.prototype,"used_project_slot_percent",void 0),e([t({type:String})],g.prototype,"default_language",void 0),e([t({type:Boolean})],g.prototype,"_status",void 0),e([t({type:Number})],g.prototype,"num_sessions",void 0),e([t({type:String})],g.prototype,"scaling_group",void 0),e([t({type:Array})],g.prototype,"scaling_groups",void 0),e([t({type:Array})],g.prototype,"sessions_list",void 0),e([t({type:Boolean})],g.prototype,"metric_updating",void 0),e([t({type:Boolean})],g.prototype,"metadata_updating",void 0),e([t({type:Boolean})],g.prototype,"aggregate_updating",void 0),e([t({type:Object})],g.prototype,"scaling_group_selection_box",void 0),e([t({type:Boolean})],g.prototype,"project_resource_monitor",void 0),e([t({type:Object})],g.prototype,"resourceBroker",void 0),e([s("#resource-gauges")],g.prototype,"resourceGauge",void 0),e([s("#scaling-group-select-box")],g.prototype,"scalingGroupSelectBox",void 0),g=e([r("backend-ai-resource-monitor")],g);
