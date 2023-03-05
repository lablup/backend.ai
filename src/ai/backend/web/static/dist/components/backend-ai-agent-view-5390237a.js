import{_ as e,e as t,c as i,a,B as s,d as o,I as r,b as l,i as n,h as d,A as c,y as u,t as p,g as h,r as g}from"./backend-ai-webui-efd2500f.js";import"./mwc-tab-bar-553aafc2.js";import"./lablup-activity-panel-b5a6a642.js";import"./vaadin-grid-af1e810c.js";import"./vaadin-grid-sort-column-46341c17.js";import"./lablup-progress-bar-71862d63.js";import"./backend-ai-list-status-9346ef68.js";import"./vaadin-item-styles-0bc384b2.js";import"./vaadin-item-42ec2f48.js";import"./label-06f60db1.js";import"./select-ea0f7a77.js";import"./switch-1637c31a.js";import"./textarea-69326eec.js";import"./textfield-8bcb1235.js";import"./mwc-switch-f419f24b.js";import"./input-behavior-1a3ba72d.js";
/**
 @license
 Copyright (c) 2015-2022 Lablup Inc. All rights reserved.
 */var v;let b=v=class extends s{constructor(){super(...arguments),this._enableAgentSchedulable=!1,this.condition="running",this.list_condition="loading",this.useHardwareMetadata=!1,this.agents=[],this.agentsObject=Object(),this.agentDetail=Object(),this.notification=Object(),this.enableAgentSchedulable=!1,this._boundEndpointRenderer=this.endpointRenderer.bind(this),this._boundRegionRenderer=this.regionRenderer.bind(this),this._boundContactDateRenderer=this.contactDateRenderer.bind(this),this._boundResourceRenderer=this.resourceRenderer.bind(this),this._boundUtilizationRenderer=this.utilizationRenderer.bind(this),this._boundDiskRenderer=this.diskRenderer.bind(this),this._boundStatusRenderer=this.statusRenderer.bind(this),this._boundControlRenderer=this.controlRenderer.bind(this),this._boundSchedulableRenderer=this.schedulableRenderer.bind(this),this.filter="",this.listCondition="loading"}static get styles(){return[o,r,l,n`
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
          --progress-bar-width: 85px;
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
          height: calc(100vh - 179px);
        }
    `]}firstUpdated(){this.notification=globalThis.lablupNotification}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._enableAgentSchedulable=globalThis.backendaiclient.supports("schedulable"),this._loadAgentList()}),!0):(this._enableAgentSchedulable=globalThis.backendaiclient.supports("schedulable"),this._loadAgentList()))}_loadAgentList(){var e;if(!0!==this.active)return;let t,i;switch(this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),this.condition){case"running":i="ALIVE",t=["id","status","version","addr","architecture","region","compute_plugins","first_contact","lost_at","status_changed","live_stat","cpu_cur_pct","mem_cur_bytes","available_slots","occupied_slots","scaling_group"];break;case"terminated":i="TERMINATED",t=["id","status","version","addr","architecture","region","compute_plugins","first_contact","lost_at","status_changed","cpu_cur_pct","mem_cur_bytes","available_slots","occupied_slots","scaling_group"];break;default:i="ALIVE",t=["id","status","version","addr","architecture","region","compute_plugins","first_contact","lost_at","status_changed","cpu_cur_pct","mem_cur_bytes","available_slots","occupied_slots","scaling_group"]}this.useHardwareMetadata&&globalThis.backendaiclient.supports("hardware-metadata")&&t.push("hardware_metadata"),globalThis.backendaiclient.supports("schedulable")&&t.push("schedulable");globalThis.backendaiclient.agent.list(i,t,1e4).then((e=>{var t;const i=e.agents;if(void 0!==i&&0!=i.length){let e;""!==this.filter&&(e=this.filter.split(":")),Object.keys(i).map(((t,a)=>{var s,o,r,l,n,d,c,u,p,h,g,v,b,m;const _=i[t];if(""===this.filter||e[0]in _&&_[e[0]]===e[1]){const e=JSON.parse(_.occupied_slots),a=JSON.parse(_.available_slots),y=JSON.parse(_.compute_plugins);if(["cpu","mem"].forEach((t=>{t in e==!1&&(e[t]="0")})),"live_stat"in _&&(i[t].live_stat=JSON.parse(_.live_stat)),i[t].cpu_slots=parseInt(a.cpu),i[t].used_cpu_slots=parseInt(e.cpu),null!==_.cpu_cur_pct?(i[t].current_cpu_percent=_.cpu_cur_pct,i[t].cpu_total_usage_ratio=i[t].used_cpu_slots/i[t].cpu_slots,i[t].cpu_current_usage_ratio=i[t].current_cpu_percent/i[t].cpu_slots/100,i[t].current_cpu_percent=i[t].current_cpu_percent.toFixed(2),i[t].total_cpu_percent=(100*i[t].cpu_total_usage_ratio).toFixed(2)):(i[t].current_cpu_percent=0,i[t].cpu_total_usage_ratio=0,i[t].cpu_current_usage_ratio=0,i[t].total_cpu_percent=(100*i[t].cpu_total_usage_ratio).toFixed(2)),null!==_.mem_cur_bytes?i[t].current_mem_bytes=_.mem_cur_bytes:i[t].current_mem_bytes=0,i[t].current_mem=globalThis.backendaiclient.utils.changeBinaryUnit(_.current_mem_bytes,"g"),i[t].mem_slots=parseInt(globalThis.backendaiclient.utils.changeBinaryUnit(a.mem,"g")),i[t].used_mem_slots=parseInt(globalThis.backendaiclient.utils.changeBinaryUnit(e.mem,"g")),i[t].mem_total_usage_ratio=i[t].used_mem_slots/i[t].mem_slots,i[t].mem_current_usage_ratio=i[t].current_mem/i[t].mem_slots,i[t].current_mem=i[t].current_mem.toFixed(2),i[t].total_mem_percent=(100*i[t].mem_total_usage_ratio).toFixed(2),"cuda.device"in a&&(i[t].cuda_gpu_slots=parseInt(a["cuda.device"]),i[t].used_cuda_gpu_slots="cuda.device"in e?parseInt(e["cuda.device"]):0,i[t].used_cuda_gpu_slots_ratio=i[t].used_cuda_gpu_slots/i[t].cuda_gpu_slots,i[t].total_cuda_gpu_percent=(100*i[t].used_cuda_gpu_slots_ratio).toFixed(2)),"cuda.shares"in a&&(i[t].cuda_fgpu_slots=parseInt(a["cuda.shares"]),i[t].used_cuda_fgpu_slots="cuda.shares"in e?parseInt(e["cuda.shares"]):0,i[t].used_cuda_fgpu_slots_ratio=i[t].used_cuda_fgpu_slots/i[t].cuda_fgpu_slots,i[t].total_cuda_fgpu_percent=(100*i[t].used_cuda_fgpu_slots_ratio).toFixed(2)),"rocm.device"in a&&(i[t].rocm_gpu_slots=parseInt(a["rocm.device"]),i[t].used_rocm_gpu_slots="rocm.device"in e?parseInt(e["rocm.device"]):0,i[t].used_rocm_gpu_slots_ratio=i[t].used_rocm_gpu_slots/i[t].rocm_gpu_slots,i[t].total_rocm_gpu_percent=(100*i[t].used_rocm_gpu_slots_ratio).toFixed(2)),"cuda"in y){const e=y.cuda;i[t].cuda_plugin=e}if(null===(o=null===(s=i[t].live_stat)||void 0===s?void 0:s.devices)||void 0===o?void 0:o.cpu_util){const e=[];Object.entries(i[t].live_stat.devices.cpu_util).forEach((([t,i])=>{const a=Object.assign({},i,{num:t});e.push(a)})),i[t].cpu_util_live=e}if(null===(l=null===(r=i[t].live_stat)||void 0===r?void 0:r.devices)||void 0===l?void 0:l.cuda_util){const e=[];let a=1;Object.entries(i[t].live_stat.devices.cuda_util).forEach((([t,i])=>{const s=Object.assign({},i,{num:t,idx:a});a+=1,e.push(s)})),i[t].cuda_util_live=e}if(null===(d=null===(n=i[t].live_stat)||void 0===n?void 0:n.devices)||void 0===d?void 0:d.cuda_mem){const e=[];let a=1;Object.entries(i[t].live_stat.devices.cuda_mem).forEach((([t,i])=>{const s=Object.assign({},i,{num:t,idx:a});a+=1,e.push(s)})),i[t].cuda_mem_live=e}if(null===(u=null===(c=i[t].live_stat)||void 0===c?void 0:c.devices)||void 0===u?void 0:u.rocm_util){const e=[];let a=1;Object.entries(i[t].live_stat.devices.rocm_util).forEach((([t,i])=>{const s=Object.assign({},i,{num:t,idx:a});a+=1,e.push(s)})),i[t].rocm_util_live=e}if(null===(h=null===(p=i[t].live_stat)||void 0===p?void 0:p.devices)||void 0===h?void 0:h.rocm_mem){const e=[];let a=1;Object.entries(i[t].live_stat.devices.rocm_mem).forEach((([t,i])=>{const s=Object.assign({},i,{num:t,idx:a});a+=1,e.push(s)})),i[t].rocm_mem_live=e}if(null===(v=null===(g=i[t].live_stat)||void 0===g?void 0:g.devices)||void 0===v?void 0:v.tpu_util){const e=[];let a=1;Object.entries(i[t].live_stat.devices.tpu_util).forEach((([t,i])=>{const s=Object.assign({},i,{num:t,idx:a});a+=1,e.push(s)})),i[t].tpu_util_live=e}if(null===(m=null===(b=i[t].live_stat)||void 0===b?void 0:b.devices)||void 0===m?void 0:m.tpu_mem){const e=[];let a=1;Object.entries(i[t].live_stat.devices.tpu_mem).forEach((([t,i])=>{const s=Object.assign({},i,{num:t,idx:a});a+=1,e.push(s)})),i[t].tpu_mem_live=e}"hardware_metadata"in _&&(i[t].hardware_metadata=JSON.parse(_.hardware_metadata)),"schedulable"in _&&(i[t].schedulable=_.schedulable),this.agentsObject[i[t].id]=i[t]}}))}this.agents=i,this._agentGrid.recalculateColumnWidths(),0==this.agents.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide(),this.agentDetailDialog.open&&(this.agentDetail=this.agentsObject[this.agentDetail.id],this.agentDetailDialog.updateComplete),!0===this.active&&setTimeout((()=>{this._loadAgentList()}),15e3)})).catch((e=>{var t;null===(t=this._listStatus)||void 0===t||t.hide(),e&&e.message&&(this.notification.text=d.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_isRunning(){return"running"===this.condition}_byteToMB(e){return Math.floor(e/1e6)}_MBtoGB(e){return Math.floor(e/1024)}_elapsed(e,t){const i=new Date(e);let a;a="running"===this.condition?new Date:new Date(t);const s=Math.floor((a.getTime()-i.getTime())/1e3);return"running"===this.condition?"Running "+s+"sec.":"Reserved for "+s+"sec."}_humanReadableDate(e){return new Date(e).toLocaleString()}_indexFrom1(e){return e+1}_heartbeatStatus(e){return e}_heartbeatColor(e){switch(e){case"ALIVE":return"green";case"TERMINATED":return"red";default:return"blue"}}_indexRenderer(e,t,i){const a=i.index+1;c(u`
        <div>${a}</div>
      `,e)}endpointRenderer(e,t,i){c(u`
        <div style="white-space:pre-wrap;">${i.item.id}</div>
        <div class="indicator monospace" style="white-space:pre-wrap;">${i.item.addr}</div>
      `,e)}regionRenderer(e,t,i){let a,s,o,r;const l=i.item.region.split("/");switch(l.length>1?(a=l[0],s=l[1]):(a=l[0],s=""),a){case"aws":case"amazon":o="orange",r="aws";break;case"azure":o="blue",r="azure";break;case"gcp":case"google":o="lightblue",r="gcp";break;case"nbp":case"naver":o="green",r="nbp";break;case"openstack":o="red",r="openstack";break;case"dgx":o="green",r="local";break;default:o="yellow",r="local"}c(u`
        <div class="horizontal start-justified center layout wrap">
          <img src="/resources/icons/${r}.png" style="width:32px;height:32px;"/>
          <lablup-shields app="${s}" color="${o}"
                          description="${a}" ui="round"></lablup-shields>
        </div>
      `,e)}_elapsed2(e,t){return globalThis.backendaiclient.utils.elapsedTime(e,t)}contactDateRenderer(e,t,i){let a;"TERMINATED"===i.item.status&&"lost_at"in i.item?(a=this._elapsed2(i.item.lost_at,Date.now()),c(u`
          <div class="layout vertical">
            <span>${this._humanReadableDate(i.item.first_contact)}</span>
            <lablup-shields app="${p("agent.Terminated")}" color="yellow"
                            description="${a}" ui="round"></lablup-shields>
          </div>`,e)):(a=this._elapsed2(i.item.first_contact,Date.now()),c(u`
          <div class="layout vertical">
            <span>${this._humanReadableDate(i.item.first_contact)}</span>
            <lablup-shields app="${p("agent.Running")}" color="darkgreen"
                            description="${a}" ui="round"></lablup-shields>
          </div>`,e))}resourceRenderer(e,t,i){c(u`
        <div class="layout flex">
          ${i.item.cpu_slots?u`
            <div class="layout horizontal center-justified flex progress-bar-section">
              <div class="layout horizontal start resource-indicator">
                <mwc-icon class="fg green">developer_board</mwc-icon>
                <span class="monospace" style="padding-left:5px;">${i.item.used_cpu_slots}/${i.item.cpu_slots}</span>
                <span class="indicator">${p("general.cores")}</span>
              </div>
              <span class="flex"></span>
              <lablup-progress-bar id="cpu-usage-bar" progress="${i.item.cpu_total_usage_ratio}"
                                   description="${i.item.total_cpu_percent}%"></lablup-progress-bar>
            </div>`:u``}
          ${i.item.mem_slots?u`
            <div class="layout horizontal center-justified flex progress-bar-section">
              <div class="layout horizontal start resource-indicator">
                <mwc-icon class="fg green">memory</mwc-icon>
                <span class="monospace" style="padding-left:5px;">${i.item.used_mem_slots}/${i.item.mem_slots}</span>
                <span class="indicator">GiB</span>
              </div>
              <span class="flex"></span>
              <lablup-progress-bar id="mem-usage-bar" progress="${i.item.mem_total_usage_ratio}"
                                   description="${i.item.total_mem_percent}%"></lablup-progress-bar>
            </div>`:u``}
          ${i.item.cuda_gpu_slots?u`
            <div class="layout horizontal center-justified flex progress-bar-section">
              <div class="layout horizontal start resource-indicator">
                <img class="indicator-icon fg green" src="/resources/icons/file_type_cuda.svg"/>
                <span class="monospace" style="padding-left:5px;">${i.item.used_cuda_gpu_slots}/${i.item.cuda_gpu_slots}</span>
                <span class="indicator">GPU</span>
              </div>
              <span class="flex"></span>
              <lablup-progress-bar id="gpu-bar" progress="${i.item.used_cuda_gpu_slots_ratio}"
                                   description="${i.item.total_cuda_gpu_percent}%"></lablup-progress-bar>
            </div>
          `:u``}
          ${i.item.cuda_fgpu_slots?u`
            <div class="layout horizontal center-justified flex progress-bar-section">
              <div class="layout horizontal start resource-indicator">
                <img class="indicator-icon fg green" src="/resources/icons/file_type_cuda.svg"/>
                <span class="monospace" style="padding-left:5px;">${i.item.used_cuda_fgpu_slots}/${i.item.cuda_fgpu_slots}</span>
                <span class="indicator">fGPU</span>
              </div>
              <span class="flex"></span>
              <lablup-progress-bar id="vgpu-bar" progress="${i.item.used_cuda_fgpu_slots_ratio}"
                                   description="${i.item.used_cuda_fgpu_slots}"></lablup-progress-bar>
            </div>
          `:u``}
          ${i.item.rocm_gpu_slots?u`
            <div class="layout horizontal center-justified flex progress-bar-section">
              <div class="layout horizontal start resource-indicator">
                <img class="indicator-icon fg green" src="/resources/icons/ROCm.png"/>
                <span class="monospace" style="padding-left:5px;">${i.item.used_rocm_gpu_slots}/${i.item.rocm_gpu_slots}</span>
                <span class="indicator">ROCm</span>
              </div>
              <span class="flex"></span>
              <lablup-progress-bar id="rocm-gpu-bar" progress="${i.item.used_rocm_gpu_slots_ratio}"
                                   description="${i.item.used_rocm_gpu_slots}"></lablup-progress-bar>
            </div>
          `:u``}
          ${i.item.tpu_slots?u`
            <div class="layout horizontal center-justified flex progress-bar-section">
              <div class="layout horizontal start resource-indicator">
                <img class="indicator-icon fg green" src="/resources/icons/tpu.svg"/>
                <span class="monospace" style="padding-left:5px;">${i.item.used_tpu_slots}/${i.item.tpu_slots}</span>
                <span class="indicator">TPU</span>
              </div>
              <span class="flex"></span>
              <lablup-progress-bar id="tpu-bar" progress="${i.item.used_tpu_slots_ratio}"
                                   description="${i.item.used_tpu_slots}"></lablup-progress-bar>
            </div>
          `:u``}
        </div>`,e)}schedulableRenderer(e,t,i){var a;c(u`
        <div class="layout horizontal center center-justified wrap">
          ${(null===(a=i.item)||void 0===a?void 0:a.schedulable)?u`
            <mwc-icon class="fg green schedulable">check_circle</mwc-icon>
          `:u`
            <mwc-icon class="fg red schedulable">block</mwc-icon>
          `}
        </div>`,e)}utilizationRenderer(e,t,i){var a,s,o,r,l,n,d,h;if("ALIVE"===i.item.status){let t={cpu_util:{capacity:0,current:0,ratio:0},mem_util:{capacity:0,current:0,ratio:0}};if(i.item.live_stat.node.cuda_util&&(t=Object.assign(t,{cuda_util:{capacity:0,current:0,ratio:0}}),t.cuda_util.capacity=parseFloat(null!==(a=i.item.live_stat.node.cuda_util.capacity)&&void 0!==a?a:0),t.cuda_util.current=parseFloat(i.item.live_stat.node.cuda_util.current),t.cuda_util.ratio=t.cuda_util.current/100||0),i.item.live_stat.node.cuda_mem){let e;t=Object.assign(t,{cuda_mem:{capacity:0,current:0,ratio:0}}),t.cuda_mem.capacity=parseFloat(null!==(s=i.item.live_stat.node.cuda_mem.capacity)&&void 0!==s?s:0),t.cuda_mem.current=parseFloat(i.item.live_stat.node.cuda_mem.current),e=t.cuda_mem.capacity&&0!==t.cuda_mem.capacity?t.cuda_mem.capacity:100,t.cuda_mem.ratio=t.cuda_mem.current/e||0}if(i.item.live_stat&&i.item.live_stat.node&&i.item.live_stat.devices){const e=Object.keys(i.item.live_stat.devices.cpu_util).length;t.cpu_util.capacity=parseFloat(i.item.live_stat.node.cpu_util.capacity),t.cpu_util.current=parseFloat(i.item.live_stat.node.cpu_util.current),t.cpu_util.ratio=t.cpu_util.current/t.cpu_util.capacity/e||0,t.mem_util.capacity=parseInt(i.item.live_stat.node.mem.capacity),t.mem_util.current=parseInt(i.item.live_stat.node.mem.current),t.mem_util.ratio=t.mem_util.current/t.mem_util.capacity||0}c(u`
            <div>
              <div class="layout horizontal justified flex progress-bar-section">
                <span style="margin-right:5px;">CPU</span>
                <lablup-progress-bar class="utilization" progress="${t.cpu_util.ratio}" description="${(100*(null===(o=t.cpu_util)||void 0===o?void 0:o.ratio)).toFixed(1)} %"></lablup-progress-bar>
              </div>
              <div class="layout horizontal justified flex progress-bar-section">
                <span style="margin-right:5px;">MEM</span>
                <lablup-progress-bar class="utilization" progress="${t.mem_util.ratio}" description="${v.bytesToGiB(t.mem_util.current)}/${v.bytesToGiB(t.mem_util.capacity)} GiB"></lablup-progress-bar>
              </div>
              ${t.cuda_util?u`
                <div class="layout horizontal justified flex progress-bar-section">
                  <span style="margin-right:5px;">GPU(util)</span>
                  <lablup-progress-bar class="utilization" progress="${null===(r=t.cuda_util)||void 0===r?void 0:r.ratio}" description="${(100*(null===(l=t.cuda_util)||void 0===l?void 0:l.ratio)).toFixed(1)} %"></lablup-progress-bar>
                </div>
                <div class="layout horizontal justified flex progress-bar-section">
                  <span style="margin-right:5px;">GPU(mem)</span>
                  <lablup-progress-bar class="utilization" progress="${(null===(n=t.cuda_mem)||void 0===n?void 0:n.ratio)||0}" description="${v.bytesToGiB(null===(d=t.cuda_mem)||void 0===d?void 0:d.current)}/${v.bytesToGiB(null===(h=t.cuda_mem)||void 0===h?void 0:h.capacity)} GiB"></lablup-progress-bar>
                </div>
              `:u``}
            </div>
        `,e)}else c(u`${p("agent.NoAvailableLiveStat")}`,e)}diskRenderer(e,t,i){let a;i.item.live_stat&&i.item.live_stat.node&&i.item.live_stat.node.disk&&(a=parseFloat(i.item.live_stat.node.disk.pct||0).toFixed(1)),c(u`
        ${a?u`
          <div class="indicator layout vertical center">
            ${a>80?u`
              <lablup-progress-bar class="utilization" progress="${a/100||0}"
                                   description="${a} %"
                                   style="margin-left:0;--progress-bar-background:var(--paper-red-500)"></lablup-progress-bar>
            `:u`
              <lablup-progress-bar class="utilization" progress="${a/100||0}"
                                   description="${a} %"
                                   style="margin-left:0;"></lablup-progress-bar>
            `}
            <div style="margin-top:10px;">${globalThis.backendaiutils._humanReadableFileSize(i.item.live_stat.node.disk.current)} / ${globalThis.backendaiutils._humanReadableFileSize(i.item.live_stat.node.disk.capacity)}</div>
          </div>
        `:u`
          <span>-</span>
        `}
      `,e)}statusRenderer(e,t,i){var a;c(u`
        <div class="layout vertical start justified wrap">
          <lablup-shields app="Agent" color="${this._heartbeatColor(i.item.status)}"
                          description="${i.item.version}" ui="round"></lablup-shields>
          ${i.item.cuda_plugin?u`
            <lablup-shields app="CUDA Plugin" color="blue"
                            description="${i.item.cuda_plugin.version}" ui="round"></lablup-shields>
            ${i.item.cuda_fgpu_slots?u`
              <lablup-shields app="" color="blue"
                              description="Fractional GPU™" ui="round"></lablup-shields>
            `:u``}
            ${(null===(a=i.item.cuda_plugin)||void 0===a?void 0:a.cuda_version)?u`
                <lablup-shields app="CUDA" color="green"
                                description="${i.item.cuda_plugin.cuda_version}" ui="round"></lablup-shields>`:u`
                <lablup-shields app="CUDA Disabled" color="green"
                                description="" ui="flat"></lablup-shields>`}`:u``}
        </div>`,e)}showAgentDetailDialog(e){this.agentDetail=this.agentsObject[e],this.agentDetailDialog.show()}controlRenderer(e,t,i){c(u`
        <div id="controls" class="layout horizontal flex center" agent-id="${i.item.addr}">
          <mwc-icon-button class="fg green controls-running" icon="assignment"
                           @click="${e=>this.showAgentDetailDialog(i.item.id)}"></mwc-icon-button>
          ${this._isRunning()?u`
            ${this._enableAgentSchedulable?u`
              <mwc-icon-button class="fg blue controls-running" icon="settings"
                               @click="${e=>this._showConfigDialog(i.item.id)}"></mwc-icon-button>
            `:u``}
            <mwc-icon-button class="temporarily-hide fg green controls-running" icon="refresh"
                             @click="${()=>this._loadAgentList()}"></mwc-icon-button>
            <mwc-icon-button class="temporarily-hide fg controls-running" disabled
                             icon="build"></mwc-icon-button>
            <mwc-icon-button class="temporarily-hide fg controls-running" disabled
                             icon="alarm"></mwc-icon-button>
            <mwc-icon-button class="temporarily-hide fg controls-running" disabled
                             icon="pause"></mwc-icon-button>
            <mwc-icon-button class="temporarily-hide fg controls-running" disabled
                             icon="delete"></mwc-icon-button>
          `:u``}
        </div>`,e)}_showConfigDialog(e){var t,i;this.agentDetail=this.agentsObject[e],this.schedulableToggle.selected=null!==(i=null===(t=this.agentDetail)||void 0===t?void 0:t.schedulable)&&void 0!==i&&i,this.agentSettingDialog.show()}_bytesToMiB(e){return Number(e/1048576).toFixed(1)}static bytesToGiB(e,t=2){return e?(e/2**30).toFixed(t):e}_modifyAgentSetting(){var e;const t=this.schedulableToggle.selected;(null===(e=this.agentDetail)||void 0===e?void 0:e.schedulable)!==t?globalThis.backendaiclient.agent.update(this.agentDetail.id,{schedulable:t}).then((e=>{this.notification.text=h("agent.AgentSettingUpdated"),this.notification.show(),this.agentSettingDialog.hide(),this._loadAgentList()})).catch((e=>{this.notification.text=d.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)})):(this.notification.text=h("agent.NoChanges"),this.notification.show(),this.agentSettingDialog.hide())}_renderAgentDetailDialog(){var e,t,i,a,s,o;return u`
      <backend-ai-dialog id="agent-detail" fixed backdrop blockscrolling persistent scrollable>
        <span slot="title">${p("agent.DetailedInformation")}</span>
        <div slot="content">
          <div class="horizontal start around-justified layout flex">
            ${(null===(e=this.agentDetail)||void 0===e?void 0:e.cpu_util_live)?u`
              <div class="vertical layout start-justified flex">
                <h3>CPU</h3>
                ${this.agentDetail.cpu_util_live.map((e=>u`
                  <div class="horizontal start-justified center layout" style="padding:0 5px;">
                    <div class="agent-detail-title">CPU${e.num}</div>
                    <lablup-progress-bar
                        class="cpu"
                        progress="${e.pct/100}"
                    ></lablup-progress-bar>
                  </div>`))}
              </div>`:u``}
              <div class="vertical layout start-justified flex">
                <h3>Memory</h3>
                <div>
                  <lablup-progress-bar
                      class="mem"
                      progress="${this.agentDetail.mem_current_usage_ratio}"
                      description="${this.agentDetail.current_mem}GiB/${this.agentDetail.mem_slots}GiB"
                  ></lablup-progress-bar>
                </div>
                <h3>Network</h3>
                ${(null===(i=null===(t=this.agentDetail)||void 0===t?void 0:t.live_stat)||void 0===i?void 0:i.node)?u`
                  <div class="horizontal layout justified" style="width:100px;">
                    <span>TX: </span>
                    <span>${this._bytesToMiB(this.agentDetail.live_stat.node.net_tx.current)}MiB</span>
                  </div>
                  <div class="horizontal layout justified flex" style="width:100px;">
                    <span>RX: </span>
                    <span>${this._bytesToMiB(this.agentDetail.live_stat.node.net_rx.current)}MiB</span>
                  </div>
                `:u`
                  <p>${p("agent.NoNetworkSignal")}</p>
                `}
              </div>
              ${(null===(a=this.agentDetail)||void 0===a?void 0:a.cuda_util_live)?u`
                <div class="vertical layout start-justified flex">
                  <h3>CUDA Devices</h3>
                  <h4>Utilization</h4>
                  ${this.agentDetail.cuda_util_live.map((e=>u`
                    <div class="horizontal start-justified center layout">
                      <div class="agent-detail-title">CUDA${e.idx}</div>
                      <div class="horizontal start-justified center layout">
                        <lablup-progress-bar
                            class="cuda"
                            progress="${e.pct/100}"
                        ></lablup-progress-bar>
                      </div>
                    </div>`))}
                  <h4>Memory</h4>
                  ${this.agentDetail.cuda_mem_live.map((e=>u`
                    <div class="horizontal start-justified center layout">
                      <div class="agent-detail-title">CUDA${e.idx}</div>
                      <div class="horizontal start-justified center layout">
                        <lablup-progress-bar
                            class="cuda"
                            progress="${e.pct/100}"
                        ></lablup-progress-bar>
                      </div>
                    </div>`))}
                </div>`:u``}
              ${(null===(s=this.agentDetail)||void 0===s?void 0:s.rocm_util_live)?u`
                <div class="vertical layout start-justified flex">
                  <h3>ROCm Devices</h3>
                  <h4>Utilization</h4>
                  ${this.agentDetail.rocm_util_live.map((e=>u`
                    <div class="horizontal start-justified center layout">
                      <div class="agent-detail-title">ROCm${e.num}</div>
                      <div class="horizontal start-justified center layout">
                        <lablup-progress-bar
                            class="cuda"
                            progress="${e.pct/100}"
                        ></lablup-progress-bar>
                      </div>
                    </div>`))}
                  <h4>Memory</h4>
                  ${this.agentDetail.rocm_mem_live.map((e=>u`
                    <div class="horizontal start-justified center layout">
                      <div class="agent-detail-title">ROCm${e.num}</div>
                      <div class="horizontal start-justified center layout">
                        <lablup-progress-bar
                            class="cuda"
                            progress="${e.pct/100}"
                        ></lablup-progress-bar>
                      </div>
                    </div>`))}
                </div>`:u``}
              ${(null===(o=this.agentDetail)||void 0===o?void 0:o.tpu_util_live)?u`
                <div class="vertical layout start-justified flex">
                  <h3>TPU Devices</h3>
                  <h4>Utilization</h4>
                  ${this.agentDetail.tpu_util_live.map((e=>u`
                    <div class="horizontal start-justified center layout">
                      <div class="agent-detail-title">TPU${e.num}</div>
                      <div class="horizontal start-justified center layout">
                        <lablup-progress-bar
                            class="cuda"
                            progress="${e.pct/100}"
                        ></lablup-progress-bar>
                      </div>
                    </div>`))}
                  <h4>Memory</h4>
                  ${this.agentDetail.tpu_mem_live.map((e=>u`
                    <div class="horizontal start-justified center layout">
                      <div class="agent-detail-title">TPU${e.num}</div>
                      <div class="horizontal start-justified center layout">
                        <lablup-progress-bar
                            class="cuda"
                            progress="${e.pct/100}"
                        ></lablup-progress-bar>
                      </div>
                    </div>`))}
                </div>`:u``}
          </div>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            icon="check"
            label="${p("button.Close")}"
            @click="${e=>this._hideDialog(e)}"></mwc-button>
        </div>
      </backend-ai-dialog>
    `}_renderAgentSettingDialog(){var e;return u`
      <backend-ai-dialog id="agent-setting" fixed backdrop blockscrolling persistent scrollable>
        <span slot="title">${p("agent.AgentSetting")}</span>
        <div slot="content" class="horizontal layout justified center">
          <span>${p("agent.Schedulable")}</span>
          <mwc-switch id="schedulable-switch" ?selected="${null===(e=this.agentDetail)||void 0===e?void 0:e.schedulable}"></mwc-switch>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
        <mwc-button
          unelevated
          icon="check"
          label="${p("button.Update")}"
          @click="${()=>this._modifyAgentSetting()}"></mwc-button>
        </div>
      </backend-ai-dialog>
    `}render(){return u`
      <div class="list-wrapper">
        <vaadin-grid class="${this.condition}" theme="row-stripes column-borders compact" aria-label="Job list"
                    .items="${this.agents}" multi-sort multi-sort-priority="append">
          <vaadin-grid-column width="30px" flex-grow="0" header="#" text-align="center"
                              .renderer="${this._indexRenderer}"></vaadin-grid-column>
          <vaadin-grid-sort-column resizable width="100px" path="id" header="${p("agent.Endpoint")}"
                              .renderer="${this._boundEndpointRenderer}">
          </vaadin-grid-sort-column>
          <vaadin-grid-column auto-width resizable header="${p("agent.Region")}"
                              .renderer="${this._boundRegionRenderer}">
          </vaadin-grid-column>
          <vaadin-grid-sort-column auto-width flex-grow="0" resizable path="architecture" header="${p("agent.Architecture")}">
          </vaadin-grid-sort-column>
          <vaadin-grid-sort-column resizable path="first_contact" auto-width flex-grow="0" header="${p("agent.Starts")}" .renderer="${this._boundContactDateRenderer}">
          </vaadin-grid-sort-column>
          <vaadin-grid-column resizable width="160px" header="${p("agent.Allocation")}"
                              .renderer="${this._boundResourceRenderer}">
          </vaadin-grid-column>
          <vaadin-grid-column resizable width="185px" header="${p("agent.Utilization")}"
                              .renderer="${this._boundUtilizationRenderer}">
          </vaadin-grid-column>
          <vaadin-grid-column resizable header="${p("agent.DiskPerc")}"
                              .renderer="${this._boundDiskRenderer}"></vaadin-grid-column>
          <vaadin-grid-sort-column resizable auto-width flex-grow="0" path="scaling_group"
                              header="${p("general.ResourceGroup")}"></vaadin-grid-sort-column>
          <vaadin-grid-column width="160px" flex-grow="0" resizable header="${p("agent.Status")}"
                              .renderer="${this._boundStatusRenderer}"></vaadin-grid-column>
          ${this._enableAgentSchedulable?u`
          <vaadin-grid-sort-column auto-width flex-grow="0" resizable path="schedulable" header="${p("agent.Schedulable")}"
                              .renderer="${this._boundSchedulableRenderer}"></vaadin-grid-sort-column>
          `:u``}
          <vaadin-grid-column resizable header="${p("general.Control")}"
                              .renderer="${this._boundControlRenderer}"></vaadin-grid-column>
        </vaadin-grid>
        <backend-ai-list-status id="list-status" statusCondition="${this.listCondition}" message="${h("agent.NoAgentToDisplay")}"></backend-ai-list-status>
      </div>
      ${this._renderAgentDetailDialog()}
      ${this._renderAgentSettingDialog()}
    `}};e([t({type:String})],b.prototype,"condition",void 0),e([t({type:String})],b.prototype,"list_condition",void 0),e([t({type:Boolean})],b.prototype,"useHardwareMetadata",void 0),e([t({type:Array})],b.prototype,"agents",void 0),e([t({type:Object})],b.prototype,"agentsObject",void 0),e([t({type:Object})],b.prototype,"agentDetail",void 0),e([t({type:Object})],b.prototype,"notification",void 0),e([t({type:Boolean})],b.prototype,"enableAgentSchedulable",void 0),e([t({type:Object})],b.prototype,"_boundEndpointRenderer",void 0),e([t({type:Object})],b.prototype,"_boundRegionRenderer",void 0),e([t({type:Object})],b.prototype,"_boundContactDateRenderer",void 0),e([t({type:Object})],b.prototype,"_boundResourceRenderer",void 0),e([t({type:Object})],b.prototype,"_boundUtilizationRenderer",void 0),e([t({type:Object})],b.prototype,"_boundDiskRenderer",void 0),e([t({type:Object})],b.prototype,"_boundStatusRenderer",void 0),e([t({type:Object})],b.prototype,"_boundControlRenderer",void 0),e([t({type:Object})],b.prototype,"_boundSchedulableRenderer",void 0),e([t({type:String})],b.prototype,"filter",void 0),e([i("#agent-detail")],b.prototype,"agentDetailDialog",void 0),e([i("#agent-setting")],b.prototype,"agentSettingDialog",void 0),e([i("#schedulable-switch")],b.prototype,"schedulableToggle",void 0),e([t({type:String})],b.prototype,"listCondition",void 0),e([i("vaadin-grid")],b.prototype,"_agentGrid",void 0),e([i("#list-status")],b.prototype,"_listStatus",void 0),b=v=e([a("backend-ai-agent-list")],b);let m=class extends s{constructor(){super(),this.condition="running",this.listCondition="loading",this.storagesObject=Object(),this.storageProxyDetail=Object(),this.notification=Object(),this._boundEndpointRenderer=this.endpointRenderer.bind(this),this._boundTypeRenderer=this.typeRenderer.bind(this),this._boundResourceRenderer=this.resourceRenderer.bind(this),this._boundCapabilitiesRenderer=this.capabilitiesRenderer.bind(this),this._boundControlRenderer=this.controlRenderer.bind(this),this.filter="",this.storages=[]}static get styles(){return[o,r,l,n`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 179px);
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
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._loadStorageProxyList()}),!0):this._loadStorageProxyList())}_loadStorageProxyList(){var e;!0===this.active&&(this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),globalThis.backendaiclient.storageproxy.list(["id","backend","capabilities","path","fsprefix","performance_metric","usage"]).then((e=>{var t;const i=e.storage_volume_list.items,a=[];void 0!==i&&0!=i.length&&Object.keys(i).map(((e,t)=>{const s=i[e];if(""!==this.filter){const e=this.filter.split(":");e[0]in s&&s[e[0]]===e[1]&&a.push(s)}else a.push(s)})),this.storages=a,0==this.storages.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide();const s=new CustomEvent("backend-ai-storage-proxy-updated",{});this.dispatchEvent(s),!0===this.active&&setTimeout((()=>{this._loadStorageProxyList()}),15e3)})).catch((e=>{var t;null===(t=this._listStatus)||void 0===t||t.hide(),e&&e.message&&(this.notification.text=d.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))})))}_byteToMB(e){return Math.floor(e/1e6)}_MBtoGB(e){return Math.floor(e/1024)}_humanReadableDate(e){return new Date(e).toLocaleString()}_indexFrom1(e){return e+1}_heartbeatStatus(e){return e}_indexRenderer(e,t,i){const a=i.index+1;c(u`
        <div>${a}</div>
      `,e)}endpointRenderer(e,t,i){c(u`
        <div>${i.item.id}</div>
        <div class="indicator monospace">${i.item.path}</div>
      `,e)}typeRenderer(e,t,i){let a,s;switch(i.item.backend){case"xfs":a="blue",s="local";break;case"ceph":case"cephfs":a="lightblue",s="ceph";break;case"vfs":case"nfs":case"dgx":case"spectrumscale":a="green",s="local";break;case"purestorage":a="red",s="purestorage";break;case"weka":a="purple",s="local";break;default:a="yellow",s="local"}c(u`
        <div class="horizontal start-justified center layout">
          <img src="/resources/icons/${s}.png" style="width:32px;height:32px;"/>
          <lablup-shields app="Backend" color="${a}"
                          description="${i.item.backend}" ui="round"></lablup-shields>
        </div>
      `,e)}_elapsed2(e,t){return globalThis.backendaiclient.utils.elapsedTime(e,t)}resourceRenderer(e,t,i){const a=JSON.parse(i.item.usage),s=a.capacity_bytes>0?a.used_bytes/a.capacity_bytes:0,o=(100*s).toFixed(3);c(u`
        <div class="layout flex">
          <div class="layout horizontal center flex">
            <div class="layout horizontal start resource-indicator">
              <mwc-icon class="fg green">data_usage</mwc-icon>
              <span class="indicator" style="padding-left:5px;">${p("session.Usage")}</span>
            </div>
            <span class="flex"></span>
            <div class="layout vertical center">
              <lablup-progress-bar id="volume-usage-bar" progress="${s}"
                                   buffer="${100}"
                                   description="${o}%"></lablup-progress-bar>
              <div class="indicator" style="margin-top:3px;">${globalThis.backendaiutils._humanReadableFileSize(a.used_bytes)} / ${globalThis.backendaiutils._humanReadableFileSize(a.capacity_bytes)}</div>
            </div>
          </div>
        </div>
      `,e)}capabilitiesRenderer(e,t,i){c(u`
        <div class="layout vertical start justified wrap">
          ${i.item.capabilities?i.item.capabilities.map((e=>u`
            <lablup-shields app="" color="blue"
                            description="${e}" ui="round"></lablup-shields>
          `)):u``}
        </div>`,e)}showStorageProxyDetailDialog(e){const t=new CustomEvent("backend-ai-selected-storage-proxy",{detail:e});document.dispatchEvent(t)}controlRenderer(e,t,i){let a;try{const e=JSON.parse(i.item.performance_metric);a=!(Object.keys(e).length>0)}catch(e){a=!0}c(u`
        <div id="controls" class="layout horizontal flex center" agent-id="${i.item.id}">
          <mwc-icon-button class="fg blue controls-running" icon="assignment"
                          ?disabled="${a}"
                          @click="${e=>this.showStorageProxyDetailDialog(i.item.id)}"></mwc-icon-button>
        </div>`,e)}_bytesToMB(e){return Number(e/1048576).toFixed(1)}render(){return u`
    <div class="list-wrapper">
      <vaadin-grid class="${this.condition}" theme="row-stripes column-borders compact" aria-label="Job list"
                    .items="${this.storages}">
          <vaadin-grid-column width="40px" flex-grow="0" header="#" text-align="center"
                              .renderer="${this._indexRenderer}"></vaadin-grid-column>
          <vaadin-grid-column resizable width="80px" header="${p("agent.Endpoint")}" .renderer="${this._boundEndpointRenderer}">
          </vaadin-grid-column>
          <vaadin-grid-column width="100px" resizable header="${p("agent.BackendType")}"
                              .renderer="${this._boundTypeRenderer}">
          </vaadin-grid-column>
          <vaadin-grid-column resizable width="60px" header="${p("agent.Resources")}"
                              .renderer="${this._boundResourceRenderer}">
          </vaadin-grid-column>
          <vaadin-grid-column width="130px" flex-grow="0" resizable header="${p("agent.Capabilities")}"
                              .renderer="${this._boundCapabilitiesRenderer}"></vaadin-grid-column>
          <vaadin-grid-column resizable header="${p("general.Control")}"
                              .renderer="${this._boundControlRenderer}"></vaadin-grid-column>
        </vaadin-grid>
        <backend-ai-list-status id="list-status" statusCondition="${this.listCondition}" message="${h("agent.NoAgentToDisplay")}"></backend-ai-list-status>
      </div>
      <backend-ai-dialog id="storage-proxy-detail" fixed backdrop blockscrolling persistent scrollable>
        <span slot="title">${p("agent.DetailedInformation")}</span>
        <div slot="content">
          <div class="horizontal start start-justified layout">
            ${"cpu_util_live"in this.storageProxyDetail?u`
                <div>
                  <h3>CPU</h3>
                  <div class="horizontal wrap layout" style="max-width:600px;">
                    ${this.storageProxyDetail.cpu_util_live.map((e=>u`
                      <div class="horizontal start-justified center layout" style="padding:0 5px;">
                        <div style="font-size:8px;width:35px;">CPU${e.num}</div>
                        <lablup-progress-bar class="cpu"
                                             progress="${e.pct/100}"
                                             description=""
                        ></lablup-progress-bar>
                      </div>`))}
                  </div>
                </div>`:u``}
            <div style="margin-left:10px;">
              <h3>Memory</h3>
              <div>
                <lablup-progress-bar class="mem"
                                     progress="${this.storageProxyDetail.mem_current_usage_ratio}"
                                     description="${this.storageProxyDetail.current_mem}GB/${this.storageProxyDetail.mem_slots}GB"
                ></lablup-progress-bar>
              </div>
              <h3>Network</h3>
              ${"live_stat"in this.storageProxyDetail&&"node"in this.storageProxyDetail.live_stat?u`
                <div>TX: ${this._bytesToMB(this.storageProxyDetail.live_stat.node.net_tx.current)}MB</div>
                <div>RX: ${this._bytesToMB(this.storageProxyDetail.live_stat.node.net_rx.current)}MB</div>
              `:u``}
            </div>
          </div>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            id="close-button"
            icon="check"
            label="${p("button.Close")}"
            @click="${e=>this._hideDialog(e)}"></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};e([t({type:String})],m.prototype,"condition",void 0),e([t({type:Array})],m.prototype,"storages",void 0),e([t({type:String})],m.prototype,"listCondition",void 0),e([t({type:Object})],m.prototype,"storagesObject",void 0),e([t({type:Object})],m.prototype,"storageProxyDetail",void 0),e([t({type:Object})],m.prototype,"notification",void 0),e([t({type:Object})],m.prototype,"_boundEndpointRenderer",void 0),e([t({type:Object})],m.prototype,"_boundTypeRenderer",void 0),e([t({type:Object})],m.prototype,"_boundResourceRenderer",void 0),e([t({type:Object})],m.prototype,"_boundCapabilitiesRenderer",void 0),e([t({type:Object})],m.prototype,"_boundControlRenderer",void 0),e([t({type:String})],m.prototype,"filter",void 0),e([i("#storage-proxy-detail")],m.prototype,"storageProxyDetailDialog",void 0),e([i("#list-status")],m.prototype,"_listStatus",void 0),m=e([a("backend-ai-storage-proxy-list")],m);
/**
 @license
 Copyright (c) 2015-2018 Lablup Inc. All rights reserved.
 */
let _=class extends s{constructor(){super(),this._boundControlRenderer=this._controlRenderer.bind(this),this.allowedSessionTypesObjects={interactive:"interactive",batch:"batch",both:"both (interactive, batch)"},this.enableSchedulerOpts=!1,this.enableWSProxyAddr=!1,this.functionCount=0,this.active=!1,this.schedulerTypes=["fifo","lifo","drf"],this.resourceGroups=[],this.resourceGroupInfo={},this.domains=[]}static get styles(){return[o,r,l,n`
        h4 {
          font-weight: 200;
          font-size: 14px;
          margin: 0px;
          padding: 5px 15px 5px 20px;
        }

        wl-button {
          --button-bg: var(--paper-light-blue-50);
          --button-bg-hover: var(--paper-blue-100);
          --button-bg-active: var(--paper-blue-600);
        }

        wl-button.delete {
          --button-bg: var(--paper-red-50);
          --button-bg-hover: var(--paper-red-100);
          --button-bg-active: var(--paper-red-600);
          margin-top: 20px;
        }

        backend-ai-dialog {
          --component-min-width: 350px;
        }

        backend-ai-dialog wl-textarea,
        backend-ai-dialog wl-select {
          margin-bottom: 20px;
          --input-font-family: var(--general-font-family);
        }

        backend-ai-dialog mwc-textfield,
        backend-ai-dialog mwc-textarea {
          width: 100%;
          margin: 5px auto 5px auto;
          --mdc-typography-font-family: var(--general-font-family);
          --mdc-theme-primary: var(--general-textfield-selected-color);
        }

        backend-ai-dialog wl-label {
          --label-font-family: 'Ubuntu', Roboto;
          --label-color: #282828;
          margin-bottom: 5px;
        }

        backend-ai-dialog wl-switch {
          margin-bottom: 20px;
          --switch-color-checked: #29b6f6;
          --switch-bg-checked: #bbdefb;
        }

        wl-select {
          --input-color-disabled: #222;
          --input-label-color-disabled: #222;
          --input-label-font-size: 12px;
          --input-border-style-disabled: 1px solid #ccc;
        }

        mwc-button[outlined] {
          width: 100%;
          margin: 10px auto;
          background-image: none;
          --mdc-button-outline-width: 2px;
          --mdc-theme-primary: #38bd73;
          --mdc-theme-on-primary: #38bd73;
        }

        mwc-textarea {
          height: 135px;
        }

        mwc-select {
          width:100%;
          --mdc-typography-font-family: var(--general-font-family);
          --mdc-theme-primary: var(--general-textfield-selected-color);
          --mdc-select-fill-color: transparent;
        }

        mwc-list-item {
          --mdc-menu-item-height: 20px;
        }

        #resource-group-detail-dialog {
          --component-width: 500px;
        }

        #resource-group-dialog {
          --component-width: 350px;
        }

        wl-expansion {
          --expansion-content-padding: 2px;
          --expansion-elevation: 0;
          --expansion-elevation-open: 0;
          --expansion-elevation-hover: 0;
          --expansion-header-padding: 16px;
          --expansion-margin-open: 0;
        }

        backend-ai-dialog h4 {
          font-weight: 700;
          font-size: 14px;
          padding: 5px 15px 5px 12px;
          margin: 0 0 10px 0;
          display: block;
          height: 20px;
          border-bottom: 1px solid #DDD;
        }

        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 225px);
        }

        vaadin-item {
          padding: 5px 17px 5px 17px;
          font-size: 12px;
          font-weight: 100;
        }

        .scheduler-option-value {
          font-size: 16px;
          font-weight: 700;
        }

        #resource-group-detail-dialog wl-textarea {
          margin-bottom: 0px;
          --input-border-width: 0;
          --input-padding-top-bottom: 0px;
          --input-padding-left-right: 12px;
          --input-font-size: 0.75rem;
          --textarea-height: 100px;
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.enableSchedulerOpts=globalThis.backendaiclient.supports("scheduler-opts"),this.enableWSProxyAddr=globalThis.backendaiclient.supports("wsproxy-addr"),globalThis.backendaiclient.scalingGroup.list_available().then((e=>{this.resourceGroups=e.scaling_groups})).catch((e=>{this.notification.text=d.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)})),globalThis.backendaiclient.domain.list().then((({domains:e})=>{this.domains=e,this.requestUpdate()})).catch((e=>{this.notification.text=d.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}))}),!0):(this.enableSchedulerOpts=globalThis.backendaiclient.supports("scheduler-opts"),this.enableWSProxyAddr=globalThis.backendaiclient.supports("wsproxy-addr"),globalThis.backendaiclient.scalingGroup.list_available().then((e=>{this.resourceGroups=e.scaling_groups})).catch((e=>{this.notification.text=d.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)})),globalThis.backendaiclient.domain.list().then((({domains:e})=>{this.domains=e,this.requestUpdate()})).catch((e=>{this.notification.text=d.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)}))))}_activeStatusRenderer(e,t,i){c(u`
        <lablup-shields
          app=""
          color=${i.item.is_active?"green":"red"}
          description=${i.item.is_active?"active":"inactive"}
          ui="flat"
        ></lablup-shields>
    `,e)}_indexRenderer(e,t,i){const a=i.index+1;c(u`
        <div>${a}</div>
      `,e)}_launchDialogById(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(e)).show()}_hideDialogById(e){var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(e)).hide()}_controlRenderer(e,t,i){c(u`
        <div id="controls" class="layout horizontal flex center">
          <wl-button fab flat inverted
            class="fg green"
            @click=${()=>this._launchDetailDialog(i.item)}
          ><wl-icon>assignment</wl-icon></wl-button>
          <wl-button fab flat inverted
            class="fg blue"
            @click=${()=>this._launchModifyDialog(i.item)}
          ><wl-icon>settings</wl-icon></wl-button>
          <wl-button fab flat inverted
            class="fg red"
            @click=${()=>this._launchDeleteDialog(i.item)}
          ><wl-icon>delete</wl-icon></wl-button>
        </div>
      `,e)}_validateResourceGroupName(){const e=this.resourceGroups.map((e=>e.name));this.resourceGroupNameInput.validityTransform=(t,i)=>{if(i.valid){const i=!e.includes(t);return i||(this.resourceGroupNameInput.validationMessage=h("resourceGroup.ResourceGroupAlreadyExist")),{valid:i,customError:!i}}return i.valueMissing?(this.resourceGroupNameInput.validationMessage=h("resourceGroup.ResourceGroupNameRequired"),{valid:i.valid,valueMissing:!i.valid}):(this.resourceGroupNameInput.validationMessage=h("resourceGroup.EnterValidResourceGroupName"),{valid:i.valid,customError:!i.valid})}}_createResourceGroup(){if(this.resourceGroupNameInput.checkValidity()&&this._verifyCreateSchedulerOpts()){this._saveSchedulerOpts();const e=this.resourceGroupNameInput.value,t=this.resourceGroupDescriptionInput.value,i=this.resourceGroupDomainSelect.value,a={description:t,is_active:!0,driver:"static",driver_opts:"{}",scheduler:"fifo"};if(this.enableSchedulerOpts&&(a.scheduler_opts=JSON.stringify(this.schedulerOpts)),this.enableWSProxyAddr){const e=this.resourceGroupWSProxyaddressInput.value;a.wsproxy_addr=e}globalThis.backendaiclient.scalingGroup.create(e,a).then((({create_scaling_group:t})=>t.ok?globalThis.backendaiclient.scalingGroup.associate_domain(i,e):Promise.reject(t.msg))).then((({associate_scaling_group_with_domain:e})=>{e.ok?(this.notification.text=h("resourceGroup.ResourceGroupCreated"),this._refreshList(),this.resourceGroupNameInput.value="",this.resourceGroupDescriptionInput.value=""):(this.notification.text=d.relieve(e.title),this.notification.detail=e.msg),this._hideDialogById("#resource-group-dialog"),this.notification.show()})).catch((e=>{this.notification.text=d.relieve(e.title),this.notification.detail=e,this._hideDialogById("#resource-group-dialog"),this.notification.show(!0,e)}))}}_modifyResourceGroup(){if(!1===this._verifyModifySchedulerOpts())return;this._saveSchedulerOpts();const e=this.resourceGroupDescriptionInput.value,t=this.resourceGroupSchedulerSelect.value,i=this.resourceGroupActiveSwitch.selected,a=this.schedulerOpts,s=this.resourceGroupInfo.name,o={};if(e!==this.resourceGroupInfo.description&&(o.description=e),t!==this.resourceGroupInfo.scheduler&&(o.scheduler=t),i!==this.resourceGroupInfo.is_active&&(o.is_active=i),this.enableWSProxyAddr){let e=this.resourceGroupWSProxyaddressInput.value;e.endsWith("/")&&(e=e.slice(0,e.length-1)),e!==this.resourceGroupInfo.wsproxy_addr&&(o.wsproxy_addr=e)}if(this.enableSchedulerOpts&&a!==this.resourceGroupInfo.scheduler_opts&&(o.scheduler_opts=JSON.stringify(a)),0===Object.keys(o).length)return this.notification.text=h("resourceGroup.NochangesMade"),void this.notification.show();globalThis.backendaiclient.scalingGroup.update(s,o).then((({modify_scaling_group:e})=>{e.ok?(this.notification.text=h("resourceGroup.ResourceGroupModified"),this._refreshList()):(this.notification.text=d.relieve(e.msg),this.notification.detail=e.msg),this._hideDialogById("#resource-group-dialog"),this.notification.show()}))}_deleteResourceGroup(){const e=this.resourceGroupInfo.name;if(this.deleteResourceGroupInput.value!==e)return this.notification.text=h("resourceGroup.ResourceGroupNameNotMatch"),this._hideDialogById("#delete-resource-group-dialog"),void this.notification.show();globalThis.backendaiclient.scalingGroup.delete(e).then((({delete_scaling_group:e})=>{e.ok?(this.notification.text=h("resourceGroup.ResourceGroupDeleted"),this._refreshList(),this.deleteResourceGroupInput.value=""):(this.notification.text=d.relieve(e.msg),this.notification.detail=e.msg),this._hideDialogById("#delete-resource-group-dialog"),this.notification.show()}))}_refreshList(){globalThis.backendaiclient.scalingGroup.list_available().then((({scaling_groups:e})=>{this.resourceGroups=e,this.requestUpdate()}))}_initializeCreateSchedulerOpts(){var e,t,i;const a=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#scheduler-options-input-form");this.allowedSessionTypesSelect.value="both",a.checked=!1,(null===(t=this.timeoutInput)||void 0===t?void 0:t.value)&&(this.timeoutInput.value=""),(null===(i=this.numberOfRetriesToSkip)||void 0===i?void 0:i.value)&&(this.numberOfRetriesToSkip.value="")}_initializeModifySchedulerOpts(e="",t){var i;"allowed_session_types"===e?t.includes("interactive")&&t.includes("batch")?this.allowedSessionTypesSelect.value="both":this.allowedSessionTypesSelect.value=t[0]:"pending_timeout"===e?this.timeoutInput.value=t:"config"===e&&(this.numberOfRetriesToSkip.value=null!==(i=t.num_retries_to_skip)&&void 0!==i?i:"")}_verifyCreateSchedulerOpts(){return!([this.allowedSessionTypesSelect,this.timeoutInput,this.numberOfRetriesToSkip].filter((e=>!e.checkValidity())).length>0)}_verifyModifySchedulerOpts(){return!([this.allowedSessionTypesSelect,this.timeoutInput,this.numberOfRetriesToSkip].filter((e=>!e.checkValidity())).length>0)}_saveSchedulerOpts(){this.schedulerOpts={},"both"===this.allowedSessionTypesSelect.value?this.schedulerOpts.allowed_session_types=["interactive","batch"]:this.schedulerOpts.allowed_session_types=[this.allowedSessionTypesSelect.value],""!==this.timeoutInput.value&&(this.schedulerOpts.pending_timeout=this.timeoutInput.value),""!==this.numberOfRetriesToSkip.value&&Object.assign(this.schedulerOpts,{config:{num_retries_to_skip:this.numberOfRetriesToSkip.value}})}_launchCreateDialog(){this.enableSchedulerOpts&&this._initializeCreateSchedulerOpts(),this.resourceGroupInfo={},this._launchDialogById("#resource-group-dialog")}_launchDeleteDialog(e){this.resourceGroupInfo=e,this._launchDialogById("#delete-resource-group-dialog")}_launchDetailDialog(e){this.resourceGroupInfo=e,this._launchDialogById("#resource-group-detail-dialog")}_launchModifyDialog(e){if(this.resourceGroupInfo=e,this.enableSchedulerOpts){const e=JSON.parse(this.resourceGroupInfo.scheduler_opts);Object.entries(e).forEach((([e,t])=>{this._initializeModifySchedulerOpts(e,t)}))}this._launchDialogById("#resource-group-dialog")}render(){var e,t,i,a,s,o,r,l,n,d,c,g,v,b,m,_,y,f,x,w;return u`
      <h4 class="horizontal flex center center-justified layout">
        <span>${p("resourceGroup.ResourceGroups")}</span>
        <span class="flex"></span>
          <mwc-button
              raised
              icon="add"
              label="${p("button.Add")}"
              @click=${this._launchCreateDialog}>
          </mwc-button>
      </h4>
      <vaadin-grid theme="row-stripes column-borders compact" aria-label="Job list" .items="${this.resourceGroups}">
        <vaadin-grid-column flex-grow="0" header="#" width="40px" .renderer=${this._indexRenderer}>
        </vaadin-grid-column>
        <vaadin-grid-column flex-grow="1" header="${p("resourceGroup.Name")}" path="name">
        </vaadin-grid-column>
        <vaadin-grid-column flex-grow="1" header="${p("resourceGroup.Description")}" path="description">
        </vaadin-grid-column>
        <vaadin-grid-column flex-grow="1" header="${p("resourceGroup.ActiveStatus")}" .renderer=${this._activeStatusRenderer}>
        </vaadin-grid-column>
        <vaadin-grid-column flex-grow="1" header="${p("resourceGroup.Driver")}" path="driver">
        </vaadin-grid-column>
        <vaadin-grid-column flex-grow="1" header="${p("resourceGroup.Scheduler")}" path="scheduler">
        </vaadin-grid-column>
        ${this.enableWSProxyAddr?u`
        <vaadin-grid-column resizable header="${p("resourceGroup.WsproxyAddress")}" path="wsproxy_addr">
        </vaadin-grid-column>
        `:u``}
        <vaadin-grid-column flex-grow="1" header="${p("general.Control")}" .renderer=${this._boundControlRenderer}>
        </vaadin-grid-column>
      </vaadin-grid>
      <backend-ai-dialog id="resource-group-dialog" fixed backdrop blockscrolling>
        <span slot="title"> ${(null===(e=this.resourceGroupInfo)||void 0===e?void 0:e.name)?p("resourceGroup.ModifyResourceGroup"):p("resourceGroup.CreateResourceGroup")}</span>
        <div slot="content" class="login-panel intro centered">
          ${Object.keys(this.resourceGroupInfo).length>0?u`
            <div class="horizontal layout flex wrap center justified">
              <p style="margin-left: 18px;color:rgba(0, 0, 0, 0.6);">
                ${p("resourceGroup.Active")}
              </p>
              <mwc-switch id="resource-group-active" style="margin-right:10px;" ?selected="${this.resourceGroupInfo.is_active}">
              </mwc-switch>
            </div>
            <mwc-select
              id="resource-group-scheduler"
              label="${p("resourceGroup.SelectScheduler")}"
              value="${0===this.resourceGroupInfo.length?"":this.resourceGroupInfo.scheduler}">
              ${this.schedulerTypes.map((e=>u`
                <mwc-list-item value="${e}">${e}</mwc-list-item>
              `))}
            </mwc-select>
          `:u`
          <mwc-select required id="resource-group-domain" label="${p("resourceGroup.SelectDomain")}">
            ${this.domains.map(((e,t)=>u`
              <mwc-list-item value="${e.name}" ?selected=${0===t}>
                ${e.name}
              </mwc-list-item>
            `))}
          </mwc-select>
          <mwc-textfield
            type="text"
            id="resource-group-name"
            label="${p("resourceGroup.ResourceGroupName")}"
            maxLength="64"
            placeholder="${p("maxLength.64chars")}"
            validationMessage="${p("data.explorer.ValueRequired")}"
            required
            autoValidate
            @change="${()=>this._validateResourceGroupName()}"
          ></mwc-textfield>
          `}
          <mwc-textarea
            name="description"
            id="resource-group-description"
            label="${p("resourceGroup.Description")}"
            maxLength="512"
            placeholder="${p("maxLength.512chars")}"
            value="${null!==(i=null===(t=this.resourceGroupInfo)||void 0===t?void 0:t.description)&&void 0!==i?i:""}"
          ></mwc-textarea>
          ${this.enableWSProxyAddr?u`
          <mwc-textfield
                id="resource-group-wsproxy-address"
                type="url"
                label="${p("resourceGroup.WsproxyAddress")}"
                placeholder="http://localhost:10200"
                value="${null!==(s=null===(a=this.resourceGroupInfo)||void 0===a?void 0:a.wsproxy_addr)&&void 0!==s?s:""}"
              ></mwc-textfield>
            `:u``}
          ${this.enableSchedulerOpts?u`
            <wl-expansion id="scheduler-options-input-form">
              <span slot="title">${p("resourceGroup.SchedulerOptions")}</span>
              <mwc-select id="allowed-session-types" label="allowed session types" required>
                ${Object.entries(this.allowedSessionTypesObjects).map((([e,t])=>u`<mwc-list-item value="${e}">${t}</mwc-list-item>`))}
              </mwc-select>
              <mwc-textfield
                type="number"
                value="0"
                id="pending-timeout"
                label="pending timeout"
                placeholder="0"
                suffix="${p("resourceGroup.TimeoutSeconds")}"
                validationMessage="${p("settings.InvalidValue")}"
                autoValidate
                min="0"
                value="${null!==(l=null===(r=null===(o=this.resourceGroupInfo)||void 0===o?void 0:o.scheduler_opts)||void 0===r?void 0:r.pending_timeout)&&void 0!==l?l:""}"
              ></mwc-textfield>
              <mwc-textfield
                  type="number"
                  value="0"
                  id="num-retries-to-skip"
                  label="# retries to skip pending session"
                  placeholder="0"
                  suffix="${p("resourceGroup.RetriesToSkip")}"
                  validationMessage="${p("settings.InvalidValue")}"
                  autoValidate
                  min="0"
                  value="${null!==(g=null===(c=null===(d=null===(n=this.resourceGroupInfo)||void 0===n?void 0:n.scheduler_opts)||void 0===d?void 0:d.config)||void 0===c?void 0:c.num_retries_to_skip)&&void 0!==g?g:""}"
                ></mwc-textfield>
            </wl-expansion>
            `:u``}
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          ${Object.keys(this.resourceGroupInfo).length>0?u`
          <mwc-button
              unelevated
              icon="save"
              label="${p("button.Save")}"
              @click="${this._modifyResourceGroup}">
          </mwc-button>
          `:u`
          <mwc-button
              unelevated
              icon="add"
              label="${p("button.Create")}"
              @click="${this._createResourceGroup}"></mwc-button>
          `}
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="delete-resource-group-dialog" fixed backdrop blockscrolling>
        <span slot="title">${p("dialog.warning.CannotBeUndone")}</span>
        <div slot="content">
          <mwc-textfield
            id="delete-resource-group"
            type="text"
            label="${p("resourceGroup.TypeResourceGroupNameToDelete")}"
            maxLength="64"
            placeholder="${p("maxLength.64chars")}"
          ></mwc-textfield>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            outlined
            icon="delete"
            label="${p("button.Delete")}"
            style="box-sizing: border-box;"
            @click="${this._deleteResourceGroup}">
            </mwc-button>
       </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="resource-group-detail-dialog" fixed backdrop blockscrolling>
        ${Object.keys(this.resourceGroupInfo).length>0?u`
          <span slot="title" class="horizontal center layout">
            <span style="margin-right:15px;">${h("resourceGroup.ResourceGroupDetail")}</span>
          </span>
          <div slot="content" class="intro">
            <div class="horizontal layout" style="margin-bottom:15px;">
              <div style="width:250px;">
                <h4>${h("credential.Information")}</h4>
                <div role="listbox" class="vertical layout">
                  <vaadin-item>
                    <div><strong>${h("resourceGroup.Name")}</strong></div>
                    <div class="scheduler-option-value">${this.resourceGroupInfo.name}</div>
                  </vaadin-item>
                  <vaadin-item>
                    <div><strong>${h("resourceGroup.ActiveStatus")}</strong></div>
                    <lablup-shields
                      app=""
                      color=${this.resourceGroupInfo.is_active?"green":"red"}
                      description=${(null===(v=this.resourceGroupInfo)||void 0===v?void 0:v.is_active)?"active":"inactive"}
                      ui="flat"
                    ></lablup-shields>
                  </vaadin-item>
                  <vaadin-item>
                    <div><strong>${h("resourceGroup.Driver")}</strong></div>
                    <div class="scheduler-option-value">${null===(b=this.resourceGroupInfo)||void 0===b?void 0:b.driver}</div>
                  </vaadin-item>
                  <vaadin-item>
                    <div><strong>${h("resourceGroup.Scheduler")}</strong></div>
                    <div class="scheduler-option-value">${null===(m=this.resourceGroupInfo)||void 0===m?void 0:m.scheduler}</div>
                  </vaadin-item>
                  ${this.enableWSProxyAddr?u`
                  <vaadin-item>
                    <div><strong>${h("resourceGroup.WsproxyAddress")}</strong></div>
                    <div class="scheduler-option-value">${null!==(y=null===(_=this.resourceGroupInfo)||void 0===_?void 0:_.wsproxy_addr)&&void 0!==y?y:"none"}</div>
                  </vaadin-item>
                  `:u``}
                </div>
              </div>
              <div class="center vertial layout" style="width:250px;">
                <div>
                  <h4 class="horizontal center layout">
                    ${p("resourceGroup.SchedulerOptions")}
                  </h4>
                  <div role="listbox">
                    ${this.enableSchedulerOpts?u`
                      ${Object.entries(JSON.parse(null===(f=this.resourceGroupInfo)||void 0===f?void 0:f.scheduler_opts)).map((([e,t])=>"allowed_session_types"===e?u`
                                  <vaadin-item>
                                    <div><strong>allowed session types</strong></div>
                                    <div class="scheduler-option-value">${t.join(", ")}</div>
                                  </vaadin-item>`:"pending_timeout"===e?u`
      <vaadin-item>
      <div><strong>pending timeout</strong></div>
      <div class="scheduler-option-value">${t+" "+h("resourceGroup.TimeoutSeconds")}</div>
    </vaadin-item>`:"config"===e&&t.num_retries_to_skip?u`
        <vaadin-item>
        <div><strong># retries to skip pending session</strong></div>
        <div class="scheduler-option-value">${t.num_retries_to_skip+" "+h("resourceGroup.RetriesToSkip")}</div>
      </vaadin-item>`:""))}
                    `:u``}
                  </div>
                </div>
                <div>
                  <h4 class="horizontal center layout">
                    ${p("resourceGroup.DriverOptions")}
                  </h4>
                  <div role="listbox">
                  </div>
                </div>
              </div>
            </div>
            <div>
              <h4>
                ${p("resourceGroup.Description")}
              </h4>
              <wl-textarea readonly value="${null!==(w=null===(x=this.resourceGroupInfo)||void 0===x?void 0:x.description)&&void 0!==w?w:""}">
              </wl-textarea>
            </div>
          </div>`:""}
      </backend-ai-dialog>
    `}};e([t({type:Object})],_.prototype,"_boundControlRenderer",void 0),e([t({type:Array})],_.prototype,"domains",void 0),e([t({type:Object})],_.prototype,"resourceGroupInfo",void 0),e([t({type:Array})],_.prototype,"resourceGroups",void 0),e([t({type:Array})],_.prototype,"schedulerTypes",void 0),e([t({type:Object})],_.prototype,"schedulerOpts",void 0),e([t({type:Object})],_.prototype,"allowedSessionTypesObjects",void 0),e([t({type:Boolean})],_.prototype,"enableSchedulerOpts",void 0),e([t({type:Boolean})],_.prototype,"enableWSProxyAddr",void 0),e([t({type:Number})],_.prototype,"functionCount",void 0),e([i("#resource-group-name")],_.prototype,"resourceGroupNameInput",void 0),e([i("#resource-group-description")],_.prototype,"resourceGroupDescriptionInput",void 0),e([i("#resource-group-domain")],_.prototype,"resourceGroupDomainSelect",void 0),e([i("#resource-group-scheduler")],_.prototype,"resourceGroupSchedulerSelect",void 0),e([i("#resource-group-active")],_.prototype,"resourceGroupActiveSwitch",void 0),e([i("#resource-group-wsproxy-address")],_.prototype,"resourceGroupWSProxyaddressInput",void 0),e([i("#allowed-session-types")],_.prototype,"allowedSessionTypesSelect",void 0),e([i("#num-retries-to-skip")],_.prototype,"numberOfRetriesToSkip",void 0),e([i("#pending-timeout")],_.prototype,"timeoutInput",void 0),e([i("#delete-resource-group")],_.prototype,"deleteResourceGroupInput",void 0),_=e([a("backend-ai-resource-group-list")],_);
/**
 @license
 Copyright (c) 2015-2022 Lablup Inc. All rights reserved.
 */
let y=class extends s{constructor(){super(...arguments),this._status="inactive",this._tab="running-lists",this.enableStorageProxy=!1}static get styles(){return[o,n`
        h3.tab {
          background-color: var(--general-tabbar-background-color);
          border-radius: 5px 5px 0 0;
          margin: 0 auto;
        }

        mwc-tab-bar {
          --mdc-theme-primary: var(--general-sidebar-selected-color);
          --mdc-text-transform: none;
          --mdc-tab-color-default: var(--general-tabbar-background-color);
          --mdc-tab-text-label-color-default: var(--general-tabbar-tab-disabled-color);
        }

        @media screen and (max-width: 805px) {
          mwc-tab {
            --mdc-typography-button-font-size: 10px;
          }
        }
      `]}firstUpdated(){void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.enableStorageProxy=globalThis.backendaiclient.supports("storage-proxy")}),!0):this.enableStorageProxy=globalThis.backendaiclient.supports("storage-proxy")}async _viewStateChanged(e){var t,i,a,s,o,r;if(await this.updateComplete,!e)return(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#running-agents")).active=!1,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#terminated-agents")).active=!1,(null===(a=this.shadowRoot)||void 0===a?void 0:a.querySelector("#scaling-groups")).active=!1,void(this._status="inactive");(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#running-agents")).active=!0,(null===(o=this.shadowRoot)||void 0===o?void 0:o.querySelector("#terminated-agents")).active=!0,(null===(r=this.shadowRoot)||void 0===r?void 0:r.querySelector("#scaling-groups")).active=!1,this._status="active"}_showTab(e){var t,i;const a=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(let e=0;e<a.length;e++)a[e].style.display="none";(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e.title)).style.display="block",this._tab=e.title}render(){return u`
      <link rel="stylesheet" href="resources/custom.css">
      <lablup-activity-panel noheader narrow autowidth>
        <div slot="message">
          <h3 class="tab horizontal center layout">
            <mwc-tab-bar>
              <mwc-tab title="running-lists" label="${p("agent.Connected")}"
                  @click="${e=>this._showTab(e.target)}"></mwc-tab>
              <mwc-tab title="terminated-lists" label="${p("agent.Terminated")}"
                  @click="${e=>this._showTab(e.target)}"></mwc-tab>
              <!--<mwc-tab title="maintenance-lists" label="${p("agent.Maintaining")}"
                  @click="${e=>this._showTab(e.target)}"></mwc-tab>-->
              ${this.enableStorageProxy?u`
              <mwc-tab title="storage-proxy-lists" label="${p("general.StorageProxies")}"
                  @click="${e=>this._showTab(e.target)}"></mwc-tab>`:u``}
              <mwc-tab title="scaling-group-lists" label="${p("general.ResourceGroup")}"
                  @click="${e=>this._showTab(e.target)}"></mwc-tab>
            </mwc-tab-bar>
            <div class="flex"></div>
          </h3>
          <div id="running-lists" class="tab-content">
            <backend-ai-agent-list id="running-agents" condition="running" ?active="${"active"===this._status&&"running-lists"===this._tab}"></backend-ai-agent-list>
          </div>
          <div id="terminated-lists" class="tab-content" style="display:none;">
            <backend-ai-agent-list id="terminated-agents" condition="terminated" ?active="${"active"===this._status&&"terminated-lists"===this._tab}"></backend-ai-agent-list>
          </div>
          ${this.enableStorageProxy?u`
          <div id="storage-proxy-lists" class="tab-content" style="display:none;">
            <backend-ai-storage-proxy-list id="storage-proxies" ?active="${"active"===this._status&&"storage-proxy-lists"===this._tab}"></backend-ai-storage-proxy-list>
          </div>`:u``}
          <div id="scaling-group-lists" class="tab-content" style="display:none;">
            <backend-ai-resource-group-list id="scaling-groups" ?active="${"active"===this._status&&"scaling-group-lists"===this._tab}"> </backend-ai-resource-group-list>
          </div>
        </div>
      </lablup-activity-panel>
    `}};e([g()],y.prototype,"_status",void 0),e([g()],y.prototype,"_tab",void 0),e([g()],y.prototype,"enableStorageProxy",void 0),y=e([a("backend-ai-agent-view")],y);var f=y;export{f as default};
