import{_ as e,n as t,e as s,t as i,B as a,b as o,I as r,a as l,i as n,d,p as c,x as p,f as u,g as _}from"./backend-ai-webui-CHZ-bl4E.js";import"./lablup-progress-bar-uZGTrT3Q.js";import"./mwc-switch-BjHJLnvp.js";import"./vaadin-grid-BPP02Fg2.js";import"./vaadin-grid-sort-column-D98JUghL.js";import"./backend-ai-list-status-D8Jm1azR.js";import"./lablup-activity-panel-BRVLvaCu.js";import"./mwc-tab-bar-DNic7EoY.js";import"./dir-utils-Oo-ABbXC.js";let g=class extends a{constructor(){super(),this._enableAgentSchedulable=!1,this.condition="running",this.useHardwareMetadata=!1,this.agents=[],this.agentsObject=Object(),this.agentDetail=Object(),this.notification=Object(),this.agentDetailDialog=Object(),this.agentSettingDialog=Object(),this._boundEndpointRenderer=this.endpointRenderer.bind(this),this._boundResourceRenderer=this.resourceRenderer.bind(this),this._boundSchedulableRenderer=this.schedulableRenderer.bind(this),this.filter="",this.listCondition="loading"}static get styles(){return[o,r,l,n`
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
      `]}firstUpdated(){var e;this.notification=globalThis.lablupNotification,this.agentDetailDialog=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#agent-detail")}connectedCallback(){super.connectedCallback()}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._enableAgentSchedulable=globalThis.backendaiclient.supports("schedulable"),this._loadAgentList()}),!0):(this._enableAgentSchedulable=globalThis.backendaiclient.supports("schedulable"),this._loadAgentList()))}_loadAgentList(){var e;if(!0!==this.active)return;this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show();const t=["id","status","available_slots","occupied_slots","architecture"];globalThis.backendaiclient.supports("schedulable")&&t.push("schedulable");const s="running"===this.condition?"ALIVE":"TERMINATED";globalThis.backendaiclient.agentSummary.list(s,t,100,0,1e4).then((e=>{var t,s,i;const a=null===(t=e.agent_summary_list)||void 0===t?void 0:t.items;if(void 0!==a&&0!=a.length){let e;""!==this.filter&&(e=this.filter.split(":")),Object.keys(a).map(((t,s)=>{var i,o,r,l,n,d,c,p,u,_,g,m,b;const h=a[t];if(""===this.filter||e[0]in h&&h[e[0]]===e[1]){const e=JSON.parse(h.occupied_slots),s=JSON.parse(h.available_slots);["cpu","mem"].forEach((t=>{t in e==!1&&(e[t]="0")})),a[t].cpu_slots=parseInt(s.cpu),a[t].used_cpu_slots=parseInt(e.cpu),null!==h.cpu_cur_pct?(a[t].cpu_total_usage_ratio=a[t].used_cpu_slots/a[t].cpu_slots,a[t].total_cpu_percent=null===(i=100*a[t].cpu_total_usage_ratio)||void 0===i?void 0:i.toFixed(2)):(a[t].cpu_total_usage_ratio=0,a[t].total_cpu_percent=null===(o=100*a[t].cpu_total_usage_ratio)||void 0===o?void 0:o.toFixed(2)),a[t].mem_slots=parseInt(globalThis.backendaiclient.utils.changeBinaryUnit(s.mem,"g")),a[t].used_mem_slots=parseInt(globalThis.backendaiclient.utils.changeBinaryUnit(e.mem,"g")),a[t].mem_total_usage_ratio=a[t].used_mem_slots/a[t].mem_slots,a[t].total_mem_percent=null===(r=100*a[t].mem_total_usage_ratio)||void 0===r?void 0:r.toFixed(2),"cuda.device"in s&&(a[t].cuda_gpu_slots=parseInt(s["cuda.device"]),a[t].used_cuda_gpu_slots="cuda.device"in e?parseInt(e["cuda.device"]):0,a[t].used_cuda_gpu_slots_ratio=a[t].used_cuda_gpu_slots/a[t].cuda_gpu_slots,a[t].total_cuda_gpu_percent=null===(l=100*a[t].used_cuda_gpu_slots_ratio)||void 0===l?void 0:l.toFixed(2)),"cuda.shares"in s&&(a[t].cuda_fgpu_slots=null===(n=parseFloat(s["cuda.shares"]))||void 0===n?void 0:n.toFixed(2),a[t].used_cuda_fgpu_slots="cuda.shares"in e?null===(d=parseFloat(e["cuda.shares"]))||void 0===d?void 0:d.toFixed(2):0,a[t].used_cuda_fgpu_slots_ratio=a[t].used_cuda_fgpu_slots/a[t].cuda_fgpu_slots,a[t].total_cuda_fgpu_percent=null===(c=100*a[t].used_cuda_fgpu_slots_ratio)||void 0===c?void 0:c.toFixed(2)),"rocm.device"in s&&(a[t].rocm_gpu_slots=parseInt(s["rocm.device"]),a[t].used_rocm_gpu_slots="rocm.device"in e?parseInt(e["rocm.device"]):0,a[t].used_rocm_gpu_slots_ratio=a[t].used_rocm_gpu_slots/a[t].rocm_gpu_slots,a[t].total_rocm_gpu_percent=null===(p=100*a[t].used_rocm_gpu_slots_ratio)||void 0===p?void 0:p.toFixed(2)),"tpu.device"in s&&(a[t].tpu_slots=parseInt(s["tpu.device"]),a[t].used_tpu_slots="tpu.device"in e?parseInt(e["tpu.device"]):0,a[t].used_tpu_slots_ratio=a[t].used_tpu_slots/a[t].tpu_slots,a[t].total_tpu_percent=null===(u=100*a[t].used_tpu_slots_ratio)||void 0===u?void 0:u.toFixed(2)),"ipu.device"in s&&(a[t].ipu_slots=parseInt(s["ipu.device"]),a[t].used_ipu_slots="ipu.device"in e?parseInt(e["ipu.device"]):0,a[t].used_ipu_slots_ratio=a[t].used_ipu_slots/a[t].ipu_slots,a[t].total_ipu_percent=null===(_=100*a[t].used_ipu_slots_ratio)||void 0===_?void 0:_.toFixed(2)),"atom.device"in s&&(a[t].atom_slots=parseInt(s["atom.device"]),a[t].used_atom_slots="atom.device"in e?parseInt(e["atom.device"]):0,a[t].used_atom_slots_ratio=a[t].used_atom_slots/a[t].atom_slots,a[t].total_atom_percent=null===(g=100*a[t].used_atom_slots_ratio)||void 0===g?void 0:g.toFixed(2)),"warboy.device"in s&&(a[t].warboy_slots=parseInt(s["warboy.device"]),a[t].used_warboy_slots="warboy.device"in e?parseInt(e["warboy.device"]):0,a[t].used_warboy_slots_ratio=a[t].used_warboy_slots/a[t].warboy_slots,a[t].total_warboy_percent=null===(m=100*a[t].used_warboy_slots_ratio)||void 0===m?void 0:m.toFixed(2)),"hyperaccel-lpu.device"in s&&(a[t].hyperaccel_lpu_slots=parseInt(s["hyperaccel-lpu.device"]),a[t].used_hyperaccel_lpu_slots="hyperaccel-lpu.device"in e?parseInt(e["hyperaccel-lpu.device"]):0,a[t].used_hyperaccel_lpu_slots_ratio=a[t].used_hyperaccel_lpu_slots/a[t].hyperaccel_lpu_slots,a[t].total_hyperaccel_lpu_percent=null===(b=100*a[t].used_hyperaccel_lpu_slots_ratio)||void 0===b?void 0:b.toFixed(2)),"schedulable"in h&&(a[t].schedulable=h.schedulable),this.agentsObject[a[t].id]=a[t]}}))}this.agents=a,this._agentGrid.recalculateColumnWidths(),0===(null===(s=this.agents)||void 0===s?void 0:s.length)?this.listCondition="no-data":null===(i=this._listStatus)||void 0===i||i.hide(),!0===this.active&&setTimeout((()=>{this._loadAgentList()}),15e3)})).catch((e=>{var t;null===(t=this._listStatus)||void 0===t||t.hide(),e&&e.message&&(console.log(e),this.notification.text=d.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_isRunning(){return"running"===this.condition}_indexRenderer(e,t,s){const i=s.index+1;c(p`
        <div>${i}</div>
      `,e)}endpointRenderer(e,t,s){c(p`
        <div style="white-space:pre-wrap;">${s.item.id}</div>
        <div class="indicator monospace" style="white-space:pre-wrap;">
          ${s.item.addr}
        </div>
      `,e)}resourceRenderer(e,t,s){c(p`
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
                      src="/resources/icons/rocm.svg"
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
          ${s.item.hyperaccel_lpu_slots?p`
                <div
                  class="layout horizontal center-justified flex progress-bar-section"
                >
                  <div class="layout horizontal start resource-indicator">
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/npu_generic.svg"
                    />
                    <span class="monospace" style="padding-left:5px;">
                      ${s.item.used_hyperaccel_lpu_slots}/${s.item.hyperaccel_lpu_slots}
                    </span>
                    <span class="indicator">Hyperaccel LPU</span>
                  </div>
                  <span class="flex"></span>
                  <lablup-progress-bar
                    id="hyperaccel-lpu-bar"
                    progress="${s.item.used_hyperaccel_lpu_slots_ratio}"
                    description="${s.item.used_hyperaccel_lpu_slots}"
                  ></lablup-progress-bar>
                </div>
              `:p``}
        </div>
      `,e)}schedulableRenderer(e,t,s){var i;c(p`
        <div class="layout horizontal center center-justified wrap">
          ${(null===(i=s.item)||void 0===i?void 0:i.schedulable)?p`
                <mwc-icon class="fg green schedulable">check_circle</mwc-icon>
              `:p`
                <mwc-icon class="fg red schedulable">block</mwc-icon>
              `}
        </div>
      `,e)}render(){return p`
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
    `}};e([t({type:String})],g.prototype,"condition",void 0),e([t({type:Boolean})],g.prototype,"useHardwareMetadata",void 0),e([t({type:Array})],g.prototype,"agents",void 0),e([t({type:Object})],g.prototype,"agentsObject",void 0),e([t({type:Object})],g.prototype,"agentDetail",void 0),e([t({type:Object})],g.prototype,"notification",void 0),e([t({type:Object})],g.prototype,"agentDetailDialog",void 0),e([t({type:Object})],g.prototype,"agentSettingDialog",void 0),e([t({type:Object})],g.prototype,"_boundEndpointRenderer",void 0),e([t({type:Object})],g.prototype,"_boundResourceRenderer",void 0),e([t({type:Object})],g.prototype,"_boundSchedulableRenderer",void 0),e([t({type:String})],g.prototype,"filter",void 0),e([t({type:String})],g.prototype,"listCondition",void 0),e([s("#list-status")],g.prototype,"_listStatus",void 0),e([s("vaadin-grid")],g.prototype,"_agentGrid",void 0),g=e([i("backend-ai-agent-summary-list")],g);let m=class extends a{constructor(){super(),this._status="inactive",this._tab="running-lists",this.hideAgents=!0}static get styles(){return[o,n`
        @media screen and (max-width: 805px) {
          mwc-tab {
            --mdc-typography-button-font-size: 10px;
          }
        }
      `]}async _viewStateChanged(e){var t,s,i,a;if(await this.updateComplete,!e)return(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#running-agents")).active=!1,(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#terminated-agents")).active=!1,void(this._status="inactive");(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#running-agents")).active=!0,(null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#terminated-agents")).active=!0,this._status="active"}_showTab(e){var t,s;const i=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(let e=0;e<i.length;e++)i[e].style.display="none";(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#"+e.title)).style.display="block",this._tab=e.title}render(){return p`
      <link rel="stylesheet" href="resources/custom.css" />
      <lablup-activity-panel noheader narrow autowidth>
        <div slot="message">
          <h3 class="tab horizontal center layout">
            <mwc-tab-bar>
              <mwc-tab
                title="running-lists"
                label="${u("agent.Connected")}"
                @click="${e=>this._showTab(e.target)}"
              ></mwc-tab>
              <mwc-tab
                title="terminated-lists"
                label="${u("agent.Terminated")}"
                @click="${e=>this._showTab(e.target)}"
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
    `}};e([t({type:String})],m.prototype,"_status",void 0),e([t({type:String})],m.prototype,"_tab",void 0),e([t({type:Boolean})],m.prototype,"hideAgents",void 0),m=e([i("backend-ai-agent-summary-view")],m);
