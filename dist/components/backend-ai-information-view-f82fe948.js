import{B as i,d as e,I as t,b as s,x as n,f as a,i as o,y as l,t as d,g as c,_ as r,e as v,a as p}from"./backend-ai-webui-efd2500f.js";import{t as u}from"./translate-unsafe-html-8abe2c79.js";import"./lablup-activity-panel-b5a6a642.js";let h=class extends i{constructor(){super(...arguments),this.notification=Object(),this.manager_version="",this.manager_version_latest="",this.webui_version="",this.api_version="",this.docker_version="",this.pgsql_version="",this.redis_version="",this.etcd_version="",this.license_valid=!1,this.license_type="",this.license_licensee="",this.license_key="",this.license_expiration="",this.account_changed=!0,this.use_ssl=!0}static get styles(){return[e,t,s,n,a,o`
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

        p.label {
          display: inline-block;
          width: auto;
          margin: 0px;
          padding: 0px 3px;
          background-clip: padding-box;
          background-color: #f9f9f9;
          border: 1px solid #ccc;
          border-radius: 3px;
        }

        .setting-item {
          margin: 15px auto;
        }

        .setting-item-bottom-expand {
          margin: 15px auto 49px auto;
        }

        .setting-desc {
          width: 65%;
          margin: 5px;
        }

        .setting-desc-shrink {
          width: 100px;
          margin: 5px 35px 5px 5px;
          margin-right: 35px;
        }

        .setting-label {
          width: 30%;
        }

        wl-card > div {
          padding: 15px;
        }

        wl-button {
          --button-bg: transparent;
          --button-bg-hover: var(--paper-red-100);
          --button-bg-active: var(--paper-red-100);
          --button-bg-disabled: #ccc;
          --button-color: var(--paper-red-100);
          --button-color-hover: var(--paper-red-100);
          --button-color-disabled: #ccc;
        }

        lablup-activity-panel {
          color: #000;
        }

        @media screen and (max-width: 805px) {
          .setting-desc {
            width: 60%;
          }

          .setting-label {
            width: 35%;
          }
        }
      `]}render(){return l`
      <link rel="stylesheet" href="resources/custom.css">
      <div class="horizontal layout flex wrap">
        <div class="vertical layout">
          <lablup-activity-panel title="${d("information.Core")}" horizontalsize="1x">
            <div slot="message">
              <div class="horizontal flex layout wrap setting-item">
                <div class="vertical center-justified layout setting-desc-shrink" style="margin-right: 65px;">
                  <div class="title">${d("information.ManagerVersion")}</div>
                </div>
                <div class="vertical center-justified layout">
                  Backend.AI ${this.manager_version}
                  <lablup-shields app="${d("information.Installation")}" color="darkgreen" description="${this.manager_version}" ui="flat"></lablup-shields>
                  <lablup-shields app="${d("information.LatestRelease")}" color="darkgreen" description="${this.manager_version_latest}" ui="flat"></lablup-shields>
                </div>
              </div>
              <div class="horizontal flex layout wrap setting-item">
                <div class="vertical center-justified layout setting-desc">
                  <div class="title">${d("information.APIVersion")}</div>
                </div>
                <div class="horizontal center end-justified layout setting-label">
                  ${this.api_version}
                </div>
              </div>
            </div>
          </lablup-activity-panel>
          <lablup-activity-panel title="${d("information.Security")}">
            <div slot="message">
              <div class="horizontal flex layout wrap setting-item">
                <div class="vertical center-justified layout setting-desc">
                  <div class="title">${d("information.DefaultAdministratorAccountChanged")}</div>
                  <div class="description">${d("information.DescDefaultAdministratorAccountChanged")}
                  </div>
                </div>
                <div class="horizontal center end-justified layout" style="width:30%;">
                ${this.account_changed?l`<mwc-icon>done</mwc-icon>`:l`<mwc-icon>warning</mwc-icon>`}
                </div>
              </div>
              <div class="horizontal flex layout wrap setting-item">
                <div class="vertical center-justified layout setting-desc">
                  <div class="title">${d("information.UsesSSL")}</div>
                  <div class="description">${d("information.DescUsesSSL")}
                  </div>
                </div>
                <div class="horizontal center end-justified layout" style="width:30%;">
                ${this.use_ssl?l`<mwc-icon>done</mwc-icon>`:l`<mwc-icon class="fg red">warning</mwc-icon>`}
                </div>
              </div>
            </div>
          </lablup-activity-panel>
        </div>
        <lablup-activity-panel title="${d("information.Component")}">
          <div slot="message">
            <div class="horizontal flex layout wrap setting-item-bottom-expand">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${d("information.DockerVersion")}</div>
                <div class="description">${u("information.DescDockerVersion")}
                </div>
              </div>
              <div class="horizontal center end-justified layout setting-label">
                <p class="label">${this.docker_version}</p>
              </div>
            </div>
            <div class="horizontal flex layout wrap setting-item-bottom-expand">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${d("information.PostgreSQLVersion")}</div>
                <div class="description">${u("information.DescPostgreSQLVersion")}
                </div>
              </div>
              <div class="horizontal center end-justified layout setting-label">
                <p class="label">${this.pgsql_version}</p>
              </div>
            </div>
            <div class="horizontal flex layout wrap setting-item-bottom-expand">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${d("information.ETCDVersion")}</div>
                <div class="description">${u("information.DescETCDVersion")}
                </div>
              </div>
              <div class="horizontal center end-justified layout setting-label">
                <p class="label">${this.etcd_version}</p>
              </div>
            </div>
            <div class="horizontal flex layout wrap setting-item-bottom-expand">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${d("information.RedisVersion")}</div>
                <div class="description">${u("information.DescRedisVersion")}
                </div>
              </div>
              <div class="horizontal center end-justified layout setting-label">
                <p class="label">${this.redis_version}</p>
              </div>
            </div>
          </div>
        </lablup-activity-panel>
        <lablup-activity-panel title="${d("information.License")}" horizontalsize="2x">
          <div slot="message">
            <div class="horizontal flex layout wrap setting-item">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${d("information.IsLicenseValid")}</div>
                <div class="description">${d("information.DescIsLicenseValid")}
                </div>
              </div>
              <div class="horizontal center end-justified layout" style="width:30%;">
              ${this.license_valid?l`<mwc-icon>done</mwc-icon>`:l`<mwc-icon class="fg red">warning</mwc-icon>`}
              </div>
            </div>
            <div class="horizontal flex layout wrap setting-item">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${d("information.LicenseType")}</div>
                <div class="description">${u("information.DescLicenseType")}
                </div>
              </div>
              <div class="horizontal center end-justified layout setting-label">
                <p class="label">
                  ${"fixed"===this.license_type?d("information.FixedLicense"):d("information.DynamicLicense")}
                </p>
              </div>
            </div>
            <div class="horizontal flex layout wrap setting-item">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${d("information.Licensee")}</div>
                <div class="description">${d("information.DescLicensee")}
                </div>
              </div>
              <div class="horizontal center end-justified layout setting-label">
                <p class="label">${this.license_licensee}</p>
              </div>
            </div>
            <div class="horizontal flex layout wrap setting-item">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${d("information.LicenseKey")}</div>
                <div class="description">${d("information.DescLicenseKey")}
                </div>
              </div>
              <div class="horizontal center end-justified layout setting-label">
                <p class="label">${this.license_key}</p>
              </div>
            </div>
            <div class="horizontal flex layout wrap setting-item">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${d("information.Expiration")}</div>
                <div class="description">${d("information.DescExpiration")}
                </div>
              </div>
              <div class="horizontal center end-justified layout setting-label">
                <p class="label">${this.license_expiration}</p>
              </div>
            </div>
          </div>
        </div>
      </lablup-activity-panel>
    `}firstUpdated(){this.notification=globalThis.lablupNotification,void 0===globalThis.backendaiclient||null===globalThis.backendaiclient?document.addEventListener("backend-ai-connected",(()=>{this.updateInformation()}),!0):this.updateInformation()}async _viewStateChanged(i){await this.updateComplete}_updateLicenseInfo(){globalThis.backendaiclient.enterprise.getLicense().then((i=>{this.license_valid=i.valid,this.license_type=i.type,this.license_licensee=i.licensee,this.license_key=i.licenseKey,this.license_expiration=i.expiration})).catch((i=>{this.license_valid=!1,this.license_type=c("information.CannotRead"),this.license_licensee=c("information.CannotRead"),this.license_key=c("information.CannotRead"),this.license_expiration=c("information.CannotRead")}))}updateInformation(){this.manager_version=globalThis.backendaiclient.managerVersion,this.webui_version=globalThis.packageVersion,this.api_version=globalThis.backendaiclient.apiVersion,this.docker_version=c("information.Compatible"),this.pgsql_version=c("information.Compatible"),this.redis_version=c("information.Compatible"),this.etcd_version=c("information.Compatible"),void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this._updateLicenseInfo()}),!0):this._updateLicenseInfo(),globalThis.backendaiclient._config.endpoint.startsWith("https:")?this.use_ssl=!0:this.use_ssl=!1}};r([v({type:Object})],h.prototype,"notification",void 0),r([v({type:String})],h.prototype,"manager_version",void 0),r([v({type:String})],h.prototype,"manager_version_latest",void 0),r([v({type:String})],h.prototype,"webui_version",void 0),r([v({type:String})],h.prototype,"api_version",void 0),r([v({type:String})],h.prototype,"docker_version",void 0),r([v({type:String})],h.prototype,"pgsql_version",void 0),r([v({type:String})],h.prototype,"redis_version",void 0),r([v({type:String})],h.prototype,"etcd_version",void 0),r([v({type:Boolean})],h.prototype,"license_valid",void 0),r([v({type:String})],h.prototype,"license_type",void 0),r([v({type:String})],h.prototype,"license_licensee",void 0),r([v({type:String})],h.prototype,"license_key",void 0),r([v({type:String})],h.prototype,"license_expiration",void 0),r([v({type:Boolean})],h.prototype,"account_changed",void 0),r([v({type:Boolean})],h.prototype,"use_ssl",void 0),h=r([p("backend-ai-information-view")],h);var g=h;export{g as default};
