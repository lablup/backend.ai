import{_ as e,e as t,a,s as i,I as s,b as l,x as o,f as r,i as n,y as c,t as d,c as p,B as h,d as u}from"./backend-ai-webui-efd2500f.js";import"./progress-spinner-c23af7f1.js";import"./tab-group-b2aae4b1.js";import"./mwc-tab-bar-553aafc2.js";import"./backend-ai-chart-f9dd0027.js";import"./radio-behavior-98d80f7f.js";import"./chart-js-74e01f0a.js";
/**
 @license
 Copyright (c) 2015-2020 Lablup Inc. All rights reserved.
 */let v=class extends i{constructor(){super(),this.num_sessions=0,this.used_time="0:00:00.00",this.cpu_used_time="0:00:00.00",this.gpu_used_time="0:00:00.00",this.disk_used=0,this.traffic_used=0}static get styles(){return[s,l,o,r,n`
        wl-card {
          padding: 20px;
        }

        .value {
          padding: 15px;
          font-size: 25px;
          font-weight: bold;
        }

        .desc {
          padding: 0px 15px 20px 15px;
        }
      `]}firstUpdated(){this.formatting()}formatting(){this.used_time=this.usedTimeFormatting(this.used_time),this.cpu_used_time=this.usedTimeFormatting(this.cpu_used_time),this.gpu_used_time=this.usedTimeFormatting(this.gpu_used_time),this.disk_used=Math.floor(this.disk_used/1073741824),this.traffic_used=Math.floor(this.traffic_used/1048576)}usedTimeFormatting(e){const t=parseInt(e.substring(0,e.indexOf(":")));let a=parseInt(e.substring(e.indexOf(":")+1,e.lastIndexOf(":")));return a=24*t+a,a+"h "+e.substring(e.lastIndexOf(":")+1,e.indexOf("."))+"m"}render(){return c`
      <wl-card>
        <wl-title level="3">${d("usagepanel.StatisticsForThisMonth")}</wl-title>
        <div class="horizontal layout">
          <div class="vertical center layout">
            <span class="value">${this.num_sessions}</span>
            <span class="desc">${d("usagepanel.NumSessions")}</span>
          </div>
          <div class="vertical center layout">
            <span class="value">${this.used_time}</span>
            <span class="desc">${d("usagepanel.UsedTime")}</span>
          </div>
          <div class="vertical center layout">
            <span class="value">${this.cpu_used_time}</span>
            <span class="desc">${d("usagepanel.CpuUsedTime")}</span>
          </div>
          <div class="vertical center layout">
            <span class="value">${this.gpu_used_time}</span>
            <span class="desc">${d("usagepanel.GpuUsedTime")}</span>
          </div>
          <div class="vertical center layout">
            <span class="value">${this.disk_used}GB</span>
            <span class="desc">${d("usagepanel.DiskUsed")}</span>
          </div>
          <div class="vertical center layout">
            <span class="value">${this.traffic_used}MB</span>
            <span class="desc">${d("usagepanel.TrafficUsed")}</span>
          </div>
        </div>
      </wl-card>
    `}};e([t({type:Number})],v.prototype,"num_sessions",void 0),e([t({type:String})],v.prototype,"used_time",void 0),e([t({type:String})],v.prototype,"cpu_used_time",void 0),e([t({type:String})],v.prototype,"gpu_used_time",void 0),e([t({type:Number})],v.prototype,"disk_used",void 0),e([t({type:Number})],v.prototype,"traffic_used",void 0),v=e([a("backend-ai-monthly-usage-panel")],v);
/**
 @license
 Copyright (c) 2015-2022 Lablup Inc. All rights reserved.
 */
