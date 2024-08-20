import{_ as e,n as a,e as t,t as i,B as n,b as s,I as c,a as l,u as o,c as d,i as r,x as u,f as g,h as m,g as p,d as b}from"./backend-ai-webui-dvRyOX_e.js";import"./lablup-activity-panel-CUzA1T9h.js";let v=class extends n{constructor(){super(...arguments),this.images=Object(),this.scanning=!1,this.recalculating=!1,this.notification=Object(),this.indicator=Object()}static get styles(){return[s,c,l,o,d,r`
        div.indicator,
        span.indicator {
          font-size: 9px;
          margin-right: 5px;
        }

        div.title {
          font-size: 14px;
          font-weight: bold;
        }

        div.description,
        span.description {
          font-size: 13px;
          margin-top: 5px;
          margin-right: 5px;
        }

        .setting-item {
          margin: 15px auto;
        }

        .setting-desc {
          width: 100%;
        }

        mwc-button[outlined] {
          width: 100%;
          margin: 10px auto;
          background-image: none;
          --mdc-button-outline-width: 2px;
        }
      `]}render(){return u`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="horizontal wrap layout" style="gap:24px;">
        <lablup-activity-panel title="${g("maintenance.Fix")}">
          <div slot="message" class="vertical flex layout wrap setting-item">
            <div class="vertical center-justified layout setting-desc">
              <div class="title">${g("maintenance.MatchDatabase")}</div>
              <div class="description">
                ${m("maintenance.DescMatchDatabase")}
              </div>
            </div>
            <mwc-button
              outlined
              id="recalculate_usage-button-desc"
              ?disabled="${this.recalculating}"
              label="${g("maintenance.RecalculateUsage")}"
              icon="refresh"
              @click="${()=>this.recalculate_usage()}"
            ></mwc-button>
          </div>
        </lablup-activity-panel>
        <lablup-activity-panel title="${g("maintenance.ImagesEnvironment")}">
          <div slot="message">
            <div class="horizontal flex layout wrap setting-item">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${g("maintenance.RescanImageList")}</div>
                <div class="description">
                  ${m("maintenance.DescRescanImageList")}
                </div>
              </div>
              <mwc-button
                outlined
                id="rescan-image-button-desc"
                ?disabled="${this.scanning}"
                label="${g("maintenance.RescanImages")}"
                icon="refresh"
                @click="${()=>this.rescan_images()}"
              ></mwc-button>
            </div>
            <div
              class="horizontal flex layout wrap setting-item temporarily-hide"
            >
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${g("maintenance.CleanupOldImages")}</div>
                <div class="description">
                  ${g("maintenance.DescCleanupOldImages")}
                </div>
              </div>
              <mwc-button
                outlined
                disabled
                label="${g("maintenance.CleanupImages")}"
                icon="delete"
              ></mwc-button>
            </div>
          </div>
        </lablup-activity-panel>
      </div>
    `}firstUpdated(){this.notification=globalThis.lablupNotification,this.indicator=globalThis.lablupIndicator,void 0!==globalThis.backendaiclient&&null!==globalThis.backendaiclient||document.addEventListener("backend-ai-connected",(()=>!0),!0)}async _viewStateChanged(e){await this.updateComplete}async rescan_images(){this.scanning=!0;const e="image-rescan:"+(new Date).getTime(),a=new CustomEvent("add-bai-notification",{detail:{key:e,message:p("maintenance.RescanImages"),description:p("maintenance.RescanImageScanning"),backgroundTask:{percent:0,status:"pending"},duration:0,open:!0}});document.dispatchEvent(a),globalThis.backendaiclient.maintenance.rescan_images().then((({rescan_images:a})=>{const t=new CustomEvent("add-bai-notification",{detail:{key:e,description:p("maintenance.RescanImageScanning"),backgroundTask:{taskId:a.task_id,statusDescriptions:{pending:p("maintenance.RescanImageScanning"),resolved:p("maintenance.RescanImageFinished"),rejected:p("maintenance.RescanFailed")},status:"pending",percent:0},duration:0}});document.dispatchEvent(t)})).finally((()=>{this.scanning=!1}))}async recalculate_usage(){this.recalculateUsageButton.label=p("maintenance.Recalculating"),this.recalculating=!0,this.tasker.add(p("maintenance.RecalculateUsage"),new Promise(((e,a)=>globalThis.backendaiclient.maintenance.recalculate_usage().then((a=>{this.recalculateUsageButton.label=p("maintenance.RecalculateUsage"),this.recalculating=!1,e({description:p("maintenance.RecalculationFinished"),progress:{percent:100,status:"success"}})})).catch((e=>{this.recalculating=!1,this.recalculateUsageButton.label=p("maintenance.RecalculateUsage"),console.log(e);let t,i=p("maintenance.RecalculationFailed");e&&e.message&&(i=b.relieve(e.title),t=e.message),a({message:i,description:t,progress:{percent:50,status:"exception"}})})))),"","database","",p("maintenance.Recalculating"),p("maintenance.RecalculationFinished"))}};e([a({type:Object})],v.prototype,"images",void 0),e([a({type:Boolean})],v.prototype,"scanning",void 0),e([a({type:Boolean})],v.prototype,"recalculating",void 0),e([a({type:Object})],v.prototype,"notification",void 0),e([a({type:Object})],v.prototype,"indicator",void 0),e([t("#recalculate_usage-button-desc")],v.prototype,"recalculateUsageButton",void 0),e([t("#rescan-image-button-desc")],v.prototype,"rescanImageButton",void 0),v=e([i("backend-ai-maintenance-view")],v);
