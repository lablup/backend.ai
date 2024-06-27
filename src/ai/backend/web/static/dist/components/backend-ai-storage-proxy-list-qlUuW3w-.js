import{_ as e,n as t,e as i,t as a,B as s,b as o,I as r,a as n,i as d,d as l,j as c,k as p,p as h,x as g,f as u,g as b}from"./backend-ai-webui-CHZ-bl4E.js";import"./backend-ai-list-status-D8Jm1azR.js";import"./backend-ai-storage-host-settings-view-Dy_i8Ge9.js";import"./lablup-progress-bar-uZGTrT3Q.js";import"./vaadin-grid-BPP02Fg2.js";import"./vaadin-grid-sort-column-D98JUghL.js";import"./dir-utils-Oo-ABbXC.js";var m;let v=m=class extends s{constructor(){super(),this.condition="running",this.listCondition="loading",this.storagesObject=Object(),this.storageProxyDetail=Object(),this.notification=Object(),this._boundEndpointRenderer=this.endpointRenderer.bind(this),this._boundTypeRenderer=this.typeRenderer.bind(this),this._boundResourceRenderer=this.resourceRenderer.bind(this),this._boundCapabilitiesRenderer=this.capabilitiesRenderer.bind(this),this._boundControlRenderer=this.controlRenderer.bind(this),this.filter="",this.storages=[]}static get styles(){return[o,r,n,d`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: var(--list-height, calc(100vh - 182px));
        }

        mwc-icon {
          --mdc-icon-size: 16px;
        }

        img.indicator-icon {
          width: 16px !important;
          height: 16px !important;
        }

        paper-icon-button {
          --paper-icon-button: {
            width: 25px;
            height: 25px;
            min-width: 25px;
            min-height: 25px;
            padding: 3px;
            margin-right: 5px;
          };
        }

        div.indicator,
        span.indicator {
          font-size: 9px;
          margin-right: 5px;
        }

        #storage-proxy-detail {
          --component-max-width: 90%;
        }

        lablup-progress-bar {
          width: 100px;
          border-radius: 3px;
          height: 10px;
          --mdc-theme-primary: #3677eb;
          --mdc-linear-progress-buffer-color: #98be5a;
        }

        lablup-progress-bar.cpu {
          --progress-bar-height: 5px;
          margin-bottom: 0;
        }

        lablup-progress-bar.cuda {
          --progress-bar-height: 15px;
          margin-bottom: 5px;
        }

        lablup-progress-bar.mem {
          --progress-bar-height: 15px;
          width: 100px;
          margin-bottom: 0;
        }

        lablup-shields {
          margin: 1px;
        }

        .resource-indicator {
          width: 100px !important;
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._loadStorageProxyList()}),!0):this._loadStorageProxyList())}_loadStorageProxyList(){var e;!0===this.active&&(this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.storageproxy.list(["id","backend","capabilities","path","fsprefix","performance_metric","usage"]).then((e=>{var t;const i=e.storage_volume_list.items,a=[];void 0!==i&&i.length>0&&Object.keys(i).map(((e,t)=>{const s=i[e];if(""!==this.filter){const e=this.filter.split(":");e[0]in s&&s[e[0]]===e[1]&&a.push(s)}else a.push(s)})),this.storages=a,0==this.storages.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide();const s=new CustomEvent("backend-ai-storage-proxy-updated",{});this.dispatchEvent(s),!0===this.active&&setTimeout((()=>{this._loadStorageProxyList()}),15e3)})).catch((e=>{var t;null===(t=this._listStatus)||void 0===t||t.hide(),e&&e.message&&(this.notification.text=l.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))})))}_moveTo(e=""){const t=""!==e?e:"summary";c.dispatch(p(decodeURIComponent(t),{})),document.dispatchEvent(new CustomEvent("react-navigate",{detail:e}))}_indexRenderer(e,t,i){const a=i.index+1;h(g`
        <div>${a}</div>
      `,e)}endpointRenderer(e,t,i){h(g`
        <div>${i.item.id}</div>
        <div class="indicator monospace">${i.item.path}</div>
      `,e)}typeRenderer(e,t,i){let a,s;switch(i.item.backend){case"xfs":a="blue",s="local";break;case"ceph":case"cephfs":a="lightblue",s="ceph";break;case"vfs":case"nfs":case"dgx":case"spectrumscale":a="green",s="local";break;case"purestorage":a="red",s="purestorage";break;case"weka":a="purple",s="local";break;default:a="yellow",s="local"}h(g`
        <div class="horizontal start-justified center layout">
          <img
            src="/resources/icons/${s}.png"
            style="width:32px;height:32px;"
          />
          <lablup-shields
            app="Backend"
            color="${a}"
            description="${i.item.backend}"
            ui="round"
          ></lablup-shields>
        </div>
      `,e)}resourceRenderer(e,t,i){const a=JSON.parse(i.item.usage),s=a.capacity_bytes>0?a.used_bytes/a.capacity_bytes:0,o=(100*s).toFixed(3);h(g`
        <div class="layout flex">
          <div class="layout horizontal center flex">
            <div class="layout horizontal start resource-indicator">
              <mwc-icon class="fg green">data_usage</mwc-icon>
              <span class="indicator" style="padding-left:5px;">
                ${u("session.Usage")}
              </span>
            </div>
            <span class="flex"></span>
            <div class="layout vertical center">
              <lablup-progress-bar
                id="volume-usage-bar"
                progress="${s}"
                buffer="${100}"
                description="${o}%"
              ></lablup-progress-bar>
              <div class="indicator" style="margin-top:3px;">
                ${globalThis.backendaiutils._humanReadableFileSize(a.used_bytes)}
                /
                ${globalThis.backendaiutils._humanReadableFileSize(a.capacity_bytes)}
              </div>
            </div>
          </div>
        </div>
      `,e)}capabilitiesRenderer(e,t,i){h(g`
        <div class="layout vertical start justified wrap">
          ${i.item.capabilities?i.item.capabilities.map((e=>g`
                  <lablup-shields
                    app=""
                    color="blue"
                    description="${e}"
                    ui="round"
                  ></lablup-shields>
                `)):g``}
        </div>
      `,e)}showStorageProxyDetailDialog(e){const t=new CustomEvent("backend-ai-selected-storage-proxy",{detail:e});document.dispatchEvent(t)}controlRenderer(e,t,i){let a;try{const e=JSON.parse(i.item.performance_metric);a=!(Object.keys(e).length>0)}catch(e){a=!0}h(g`
        <div
          id="controls"
          class="layout horizontal flex center"
          agent-id="${i.item.id}"
        >
          <mwc-icon-button
            class="fg green controls-running"
            icon="assignment"
            ?disabled="${a}"
            @click="${e=>this.showStorageProxyDetailDialog(i.item.id)}"
          ></mwc-icon-button>
          <mwc-icon-button
            class="fg blue controls-running"
            icon="settings"
            @click="${()=>this._moveTo(`/storage-settings/${i.item.id}`)}"
          ></mwc-icon-button>
        </div>
      `,e)}static bytesToMB(e,t=1){return Number(e/10**6).toFixed(t)}render(){return g`
      <div class="list-wrapper">
        <vaadin-grid
          class="${this.condition}"
          theme="row-stripes column-borders compact dark"
          aria-label="Job list"
          .items="${this.storages}"
        >
          <vaadin-grid-column
            width="40px"
            flex-grow="0"
            header="#"
            text-align="center"
            .renderer="${this._indexRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            resizable
            width="80px"
            header="${u("agent.Endpoint")}"
            .renderer="${this._boundEndpointRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            width="100px"
            resizable
            header="${u("agent.BackendType")}"
            .renderer="${this._boundTypeRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            resizable
            width="60px"
            header="${u("agent.Resources")}"
            .renderer="${this._boundResourceRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            width="130px"
            flex-grow="0"
            resizable
            header="${u("agent.Capabilities")}"
            .renderer="${this._boundCapabilitiesRenderer}"
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
          message="${b("agent.NoAgentToDisplay")}"
        ></backend-ai-list-status>
      </div>
      <backend-ai-dialog
        id="storage-proxy-detail"
        fixed
        backdrop
        blockscrolling
        persistent
        scrollable
      >
        <span slot="title">${u("agent.DetailedInformation")}</span>
        <div slot="content">
          <div class="horizontal start start-justified layout">
            ${"cpu_util_live"in this.storageProxyDetail?g`
                  <div>
                    <h3>CPU</h3>
                    <div
                      class="horizontal wrap layout"
                      style="max-width:600px;"
                    >
                      ${this.storageProxyDetail.cpu_util_live.map((e=>g`
                          <div
                            class="horizontal start-justified center layout"
                            style="padding:0 5px;"
                          >
                            <div style="font-size:8px;width:35px;">
                              CPU${e.num}
                            </div>
                            <lablup-progress-bar
                              class="cpu"
                              progress="${e.pct/100}"
                              description=""
                            ></lablup-progress-bar>
                          </div>
                        `))}
                    </div>
                  </div>
                `:g``}
            <div style="margin-left:10px;">
              <h3>Memory</h3>
              <div>
                <lablup-progress-bar
                  class="mem"
                  progress="${this.storageProxyDetail.mem_current_usage_ratio}"
                  description="${this.storageProxyDetail.current_mem} GiB / ${this.storageProxyDetail.mem_slots} GiB"
                ></lablup-progress-bar>
              </div>
              <h3>Network</h3>
              ${"live_stat"in this.storageProxyDetail&&"node"in this.storageProxyDetail.live_stat?g`
                    <div>
                      TX:
                      ${m.bytesToMB(this.storageProxyDetail.live_stat.node.net_tx.current)}
                      MB
                    </div>
                    <div>
                      RX:
                      ${m.bytesToMB(this.storageProxyDetail.live_stat.node.net_rx.current)}
                      MB
                    </div>
                  `:g``}
            </div>
          </div>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            id="close-button"
            icon="check"
            label="${u("button.Close")}"
            @click="${e=>this._hideDialog(e)}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};e([t({type:String})],v.prototype,"condition",void 0),e([t({type:Array})],v.prototype,"storages",void 0),e([t({type:String})],v.prototype,"listCondition",void 0),e([t({type:Object})],v.prototype,"storagesObject",void 0),e([t({type:Object})],v.prototype,"storageProxyDetail",void 0),e([t({type:Object})],v.prototype,"notification",void 0),e([t({type:Object})],v.prototype,"_boundEndpointRenderer",void 0),e([t({type:Object})],v.prototype,"_boundTypeRenderer",void 0),e([t({type:Object})],v.prototype,"_boundResourceRenderer",void 0),e([t({type:Object})],v.prototype,"_boundCapabilitiesRenderer",void 0),e([t({type:Object})],v.prototype,"_boundControlRenderer",void 0),e([t({type:String})],v.prototype,"filter",void 0),e([i("#storage-proxy-detail")],v.prototype,"storageProxyDetailDialog",void 0),e([i("#list-status")],v.prototype,"_listStatus",void 0),v=m=e([a("backend-ai-storage-proxy-list")],v);
