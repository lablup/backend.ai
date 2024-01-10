import{_ as e,n as t,b as i,e as a,B as s,c as o,I as n,a as r,i as l,p as c,x as d,t as p,g,q as h,d as u,O as b,f as m,h as v,j as y}from"./backend-ai-webui-7bb27bb8.js";import"./vaadin-grid-59d71259.js";import"./vaadin-grid-selection-column-34dfab99.js";import"./vaadin-grid-sort-column-d8d756cf.js";import"./vaadin-iconset-35e87c2b.js";import"./backend-ai-list-status-dbbdda83.js";import"./lablup-codemirror-09035526.js";import"./lablup-loading-spinner-2383f266.js";import"./mwc-switch-17cdddca.js";import"./lablup-activity-panel-6efe057d.js";import"./mwc-tab-bar-bc6f9f8d.js";import"./dir-utils-ff9a8c25.js";let f=class extends s{constructor(){super(...arguments),this.timestamp="",this.errorType="",this.requestUrl="",this.statusCode="",this.statusText="",this.title="",this.message="",this.logs=[],this._selected_items=[],this.listCondition="loading",this._grid=Object(),this.logView=[],this._pageSize=25,this._currentPage=1,this._totalLogCount=0,this.boundTimeStampRenderer=this.timeStampRenderer.bind(this),this.boundStatusRenderer=this.statusRenderer.bind(this),this.boundErrTitleRenderer=this.errTitleRenderer.bind(this),this.boundErrMsgRenderer=this.errMsgRenderer.bind(this),this.boundErrTypeRenderer=this.errTypeRenderer.bind(this),this.boundMethodRenderer=this.methodRenderer.bind(this),this.boundReqUrlRenderer=this.reqUrlRender.bind(this),this.boundParamRenderer=this.paramRenderer.bind(this)}static get styles(){return[o,n,r,l`
        vaadin-grid {
          width: 100%;
          border: 0;
          font-size: 12px;
          height: calc(100vh - 305px);
        }

        vaadin-grid-cell {
          font-size: 10px;
        }

        vaadin-grid#list-grid {
          border-top: 1px solid #dbdbdb;
        }

        .error-cell {
          color: red;
        }

        div.pagination-label {
          background-color: var(--paper-grey-100);
          min-width: 60px;
          font-size: 12px;
          font-family: var(--general-font-family);
          padding-top: 5px;
          width: auto;
          text-align: center;
        }

        mwc-icon-button.pagination {
          --button-bg: transparent;
          --button-bg-hover: var(--paper-teal-100);
          --button-bg-active: var(--paper-teal-600);
          --button-bg-active-flat: var(--paper-teal-600);
          --button-bg-disabled: var(--paper-grey-50);
          --button-color-disabled: var(--paper-grey-200);
        }
      `]}firstUpdated(){var e,t;this._updatePageItemSize(),this._grid=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#list-grid"),globalThis.backendaiclient&&globalThis.backendaiclient.is_admin||((null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("vaadin-grid")).style.height="calc(100vh - 275px)!important"),this.notification=globalThis.lablupNotification,document.addEventListener("log-message-refresh",(()=>this._refreshLogData())),document.addEventListener("log-message-clear",(()=>this._clearLogData()))}_updatePageItemSize(){const e=window.innerHeight-275-30;this._pageSize=Math.floor(e/31)}_refreshLogData(){var e,t;this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show(),this._updatePageItemSize(),this.logs=JSON.parse(localStorage.getItem("backendaiwebui.logs")||"{}"),this._totalLogCount=this.logs.length>0?this.logs.length:1,this._updateItemsFromPage(1),this._grid.clearCache(),0==this.logs.length?this.listCondition="no-data":null===(t=this._listStatus)||void 0===t||t.hide()}_clearLogData(){this.logs=[],this.logView=[],this._totalLogCount=1,this._currentPage=1,this._grid.clearCache()}_updateItemsFromPage(e){if("number"!=typeof e){let t=e.target;"button"!==t.role&&(t=e.target.closest("mwc-icon-button")),"previous-page"===t.id?this._currentPage-=1:this._currentPage+=1}const t=(this._currentPage-1)*this._grid.pageSize,i=this._currentPage*this._grid.pageSize;if(this.logs.length>0){const e=this.logs.slice(t,i);e.forEach((e=>{e.timestamp_hr=this._humanReadableTime(e.timestamp)})),this.logView=e}}_humanReadableTime(e){return(e=new Date(e)).toLocaleString("en-US",{hour12:!1})}_toISOTime(e){return(e=new Date(e)).toISOString()}timeStampRenderer(e,t,i){c(d`
        <div class="layout vertical">
          <span class="monospace ${i.item.isError?"error-cell":""}">
            ${i.item.timestamp_hr}
          </span>
        </div>
      `,e)}statusRenderer(e,t,i){c(d`
        <div class="layout vertical">
          <span class="${i.item.isError?"error-cell":""}">
            ${i.item.statusCode+" "+i.item.statusText}
          </span>
        </div>
      `,e)}errTitleRenderer(e,t,i){c(d`
        <div class="layout vertical">
          <span class="${i.item.isError?"error-cell":""}">
            ${i.item.title}
          </span>
        </div>
      `,e)}errMsgRenderer(e,t,i){c(d`
        <div class="layout vertical">
          <span class="${i.item.isError?"error-cell":""}">
            ${i.item.message}
          </span>
        </div>
      `,e)}errTypeRenderer(e,t,i){c(d`
        <div class="layout vertical">
          <span class="${i.item.isError?"error-cell":""}">
            ${i.item.type}
          </span>
        </div>
      `,e)}methodRenderer(e,t,i){c(d`
        <div class="layout vertical">
          <span class="${i.item.isError?"error-cell":""}">
            ${i.item.requestMethod}
          </span>
        </div>
      `,e)}reqUrlRender(e,t,i){c(d`
        <div class="layout vertical">
          <span class="monospace ${i.item.isError?"error-cell":""}">
            ${i.item.requestUrl}
          </span>
        </div>
      `,e)}paramRenderer(e,t,i){c(d`
        <div class="layout vertical">
          <span class="monospace ${i.item.isError?"error-cell":""}">
            ${i.item.requestParameters}
          </span>
        </div>
      `,e)}render(){return d`
      <lablup-loading-spinner id="loading-spinner"></lablup-loading-spinner>
      <div class="list-wrapper">
        <vaadin-grid
          id="list-grid"
          page-size="${this._pageSize}"
          theme="row-stripes column-borders compact wrap-cell-content"
          aria-label="Error logs"
          .items="${this.logView}"
        >
          <vaadin-grid-column
            width="250px"
            flex-grow="0"
            text-align="start"
            auto-width
            header="${p("logs.TimeStamp")}"
            .renderer="${this.boundTimeStampRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            resizable
            flex-grow="0"
            text-align="start"
            auto-width
            header="${p("logs.Status")}"
            .renderer="${this.boundStatusRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            resizable
            flex-grow="0"
            text-align="start"
            auto-width
            header="${p("logs.ErrorTitle")}"
            .renderer="${this.boundErrTitleRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            resizable
            flex-grow="0"
            text-align="start"
            auto-width
            header="${p("logs.ErrorMessage")}"
            .renderer="${this.boundErrMsgRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            width="50px"
            flex-grow="0"
            text-align="start"
            auto-width
            header="${p("logs.ErrorType")}"
            .renderer="${this.boundErrTypeRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            resizable
            flex-grow="0"
            text-align="start"
            auto-width
            header="${p("logs.Method")}"
            .renderer="${this.boundMethodRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            resizable
            flex-grow="0"
            text-align="start"
            auto-width
            header="${p("logs.RequestUrl")}"
            .renderer="${this.boundReqUrlRenderer}"
          ></vaadin-grid-column>
          <vaadin-grid-column
            resizable
            auto-width
            text-align="start"
            header="${p("logs.Parameters")}"
            .renderer="${this.boundParamRenderer}"
          ></vaadin-grid-column>
        </vaadin-grid>
        <backend-ai-list-status
          id="list-status"
          statusCondition="${this.listCondition}"
          message="${g("logs.NoLogToDisplay")}"
        ></backend-ai-list-status>
      </div>
      <div
        class="horizontal center-justified layout flex"
        style="padding: 10px;border-top:1px solid #ccc;"
      >
        <mwc-icon-button
          class="pagination"
          id="previous-page"
          icon="navigate_before"
          ?disabled="${1===this._currentPage}"
          @click="${e=>{this._updateItemsFromPage(e)}}"
        ></mwc-icon-button>
        <div class="pagination-label">
          ${this._currentPage} /
          ${Math.ceil(this._totalLogCount/this._pageSize)}
        </div>
        <mwc-icon-button
          class="pagination"
          id="next-page"
          icon="navigate_next"
          ?disabled="${this._totalLogCount<=this._pageSize*this._currentPage}"
          @click="${e=>{this._updateItemsFromPage(e)}}"
        ></mwc-icon-button>
      </div>
    `}};e([t({type:String})],f.prototype,"timestamp",void 0),e([t({type:String})],f.prototype,"errorType",void 0),e([t({type:String})],f.prototype,"requestUrl",void 0),e([t({type:String})],f.prototype,"statusCode",void 0),e([t({type:String})],f.prototype,"statusText",void 0),e([t({type:String})],f.prototype,"title",void 0),e([t({type:String})],f.prototype,"message",void 0),e([t({type:Array})],f.prototype,"logs",void 0),e([t({type:Array})],f.prototype,"_selected_items",void 0),e([t({type:String})],f.prototype,"listCondition",void 0),e([t({type:Object})],f.prototype,"_grid",void 0),e([t({type:Array})],f.prototype,"logView",void 0),e([t({type:Number})],f.prototype,"_pageSize",void 0),e([t({type:Number})],f.prototype,"_currentPage",void 0),e([t({type:Number})],f.prototype,"_totalLogCount",void 0),e([t({type:Object})],f.prototype,"boundTimeStampRenderer",void 0),e([t({type:Object})],f.prototype,"boundStatusRenderer",void 0),e([t({type:Object})],f.prototype,"boundErrTitleRenderer",void 0),e([t({type:Object})],f.prototype,"boundErrMsgRenderer",void 0),e([t({type:Object})],f.prototype,"boundErrTypeRenderer",void 0),e([t({type:Object})],f.prototype,"boundMethodRenderer",void 0),e([t({type:Object})],f.prototype,"boundReqUrlRenderer",void 0),e([t({type:Object})],f.prototype,"boundParamRenderer",void 0),e([i("#loading-spinner")],f.prototype,"spinner",void 0),e([i("#list-status")],f.prototype,"_listStatus",void 0),f=e([a("backend-ai-error-log-list")],f);let S=class extends s{constructor(){super(),this.lastSavedBootstrapScript="",this.supportLanguages=[{name:p("language.OSDefault"),code:"default"},{name:p("language.English"),code:"en"},{name:p("language.Korean"),code:"ko"},{name:p("language.Brazilian"),code:"pt-BR"},{name:p("language.Chinese"),code:"zh-CN"},{name:p("language.Chinese (Simplified)"),code:"zh-TW"},{name:p("language.French"),code:"fr"},{name:p("language.Finnish"),code:"fi"},{name:p("language.German"),code:"de"},{name:p("language.Greek"),code:"el"},{name:p("language.Indonesian"),code:"id"},{name:p("language.Italian"),code:"it"},{name:p("language.Japanese"),code:"ja"},{name:p("language.Mongolian"),code:"mn"},{name:p("language.Polish"),code:"pl"},{name:p("language.Portuguese"),code:"pt"},{name:p("language.Russian"),code:"ru"},{name:p("language.Spanish"),code:"es"},{name:p("language.Turkish"),code:"tr"},{name:p("language.Vietnamese"),code:"vi"}],this.beta_feature_panel=!1,this.shell_script_edit=!1,this.rcfile="",this.prevRcfile="",this.preferredSSHPort="",this.publicSSHkey="",this.rcfiles=[]}static get styles(){return[o,n,r,h,u,l`
        div.indicator,
        span.indicator {
          font-size: 9px;
          margin-right: 5px;
        }

        span[slot='title'] {
          font-weight: bold;
          margin-top: 15px !important;
          margin-bottom: 15px;
          display: inline-block;
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
          margin: 15px 10px;
          width: 360px;
        }

        .setting-desc {
          width: 300px;
        }

        .setting-button {
          width: 35px;
        }

        .setting-select-desc {
          width: auto;
          margin-right: 5px;
        }

        .setting-select {
          width: 135px;
        }

        .setting-text-desc {
          width: 260px;
        }

        .setting-text {
          width: 75px;
        }

        .ssh-keypair {
          margin-right: 10px;
          width: 450px;
          min-height: 100px;
          overflow-y: scroll;
          white-space: pre-wrap;
          word-wrap: break-word;
          font-size: 10px;
          scrollbar-width: none; /* firefox */
        }

        #bootstrap-dialog,
        #userconfig-dialog {
          --component-width: calc(100vw - 200px);
          --component-height: calc(100vh - 100px);
          --component-min-width: calc(100vw - 200px);
          --component-max-width: calc(100vw - 200px);
          --component-min-height: calc(100vh - 100px);
          --component-max-height: calc(100vh - 100px);
        }

        .terminal-area {
          height: calc(100vh - 300px);
        }

        mwc-select {
          width: 160px;
          font-family: var(--general-font-family);
          --mdc-typography-subtitle1-font-family: var(--general-font-family);
          --mdc-typography-subtitle1-font-size: 11px;
          --mdc-theme-primary: var(--general-sidebar-color);
          --mdc-select-fill-color: transparent;
          --mdc-select-label-ink-color: rgba(0, 0, 0, 0.75);
          --mdc-select-focused-dropdown-icon-color: var(
            --general-sidebar-color
          );
          --mdc-select-disabled-dropdown-icon-color: var(
            --general-sidebar-color
          );
          --mdc-select-idle-line-color: rgba(0, 0, 0, 0.42);
          --mdc-select-hover-line-color: var(--general-sidebar-color);
          --mdc-select-outlined-idle-border-color: var(--general-sidebar-color);
          --mdc-select-outlined-hover-border-color: var(
            --general-sidebar-color
          );
          --mdc-theme-surface: white;
          --mdc-list-vertical-padding: 5px;
          --mdc-list-side-padding: 25px;
        }

        mwc-select#select-rcfile-type {
          width: 300px;
          margin-bottom: 10px;
        }

        mwc-select#select-rcfile-type > mwc-list-item {
          width: 250px;
        }

        mwc-textarea {
          --mdc-theme-primary: var(--general-sidebar-color);
        }

        mwc-icon-button {
          color: #27824f;
        }

        mwc-button[outlined] {
          background-image: none;
          --mdc-button-outline-width: 2px;
          --mdc-button-disabled-outline-color: var(
            --general-button-background-color
          );
          --mdc-button-disabled-ink-color: var(
            --general-button-background-color
          );
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
        }

        mwc-button {
          margin: auto 10px;
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
        }

        mwc-button[unelevated] {
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
        }

        mwc-button.shell-button {
          margin: 5px;
          width: 260px;
        }

        ::-webkit-scrollbar {
          display: none; /* Chrome and Safari */
        }

        @media screen and (max-width: 500px) {
          #bootstrap-dialog,
          #userconfig-dialog {
            --component-min-width: 300px;
          }

          mwc-select#select-rcfile-type {
            width: 250px;
          }

          mwc-select#select-rcfile-type > mwc-list-item {
            width: 200px;
          }

          .setting-desc {
            width: 200px;
          }

          #language-setting {
            width: 160px;
          }
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}async _viewStateChanged(e){await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.preferredSSHPort=globalThis.backendaioptions.get("custom_ssh_port"),globalThis.backendaiclient.isAPIVersionCompatibleWith("v4.20191231")&&(this.shell_script_edit=!0,this.rcfile=".bashrc")})):(this.preferredSSHPort=globalThis.backendaioptions.get("custom_ssh_port"),globalThis.backendaiclient.isAPIVersionCompatibleWith("v4.20191231")&&(this.shell_script_edit=!0,this.rcfile=".bashrc")),this.userconfigDialog.addEventListener("dialog-closing-confirm",(()=>{const e=this.userSettingEditor.getValue(),t=this.rcfiles.findIndex((e=>e.path===this.rcfile));this.rcfiles[t].data!==e?(this.prevRcfile=this.rcfile,this._launchChangeCurrentEditorDialog()):(this.userconfigDialog.closeWithConfirmation=!1,this.userconfigDialog.hide())})))}toggleDesktopNotification(e){!1===e.target.selected?(globalThis.backendaioptions.set("desktop_notification",!1),this.notification.supportDesktopNotification=!1):(globalThis.backendaioptions.set("desktop_notification",!0),this.notification.supportDesktopNotification=!0)}toggleCompactSidebar(e){!1===e.target.selected?globalThis.backendaioptions.set("compact_sidebar",!1):globalThis.backendaioptions.set("compact_sidebar",!0)}togglePreserveLogin(e){!1===e.target.selected?globalThis.backendaioptions.set("preserve_login",!1):globalThis.backendaioptions.set("preserve_login",!0)}toggleAutoLogout(e){if(!1===e.target.selected){globalThis.backendaioptions.set("auto_logout",!1);const e=new CustomEvent("backend-ai-auto-logout",{detail:!1});document.dispatchEvent(e)}else{globalThis.backendaioptions.set("auto_logout",!0);const e=new CustomEvent("backend-ai-auto-logout",{detail:!0});document.dispatchEvent(e)}}toggleAutomaticUploadCheck(e){!1===e.target.selected?globalThis.backendaioptions.set("automatic_update_check",!1):(globalThis.backendaioptions.set("automatic_update_check",!0),globalThis.backendaioptions.set("automatic_update_count_trial",0))}setUserLanguage(e){if(e.target.selected.value!==globalThis.backendaioptions.get("language")){let t=e.target.selected.value;"default"===t&&(t=globalThis.navigator.language.split("-")[0]),globalThis.backendaioptions.set("language",e.target.selected.value),globalThis.backendaioptions.set("current_language",t),b(t),setTimeout((()=>{var e,t;this.languageSelect.selectedText=null===(t=null===(e=this.languageSelect.selected)||void 0===e?void 0:e.textContent)||void 0===t?void 0:t.trim()}),100)}}changePreferredSSHPort(e){const t=Number(e.target.value);if(t!==globalThis.backendaioptions.get("custom_ssh_port",""))if(0!==t&&t){if(t<1024||t>65534)return this.notification.text=g("usersettings.InvalidPortNumber"),void this.notification.show();globalThis.backendaioptions.set("custom_ssh_port",t)}else globalThis.backendaioptions.delete("custom_ssh_port")}toggleBetaFeature(e){!1===e.target.selected?(globalThis.backendaioptions.set("beta_feature",!1),this.beta_feature_panel=!1):(globalThis.backendaioptions.set("beta_feature",!0),this.beta_feature_panel=!0)}_fetchBootstrapScript(){return globalThis.backendaiclient.userConfig.get_bootstrap_script().then((e=>{const t=e||"";return this.lastSavedBootstrapScript=t,t})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=m.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _saveBootstrapScript(){const e=this.bootstrapEditor.getValue();if(this.lastSavedBootstrapScript===e)return this.notification.text=g("resourceGroup.NochangesMade"),void this.notification.show();this.spinner.show(),globalThis.backendaiclient.userConfig.update_bootstrap_script(e).then((e=>{this.notification.text=g("usersettings.BootstrapScriptUpdated"),this.notification.show(),this.spinner.hide()}))}async _saveBootstrapScriptAndCloseDialog(){await this._saveBootstrapScript(),this._hideBootstrapScriptDialog()}async _launchBootstrapScriptDialog(){const e=await this._fetchBootstrapScript();this.bootstrapEditor.setValue(e),this.bootstrapEditor.focus(),this.bootstrapDialog.show()}_hideBootstrapScriptDialog(){this.bootstrapDialog.hide()}async _editUserConfigScript(){this.rcfiles=await this._fetchUserConfigScript();[".bashrc",".zshrc",".tmux.conf.local",".vimrc",".Renviron"].map((e=>{const t=this.rcfiles.findIndex((t=>t.path===e));if(-1===t)this.rcfiles.push({path:e,data:""}),this.userSettingEditor.setValue("");else{const e=this.rcfiles[t].data;this.userSettingEditor.setValue(e)}}));[".tmux.conf"].forEach((e=>{const t=this.rcfiles.findIndex((t=>t.path===e));t>-1&&this.rcfiles.splice(t,1)}));const e=this.rcfiles.findIndex((e=>e.path===this.rcfile));if(-1!=e){const t=this.rcfiles[e].data;this.userSettingEditor.setValue(t)}else this.userSettingEditor.setValue("");this.userSettingEditor.focus(),this.spinner.hide(),this._toggleDeleteButton()}_fetchUserConfigScript(){return globalThis.backendaiclient.userConfig.get().then((e=>e||"")).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=m.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}async _saveUserConfigScript(e=this.rcfile){const t=this.userSettingEditor.getValue(),i=this.rcfiles.findIndex((t=>t.path===e));if(this.rcFileTypeSelect.items.length>0){const t=this.rcFileTypeSelect.items.find((t=>t.value===e));if(t){const e=this.rcFileTypeSelect.items.indexOf(t);this.rcFileTypeSelect.select(e)}}if(-1!=i)if(""===this.rcfiles[i].data){if(""===t)return this.spinner.hide(),this.notification.text=g("usersettings.DescNewUserConfigFileCreated"),void this.notification.show();globalThis.backendaiclient.userConfig.create(t,this.rcfiles[i].path).then((e=>{this.spinner.hide(),this.notification.text=g("usersettings.DescScriptCreated"),this.notification.show()})).catch((e=>{this.spinner.hide(),console.log(e),e&&e.message&&(this.notification.text=m.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}else{if(this.rcfiles[i].data===t)return this.notification.text=g("resourceGroup.NochangesMade"),void this.notification.show();if(""===t)return this.notification.text=g("usersettings.DescLetUserUpdateScriptWithNonEmptyValue"),void this.notification.show();await globalThis.backendaiclient.userConfig.update(t,e).then((e=>{this.notification.text=g("usersettings.DescScriptUpdated"),this.notification.show(),this.spinner.hide()})).catch((e=>{this.spinner.hide(),console.log(e),e&&e.message&&(this.notification.text=m.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}setTimeout((()=>{this._editUserConfigScript()}),200),this.spinner.show()}async _saveUserConfigScriptAndCloseDialog(){await this._saveUserConfigScript(),this._hideUserConfigScriptDialog()}_hideUserConfigScriptDialog(){this.userconfigDialog.hide()}_hideCurrentEditorChangeDialog(){this.changeCurrentEditorDialog.hide()}_updateSelectedRcFileName(e){if(this.rcFileTypeSelect.items.length>0){const t=this.rcFileTypeSelect.items.find((t=>t.value===e));if(t){const e=this.rcFileTypeSelect.items.indexOf(t),i=this.rcfiles[e].data;this.rcFileTypeSelect.select(e),this.userSettingEditor.setValue(i)}}}_changeCurrentEditorData(){const e=this.rcfiles.findIndex((e=>e.path===this.rcFileTypeSelect.value)),t=this.rcfiles[e].data;this.userSettingEditor.setValue(t)}_toggleRcFileName(){var e;this.prevRcfile=this.rcfile,this.rcfile=this.rcFileTypeSelect.value;let t=this.rcfiles.findIndex((e=>e.path===this.prevRcfile)),i=t>-1?this.rcfiles[t].data:"";const a=this.userSettingEditor.getValue();this.rcFileTypeSelect.layout(),this._toggleDeleteButton(),i!==a?this._launchChangeCurrentEditorDialog():(t=this.rcfiles.findIndex((e=>e.path===this.rcfile)),i=(null===(e=this.rcfiles[t])||void 0===e?void 0:e.data)?this.rcfiles[t].data:"",this.userSettingEditor.setValue(i))}_toggleDeleteButton(){var e,t;const i=this.rcfiles.findIndex((e=>e.path===this.rcfile));i>-1&&(this.deleteRcfileButton.disabled=!((null===(e=this.rcfiles[i])||void 0===e?void 0:e.data)&&(null===(t=this.rcfiles[i])||void 0===t?void 0:t.permission)))}async _deleteRcFile(e){e||(e=this.rcfile),e&&globalThis.backendaiclient.userConfig.delete(e).then((t=>{const i=g("usersettings.DescScriptDeleted")+e;this.notification.text=i,this.notification.show(),this.spinner.hide(),this._hideUserConfigScriptDialog()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=m.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))})),await setTimeout((()=>{this._editUserConfigScript()}),200)}async _deleteRcFileAll(){const e=this.rcfiles.filter((e=>""!==e.permission&&""!==e.data)).map((e=>{const t=e.path;return globalThis.backendaiclient.userConfig.delete(t)}));Promise.all(e).then((e=>{const t=g("usersettings.DescScriptAllDeleted");this.notification.text=t,this.notification.show(),this.spinner.hide()})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=m.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))})),await setTimeout((()=>{this._editUserConfigScript()}),200)}_createRcFile(e){e&&globalThis.backendaiclient.userConfig.create(e)}async _launchUserConfigDialog(){await this._editUserConfigScript(),this.userconfigDialog.closeWithConfirmation=!0,this.userconfigDialog.show()}_launchChangeCurrentEditorDialog(){this.changeCurrentEditorDialog.show()}_openSSHKeypairManagementDialog(){this.sshKeypairManagementDialog.show()}async _openSSHKeypairRefreshDialog(){globalThis.backendaiclient.fetchSSHKeypair().then((e=>{this.currentSSHPublicKeyInput.value=e.ssh_public_key?e.ssh_public_key:"",this.currentSSHPublicKeyInput.disabled=""===this.currentSSHPublicKeyInput.value,this.copyCurrentSSHPublicKeyButton.disabled=this.currentSSHPublicKeyInput.disabled,this.publicSSHkey=this.currentSSHPublicKeyInput.value?this.currentSSHPublicKeyInput.value:g("usersettings.NoExistingSSHKeypair"),this.sshKeypairManagementDialog.show()}))}_openSSHKeypairClearDialog(){this.clearSSHKeypairDialog.show()}_hideSSHKeypairGenerationDialog(){this.generateSSHKeypairDialog.hide();const e=this.sshPublicKeyInput.value;""!==e&&(this.currentSSHPublicKeyInput.value=e,this.copyCurrentSSHPublicKeyButton.disabled=!1)}_hideSSHKeypairDialog(){this.sshKeypairManagementDialog.hide()}_hideSSHKeypairClearDialog(){this.clearSSHKeypairDialog.hide()}async _refreshSSHKeypair(){globalThis.backendaiclient.refreshSSHKeypair().then((e=>{this.sshPublicKeyInput.value=e.ssh_public_key,this.sshPrivateKeyInput.value=e.ssh_private_key,this.generateSSHKeypairDialog.show()}))}_initManualSSHKeypairFormDialog(){this.enteredSSHPublicKeyInput.value="",this.enteredSSHPrivateKeyInput.value=""}_openSSHKeypairFormDialog(){this.sshKeypairFormDialog.show()}_hideSSHKeypairFormDialog(){this.sshKeypairFormDialog.hide()}_saveSSHKeypairFormDialog(){const e=this.enteredSSHPublicKeyInput.value,t=this.enteredSSHPrivateKeyInput.value;globalThis.backendaiclient.postSSHKeypair({pubkey:e,privkey:t}).then((e=>{this.notification.text=g("usersettings.SSHKeypairEnterManuallyFinished"),this.notification.show(),this._hideSSHKeypairFormDialog(),this._openSSHKeypairRefreshDialog()})).catch((e=>{e&&e.message&&(this.notification.text=m.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_clearCurrentSSHKeypair(){this._hideSSHKeypairClearDialog(),this._hideSSHKeypairGenerationDialog()}_discardCurrentEditorChange(){this._updateSelectedRcFileName(this.rcfile),this._hideCurrentEditorChangeDialog()}_saveCurrentEditorChange(){this._saveUserConfigScript(this.prevRcfile),this._updateSelectedRcFileName(this.rcfile),this._hideCurrentEditorChangeDialog()}_cancelCurrentEditorChange(){this._updateSelectedRcFileName(this.prevRcfile),this._hideCurrentEditorChangeDialog()}_copySSHKey(e){var t;if(""!==e){const i=(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector(e)).value;if(0==i.length)this.notification.text=g("usersettings.NoExistingSSHKeypair"),this.notification.show();else if(void 0!==navigator.clipboard)navigator.clipboard.writeText(i).then((()=>{this.notification.text=g("usersettings.SSHKeyClipboardCopy"),this.notification.show()}),(e=>{console.error("Could not copy text: ",e)}));else{const e=document.createElement("input");e.type="text",e.value=i,document.body.appendChild(e),e.select(),document.execCommand("copy"),document.body.removeChild(e)}}}render(){return d`
      <lablup-loading-spinner id="loading-spinner"></lablup-loading-spinner>
      <h3 class="horizontal center layout">
        <span>${p("usersettings.Preferences")}</span>
        <span class="flex"></span>
      </h3>
      <div class="horizontal wrap layout">
        <div class="horizontal layout wrap setting-item">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${p("usersettings.DesktopNotification")}</div>
            <div class="description">
              ${v("usersettings.DescDesktopNotification")}
            </div>
          </div>
          <div class="vertical center-justified layout setting-button flex end">
            <mwc-switch
              id="desktop-notification-switch"
              @click="${e=>this.toggleDesktopNotification(e)}"
              ?selected="${globalThis.backendaioptions.get("desktop_notification")}"
            ></mwc-switch>
          </div>
        </div>
        <div class="horizontal layout wrap setting-item">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${p("usersettings.UseCompactSidebar")}</div>
            <div class="description">
              ${v("usersettings.DescUseCompactSidebar")}
            </div>
          </div>
          <div class="vertical center-justified layout setting-button flex end">
            <mwc-switch
              id="compact-sidebar-switch"
              @click="${e=>this.toggleCompactSidebar(e)}"
              ?selected="${globalThis.backendaioptions.get("compact_sidebar")}"
            ></mwc-switch>
          </div>
        </div>
        <div class="horizontal layout wrap setting-item">
          <div
            class="vertical start start-justified layout setting-select-desc"
            id="language-setting"
          >
            <div class="title">${p("usersettings.Language")}</div>
            <div class="description">${v("usersettings.DescLanguage")}</div>
          </div>
          <div class="vertical center-justified layout setting-select flex end">
            <mwc-select
              id="ui-language"
              required
              outlined
              @selected="${e=>this.setUserLanguage(e)}"
            >
              ${this.supportLanguages.map((e=>d`
                  <mwc-list-item
                    value="${e.code}"
                    ?selected=${globalThis.backendaioptions.get("language")===e.code}
                  >
                    ${e.name}
                  </mwc-list-item>
                `))}
            </mwc-select>
          </div>
        </div>
        ${globalThis.isElectron?d`
              <div class="horizontal layout wrap setting-item">
                <div class="vertical start start-justified layout setting-desc">
                  <div class="title">
                    ${p("usersettings.KeepLoginSessionInformation")}
                  </div>
                  <div class="description">
                    ${v("usersettings.DescKeepLoginSessionInformation")}
                  </div>
                </div>
                <div
                  class="vertical center-justified layout setting-button flex end"
                >
                  <mwc-switch
                    id="preserve-login-switch"
                    @click="${e=>this.togglePreserveLogin(e)}"
                    ?selected="${globalThis.backendaioptions.get("preserve_login")}"
                  ></mwc-switch>
                </div>
              </div>
              <div class="horizontal layout wrap setting-item">
                <div
                  class="vertical start start-justified layout setting-text-desc"
                >
                  <div class="title">
                    ${p("usersettings.PreferredSSHPort")}
                  </div>
                  <div class="description">
                    ${v("usersettings.DescPreferredSSHPort")}
                  </div>
                </div>
                <div class="vertical center-justified layout setting-text">
                  <mwc-textfield
                    pattern="[0-9]*"
                    @change="${e=>this.changePreferredSSHPort(e)}"
                    value="${this.preferredSSHPort}"
                    validationMessage="${p("credential.validation.NumbersOnly")}"
                    auto-validate
                    maxLength="5"
                  ></mwc-textfield>
                </div>
              </div>
            `:d``}
        <div class="horizontal layout wrap setting-item">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${p("usersettings.SSHKeypairManagement")}</div>
            <div class="description">
              ${v("usersettings.DescSSHKeypairManagement")}
            </div>
          </div>
          <div class="vertical center-justified layout flex end">
            <mwc-icon-button
              id="ssh-keypair-details"
              icon="more"
              @click="${this._openSSHKeypairRefreshDialog}"
            ></mwc-icon-button>
          </div>
        </div>
        <div class="horizontal layout wrap setting-item">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${p("usersettings.AutomaticUpdateCheck")}</div>
            <div class="description">
              ${v("usersettings.DescAutomaticUpdateCheck")}
            </div>
          </div>
          <div class="vertical center-justified layout setting-button flex end">
            <mwc-switch
              id="automatic-update-check-switch"
              @click="${e=>this.toggleAutomaticUploadCheck(e)}"
              ?selected="${globalThis.backendaioptions.get("automatic_update_check")}"
            ></mwc-switch>
          </div>
        </div>
        <div class="horizontal layout wrap setting-item" style="display:none;">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${p("usersettings.BetaFeatures")}</div>
            <div class="description">
              ${v("usersettings.DescBetaFeatures")}
            </div>
          </div>
          <div class="vertical center-justified layout setting-button flex end">
            <mwc-switch
              id="beta-feature-switch"
              @click="${e=>this.toggleBetaFeature(e)}"
              ?selected="${globalThis.backendaioptions.get("beta_feature")}"
            ></mwc-switch>
          </div>
        </div>
        <div class="horizontal layout wrap setting-item">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${p("usersettings.AutoLogout")}</div>
            <div class="description">${v("usersettings.DescAutoLogout")}</div>
          </div>
          <div class="vertical center-justified layout setting-button flex end">
            <mwc-switch
              id="auto-logout-switch"
              @click="${e=>this.toggleAutoLogout(e)}"
              ?selected="${globalThis.backendaioptions.get("auto_logout",!1)}"
            ></mwc-switch>
          </div>
        </div>
        ${this.beta_feature_panel?d`
              <h3 class="horizontal center layout">
                <span>${p("usersettings.BetaFeatures")}</span>
                <span class="flex"></span>
              </h3>
              <div class="description">
                ${p("usersettings.DescNoBetaFeatures")}
              </div>
            `:d``}
      </div>
      ${this.shell_script_edit?d`
            <h3 class="horizontal center layout">
              <span>${p("usersettings.ShellEnvironments")}</span>
              <span class="flex"></span>
            </h3>
            <div class="horizontal wrap layout">
              <mwc-button
                class="shell-button"
                icon="edit"
                outlined
                label="${p("usersettings.EditBootstrapScript")}"
                @click="${()=>this._launchBootstrapScriptDialog()}"
              ></mwc-button>
              <mwc-button
                class="shell-button"
                icon="edit"
                outlined
                label="${p("usersettings.EditUserConfigScript")}"
                @click="${()=>this._launchUserConfigDialog()}"
              ></mwc-button>
            </div>
            <h3 class="horizontal center layout" style="display:none;">
              <span>${p("usersettings.PackageInstallation")}</span>
              <span class="flex"></span>
            </h3>
            <div class="horizontal wrap layout" style="display:none;">
              <div class="horizontal layout wrap setting-item">
                <div class="vertical center-justified layout setting-desc">
                  <div>TEST1</div>
                  <div class="description">This is description.</div>
                </div>
                <div
                  class="vertical center-justified layout setting-button flex end"
                >
                  <mwc-switch
                    id="register-new-image-switch"
                    disabled
                  ></mwc-switch>
                </div>
              </div>
            </div>
          `:d``}
      <backend-ai-dialog
        id="bootstrap-dialog"
        fixed
        backdrop
        scrollable
        blockScrolling
        persistent
      >
        <span slot="title">${p("usersettings.EditBootstrapScript")}</span>
        <div slot="content" class="vertical layout terminal-area">
          <div style="margin-bottom:1em">
            ${p("usersettings.BootstrapScriptDescription")}
          </div>
          <div style="background-color:#272823;height:100%;">
            <lablup-codemirror
              id="bootstrap-editor"
              mode="shell"
            ></lablup-codemirror>
          </div>
        </div>
        <div slot="footer" class="end-justified layout flex horizontal">
          <mwc-button
            id="discard-code"
            label="${p("button.Cancel")}"
            @click="${()=>this._hideBootstrapScriptDialog()}"
          ></mwc-button>
          <mwc-button
            unelevated
            id="save-code"
            label="${p("button.Save")}"
            @click="${()=>this._saveBootstrapScript()}"
          ></mwc-button>
          <mwc-button
            unelevated
            id="save-code-and-close"
            label="${p("button.SaveAndClose")}"
            @click="${()=>this._saveBootstrapScriptAndCloseDialog()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="userconfig-dialog"
        fixed
        backdrop
        scrollable
        blockScrolling
        persistent
        closeWithConfirmation
      >
        <span slot="title">
          ${p("usersettings.Edit_ShellScriptTitle_1")} ${this.rcfile}
          ${p("usersettings.Edit_ShellScriptTitle_2")}
        </span>
        <div slot="content" class="vertical layout terminal-area">
          <mwc-select
            id="select-rcfile-type"
            label="${p("usersettings.ConfigFilename")}"
            required
            outlined
            fixedMenuPosition
            validationMessage="${p("credential.validation.PleaseSelectOption")}"
            @selected="${()=>this._toggleRcFileName()}"
            helper=${p("dialog.warning.WillBeAppliedToNewSessions")}
          >
            ${this.rcfiles.map((e=>d`
                <mwc-list-item
                  id="${e.path}"
                  value="${e.path}"
                  ?selected=${this.rcfile===e.path}
                >
                  ${e.path}
                </mwc-list-item>
              `))}
          </mwc-select>
          <div style="background-color:#272823;height:100%;">
            <lablup-codemirror
              id="usersetting-editor"
              mode="shell"
            ></lablup-codemirror>
          </div>
        </div>
        <div slot="footer" class="end-justified layout flex horizontal">
          <mwc-button
            id="discard-code"
            label="${p("button.Cancel")}"
            @click="${()=>this._hideUserConfigScriptDialog()}"
          ></mwc-button>
          <mwc-button
            id="delete-rcfile"
            label="${p("button.Delete")}"
            @click="${()=>this._deleteRcFile()}"
          ></mwc-button>
          <mwc-button
            unelevated
            id="save-code"
            label="${p("button.Save")}"
            @click="${()=>this._saveUserConfigScript()}"
          ></mwc-button>
          <mwc-button
            unelevated
            id="save-code-and-close"
            label="${p("button.SaveAndClose")}"
            @click="${()=>this._saveUserConfigScriptAndCloseDialog()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="change-current-editor-dialog"
        noclosebutton
        fixed
        backdrop
        scrollable
        blockScrolling
        persistent
        style="border-bottom:none;"
      >
        <div slot="title">
          ${p("usersettings.DialogDiscardOrSave",{File:()=>this.prevRcfile})}
        </div>
        <div slot="content">${p("usersettings.DialogNoSaveNoPreserve")}</div>
        <div
          slot="footer"
          style="border-top:none;"
          class="end-justified layout flex horizontal"
        >
          <mwc-button
            id="cancel-editor"
            label="${p("button.Discard")}"
            @click="${()=>this._discardCurrentEditorChange()}"
          ></mwc-button>
          <mwc-button
            unelevated
            id="save-editor-data"
            label="${p("button.Save")}"
            @click="${()=>this._saveCurrentEditorChange()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="ssh-keypair-management-dialog"
        fixed
        backdrop
        persistent
      >
        <span slot="title">${p("usersettings.SSHKeypairManagement")}</span>
        <div slot="content" style="max-width:500px">
          <span slot="title">${p("usersettings.CurrentSSHPublicKey")}</span>
          <mwc-textarea
            outlined
            readonly
            class="ssh-keypair"
            id="current-ssh-public-key"
            style="width:430px; height:270px;"
            value="${this.publicSSHkey}"
          ></mwc-textarea>
          <mwc-icon-button
            id="copy-current-ssh-public-key-button"
            icon="content_copy"
            @click="${()=>this._copySSHKey("#current-ssh-public-key")}"
          ></mwc-icon-button>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            label="${p("button.Close")}"
            @click="${this._hideSSHKeypairDialog}"
          ></mwc-button>
          <mwc-button
            unelevated
            label="${p("button.Generate")}"
            @click="${this._refreshSSHKeypair}"
          ></mwc-button>
          <mwc-button
            unelevated
            label="${p("button.EnterManually")}"
            @click="${()=>{this._initManualSSHKeypairFormDialog(),this._openSSHKeypairFormDialog()}}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog
        id="generate-ssh-keypair-dialog"
        fixed
        persistent
        noclosebutton
      >
        <span slot="title">${p("usersettings.SSHKeypairGeneration")}</span>
        <div slot="content" style="max-width:500px;">
          <div class="vertical layout" style="display:inline-block;">
            <span slot="title">${p("usersettings.PublicKey")}</span>
            <div class="horizontal layout flex">
              <mwc-textarea
                class="ssh-keypair"
                id="ssh-public-key"
                outlined
                readonly
              ></mwc-textarea>
              <mwc-icon-button
                icon="content_copy"
                @click="${()=>this._copySSHKey("#ssh-public-key")}"
              ></mwc-icon-button>
            </div>
            <span slot="title">${p("usersettings.PrivateKey")}</span>
            <div class="horizontal layout flex">
              <mwc-textarea
                class="ssh-keypair"
                id="ssh-private-key"
                outlined
                readonly
              ></mwc-textarea>
              <mwc-icon-button
                icon="content_copy"
                @click="${()=>this._copySSHKey("#ssh-private-key")}"
              ></mwc-icon-button>
            </div>
            <div style="color:crimson">
              ${p("usersettings.SSHKeypairGenerationWarning")}
            </div>
          </div>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            label="${p("button.Close")}"
            @click="${this._openSSHKeypairClearDialog}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="clear-ssh-keypair-dialog" fixed persistent>
        <span slot="title">${p("usersettings.ClearSSHKeypairInput")}</span>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            outlined
            label="${p("button.No")}"
            @click="${this._hideSSHKeypairClearDialog}"
          ></mwc-button>
          <mwc-button
            unelevated
            label="${p("button.Yes")}"
            @click="${this._clearCurrentSSHKeypair}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="ssh-keypair-form-dialog" fixed persistent>
        <span slot="title">${p("usersettings.SSHKeypairEnterManually")}</span>
        <div slot="content" style="max-width:500px;">
          <div class="vertical layout" style="display:inline-block;">
            <span slot="title">${p("usersettings.PublicKey")}</span>
            <div class="horizontal layout flex">
              <mwc-textarea
                class="ssh-keypair"
                id="entered-ssh-public-key"
                outlined
              ></mwc-textarea>
            </div>
            <span slot="title">${p("usersettings.PrivateKey")}</span>
            <div class="horizontal layout flex">
              <mwc-textarea
                class="ssh-keypair"
                id="entered-ssh-private-key"
                outlined
              ></mwc-textarea>
            </div>
          </div>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            outlined
            label="${p("button.Cancel")}"
            @click="${this._hideSSHKeypairFormDialog}"
          ></mwc-button>
          <mwc-button
            unelevated
            label="${p("button.Save")}"
            @click="${this._saveSSHKeypairFormDialog}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};e([t({type:Object})],S.prototype,"notification",void 0),e([t({type:Array})],S.prototype,"supportLanguages",void 0),e([t({type:Boolean})],S.prototype,"beta_feature_panel",void 0),e([t({type:Boolean})],S.prototype,"shell_script_edit",void 0),e([t({type:Array})],S.prototype,"rcfiles",void 0),e([t({type:String})],S.prototype,"rcfile",void 0),e([t({type:String})],S.prototype,"prevRcfile",void 0),e([t({type:String})],S.prototype,"preferredSSHPort",void 0),e([t({type:String})],S.prototype,"publicSSHkey",void 0),e([i("#loading-spinner")],S.prototype,"spinner",void 0),e([i("#bootstrap-editor")],S.prototype,"bootstrapEditor",void 0),e([i("#usersetting-editor")],S.prototype,"userSettingEditor",void 0),e([i("#select-rcfile-type")],S.prototype,"rcFileTypeSelect",void 0),e([i("#ssh-public-key")],S.prototype,"sshPublicKeyInput",void 0),e([i("#ssh-private-key")],S.prototype,"sshPrivateKeyInput",void 0),e([i("#current-ssh-public-key")],S.prototype,"currentSSHPublicKeyInput",void 0),e([i("#copy-current-ssh-public-key-button")],S.prototype,"copyCurrentSSHPublicKeyButton",void 0),e([i("#bootstrap-dialog")],S.prototype,"bootstrapDialog",void 0),e([i("#change-current-editor-dialog")],S.prototype,"changeCurrentEditorDialog",void 0),e([i("#userconfig-dialog")],S.prototype,"userconfigDialog",void 0),e([i("#ssh-keypair-management-dialog")],S.prototype,"sshKeypairManagementDialog",void 0),e([i("#clear-ssh-keypair-dialog")],S.prototype,"clearSSHKeypairDialog",void 0),e([i("#generate-ssh-keypair-dialog")],S.prototype,"generateSSHKeypairDialog",void 0),e([i("#ssh-keypair-form-dialog")],S.prototype,"sshKeypairFormDialog",void 0),e([i("#entered-ssh-public-key")],S.prototype,"enteredSSHPublicKeyInput",void 0),e([i("#entered-ssh-private-key")],S.prototype,"enteredSSHPrivateKeyInput",void 0),e([i("#ui-language")],S.prototype,"languageSelect",void 0),e([i("#delete-rcfile")],S.prototype,"deleteRcfileButton",void 0),S=e([a("backend-ai-usersettings-general-list")],S);let w=class extends s{constructor(){super(),this.images=Object(),this.options=Object(),this._activeTab=Object(),this.logGrid=Object(),this.options={automatic_image_update:!1,cuda_gpu:!1,cuda_fgpu:!1,rocm_gpu:!1,tpu:!1,scheduler:"fifo"}}static get is(){return"backend-ai-usersettings-view"}static get styles(){return[o,n,r,h,u,l`
        div.spinner,
        span.spinner {
          font-size: 9px;
          margin-right: 5px;
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
          --mdc-tab-text-label-color-default: var(
            --general-tabbar-tab-disabled-color
          );
        }

        mwc-button {
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
        }

        mwc-button[unelevated] {
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
        }

        mwc-button[outlined] {
          background-image: none;
          --mdc-button-outline-width: 2px;
          --mdc-button-disabled-outline-color: var(
            --general-button-background-color
          );
          --mdc-button-disabled-ink-color: var(
            --general-button-background-color
          );
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
        }

        mwc-button.log {
          margin: 0px 10px;
        }

        .outer-space {
          margin: 20px;
        }

        @media screen and (max-width: 750px) {
          mwc-button {
            width: auto;
          }
          mwc-button > span {
            display: none;
          }
        }
      `]}render(){return d`
      <link rel="stylesheet" href="resources/custom.css" />
      <lablup-loading-spinner id="loading-spinner"></lablup-loading-spinner>
      <lablup-activity-panel noheader narrow autowidth>
        <div slot="message">
          <h3 class="tab horizontal wrap layout">
            <mwc-tab-bar>
              <mwc-tab
                title="general"
                label="${p("usersettings.General")}"
                @click="${e=>this._showTab(e.target)}"
              ></mwc-tab>
              <mwc-tab
                title="logs"
                label="${p("usersettings.Logs")}"
                @click="${e=>this._showTab(e.target)}"
              ></mwc-tab>
            </mwc-tab-bar>
          </h3>
          <div id="general" class="item tab-content outer-space">
            <backend-ai-usersettings-general-list
              active="true"
            ></backend-ai-usersettings-general-list>
          </div>
          <div id="logs" class="item tab-content" style="display:none;">
            <h3 class="horizontal center layout outer-space">
              <span>${p("logs.LogMessages")}</span>
              <span class="mini" style="font-size:13px;padding-left:15px;">
                ${p("logs.UpTo3000Logs")}
              </span>
              <span class="flex"></span>
              <mwc-button
                class="log"
                icon="refresh"
                @click="${()=>this._refreshLogs()}"
              >
                <span>${p("button.Refresh")}</span>
              </mwc-button>
              <mwc-button
                class="log"
                icon="delete"
                raised
                @click="${()=>this._showClearLogsDialog()}"
              >
                <span>${p("button.ClearLogs")}</span>
              </mwc-button>
            </h3>
            <backend-ai-error-log-list
              active="true"
            ></backend-ai-error-log-list>
          </div>
        </div>
      </lablup-activity-panel>
      <backend-ai-dialog
        id="clearlogs-dialog"
        fixed
        backdrop
        scrollable
        blockScrolling
      >
        <span slot="title">${p("dialog.warning.LogDeletion")}</span>
        <div slot="content">${p("dialog.warning.CannotBeUndone")}</div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            class="operation"
            id="discard-removal"
            label="${p("button.No")}"
            @click="${()=>this._hideClearLogsDialog()}"
          ></mwc-button>
          <mwc-button
            unelevated
            class="operation"
            id="apply-removal"
            label="${p("button.Yes")}"
            @click="${()=>this._removeLogMessage()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}firstUpdated(){void 0===globalThis.backendaiclient||null===globalThis.backendaiclient?document.addEventListener("backend-ai-connected",(()=>{this.updateSettings()}),!0):this.updateSettings(),this.notification=globalThis.lablupNotification,document.addEventListener("backend-ai-usersettings-logs",(()=>{this._viewStateChanged(!0)})),document.addEventListener("backend-ai-usersettings",(()=>{this._viewStateChanged(!0)}))}async _viewStateChanged(e){const t=y.getState().app.params.tab;t&&"logs"===t?globalThis.setTimeout((()=>{var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector('mwc-tab[title="logs"]')).click()}),0):globalThis.setTimeout((()=>{var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector('mwc-tab[title="general"]')).click()}),0)}updateSettings(){}_hideClearLogsDialog(){this.clearLogsDialog.hide()}_removeLogMessage(){localStorage.getItem("backendaiwebui.logs")&&localStorage.removeItem("backendaiwebui.logs");const e=new CustomEvent("log-message-clear",{});document.dispatchEvent(e),localStorage.getItem("backendaiwebui.logs"),this.clearLogsDialog.hide(),this.notification.text=g("logs.LogMessageRemoved"),this.notification.show(),this.spinner.hide()}_showClearLogsDialog(){this.clearLogsDialog.show()}_refreshLogs(){this.logGrid=JSON.parse(localStorage.getItem("backendaiwebui.logs")||"{}");const e=new CustomEvent("log-message-refresh",this.logGrid);document.dispatchEvent(e)}_showTab(e){var t,i;const a=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".tab-content");for(let e=0;e<a.length;e++)a[e].style.display="none";this._activeTab=e.title,"logs"===this._activeTab&&this._refreshLogs(),(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+e.title)).style.display="block"}};e([t({type:Object})],w.prototype,"images",void 0),e([t({type:Object})],w.prototype,"options",void 0),e([t({type:Object})],w.prototype,"_activeTab",void 0),e([t({type:Object})],w.prototype,"logGrid",void 0),e([i("#loading-spinner")],w.prototype,"spinner",void 0),e([i("#clearlogs-dialog")],w.prototype,"clearLogsDialog",void 0),w=e([a("backend-ai-usersettings-view")],w);