let b=class extends h{constructor(){super(),this._map={num_sessions:"Sessions",cpu_allocated:"CPU",mem_allocated:"Memory",gpu_allocated:"GPU",io_read_bytes:"IO-Read",io_write_bytes:"IO-Write"},this.templates={"1D":{interval:1,length:96},"1W":{interval:1,length:672}},this.collection=Object(),this.period="1D",this.updating=!1,this.elapsedDays=0,this.data=[]}static get styles(){return[u,s,l,o,r,n`
        mwc-select {
          width: 100%;
          font-family: var(--general-font-family);
          --mdc-typography-subtitle1-font-family: var(--general-font-family);
          --mdc-theme-primary: var(--general-sidebar-color);
          --mdc-select-fill-color: transparent;
          --mdc-select-label-ink-color: rgba(0, 0, 0, 0.75);
          --mdc-select-focused-dropdown-icon-color: var(--general-sidebar-color);
          --mdc-select-disabled-dropdown-icon-color: var(--general-sidebar-color);
          --mdc-select-idle-line-color: rgba(0, 0, 0, 0.42);
          --mdc-select-hover-line-color: var(--general-sidebar-color);
          --mdc-select-outlined-idle-border-color: var(--general-sidebar-color);
          --mdc-select-outlined-hover-border-color: var(--general-sidebar-color);
          --mdc-theme-surface: white;
          --mdc-list-vertical-padding: 5px;
          --mdc-list-side-padding: 25px;
          --mdc-list-item__primary-text: {
            height: 20px;
          };
        }
      `]}attributeChangedCallback(e,t,a){var i;"active"===e&&null!==a?(this.active||this._menuChanged(!0),this.active=!0):(this.active=!1,this._menuChanged(!1),null===(i=this.shadowRoot)||void 0===i||i.querySelectorAll("backend-ai-chart").forEach((e=>{e.wipe()}))),super.attributeChangedCallback(e,t,a)}async _menuChanged(e){var t;await this.updateComplete,!1!==e?this.init():null===(t=this.shadowRoot)||void 0===t||t.querySelectorAll("backend-ai-chart").forEach((e=>{e.wipe()}))}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._getUserInfo(),this.init(),setTimeout((()=>{var e,t,a;this.periodSelec.selectedText=null!==(a=null===(t=null===(e=this.periodSelec.selected)||void 0===e?void 0:e.textContent)||void 0===t?void 0:t.trim())&&void 0!==a?a:""}),100)}),!0):(this._getUserInfo(),this.init(),setTimeout((()=>{var e,t;this.periodSelec.selectedText=null===(t=null===(e=this.periodSelec.selected)||void 0===e?void 0:e.textContent)||void 0===t?void 0:t.trim()}),100)))}_getUserInfo(){globalThis.backendaiclient.keypair.info(globalThis.backendaiclient._config.accessKey,["created_at"]).then((e=>{const t=e.keypair.created_at,a=new Date(t),i=new Date,s=Math.floor((i.getTime()-a.getTime())/1e3),l=Math.floor(s/86400);this.elapsedDays=l}))}init(){if(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready)document.addEventListener("backend-ai-connected",(()=>{this.updating||(this.updating=!0,this.readUserStat().then((e=>{var t;null===(t=this.shadowRoot)||void 0===t||t.querySelectorAll("backend-ai-chart").forEach((e=>{e.init()})),this.updating=!1})).catch((e=>{this.updating=!1})))}),!0);else{if(this.updating)return;this.updating=!0,this.readUserStat().then((e=>{var t;null===(t=this.shadowRoot)||void 0===t||t.querySelectorAll("backend-ai-chart").forEach((e=>{e.init()})),this.updating=!1})).catch((e=>{this.updating=!1}))}}readUserStat(){return globalThis.backendaiclient.resources.user_stats().then((e=>{const{period:t,templates:a}=this;this.data=e;const i={};return i[t]={},Object.keys(this._map).forEach((s=>{i[t][s]={data:[e.filter(((i,s)=>e.length-a[t].length<=s)).map((e=>({x:new Date(1e3*e.date),y:e[s].value})))],labels:[e.filter(((i,s)=>e.length-a[t].length<=s)).map((e=>new Date(1e3*e.date).toString()))],axisTitle:{x:"Date",y:this._map[s]},period:t,unit_hint:e[0][s].unit_hint}})),this.collection=i,this.updateComplete})).catch((e=>{console.log(e)}))}pulldownChange(e){this.period=e.target.value,console.log(this.period);const{data:t,period:a,collection:i,_map:s,templates:l}=this;a in i||(i[a]={},Object.keys(s).forEach((e=>{i[a][e]={data:[t.filter(((e,i)=>t.length-l[a].length<=i)).map((t=>({x:new Date(1e3*t.date),y:t[e].value})))],axisTitle:{x:"Date",y:s[e]},period:a,unit_hint:t[t.length-1][e].unit_hint}})))}render(){return c`
      <link rel="stylesheet" href="resources/custom.css">
      <div class="card" elevation="0">
        <!--<backend-ai-monthly-usage-panel></backend-ai-monthly-usage-panel>-->
        <h3 class="horizontal center layout">
          <mwc-select label="${d("statistics.SelectPeriod")}"
              id="period-selector" style="width:150px; border:1px solid #ccc;"
              @change="${e=>{this.pulldownChange(e)}}">
            <mwc-list-item value="1D" selected>${d("statistics.1Day")}</mwc-list-item>
            ${this.elapsedDays>7?c`
              <mwc-list-item value="1W">${d("statistics.1Week")}</mwc-list-item>
            `:c``}
          </mwc-select>
          <span class="flex"></span>
        </h3>
        ${Object.keys(this.collection).length>0?Object.keys(this._map).map(((e,t)=>c`
              <h3 class="horizontal center layout">
                <span style="color:#222222;">${this._map[e]}</span>
                <span class="flex"></span>
              </h3>
              <div style="width:100%;min-height:180px;">
                <backend-ai-chart
                  idx=${t}
                  .collection=${this.collection[this.period][e]}
                ></backend-ai-chart>
              </div>
            `)):c``}
      </div>
    `}};e([t({type:Object})],b.prototype,"_map",void 0),e([t({type:Object})],b.prototype,"templates",void 0),e([t({type:Object})],b.prototype,"collection",void 0),e([t({type:String})],b.prototype,"period",void 0),e([t({type:Boolean})],b.prototype,"updating",void 0),e([t({type:Number})],b.prototype,"elapsedDays",void 0),e([p("#period-selector")],b.prototype,"periodSelec",void 0),b=e([a("backend-ai-usage-list")],b);
