import{_ as t,n as e,b as s,e as i,B as a,c as o,I as r,a as n,i as l,f as d,l as c,x as p,t as u,g as _}from"./backend-ai-webui-75df15ed.js";import"./lablup-progress-bar-b230f3e3.js";import"./mwc-switch-13f7c132.js";import"./vaadin-grid-461d199a.js";import"./vaadin-grid-sort-column-d722536e.js";import"./backend-ai-list-status-fa13c15b.js";import"./lablup-activity-panel-86e1deef.js";import"./mwc-tab-bar-45ba859c.js";import"./dir-utils-f5050166.js";let g=class extends a{constructor(){super(),this._enableAgentSchedulable=!1,this.condition="running",this.useHardwareMetadata=!1,this.agents=[],this.agentsObject=Object(),this.agentDetail=Object(),this.notification=Object(),this.agentDetailDialog=Object(),this.agentSettingDialog=Object(),this._boundEndpointRenderer=this.endpointRenderer.bind(this),this._boundResourceRenderer=this.resourceRenderer.bind(this),this._boundSchedulableRenderer=this.schedulableRenderer.bind(this),this.filter="",this.listCondition="loading"}static get styles(){return[o,r,n,l`
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
      `]}firstUpdated(){var t;this.notification=globalThis.lablupNotification,this.agentDetailDialog=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#agent-detail")}connectedCallback(){super.connectedCallback()}async _viewStateChanged(t){await this.updateComplete,!1!==t&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._enableAgentSchedulable=globalThis.backendaiclient.supports("schedulable"),this._loadAgentList()}),!0):(this._enableAgentSchedulable=globalThis.backendaiclient.supports("schedulable"),this._loadAgentList()))}_loadAgentList(){var t;if(!0!==this.active)return;this.listCondition="loading",null===(t=this._listStatus)||void 0===t||t.show();const e=["id","status","available_slots","occupied_slots","architecture"];globalThis.backendaiclient.supports("schedulable")&&e.push("schedulable");const s="running"===this.condition?"ALIVE":"TERMINATED";globalThis.backendaiclient.agentSummary.list(s,e,100,0,1e4).then((t=>{var e,s,i;const a=null===(e=t.agent_summary_list)||void 0===e?void 0:e.items;if(void 0!==a&&0!=a.length){let t;""!==this.filter&&(t=this.filter.split(":")),Object.keys(a).map(((e,s)=>{var i,o,r,n,l,d,c,p,u,_,g,b;const m=a[e];if(""===this.filter||t[0]in m&&m[t[0]]===t[1]){const t=JSON.parse(m.occupied_slots),s=JSON.parse(m.available_slots);["cpu","mem"].forEach((e=>{e in t==!1&&(t[e]="0")})),a[e].cpu_slots=parseInt(s.cpu),a[e].used_cpu_slots=parseInt(t.cpu),null!==m.cpu_cur_pct?(a[e].cpu_total_usage_ratio=a[e].used_cpu_slots/a[e].cpu_slots,a[e].total_cpu_percent=null===(i=100*a[e].cpu_total_usage_ratio)||void 0===i?void 0:i.toFixed(2)):(a[e].cpu_total_usage_ratio=0,a[e].total_cpu_percent=null===(o=100*a[e].cpu_total_usage_ratio)||void 0===o?void 0:o.toFixed(2)),a[e].mem_slots=parseInt(globalThis.backendaiclient.utils.changeBinaryUnit(s.mem,"g")),a[e].used_mem_slots=parseInt(globalThis.backendaiclient.utils.changeBinaryUnit(t.mem,"g")),a[e].mem_total_usage_ratio=a[e].used_mem_slots/a[e].mem_slots,a[e].total_mem_percent=null===(r=100*a[e].mem_total_usage_ratio)||void 0===r?void 0:r.toFixed(2),"cuda.device"in s&&(a[e].cuda_gpu_slots=parseInt(s["cuda.device"]),a[e].used_cuda_gpu_slots="cuda.device"in t?parseInt(t["cuda.device"]):0,a[e].used_cuda_gpu_slots_ratio=a[e].used_cuda_gpu_slots/a[e].cuda_gpu_slots,a[e].total_cuda_gpu_percent=null===(n=100*a[e].used_cuda_gpu_slots_ratio)||void 0===n?void 0:n.toFixed(2)),"cuda.shares"in s&&(a[e].cuda_fgpu_slots=null===(l=parseFloat(s["cuda.shares"]))||void 0===l?void 0:l.toFixed(2),a[e].used_cuda_fgpu_slots="cuda.shares"in t?null===(d=parseFloat(t["cuda.shares"]))||void 0===d?void 0:d.toFixed(2):0,a[e].used_cuda_fgpu_slots_ratio=a[e].used_cuda_fgpu_slots/a[e].cuda_fgpu_slots,a[e].total_cuda_fgpu_percent=null===(c=100*a[e].used_cuda_fgpu_slots_ratio)||void 0===c?void 0:c.toFixed(2)),"rocm.device"in s&&(a[e].rocm_gpu_slots=parseInt(s["rocm.device"]),a[e].used_rocm_gpu_slots="rocm.device"in t?parseInt(t["rocm.device"]):0,a[e].used_rocm_gpu_slots_ratio=a[e].used_rocm_gpu_slots/a[e].rocm_gpu_slots,a[e].total_rocm_gpu_percent=null===(p=100*a[e].used_rocm_gpu_slots_ratio)||void 0===p?void 0:p.toFixed(2)),"tpu.device"in s&&(a[e].tpu_slots=parseInt(s["tpu.device"]),a[e].used_tpu_slots="tpu.device"in t?parseInt(t["tpu.device"]):0,a[e].used_tpu_slots_ratio=a[e].used_tpu_slots/a[e].tpu_slots,a[e].total_tpu_percent=null===(u=100*a[e].used_tpu_slots_ratio)||void 0===u?void 0:u.toFixed(2)),"ipu.device"in s&&(a[e].ipu_slots=parseInt(s["ipu.device"]),a[e].used_ipu_slots="ipu.device"in t?parseInt(t["ipu.device"]):0,a[e].used_ipu_slots_ratio=a[e].used_ipu_slots/a[e].ipu_slots,a[e].total_ipu_percent=null===(_=100*a[e].used_ipu_slots_ratio)||void 0===_?void 0:_.toFixed(2)),"atom.device"in s&&(a[e].atom_slots=parseInt(s["atom.device"]),a[e].used_atom_slots="atom.device"in t?parseInt(t["atom.device"]):0,a[e].used_atom_slots_ratio=a[e].used_atom_slots/a[e].atom_slots,a[e].total_atom_percent=null===(g=100*a[e].used_atom_slots_ratio)||void 0===g?void 0:g.toFixed(2)),"warboy.device"in s&&(a[e].warboy_slots=parseInt(s["warboy.device"]),a[e].used_warboy_slots="warboy.device"in t?parseInt(t["warboy.device"]):0,a[e].used_warboy_slots_ratio=a[e].used_warboy_slots/a[e].warboy_slots,a[e].total_warboy_percent=null===(b=100*a[e].used_warboy_slots_ratio)||void 0===b?void 0:b.toFixed(2)),"schedulable"in m&&(a[e].schedulable=m.schedulable),this.agentsObject[a[e].id]=a[e]}}))}this.agents=a,this._agentGrid.recalculateColumnWidths(),0===(null===(s=this.agents)||void 0===s?void 0:s.length)?this.listCondition="no-data":null===(i=this._listStatus)||void 0===i||i.hide(),!0===this.active&&setTimeout((()=>{this._loadAgentList()}),15e3)})).catch((t=>{var e;null===(e=this._listStatus)||void 0===e||e.hide(),t&&t.message&&(console.log(t),this.notification.text=d.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))}))}_isRunning(){return"running"===this.condition}_indexRenderer(t,e,s){const i=s.index+1;c(p`
        <div>${i}</div>
      `,t)}endpointRenderer(t,e,s){c(p`
        <div style="white-space:pre-wrap;">${s.item.id}</div>
        <div class="indicator monospace" style="white-space:pre-wrap;">
          ${s.item.addr}
        </div>
      `,t)}resourceRenderer(t,e,s){c(p`
        <div class="layout flex">
          ${s.item.cpu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <mwc-icon class="fg green">developer_board</mwc-icon>
                    <span class="monospace" style="padding-left:5px;">
                      ${s.item.used_cpu_slots}/${s.item.cpu_slots}
                    </span>
                    <span class="indicator">${u("general.cores")}</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="cpu-usage-bar"
                    progress="${s.item.cpu_total_usage_ratio}"
                    description="${s.item.total_cpu_percent}%"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${s.item.mem_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <mwc-icon class="fg green">memory</mwc-icon>
                    <span class="monospace" style="padding-left:5px;">
                      ${s.item.used_mem_slots}/${s.item.mem_slots}
                    </span>
                    <span class="indicator">GiB</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="mem-usage-bar"
                    progress="${s.item.mem_total_usage_ratio}"
                    description="${s.item.total_mem_percent}%"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${s.item.cuda_gpu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/file_type_cuda.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${s.item.used_cuda_gpu_slots}/${s.item.cuda_gpu_slots}
                    </span>
                    <span class="indicator">GPU</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="gpu-bar"
                    progress="${s.item.used_cuda_gpu_slots_ratio}"
                    description="${s.item.total_cuda_gpu_percent}%"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${s.item.cuda_fgpu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/file_type_cuda.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${s.item.used_cuda_fgpu_slots}/${s.item.cuda_fgpu_slots}
                    </span>
                    <span class="indicator">fGPU</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="vgpu-bar"
                    progress="${s.item.used_cuda_fgpu_slots_ratio}"
                    description="${s.item.used_cuda_fgpu_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${s.item.rocm_gpu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/ROCm.png"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${s.item.used_rocm_gpu_slots}/${s.item.rocm_gpu_slots}
                    </span>
                    <span class="indicator">ROCm</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="rocm-gpu-bar"
                    progress="${s.item.used_rocm_gpu_slots_ratio}"
                    description="${s.item.used_rocm_gpu_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${s.item.tpu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/tpu.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${s.item.used_tpu_slots}/${s.item.tpu_slots}
                    </span>
                    <span class="indicator">TPU</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="tpu-bar"
                    progress="${s.item.used_tpu_slots_ratio}"
                    description="${s.item.used_tpu_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${s.item.ipu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/tpu.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${s.item.used_ipu_slots}/${s.item.ipu_slots}
                    </span>
                    <span class="indicator">IPU</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="ipu-bar"
                    progress="${s.item.used_ipu_slots_ratio}"
                    description="${s.item.used_ipu_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${s.item.atom_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/tpu.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${s.item.used_atom_slots}/${s.item.atom_slots}
                    </span>
                    <span class="indicator">ATOM</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="atom-bar"
                    progress="${s.item.used_atom_slots_ratio}"
                    description="${s.item.used_atom_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
          ${s.item.warboy_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/tpu.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${s.item.used_warboy_slots}/${s.item.warboy_slots}
                    </span>
                    <span class="indicator">Warboy</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="warboy-bar"
                    progress="${s.item.used_warboy_slots_ratio}"
                    description="${s.item.used_warboy_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
        </div>
      `,t)}schedulableRenderer(t,e,s){var i;c(p`
        <div class="layout horizontal center center-justified wrap">
          ${(null===(i=s.item)||void 0===i?void 0:i.schedulable)?p`
                <mwc-icon class="fg green schedulable">check_circle</mwc-icon>
              `:p`
                <mwc-icon class="fg red schedulable">block</mwc-icon>
              `}
        </div>
      `,t)}render(){return p`
      <div class="list-wrapper">
        <vaadin-grid
          class="${this.condition}"
          theme="row-stripes column-borders compact"
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
    `}};t([e({type:String})],g.prototype,"condition",void 0),t([e({type:Boolean})],g.prototype,"useHardwareMetadata",void 0),t([e({type:Array})],g.prototype,"agents",void 0),t([e({type:Object})],g.prototype,"agentsObject",void 0),t([e({type:Object})],g.prototype,"agentDetail",void 0),t([e({type:Object})],g.prototype,"notification",void 0),t([e({type:Object})],g.prototype,"agentDetailDialog",void 0),t([e({type:Object})],g.prototype,"agentSettingDialog",void 0),t([e({type:Object})],g.prototype,"_boundEndpointRenderer",void 0),t([e({type:Object})],g.prototype,"_boundResourceRenderer",void 0),t([e({type:Object})],g.prototype,"_boundSchedulableRenderer",void 0),t([e({type:String})],g.prototype,"filter",void 0),t([e({type:String})],g.prototype,"listCondition",void 0),t([s("#list-status")],g.prototype,"_listStatus",void 0),t([s("vaadin-grid")],g.prototype,"_agentGrid",void 0),g=t([i("backend-ai-agent-summary-list")],g);let b=class extends a{constructor(){super(),this._status="inactive",this._tab="running-lists",this.hideAgents=!0}static get styles(){return[o,l`
        h3.tab {
          background-color: var(--general-tabbar-background-color);
          border-radius: 5px 5px 0 0;
          margin: 0 auto;
        }

        mwc-tab-bar {
          --mdc-theme-primary: var(--general-sidebar-selected-color);
          --mdc-text-transform: none;
          --mdc-tab-color-default: var(--general-tabbar-background-color);
          --mdc-tab-text-label-color-default: var(
            --general-tabbar-tab-disabled-color
          );
        }

        @media screen and (max-width: 805px) {
          mwc-tab {
            --mdc-typography-button-font-size: 10px;
          }
        }
      `]}async _viewStateChanged(t){var e,s,i,a;if(await this.updateComplete,!t)return(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#running-agents")).active=!1,(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#terminated-agents")).active=!1,void(this._status="inactive");(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#running-agents")).active=!0,(null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#terminated-agents")).active=!0,this._status="active"}_showTab(t){var e,s;const i=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll(".tab-content");for(let t=0;t<i.length;t++)i[t].style.display="none";(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#"+t.title)).style.display="block",this._tab=t.title}render(){return p`
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
    `}};t([e({type:String})],b.prototype,"_status",void 0),t([e({type:String})],b.prototype,"_tab",void 0),t([e({type:Boolean})],b.prototype,"hideAgents",void 0),b=t([i("backend-ai-agent-summary-view")],b);
