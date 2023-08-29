import{_ as e,n as t,e as s,s as i,x as r,g as n,I as a,a as o,i as l,b as c,B as p,c as u,d as h,f as d,t as g,h as m,o as b}from"./backend-ai-webui-d4819018.js";import"./lablup-activity-panel-9287ea5d.js";import"./backend-ai-resource-monitor-0d8af920.js";import"./lablup-loading-spinner-5b09b684.js";import"./lablup-progress-bar-eedf2fcd.js";import"./backend-ai-session-launcher-598fd926.js";import"./mwc-switch-79aabe22.js";import"./mwc-check-list-item-de5f8c59.js";import"./slider-2bcf3732.js";import"./vaadin-grid-8bcb41b9.js";import"./dir-utils-31fa6465.js";import"./vaadin-grid-filter-column-ea2d3d99.js";import"./vaadin-grid-selection-column-132c974d.js";import"./media-query-controller-83d85766.js";import"./lablup-codemirror-6731a5d1.js";
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */let f=class extends i{constructor(){super(...arguments),this.releaseURL="https://raw.githubusercontent.com/lablup/backend.ai-webui/release/version.json",this.localVersion="",this.localBuild="",this.remoteVersion="",this.remoteBuild="",this.remoteRevision="",this.updateChecked=!1,this.updateNeeded=!1,this.updateURL=""}static get styles(){return[]}render(){return r`
    `}firstUpdated(){this.notification=globalThis.lablupNotification,globalThis.isElectron&&void 0!==globalThis.backendaioptions&&globalThis.backendaioptions.get("automatic_update_check",!0)&&this.checkRelease()}async checkRelease(){this.updateChecked||fetch(this.releaseURL).then((e=>e.json())).then((e=>{this.updateChecked=!0,this.remoteVersion=e.package,this.remoteBuild=e.build,this.remoteRevision=e.revision,this.compareVersion(globalThis.packageVersion,this.remoteVersion)<0&&(this.updateNeeded=!0,this.updateURL=`https://github.com/lablup/backend.ai-webui/releases/tag/v${this.remoteVersion}`,globalThis.isElectron&&(this.notification.text=n("update.NewWebUIVersionAvailable")+" "+this.remoteVersion,this.notification.detail=n("update.NewWebUIVersionAvailable"),this.notification.url=this.updateURL,this.notification.show()))})).catch((e=>{const t=globalThis.backendaioptions.get("automatic_update_count_trial",0);t>3&&globalThis.backendaioptions.set("automatic_update_check",!1),globalThis.backendaioptions.set("automatic_update_count_trial",t+1)}))}compareVersion(e,t){if("string"!=typeof e)return 0;if("string"!=typeof t)return 0;e=e.split("."),t=t.split(".");const s=Math.min(e.length,t.length);for(let i=0;i<s;++i){if(e[i]=parseInt(e[i],10),t[i]=parseInt(t[i],10),e[i]>t[i])return 1;if(e[i]<t[i])return-1}return e.length==t.length?0:e.length<t.length?-1:1}};e([t({type:String})],f.prototype,"releaseURL",void 0),e([t({type:String})],f.prototype,"localVersion",void 0),e([t({type:String})],f.prototype,"localBuild",void 0),e([t({type:String})],f.prototype,"remoteVersion",void 0),e([t({type:String})],f.prototype,"remoteBuild",void 0),e([t({type:String})],f.prototype,"remoteRevision",void 0),e([t({type:Boolean})],f.prototype,"updateChecked",void 0),e([t({type:Boolean})],f.prototype,"updateNeeded",void 0),e([t({type:String})],f.prototype,"updateURL",void 0),e([t({type:Object})],f.prototype,"notification",void 0),f=e([s("backend-ai-release-check")],f);let _=class extends i{constructor(){super(...arguments),this.currentNumber=50,this.maxNumber=100,this.unit="%",this.url="",this.textcolor="#888888",this.chartcolor="#ff2222",this.size=200,this.fontsize=60,this.chartFontSize="0",this.indicatorPath="",this.prefix="",this.sizeParam=""}static get is(){return"lablup-piechart"}static get styles(){return[a,o,l`
        #chart {
          cursor: pointer;
        }
      `]}firstUpdated(){var e,t,s,i,r,n,a;this.sizeParam=this.size+"px";let o=this.fontsize/this.size;o=o>=.5?.3:.9/this.currentNumber.toString().length,this.chartFontSize=o.toString();let l=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#chart"),c=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#chart-text"),p=null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#unit-text"),u=(.3-.05*this.unit.length).toString();l.setAttribute("fill",this.chartcolor),c.setAttribute("fill",this.textcolor),c.setAttribute("font-size",this.chartFontSize),p.setAttribute("font-size",u),l.setAttribute("width",this.sizeParam),l.setAttribute("height",this.sizeParam),this.indicatorPath="M 0.5 0.5 L0.5 0 ";var h=100*(this.maxNumber-this.currentNumber)/this.maxNumber;h>12.5&&(this.indicatorPath=this.indicatorPath+"L1 0 "),h>37.5&&(this.indicatorPath=this.indicatorPath+"L1 1 "),h>62.5&&(this.indicatorPath=this.indicatorPath+"L0 1 "),h>87.5&&(this.indicatorPath=this.indicatorPath+"L0 0 ");let d=h/100*2*Math.PI,g=Math.sin(d)/Math.cos(d),m=0,b=0;h<=12.5||h>87.5?(b=.5,m=b*g):h>12.5&&h<=37.5?(m=.5,b=m/g):h>37.5&&h<=62.5?(b=-.5,m=b*g):h>62.5&&h<=87.5&&(m=-.5,b=m/g),m+=.5,b=.5-b,this.indicatorPath=this.indicatorPath+"L"+m+" "+b+" z",null===(r=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#pievalue"))||void 0===r||r.setAttribute("d",this.indicatorPath),void 0!==this.url&&""!==this.url&&(null===(a=null===(n=this.shadowRoot)||void 0===n?void 0:n.querySelector("#chart"))||void 0===a||a.addEventListener("tap",this._moveTo.bind(this))),this.requestUpdate()}connectedCallback(){super.connectedCallback()}_moveTo(){window.location.href=this.url}render(){return r`
      <svg id="chart"
           xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1"
           viewBox="0 0 1 1" style="background-color:transparent;">
        <g id="piechart">
          <circle cx="0.5" cy="0.5" r="0.5" />
          <circle cx="0.5" cy="0.5" r="0.40" fill="rgba(255,255,255,0.9)"/>
          <path id="pievalue" stroke="none" fill="rgba(255, 255, 255, 0.75)"/>
          <text id="chart-text" x="0.5" y="0.5" font-family="Roboto" text-anchor="middle"
                dy="0.1">
            <tspan>${this.prefix}</tspan>
            <tspan>${this.currentNumber}</tspan>
            <tspan id="unit-text" font-size="0.2" dy="-0.07">${this.unit}</tspan>
          </text>
        </g>
      </svg>
    `}};e([t({type:Number})],_.prototype,"currentNumber",void 0),e([t({type:Number})],_.prototype,"maxNumber",void 0),e([t({type:String})],_.prototype,"unit",void 0),e([t({type:String})],_.prototype,"url",void 0),e([t({type:String})],_.prototype,"textcolor",void 0),e([t({type:String})],_.prototype,"chartcolor",void 0),e([t({type:Number})],_.prototype,"size",void 0),e([t({type:Number})],_.prototype,"fontsize",void 0),e([t({type:String})],_.prototype,"chartFontSize",void 0),e([t({type:String})],_.prototype,"indicatorPath",void 0),e([t({type:String})],_.prototype,"prefix",void 0),e([t({type:String})],_.prototype,"sizeParam",void 0),_=e([s("lablup-piechart")],_);
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */
let y=class extends p{constructor(){super(...arguments),this.condition="running",this.sessions=0,this.agents=0,this.is_admin=!1,this.is_superadmin=!1,this.resources=Object(),this.authenticated=!1,this.manager_version="",this.webui_version="",this.cpu_total=0,this.cpu_used=0,this.cpu_percent="0",this.cpu_total_percent="0",this.cpu_total_usage_ratio=0,this.cpu_current_usage_ratio=0,this.mem_total="0",this.mem_used="0",this.mem_allocated="0",this.mem_total_usage_ratio=0,this.mem_current_usage_ratio=0,this.mem_current_usage_percent="0",this.cuda_gpu_total=0,this.cuda_gpu_used=0,this.cuda_fgpu_total=0,this.cuda_fgpu_used=0,this.rocm_gpu_total=0,this.rocm_gpu_used=0,this.tpu_total=0,this.tpu_used=0,this.ipu_total=0,this.ipu_used=0,this.atom_total=0,this.atom_used=0,this.warboy_total=0,this.warboy_used=0,this.notification=Object(),this.announcement="",this.height=0}static get styles(){return[u,a,o,h,l`
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
          transition: color ease-in .2s;
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
          background-color: #F6F6F6;
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
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}_refreshHealthPanel(){this.activeConnected&&(this._refreshSessionInformation(),this.is_superadmin&&this._refreshAgentInformation())}_refreshSessionInformation(){if(!this.activeConnected)return;this.spinner.show();let e="RUNNING";switch(this.condition){case"running":case"archived":default:e="RUNNING";break;case"finished":e="TERMINATED"}globalThis.backendaiclient.computeSession.total_count(e).then((e=>{this.spinner.hide(),!e.compute_session_list&&e.legacy_compute_session_list&&(e.compute_session_list=e.legacy_compute_session_list),this.sessions=e.compute_session_list.total_count,this.active&&setTimeout((()=>{this._refreshSessionInformation()}),15e3)})).catch((e=>{this.spinner.hide(),this.sessions=0,this.notification.text=n("summary.connectingToCluster"),this.notification.detail=e,this.notification.show(!1,e),this.active&&setTimeout((()=>{this._refreshSessionInformation()}),15e3)}))}_refreshResourceInformation(){if(this.activeConnected)return globalThis.backendaiclient.resourcePolicy.get(globalThis.backendaiclient.resource_policy).then((e=>{const t=e.keypair_resource_policies;this.resourcePolicy=globalThis.backendaiclient.utils.gqlToObject(t,"name")}))}_refreshAgentInformation(e="running"){if(this.activeConnected){switch(this.condition){case"running":case"archived":default:e="ALIVE";break;case"finished":e="TERMINATED"}this.spinner.show(),globalThis.backendaiclient.resources.totalResourceInformation().then((t=>{this.spinner.hide(),this.resources=t,this._sync_resource_values(),1==this.active&&setTimeout((()=>{this._refreshAgentInformation(e)}),15e3)})).catch((e=>{this.spinner.hide(),e&&e.message&&(this.notification.text=d.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}}_init_resource_values(){this.resources.cpu={},this.resources.cpu.total=0,this.resources.cpu.used=0,this.resources.cpu.percent=0,this.resources.mem={},this.resources.mem.total=0,this.resources.mem.allocated=0,this.resources.mem.used=0,this.resources.cuda_gpu={},this.resources.cuda_gpu.total=0,this.resources.cuda_gpu.used=0,this.resources.cuda_fgpu={},this.resources.cuda_fgpu.total=0,this.resources.cuda_fgpu.used=0,this.resources.rocm_gpu={},this.resources.rocm_gpu.total=0,this.resources.rocm_gpu.used=0,this.resources.tpu={},this.resources.tpu.total=0,this.resources.tpu.used=0,this.resources.ipu={},this.resources.ipu.total=0,this.resources.ipu.used=0,this.resources.atom={},this.resources.atom.total=0,this.resources.atom.used=0,this.resources.warboy={},this.resources.warboy.total=0,this.resources.warboy.used=0,this.resources.agents={},this.resources.agents.total=0,this.resources.agents.using=0,this.cpu_total_usage_ratio=0,this.cpu_current_usage_ratio=0,this.mem_total_usage_ratio=0,this.mem_current_usage_ratio=0,this.mem_current_usage_percent="0",this.is_admin=!1,this.is_superadmin=!1}_sync_resource_values(){this.manager_version=globalThis.backendaiclient.managerVersion,this.webui_version=globalThis.packageVersion,this.cpu_total=this.resources.cpu.total,this.mem_total=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(this.resources.mem.total,"g")).toFixed(2),isNaN(this.resources["cuda.device"].total)?this.cuda_gpu_total=0:this.cuda_gpu_total=this.resources["cuda.device"].total,isNaN(this.resources["cuda.shares"].total)?this.cuda_fgpu_total=0:this.cuda_fgpu_total=this.resources["cuda.shares"].total,isNaN(this.resources["rocm.device"].total)?this.rocm_gpu_total=0:this.rocm_gpu_total=this.resources["rocm.device"].total,isNaN(this.resources["tpu.device"].total)?this.tpu_total=0:this.tpu_total=this.resources["tpu.device"].total,isNaN(this.resources["ipu.device"].total)?this.ipu_total=0:this.ipu_total=this.resources["ipu.device"].total,isNaN(this.resources["atom.device"].total)?this.atom_total=0:this.atom_total=this.resources["atom.device"].total,isNaN(this.resources["warboy.device"].total)?this.warboy_total=0:this.warboy_total=this.resources["warboy.device"].total,this.cpu_used=this.resources.cpu.used,this.cuda_gpu_used=this.resources["cuda.device"].used,this.cuda_fgpu_used=this.resources["cuda.shares"].used,this.rocm_gpu_used=this.resources["rocm.device"].used,this.tpu_used=this.resources["tpu.device"].used,this.ipu_used=this.resources["ipu.device"].used,this.atom_used=this.resources["atom.device"].used,this.warboy_used=this.resources["warboy.device"].used,this.cpu_percent=parseFloat(this.resources.cpu.percent).toFixed(2),this.cpu_total_percent=0!==this.cpu_used?(this.cpu_used/this.cpu_total*100).toFixed(2):"0",this.cpu_total_usage_ratio=this.resources.cpu.used/this.resources.cpu.total*100,this.cpu_current_usage_ratio=this.resources.cpu.percent/this.resources.cpu.total,this.mem_used=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(this.resources.mem.used,"g")).toFixed(2),this.mem_allocated=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(this.resources.mem.allocated,"g")).toFixed(2),this.mem_total_usage_ratio=this.resources.mem.allocated/this.resources.mem.total*100,this.mem_current_usage_ratio=this.resources.mem.used/this.resources.mem.total*100,0===this.mem_total_usage_ratio?this.mem_current_usage_percent="0.0":this.mem_current_usage_percent=this.mem_total_usage_ratio.toFixed(2),this.agents=this.resources.agents.total,isNaN(parseFloat(this.mem_current_usage_percent))&&(this.mem_current_usage_percent="0")}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(this._init_resource_values(),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_superadmin=globalThis.backendaiclient.is_superadmin,this.is_admin=globalThis.backendaiclient.is_admin,this.authenticated=!0,this.activeConnected&&(this._refreshHealthPanel(),this.requestUpdate())}),!0):(this.is_superadmin=globalThis.backendaiclient.is_superadmin,this.is_admin=globalThis.backendaiclient.is_admin,this.authenticated=!0,this._refreshHealthPanel(),this.requestUpdate()))}_toInt(e){return Math.ceil(e)}_countObject(e){return Object.keys(e).length}_addComma(e){if(void 0===e)return"";return e.toString().replace(/\B(?=(\d{3})+(?!\d))/g,",")}render(){return r`
      <link rel="stylesheet" href="resources/custom.css">
      <lablup-loading-spinner id="loading-spinner"></lablup-loading-spinner>
      <lablup-activity-panel title="${g("summary.SystemResources")}" elevation="1" narrow height="${this.height}">
        <div slot="message">
          <div class="horizontal justified layout wrap indicators">
            ${this.is_superadmin?r`
              <div class="vertical layout center system-health-indicator">
                <div class="big indicator">${this.agents}</div>
                <span>${m("summary.ConnectedNodes")}</span>
              </div>`:r``}
            <div class="vertical layout center system-health-indicator">
              <div class="big indicator">${this.sessions}</div>
              <span>${g("summary.ActiveSessions")}</span>
            </div>
          </div>
          <div class="vertical-card" style="align-items: flex-start">
            ${this.is_superadmin?r`
            <div class="layout horizontal center flex resource">
              <div class="layout vertical center center-justified resource-name">
                <div class="gauge-name">CPU</div>
              </div>
              <div class="layout vertical start-justified wrap">
                <lablup-progress-bar id="cpu-usage-bar" class="start"
                  progress="${this.cpu_total_usage_ratio/100}"
                  description="${this._addComma(this.cpu_used)}/${this._addComma(this.cpu_total)} ${g("summary.CoresReserved")}."
                ></lablup-progress-bar>
                <lablup-progress-bar id="cpu-usage-bar-2" class="end"
                  progress="${this.cpu_current_usage_ratio/100}"
                  description="${g("summary.Using")} ${this.cpu_total_percent} % (util. ${this.cpu_percent} %)"
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage start-bar">${parseInt(this.cpu_total_percent)+"%"}</span>
                <span class="percentage end-bar">${parseInt(this.cpu_percent)+"%"}</span>
              </div>
            </div>
            <div class="resource-line"></div>
            <div class="layout horizontal center flex resource">
              <div class="layout vertical center center-justified resource-name">
                <div class="gauge-name">RAM</div>
              </div>
              <div class="layout vertical start-justified wrap">
                <lablup-progress-bar id="mem-usage-bar" class="start"
                  progress="${this.mem_total_usage_ratio/100}"
                  description="${this._addComma(this.mem_allocated)} / ${this._addComma(this.mem_total)} GiB ${g("summary.reserved")}."
                ></lablup-progress-bar>
                <lablup-progress-bar id="mem-usage-bar-2" class="end"
                  progress="${this.mem_current_usage_ratio/100}"
                  description="${g("summary.Using")} ${this._addComma(this.mem_used)} GiB
                    (${0!==parseInt(this.mem_used)?(parseInt(this.mem_used)/parseInt(this.mem_total)*100).toFixed(0):"0"} %)"
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage start-bar">${this.mem_total_usage_ratio.toFixed(1)+"%"}</span>
                <span class="percentage end-bar">${(0!==parseInt(this.mem_used)?(parseInt(this.mem_used)/parseInt(this.mem_total)*100).toFixed(0):"0")+"%"}</span>
              </div>
            </div>
            ${this.cuda_gpu_total||this.cuda_fgpu_total||this.rocm_gpu_total||this.tpu_total||this.ipu_total||this.atom_total||this.warboy_total?r`
            <div class="resource-line"></div>
            <div class="layout horizontal center flex resource">
              <div class="layout vertical center center-justified resource-name">
                <div class="gauge-name">GPU/NPU</div>
              </div>
              ${this.cuda_gpu_total?r`
              <div class="layout vertical start-justified wrap">
                <lablup-progress-bar id="gpu-usage-bar" class="start"
                  progress="${this.cuda_gpu_used/this.cuda_gpu_total}"
                  description="${this.cuda_gpu_used} / ${this.cuda_gpu_total} CUDA GPUs ${g("summary.reserved")}."
                ></lablup-progress-bar>
                <lablup-progress-bar id="gpu-usage-bar-2" class="end"
                  progress="0"
                  description="${g("summary.FractionalGPUScalingEnabled")}."
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage start-bar">${0!==this.cuda_gpu_used?(this.cuda_gpu_used/this.cuda_gpu_total*100).toFixed(1):0}%</span>
                <span class="percentage end-bar">&nbsp;</span>
              </div>
              `:r``}
              ${this.cuda_fgpu_total?r`
              <div class="layout vertical start-justified wrap">
                <lablup-progress-bar id="fgpu-usage-bar" class="start"
                  progress="${this.cuda_fgpu_used/this.cuda_fgpu_total}"
                  description="${this.cuda_fgpu_used} / ${this.cuda_fgpu_total} CUDA FGPUs ${g("summary.reserved")}."
                ></lablup-progress-bar>
                <lablup-progress-bar id="fgpu-usage-bar-2" class="end"
                  progress="0"
                  description="${g("summary.FractionalGPUScalingEnabled")}."
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage start-bar">${0!==this.cuda_fgpu_used?(this.cuda_fgpu_used/this.cuda_fgpu_total*100).toFixed(1):0}%</span>
                <span class="percentage end-bar">&nbsp;</span>
              </div>
              `:r``}
              ${this.rocm_gpu_total?r`
              <div class="layout vertical start-justified wrap">
                <lablup-progress-bar id="rocm-gpu-usage-bar" class="start"
                  progress="${this.rocm_gpu_used/100}"
                  description="${this.rocm_gpu_used} / ${this.rocm_gpu_total} ROCm GPUs ${g("summary.reserved")}."
                ></lablup-progress-bar>
                <lablup-progress-bar id="rocm-gpu-usage-bar-2" class="end"
                  progress="0"
                  description="${g("summary.ROCMGPUEnabled")}."
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage start-bar">${this.rocm_gpu_used.toFixed(1)+"%"}</span>
                <span class="percentage end-bar">&nbsp;</span>
              </div>`:r``}
              ${this.tpu_total?r`
              <div class="layout vertical start-justified wrap">
                <lablup-progress-bar id="tpu-usage-bar" class="start"
                  progress="${this.tpu_used/100}"
                  description="${this.tpu_used} / ${this.tpu_total} TPUs ${g("summary.reserved")}."
                ></lablup-progress-bar>
                <lablup-progress-bar id="tpu-usage-bar-2" class="end"
                  progress="0"
                  description="${g("summary.TPUEnabled")}."
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage start-bar">${this.tpu_used.toFixed(1)+"%"}</span>
                <span class="percentage end-bar"></span>
              </div>`:r``}
              ${this.ipu_total?r`
              <div class="layout vertical start-justified wrap">
                <lablup-progress-bar id="ipu-usage-bar" class="start"
                  progress="${this.ipu_used/100}"
                  description="${this.ipu_used} / ${this.ipu_total} IPUs ${g("summary.reserved")}."
                ></lablup-progress-bar>
                <lablup-progress-bar id="ipu-usage-bar-2" class="end"
                  progress="0"
                  description="${g("summary.IPUEnabled")}."
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage start-bar">${this.ipu_used.toFixed(1)+"%"}</span>
                <span class="percentage end-bar"></span>
              </div>`:r``}
              ${this.atom_total?r`
              <div class="layout vertical start-justified wrap">
                <lablup-progress-bar id="atom-usage-bar" class="start"
                  progress="${this.atom_used/100}"
                  description="${this.atom_used} / ${this.atom_total} ATOMs ${g("summary.reserved")}."
                ></lablup-progress-bar>
                <lablup-progress-bar id="atom-usage-bar-2" class="end"
                  progress="0"
                  description="${g("summary.ATOMEnabled")}."
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage start-bar">${this.atom_used.toFixed(1)+"%"}</span>
                <span class="percentage end-bar"></span>
              </div>`:r``}
              ${this.warboy_total?r`
              <div class="layout vertical start-justified wrap">
                <lablup-progress-bar id="warboy-usage-bar" class="start"
                  progress="${this.warboy_used/100}"
                  description="${this.warboy_used} / ${this.warboy_total} Warboys ${g("summary.reserved")}."
                ></lablup-progress-bar>
                <lablup-progress-bar id="warboy-usage-bar-2" class="end"
                  progress="0"
                  description="${g("summary.WarboyEnabled")}."
                ></lablup-progress-bar>
              </div>
              <div class="layout vertical center center-justified">
                <span class="percentage start-bar">${this.warboy_used.toFixed(1)+"%"}</span>
                <span class="percentage end-bar"></span>
              </div>`:r``}

            </div>`:r``}
            <div class="vertical start layout" style="margin-top:30px;">
              <div class="horizontal layout resource-legend-stack">
                <div class="resource-legend-icon start"></div>
                <span class="resource-legend">${g("summary.Reserved")} ${g("resourcePolicy.Resources")}</span>
              </div>
              <div class="horizontal layout resource-legend-stack">
                <div class="resource-legend-icon end"></div>
                <span class="resource-legend">${g("summary.Used")} ${g("resourcePolicy.Resources")}</span>
              </div>
              <div class="horizontal layout">
                <div class="resource-legend-icon total"></div>
                <span class="resource-legend">${g("summary.Total")} ${g("resourcePolicy.Resources")}</span>
              </div>
            </div>`:r``}
          </div>
        </div>
      </lablup-activity-panel>
`}};function v(){return{async:!1,baseUrl:null,breaks:!1,extensions:null,gfm:!0,headerIds:!1,headerPrefix:"",highlight:null,hooks:null,langPrefix:"language-",mangle:!1,pedantic:!1,renderer:null,sanitize:!1,sanitizer:null,silent:!1,smartypants:!1,tokenizer:null,walkTokens:null,xhtml:!1}}e([t({type:String})],y.prototype,"condition",void 0),e([t({type:Number})],y.prototype,"sessions",void 0),e([t({type:Number})],y.prototype,"agents",void 0),e([t({type:Boolean})],y.prototype,"is_admin",void 0),e([t({type:Boolean})],y.prototype,"is_superadmin",void 0),e([t({type:Object})],y.prototype,"resources",void 0),e([t({type:Boolean})],y.prototype,"authenticated",void 0),e([t({type:String})],y.prototype,"manager_version",void 0),e([t({type:String})],y.prototype,"webui_version",void 0),e([t({type:Number})],y.prototype,"cpu_total",void 0),e([t({type:Number})],y.prototype,"cpu_used",void 0),e([t({type:String})],y.prototype,"cpu_percent",void 0),e([t({type:String})],y.prototype,"cpu_total_percent",void 0),e([t({type:Number})],y.prototype,"cpu_total_usage_ratio",void 0),e([t({type:Number})],y.prototype,"cpu_current_usage_ratio",void 0),e([t({type:String})],y.prototype,"mem_total",void 0),e([t({type:String})],y.prototype,"mem_used",void 0),e([t({type:String})],y.prototype,"mem_allocated",void 0),e([t({type:Number})],y.prototype,"mem_total_usage_ratio",void 0),e([t({type:Number})],y.prototype,"mem_current_usage_ratio",void 0),e([t({type:String})],y.prototype,"mem_current_usage_percent",void 0),e([t({type:Number})],y.prototype,"cuda_gpu_total",void 0),e([t({type:Number})],y.prototype,"cuda_gpu_used",void 0),e([t({type:Number})],y.prototype,"cuda_fgpu_total",void 0),e([t({type:Number})],y.prototype,"cuda_fgpu_used",void 0),e([t({type:Number})],y.prototype,"rocm_gpu_total",void 0),e([t({type:Number})],y.prototype,"rocm_gpu_used",void 0),e([t({type:Number})],y.prototype,"tpu_total",void 0),e([t({type:Number})],y.prototype,"tpu_used",void 0),e([t({type:Number})],y.prototype,"ipu_total",void 0),e([t({type:Number})],y.prototype,"ipu_used",void 0),e([t({type:Number})],y.prototype,"atom_total",void 0),e([t({type:Number})],y.prototype,"atom_used",void 0),e([t({type:Number})],y.prototype,"warboy_total",void 0),e([t({type:Number})],y.prototype,"warboy_used",void 0),e([t({type:Object})],y.prototype,"notification",void 0),e([t({type:Object})],y.prototype,"resourcePolicy",void 0),e([t({type:String})],y.prototype,"announcement",void 0),e([t({type:Number})],y.prototype,"height",void 0),e([c("#loading-spinner")],y.prototype,"spinner",void 0),y=e([s("backend-ai-resource-panel")],y);let k={async:!1,baseUrl:null,breaks:!1,extensions:null,gfm:!0,headerIds:!1,headerPrefix:"",highlight:null,hooks:null,langPrefix:"language-",mangle:!1,pedantic:!1,renderer:null,sanitize:!1,sanitizer:null,silent:!1,smartypants:!1,tokenizer:null,walkTokens:null,xhtml:!1};function x(e){k=e}const w=/[&<>"']/,$=new RegExp(w.source,"g"),z=/[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/,S=new RegExp(z.source,"g"),T={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"},A=e=>T[e];function j(e,t){if(t){if(w.test(e))return e.replace($,A)}else if(z.test(e))return e.replace(S,A);return e}const N=/&(#(?:\d+)|(?:#x[0-9A-Fa-f]+)|(?:\w+));?/gi;function R(e){return e.replace(N,((e,t)=>"colon"===(t=t.toLowerCase())?":":"#"===t.charAt(0)?"x"===t.charAt(1)?String.fromCharCode(parseInt(t.substring(2),16)):String.fromCharCode(+t.substring(1)):""))}const I=/(^|[^\[])\^/g;function P(e,t){e="string"==typeof e?e:e.source,t=t||"";const s={replace:(t,i)=>(i=(i="object"==typeof i&&"source"in i?i.source:i).replace(I,"$1"),e=e.replace(t,i),s),getRegex:()=>new RegExp(e,t)};return s}const U=/[^\w:]/g,O=/^$|^[a-z][a-z0-9+.-]*:|^[?#]/i;function C(e,t,s){if(e){let e;try{e=decodeURIComponent(R(s)).replace(U,"").toLowerCase()}catch(e){return null}if(0===e.indexOf("javascript:")||0===e.indexOf("vbscript:")||0===e.indexOf("data:"))return null}t&&!O.test(s)&&(s=function(e,t){E[" "+e]||(L.test(e)?E[" "+e]=e+"/":E[" "+e]=B(e,"/",!0));e=E[" "+e];const s=-1===e.indexOf(":");return"//"===t.substring(0,2)?s?t:e.replace(M,"$1")+t:"/"===t.charAt(0)?s?t:e.replace(F,"$1")+t:e+t}(t,s));try{s=encodeURI(s).replace(/%25/g,"%")}catch(e){return null}return s}const E={},L=/^[^:]+:\/*[^/]*$/,M=/^([^:]+:)[\s\S]*$/,F=/^([^:]+:\/*[^/]*)[\s\S]*$/;const q={exec:()=>null};function D(e,t){const s=e.replace(/\|/g,((e,t,s)=>{let i=!1,r=t;for(;--r>=0&&"\\"===s[r];)i=!i;return i?"|":" |"})).split(/ \|/);let i=0;if(s[0].trim()||s.shift(),s.length>0&&!s[s.length-1].trim()&&s.pop(),t)if(s.length>t)s.splice(t);else for(;s.length<t;)s.push("");for(;i<s.length;i++)s[i]=s[i].trim().replace(/\\\|/g,"|");return s}function B(e,t,s){const i=e.length;if(0===i)return"";let r=0;for(;r<i;){const n=e.charAt(i-r-1);if(n!==t||s){if(n===t||!s)break;r++}else r++}return e.slice(0,i-r)}function V(e,t,s,i){const r=t.href,n=t.title?j(t.title):null,a=e[1].replace(/\\([\[\]])/g,"$1");if("!"!==e[0].charAt(0)){i.state.inLink=!0;const e={type:"link",raw:s,href:r,title:n,text:a,tokens:i.inlineTokens(a)};return i.state.inLink=!1,e}return{type:"image",raw:s,href:r,title:n,text:j(a)}}class Z{options;rules;lexer;constructor(e){this.options=e||k}space(e){const t=this.rules.block.newline.exec(e);if(t&&t[0].length>0)return{type:"space",raw:t[0]}}code(e){const t=this.rules.block.code.exec(e);if(t){const e=t[0].replace(/^ {1,4}/gm,"");return{type:"code",raw:t[0],codeBlockStyle:"indented",text:this.options.pedantic?e:B(e,"\n")}}}fences(e){const t=this.rules.block.fences.exec(e);if(t){const e=t[0],s=function(e,t){const s=e.match(/^(\s+)(?:```)/);if(null===s)return t;const i=s[1];return t.split("\n").map((e=>{const t=e.match(/^\s+/);if(null===t)return e;const[s]=t;return s.length>=i.length?e.slice(i.length):e})).join("\n")}(e,t[3]||"");return{type:"code",raw:e,lang:t[2]?t[2].trim().replace(this.rules.inline._escapes,"$1"):t[2],text:s}}}heading(e){const t=this.rules.block.heading.exec(e);if(t){let e=t[2].trim();if(/#$/.test(e)){const t=B(e,"#");this.options.pedantic?e=t.trim():t&&!/ $/.test(t)||(e=t.trim())}return{type:"heading",raw:t[0],depth:t[1].length,text:e,tokens:this.lexer.inline(e)}}}hr(e){const t=this.rules.block.hr.exec(e);if(t)return{type:"hr",raw:t[0]}}blockquote(e){const t=this.rules.block.blockquote.exec(e);if(t){const e=t[0].replace(/^ *>[ \t]?/gm,""),s=this.lexer.state.top;this.lexer.state.top=!0;const i=this.lexer.blockTokens(e);return this.lexer.state.top=s,{type:"blockquote",raw:t[0],tokens:i,text:e}}}list(e){let t=this.rules.block.list.exec(e);if(t){let s,i,r,n,a,o,l,c,p,u,h,d,g=t[1].trim();const m=g.length>1,b={type:"list",raw:"",ordered:m,start:m?+g.slice(0,-1):"",loose:!1,items:[]};g=m?`\\d{1,9}\\${g.slice(-1)}`:`\\${g}`,this.options.pedantic&&(g=m?g:"[*+-]");const f=new RegExp(`^( {0,3}${g})((?:[\t ][^\\n]*)?(?:\\n|$))`);for(;e&&(d=!1,t=f.exec(e))&&!this.rules.block.hr.test(e);){if(s=t[0],e=e.substring(s.length),c=t[2].split("\n",1)[0].replace(/^\t+/,(e=>" ".repeat(3*e.length))),p=e.split("\n",1)[0],this.options.pedantic?(n=2,h=c.trimLeft()):(n=t[2].search(/[^ ]/),n=n>4?1:n,h=c.slice(n),n+=t[1].length),o=!1,!c&&/^ *$/.test(p)&&(s+=p+"\n",e=e.substring(p.length+1),d=!0),!d){const t=new RegExp(`^ {0,${Math.min(3,n-1)}}(?:[*+-]|\\d{1,9}[.)])((?:[ \t][^\\n]*)?(?:\\n|$))`),i=new RegExp(`^ {0,${Math.min(3,n-1)}}((?:- *){3,}|(?:_ *){3,}|(?:\\* *){3,})(?:\\n+|$)`),r=new RegExp(`^ {0,${Math.min(3,n-1)}}(?:\`\`\`|~~~)`),a=new RegExp(`^ {0,${Math.min(3,n-1)}}#`);for(;e&&(u=e.split("\n",1)[0],p=u,this.options.pedantic&&(p=p.replace(/^ {1,4}(?=( {4})*[^ ])/g,"  ")),!r.test(p))&&!a.test(p)&&!t.test(p)&&!i.test(e);){if(p.search(/[^ ]/)>=n||!p.trim())h+="\n"+p.slice(n);else{if(o)break;if(c.search(/[^ ]/)>=4)break;if(r.test(c))break;if(a.test(c))break;if(i.test(c))break;h+="\n"+p}o||p.trim()||(o=!0),s+=u+"\n",e=e.substring(u.length+1),c=p.slice(n)}}b.loose||(l?b.loose=!0:/\n *\n *$/.test(s)&&(l=!0)),this.options.gfm&&(i=/^\[[ xX]\] /.exec(h),i&&(r="[ ] "!==i[0],h=h.replace(/^\[[ xX]\] +/,""))),b.items.push({type:"list_item",raw:s,task:!!i,checked:r,loose:!1,text:h}),b.raw+=s}b.items[b.items.length-1].raw=s.trimRight(),b.items[b.items.length-1].text=h.trimRight(),b.raw=b.raw.trimRight();const _=b.items.length;for(a=0;a<_;a++)if(this.lexer.state.top=!1,b.items[a].tokens=this.lexer.blockTokens(b.items[a].text,[]),!b.loose){const e=b.items[a].tokens.filter((e=>"space"===e.type)),t=e.length>0&&e.some((e=>/\n.*\n/.test(e.raw)));b.loose=t}if(b.loose)for(a=0;a<_;a++)b.items[a].loose=!0;return b}}html(e){const t=this.rules.block.html.exec(e);if(t){const e={type:"html",block:!0,raw:t[0],pre:!this.options.sanitizer&&("pre"===t[1]||"script"===t[1]||"style"===t[1]),text:t[0]};if(this.options.sanitize){const s=this.options.sanitizer?this.options.sanitizer(t[0]):j(t[0]),i=e;i.type="paragraph",i.text=s,i.tokens=this.lexer.inline(s)}return e}}def(e){const t=this.rules.block.def.exec(e);if(t){const e=t[1].toLowerCase().replace(/\s+/g," "),s=t[2]?t[2].replace(/^<(.*)>$/,"$1").replace(this.rules.inline._escapes,"$1"):"",i=t[3]?t[3].substring(1,t[3].length-1).replace(this.rules.inline._escapes,"$1"):t[3];return{type:"def",tag:e,raw:t[0],href:s,title:i}}}table(e){const t=this.rules.block.table.exec(e);if(t){const e={type:"table",raw:t[0],header:D(t[1]).map((e=>({text:e}))),align:t[2].replace(/^ *|\| *$/g,"").split(/ *\| */),rows:t[3]&&t[3].trim()?t[3].replace(/\n[ \t]*$/,"").split("\n"):[]};if(e.header.length===e.align.length){let t,s,i,r,n=e.align.length;for(t=0;t<n;t++)/^ *-+: *$/.test(e.align[t])?e.align[t]="right":/^ *:-+: *$/.test(e.align[t])?e.align[t]="center":/^ *:-+ *$/.test(e.align[t])?e.align[t]="left":e.align[t]=null;for(n=e.rows.length,t=0;t<n;t++)e.rows[t]=D(e.rows[t],e.header.length).map((e=>({text:e})));for(n=e.header.length,s=0;s<n;s++)e.header[s].tokens=this.lexer.inline(e.header[s].text);for(n=e.rows.length,s=0;s<n;s++)for(r=e.rows[s],i=0;i<r.length;i++)r[i].tokens=this.lexer.inline(r[i].text);return e}}}lheading(e){const t=this.rules.block.lheading.exec(e);if(t)return{type:"heading",raw:t[0],depth:"="===t[2].charAt(0)?1:2,text:t[1],tokens:this.lexer.inline(t[1])}}paragraph(e){const t=this.rules.block.paragraph.exec(e);if(t){const e="\n"===t[1].charAt(t[1].length-1)?t[1].slice(0,-1):t[1];return{type:"paragraph",raw:t[0],text:e,tokens:this.lexer.inline(e)}}}text(e){const t=this.rules.block.text.exec(e);if(t)return{type:"text",raw:t[0],text:t[0],tokens:this.lexer.inline(t[0])}}escape(e){const t=this.rules.inline.escape.exec(e);if(t)return{type:"escape",raw:t[0],text:j(t[1])}}tag(e){const t=this.rules.inline.tag.exec(e);if(t)return!this.lexer.state.inLink&&/^<a /i.test(t[0])?this.lexer.state.inLink=!0:this.lexer.state.inLink&&/^<\/a>/i.test(t[0])&&(this.lexer.state.inLink=!1),!this.lexer.state.inRawBlock&&/^<(pre|code|kbd|script)(\s|>)/i.test(t[0])?this.lexer.state.inRawBlock=!0:this.lexer.state.inRawBlock&&/^<\/(pre|code|kbd|script)(\s|>)/i.test(t[0])&&(this.lexer.state.inRawBlock=!1),{type:this.options.sanitize?"text":"html",raw:t[0],inLink:this.lexer.state.inLink,inRawBlock:this.lexer.state.inRawBlock,block:!1,text:this.options.sanitize?this.options.sanitizer?this.options.sanitizer(t[0]):j(t[0]):t[0]}}link(e){const t=this.rules.inline.link.exec(e);if(t){const e=t[2].trim();if(!this.options.pedantic&&/^</.test(e)){if(!/>$/.test(e))return;const t=B(e.slice(0,-1),"\\");if((e.length-t.length)%2==0)return}else{const e=function(e,t){if(-1===e.indexOf(t[1]))return-1;const s=e.length;let i=0,r=0;for(;r<s;r++)if("\\"===e[r])r++;else if(e[r]===t[0])i++;else if(e[r]===t[1]&&(i--,i<0))return r;return-1}(t[2],"()");if(e>-1){const s=(0===t[0].indexOf("!")?5:4)+t[1].length+e;t[2]=t[2].substring(0,e),t[0]=t[0].substring(0,s).trim(),t[3]=""}}let s=t[2],i="";if(this.options.pedantic){const e=/^([^'"]*[^\s])\s+(['"])(.*)\2/.exec(s);e&&(s=e[1],i=e[3])}else i=t[3]?t[3].slice(1,-1):"";return s=s.trim(),/^</.test(s)&&(s=this.options.pedantic&&!/>$/.test(e)?s.slice(1):s.slice(1,-1)),V(t,{href:s?s.replace(this.rules.inline._escapes,"$1"):s,title:i?i.replace(this.rules.inline._escapes,"$1"):i},t[0],this.lexer)}}reflink(e,t){let s;if((s=this.rules.inline.reflink.exec(e))||(s=this.rules.inline.nolink.exec(e))){let e=(s[2]||s[1]).replace(/\s+/g," ");if(e=t[e.toLowerCase()],!e){const e=s[0].charAt(0);return{type:"text",raw:e,text:e}}return V(s,e,s[0],this.lexer)}}emStrong(e,t,s=""){let i=this.rules.inline.emStrong.lDelim.exec(e);if(!i)return;if(i[3]&&s.match(/[\p{L}\p{N}]/u))return;if(!(i[1]||i[2]||"")||!s||this.rules.inline.punctuation.exec(s)){const s=[...i[0]].length-1;let r,n,a=s,o=0;const l="*"===i[0][0]?this.rules.inline.emStrong.rDelimAst:this.rules.inline.emStrong.rDelimUnd;for(l.lastIndex=0,t=t.slice(-1*e.length+s);null!=(i=l.exec(t));){if(r=i[1]||i[2]||i[3]||i[4]||i[5]||i[6],!r)continue;if(n=[...r].length,i[3]||i[4]){a+=n;continue}if((i[5]||i[6])&&s%3&&!((s+n)%3)){o+=n;continue}if(a-=n,a>0)continue;n=Math.min(n,n+a+o);const t=[...e].slice(0,s+i.index+n+1).join("");if(Math.min(s,n)%2){const e=t.slice(1,-1);return{type:"em",raw:t,text:e,tokens:this.lexer.inlineTokens(e)}}const l=t.slice(2,-2);return{type:"strong",raw:t,text:l,tokens:this.lexer.inlineTokens(l)}}}}codespan(e){const t=this.rules.inline.code.exec(e);if(t){let e=t[2].replace(/\n/g," ");const s=/[^ ]/.test(e),i=/^ /.test(e)&&/ $/.test(e);return s&&i&&(e=e.substring(1,e.length-1)),e=j(e,!0),{type:"codespan",raw:t[0],text:e}}}br(e){const t=this.rules.inline.br.exec(e);if(t)return{type:"br",raw:t[0]}}del(e){const t=this.rules.inline.del.exec(e);if(t)return{type:"del",raw:t[0],text:t[2],tokens:this.lexer.inlineTokens(t[2])}}autolink(e,t){const s=this.rules.inline.autolink.exec(e);if(s){let e,i;return"@"===s[2]?(e=j(this.options.mangle?t(s[1]):s[1]),i="mailto:"+e):(e=j(s[1]),i=e),{type:"link",raw:s[0],text:e,href:i,tokens:[{type:"text",raw:e,text:e}]}}}url(e,t){let s;if(s=this.rules.inline.url.exec(e)){let e,i;if("@"===s[2])e=j(this.options.mangle?t(s[0]):s[0]),i="mailto:"+e;else{let t;do{t=s[0],s[0]=this.rules.inline._backpedal.exec(s[0])[0]}while(t!==s[0]);e=j(s[0]),i="www."===s[1]?"http://"+s[0]:s[0]}return{type:"link",raw:s[0],text:e,href:i,tokens:[{type:"text",raw:e,text:e}]}}}inlineText(e,t){const s=this.rules.inline.text.exec(e);if(s){let e;return e=this.lexer.state.inRawBlock?this.options.sanitize?this.options.sanitizer?this.options.sanitizer(s[0]):j(s[0]):s[0]:j(this.options.smartypants?t(s[0]):s[0]),{type:"text",raw:s[0],text:e}}}}const Q={newline:/^(?: *(?:\n|$))+/,code:/^( {4}[^\n]+(?:\n(?: *(?:\n|$))*)?)+/,fences:/^ {0,3}(`{3,}(?=[^`\n]*(?:\n|$))|~{3,})([^\n]*)(?:\n|$)(?:|([\s\S]*?)(?:\n|$))(?: {0,3}\1[~`]* *(?=\n|$)|$)/,hr:/^ {0,3}((?:-[\t ]*){3,}|(?:_[ \t]*){3,}|(?:\*[ \t]*){3,})(?:\n+|$)/,heading:/^ {0,3}(#{1,6})(?=\s|$)(.*)(?:\n+|$)/,blockquote:/^( {0,3}> ?(paragraph|[^\n]*)(?:\n|$))+/,list:/^( {0,3}bull)([ \t][^\n]+?)?(?:\n|$)/,html:"^ {0,3}(?:<(script|pre|style|textarea)[\\s>][\\s\\S]*?(?:</\\1>[^\\n]*\\n+|$)|comment[^\\n]*(\\n+|$)|<\\?[\\s\\S]*?(?:\\?>\\n*|$)|<![A-Z][\\s\\S]*?(?:>\\n*|$)|<!\\[CDATA\\[[\\s\\S]*?(?:\\]\\]>\\n*|$)|</?(tag)(?: +|\\n|/?>)[\\s\\S]*?(?:(?:\\n *)+\\n|$)|<(?!script|pre|style|textarea)([a-z][\\w-]*)(?:attribute)*? */?>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n *)+\\n|$)|</(?!script|pre|style|textarea)[a-z][\\w-]*\\s*>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n *)+\\n|$))",def:/^ {0,3}\[(label)\]: *(?:\n *)?([^<\s][^\s]*|<.*?>)(?:(?: +(?:\n *)?| *\n *)(title))? *(?:\n+|$)/,table:q,lheading:/^((?:(?!^bull ).|\n(?!\n|bull ))+?)\n {0,3}(=+|-+) *(?:\n+|$)/,_paragraph:/^([^\n]+(?:\n(?!hr|heading|lheading|blockquote|fences|list|html|table| +\n)[^\n]+)*)/,text:/^[^\n]+/,_label:/(?!\s*\])(?:\\.|[^\[\]\\])+/,_title:/(?:"(?:\\"?|[^"\\])*"|'[^'\n]*(?:\n[^'\n]+)*\n?'|\([^()]*\))/};Q.def=P(Q.def).replace("label",Q._label).replace("title",Q._title).getRegex(),Q.bullet=/(?:[*+-]|\d{1,9}[.)])/,Q.listItemStart=P(/^( *)(bull) */).replace("bull",Q.bullet).getRegex(),Q.list=P(Q.list).replace(/bull/g,Q.bullet).replace("hr","\\n+(?=\\1?(?:(?:- *){3,}|(?:_ *){3,}|(?:\\* *){3,})(?:\\n+|$))").replace("def","\\n+(?="+Q.def.source+")").getRegex(),Q._tag="address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|meta|nav|noframes|ol|optgroup|option|p|param|section|source|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul",Q._comment=/<!--(?!-?>)[\s\S]*?(?:-->|$)/,Q.html=P(Q.html,"i").replace("comment",Q._comment).replace("tag",Q._tag).replace("attribute",/ +[a-zA-Z:_][\w.:-]*(?: *= *"[^"\n]*"| *= *'[^'\n]*'| *= *[^\s"'=<>`]+)?/).getRegex(),Q.lheading=P(Q.lheading).replace(/bull/g,Q.bullet).getRegex(),Q.paragraph=P(Q._paragraph).replace("hr",Q.hr).replace("heading"," {0,3}#{1,6} ").replace("|lheading","").replace("|table","").replace("blockquote"," {0,3}>").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list"," {0,3}(?:[*+-]|1[.)]) ").replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",Q._tag).getRegex(),Q.blockquote=P(Q.blockquote).replace("paragraph",Q.paragraph).getRegex(),Q.normal={...Q},Q.gfm={...Q.normal,table:"^ *([^\\n ].*\\|.*)\\n {0,3}(?:\\| *)?(:?-+:? *(?:\\| *:?-+:? *)*)(?:\\| *)?(?:\\n((?:(?! *\\n|hr|heading|blockquote|code|fences|list|html).*(?:\\n|$))*)\\n*|$)"},Q.gfm.table=P(Q.gfm.table).replace("hr",Q.hr).replace("heading"," {0,3}#{1,6} ").replace("blockquote"," {0,3}>").replace("code"," {4}[^\\n]").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list"," {0,3}(?:[*+-]|1[.)]) ").replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",Q._tag).getRegex(),Q.gfm.paragraph=P(Q._paragraph).replace("hr",Q.hr).replace("heading"," {0,3}#{1,6} ").replace("|lheading","").replace("table",Q.gfm.table).replace("blockquote"," {0,3}>").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list"," {0,3}(?:[*+-]|1[.)]) ").replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",Q._tag).getRegex(),Q.pedantic={...Q.normal,html:P("^ *(?:comment *(?:\\n|\\s*$)|<(tag)[\\s\\S]+?</\\1> *(?:\\n{2,}|\\s*$)|<tag(?:\"[^\"]*\"|'[^']*'|\\s[^'\"/>\\s]*)*?/?> *(?:\\n{2,}|\\s*$))").replace("comment",Q._comment).replace(/tag/g,"(?!(?:a|em|strong|small|s|cite|q|dfn|abbr|data|time|code|var|samp|kbd|sub|sup|i|b|u|mark|ruby|rt|rp|bdi|bdo|span|br|wbr|ins|del|img)\\b)\\w+(?!:|[^\\w\\s@]*@)\\b").getRegex(),def:/^ *\[([^\]]+)\]: *<?([^\s>]+)>?(?: +(["(][^\n]+[")]))? *(?:\n+|$)/,heading:/^(#{1,6})(.*)(?:\n+|$)/,fences:q,lheading:/^(.+?)\n {0,3}(=+|-+) *(?:\n+|$)/,paragraph:P(Q.normal._paragraph).replace("hr",Q.hr).replace("heading"," *#{1,6} *[^\n]").replace("lheading",Q.lheading).replace("blockquote"," {0,3}>").replace("|fences","").replace("|list","").replace("|html","").getRegex()};const G={escape:/^\\([!"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])/,autolink:/^<(scheme:[^\s\x00-\x1f<>]*|email)>/,url:q,tag:"^comment|^</[a-zA-Z][\\w:-]*\\s*>|^<[a-zA-Z][\\w-]*(?:attribute)*?\\s*/?>|^<\\?[\\s\\S]*?\\?>|^<![a-zA-Z]+\\s[\\s\\S]*?>|^<!\\[CDATA\\[[\\s\\S]*?\\]\\]>",link:/^!?\[(label)\]\(\s*(href)(?:\s+(title))?\s*\)/,reflink:/^!?\[(label)\]\[(ref)\]/,nolink:/^!?\[(ref)\](?:\[\])?/,reflinkSearch:"reflink|nolink(?!\\()",emStrong:{lDelim:/^(?:\*+(?:((?!\*)[punct])|[^\s*]))|^_+(?:((?!_)[punct])|([^\s_]))/,rDelimAst:/^[^_*]*?__[^_*]*?\*[^_*]*?(?=__)|[^*]+(?=[^*])|(?!\*)[punct](\*+)(?=[\s]|$)|[^punct\s](\*+)(?!\*)(?=[punct\s]|$)|(?!\*)[punct\s](\*+)(?=[^punct\s])|[\s](\*+)(?!\*)(?=[punct])|(?!\*)[punct](\*+)(?!\*)(?=[punct])|[^punct\s](\*+)(?=[^punct\s])/,rDelimUnd:/^[^_*]*?\*\*[^_*]*?_[^_*]*?(?=\*\*)|[^_]+(?=[^_])|(?!_)[punct](_+)(?=[\s]|$)|[^punct\s](_+)(?!_)(?=[punct\s]|$)|(?!_)[punct\s](_+)(?=[^punct\s])|[\s](_+)(?!_)(?=[punct])|(?!_)[punct](_+)(?!_)(?=[punct])/},code:/^(`+)([^`]|[^`][\s\S]*?[^`])\1(?!`)/,br:/^( {2,}|\\)\n(?!\s*$)/,del:q,text:/^(`+|[^`])(?:(?= {2,}\n)|[\s\S]*?(?:(?=[\\<!\[`*_]|\b_|$)|[^ ](?= {2,}\n)))/,punctuation:/^((?![*_])[\spunctuation])/};function H(e){return e.replace(/---/g,"—").replace(/--/g,"–").replace(/(^|[-\u2014/(\[{"\s])'/g,"$1‘").replace(/'/g,"’").replace(/(^|[-\u2014/(\[{\u2018\s])"/g,"$1“").replace(/"/g,"”").replace(/\.{3}/g,"…")}function W(e){let t,s,i="";const r=e.length;for(t=0;t<r;t++)s=e.charCodeAt(t),Math.random()>.5&&(s="x"+s.toString(16)),i+="&#"+s+";";return i}G._punctuation="\\p{P}$+<=>`^|~",G.punctuation=P(G.punctuation,"u").replace(/punctuation/g,G._punctuation).getRegex(),G.blockSkip=/\[[^[\]]*?\]\([^\(\)]*?\)|`[^`]*?`|<[^<>]*?>/g,G.anyPunctuation=/\\[punct]/g,G._escapes=/\\([punct])/g,G._comment=P(Q._comment).replace("(?:--\x3e|$)","--\x3e").getRegex(),G.emStrong.lDelim=P(G.emStrong.lDelim,"u").replace(/punct/g,G._punctuation).getRegex(),G.emStrong.rDelimAst=P(G.emStrong.rDelimAst,"gu").replace(/punct/g,G._punctuation).getRegex(),G.emStrong.rDelimUnd=P(G.emStrong.rDelimUnd,"gu").replace(/punct/g,G._punctuation).getRegex(),G.anyPunctuation=P(G.anyPunctuation,"gu").replace(/punct/g,G._punctuation).getRegex(),G._escapes=P(G._escapes,"gu").replace(/punct/g,G._punctuation).getRegex(),G._scheme=/[a-zA-Z][a-zA-Z0-9+.-]{1,31}/,G._email=/[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+(@)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+(?![-_])/,G.autolink=P(G.autolink).replace("scheme",G._scheme).replace("email",G._email).getRegex(),G._attribute=/\s+[a-zA-Z:_][\w.:-]*(?:\s*=\s*"[^"]*"|\s*=\s*'[^']*'|\s*=\s*[^\s"'=<>`]+)?/,G.tag=P(G.tag).replace("comment",G._comment).replace("attribute",G._attribute).getRegex(),G._label=/(?:\[(?:\\.|[^\[\]\\])*\]|\\.|`[^`]*`|[^\[\]\\`])*?/,G._href=/<(?:\\.|[^\n<>\\])+>|[^\s\x00-\x1f]*/,G._title=/"(?:\\"?|[^"\\])*"|'(?:\\'?|[^'\\])*'|\((?:\\\)?|[^)\\])*\)/,G.link=P(G.link).replace("label",G._label).replace("href",G._href).replace("title",G._title).getRegex(),G.reflink=P(G.reflink).replace("label",G._label).replace("ref",Q._label).getRegex(),G.nolink=P(G.nolink).replace("ref",Q._label).getRegex(),G.reflinkSearch=P(G.reflinkSearch,"g").replace("reflink",G.reflink).replace("nolink",G.nolink).getRegex(),G.normal={...G},G.pedantic={...G.normal,strong:{start:/^__|\*\*/,middle:/^__(?=\S)([\s\S]*?\S)__(?!_)|^\*\*(?=\S)([\s\S]*?\S)\*\*(?!\*)/,endAst:/\*\*(?!\*)/g,endUnd:/__(?!_)/g},em:{start:/^_|\*/,middle:/^()\*(?=\S)([\s\S]*?\S)\*(?!\*)|^_(?=\S)([\s\S]*?\S)_(?!_)/,endAst:/\*(?!\*)/g,endUnd:/_(?!_)/g},link:P(/^!?\[(label)\]\((.*?)\)/).replace("label",G._label).getRegex(),reflink:P(/^!?\[(label)\]\s*\[([^\]]*)\]/).replace("label",G._label).getRegex()},G.gfm={...G.normal,escape:P(G.escape).replace("])","~|])").getRegex(),_extended_email:/[A-Za-z0-9._+-]+(@)[a-zA-Z0-9-_]+(?:\.[a-zA-Z0-9-_]*[a-zA-Z0-9])+(?![-_])/,url:/^((?:ftp|https?):\/\/|www\.)(?:[a-zA-Z0-9\-]+\.?)+[^\s<]*|^email/,_backpedal:/(?:[^?!.,:;*_'"~()&]+|\([^)]*\)|&(?![a-zA-Z0-9]+;$)|[?!.,:;*_'"~)]+(?!$))+/,del:/^(~~?)(?=[^\s~])([\s\S]*?[^\s~])\1(?=[^~]|$)/,text:/^([`~]+|[^`~])(?:(?= {2,}\n)|(?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)|[\s\S]*?(?:(?=[\\<!\[`*~_]|\b_|https?:\/\/|ftp:\/\/|www\.|$)|[^ ](?= {2,}\n)|[^a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-](?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)))/},G.gfm.url=P(G.gfm.url,"i").replace("email",G.gfm._extended_email).getRegex(),G.breaks={...G.gfm,br:P(G.br).replace("{2,}","*").getRegex(),text:P(G.gfm.text).replace("\\b_","\\b_| {2,}\\n").replace(/\{2,\}/g,"*").getRegex()};class X{tokens;options;state;tokenizer;inlineQueue;constructor(e){this.tokens=[],this.tokens.links=Object.create(null),this.options=e||k,this.options.tokenizer=this.options.tokenizer||new Z,this.tokenizer=this.options.tokenizer,this.tokenizer.options=this.options,this.tokenizer.lexer=this,this.inlineQueue=[],this.state={inLink:!1,inRawBlock:!1,top:!0};const t={block:Q.normal,inline:G.normal};this.options.pedantic?(t.block=Q.pedantic,t.inline=G.pedantic):this.options.gfm&&(t.block=Q.gfm,this.options.breaks?t.inline=G.breaks:t.inline=G.gfm),this.tokenizer.rules=t}static get rules(){return{block:Q,inline:G}}static lex(e,t){return new X(t).lex(e)}static lexInline(e,t){return new X(t).inlineTokens(e)}lex(e){let t;for(e=e.replace(/\r\n|\r/g,"\n"),this.blockTokens(e,this.tokens);t=this.inlineQueue.shift();)this.inlineTokens(t.src,t.tokens);return this.tokens}blockTokens(e,t=[]){let s,i,r,n;for(e=this.options.pedantic?e.replace(/\t/g,"    ").replace(/^ +$/gm,""):e.replace(/^( *)(\t+)/gm,((e,t,s)=>t+"    ".repeat(s.length)));e;)if(!(this.options.extensions&&this.options.extensions.block&&this.options.extensions.block.some((i=>!!(s=i.call({lexer:this},e,t))&&(e=e.substring(s.raw.length),t.push(s),!0)))))if(s=this.tokenizer.space(e))e=e.substring(s.raw.length),1===s.raw.length&&t.length>0?t[t.length-1].raw+="\n":t.push(s);else if(s=this.tokenizer.code(e))e=e.substring(s.raw.length),i=t[t.length-1],!i||"paragraph"!==i.type&&"text"!==i.type?t.push(s):(i.raw+="\n"+s.raw,i.text+="\n"+s.text,this.inlineQueue[this.inlineQueue.length-1].src=i.text);else if(s=this.tokenizer.fences(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.heading(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.hr(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.blockquote(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.list(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.html(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.def(e))e=e.substring(s.raw.length),i=t[t.length-1],!i||"paragraph"!==i.type&&"text"!==i.type?this.tokens.links[s.tag]||(this.tokens.links[s.tag]={href:s.href,title:s.title}):(i.raw+="\n"+s.raw,i.text+="\n"+s.raw,this.inlineQueue[this.inlineQueue.length-1].src=i.text);else if(s=this.tokenizer.table(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.lheading(e))e=e.substring(s.raw.length),t.push(s);else{if(r=e,this.options.extensions&&this.options.extensions.startBlock){let t=1/0;const s=e.slice(1);let i;this.options.extensions.startBlock.forEach((e=>{i=e.call({lexer:this},s),"number"==typeof i&&i>=0&&(t=Math.min(t,i))})),t<1/0&&t>=0&&(r=e.substring(0,t+1))}if(this.state.top&&(s=this.tokenizer.paragraph(r)))i=t[t.length-1],n&&"paragraph"===i.type?(i.raw+="\n"+s.raw,i.text+="\n"+s.text,this.inlineQueue.pop(),this.inlineQueue[this.inlineQueue.length-1].src=i.text):t.push(s),n=r.length!==e.length,e=e.substring(s.raw.length);else if(s=this.tokenizer.text(e))e=e.substring(s.raw.length),i=t[t.length-1],i&&"text"===i.type?(i.raw+="\n"+s.raw,i.text+="\n"+s.text,this.inlineQueue.pop(),this.inlineQueue[this.inlineQueue.length-1].src=i.text):t.push(s);else if(e){const t="Infinite loop on byte: "+e.charCodeAt(0);if(this.options.silent){console.error(t);break}throw new Error(t)}}return this.state.top=!0,t}inline(e,t=[]){return this.inlineQueue.push({src:e,tokens:t}),t}inlineTokens(e,t=[]){let s,i,r,n,a,o,l=e;if(this.tokens.links){const e=Object.keys(this.tokens.links);if(e.length>0)for(;null!=(n=this.tokenizer.rules.inline.reflinkSearch.exec(l));)e.includes(n[0].slice(n[0].lastIndexOf("[")+1,-1))&&(l=l.slice(0,n.index)+"["+"a".repeat(n[0].length-2)+"]"+l.slice(this.tokenizer.rules.inline.reflinkSearch.lastIndex))}for(;null!=(n=this.tokenizer.rules.inline.blockSkip.exec(l));)l=l.slice(0,n.index)+"["+"a".repeat(n[0].length-2)+"]"+l.slice(this.tokenizer.rules.inline.blockSkip.lastIndex);for(;null!=(n=this.tokenizer.rules.inline.anyPunctuation.exec(l));)l=l.slice(0,n.index)+"++"+l.slice(this.tokenizer.rules.inline.anyPunctuation.lastIndex);for(;e;)if(a||(o=""),a=!1,!(this.options.extensions&&this.options.extensions.inline&&this.options.extensions.inline.some((i=>!!(s=i.call({lexer:this},e,t))&&(e=e.substring(s.raw.length),t.push(s),!0)))))if(s=this.tokenizer.escape(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.tag(e))e=e.substring(s.raw.length),i=t[t.length-1],i&&"text"===s.type&&"text"===i.type?(i.raw+=s.raw,i.text+=s.text):t.push(s);else if(s=this.tokenizer.link(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.reflink(e,this.tokens.links))e=e.substring(s.raw.length),i=t[t.length-1],i&&"text"===s.type&&"text"===i.type?(i.raw+=s.raw,i.text+=s.text):t.push(s);else if(s=this.tokenizer.emStrong(e,l,o))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.codespan(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.br(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.del(e))e=e.substring(s.raw.length),t.push(s);else if(s=this.tokenizer.autolink(e,W))e=e.substring(s.raw.length),t.push(s);else if(this.state.inLink||!(s=this.tokenizer.url(e,W))){if(r=e,this.options.extensions&&this.options.extensions.startInline){let t=1/0;const s=e.slice(1);let i;this.options.extensions.startInline.forEach((e=>{i=e.call({lexer:this},s),"number"==typeof i&&i>=0&&(t=Math.min(t,i))})),t<1/0&&t>=0&&(r=e.substring(0,t+1))}if(s=this.tokenizer.inlineText(r,H))e=e.substring(s.raw.length),"_"!==s.raw.slice(-1)&&(o=s.raw.slice(-1)),a=!0,i=t[t.length-1],i&&"text"===i.type?(i.raw+=s.raw,i.text+=s.text):t.push(s);else if(e){const t="Infinite loop on byte: "+e.charCodeAt(0);if(this.options.silent){console.error(t);break}throw new Error(t)}}else e=e.substring(s.raw.length),t.push(s);return t}}class Y{options;constructor(e){this.options=e||k}code(e,t,s){const i=(t||"").match(/\S*/)[0];if(this.options.highlight){const t=this.options.highlight(e,i);null!=t&&t!==e&&(s=!0,e=t)}return e=e.replace(/\n$/,"")+"\n",i?'<pre><code class="'+this.options.langPrefix+j(i)+'">'+(s?e:j(e,!0))+"</code></pre>\n":"<pre><code>"+(s?e:j(e,!0))+"</code></pre>\n"}blockquote(e){return`<blockquote>\n${e}</blockquote>\n`}html(e,t){return e}heading(e,t,s,i){if(this.options.headerIds){return`<h${t} id="${this.options.headerPrefix+i.slug(s)}">${e}</h${t}>\n`}return`<h${t}>${e}</h${t}>\n`}hr(){return this.options.xhtml?"<hr/>\n":"<hr>\n"}list(e,t,s){const i=t?"ol":"ul";return"<"+i+(t&&1!==s?' start="'+s+'"':"")+">\n"+e+"</"+i+">\n"}listitem(e,t,s){return`<li>${e}</li>\n`}checkbox(e){return"<input "+(e?'checked="" ':"")+'disabled="" type="checkbox"'+(this.options.xhtml?" /":"")+"> "}paragraph(e){return`<p>${e}</p>\n`}table(e,t){return t&&(t=`<tbody>${t}</tbody>`),"<table>\n<thead>\n"+e+"</thead>\n"+t+"</table>\n"}tablerow(e){return`<tr>\n${e}</tr>\n`}tablecell(e,t){const s=t.header?"th":"td";return(t.align?`<${s} align="${t.align}">`:`<${s}>`)+e+`</${s}>\n`}strong(e){return`<strong>${e}</strong>`}em(e){return`<em>${e}</em>`}codespan(e){return`<code>${e}</code>`}br(){return this.options.xhtml?"<br/>":"<br>"}del(e){return`<del>${e}</del>`}link(e,t,s){if(null===(e=C(this.options.sanitize,this.options.baseUrl,e)))return s;let i='<a href="'+e+'"';return t&&(i+=' title="'+t+'"'),i+=">"+s+"</a>",i}image(e,t,s){if(null===(e=C(this.options.sanitize,this.options.baseUrl,e)))return s;let i=`<img src="${e}" alt="${s}"`;return t&&(i+=` title="${t}"`),i+=this.options.xhtml?"/>":">",i}text(e){return e}}class K{strong(e){return e}em(e){return e}codespan(e){return e}del(e){return e}html(e){return e}text(e){return e}link(e,t,s){return""+s}image(e,t,s){return""+s}br(){return""}}class J{seen;constructor(){this.seen={}}serialize(e){return e.toLowerCase().trim().replace(/<[!\/a-z].*?>/gi,"").replace(/[\u2000-\u206F\u2E00-\u2E7F\\'!"#$%&()*+,./:;<=>?@[\]^`{|}~]/g,"").replace(/\s/g,"-")}getNextSafeSlug(e,t){let s=e,i=0;if(this.seen.hasOwnProperty(s)){i=this.seen[e];do{i++,s=e+"-"+i}while(this.seen.hasOwnProperty(s))}return t||(this.seen[e]=i,this.seen[s]=0),s}slug(e,t={}){const s=this.serialize(e);return this.getNextSafeSlug(s,t.dryrun)}}class ee{options;renderer;textRenderer;slugger;constructor(e){this.options=e||k,this.options.renderer=this.options.renderer||new Y,this.renderer=this.options.renderer,this.renderer.options=this.options,this.textRenderer=new K,this.slugger=new J}static parse(e,t){return new ee(t).parse(e)}static parseInline(e,t){return new ee(t).parseInline(e)}parse(e,t=!0){let s,i,r,n,a,o,l,c,p,u,h,d,g,m,b,f,_,y,v,k="";const x=e.length;for(s=0;s<x;s++)if(u=e[s],this.options.extensions&&this.options.extensions.renderers&&this.options.extensions.renderers[u.type]&&(v=this.options.extensions.renderers[u.type].call({parser:this},u),!1!==v||!["space","hr","heading","code","table","blockquote","list","html","paragraph","text"].includes(u.type)))k+=v||"";else switch(u.type){case"space":continue;case"hr":k+=this.renderer.hr();continue;case"heading":k+=this.renderer.heading(this.parseInline(u.tokens),u.depth,R(this.parseInline(u.tokens,this.textRenderer)),this.slugger);continue;case"code":k+=this.renderer.code(u.text,u.lang,!!u.escaped);continue;case"table":for(c="",l="",n=u.header.length,i=0;i<n;i++)l+=this.renderer.tablecell(this.parseInline(u.header[i].tokens),{header:!0,align:u.align[i]});for(c+=this.renderer.tablerow(l),p="",n=u.rows.length,i=0;i<n;i++){for(o=u.rows[i],l="",a=o.length,r=0;r<a;r++)l+=this.renderer.tablecell(this.parseInline(o[r].tokens),{header:!1,align:u.align[r]});p+=this.renderer.tablerow(l)}k+=this.renderer.table(c,p);continue;case"blockquote":p=this.parse(u.tokens),k+=this.renderer.blockquote(p);continue;case"list":for(h=u.ordered,d=u.start,g=u.loose,n=u.items.length,p="",i=0;i<n;i++)b=u.items[i],f=b.checked,_=b.task,m="",b.task&&(y=this.renderer.checkbox(!!f),g?b.tokens.length>0&&"paragraph"===b.tokens[0].type?(b.tokens[0].text=y+" "+b.tokens[0].text,b.tokens[0].tokens&&b.tokens[0].tokens.length>0&&"text"===b.tokens[0].tokens[0].type&&(b.tokens[0].tokens[0].text=y+" "+b.tokens[0].tokens[0].text)):b.tokens.unshift({type:"text",text:y}):m+=y),m+=this.parse(b.tokens,g),p+=this.renderer.listitem(m,_,!!f);k+=this.renderer.list(p,h,d);continue;case"html":k+=this.renderer.html(u.text,u.block);continue;case"paragraph":k+=this.renderer.paragraph(this.parseInline(u.tokens));continue;case"text":for(p=u.tokens?this.parseInline(u.tokens):u.text;s+1<x&&"text"===e[s+1].type;)u=e[++s],p+="\n"+(u.tokens?this.parseInline(u.tokens):u.text);k+=t?this.renderer.paragraph(p):p;continue;default:{const e='Token with "'+u.type+'" type was not found.';if(this.options.silent)return console.error(e),"";throw new Error(e)}}return k}parseInline(e,t){t=t||this.renderer;let s,i,r,n="";const a=e.length;for(s=0;s<a;s++)if(i=e[s],this.options.extensions&&this.options.extensions.renderers&&this.options.extensions.renderers[i.type]&&(r=this.options.extensions.renderers[i.type].call({parser:this},i),!1!==r||!["escape","html","link","image","strong","em","codespan","br","del","text"].includes(i.type)))n+=r||"";else switch(i.type){case"escape":case"text":n+=t.text(i.text);break;case"html":n+=t.html(i.text);break;case"link":n+=t.link(i.href,i.title,this.parseInline(i.tokens,t));break;case"image":n+=t.image(i.href,i.title,i.text);break;case"strong":n+=t.strong(this.parseInline(i.tokens,t));break;case"em":n+=t.em(this.parseInline(i.tokens,t));break;case"codespan":n+=t.codespan(i.text);break;case"br":n+=t.br();break;case"del":n+=t.del(this.parseInline(i.tokens,t));break;default:{const e='Token with "'+i.type+'" type was not found.';if(this.options.silent)return console.error(e),"";throw new Error(e)}}return n}}class te{options;constructor(e){this.options=e||k}static passThroughHooks=new Set(["preprocess","postprocess"]);preprocess(e){return e}postprocess(e){return e}}const se=new class{defaults={async:!1,baseUrl:null,breaks:!1,extensions:null,gfm:!0,headerIds:!1,headerPrefix:"",highlight:null,hooks:null,langPrefix:"language-",mangle:!1,pedantic:!1,renderer:null,sanitize:!1,sanitizer:null,silent:!1,smartypants:!1,tokenizer:null,walkTokens:null,xhtml:!1};options=this.setOptions;parse=this.#e(X.lex,ee.parse);parseInline=this.#e(X.lexInline,ee.parseInline);Parser=ee;parser=ee.parse;Renderer=Y;TextRenderer=K;Lexer=X;lexer=X.lex;Tokenizer=Z;Slugger=J;Hooks=te;constructor(...e){this.use(...e)}walkTokens(e,t){let s=[];for(const i of e)switch(s=s.concat(t.call(this,i)),i.type){case"table":for(const e of i.header)s=s.concat(this.walkTokens(e.tokens,t));for(const e of i.rows)for(const i of e)s=s.concat(this.walkTokens(i.tokens,t));break;case"list":s=s.concat(this.walkTokens(i.items,t));break;default:this.defaults.extensions&&this.defaults.extensions.childTokens&&this.defaults.extensions.childTokens[i.type]?this.defaults.extensions.childTokens[i.type].forEach((e=>{s=s.concat(this.walkTokens(i[e],t))})):i.tokens&&(s=s.concat(this.walkTokens(i.tokens,t)))}return s}use(...e){const t=this.defaults.extensions||{renderers:{},childTokens:{}};return e.forEach((e=>{const s={...e};if(s.async=this.defaults.async||s.async||!1,e.extensions&&(e.extensions.forEach((e=>{if(!e.name)throw new Error("extension name required");if("renderer"in e){const s=t.renderers[e.name];t.renderers[e.name]=s?function(...t){let i=e.renderer.apply(this,t);return!1===i&&(i=s.apply(this,t)),i}:e.renderer}if("tokenizer"in e){if(!e.level||"block"!==e.level&&"inline"!==e.level)throw new Error("extension level must be 'block' or 'inline'");t[e.level]?t[e.level].unshift(e.tokenizer):t[e.level]=[e.tokenizer],e.start&&("block"===e.level?t.startBlock?t.startBlock.push(e.start):t.startBlock=[e.start]:"inline"===e.level&&(t.startInline?t.startInline.push(e.start):t.startInline=[e.start]))}"childTokens"in e&&e.childTokens&&(t.childTokens[e.name]=e.childTokens)})),s.extensions=t),e.renderer){const t=this.defaults.renderer||new Y(this.defaults);for(const s in e.renderer){const i=e.renderer[s],r=s,n=t[r];t[r]=(...e)=>{let s=i.apply(t,e);return!1===s&&(s=n.apply(t,e)),s||""}}s.renderer=t}if(e.tokenizer){const t=this.defaults.tokenizer||new Z(this.defaults);for(const s in e.tokenizer){const i=e.tokenizer[s],r=s,n=t[r];t[r]=(...e)=>{let s=i.apply(t,e);return!1===s&&(s=n.apply(t,e)),s}}s.tokenizer=t}if(e.hooks){const t=this.defaults.hooks||new te;for(const s in e.hooks){const i=e.hooks[s],r=s,n=t[r];te.passThroughHooks.has(s)?t[r]=e=>{if(this.defaults.async)return Promise.resolve(i.call(t,e)).then((e=>n.call(t,e)));const s=i.call(t,e);return n.call(t,s)}:t[r]=(...e)=>{let s=i.apply(t,e);return!1===s&&(s=n.apply(t,e)),s}}s.hooks=t}if(e.walkTokens){const t=this.defaults.walkTokens;s.walkTokens=function(s){let i=[];return i.push(e.walkTokens.call(this,s)),t&&(i=i.concat(t.call(this,s))),i}}this.defaults={...this.defaults,...s}})),this}setOptions(e){return this.defaults={...this.defaults,...e},this}#e(e,t){return(s,i,r)=>{"function"==typeof i&&(r=i,i=null);const n={...i},a={...this.defaults,...n},o=this.#t(!!a.silent,!!a.async,r);if(null==s)return o(new Error("marked(): input parameter is undefined or null"));if("string"!=typeof s)return o(new Error("marked(): input parameter is of type "+Object.prototype.toString.call(s)+", string expected"));if(function(e,t){e&&!e.silent&&(t&&console.warn("marked(): callback is deprecated since version 5.0.0, should not be used and will be removed in the future. Read more here: https://marked.js.org/using_pro#async"),(e.sanitize||e.sanitizer)&&console.warn("marked(): sanitize and sanitizer parameters are deprecated since version 0.7.0, should not be used and will be removed in the future. Read more here: https://marked.js.org/#/USING_ADVANCED.md#options"),(e.highlight||"language-"!==e.langPrefix)&&console.warn("marked(): highlight and langPrefix parameters are deprecated since version 5.0.0, should not be used and will be removed in the future. Instead use https://www.npmjs.com/package/marked-highlight."),e.mangle&&console.warn("marked(): mangle parameter is enabled by default, but is deprecated since version 5.0.0, and will be removed in the future. To clear this warning, install https://www.npmjs.com/package/marked-mangle, or disable by setting `{mangle: false}`."),e.baseUrl&&console.warn("marked(): baseUrl parameter is deprecated since version 5.0.0, should not be used and will be removed in the future. Instead use https://www.npmjs.com/package/marked-base-url."),e.smartypants&&console.warn("marked(): smartypants parameter is deprecated since version 5.0.0, should not be used and will be removed in the future. Instead use https://www.npmjs.com/package/marked-smartypants."),e.xhtml&&console.warn("marked(): xhtml parameter is deprecated since version 5.0.0, should not be used and will be removed in the future. Instead use https://www.npmjs.com/package/marked-xhtml."),(e.headerIds||e.headerPrefix)&&console.warn("marked(): headerIds and headerPrefix parameters enabled by default, but are deprecated since version 5.0.0, and will be removed in the future. To clear this warning, install  https://www.npmjs.com/package/marked-gfm-heading-id, or disable by setting `{headerIds: false}`."))}(a,r),a.hooks&&(a.hooks.options=a),r){const i=a.highlight;let n;try{a.hooks&&(s=a.hooks.preprocess(s)),n=e(s,a)}catch(e){return o(e)}const l=e=>{let s;if(!e)try{a.walkTokens&&this.walkTokens(n,a.walkTokens),s=t(n,a),a.hooks&&(s=a.hooks.postprocess(s))}catch(t){e=t}return a.highlight=i,e?o(e):r(null,s)};if(!i||i.length<3)return l();if(delete a.highlight,!n.length)return l();let c=0;return this.walkTokens(n,(e=>{"code"===e.type&&(c++,setTimeout((()=>{i(e.text,e.lang,((t,s)=>{if(t)return l(t);null!=s&&s!==e.text&&(e.text=s,e.escaped=!0),c--,0===c&&l()}))}),0))})),void(0===c&&l())}if(a.async)return Promise.resolve(a.hooks?a.hooks.preprocess(s):s).then((t=>e(t,a))).then((e=>a.walkTokens?Promise.all(this.walkTokens(e,a.walkTokens)).then((()=>e)):e)).then((e=>t(e,a))).then((e=>a.hooks?a.hooks.postprocess(e):e)).catch(o);try{a.hooks&&(s=a.hooks.preprocess(s));const i=e(s,a);a.walkTokens&&this.walkTokens(i,a.walkTokens);let r=t(i,a);return a.hooks&&(r=a.hooks.postprocess(r)),r}catch(e){return o(e)}}}#t(e,t,s){return i=>{if(i.message+="\nPlease report this to https://github.com/markedjs/marked.",e){const e="<p>An error occurred:</p><pre>"+j(i.message+"",!0)+"</pre>";return t?Promise.resolve(e):s?void s(null,e):e}if(t)return Promise.reject(i);if(!s)throw i;s(i)}}};function ie(e,t,s){return se.parse(e,t,s)}ie.options=ie.setOptions=function(e){return se.setOptions(e),ie.defaults=se.defaults,x(ie.defaults),ie},ie.getDefaults=v,ie.defaults=k,ie.use=function(...e){return se.use(...e),ie.defaults=se.defaults,x(ie.defaults),ie},ie.walkTokens=function(e,t){return se.walkTokens(e,t)},ie.parseInline=se.parseInline,ie.Parser=ee,ie.parser=ee.parse,ie.Renderer=Y,ie.TextRenderer=K,ie.Lexer=X,ie.lexer=X.lex,ie.Tokenizer=Z,ie.Slugger=J,ie.Hooks=te,ie.parse=ie,ie.options,ie.setOptions,ie.use,ie.walkTokens,ie.parseInline;
/**
 @license
 Copyright (c) 2015-2023 Lablup Inc. All rights reserved.
 */
let re=class extends p{constructor(){super(),this.condition="running",this.sessions=0,this.jobs=Object(),this.agents=0,this.is_admin=!1,this.is_superadmin=!1,this.resources=Object(),this.update_checker=Object(),this.authenticated=!1,this.manager_version="",this.webui_version="",this.cpu_total=0,this.cpu_used=0,this.cpu_percent="0",this.cpu_total_percent="0",this.cpu_total_usage_ratio=0,this.cpu_current_usage_ratio=0,this.mem_total="0",this.mem_used="0",this.mem_allocated="0",this.mem_total_usage_ratio=0,this.mem_current_usage_ratio=0,this.mem_current_usage_percent="0",this.cuda_gpu_total=0,this.cuda_gpu_used=0,this.cuda_fgpu_total=0,this.cuda_fgpu_used=0,this.rocm_gpu_total=0,this.rocm_gpu_used=0,this.tpu_total=0,this.tpu_used=0,this.ipu_total=0,this.ipu_used=0,this.atom_total=0,this.atom_used=0,this.notification=Object(),this.announcement="",this.invitations=Object(),this.downloadAppOS="",this.invitations=[],this.appDownloadMap={Linux:{os:"linux",architecture:["arm64","x64"],extension:"zip"},MacOS:{os:"macos",architecture:["intel","apple"],extension:"dmg"},Windows:{os:"win32",architecture:["arm64","x64"],extension:"zip"}}}static get styles(){return[u,a,o,h,l`
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
          transition: color ease-in .2s;
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

        mwc-button, mwc-button[unelevated], mwc-button[outlined] {
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
          background-color: #F6F6F6;
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
          --mdc-select-fill-color: rgba(255, 255, 255, 1.0);
          --mdc-select-label-ink-color: rgba(24, 24, 24, 1.0);
          --mdc-select-disabled-ink-color: rgba(24, 24, 24, 1.0);
          --mdc-select-dropdown-icon-color: rgba(24, 24, 24, 1.0);
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
      `]}firstUpdated(){var e;this.notification=globalThis.lablupNotification,this.update_checker=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#update-checker"),this._getUserOS(),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._readAnnouncement()}),!0):this._readAnnouncement()}_getUserOS(){this.downloadAppOS="MacOS",-1!=navigator.userAgent.indexOf("Mac")&&(this.downloadAppOS="MacOS"),-1!=navigator.userAgent.indexOf("Win")&&(this.downloadAppOS="Windows"),-1!=navigator.userAgent.indexOf("Linux")&&(this.downloadAppOS="Linux")}_refreshConsoleUpdateInformation(){this.is_superadmin&&globalThis.backendaioptions.get("automatic_update_check",!0)&&this.update_checker.checkRelease()}async _viewStateChanged(e){await this.updateComplete,!1!==e?(this.resourceMonitor.setAttribute("active","true"),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_superadmin=globalThis.backendaiclient.is_superadmin,this.is_admin=globalThis.backendaiclient.is_admin,this.authenticated=!0,this.manager_version=globalThis.backendaiclient.managerVersion,this.webui_version=globalThis.packageVersion,this.appDownloadUrl=globalThis.backendaiclient._config.appDownloadUrl,this.activeConnected&&this._refreshConsoleUpdateInformation(),this._refreshInvitations()}),!0):(this.is_superadmin=globalThis.backendaiclient.is_superadmin,this.is_admin=globalThis.backendaiclient.is_admin,this.authenticated=!0,this.manager_version=globalThis.backendaiclient.managerVersion,this.webui_version=globalThis.packageVersion,this.appDownloadUrl=globalThis.backendaiclient._config.appDownloadUrl,this._refreshConsoleUpdateInformation(),this._refreshInvitations())):this.resourceMonitor.removeAttribute("active")}_readAnnouncement(){this.activeConnected&&globalThis.backendaiclient.service.get_announcement().then((e=>{"message"in e&&(this.announcement=ie(e.message))})).catch((e=>{}))}_toInt(e){return Math.ceil(e)}_countObject(e){return Object.keys(e).length}_addComma(e){if(void 0===e)return"";return e.toString().replace(/\B(?=(\d{3})+(?!\d))/g,",")}_refreshInvitations(e=!1){this.activeConnected&&globalThis.backendaiclient.vfolder.invitations().then((t=>{this.invitations=t.invitations,this.active&&!e&&setTimeout((()=>{this._refreshInvitations()}),6e4)}))}async _acceptInvitation(e,t){if(!this.activeConnected)return;const s=e.target.closest("lablup-activity-panel");try{s.setAttribute("disabled","true"),s.querySelectorAll("mwc-button").forEach((e=>{e.setAttribute("disabled","true")})),await globalThis.backendaiclient.vfolder.accept_invitation(t.id),this.notification.text=n("summary.AcceptSharedVFolder")+`${t.vfolder_name}`,this.notification.show(),this._refreshInvitations()}catch(e){s.setAttribute("disabled","false"),s.querySelectorAll("mwc-button").forEach((e=>{e.setAttribute("disabled","false")})),this.notification.text=d.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}}async _deleteInvitation(e,t){if(!this.activeConnected)return;const s=e.target.closest("lablup-activity-panel");try{s.setAttribute("disabled","true"),s.querySelectorAll("mwc-button").forEach((e=>{e.setAttribute("disabled","true")})),await globalThis.backendaiclient.vfolder.delete_invitation(t.id),this.notification.text=n("summary.DeclineSharedVFolder")+`${t.vfolder_name}`,this.notification.show(),this._refreshInvitations()}catch(e){s.setAttribute("disabled","false"),s.querySelectorAll("mwc-button").forEach((e=>{e.setAttribute("disabled","false")})),this.notification.text=d.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}}_stripHTMLTags(e){return e.replace(/(<([^>]+)>)/gi,"")}_updateSelectedDownloadAppOS(e){this.downloadAppOS=e.target.value}_downloadApplication(e){let t="";const s=e.target.innerText.toLowerCase(),i=globalThis.packageVersion,r=this.appDownloadMap[this.downloadAppOS].os,n=this.appDownloadMap[this.downloadAppOS].extension;t=`${this.appDownloadUrl}/v${i}/backend.ai-desktop-${i}-${r}-${s}.${n}`,window.open(t,"_blank")}render(){return r`
      <link rel="stylesheet" href="/resources/fonts/font-awesome-all.min.css">
      <link rel="stylesheet" href="resources/custom.css">
      <div class="item" elevation="1" class="vertical layout center wrap flex">
        ${""!=this.announcement?r`
          <div class="notice-ticker horizontal layout wrap flex">
            <lablup-shields app="" color="red" description="Notice" ui="round"></lablup-shields>
            <span>${this._stripHTMLTags(this.announcement)}</span>
          </div>
        `:r``}
        <div class="horizontal wrap layout">
          <lablup-activity-panel title="${g("summary.StartMenu")}" elevation="1" height="500">
            <div slot="message">
              <img src="/resources/images/launcher-background.png" style="width:300px;margin-bottom:30px;"/>
              <div class="horizontal center-justified layout wrap">
                <backend-ai-session-launcher location="summary" id="session-launcher" ?active="${!0===this.active}"></backend-ai-session-launcher>
              </div>
              <div class="horizontal center-justified layout wrap">
                <a href="/data" class="vertical center center-justified layout start-menu-items">
                  <i class="fas fa-upload fa-2x"></i>
                  <span>${g("summary.UploadFiles")}</span>
                </a>
                ${this.is_admin?r`
                  <a href="/credential?action=add" class="vertical center center-justified layout start-menu-items" style="border-left:1px solid #ccc;">
                    <i class="fas fa-key fa-2x"></i>
                    <span>${g("summary.CreateANewKeypair")}</span>
                  </a>
                  <a href="/credential" class="vertical center center-justified layout start-menu-items" style="border-left:1px solid #ccc;">
                    <i class="fas fa-cogs fa-2x"></i>
                    <span>${g("summary.MaintainKeypairs")}</span>
                  </a>
                `:r``}
              </div>
            </div>
          </lablup-activity-panel>
          <lablup-activity-panel title="${g("summary.ResourceStatistics")}" elevation="1" narrow height="500">
            <div slot="message">
                <backend-ai-resource-monitor location="summary" id="resource-monitor" ?active="${!0===this.active}" direction="vertical"></backend-ai-resource-monitor>
            </div>
          </lablup-activity-panel>
          <backend-ai-resource-panel ?active="${!0===this.active}" height="500"></backend-ai-resource-panel>
          <div class="horizontal wrap layout">
            <lablup-activity-panel title="${g("summary.Announcement")}" elevation="1" horizontalsize="2x" height="245">
              <div slot="message" style="max-height:150px; overflow:scroll">
                ${""!==this.announcement?b(this.announcement):g("summary.NoAnnouncement")}
              </div>
            </lablup-activity-panel>
            <lablup-activity-panel title="${g("summary.Invitation")}" elevation="1" height="245" scrollableY>
              <div slot="message">
                ${this.invitations.length>0?this.invitations.map(((e,t)=>r`
                  <lablup-activity-panel class="inner-panel" noheader autowidth elevation="0" height="130">
                    <div slot="message">
                      <div class="wrap layout">
                      <h3 style="padding-top:10px;">From ${e.inviter}</h3>
                      <span class="invitation_folder_name">${g("summary.FolderName")}: ${e.vfolder_name}</span>
                      <div class="horizontal center layout">
                        ${g("summary.Permission")}:
                        ${[...e.perm].map((e=>r`
                            <lablup-shields app="" color="${["green","blue","red"][["r","w","d"].indexOf(e)]}"
                                description="${e.toUpperCase()}" ui="flat"></lablup-shields>
                        `))}
                      </div>
                      <div style="margin:15px auto;" class="horizontal layout end-justified">
                        <mwc-button
                            outlined
                            label="${g("summary.Decline")}"
                            @click="${t=>this._deleteInvitation(t,e)}"></mwc-button>
                        <mwc-button
                            unelevated
                            label="${g("summary.Accept")}"
                            @click="${t=>this._acceptInvitation(t,e)}"></mwc-button>
                        <span class="flex"></span>
                      </div>
                    </div>
                  </div>
                </lablup-activity-panel>`)):r`
                <p>${n("summary.NoInvitations")}</p>`}
              </div>
            </lablup-activity-panel>
          </div>
          ${globalThis.isElectron?r``:r`
            <lablup-activity-panel title="${g("summary.DownloadWebUIApp")}" elevation="1" narrow height="245">
              <div slot="message">
                <div id="download-app-os-select-box" class="horizontal layout start-justified">
                  <mwc-select @selected="${e=>this._updateSelectedDownloadAppOS(e)}">
                    ${Object.keys(this.appDownloadMap).map((e=>r`
                      <mwc-list-item
                          value="${e}"
                          ?selected="${e===this.downloadAppOS}">
                        ${e}
                      </mwc-list-item>
                    `))}
                  </mwc-select>
                </div>
                <div class="horizontal layout center center-justified">
                  ${this.downloadAppOS&&this.appDownloadMap[this.downloadAppOS].architecture.map((e=>r`
                    <mwc-button
                        raised
                        style="margin:10px;flex-basis:50%;"
                        @click="${e=>this._downloadApplication(e)}">
                        ${e}
                    </mwc-button>
                  `))}
                </div>
              </div>
            </lablup-activity-panel>
          `}
          </div>
          <div class="vertical layout">
            ${this.is_admin?r`
              <div class="horizontal layout wrap">
                <div class="vertical layout">
                  <div class="line"></div>
                  <div class="horizontal layout flex wrap center-justified">
                    <lablup-activity-panel class="footer-menu" noheader autowidth style="display: none;">
                      <div slot="message" class="vertical layout center start-justified flex upper-lower-space">
                        <h3 style="margin-top:0px;">${g("summary.CurrentVersion")}</h3>
                        ${this.is_superadmin?r`
                          <div class="layout vertical center center-justified flex" style="margin-bottom:5px;">
                            <lablup-shields app="Manager version" color="darkgreen" description="${this.manager_version}" ui="flat"></lablup-shields>
                            <div class="layout horizontal center flex" style="margin-top:4px;">
                              <lablup-shields app="Console version" color="${this.update_checker.updateNeeded?"red":"darkgreen"}" description="${this.webui_version}" ui="flat"></lablup-shields>
                              ${this.update_checker.updateNeeded?r`
                                <mwc-icon-button class="update-button" icon="new_releases"
                                  @click="${()=>{window.open(this.update_checker.updateURL,"_blank")}}"></mwc-icon-button>`:r`
                                    <mwc-icon class="update-icon">done</mwc-icon>
                                  `}
                            </div>
                          </div>
                        `:r``}
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
                    ${this.is_superadmin?r`
                    <lablup-activity-panel class="footer-menu" noheader autowidth>
                    <div slot="message" class="layout horizontal center center-justified flex upper-lower-space">
                      <a href="/agent">
                        <div class="layout horizontal center center-justified flex" style="font-size:14px;">
                          <i class="fas fa-box larger left-end-icon"></i>
                          <span>${g("summary.CheckResources")}</span>
                          <i class="fas fa-chevron-right right-end-icon"></i>
                        </div>
                      </a>
                    </div>
                  </lablup-activity-panel>
                  <lablup-activity-panel class="footer-menu" noheader autowidth>
                    <div slot="message" class="layout horizontal center center-justified flex upper-lower-space">
                        <a href="/settings">
                          <div class="layout horizontal center center-justified flex"  style="font-size:14px;">
                            <i class="fas fa-desktop larger left-end-icon"></i>
                            <span>${g("summary.ChangeSystemSetting")}</span>
                            <i class="fas fa-chevron-right right-end-icon"></i>
                          </div>
                        </a>
                    </div>
                  </lablup-activity-panel>`:r``}

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
          </div>`:r``}
        </div>
      </div>
    <backend-ai-release-check id="update-checker"></backend-ai-release-check>
  `}};e([t({type:String})],re.prototype,"condition",void 0),e([t({type:Number})],re.prototype,"sessions",void 0),e([t({type:Object})],re.prototype,"jobs",void 0),e([t({type:Number})],re.prototype,"agents",void 0),e([t({type:Boolean})],re.prototype,"is_admin",void 0),e([t({type:Boolean})],re.prototype,"is_superadmin",void 0),e([t({type:Object})],re.prototype,"resources",void 0),e([t({type:Object})],re.prototype,"update_checker",void 0),e([t({type:Boolean})],re.prototype,"authenticated",void 0),e([t({type:String})],re.prototype,"manager_version",void 0),e([t({type:String})],re.prototype,"webui_version",void 0),e([t({type:Number})],re.prototype,"cpu_total",void 0),e([t({type:Number})],re.prototype,"cpu_used",void 0),e([t({type:String})],re.prototype,"cpu_percent",void 0),e([t({type:String})],re.prototype,"cpu_total_percent",void 0),e([t({type:Number})],re.prototype,"cpu_total_usage_ratio",void 0),e([t({type:Number})],re.prototype,"cpu_current_usage_ratio",void 0),e([t({type:String})],re.prototype,"mem_total",void 0),e([t({type:String})],re.prototype,"mem_used",void 0),e([t({type:String})],re.prototype,"mem_allocated",void 0),e([t({type:Number})],re.prototype,"mem_total_usage_ratio",void 0),e([t({type:Number})],re.prototype,"mem_current_usage_ratio",void 0),e([t({type:String})],re.prototype,"mem_current_usage_percent",void 0),e([t({type:Number})],re.prototype,"cuda_gpu_total",void 0),e([t({type:Number})],re.prototype,"cuda_gpu_used",void 0),e([t({type:Number})],re.prototype,"cuda_fgpu_total",void 0),e([t({type:Number})],re.prototype,"cuda_fgpu_used",void 0),e([t({type:Number})],re.prototype,"rocm_gpu_total",void 0),e([t({type:Number})],re.prototype,"rocm_gpu_used",void 0),e([t({type:Number})],re.prototype,"tpu_total",void 0),e([t({type:Number})],re.prototype,"tpu_used",void 0),e([t({type:Number})],re.prototype,"ipu_total",void 0),e([t({type:Number})],re.prototype,"ipu_used",void 0),e([t({type:Number})],re.prototype,"atom_total",void 0),e([t({type:Number})],re.prototype,"atom_used",void 0),e([t({type:Object})],re.prototype,"notification",void 0),e([t({type:Object})],re.prototype,"resourcePolicy",void 0),e([t({type:String})],re.prototype,"announcement",void 0),e([t({type:Object})],re.prototype,"invitations",void 0),e([t({type:Object})],re.prototype,"appDownloadMap",void 0),e([t({type:String})],re.prototype,"appDownloadUrl",void 0),e([t({type:String})],re.prototype,"downloadAppOS",void 0),e([c("#resource-monitor")],re.prototype,"resourceMonitor",void 0),re=e([s("backend-ai-summary-view")],re);var ne=re;export{ne as default};
