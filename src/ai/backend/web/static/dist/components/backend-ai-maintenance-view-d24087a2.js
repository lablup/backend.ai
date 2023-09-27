import{_ as e,n as a,b as t,e as i,B as n,c as s,I as c,a as l,m as o,d,i as r,x as g,t as m,h as u,g as b,f as h}from"./backend-ai-webui-75df15ed.js";import"./lablup-activity-panel-86e1deef.js";let p=class extends n{constructor(){super(...arguments),this.images=Object(),this.scanning=!1,this.recalculating=!1,this.notification=Object(),this.indicator=Object()}static get styles(){return[s,c,l,o,d,r`
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
          --mdc-button-disabled-outline-color: var(--general-sidebar-color);
          --mdc-button-disabled-ink-color: var(--general-sidebar-color);
          --mdc-theme-primary: #38bd73;
          --mdc-theme-on-primary: #38bd73;
        }

        lablup-activity-panel {
          color: #000;
        }
      `]}render(){return g`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="horizontal wrap layout">
        <lablup-activity-panel title="${m("maintenance.Fix")}">
          <div slot="message" class="vertical flex layout wrap setting-item">
            <div class="vertical center-justified layout setting-desc">
              <div class="title">${m("maintenance.MatchDatabase")}</div>
              <div class="description">
                ${u("maintenance.DescMatchDatabase")}
              </div>
            </div>
            <mwc-button
              outlined
              id="recalculate_usage-button-desc"
              ?disabled="${this.recalculating}"
              label="${m("maintenance.RecalculateUsage")}"
              icon="refresh"
              @click="${()=>this.recalculate_usage()}"
            ></mwc-button>
          </div>
        </lablup-activity-panel>
        <lablup-activity-panel title="${m("maintenance.ImagesEnvironment")}">
          <div slot="message">
            <div class="horizontal flex layout wrap setting-item">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${m("maintenance.RescanImageList")}</div>
                <div class="description">
                  ${u("maintenance.DescRescanImageList")}
                </div>
              </div>
              <mwc-button
                outlined
                id="rescan-image-button-desc"
                ?disabled="${this.scanning}"
                label="${m("maintenance.RescanImages")}"
                icon="refresh"
                @click="${()=>this.rescan_images()}"
              ></mwc-button>
            </div>
            <div
              class="horizontal flex layout wrap setting-item temporarily-hide"
            >
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${m("maintenance.CleanupOldImages")}</div>
                <div class="description">
                  ${m("maintenance.DescCleanupOldImages")}
                </div>
              </div>
              <mwc-button
                outlined
                disabled
                label="${m("maintenance.CleanupImages")}"
                icon="delete"
              ></mwc-button>
            </div>
          </div>
        </lablup-activity-panel>
      </div>
    `}firstUpdated(){this.notification=globalThis.lablupNotification,this.indicator=globalThis.lablupIndicator,void 0!==globalThis.backendaiclient&&null!==globalThis.backendaiclient||document.addEventListener("backend-ai-connected",(()=>!0),!0)}async _viewStateChanged(e){await this.updateComplete}async rescan_images(){this.rescanImageButton.label=b("maintenance.RescanImageScanning"),this.scanning=!0;const e=await this.indicator.start("indeterminate");e.set(0,b("maintenance.Scanning")),globalThis.tasker.add(b("maintenance.RescanImages"),globalThis.backendaiclient.maintenance.rescan_images().then((({rescan_images:a})=>{const t=globalThis.backendaiclient.maintenance.attach_background_task(a.task_id);t.addEventListener("bgtask_updated",(a=>{const t=JSON.parse(a.data),i=t.current_progress/t.total_progress;e.set(100*i,b("maintenance.Scanning"))})),t.addEventListener("bgtask_done",(a=>{const i=new CustomEvent("image-rescanned");document.dispatchEvent(i),e.set(100,b("maintenance.RescanImageFinished")),t.close()})),t.addEventListener("bgtask_failed",(e=>{throw console.log("task_failed",e.data),t.close(),new Error("Background Image scanning task has failed")})),t.addEventListener("bgtask_cancelled",(e=>{throw t.close(),new Error("Background Image scanning task has been cancelled")})),this.rescanImageButton.label=b("maintenance.RescanImages"),this.scanning=!1})).catch((a=>{this.scanning=!1,this.rescanImageButton.label=b("maintenance.RescanImages"),console.log(a),e.set(50,b("maintenance.RescanFailed")),e.end(1e3),a&&a.message&&(this.notification.text=h.relieve(a.title),this.notification.detail=a.message,this.notification.show(!0,a))})),"","image")}async recalculate_usage(){this.recalculateUsageButton.label=b("maintenance.Recalculating"),this.recalculating=!0;const e=await this.indicator.start("indeterminate");e.set(10,b("maintenance.Recalculating")),this.tasker.add(b("maintenance.RecalculateUsage"),globalThis.backendaiclient.maintenance.recalculate_usage().then((a=>{this.recalculateUsageButton.label=b("maintenance.RecalculateUsage"),this.recalculating=!1,e.set(100,b("maintenance.RecalculationFinished"))})).catch((a=>{this.recalculating=!1,this.recalculateUsageButton.label=b("maintenance.RecalculateUsage"),console.log(a),e.set(50,b("maintenance.RecalculationFailed")),e.end(1e3),a&&a.message&&(this.notification.text=h.relieve(a.title),this.notification.detail=a.message,this.notification.show(!0,a))})),"","database")}};e([a({type:Object})],p.prototype,"images",void 0),e([a({type:Boolean})],p.prototype,"scanning",void 0),e([a({type:Boolean})],p.prototype,"recalculating",void 0),e([a({type:Object})],p.prototype,"notification",void 0),e([a({type:Object})],p.prototype,"indicator",void 0),e([t("#recalculate_usage-button-desc")],p.prototype,"recalculateUsageButton",void 0),e([t("#rescan-image-button-desc")],p.prototype,"rescanImageButton",void 0),p=e([i("backend-ai-maintenance-view")],p);