/**
 @license
 Copyright (c) 2015-2022 Lablup Inc. All rights reserved.
 */
let m=class extends h{constructor(){super(...arguments),this._status="inactive"}static get styles(){return[u,s,l,o,r,n`
        wl-card h3.tab {
          padding-top: 0;
          padding-bottom: 0;
          padding-left: 0;
        }
        wl-tab-group {
          --tab-group-indicator-bg: var(--paper-cyan-500);
        }

        wl-tab {
          --tab-color: #666;
          --tab-color-hover: #222;
          --tab-color-hover-filled: #222;
          --tab-color-active: #222;
          --tab-color-active-hover: #222;
          --tab-color-active-filled: #ccc;
          --tab-bg-active: var(--paper-cyan-50);
          --tab-bg-filled: var(--paper-cyan-50);
          --tab-bg-active-hover: var(--paper-cyan-100);
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

        .tab-content {
          width: 100%;
        }
      `]}async _viewStateChanged(e){var t;await this.updateComplete,!1!==e?((null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#usage-list")).setAttribute("active","true"),this._status="active"):this._status="inactive"}_showTab(e){var t,a,i;const s=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(const e of Array.from(s))e.style.display="none";(null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#"+e.title+"-stat")).style.display="block",s.forEach((e=>{e.children[0].removeAttribute("active")})),(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector(`#${e.title}-list`)).setAttribute("active","true")}render(){return c`
        <lablup-activity-panel elevation="1" noheader narrow autowidth>
          <div slot="message">
            <h3 class="tab horizontal center layout">
              <mwc-tab-bar>
                <mwc-tab title="usage" label="${d("statistics.Usage")}"></mwc-tab>
              </mwc-tab-bar>
            </h3>
            <div class="horizontal wrap layout">
              <div id="usage-stat" class="tab-content">
                <backend-ai-usage-list id="usage-list"><wl-progress-spinner active></wl-progress-spinner></backend-ai-usage-list>
              </div>
            </div>
          </div>
        </lablup-activity-panel>
      `}};e([t({type:String})],m.prototype,"_status",void 0),m=e([a("backend-ai-statistics-view")],m);var g=m;export{g as default};
