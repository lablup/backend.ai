import{_ as e,n as t,e as s,s as i,I as r,a as n,i as a,x as o,g as l,b as c,B as p,c as u,d,f as h,t as g,h as m,o as b}from"./backend-ai-webui-75df15ed.js";import"./backend-ai-resource-monitor-21ef3974.js";import"./lablup-activity-panel-86e1deef.js";import"./lablup-loading-spinner-02aea3b9.js";import"./lablup-progress-bar-b230f3e3.js";import"./backend-ai-session-launcher-676818a7.js";import"./mwc-switch-13f7c132.js";import"./lablup-codemirror-59c15e56.js";import"./slider-3f740add.js";import"./mwc-check-list-item-5618f22b.js";import"./media-query-controller-bc25d693.js";import"./dir-utils-f5050166.js";import"./vaadin-grid-461d199a.js";import"./vaadin-grid-filter-column-2b22f222.js";import"./vaadin-grid-selection-column-29a490b5.js";let _=class extends i{constructor(){super(...arguments),this.currentNumber=50,this.maxNumber=100,this.unit="%",this.url="",this.textcolor="#888888",this.chartcolor="#ff2222",this.size=200,this.fontsize=60,this.chartFontSize="0",this.indicatorPath="",this.prefix="",this.sizeParam=""}static get is(){return"lablup-piechart"}static get styles(){return[r,n,a`
        #chart {
          cursor: pointer;
        }
      `]}firstUpdated(){var e,t,s,i,r,n,a;this.sizeParam=this.size+"px";let o=this.fontsize/this.size;o=o>=.5?.3:.9/this.currentNumber.toString().length,this.chartFontSize=o.toString();let l=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#chart"),c=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#chart-text"),p=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#unit-text"),u=(.3-.05*this.unit.length).toString();l.setAttribute("fill",this.chartcolor),c.setAttribute("fill",this.textcolor),c.setAttribute("font-size",this.chartFontSize),p.setAttribute("font-size",u),l.setAttribute("width",this.sizeParam),l.setAttribute("height",this.sizeParam),this.indicatorPath="M 0.5 0.5 L0.5 0 ";var d=100*(this.maxNumber-this.currentNumber)/this.maxNumber;d>12.5&&(this.indicatorPath=this.indicatorPath+"L1 0 "),d>37.5&&(this.indicatorPath=this.indicatorPath+"L1 1 "),d>62.5&&(this.indicatorPath=this.indicatorPath+"L0 1 "),d>87.5&&(this.indicatorPath=this.indicatorPath+"L0 0 ");let h=d/100*2*Math.PI,g=Math.sin(h)/Math.cos(h),m=0,b=0;d<=12.5||d>87.5?(b=.5,m=b*g):d>12.5&&d<=37.5?(m=.5,b=m/g):d>37.5&&d<=62.5?(b=-.5,m=b*g):d>62.5&&d<=87.5&&(m=-.5,b=m/g),m+=.5,b=.5-b,this.indicatorPath=this.indicatorPath+"L"+m+" "+b+" z",null===(r=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#pievalue"))||void 0===r||r.setAttribute("d",this.indicatorPath),void 0!==this.url&&""!==this.url&&(null===(a=null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("#chart"))||void 0===a||a.addEventListener("tap",this._moveTo.bind(this))),this.requestUpdate()}connectedCallback(){super.connectedCallback()}_moveTo(){window.location.href=this.url}render(){return o`
      <svg
        id="chart"
        xmlns="http://www.w3.org/2000/svg"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        version="1.1"
        viewBox="0 0 1 1"
        style="background-color:transparent;"
      >
        <g id="piechart">
          <circle cx="0.5" cy="0.5" r="0.5" />
          <circle cx="0.5" cy="0.5" r="0.40" fill="rgba(255,255,255,0.9)" />
          <path id="pievalue" stroke="none" fill="rgba(255, 255, 255, 0.75)" />
          <text
            id="chart-text"
            x="0.5"
            y="0.5"
            font-family="Roboto"
            text-anchor="middle"
            dy="0.1"
          >
            <tspan>${this.prefix}</tspan>
            <tspan>${this.currentNumber}</tspan>
            <tspan id="unit-text" font-size="0.2" dy="-0.07">
              ${this.unit}
            </tspan>
          </text>
        </g>
      </svg>
    `}};e([t({type:Number})],_.prototype,"currentNumber",void 0),e([t({type:Number})],_.prototype,"maxNumber",void 0),e([t({type:String})],_.prototype,"unit",void 0),e([t({type:String})],_.prototype,"url",void 0),e([t({type:String})],_.prototype,"textcolor",void 0),e([t({type:String})],_.prototype,"chartcolor",void 0),e([t({type:Number})],_.prototype,"size",void 0),e([t({type:Number})],_.prototype,"fontsize",void 0),e([t({type:String})],_.prototype,"chartFontSize",void 0),e([t({type:String})],_.prototype,"indicatorPath",void 0),e([t({type:String})],_.prototype,"prefix",void 0),e([t({type:String})],_.prototype,"sizeParam",void 0),_=e([s("lablup-piechart")],_);let f=class extends i{constructor(){super(...arguments),this.releaseURL="https://raw.githubusercontent.com/lablup/backend.ai-webui/release/version.json",this.localVersion="",this.localBuild="",this.remoteVersion="",this.remoteBuild="",this.remoteRevision="",this.updateChecked=!1,this.updateNeeded=!1,this.updateURL=""}static get styles(){return[]}render(){return o``}firstUpdated(){this.notification=globalThis.lablupNotification,globalThis.isElectron&&void 0!==globalThis.backendaioptions&&globalThis.backendaioptions.get("automatic_update_check",!0)&&this.checkRelease()}async checkRelease(){this.updateChecked||fetch(this.releaseURL).then((e=>e.json())).then((e=>{this.updateChecked=!0,this.remoteVersion=e.package,this.remoteBuild=e.build,this.remoteRevision=e.revision,this.compareVersion(globalThis.packageVersion,this.remoteVersion)<0&&(this.updateNeeded=!0,this.updateURL=`https://github.com/lablup/backend.ai-webui/releases/tag/v${this.remoteVersion}`,globalThis.isElectron&&(this.notification.text=l("update.NewWebUIVersionAvailable")+" "+this.remoteVersion,this.notification.detail=l("update.NewWebUIVersionAvailable"),this.notification.url=this.updateURL,this.notification.show()))})).catch((e=>{const t=globalThis.backendaioptions.get("automatic_update_count_trial",0);t>3&&globalThis.backendaioptions.set("automatic_update_check",!1),globalThis.backendaioptions.set("automatic_update_count_trial",t+1)}))}compareVersion(e,t){if("string"!=typeof e)return 0;if("string"!=typeof t)return 0;e=e.split("."),t=t.split(".");const s=Math.min(e.length,t.length);for(let i=0;i<s;++i){if(e[i]=parseInt(e[i],10),t[i]=parseInt(t[i],10),e[i]>t[i])return 1;if(e[i]<t[i])return-1}return e.length==t.length?0:e.length<t.length?-1:1}};e([t({type:String})],f.prototype,"releaseURL",void 0),e([t({type:String})],f.prototype,"localVersion",void 0),e([t({type:String})],f.prototype,"localBuild",void 0),e([t({type:String})],f.prototype,"remoteVersion",void 0),e([t({type:String})],f.prototype,"remoteBuild",void 0),e([t({type:String})],f.prototype,"remoteRevision",void 0),e([t({type:Boolean})],f.prototype,"updateChecked",void 0),e([t({type:Boolean})],f.prototype,"updateNeeded",void 0),e([t({type:String})],f.prototype,"updateURL",void 0),e([t({type:Object})],f.prototype,"notification",void 0),f=e([s("backend-ai-release-check")],f);let y=class extends p{constructor(){super(...arguments),this.condition="running",this.sessions=0,this.agents=0,this.is_admin=!1,this.is_superadmin=!1,this.resources=Object(),this.authenticated=!1,this.manager_version="",this.webui_version="",this.cpu_total=0,this.cpu_used=0,this.cpu_percent="0",this.cpu_total_percent="0",this.cpu_total_usage_ratio=0,this.cpu_current_usage_ratio=0,this.mem_total="0",this.mem_used="0",this.mem_allocated="0",this.mem_total_usage_ratio=0,this.mem_current_usage_ratio=0,this.mem_current_usage_percent="0",this.cuda_gpu_total=0,this.cuda_gpu_used=0,this.cuda_fgpu_total=0,this.cuda_fgpu_used=0,this.rocm_gpu_total=0,this.rocm_gpu_used=0,this.tpu_total=0,this.tpu_used=0,this.ipu_total=0,this.ipu_used=0,this.atom_total=0,this.atom_used=0,this.warboy_total=0,this.warboy_used=0,this.notification=Object(),this.announcement="",this.height=0}static get styles(){return[u,r,n,d,a`
        ul {
          padding-left: 0;
        }

        ul li {
          list-style: none;
          font-size: 14px;
        }

        li:before {
          padding: 3px;
          transform: rotate(-45deg) translateY(-2px);
          transition: color ease-in 0.2s;
          border: solid;
          border-width: 0 2px 2px 0;
          border-color: #242424;
          margin-right: 10px;
          content: '';
          display: inline-block;
        }

        span.indicator {
          width: 100px;
        }

        div.card {
          margin: 20px;
        }

        div.big.indicator {
          font-size: 48px;
        }

        a,
        a:visited {
          color: #222222;
        }

        a:hover {
          color: #3e872d;
        }

        mwc-linear-progress {
          width: 260px;
          height: 15px;
          border-radius: 0;
          --mdc-theme-primary: #3677eb;
        }

        mwc-linear-progress.start-bar {
          border-top-left-radius: 3px;
          border-top-right-radius: 3px;
          --mdc-theme-primary: #3677eb;
        }

        mwc-linear-progress.end-bar {
          border-bottom-left-radius: 3px;
          border-bottom-right-radius: 3px;
          --mdc-theme-primary: #98be5a;
        }

        mwc-icon-button.update-button {
          --mdc-icon-size: 16px;
          --mdc-icon-button-size: 24px;
          color: red;
        }

        mwc-icon.update-icon {
          --mdc-icon-size: 16px;
          --mdc-icon-button-size: 24px;
          color: black;
        }

        img.resource-type-icon {
          width: 16px;
          height: 16px;
          margin-right: 5px;
        }

        div.indicators {
          min-height: 80px;
          padding: 15px 20px 5px 20px;
          background-color: #f6f6f6;
        }

        .system-health-indicator {
          width: 90px;
        }

        .resource {
          margin-bottom: 10px;
          margin-left: 5px;
          height: 46px;
        }

        .resource-line {
          margin-left: 85px;
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}_refreshHealthPanel(){this.activeConnected&&(this._refreshSessionInformation(),this.is_superadmin&&this._refreshAgentInformation())}_refreshSessionInformation(){if(!this.activeConnected)return;this.spinner.show();let e="RUNNING";switch(this.condition){case"running":case"archived":default:e="RUNNING";break;case"finished":e="TERMINATED"}globalThis.backendaiclient.computeSession.total_count(e).then((e=>{this.spinner.hide(),!e.compute_session_list&&e.legacy_compute_session_list&&(e.compute_session_list=e.legacy_compute_session_list),this.sessions=e.compute_session_list.total_count,this.active&&setTimeout((()=>{this._refreshSessionInformation()}),15e3)})).catch((e=>{this.spinner.hide(),this.sessions=0,this.notification.text=l("summary.connectingToCluster"),this.notification.detail=e,this.notification.show(!1,e),this.active&&setTimeout((()=>{this._refreshSessionInformation()}),15e3)}))}_refreshResourceInformation(){if(this.activeConnected)return globalThis.backendaiclient.resourcePolicy.get(globalThis.backendaiclient.resource_policy).then((e=>{const t=e.keypair_resource_policies;this.resourcePolicy=globalThis.backendaiclient.utils.gqlToObject(t,"name")}))}_refreshAgentInformation(e="running"){if(this.activeConnected){switch(this.condition){case"running":case"archived":default:e="ALIVE";break;case"finished":e="TERMINATED"}this.spinner.show(),globalThis.backendaiclient.resources.totalResourceInformation().then((t=>{this.spinner.hide(),this.resources=t,this._sync_resource_values(),1==this.active&&setTimeout((()=>{this._refreshAgentInformation(e)}),15e3)})).catch((e=>{this.spinner.hide(),e&&e.message&&(this.notification.text=h.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}}_init_resource_values(){this.resources.cpu={},this.resources.cpu.total=0,this.resources.cpu.used=0,this.resources.cpu.percent=0,this.resources.mem={},this.resources.mem.total=0,this.resources.mem.allocated=0,this.resources.mem.used=0,this.resources.cuda_gpu={},this.resources.cuda_gpu.total=0,this.resources.cuda_gpu.used=0,this.resources.cuda_fgpu={},this.resources.cuda_fgpu.total=0,this.resources.cuda_fgpu.used=0,this.resources.rocm_gpu={},this.resources.rocm_gpu.total=0,this.resources.rocm_gpu.used=0,this.resources.tpu={},this.resources.tpu.total=0,this.resources.tpu.used=0,this.resources.ipu={},this.resources.ipu.total=0,this.resources.ipu.used=0,this.resources.atom={},this.resources.atom.total=0,this.resources.atom.used=0,this.resources.warboy={},this.resources.warboy.total=0,this.resources.warboy.used=0,this.resources.agents={},this.resources.agents.total=0,this.resources.agents.using=0,this.cpu_total_usage_ratio=0,this.cpu_current_usage_ratio=0,this.mem_total_usage_ratio=0,this.mem_current_usage_ratio=0,this.mem_current_usage_percent="0",this.is_admin=!1,this.is_superadmin=!1}_sync_resource_values(){this.manager_version=globalThis.backendaiclient.managerVersion,this.webui_version=globalThis.packageVersion,this.cpu_total=this.resources.cpu.total,this.mem_total=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(this.resources.mem.total,"g")).toFixed(2),isNaN(this.resources["cuda.device"].total)?this.cuda_gpu_total=0:this.cuda_gpu_total=this.resources["cuda.device"].total,isNaN(this.resources["cuda.shares"].total)?this.cuda_fgpu_total=0:this.cuda_fgpu_total=this.resources["cuda.shares"].total,isNaN(this.resources["rocm.device"].total)?this.rocm_gpu_total=0:this.rocm_gpu_total=this.resources["rocm.device"].total,isNaN(this.resources["tpu.device"].total)?this.tpu_total=0:this.tpu_total=this.resources["tpu.device"].total,isNaN(this.resources["ipu.device"].total)?this.ipu_total=0:this.ipu_total=this.resources["ipu.device"].total,isNaN(this.resources["atom.device"].total)?this.atom_total=0:this.atom_total=this.resources["atom.device"].total,isNaN(this.resources["warboy.device"].total)?this.warboy_total=0:this.warboy_total=this.resources["warboy.device"].total,this.cpu_used=this.resources.cpu.used,this.cuda_gpu_used=this.resources["cuda.device"].used,this.cuda_fgpu_used=this.resources["cuda.shares"].used,this.rocm_gpu_used=this.resources["rocm.device"].used,this.tpu_used=this.resources["tpu.device"].used,this.ipu_used=this.resources["ipu.device"].used,this.atom_used=this.resources["atom.device"].used,this.warboy_used=this.resources["warboy.device"].used,this.cpu_percent=parseFloat(this.resources.cpu.percent).toFixed(2),this.cpu_total_percent=0!==this.cpu_used?(this.cpu_used/this.cpu_total*100).toFixed(2):"0",this.cpu_total_usage_ratio=this.resources.cpu.used/this.resources.cpu.total*100,this.cpu_current_usage_ratio=this.resources.cpu.percent/this.resources.cpu.total,this.mem_used=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(this.resources.mem.used,"g")).toFixed(2),this.mem_allocated=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(this.resources.mem.allocated,"g")).toFixed(2),this.mem_total_usage_ratio=this.resources.mem.allocated/this.resources.mem.total*100,this.mem_current_usage_ratio=this.resources.mem.used/this.resources.mem.total*100,0===this.mem_total_usage_ratio?this.mem_current_usage_percent="0.0":this.mem_current_usage_percent=this.mem_total_usage_ratio.toFixed(2),this.agents=this.resources.agents.total,isNaN(parseFloat(this.mem_current_usage_percent))&&(this.mem_current_usage_percent="0")}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(this._init_resource_values(),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_superadmin=globalThis.backendaiclient.is_superadmin,this.is_admin=globalThis.backendaiclient.is_admin,this.authenticated=!0,this.activeConnected&&(this._refreshHealthPanel(),this.requestUpdate())}),!0):(this.is_superadmin=globalThis.backendaiclient.is_superadmin,this.is_admin=globalThis.backendaiclient.is_admin,this.authenticated=!0,this._refreshHealthPanel(),this.requestUpdate()))}_toInt(e){return Math.ceil(e)}_countObject(e){return Object.keys(e).length}_addComma(e){if(void 0===e)return"";return e.toString().replace(/\B(?=(\d{3})+(?!\d))/g,",")}render(){return o`
      <link rel="stylesheet" href="resources/custom.css" />
      <lablup-loading-spinner id="loading-spinner"></lablup-loading-spinner>
      <lablup-activity-panel
        title="${g("summary.SystemResources")}"
        elevation="1"
        narrow
        height="${this.height}"
      >
        <div slot="message">
          <div class="horizontal justified layout wrap indicators">
            ${this.is_superadmin?o`
                  <div class="vertical layout center system-health-indicator">
                    <div class="big indicator">${this.agents}</div>
                    <span>${m("summary.ConnectedNodes")}</span>
                  </div>
                `:o``}
            <div class="vertical layout center system-health-indicator">
              <div class="big indicator">${this.sessions}</div>
              <span>${g("summary.ActiveSessions")}</span>
            </div>
          </div>
          <div class="vertical-card" style="align-items: flex-start">
            ${this.is_superadmin?o`
                  <div class="layout horizontal center flex resource">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <div class="gauge-name">CPU</div>
                    </div>
                    <div class="layout vertical start-justified wrap">
                      <lablup-progress-bar
                        id="cpu-usage-bar"
                        class="start"
                        progress="${this.cpu_total_usage_ratio/100}"
                        description="${this._addComma(this.cpu_used)}/${this._addComma(this.cpu_total)} ${g("summary.CoresReserved")}."
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="cpu-usage-bar-2"
                        class="end"
                        progress="${this.cpu_current_usage_ratio/100}"
                        description="${g("summary.Using")} ${this.cpu_total_percent} % (util. ${this.cpu_percent} %)"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${parseInt(this.cpu_total_percent)+"%"}
                      </span>
                      <span class="percentage end-bar">
                        ${parseInt(this.cpu_percent)+"%"}
                      </span>
                    </div>
                  </div>
                  <div class="resource-line"></div>
                  <div class="layout horizontal center flex resource">
                    <div
                      class="layout vertical center center-justified resource-name"
                    >
                      <div class="gauge-name">RAM</div>
                    </div>
                    <div class="layout vertical start-justified wrap">
                      <lablup-progress-bar
                        id="mem-usage-bar"
                        class="start"
                        progress="${this.mem_total_usage_ratio/100}"
                        description="${this._addComma(this.mem_allocated)} / ${this._addComma(this.mem_total)} GiB ${g("summary.reserved")}."
                      ></lablup-progress-bar>
                      <lablup-progress-bar
                        id="mem-usage-bar-2"
                        class="end"
                        progress="${this.mem_current_usage_ratio/100}"
                        description="${g("summary.Using")} ${this._addComma(this.mem_used)} GiB
                    (${0!==parseInt(this.mem_used)?(parseInt(this.mem_used)/parseInt(this.mem_total)*100).toFixed(0):"0"} %)"
                      ></lablup-progress-bar>
                    </div>
                    <div class="layout vertical center center-justified">
                      <span class="percentage start-bar">
                        ${this.mem_total_usage_ratio.toFixed(1)+"%"}
                      </span>
                      <span class="percentage end-bar">
                        ${(0!==parseInt(this.mem_used)?(parseInt(this.mem_used)/parseInt(this.mem_total)*100).toFixed(0):"0")+"%"}
                      </span>
                    </div>
                  </div>
                  ${this.cuda_gpu_total||this.cuda_fgpu_total||this.rocm_gpu_total||this.tpu_total||this.ipu_total||this.atom_total||this.warboy_total?o`
                        <div class="resource-line"></div>
                        <div class="layout horizontal center flex resource">
                          <div
                            class="layout vertical center center-justified resource-name"
                          >
                            <div class="gauge-name">GPU/NPU</div>
                          </div>
                          ${this.cuda_gpu_total?o`
                                <div
                                  class="layout vertical start-justified wrap"
                                >
                                  <lablup-progress-bar
                                    id="gpu-usage-bar"
                                    class="start"
                                    progress="${this.cuda_gpu_used/this.cuda_gpu_total}"
                                    description="${this.cuda_gpu_used} / ${this.cuda_gpu_total} CUDA GPUs ${g("summary.reserved")}."
                                  ></lablup-progress-bar>
                                  <lablup-progress-bar
                                    id="gpu-usage-bar-2"
                                    class="end"
                                    progress="0"
                                    description="${g("summary.FractionalGPUScalingEnabled")}."
                                  ></lablup-progress-bar>
                                </div>
                                <div
                                  class="layout vertical center center-justified"
                                >
                                  <span class="percentage start-bar">
                                    ${0!==this.cuda_gpu_used?(this.cuda_gpu_used/this.cuda_gpu_total*100).toFixed(1):0}%
                                  </span>
                                  <span class="percentage end-bar">&nbsp;</span>
                                </div>
                              `:o``}
                          ${this.cuda_fgpu_total?o`
                                <div
                                  class="layout vertical start-justified wrap"
                                >
                                  <lablup-progress-bar
                                    id="fgpu-usage-bar"
                                    class="start"
                                    progress="${this.cuda_fgpu_used/this.cuda_fgpu_total}"
                                    description="${this.cuda_fgpu_used} / ${this.cuda_fgpu_total} CUDA FGPUs ${g("summary.reserved")}."
                                  ></lablup-progress-bar>
                                  <lablup-progress-bar
                                    id="fgpu-usage-bar-2"
                                    class="end"
                                    progress="0"
                                    description="${g("summary.FractionalGPUScalingEnabled")}."
                                  ></lablup-progress-bar>
                                </div>
                                <div
                                  class="layout vertical center center-justified"
                                >
                                  <span class="percentage start-bar">
                                    ${0!==this.cuda_fgpu_used?(this.cuda_fgpu_used/this.cuda_fgpu_total*100).toFixed(1):0}%
                                  </span>
                                  <span class="percentage end-bar">&nbsp;</span>
                                </div>
                              `:o``}
                          ${this.rocm_gpu_total?o`
                                <div
                                  class="layout vertical start-justified wrap"
                                >
                                  <lablup-progress-bar
                                    id="rocm-gpu-usage-bar"
                                    class="start"
                                    progress="${this.rocm_gpu_used/100}"
                                    description="${this.rocm_gpu_used} / ${this.rocm_gpu_total} ROCm GPUs ${g("summary.reserved")}."
                                  ></lablup-progress-bar>
                                  <lablup-progress-bar
                                    id="rocm-gpu-usage-bar-2"
                                    class="end"
                                    progress="0"
                                    description="${g("summary.ROCMGPUEnabled")}."
                                  ></lablup-progress-bar>
                                </div>
                                <div
                                  class="layout vertical center center-justified"
                                >
                                  <span class="percentage start-bar">
                                    ${this.rocm_gpu_used.toFixed(1)+"%"}
                                  </span>
                                  <span class="percentage end-bar">&nbsp;</span>
                                </div>
                              `:o``}
                          ${this.tpu_total?o`
                                <div
                                  class="layout vertical start-justified wrap"
                                >
                                  <lablup-progress-bar
                                    id="tpu-usage-bar"
                                    class="start"
                                    progress="${this.tpu_used/100}"
                                    description="${this.tpu_used} / ${this.tpu_total} TPUs ${g("summary.reserved")}."
                                  ></lablup-progress-bar>
                                  <lablup-progress-bar
                                    id="tpu-usage-bar-2"
                                    class="end"
                                    progress="0"
                                    description="${g("summary.TPUEnabled")}."
                                  ></lablup-progress-bar>
                                </div>
                                <div
                                  class="layout vertical center center-justified"
                                >
                                  <span class="percentage start-bar">
                                    ${this.tpu_used.toFixed(1)+"%"}
                                  </span>
                                  <span class="percentage end-bar"></span>
                                </div>
                              `:o``}
                          ${this.ipu_total?o`
                                <div
                                  class="layout vertical start-justified wrap"
                                >
                                  <lablup-progress-bar
                                    id="ipu-usage-bar"
                                    class="start"
                                    progress="${this.ipu_used/100}"
                                    description="${this.ipu_used} / ${this.ipu_total} IPUs ${g("summary.reserved")}."
                                  ></lablup-progress-bar>
                                  <lablup-progress-bar
                                    id="ipu-usage-bar-2"
                                    class="end"
                                    progress="0"
                                    description="${g("summary.IPUEnabled")}."
                                  ></lablup-progress-bar>
                                </div>
                                <div
                                  class="layout vertical center center-justified"
                                >
                                  <span class="percentage start-bar">
                                    ${this.ipu_used.toFixed(1)+"%"}
                                  </span>
                                  <span class="percentage end-bar"></span>
                                </div>
                              `:o``}
                          ${this.atom_total?o`
                                <div
                                  class="layout vertical start-justified wrap"
                                >
                                  <lablup-progress-bar
                                    id="atom-usage-bar"
                                    class="start"
                                    progress="${this.atom_used/100}"
                                    description="${this.atom_used} / ${this.atom_total} ATOMs ${g("summary.reserved")}."
                                  ></lablup-progress-bar>
                                  <lablup-progress-bar
                                    id="atom-usage-bar-2"
                                    class="end"
                                    progress="0"
                                    description="${g("summary.ATOMEnabled")}."
                                  ></lablup-progress-bar>
                                </div>
                                <div
                                  class="layout vertical center center-justified"
                                >
                                  <span class="percentage start-bar">
                                    ${this.atom_used.toFixed(1)+"%"}
                                  </span>
                                  <span class="percentage end-bar"></span>
                                </div>
                              `:o``}
                          ${this.warboy_total?o`
                                <div
                                  class="layout vertical start-justified wrap"
                                >
                                  <lablup-progress-bar
                                    id="warboy-usage-bar"
                                    class="start"
                                    progress="${this.warboy_used/100}"
                                    description="${this.warboy_used} / ${this.warboy_total} Warboys ${g("summary.reserved")}."
                                  ></lablup-progress-bar>
                                  <lablup-progress-bar
                                    id="warboy-usage-bar-2"
                                    class="end"
                                    progress="0"
                                    description="${g("summary.WarboyEnabled")}."
                                  ></lablup-progress-bar>
                                </div>
                                <div
                                  class="layout vertical center center-justified"
                                >
                                  <span class="percentage start-bar">
                                    ${this.warboy_used.toFixed(1)+"%"}
                                  </span>
                                  <span class="percentage end-bar"></span>
                                </div>
                              `:o``}
                        </div>
                      `:o``}
                  <div class="vertical start layout" style="margin-top:30px;">
                    <div class="horizontal layout resource-legend-stack">
                      <div class="resource-legend-icon start"></div>
                      <span class="resource-legend">
                        ${g("summary.Reserved")}
                        ${g("resourcePolicy.Resources")}
                      </span>
                    </div>
                    <div class="horizontal layout resource-legend-stack">
                      <div class="resource-legend-icon end"></div>
                      <span class="resource-legend">
                        ${g("summary.Used")} ${g("resourcePolicy.Resources")}
                      </span>
                    </div>
                    <div class="horizontal layout">
                      <div class="resource-legend-icon total"></div>
                      <span class="resource-legend">
                        ${g("summary.Total")} ${g("resourcePolicy.Resources")}
                      </span>
                    </div>
                  </div>
                `:o``}
          </div>
        </div>
      </lablup-activity-panel>
    `}};function v(){return{async:!1,breaks:!1,extensions:null,gfm:!0,hooks:null,pedantic:!1,renderer:null,silent:!1,tokenizer:null,walkTokens:null}}e([t({type:String})],y.prototype,"condition",void 0),e([t({type:Number})],y.prototype,"sessions",void 0),e([t({type:Number})],y.prototype,"agents",void 0),e([t({type:Boolean})],y.prototype,"is_admin",void 0),e([t({type:Boolean})],y.prototype,"is_superadmin",void 0),e([t({type:Object})],y.prototype,"resources",void 0),e([t({type:Boolean})],y.prototype,"authenticated",void 0),e([t({type:String})],y.prototype,"manager_version",void 0),e([t({type:String})],y.prototype,"webui_version",void 0),e([t({type:Number})],y.prototype,"cpu_total",void 0),e([t({type:Number})],y.prototype,"cpu_used",void 0),e([t({type:String})],y.prototype,"cpu_percent",void 0),e([t({type:String})],y.prototype,"cpu_total_percent",void 0),e([t({type:Number})],y.prototype,"cpu_total_usage_ratio",void 0),e([t({type:Number})],y.prototype,"cpu_current_usage_ratio",void 0),e([t({type:String})],y.prototype,"mem_total",void 0),e([t({type:String})],y.prototype,"mem_used",void 0),e([t({type:String})],y.prototype,"mem_allocated",void 0),e([t({type:Number})],y.prototype,"mem_total_usage_ratio",void 0),e([t({type:Number})],y.prototype,"mem_current_usage_ratio",void 0),e([t({type:String})],y.prototype,"mem_current_usage_percent",void 0),e([t({type:Number})],y.prototype,"cuda_gpu_total",void 0),e([t({type:Number})],y.prototype,"cuda_gpu_used",void 0),e([t({type:Number})],y.prototype,"cuda_fgpu_total",void 0),e([t({type:Number})],y.prototype,"cuda_fgpu_used",void 0),e([t({type:Number})],y.prototype,"rocm_gpu_total",void 0),e([t({type:Number})],y.prototype,"rocm_gpu_used",void 0),e([t({type:Number})],y.prototype,"tpu_total",void 0),e([t({type:Number})],y.prototype,"tpu_used",void 0),e([t({type:Number})],y.prototype,"ipu_total",void 0),e([t({type:Number})],y.prototype,"ipu_used",void 0),e([t({type:Number})],y.prototype,"atom_total",void 0),e([t({type:Number})],y.prototype,"atom_used",void 0),e([t({type:Number})],y.prototype,"warboy_total",void 0),e([t({type:Number})],y.prototype,"warboy_used",void 0),e([t({type:Object})],y.prototype,"notification",void 0),e([t({type:Object})],y.prototype,"resourcePolicy",void 0),e([t({type:String})],y.prototype,"announcement",void 0),e([t({type:Number})],y.prototype,"height",void 0),e([c("#loading-spinner")],y.prototype,"spinner",void 0),y=e([s("backend-ai-resource-panel")],y);let k={async:!1,breaks:!1,extensions:null,gfm:!0,hooks:null,pedantic:!1,renderer:null,silent:!1,tokenizer:null,walkTokens:null};function x(e){k=e}const w=/[&<>"']/,$=new RegExp(w.source,"g"),S=/[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/,z=new RegExp(S.source,"g"),T={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"},A=e=>T[e];function N(e,t){if(t){if(w.test(e))return e.replace($,A)}else if(S.test(e))return e.replace(z,A);return e}const j=/&(#(?:\d+)|(?:#x[0-9A-Fa-f]+)|(?:\w+));?/gi;const R=/(^|[^\[])\^/g;function I(e,t){e="string"==typeof e?e:e.source,t=t||"";const s={replace:(t,i)=>(i=(i="object"==typeof i&&"source"in i?i.source:i).replace(R,"$1"),e=e.replace(t,i),s),getRegex:()=>new RegExp(e,t)};return s}function O(e){try{e=encodeURI(e).replace(/%25/g,"%")}catch(e){return null}return e}const U={exec:()=>null};function P(e,t){const s=e.replace(/\|/g,((e,t,s)=>{let i=!1,r=t;for(;--r>=0&&"\\"===s[r];)i=!i;return i?"|":" |"})).split(/ \|/);let i=0;if(s[0].trim()||s.shift(),s.length>0&&!s[s.length-1].trim()&&s.pop(),t)if(s.length>t)s.splice(t);else for(;s.length<t;)s.push("");for(;i<s.length;i++)s[i]=s[i].trim().replace(/\\\|/g,"|");return s}function C(e,t,s){const i=e.length;if(0===i)return"";let r=0;for(;r<i;){const n=e.charAt(i-r-1);if(n!==t||s){if(n===t||!s)break;r++}else r++}return e.slice(0,i-r)}function E(e,t,s,i){const r=t.href,n=t.title?N(t.title):null,a=e[1].replace(/\\([\[\]])/g,"$1");if("!"!==e[0].charAt(0)){i.state.inLink=!0;const e={type:"link",raw:s,href:r,title:n,text:a,tokens:i.inlineTokens(a)};return i.state.inLink=!1,e}return{type:"image",raw:s,href:r,title:n,text:N(a)}}class M{options;rules;lexer;constructor(e){this.options=e||k}space(e){const t=this.rules.block.newline.exec(e);if(t&&t[0].length>0)return{type:"space",raw:t[0]}}code(e){const t=this.rules.block.code.exec(e);if(t){const e=t[0].replace(/^ {1,4}/gm,"");return{type:"code",raw:t[0],codeBlockStyle:"indented",text:this.options.pedantic?e:C(e,"\n")}}}fences(e){const t=this.rules.block.fences.exec(e);if(t){const e=t[0],s=function(e,t){const s=e.match(/^(\s+)(?:```)/);if(null===s)return t;const i=s[1];return t.split("\n").map((e=>{const t=e.match(/^\s+/);if(null===t)return e;const[s]=t;return s.length>=i.length?e.slice(i.length):e})).join("\n")}(e,t[3]||"");return{type:"code",raw:e,lang:t[2]?t[2].trim().replace(this.rules.inline._escapes,"$1"):t[2],text:s}}}heading(e){const t=this.rules.block.heading.exec(e);if(t){let e=t[2].trim();if(/#$/.test(e)){const t=C(e,"#");this.options.pedantic?e=t.trim():t&&!/ $/.test(t)||(e=t.trim())}return{type:"heading",raw:t[0],depth:t[1].length,text:e,tokens:this.lexer.inline(e)}}}hr(e){const t=this.rules.block.hr.exec(e);if(t)return{type:"hr",raw:t[0]}}blockquote(e){const t=this.rules.block.blockquote.exec(e);if(t){const e=t[0].replace(/^ *>[ \t]?/gm,""),s=this.lexer.state.top;this.lexer.state.top=!0;const i=this.lexer.blockTokens(e);return this.lexer.state.top=s,{type:"blockquote",raw:t[0],tokens:i,text:e}}}list(e){let t=this.rules.block.list.exec(e);if(t){let s=t[1].trim();const i=s.length>1,r={type:"list",raw:"",ordered:i,start:i?+s.slice(0,-1):"",loose:!1,items:[]};s=i?`\\d{1,9}\\${s.slice(-1)}`:`\\${s}`,this.options.pedantic&&(s=i?s:"[*+-]");const n=new RegExp(`^( {0,3}${s})((?:[\t ][^\\n]*)?(?:\\n|$))`);let a="",o="",l=!1;for(;e;){let s=!1;if(!(t=n.exec(e)))break;if(this.rules.block.hr.test(e))break;a=t[0],e=e.substring(a.length);let i=t[2].split("\n",1)[0].replace(/^\t+/,(e=>" ".repeat(3*e.length))),c=e.split("\n",1)[0],p=0;this.options.pedantic?(p=2,o=i.trimStart()):(p=t[2].search(/[^ ]/),p=p>4?1:p,o=i.slice(p),p+=t[1].length);let u=!1;if(!i&&/^ *$/.test(c)&&(a+=c+"\n",e=e.substring(c.length+1),s=!0),!s){const t=new RegExp(`^ {0,${Math.min(3,p-1)}}(?:[*+-]|\\d{1,9}[.)])((?:[ \t][^\\n]*)?(?:\\n|$))`),s=new RegExp(`^ {0,${Math.min(3,p-1)}}((?:- *){3,}|(?:_ *){3,}|(?:\\* *){3,})(?:\\n+|$)`),r=new RegExp(`^ {0,${Math.min(3,p-1)}}(?:\`\`\`|~~~)`),n=new RegExp(`^ {0,${Math.min(3,p-1)}}#`);for(;e;){const l=e.split("\n",1)[0];if(c=l,this.options.pedantic&&(c=c.replace(/^ {1,4}(?=( {4})*[^ ])/g,"  ")),r.test(c))break;if(n.test(c))break;if(t.test(c))break;if(s.test(e))break;if(c.search(/[^ ]/)>=p||!c.trim())o+="\n"+c.slice(p);else{if(u)break;if(i.search(/[^ ]/)>=4)break;if(r.test(i))break;if(n.test(i))break;if(s.test(i))break;o+="\n"+c}u||c.trim()||(u=!0),a+=l+"\n",e=e.substring(l.length+1),i=c.slice(p)}}r.loose||(l?r.loose=!0:/\n *\n *$/.test(a)&&(l=!0));let d,h=null;this.options.gfm&&(h=/^\[[ xX]\] /.exec(o),h&&(d="[ ] "!==h[0],o=o.replace(/^\[[ xX]\] +/,""))),r.items.push({type:"list_item",raw:a,task:!!h,checked:d,loose:!1,text:o,tokens:[]}),r.raw+=a}r.items[r.items.length-1].raw=a.trimEnd(),r.items[r.items.length-1].text=o.trimEnd(),r.raw=r.raw.trimEnd();for(let e=0;e<r.items.length;e++)if(this.lexer.state.top=!1,r.items[e].tokens=this.lexer.blockTokens(r.items[e].text,[]),!r.loose){const t=r.items[e].tokens.filter((e=>"space"===e.type)),s=t.length>0&&t.some((e=>/\n.*\n/.test(e.raw)));r.loose=s}if(r.loose)for(let e=0;e<r.items.length;e++)r.items[e].loose=!0;return r}}html(e){const t=this.rules.block.html.exec(e);if(t){return{type:"html",block:!0,raw:t[0],pre:"pre"===t[1]||"script"===t[1]||"style"===t[1],text:t[0]}}}def(e){const t=this.rules.block.def.exec(e);if(t){const e=t[1].toLowerCase().replace(/\s+/g," "),s=t[2]?t[2].replace(/^<(.*)>$/,"$1").replace(this.rules.inline._escapes,"$1"):"",i=t[3]?t[3].substring(1,t[3].length-1).replace(this.rules.inline._escapes,"$1"):t[3];return{type:"def",tag:e,raw:t[0],href:s,title:i}}}table(e){const t=this.rules.block.table.exec(e);if(t){const e={type:"table",raw:t[0],header:P(t[1]).map((e=>({text:e,tokens:[]}))),align:t[2].replace(/^ *|\| *$/g,"").split(/ *\| */),rows:t[3]&&t[3].trim()?t[3].replace(/\n[ \t]*$/,"").split("\n"):[]};if(e.header.length===e.align.length){let t,s,i,r,n=e.align.length;for(t=0;t<n;t++){const s=e.align[t];s&&(/^ *-+: *$/.test(s)?e.align[t]="right":/^ *:-+: *$/.test(s)?e.align[t]="center":/^ *:-+ *$/.test(s)?e.align[t]="left":e.align[t]=null)}for(n=e.rows.length,t=0;t<n;t++)e.rows[t]=P(e.rows[t],e.header.length).map((e=>({text:e,tokens:[]})));for(n=e.header.length,s=0;s<n;s++)e.header[s].tokens=this.lexer.inline(e.header[s].text);for(n=e.rows.length,s=0;s<n;s++)for(r=e.rows[s],i=0;i<r.length;i++)r[i].tokens=this.lexer.inline(r[i].text);return e}}}lheading(e){const t=this.rules.block.lheading.exec(e);if(t)return{type:"heading",raw:t[0],depth:"="===t[2].charAt(0)?1:2,text:t[1],tokens:this.lexer.inline(t[1])}}paragraph(e){const t=this.rules.block.paragraph.exec(e);if(t){const e="\n"===t[1].charAt(t[1].length-1)?t[1].slice(0,-1):t[1];return{type:"paragraph",raw:t[0],text:e,tokens:this.lexer.inline(e)}}}text(e){const t=this.rules.block.text.exec(e);if(t)return{type:"text",raw:t[0],text:t[0],tokens:this.lexer.inline(t[0])}}escape(e){const t=this.rules.inline.escape.exec(e);if(t)return{type:"escape",raw:t[0],text:N(t[1])}}tag(e){const t=this.rules.inline.tag.exec(e);if(t)return!this.lexer.state.inLink&&/^<a /i.test(t[0])?this.lexer.state.inLink=!0:this.lexer.state.inLink&&/^<\/a>/i.test(t[0])&&(this.lexer.state.inLink=!1),!this.lexer.state.inRawBlock&&/^<(pre|code|kbd|script)(\s|>)/i.test(t[0])?this.lexer.state.inRawBlock=!0:this.lexer.state.inRawBlock&&/^<\/(pre|code|kbd|script)(\s|>)/i.test(t[0])&&(this.lexer.state.inRawBlock=!1),{type:"html",raw:t[0],inLink:this.lexer.state.inLink,inRawBlock:this.lexer.state.inRawBlock,block:!1,text:t[0]}}link(e){const t=this.rules.inline.link.exec(e);if(t){const e=t[2].trim();if(!this.options.pedantic&&/^</.test(e)){if(!/>$/.test(e))return;const t=C(e.slice(0,-1),"\\");if((e.length-t.length)%2==0)return}else{const e=function(e,t){if(-1===e.indexOf(t[1]))return-1;let s=0;for(let i=0;i<e.length;i++)if("\\"===e[i])i++;else if(e[i]===t[0])s++;else if(e[i]===t[1]&&(s--,s<0))return i;return-1}(t[2],"()");if(e>-1){const s=(0===t[0].indexOf("!")?5:4)+t[1].length+e;t[2]=t[2].substring(0,e),t[0]=t[0].substring(0,s).trim(),t[3]=""}}let s=t[2],i="";if(this.options.pedantic){const e=/^([^'"]*[^\s])\s+(['"])(.*)\2/.exec(s);e&&(s=e[1],i=e[3])}else i=t[3]?t[3].slice(1,-1):"";return s=s.trim(),/^</.test(s)&&(s=this.options.pedantic&&!/>$/.test(e)?s.slice(1):s.slice(1,-1)),E(t,{href:s?s.replace(this.rules.inline._escapes,"$1"):s,title:i?i.replace(this.rules.inline._escapes,"$1"):i},t[0],this.lexer)}}reflink(e,t){let s;if((s=this.rules.inline.reflink.exec(e))||(s=this.rules.inline.nolink.exec(e))){let e=(s[2]||s[1]).replace(/\s+/g," ");if(e=t[e.toLowerCase()],!e){const e=s[0].charAt(0);return{type:"text",raw:e,text:e}}return E(s,e,s[0],this.lexer)}}emStrong(e,t,s=""){let i=this.rules.inline.emStrong.lDelim.exec(e);if(!i)return;if(i[3]&&s.match(/[\p{L}\p{N}]/u))return;if(!(i[1]||i[2]||"")||!s||this.rules.inline.punctuation.exec(s)){const s=[...i[0]].length-1;let r,n,a=s,o=0;const l="*"===i[0][0]?this.rules.inline.emStrong.rDelimAst:this.rules.inline.emStrong.rDelimUnd;for(l.lastIndex=0,t=t.slice(-1*e.length+s);null!=(i=l.exec(t));){if(r=i[1]||i[2]||i[3]||i[4]||i[5]||i[6],!r)continue;if(n=[...r].length,i[3]||i[4]){a+=n;continue}if((i[5]||i[6])&&s%3&&!((s+n)%3)){o+=n;continue}if(a-=n,a>0)continue;n=Math.min(n,n+a+o);const t=[...e].slice(0,s+i.index+n+1).join("");if(Math.min(s,n)%2){const e=t.slice(1,-1);return{type:"em",raw:t,text:e,tokens:this.lexer.inlineTokens(e)}}const l=t.slice(2,-2);return{type:"strong",raw:t,text:l,tokens:this.lexer.inlineTokens(l)}}}}codespan(e){const t=this.rules.inline.code.exec(e);if(t){let e=t[2].replace(/\n/g," ");const s=/[^ ]/.test(e),i=/^ /.test(e)&&/ $/.test(e);return s&&i&&(e=e.substring(1,e.length-1)),e=N(e,!0),{type:"codespan",raw:t[0],text:e}}}br(e){const t=this.rules.inline.br.exec(e);if(t)return{type:"br",raw:t[0]}}del(e){const t=this.rules.inline.del.exec(e);if(t)return{type:"del",raw:t[0],text:t[2],tokens:this.lexer.inlineTokens(t[2])}}autolink(e){const t=this.rules.inline.autolink.exec(e);if(t){let e,s;return"@"===t[2]?(e=N(t[1]),s="mailto:"+e):(e=N(t[1]),s=e),{type:"link",raw:t[0],text:e,href:s,tokens:[{type:"text",raw:e,text:e}]}}}url(e){let t;if(t=this.rules.inline.url.exec(e)){let e,s;if("@"===t[2])e=N(t[0]),s="mailto:"+e;else{let i;do{i=t[0],t[0]=this.rules.inline._backpedal.exec(t[0])[0]}while(i!==t[0]);e=N(t[0]),s="www."===t[1]?"http://"+t[0]:t[0]}return{type:"link",raw:t[0],text:e,href:s,tokens:[{type:"text",raw:e,text:e}]}}}inlineText(e){const t=this.rules.inline.text.exec(e);if(t){let e;return e=this.lexer.state.inRawBlock?t[0]:N(t[0]),{type:"text",raw:t[0],text:e}}}}const L={newline:/^(?: *(?:\n|$))+/,code:/^( {4}[^\n]+(?:\n(?: *(?:\n|$))*)?)+/,fences:/^ {0,3}(`{3,}(?=[^`\n]*(?:\n|$))|~{3,})([^\n]*)(?:\n|$)(?:|([\s\S]*?)(?:\n|$))(?: {0,3}\1[~`]* *(?=\n|$)|$)/,hr:/^ {0,3}((?:-[\t ]*){3,}|(?:_[ \t]*){3,}|(?:\*[ \t]*){3,})(?:\n+|$)/,heading:/^ {0,3}(#{1,6})(?=\s|$)(.*)(?:\n+|$)/,blockquote:/^( {0,3}> ?(paragraph|[^\n]*)(?:\n|$))+/,list:/^( {0,3}bull)([ \t][^\n]+?)?(?:\n|$)/,html:"^ {0,3}(?:<(script|pre|style|textarea)[\\s>][\\s\\S]*?(?:</\\1>[^\\n]*\\n+|$)|comment[^\\n]*(\\n+|$)|<\\?[\\s\\S]*?(?:\\?>\\n*|$)|<![A-Z][\\s\\S]*?(?:>\\n*|$)|<!\\[CDATA\\[[\\s\\S]*?(?:\\]\\]>\\n*|$)|</?(tag)(?: +|\\n|/?>)[\\s\\S]*?(?:(?:\\n *)+\\n|$)|<(?!script|pre|style|textarea)([a-z][\\w-]*)(?:attribute)*? */?>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n *)+\\n|$)|</(?!script|pre|style|textarea)[a-z][\\w-]*\\s*>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n *)+\\n|$))",def:/^ {0,3}\[(label)\]: *(?:\n *)?([^<\s][^\s]*|<.*?>)(?:(?: +(?:\n *)?| *\n *)(title))? *(?:\n+|$)/,table:U,lheading:/^((?:(?!^bull ).|\n(?!\n|bull ))+?)\n {0,3}(=+|-+) *(?:\n+|$)/,_paragraph:/^([^\n]+(?:\n(?!hr|heading|lheading|blockquote|fences|list|html|table| +\n)[^\n]+)*)/,text:/^[^\n]+/,_label:/(?!\s*\])(?:\\.|[^\[\]\\])+/,_title:/(?:"(?:\\"?|[^"\\])*"|'[^'\n]*(?:\n[^'\n]+)*\n?'|\([^()]*\))/};L.def=I(L.def).replace("label",L._label).replace("title",L._title).getRegex(),L.bullet=/(?:[*+-]|\d{1,9}[.)])/,L.listItemStart=I(/^( *)(bull) */).replace("bull",L.bullet).getRegex(),L.list=I(L.list).replace(/bull/g,L.bullet).replace("hr","\\n+(?=\\1?(?:(?:- *){3,}|(?:_ *){3,}|(?:\\* *){3,})(?:\\n+|$))").replace("def","\\n+(?="+L.def.source+")").getRegex(),L._tag="address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|meta|nav|noframes|ol|optgroup|option|p|param|section|source|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul",L._comment=/<!--(?!-?>)[\s\S]*?(?:-->|$)/,L.html=I(L.html,"i").replace("comment",L._comment).replace("tag",L._tag).replace("attribute",/ +[a-zA-Z:_][\w.:-]*(?: *= *"[^"\n]*"| *= *'[^'\n]*'| *= *[^\s"'=<>`]+)?/).getRegex(),L.lheading=I(L.lheading).replace(/bull/g,L.bullet).getRegex(),L.paragraph=I(L._paragraph).replace("hr",L.hr).replace("heading"," {0,3}#{1,6} ").replace("|lheading","").replace("|table","").replace("blockquote"," {0,3}>").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list"," {0,3}(?:[*+-]|1[.)]) ").replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",L._tag).getRegex(),L.blockquote=I(L.blockquote).replace("paragraph",L.paragraph).getRegex(),L.normal={...L},L.gfm={...L.normal,table:"^ *([^\\n ].*\\|.*)\\n {0,3}(?:\\| *)?(:?-+:? *(?:\\| *:?-+:? *)*)(?:\\| *)?(?:\\n((?:(?! *\\n|hr|heading|blockquote|code|fences|list|html).*(?:\\n|$))*)\\n*|$)"},L.gfm.table=I(L.gfm.table).replace("hr",L.hr).replace("heading"," {0,3}#{1,6} ").replace("blockquote"," {0,3}>").replace("code"," {4}[^\\n]").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list"," {0,3}(?:[*+-]|1[.)]) ").replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",L._tag).getRegex(),L.gfm.paragraph=I(L._paragraph).replace("hr",L.hr).replace("heading"," {0,3}#{1,6} ").replace("|lheading","").replace("table",L.gfm.table).replace("blockquote"," {0,3}>").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list"," {0,3}(?:[*+-]|1[.)]) ").replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",L._tag).getRegex(),L.pedantic={...L.normal,html:I("^ *(?:comment *(?:\\n|\\s*$)|<(tag)[\\s\\S]+?</\\1> *(?:\\n{2,}|\\s*$)|<tag(?:\"[^\"]*\"|'[^']*'|\\s[^'\"/>\\s]*)*?/?> *(?:\\n{2,}|\\s*$))").replace("comment",L._comment).replace(/tag/g,"(?!(?:a|em|strong|small|s|cite|q|dfn|abbr|data|time|code|var|samp|kbd|sub|sup|i|b|u|mark|ruby|rt|rp|bdi|bdo|span|br|wbr|ins|del|img)\\b)\\w+(?!:|[^\\w\\s@]*@)\\b").getRegex(),def:/^ *\[([^\]]+)\]: *<?([^\s>]+)>?(?: +(["(][^\n]+[")]))? *(?:\n+|$)/,heading:/^(#{1,6})(.*)(?:\n+|$)/,fences:U,lheading:/^(.+?)\n {0,3}(=+|-+) *(?:\n+|$)/,paragraph:I(L.normal._paragraph).replace("hr",L.hr).replace("heading"," *#{1,6} *[^\n]").replace("lheading",L.lheading).replace("blockquote"," {0,3}>").replace("|fences","").replace("|list","").replace("|html","").getRegex()};const q={escape:/^\\([!"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])/,autolink:/^<(scheme:[^\s\x00-\x1f<>]*|email)>/,url:U,tag:"^comment|^</[a-zA-Z][\\w:-]*\\s*>|^<[a-zA-Z][\\w-]*(?:attribute)*?\\s*/?>|^<\\?[\\s\\S]*?\\?>|^<![a-zA-Z]+\\s[\\s\\S]*?>|^<!\\[CDATA\\[[\\s\\S]*?\\]\\]>",link:/^!?\[(label)\]\(\s*(href)(?:\s+(title))?\s*\)/,reflink:/^!?\[(label)\]\[(ref)\]/,nolink:/^!?\[(ref)\](?:\[\])?/,reflinkSearch:"reflink|nolink(?!\\()",emStrong:{lDelim:/^(?:\*+(?:((?!\*)[punct])|[^\s*]))|^_+(?:((?!_)[punct])|([^\s_]))/,rDelimAst:/^[^_*]*?__[^_*]*?\*[^_*]*?(?=__)|[^*]+(?=[^*])|(?!\*)[punct](\*+)(?=[\s]|$)|[^punct\s](\*+)(?!\*)(?=[punct\s]|$)|(?!\*)[punct\s](\*+)(?=[^punct\s])|[\s](\*+)(?!\*)(?=[punct])|(?!\*)[punct](\*+)(?!\*)(?=[punct])|[^punct\s](\*+)(?=[^punct\s])/,rDelimUnd:/^[^_*]*?\*\*[^_*]*?_[^_*]*?(?=\*\*)|[^_]+(?=[^_])|(?!_)[punct](_+)(?=[\s]|$)|[^punct\s](_+)(?!_)(?=[punct\s]|$)|(?!_)[punct\s](_+)(?=[^punct\s])|[\s](_+)(?!_)(?=[punct])|(?!_)[punct](_+)(?!_)(?=[punct])/},code:/^(`+)([^`]|[^`][\s\S]*?[^`])\1(?!`)/,br:/^( {2,}|\\)\n(?!\s*$)/,del:U,text:/^(`+|[^`])(?:(?= {2,}\n)|[\s\S]*?(?:(?=[\\<!\[`*_]|\b_|$)|[^ ](?= {2,}\n)))/,punctuation:/^((?![*_])[\spunctuation])/,_punctuation:"\\p{P}$+<=>`^|~"};q.punctuation=I(q.punctuation,"u").replace(/punctuation/g,q._punctuation).getRegex(),q.blockSkip=/\[[^[\]]*?\]\([^\(\)]*?\)|`[^`]*?`|<[^<>]*?>/g,q.anyPunctuation=/\\[punct]/g,q._escapes=/\\([punct])/g,q._comment=I(L._comment).replace("(?:--\x3e|$)","--\x3e").getRegex(),q.emStrong.lDelim=I(q.emStrong.lDelim,"u").replace(/punct/g,q._punctuation).getRegex(),q.emStrong.rDelimAst=I(q.emStrong.rDelimAst,"gu").replace(/punct/g,q._punctuation).getRegex(),q.emStrong.rDelimUnd=I(q.emStrong.rDelimUnd,"gu").replace(/punct/g,q._punctuation).getRegex(),q.anyPunctuation=I(q.anyPunctuation,"gu").replace(/punct/g,q._punctuation).getRegex(),q._escapes=I(q._escapes,"gu").replace(/punct/g,q._punctuation).getRegex(),q._scheme=/[a-zA-Z][a-zA-Z0-9+.-]{1,31}/,q._email=/[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+(@)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+(?![-_])/,q.autolink=I(q.autolink).replace("scheme",q._scheme).replace("email",q._email).getRegex(),q._attribute=/\s+[a-zA-Z:_][\w.:-]*(?:\s*=\s*"[^"]*"|\s*=\s*'[^']*'|\s*=\s*[^\s"'=<>`]+)?/,q.tag=I(q.tag).replace("comment",q._comment).replace("attribute",q._attribute).getRegex(),q._label=/(?:\[(?:\\.|[^\[\]\\])*\]|\\.|`[^`]*`|[^\[\]\\`])*?/,q._href=/<(?:\\.|[^\n<>\\])+>|[^\s\x00-\x1f]*/,q._title=/"(?:\\"?|[^"\\])*"|'(?:\\'?|[^'\\])*'|\((?:\\\)?|[^)\\])*\)/,q.link=I(q.link).replace("label",q._label).replace("href",q._href).replace("title",q._title).getRegex(),q.reflink=I(q.reflink).replace("label",q._label).replace("ref",L._label).getRegex(),q.nolink=I(q.nolink).replace("ref",L._label).getRegex(),q.reflinkSearch=I(q.reflinkSearch,"g").replace("reflink",q.reflink).replace("nolink",q.nolink).getRegex(),q.normal={...q},q.pedantic={...q.normal,strong:{start:/^__|\*\*/,middle:/^__(?=\S)([\s\S]*?\S)__(?!_)|^\*\*(?=\S)([\s\S]*?\S)\*\*(?!\*)/,endAst:/\*\*(?!\*)/g,endUnd:/__(?!_)/g},em:{start:/^_|\*/,middle:/^()\*(?=\S)([\s\S]*?\S)\*(?!\*)|^_(?=\S)([\s\S]*?\S)_(?!_)/,endAst:/\*(?!\*)/g,endUnd:/_(?!_)/g},link:I(/^!?\[(label)\]\((.*?)\)/).replace("label",q._label).getRegex(),reflink:I(/^!?\[(label)\]\s*\[([^\]]*)\]/).replace("label",q._label).getRegex()},q.gfm={...q.normal,escape:I(q.escape).replace("])","~|])").getRegex(),_extended_email:/[A-Za-z0-9._+-]+(@)[a-zA-Z0-9-_]+(?:\.[a-zA-Z0-9-_]*[a-zA-Z0-9])+(?![-_])/,url:/^((?:ftp|https?):\/\/|www\.)(?:[a-zA-Z0-9\-]+\.?)+[^\s<]*|^email/,_backpedal:/(?:[^?!.,:;*_'"~()&]+|\([^)]*\)|&(?![a-zA-Z0-9]+;$)|[?!.,:;*_'"~)]+(?!$))+/,del:/^(~~?)(?=[^\s~])([\s\S]*?[^\s~])\1(?=[^~]|$)/,text:/^([`~]+|[^`~])(?:(?= {2,}\n)|(?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)|[\s\S]*?(?:(?=[\\<!\[`*~_]|\b_|https?:\/\/|ftp:\/\/|www\.|$)|[^ ](?= {2,}\n)|[^a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-](?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)))/},q.gfm.url=I(q.gfm.url,"i").replace("email",q.gfm._extended_email).getRegex(),q.breaks={...q.gfm,br:I(q.br).replace("{2,}","*").getRegex(),text:I(q.gfm.text).replace("\\b_","\\b_| {2,}\\n").replace(/\{2,\}/g,"*").getRegex()};class B{tokens;options;state;tokenizer;inlineQueue;constructor(e){this.tokens=[],this.tokens.links=Object.create(null),this.options=e||k,this.options.tokenizer=this.options.tokenizer||new M,this.tokenizer=this.options.tokenizer,this.tokenizer.options=this.options,this.tokenizer.lexer=this,this.inlineQueue=[],this.state={inLink:!1,inRawBlock:!1,top:!0};const t={block:L.normal,inline:q.normal};this.options.pedantic?(t.block=L.pedantic,t.inline=q.pedantic):this.options.gfm&&(t.block=L.gfm,this.options.breaks?t.inline=q.breaks:t.inline=q.gfm),this.tokenizer.rules=t}static get rules(){return{block:L,inline:q}}static lex(e,t){return new B(t).lex(e)}static lexInline(e,t){return new B(t).inlineTokens(e)}lex(e){let t;for(e=e.replace(/\r\n|\r/g,"\n"),this.blockTokens(e,this.tokens);t=this.inlineQueue.shift();)this.inlineTokens(t.src,t.tokens);return this.tokens}blockTokens(e,t=[]){let s,i,r,n;for(e=this.options.pedantic?e.replace(/\t/g,"    ").replace(/^ +$/gm,""):e.replace(/^( *)(\t+)/gm,((e,t,s)=>t+"    ".repeat(s.length)));e;)if(!(this.options.extensions&&this.options.extensions.block&&this.options.extensions.block.some((i=>!!(s=i.call({lexer:this},e,t))&&(e=e.substring(s.raw.length),t.push(s),!0)))))if(s=this.tokenizer.space(e))e=e.substring(s.raw.length),1===s.raw.length&&t.length>0?t[t.length-1].raw+="\n":t.push(s);else if(s=this.tokenizer.code(e))e=e.substring(s.raw.length),i=t[t.length-1],!i||"paragraph"!==i.type&&"text"!==i.type?t.push(s):(i.raw+="\n"+s.raw,i.text+="\n"+s.text,this.inlineQueue[this.inlineQueue.length-1].src=i.text);else if(s=this.tokenizer.fences(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.heading(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.hr(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.blockquote(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.list(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.html(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.def(e))e=e.substring(s.raw.length),i=t[t.length-1],!i||"paragraph"!==i.type&&"text"!==i.type?this.tokens.links[s.tag]||(this.tokens.links[s.tag]={href:s.href,title:s.title}):(i.raw+="\n"+s.raw,i.text+="\n"+s.raw,this.inlineQueue[this.inlineQueue.length-1].src=i.text);else if(s=this.tokenizer.table(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.lheading(e))e=e.substring(s.raw.length),t.push(s);else{if(r=e,this.options.extensions&&this.options.extensions.startBlock){let t=1/0;const s=e.slice(1);let i;this.options.extensions.startBlock.forEach((e=>{i=e.call({lexer:this},s),"number"==typeof i&&i>=0&&(t=Math.min(t,i))})),t<1/0&&t>=0&&(r=e.substring(0,t+1))}if(this.state.top&&(s=this.tokenizer.paragraph(r)))i=t[t.length-1],n&&"paragraph"===i.type?(i.raw+="\n"+s.raw,i.text+="\n"+s.text,this.inlineQueue.pop(),this.inlineQueue[this.inlineQueue.length-1].src=i.text):t.push(s),n=r.length!==e.length,e=e.substring(s.raw.length);else if(s=this.tokenizer.text(e))e=e.substring(s.raw.length),i=t[t.length-1],i&&"text"===i.type?(i.raw+="\n"+s.raw,i.text+="\n"+s.text,this.inlineQueue.pop(),this.inlineQueue[this.inlineQueue.length-1].src=i.text):t.push(s);else if(e){const t="Infinite loop on byte: "+e.charCodeAt(0);if(this.options.silent){console.error(t);break}throw new Error(t)}}return this.state.top=!0,t}inline(e,t=[]){return this.inlineQueue.push({src:e,tokens:t}),t}inlineTokens(e,t=[]){let s,i,r,n,a,o,l=e;if(this.tokens.links){const e=Object.keys(this.tokens.links);if(e.length>0)for(;null!=(n=this.tokenizer.rules.inline.reflinkSearch.exec(l));)e.includes(n[0].slice(n[0].lastIndexOf("[")+1,-1))&&(l=l.slice(0,n.index)+"["+"a".repeat(n[0].length-2)+"]"+l.slice(this.tokenizer.rules.inline.reflinkSearch.lastIndex))}for(;null!=(n=this.tokenizer.rules.inline.blockSkip.exec(l));)l=l.slice(0,n.index)+"["+"a".repeat(n[0].length-2)+"]"+l.slice(this.tokenizer.rules.inline.blockSkip.lastIndex);for(;null!=(n=this.tokenizer.rules.inline.anyPunctuation.exec(l));)l=l.slice(0,n.index)+"++"+l.slice(this.tokenizer.rules.inline.anyPunctuation.lastIndex);for(;e;)if(a||(o=""),a=!1,!(this.options.extensions&&this.options.extensions.inline&&this.options.extensions.inline.some((i=>!!(s=i.call({lexer:this},e,t))&&(e=e.substring(s.raw.length),t.push(s),!0)))))if(s=this.tokenizer.escape(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.tag(e))e=e.substring(s.raw.length),i=t[t.length-1],i&&"text"===s.type&&"text"===i.type?(i.raw+=s.raw,i.text+=s.text):t.push(s);else if(s=this.tokenizer.link(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.reflink(e,this.tokens.links))e=e.substring(s.raw.length),i=t[t.length-1],i&&"text"===s.type&&"text"===i.type?(i.raw+=s.raw,i.text+=s.text):t.push(s);else if(s=this.tokenizer.emStrong(e,l,o))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.codespan(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.br(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.del(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.autolink(e))e=e.substring(s.raw.length),t.push(s);else if(this.state.inLink||!(s=this.tokenizer.url(e))){if(r=e,this.options.extensions&&this.options.extensions.startInline){let t=1/0;const s=e.slice(1);let i;this.options.extensions.startInline.forEach((e=>{i=e.call({lexer:this},s),"number"==typeof i&&i>=0&&(t=Math.min(t,i))})),t<1/0&&t>=0&&(r=e.substring(0,t+1))}if(s=this.tokenizer.inlineText(r))e=e.substring(s.raw.length),"_"!==s.raw.slice(-1)&&(o=s.raw.slice(-1)),a=!0,i=t[t.length-1],i&&"text"===i.type?(i.raw+=s.raw,i.text+=s.text):t.push(s);else if(e){const t="Infinite loop on byte: "+e.charCodeAt(0);if(this.options.silent){console.error(t);break}throw new Error(t)}}else e=e.substring(s.raw.length),t.push(s);return t}}class D{options;constructor(e){this.options=e||k}code(e,t,s){const i=(t||"").match(/^\S*/)?.[0];return e=e.replace(/\n$/,"")+"\n",i?'<pre><code class="language-'+N(i)+'">'+(s?e:N(e,!0))+"</code></pre>\n":"<pre><code>"+(s?e:N(e,!0))+"</code></pre>\n"}blockquote(e){return`<blockquote>\n${e}</blockquote>\n`}html(e,t){return e}heading(e,t,s){return`<h${t}>${e}</h${t}>\n`}hr(){return"<hr>\n"}list(e,t,s){const i=t?"ol":"ul";return"<"+i+(t&&1!==s?' start="'+s+'"':"")+">\n"+e+"</"+i+">\n"}listitem(e,t,s){return`<li>${e}</li>\n`}checkbox(e){return"<input "+(e?'checked="" ':"")+'disabled="" type="checkbox">'}paragraph(e){return`<p>${e}</p>\n`}table(e,t){return t&&(t=`<tbody>${t}</tbody>`),"<table>\n<thead>\n"+e+"</thead>\n"+t+"</table>\n"}tablerow(e){return`<tr>\n${e}</tr>\n`}tablecell(e,t){const s=t.header?"th":"td";return(t.align?`<${s} align="${t.align}">`:`<${s}>`)+e+`</${s}>\n`}strong(e){return`<strong>${e}</strong>`}em(e){return`<em>${e}</em>`}codespan(e){return`<code>${e}</code>`}br(){return"<br>"}del(e){return`<del>${e}</del>`}link(e,t,s){const i=O(e);if(null===i)return s;let r='<a href="'+(e=i)+'"';return t&&(r+=' title="'+t+'"'),r+=">"+s+"</a>",r}image(e,t,s){const i=O(e);if(null===i)return s;let r=`<img src="${e=i}" alt="${s}"`;return t&&(r+=` title="${t}"`),r+=">",r}text(e){return e}}class F{strong(e){return e}em(e){return e}codespan(e){return e}del(e){return e}html(e){return e}text(e){return e}link(e,t,s){return""+s}image(e,t,s){return""+s}br(){return""}}class V{options;renderer;textRenderer;constructor(e){this.options=e||k,this.options.renderer=this.options.renderer||new D,this.renderer=this.options.renderer,this.renderer.options=this.options,this.textRenderer=new F}static parse(e,t){return new V(t).parse(e)}static parseInline(e,t){return new V(t).parseInline(e)}parse(e,t=!0){let s="";for(let i=0;i<e.length;i++){const r=e[i];if(this.options.extensions&&this.options.extensions.renderers&&this.options.extensions.renderers[r.type]){const e=r,t=this.options.extensions.renderers[e.type].call({parser:this},e);if(!1!==t||!["space","hr","heading","code","table","blockquote","list","html","paragraph","text"].includes(e.type)){s+=t||"";continue}}switch(r.type){case"space":continue;case"hr":s+=this.renderer.hr();continue;case"heading":{const e=r;s+=this.renderer.heading(this.parseInline(e.tokens),e.depth,this.parseInline(e.tokens,this.textRenderer).replace(j,((e,t)=>"colon"===(t=t.toLowerCase())?":":"#"===t.charAt(0)?"x"===t.charAt(1)?String.fromCharCode(parseInt(t.substring(2),16)):String.fromCharCode(+t.substring(1)):"")));continue}case"code":{const e=r;s+=this.renderer.code(e.text,e.lang,!!e.escaped);continue}case"table":{const e=r;let t="",i="";for(let t=0;t<e.header.length;t++)i+=this.renderer.tablecell(this.parseInline(e.header[t].tokens),{header:!0,align:e.align[t]});t+=this.renderer.tablerow(i);let n="";for(let t=0;t<e.rows.length;t++){const s=e.rows[t];i="";for(let t=0;t<s.length;t++)i+=this.renderer.tablecell(this.parseInline(s[t].tokens),{header:!1,align:e.align[t]});n+=this.renderer.tablerow(i)}s+=this.renderer.table(t,n);continue}case"blockquote":{const e=r,t=this.parse(e.tokens);s+=this.renderer.blockquote(t);continue}case"list":{const e=r,t=e.ordered,i=e.start,n=e.loose;let a="";for(let t=0;t<e.items.length;t++){const s=e.items[t],i=s.checked,r=s.task;let o="";if(s.task){const e=this.renderer.checkbox(!!i);n?s.tokens.length>0&&"paragraph"===s.tokens[0].type?(s.tokens[0].text=e+" "+s.tokens[0].text,s.tokens[0].tokens&&s.tokens[0].tokens.length>0&&"text"===s.tokens[0].tokens[0].type&&(s.tokens[0].tokens[0].text=e+" "+s.tokens[0].tokens[0].text)):s.tokens.unshift({type:"text",text:e+" "}):o+=e+" "}o+=this.parse(s.tokens,n),a+=this.renderer.listitem(o,r,!!i)}s+=this.renderer.list(a,t,i);continue}case"html":{const e=r;s+=this.renderer.html(e.text,e.block);continue}case"paragraph":{const e=r;s+=this.renderer.paragraph(this.parseInline(e.tokens));continue}case"text":{let n=r,a=n.tokens?this.parseInline(n.tokens):n.text;for(;i+1<e.length&&"text"===e[i+1].type;)n=e[++i],a+="\n"+(n.tokens?this.parseInline(n.tokens):n.text);s+=t?this.renderer.paragraph(a):a;continue}default:{const e='Token with "'+r.type+'" type was not found.';if(this.options.silent)return console.error(e),"";throw new Error(e)}}}return s}parseInline(e,t){t=t||this.renderer;let s="";for(let i=0;i<e.length;i++){const r=e[i];if(this.options.extensions&&this.options.extensions.renderers&&this.options.extensions.renderers[r.type]){const e=this.options.extensions.renderers[r.type].call({parser:this},r);if(!1!==e||!["escape","html","link","image","strong","em","codespan","br","del","text"].includes(r.type)){s+=e||"";continue}}switch(r.type){case"escape":{const e=r;s+=t.text(e.text);break}case"html":{const e=r;s+=t.html(e.text);break}case"link":{const e=r;s+=t.link(e.href,e.title,this.parseInline(e.tokens,t));break}case"image":{const e=r;s+=t.image(e.href,e.title,e.text);break}case"strong":{const e=r;s+=t.strong(this.parseInline(e.tokens,t));break}case"em":{const e=r;s+=t.em(this.parseInline(e.tokens,t));break}case"codespan":{const e=r;s+=t.codespan(e.text);break}case"br":s+=t.br();break;case"del":{const e=r;s+=t.del(this.parseInline(e.tokens,t));break}case"text":{const e=r;s+=t.text(e.text);break}default:{const e='Token with "'+r.type+'" type was not found.';if(this.options.silent)return console.error(e),"";throw new Error(e)}}}return s}}class Z{options;constructor(e){this.options=e||k}static passThroughHooks=new Set(["preprocess","postprocess"]);preprocess(e){return e}postprocess(e){return e}}const Q=new class{defaults={async:!1,breaks:!1,extensions:null,gfm:!0,hooks:null,pedantic:!1,renderer:null,silent:!1,tokenizer:null,walkTokens:null};options=this.setOptions;parse=this.#e(B.lex,V.parse);parseInline=this.#e(B.lexInline,V.parseInline);Parser=V;parser=V.parse;Renderer=D;TextRenderer=F;Lexer=B;lexer=B.lex;Tokenizer=M;Hooks=Z;constructor(...e){this.use(...e)}walkTokens(e,t){let s=[];for(const i of e)switch(s=s.concat(t.call(this,i)),i.type){case"table":{const e=i;for(const i of e.header)s=s.concat(this.walkTokens(i.tokens,t));for(const i of e.rows)for(const e of i)s=s.concat(this.walkTokens(e.tokens,t));break}case"list":{const e=i;s=s.concat(this.walkTokens(e.items,t));break}default:{const e=i;this.defaults.extensions?.childTokens?.[e.type]?this.defaults.extensions.childTokens[e.type].forEach((i=>{s=s.concat(this.walkTokens(e[i],t))})):e.tokens&&(s=s.concat(this.walkTokens(e.tokens,t)))}}return s}use(...e){const t=this.defaults.extensions||{renderers:{},childTokens:{}};return e.forEach((e=>{const s={...e};if(s.async=this.defaults.async||s.async||!1,e.extensions&&(e.extensions.forEach((e=>{if(!e.name)throw new Error("extension name required");if("renderer"in e){const s=t.renderers[e.name];t.renderers[e.name]=s?function(...t){let i=e.renderer.apply(this,t);return!1===i&&(i=s.apply(this,t)),i}:e.renderer}if("tokenizer"in e){if(!e.level||"block"!==e.level&&"inline"!==e.level)throw new Error("extension level must be 'block' or 'inline'");const s=t[e.level];s?s.unshift(e.tokenizer):t[e.level]=[e.tokenizer],e.start&&("block"===e.level?t.startBlock?t.startBlock.push(e.start):t.startBlock=[e.start]:"inline"===e.level&&(t.startInline?t.startInline.push(e.start):t.startInline=[e.start]))}"childTokens"in e&&e.childTokens&&(t.childTokens[e.name]=e.childTokens)})),s.extensions=t),e.renderer){const t=this.defaults.renderer||new D(this.defaults);for(const s in e.renderer){const i=e.renderer[s],r=s,n=t[r];t[r]=(...e)=>{let s=i.apply(t,e);return!1===s&&(s=n.apply(t,e)),s||""}}s.renderer=t}if(e.tokenizer){const t=this.defaults.tokenizer||new M(this.defaults);for(const s in e.tokenizer){const i=e.tokenizer[s],r=s,n=t[r];t[r]=(...e)=>{let s=i.apply(t,e);return!1===s&&(s=n.apply(t,e)),s}}s.tokenizer=t}if(e.hooks){const t=this.defaults.hooks||new Z;for(const s in e.hooks){const i=e.hooks[s],r=s,n=t[r];Z.passThroughHooks.has(s)?t[r]=e=>{if(this.defaults.async)return Promise.resolve(i.call(t,e)).then((e=>n.call(t,e)));const s=i.call(t,e);return n.call(t,s)}:t[r]=(...e)=>{let s=i.apply(t,e);return!1===s&&(s=n.apply(t,e)),s}}s.hooks=t}if(e.walkTokens){const t=this.defaults.walkTokens,i=e.walkTokens;s.walkTokens=function(e){let s=[];return s.push(i.call(this,e)),t&&(s=s.concat(t.call(this,e))),s}}this.defaults={...this.defaults,...s}})),this}setOptions(e){return this.defaults={...this.defaults,...e},this}#e(e,t){return(s,i)=>{const r={...i},n={...this.defaults,...r};!0===this.defaults.async&&!1===r.async&&(n.silent||console.warn("marked(): The async option was set to true by an extension. The async: false option sent to parse will be ignored."),n.async=!0);const a=this.#t(!!n.silent,!!n.async);if(null==s)return a(new Error("marked(): input parameter is undefined or null"));if("string"!=typeof s)return a(new Error("marked(): input parameter is of type "+Object.prototype.toString.call(s)+", string expected"));if(n.hooks&&(n.hooks.options=n),n.async)return Promise.resolve(n.hooks?n.hooks.preprocess(s):s).then((t=>e(t,n))).then((e=>n.walkTokens?Promise.all(this.walkTokens(e,n.walkTokens)).then((()=>e)):e)).then((e=>t(e,n))).then((e=>n.hooks?n.hooks.postprocess(e):e)).catch(a);try{n.hooks&&(s=n.hooks.preprocess(s));const i=e(s,n);n.walkTokens&&this.walkTokens(i,n.walkTokens);let r=t(i,n);return n.hooks&&(r=n.hooks.postprocess(r)),r}catch(e){return a(e)}}}#t(e,t){return s=>{if(s.message+="\nPlease report this to https://github.com/markedjs/marked.",e){const e="<p>An error occurred:</p><pre>"+N(s.message+"",!0)+"</pre>";return t?Promise.resolve(e):e}if(t)return Promise.reject(s);throw s}}};function G(e,t){return Q.parse(e,t)}G.options=G.setOptions=function(e){return Q.setOptions(e),G.defaults=Q.defaults,x(G.defaults),G},G.getDefaults=v,G.defaults=k,G.use=function(...e){return Q.use(...e),G.defaults=Q.defaults,x(G.defaults),G},G.walkTokens=function(e,t){return Q.walkTokens(e,t)},G.parseInline=Q.parseInline,G.Parser=V,G.parser=V.parse,G.Renderer=D,G.TextRenderer=F,G.Lexer=B,G.lexer=B.lex,G.Tokenizer=M,G.Hooks=Z,G.parse=G,G.options,G.setOptions,G.use,G.walkTokens,G.parseInline;let H=class extends p{constructor(){super(),this.condition="running",this.sessions=0,this.jobs=Object(),this.agents=0,this.is_admin=!1,this.is_superadmin=!1,this.resources=Object(),this.update_checker=Object(),this.authenticated=!1,this.manager_version="",this.webui_version="",this.cpu_total=0,this.cpu_used=0,this.cpu_percent="0",this.cpu_total_percent="0",this.cpu_total_usage_ratio=0,this.cpu_current_usage_ratio=0,this.mem_total="0",this.mem_used="0",this.mem_allocated="0",this.mem_total_usage_ratio=0,this.mem_current_usage_ratio=0,this.mem_current_usage_percent="0",this.cuda_gpu_total=0,this.cuda_gpu_used=0,this.cuda_fgpu_total=0,this.cuda_fgpu_used=0,this.rocm_gpu_total=0,this.rocm_gpu_used=0,this.tpu_total=0,this.tpu_used=0,this.ipu_total=0,this.ipu_used=0,this.atom_total=0,this.atom_used=0,this.notification=Object(),this.announcement="",this.invitations=Object(),this.downloadAppOS="",this.invitations=[],this.appDownloadMap={Linux:{os:"linux",architecture:["arm64","x64"],extension:"zip"},MacOS:{os:"macos",architecture:["intel","apple"],extension:"dmg"},Windows:{os:"win32",architecture:["arm64","x64"],extension:"zip"}}}static get styles(){return[u,r,n,d,a`
        ul {
          padding-left: 0;
        }

        ul li {
          list-style: none;
          font-size: 14px;
        }

        li:before {
          padding: 3px;
          transform: rotate(-45deg) translateY(-2px);
          transition: color ease-in 0.2s;
          border: solid;
          border-width: 0 2px 2px 0;
          border-color: #242424;
          margin-right: 10px;
          content: '';
          display: inline-block;
        }

        span.indicator {
          width: 100px;
        }

        div.big.indicator {
          font-size: 48px;
        }

        a,
        a:visited {
          color: #222222;
        }

        a:hover {
          color: #3e872d;
        }

        mwc-button,
        mwc-button[unelevated],
        mwc-button[outlined] {
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
          --mdc-typography-font-family: var(--general-font-family);
        }

        .notice-ticker {
          margin-left: 15px;
          margin-top: 10px;
          font-size: 13px;
          font-weight: 400;
          max-height: 55px;
          max-width: 1000px;
          overflow-y: scroll;
        }

        .notice-ticker > span {
          display: inline-block;
          white-space: pre-line;
          font-size: 1rem;
        }

        .notice-ticker lablup-shields {
          margin-right: 15px;
        }

        #session-launcher {
          --component-width: 284px;
        }

        .start-menu-items {
          margin-top: 20px;
          width: 100px;
        }

        .start-menu-items span {
          padding-left: 10px;
          padding-right: 10px;
          text-align: center;
        }

        .invitation_folder_name {
          font-size: 13px;
        }

        mwc-icon-button.update-button {
          --mdc-icon-size: 16px;
          --mdc-icon-button-size: 24px;
          color: red;
        }

        a > i {
          color: #5b5b5b;
          margin: 10px;
        }

        a > span {
          max-width: 70px;
          color: #838383;
        }

        mwc-icon.update-icon {
          --mdc-icon-size: 16px;
          --mdc-icon-button-size: 24px;
          color: black;
        }

        img.resource-type-icon {
          width: 16px;
          height: 16px;
          margin-right: 5px;
        }

        .system-health-indicator {
          width: 90px;
        }

        .upper-lower-space {
          padding-top: 20px;
          padding-bottom: 10px;
        }

        i.larger {
          font-size: 1.2rem;
        }

        .left-end-icon {
          margin-left: 11px;
          margin-right: 12px;
        }

        .right-end-icon {
          margin-left: 12px;
          margin-right: 11px;
        }

        #download-app-os-select-box {
          height: 80px;
          padding-top: 20px;
          padding-left: 20px;
          background-color: #f6f6f6;
          margin-bottom: 15px;
        }

        #download-app-os-select-box mwc-select {
          width: 305px;
          height: 58px;
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

        lablup-activity-panel.inner-panel:hover {
          --card-background-color: var(--general-sidepanel-color);
        }

        @media screen and (max-width: 899px) {
          .notice-ticker {
            justify-content: left !important;
          }
        }

        @media screen and (max-width: 850px) {
          .notice-ticker {
            margin-left: 0px;
            width: auto;
          }

          .notice-ticker > span {
            max-width: 250px;
            line-height: 1em;
          }
        }

        @media screen and (max-width: 750px) {
          lablup-activity-panel.footer-menu > div > a > div > span {
            text-align: left;
            width: 250px;
          }
        }
      `]}firstUpdated(){var e;this.notification=globalThis.lablupNotification,this.update_checker=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#update-checker"),this._getUserOS(),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._readAnnouncement()}),!0):this._readAnnouncement()}_getUserOS(){this.downloadAppOS="MacOS",-1!=navigator.userAgent.indexOf("Mac")&&(this.downloadAppOS="MacOS"),-1!=navigator.userAgent.indexOf("Win")&&(this.downloadAppOS="Windows"),-1!=navigator.userAgent.indexOf("Linux")&&(this.downloadAppOS="Linux")}_refreshConsoleUpdateInformation(){this.is_superadmin&&globalThis.backendaioptions.get("automatic_update_check",!0)&&this.update_checker.checkRelease()}async _viewStateChanged(e){await this.updateComplete,!1!==e?(this.resourceMonitor.setAttribute("active","true"),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_superadmin=globalThis.backendaiclient.is_superadmin,this.is_admin=globalThis.backendaiclient.is_admin,this.authenticated=!0,this.manager_version=globalThis.backendaiclient.managerVersion,this.webui_version=globalThis.packageVersion,this.appDownloadUrl=globalThis.backendaiclient._config.appDownloadUrl,this.activeConnected&&this._refreshConsoleUpdateInformation(),this._refreshInvitations()}),!0):(this.is_superadmin=globalThis.backendaiclient.is_superadmin,this.is_admin=globalThis.backendaiclient.is_admin,this.authenticated=!0,this.manager_version=globalThis.backendaiclient.managerVersion,this.webui_version=globalThis.packageVersion,this.appDownloadUrl=globalThis.backendaiclient._config.appDownloadUrl,this._refreshConsoleUpdateInformation(),this._refreshInvitations())):this.resourceMonitor.removeAttribute("active")}_readAnnouncement(){this.activeConnected&&globalThis.backendaiclient.service.get_announcement().then((e=>{"message"in e&&(this.announcement=G(e.message))})).catch((e=>{}))}_toInt(e){return Math.ceil(e)}_countObject(e){return Object.keys(e).length}_addComma(e){if(void 0===e)return"";return e.toString().replace(/\B(?=(\d{3})+(?!\d))/g,",")}_refreshInvitations(e=!1){this.activeConnected&&globalThis.backendaiclient.vfolder.invitations().then((t=>{this.invitations=t.invitations,this.active&&!e&&setTimeout((()=>{this._refreshInvitations()}),6e4)}))}async _acceptInvitation(e,t){if(!this.activeConnected)return;const s=e.target.closest("lablup-activity-panel");try{s.setAttribute("disabled","true"),s.querySelectorAll("mwc-button").forEach((e=>{e.setAttribute("disabled","true")})),await globalThis.backendaiclient.vfolder.accept_invitation(t.id),this.notification.text=l("summary.AcceptSharedVFolder")+`${t.vfolder_name}`,this.notification.show(),this._refreshInvitations()}catch(e){s.setAttribute("disabled","false"),s.querySelectorAll("mwc-button").forEach((e=>{e.setAttribute("disabled","false")})),this.notification.text=h.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}}async _deleteInvitation(e,t){if(!this.activeConnected)return;const s=e.target.closest("lablup-activity-panel");try{s.setAttribute("disabled","true"),s.querySelectorAll("mwc-button").forEach((e=>{e.setAttribute("disabled","true")})),await globalThis.backendaiclient.vfolder.delete_invitation(t.id),this.notification.text=l("summary.DeclineSharedVFolder")+`${t.vfolder_name}`,this.notification.show(),this._refreshInvitations()}catch(e){s.setAttribute("disabled","false"),s.querySelectorAll("mwc-button").forEach((e=>{e.setAttribute("disabled","false")})),this.notification.text=h.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}}_stripHTMLTags(e){return e.replace(/(<([^>]+)>)/gi,"")}_updateSelectedDownloadAppOS(e){this.downloadAppOS=e.target.value}_downloadApplication(e){let t="";const s=e.target.innerText.toLowerCase(),i=globalThis.packageVersion,r=this.appDownloadMap[this.downloadAppOS].os,n=this.appDownloadMap[this.downloadAppOS].extension;t=`${this.appDownloadUrl}/v${i}/backend.ai-desktop-${i}-${r}-${s}.${n}`,window.open(t,"_blank")}render(){return o`
      <link rel="stylesheet" href="/resources/fonts/font-awesome-all.min.css" />
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="item" elevation="1" class="vertical layout center wrap flex">
        ${""!=this.announcement?o`
              <div class="notice-ticker horizontal layout wrap flex">
                <lablup-shields
                  app=""
                  color="red"
                  description="Notice"
                  ui="round"
                ></lablup-shields>
                <span>${this._stripHTMLTags(this.announcement)}</span>
              </div>
            `:o``}
        <div class="horizontal wrap layout">
          <lablup-activity-panel
            title="${g("summary.StartMenu")}"
            elevation="1"
            height="500"
          >
            <div slot="message">
              <img
                src="/resources/images/launcher-background.png"
                style="width:300px;margin-bottom:30px;"
              />
              <div class="horizontal center-justified layout wrap">
                <backend-ai-session-launcher
                  location="summary"
                  id="session-launcher"
                  ?active="${!0===this.active}"
                ></backend-ai-session-launcher>
              </div>
              <div class="horizontal center-justified layout wrap">
                <a
                  href="/data"
                  class="vertical center center-justified layout start-menu-items"
                >
                  <i class="fas fa-upload fa-2x"></i>
                  <span>${g("summary.UploadFiles")}</span>
                </a>
                ${this.is_admin?o`
                      <a
                        href="/credential?action=add"
                        class="vertical center center-justified layout start-menu-items"
                        style="border-left:1px solid #ccc;"
                      >
                        <i class="fas fa-key fa-2x"></i>
                        <span>${g("summary.CreateANewKeypair")}</span>
                      </a>
                      <a
                        href="/credential"
                        class="vertical center center-justified layout start-menu-items"
                        style="border-left:1px solid #ccc;"
                      >
                        <i class="fas fa-cogs fa-2x"></i>
                        <span>${g("summary.MaintainKeypairs")}</span>
                      </a>
                    `:o``}
              </div>
            </div>
          </lablup-activity-panel>
          <lablup-activity-panel
            title="${g("summary.ResourceStatistics")}"
            elevation="1"
            narrow
            height="500"
          >
            <div slot="message">
              <backend-ai-resource-monitor
                location="summary"
                id="resource-monitor"
                ?active="${!0===this.active}"
                direction="vertical"
              ></backend-ai-resource-monitor>
            </div>
          </lablup-activity-panel>
          <backend-ai-resource-panel
            ?active="${!0===this.active}"
            height="500"
          ></backend-ai-resource-panel>
          <div class="horizontal wrap layout">
            <lablup-activity-panel
              title="${g("summary.Announcement")}"
              elevation="1"
              horizontalsize="2x"
              height="245"
            >
              <div slot="message" style="max-height:150px; overflow:scroll">
                ${""!==this.announcement?b(this.announcement):g("summary.NoAnnouncement")}
              </div>
            </lablup-activity-panel>
            <lablup-activity-panel
              title="${g("summary.Invitation")}"
              elevation="1"
              height="245"
              scrollableY
            >
              <div slot="message">
                ${this.invitations.length>0?this.invitations.map(((e,t)=>o`
                        <lablup-activity-panel
                          class="inner-panel"
                          noheader
                          autowidth
                          elevation="0"
                          height="130"
                        >
                          <div slot="message">
                            <div class="wrap layout">
                              <h3 style="padding-top:10px;">
                                From ${e.inviter}
                              </h3>
                              <span class="invitation_folder_name">
                                ${g("summary.FolderName")}:
                                ${e.vfolder_name}
                              </span>
                              <div class="horizontal center layout">
                                ${g("summary.Permission")}:
                                ${[...e.perm].map((e=>o`
                                    <lablup-shields
                                      app=""
                                      color="${["green","blue","red"][["r","w","d"].indexOf(e)]}"
                                      description="${e.toUpperCase()}"
                                      ui="flat"
                                    ></lablup-shields>
                                  `))}
                              </div>
                              <div
                                style="margin:15px auto;"
                                class="horizontal layout end-justified"
                              >
                                <mwc-button
                                  outlined
                                  label="${g("summary.Decline")}"
                                  @click="${t=>this._deleteInvitation(t,e)}"
                                ></mwc-button>
                                <mwc-button
                                  unelevated
                                  label="${g("summary.Accept")}"
                                  @click="${t=>this._acceptInvitation(t,e)}"
                                ></mwc-button>
                                <span class="flex"></span>
                              </div>
                            </div>
                          </div>
                        </lablup-activity-panel>
                      `)):o`
                      <p>${l("summary.NoInvitations")}</p>
                    `}
              </div>
            </lablup-activity-panel>
          </div>
          ${globalThis.isElectron?o``:o`
                <lablup-activity-panel
                  title="${g("summary.DownloadWebUIApp")}"
                  elevation="1"
                  narrow
                  height="245"
                >
                  <div slot="message">
                    <div
                      id="download-app-os-select-box"
                      class="horizontal layout start-justified"
                    >
                      <mwc-select
                        @selected="${e=>this._updateSelectedDownloadAppOS(e)}"
                      >
                        ${Object.keys(this.appDownloadMap).map((e=>o`
                            <mwc-list-item
                              value="${e}"
                              ?selected="${e===this.downloadAppOS}"
                            >
                              ${e}
                            </mwc-list-item>
                          `))}
                      </mwc-select>
                    </div>
                    <div class="horizontal layout center center-justified">
                      ${this.downloadAppOS&&this.appDownloadMap[this.downloadAppOS].architecture.map((e=>o`
                          <mwc-button
                            raised
                            style="margin:10px;flex-basis:50%;"
                            @click="${e=>this._downloadApplication(e)}"
                          >
                            ${e}
                          </mwc-button>
                        `))}
                    </div>
                  </div>
                </lablup-activity-panel>
              `}
        </div>
        <div class="vertical layout">
          ${this.is_admin?o`
              <div class="horizontal layout wrap">
                <div class="vertical layout">
                  <div class="line"></div>
                  <div class="horizontal layout flex wrap center-justified">
                    <lablup-activity-panel class="footer-menu" noheader autowidth style="display: none;">
                      <div slot="message" class="vertical layout center start-justified flex upper-lower-space">
                        <h3 style="margin-top:0px;">${g("summary.CurrentVersion")}</h3>
                        ${this.is_superadmin?o`
                                <div
                                  class="layout vertical center center-justified flex"
                                  style="margin-bottom:5px;"
                                >
                                  <lablup-shields
                                    app="Manager version"
                                    color="darkgreen"
                                    description="${this.manager_version}"
                                    ui="flat"
                                  ></lablup-shields>
                                  <div
                                    class="layout horizontal center flex"
                                    style="margin-top:4px;"
                                  >
                                    <lablup-shields
                                      app="Console version"
                                      color="${this.update_checker.updateNeeded?"red":"darkgreen"}"
                                      description="${this.webui_version}"
                                      ui="flat"
                                    ></lablup-shields>
                                    ${this.update_checker.updateNeeded?o`
                                          <mwc-icon-button
                                            class="update-button"
                                            icon="new_releases"
                                            @click="${()=>{window.open(this.update_checker.updateURL,"_blank")}}"
                                          ></mwc-icon-button>
                                        `:o`
                                          <mwc-icon class="update-icon">
                                            done
                                          </mwc-icon>
                                        `}
                                  </div>
                                </div>
                              `:o``}
                      </div>
                    </lablup-activity-panel>
                    <lablup-activity-panel class="footer-menu" noheader autowidth>
                      <div slot="message" class="layout horizontal center center-justified flex upper-lower-space">
                          <a href="/environment">
                            <div class="layout horizontal center center-justified flex"  style="font-size:14px;">
                              <i class="fas fa-sync-alt larger left-end-icon"></i>
                              <span>${g("summary.UpdateEnvironmentImages")}</span>
                              <i class="fas fa-chevron-right right-end-icon"></i>
                            </div>
                          </a>
                      </div>
                    </lablup-activity-panel>
                    ${this.is_superadmin?o`
                            <lablup-activity-panel
                              class="footer-menu"
                              noheader
                              autowidth
                            >
                              <div
                                slot="message"
                                class="layout horizontal center center-justified flex upper-lower-space"
                              >
                                <a href="/agent">
                                  <div
                                    class="layout horizontal center center-justified flex"
                                    style="font-size:14px;"
                                  >
                                    <i
                                      class="fas fa-box larger left-end-icon"
                                    ></i>
                                    <span>${g("summary.CheckResources")}</span>
                                    <i
                                      class="fas fa-chevron-right right-end-icon"
                                    ></i>
                                  </div>
                                </a>
                              </div>
                            </lablup-activity-panel>
                            <lablup-activity-panel
                              class="footer-menu"
                              noheader
                              autowidth
                            >
                              <div
                                slot="message"
                                class="layout horizontal center center-justified flex upper-lower-space"
                              >
                                <a href="/settings">
                                  <div
                                    class="layout horizontal center center-justified flex"
                                    style="font-size:14px;"
                                  >
                                    <i
                                      class="fas fa-desktop larger left-end-icon"
                                    ></i>
                                    <span>
                                      ${g("summary.ChangeSystemSetting")}
                                    </span>
                                    <i
                                      class="fas fa-chevron-right right-end-icon"
                                    ></i>
                                  </div>
                                </a>
                              </div>
                            </lablup-activity-panel>
                          `:o``}

                    <lablup-activity-panel class="footer-menu" noheader autowidth>
                      <div slot="message" class="layout horizontal center center-justified flex upper-lower-space">
                          <a href="/maintenance">
                            <div class="layout horizontal center center-justified flex"  style="font-size:14px;">
                              <i class="fas fa-tools larger left-end-icon"></i>
                              <span>${g("summary.SystemMaintenance")}</span>
                              <i class="fas fa-chevron-right right-end-icon"></i>
                            </div>
                          </a>
                      </div>
                    </lablup-activity-panel>
                  </div>
                </div>
              </div>
          </div>`:o``}
        </div>
      </div>
      <backend-ai-release-check id="update-checker"></backend-ai-release-check>
    `}};e([t({type:String})],H.prototype,"condition",void 0),e([t({type:Number})],H.prototype,"sessions",void 0),e([t({type:Object})],H.prototype,"jobs",void 0),e([t({type:Number})],H.prototype,"agents",void 0),e([t({type:Boolean})],H.prototype,"is_admin",void 0),e([t({type:Boolean})],H.prototype,"is_superadmin",void 0),e([t({type:Object})],H.prototype,"resources",void 0),e([t({type:Object})],H.prototype,"update_checker",void 0),e([t({type:Boolean})],H.prototype,"authenticated",void 0),e([t({type:String})],H.prototype,"manager_version",void 0),e([t({type:String})],H.prototype,"webui_version",void 0),e([t({type:Number})],H.prototype,"cpu_total",void 0),e([t({type:Number})],H.prototype,"cpu_used",void 0),e([t({type:String})],H.prototype,"cpu_percent",void 0),e([t({type:String})],H.prototype,"cpu_total_percent",void 0),e([t({type:Number})],H.prototype,"cpu_total_usage_ratio",void 0),e([t({type:Number})],H.prototype,"cpu_current_usage_ratio",void 0),e([t({type:String})],H.prototype,"mem_total",void 0),e([t({type:String})],H.prototype,"mem_used",void 0),e([t({type:String})],H.prototype,"mem_allocated",void 0),e([t({type:Number})],H.prototype,"mem_total_usage_ratio",void 0),e([t({type:Number})],H.prototype,"mem_current_usage_ratio",void 0),e([t({type:String})],H.prototype,"mem_current_usage_percent",void 0),e([t({type:Number})],H.prototype,"cuda_gpu_total",void 0),e([t({type:Number})],H.prototype,"cuda_gpu_used",void 0),e([t({type:Number})],H.prototype,"cuda_fgpu_total",void 0),e([t({type:Number})],H.prototype,"cuda_fgpu_used",void 0),e([t({type:Number})],H.prototype,"rocm_gpu_total",void 0),e([t({type:Number})],H.prototype,"rocm_gpu_used",void 0),e([t({type:Number})],H.prototype,"tpu_total",void 0),e([t({type:Number})],H.prototype,"tpu_used",void 0),e([t({type:Number})],H.prototype,"ipu_total",void 0),e([t({type:Number})],H.prototype,"ipu_used",void 0),e([t({type:Number})],H.prototype,"atom_total",void 0),e([t({type:Number})],H.prototype,"atom_used",void 0),e([t({type:Object})],H.prototype,"notification",void 0),e([t({type:Object})],H.prototype,"resourcePolicy",void 0),e([t({type:String})],H.prototype,"announcement",void 0),e([t({type:Object})],H.prototype,"invitations",void 0),e([t({type:Object})],H.prototype,"appDownloadMap",void 0),e([t({type:String})],H.prototype,"appDownloadUrl",void 0),e([t({type:String})],H.prototype,"downloadAppOS",void 0),e([c("#resource-monitor")],H.prototype,"resourceMonitor",void 0),H=e([s("backend-ai-summary-view")],H);var W=H;export{W as default};
