import{_ as t,n as s,b as e,e as i,B as a,c as o,I as r,a as n,i as l,f as d,m as c,x as p,t as u,g as _}from"./backend-ai-webui-45991858.js";import"./lablup-progress-bar-a35e300f.js";import"./mwc-switch-ae556d04.js";import"./vaadin-grid-9c58de6c.js";import"./vaadin-grid-sort-column-64ff581b.js";import"./backend-ai-list-status-3729db9d.js";import"./lablup-activity-panel-5f8f4051.js";import"./mwc-tab-bar-b2673269.js";import"./dir-utils-fd56b6df.js";let g=class extends a{constructor(){super(),this._enableAgentSchedulable=!1,this.condition="running",this.useHardwareMetadata=!1,this.agents=[],this.agentsObject=Object(),this.agentDetail=Object(),this.notification=Object(),this.agentDetailDialog=Object(),this.agentSettingDialog=Object(),this._boundEndpointRenderer=this.endpointRenderer.bind(this),this._boundResourceRenderer=this.resourceRenderer.bind(this),this._boundSchedulableRenderer=this.schedulableRenderer.bind(this),this.filter="",this.listCondition="loading"}static get styles(){return[o,r,n,l`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 182px);
        }

        .progress-bar-section {
          height: 20px;
        }

        .resource-indicator {
          width: 100px !important;
        }

        .agent-detail-title {
          font-size: 8px;
          width: 42px;
        }

        div.indicator,
        span.indicator {
          font-size: 9px;
          margin-right: 5px;
        }

        backend-ai-dialog#agent-detail {
          --component-max-width: 90%;
          --component-min-width: 400px;
        }

        backend-ai-dialog {
          --component-width: 350px;
        }

        img.indicator-icon {
          width: 16px !important;
          height: 16px !important;
        }

        lablup-progress-bar {
          --progress-bar-width: 70px;
          border-radius: 3px;
          height: 10px;
          --mdc-theme-primary: #3677eb;
          --mdc-linear-progress-buffer-color: #98be5a;
          margin-bottom: 0;
        }

        lablup-progress-bar.cpu {
          --progress-bar-height: 7px;
        }

        lablup-progress-bar.cuda {
          --progress-bar-width: 80px;
          --progress-bar-height: 15px;
          margin-bottom: 5px;
        }

        lablup-progress-bar.mem {
          --progress-bar-width: 100px;
          --progress-bar-height: 15px;
        }

        lablup-progress-bar.utilization {
          --progress-bar-width: 80px;
          margin-left: 10px;
        }

        lablup-shields {
          margin: 1px;
        }

        mwc-icon {
          --mdc-icon-size: 16px;
        }

        mwc-icon.schedulable {
          --mdc-icon-size: 24px;
        }

        vaadin-grid {
          border: 0;
          font-size: 14px;
        }
      `]}firstUpdated(){var t;this.notification=globalThis.lablupNotification,this.agentDetailDialog=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#agent-detail")}connectedCallback(){super.connectedCallback()}async _viewStateChanged(t){await this.updateComplete,!1!==t&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._enableAgentSchedulable=globalThis.backendaiclient.supports("schedulable"),this._loadAgentList()}),!0):(this._enableAgentSchedulable=globalThis.backendaiclient.supports("schedulable"),this._loadAgentList()))}_loadAgentList(){var t;if(!0!==this.active)return;this.listCondition="loading",null===(t=this._listStatus)||void 0===t||t.show();const s=["id","status","available_slots","occupied_slots","architecture"];globalThis.backendaiclient.supports("schedulable")&&s.push("schedulable");const e="running"===this.condition?"ALIVE":"TERMINATED";globalThis.backendaiclient.agentSummary.list(e,s,100,0,1e4).then((t=>{var s,e,i;const a=null===(s=t.agent_summary_list)||void 0===s?void 0:s.items;if(void 0!==a&&0!=a.length){let t;""!==this.filter&&(t=this.filter.split(":")),Object.keys(a).map(((s,e)=>{var i,o,r,n,l,d,c,p,u,_,g,m;const b=a[s];if(""===this.filter||t[0]in b&&b[t[0]]===t[1]){const t=JSON.parse(b.occupied_slots),e=JSON.parse(b.available_slots);["cpu","mem"].forEach((s=>{s in t==!1&&(t[s]="0")})),a[s].cpu_slots=parseInt(e.cpu),a[s].used_cpu_slots=parseInt(t.cpu),null!==b.cpu_cur_pct?(a[s].cpu_total_usage_ratio=a[s].used_cpu_slots/a[s].cpu_slots,a[s].total_cpu_percent=null===(i=100*a[s].cpu_total_usage_ratio)||void 0===i?void 0:i.toFixed(2)):(a[s].cpu_total_usage_ratio=0,a[s].total_cpu_percent=null===(o=100*a[s].cpu_total_usage_ratio)||void 0===o?void 0:o.toFixed(2)),a[s].mem_slots=parseInt(globalThis.backendaiclient.utils.changeBinaryUnit(e.mem,"g")),a[s].used_mem_slots=parseInt(globalThis.backendaiclient.utils.changeBinaryUnit(t.mem,"g")),a[s].mem_total_usage_ratio=a[s].used_mem_slots/a[s].mem_slots,a[s].total_mem_percent=null===(r=100*a[s].mem_total_usage_ratio)||void 0===r?void 0:r.toFixed(2),"cuda.device"in e&&(a[s].cuda_gpu_slots=parseInt(e["cuda.device"]),a[s].used_cuda_gpu_slots="cuda.device"in t?parseInt(t["cuda.device"]):0,a[s].used_cuda_gpu_slots_ratio=a[s].used_cuda_gpu_slots/a[s].cuda_gpu_slots,a[s].total_cuda_gpu_percent=null===(n=100*a[s].used_cuda_gpu_slots_ratio)||void 0===n?void 0:n.toFixed(2)),"cuda.shares"in e&&(a[s].cuda_fgpu_slots=null===(l=parseFloat(e["cuda.shares"]))||void 0===l?void 0:l.toFixed(2),a[s].used_cuda_fgpu_slots="cuda.shares"in t?null===(d=parseFloat(t["cuda.shares"]))||void 0===d?void 0:d.toFixed(2):0,a[s].used_cuda_fgpu_slots_ratio=a[s].used_cuda_fgpu_slots/a[s].cuda_fgpu_slots,a[s].total_cuda_fgpu_percent=null===(c=100*a[s].used_cuda_fgpu_slots_ratio)||void 0===c?void 0:c.toFixed(2)),"rocm.device"in e&&(a[s].rocm_gpu_slots=parseInt(e["rocm.device"]),a[s].used_rocm_gpu_slots="rocm.device"in t?parseInt(t["rocm.device"]):0,a[s].used_rocm_gpu_slots_ratio=a[s].used_rocm_gpu_slots/a[s].rocm_gpu_slots,a[s].total_rocm_gpu_percent=null===(p=100*a[s].used_rocm_gpu_slots_ratio)||void 0===p?void 0:p.toFixed(2)),"tpu.device"in e&&(a[s].tpu_slots=parseInt(e["tpu.device"]),a[s].used_tpu_slots="tpu.device"in t?parseInt(t["tpu.device"]):0,a[s].used_tpu_slots_ratio=a[s].used_tpu_slots/a[s].tpu_slots,a[s].total_tpu_percent=null===(u=100*a[s].used_tpu_slots_ratio)||void 0===u?void 0:u.toFixed(2)),"ipu.device"in e&&(a[s].ipu_slots=parseInt(e["ipu.device"]),a[s].used_ipu_slots="ipu.device"in t?parseInt(t["ipu.device"]):0,a[s].used_ipu_slots_ratio=a[s].used_ipu_slots/a[s].ipu_slots,a[s].total_ipu_percent=null===(_=100*a[s].used_ipu_slots_ratio)||void 0===_?void 0:_.toFixed(2)),"atom.device"in e&&(a[s].atom_slots=parseInt(e["atom.device"]),a[s].used_atom_slots="atom.device"in t?parseInt(t["atom.device"]):0,a[s].used_atom_slots_ratio=a[s].used_atom_slots/a[s].atom_slots,a[s].total_atom_percent=null===(g=100*a[s].used_atom_slots_ratio)||void 0===g?void 0:g.toFixed(2)),"warboy.device"in e&&(a[s].warboy_slots=parseInt(e["warboy.device"]),a[s].used_warboy_slots="warboy.device"in t?parseInt(t["warboy.device"]):0,a[s].used_warboy_slots_ratio=a[s].used_warboy_slots/a[s].warboy_slots,a[s].total_warboy_percent=null===(m=100*a[s].used_warboy_slots_ratio)||void 0===m?void 0:m.toFixed(2)),"schedulable"in b&&(a[s].schedulable=b.schedulable),this.agentsObject[a[s].id]=a[s]}}))}this.agents=a,this._agentGrid.recalculateColumnWidths(),0===(null===(e=this.agents)||void 0===e?void 0:e.length)?this.listCondition="no-data":null===(i=this._listStatus)||void 0===i||i.hide(),!0===this.active&&setTimeout((()=>{this._loadAgentList()}),15e3)})).catch((t=>{var s;null===(s=this._listStatus)||void 0===s||s.hide(),t&&t.message&&(console.log(t),this.notification.text=d.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))}))}_isRunning(){return"running"===this.condition}_indexRenderer(t,s,e){const i=e.index+1;c(p`
        <div>${i}</div>
      `,t)}endpointRenderer(t,s,e){c(p`
        <div style="white-space:pre-wrap;">${e.item.id}</div>
        <div class="indicator monospace" style="white-space:pre-wrap;">
          ${e.item.addr}
        </div>
      `,t)}resourceRenderer(t,s,e){c(p`
        <div class="layout flex">
          ${e.item.cpu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <mwc-icon class="fg green">developer_board</mwc-icon>
                    <span class="monospace" style="padding-left:5px;">
                      ${e.item.used_cpu_slots}/${e.item.cpu_slots}
                    </span>
                    <span class="indicator">${u("general.cores")}</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="cpu-usage-bar"
                    progress="${e.item.cpu_total_usage_ratio}"
                    description="${e.item.total_cpu_percent}%"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${e.item.mem_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <mwc-icon class="fg green">memory</mwc-icon>
                    <span class="monospace" style="padding-left:5px;">
                      ${e.item.used_mem_slots}/${e.item.mem_slots}
                    </span>
                    <span class="indicator">GiB</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="mem-usage-bar"
                    progress="${e.item.mem_total_usage_ratio}"
                    description="${e.item.total_mem_percent}%"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${e.item.cuda_gpu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/file_type_cuda.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${e.item.used_cuda_gpu_slots}/${e.item.cuda_gpu_slots}
                    </span>
                    <span class="indicator">GPU</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="gpu-bar"
                    progress="${e.item.used_cuda_gpu_slots_ratio}"
                    description="${e.item.total_cuda_gpu_percent}%"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${e.item.cuda_fgpu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/file_type_cuda.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${e.item.used_cuda_fgpu_slots}/${e.item.cuda_fgpu_slots}
                    </span>
                    <span class="indicator">fGPU</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="vgpu-bar"
                    progress="${e.item.used_cuda_fgpu_slots_ratio}"
                    description="${e.item.used_cuda_fgpu_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${e.item.rocm_gpu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/rocm.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${e.item.used_rocm_gpu_slots}/${e.item.rocm_gpu_slots}
                    </span>
                    <span class="indicator">ROCm</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="rocm-gpu-bar"
                    progress="${e.item.used_rocm_gpu_slots_ratio}"
                    description="${e.item.used_rocm_gpu_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${e.item.tpu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/tpu.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${e.item.used_tpu_slots}/${e.item.tpu_slots}
                    </span>
                    <span class="indicator">TPU</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="tpu-bar"
                    progress="${e.item.used_tpu_slots_ratio}"
                    description="${e.item.used_tpu_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${e.item.ipu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/tpu.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${e.item.used_ipu_slots}/${e.item.ipu_slots}
                    </span>
                    <span class="indicator">IPU</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="ipu-bar"
                    progress="${e.item.used_ipu_slots_ratio}"
                    description="${e.item.used_ipu_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${e.item.atom_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/tpu.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${e.item.used_atom_slots}/${e.item.atom_slots}
                    </span>
                    <span class="indicator">ATOM</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="atom-bar"
                    progress="${e.item.used_atom_slots_ratio}"
                    description="${e.item.used_atom_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${e.item.warboy_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/tpu.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${e.item.used_warboy_slots}/${e.item.warboy_slots}
                    </span>
                    <span class="indicator">Warboy</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="warboy-bar"
                    progress="${e.item.used_warboy_slots_ratio}"
                    description="${e.item.used_warboy_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
        </div>
      `,t)}schedulableRenderer(t,s,e){var i;c(p`
        <div class="layout horizontal center center-justified wrap">
          ${(null===(i=e.item)||void 0===i?void 0:i.schedulable)?p`
                <mwc-icon class="fg green schedulable">check_circle</mwc-icon>
              `:p`
                <mwc-icon class="fg red schedulable">block</mwc-icon>
              `}
        </div>
      `,t)}render(){return p`
      <div class="list-wrapper">
        <vaadin-grid
          class="${this.condition}"
          theme="row-stripes column-borders compact dark"
          aria-label="Job list"
          .items="${this.agents}"
        >
          <vaadin-grid-column
            width="30px"
            flex-grow="0"
            header="#"
            text-align="center"
            .renderer="${this._indexRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            resizable
            auto-width
            header="${u("agent.Endpoint")}"
            .renderer="${this._boundEndpointRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-sort-column
            auto-width
            resizable
            path="architecture"
            header="${u("agent.Architecture")}"
          ></vaadin-grid-sort-column>
          <vaadin-grid-column
            resizable
            auto-width
            header="${u("agent.Allocation")}"
            .renderer="${this._boundResourceRenderer}"
          ></vaadin-grid-column>
          ${this._enableAgentSchedulable?p`
                <vaadin-grid-column
                  auto-width
                  flex-grow="0"
                  resizable
                  header="${u("agent.Schedulable")}"
                  .renderer="${this._boundSchedulableRenderer}"
                ></vaadin-grid-column>
              `:p``}
        </vaadin-grid>
        <backend-ai-list-status
          id="list-status"
          statusCondition="${this.listCondition}"
          message="${_("agent.NoAgentToDisplay")}"
        ></backend-ai-list-status>
      </div>
    `}};t([s({type:String})],g.prototype,"condition",void 0),t([s({type:Boolean})],g.prototype,"useHardwareMetadata",void 0),t([s({type:Array})],g.prototype,"agents",void 0),t([s({type:Object})],g.prototype,"agentsObject",void 0),t([s({type:Object})],g.prototype,"agentDetail",void 0),t([s({type:Object})],g.prototype,"notification",void 0),t([s({type:Object})],g.prototype,"agentDetailDialog",void 0),t([s({type:Object})],g.prototype,"agentSettingDialog",void 0),t([s({type:Object})],g.prototype,"_boundEndpointRenderer",void 0),t([s({type:Object})],g.prototype,"_boundResourceRenderer",void 0),t([s({type:Object})],g.prototype,"_boundSchedulableRenderer",void 0),t([s({type:String})],g.prototype,"filter",void 0),t([s({type:String})],g.prototype,"listCondition",void 0),t([e("#list-status")],g.prototype,"_listStatus",void 0),t([e("vaadin-grid")],g.prototype,"_agentGrid",void 0),g=t([i("backend-ai-agent-summary-list")],g);let m=class extends a{constructor(){super(),this._status="inactive",this._tab="running-lists",this.hideAgents=!0}static get styles(){return[o,l`
        @media screen and (max-width: 805px) {
          mwc-tab {
            --mdc-typography-button-font-size: 10px;
          }
        }
      `]}async _viewStateChanged(t){var s,e,i,a;if(await this.updateComplete,!t)return(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#running-agents")).active=!1,(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#terminated-agents")).active=!1,void(this._status="inactive");(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#running-agents")).active=!0,(null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#terminated-agents")).active=!0,this._status="active"}_showTab(t){var s,e;const i=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelectorAll(".tab-content");for(let t=0;t<i.length;t++)i[t].style.display="none";(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#"+t.title)).style.display="block",this._tab=t.title}render(){return p`
      <link rel="stylesheet" href="resources/custom.css" />
      <lablup-activity-panel noheader narrow autowidth>
        <div slot="message">
          <h3 class="tab horizontal center layout">
            <mwc-tab-bar>
              <mwc-tab
                title="running-lists"
                label="${u("agent.Connected")}"
                @click="${t=>this._showTab(t.target)}"
              ></mwc-tab>
              <mwc-tab
                title="terminated-lists"
                label="${u("agent.Terminated")}"
                @click="${t=>this._showTab(t.target)}"
              ></mwc-tab>
            </mwc-tab-bar>
            <div class="flex"></div>
          </h3>
          <div id="running-lists" class="tab-content">
            <backend-ai-agent-summary-list
              id="running-agents"
              condition="running"
              ?active="${"active"===this._status&&"running-lists"===this._tab}"
            ></backend-ai-agent-summary-list>
          </div>
          <div id="terminated-lists" class="tab-content" style="display:none;">
            <backend-ai-agent-summary-list
              id="terminated-agents"
              condition="terminated"
              ?active="${"active"===this._status&&"terminated-lists"===this._tab}"
            ></backend-ai-agent-summary-list>
          </div>
        </div>
      </lablup-activity-panel>
    `}};t([s({type:String})],m.prototype,"_status",void 0),t([s({type:String})],m.prototype,"_tab",void 0),t([s({type:Boolean})],m.prototype,"hideAgents",void 0),m=t([i("backend-ai-agent-summary-view")],m);
