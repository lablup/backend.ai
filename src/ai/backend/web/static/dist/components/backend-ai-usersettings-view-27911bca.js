import{_ as t,n as e,b as i,e as a,B as s,t as o,c as n,I as l,a as r,q as c,d,i as p,O as h,g as u,f as g,x as b,h as v,j as m}from"./backend-ai-webui-951d3157.js";import"./backend-ai-list-status-97faa3e2.js";import"./lablup-codemirror-b99580d8.js";import"./lablup-loading-spinner-c8fd9cda.js";import"./mwc-switch-dbe2f230.js";import"./lablup-activity-panel-19b0435c.js";import"./mwc-tab-bar-96f06601.js";let y=class extends s{constructor(){super(),this.lastSavedBootstrapScript="",this.supportLanguages=[{name:o("language.OSDefault"),code:"default"},{name:o("language.English"),code:"en"},{name:o("language.Korean"),code:"ko"},{name:o("language.Brazilian"),code:"pt-BR"},{name:o("language.Chinese"),code:"zh-CN"},{name:o("language.Chinese (Simplified)"),code:"zh-TW"},{name:o("language.French"),code:"fr"},{name:o("language.Finnish"),code:"fi"},{name:o("language.German"),code:"de"},{name:o("language.Greek"),code:"el"},{name:o("language.Indonesian"),code:"id"},{name:o("language.Italian"),code:"it"},{name:o("language.Japanese"),code:"ja"},{name:o("language.Mongolian"),code:"mn"},{name:o("language.Polish"),code:"pl"},{name:o("language.Portuguese"),code:"pt"},{name:o("language.Russian"),code:"ru"},{name:o("language.Spanish"),code:"es"},{name:o("language.Turkish"),code:"tr"},{name:o("language.Vietnamese"),code:"vi"}],this.beta_feature_panel=!1,this.shell_script_edit=!1,this.rcfile="",this.prevRcfile="",this.preferredSSHPort="",this.publicSSHkey="",this.isOpenMyKeypairInfoDialog=!1,this.rcfiles=[]}static get styles(){return[n,l,r,c,d,p`
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
      `]}firstUpdated(){this.notification=globalThis.lablupNotification}async _viewStateChanged(t){await this.updateComplete,!1!==t&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.preferredSSHPort=globalThis.backendaioptions.get("custom_ssh_port"),globalThis.backendaiclient.isAPIVersionCompatibleWith("v4.20191231")&&(this.shell_script_edit=!0,this.rcfile=".bashrc")})):(this.preferredSSHPort=globalThis.backendaioptions.get("custom_ssh_port"),globalThis.backendaiclient.isAPIVersionCompatibleWith("v4.20191231")&&(this.shell_script_edit=!0,this.rcfile=".bashrc")),this.userconfigDialog.addEventListener("dialog-closing-confirm",(()=>{const t=this.userSettingEditor.getValue(),e=this.rcfiles.findIndex((t=>t.path===this.rcfile));this.rcfiles[e].data!==t?(this.prevRcfile=this.rcfile,this._launchChangeCurrentEditorDialog()):(this.userconfigDialog.closeWithConfirmation=!1,this.userconfigDialog.hide())})))}toggleDesktopNotification(t){!1===t.target.selected?(globalThis.backendaioptions.set("desktop_notification",!1),this.notification.supportDesktopNotification=!1):(globalThis.backendaioptions.set("desktop_notification",!0),this.notification.supportDesktopNotification=!0)}toggleCompactSidebar(t){!1===t.target.selected?globalThis.backendaioptions.set("compact_sidebar",!1):globalThis.backendaioptions.set("compact_sidebar",!0)}togglePreserveLogin(t){!1===t.target.selected?globalThis.backendaioptions.set("preserve_login",!1):globalThis.backendaioptions.set("preserve_login",!0)}toggleAutoLogout(t){if(!1===t.target.selected){globalThis.backendaioptions.set("auto_logout",!1);const t=new CustomEvent("backend-ai-auto-logout",{detail:!1});document.dispatchEvent(t)}else{globalThis.backendaioptions.set("auto_logout",!0);const t=new CustomEvent("backend-ai-auto-logout",{detail:!0});document.dispatchEvent(t)}}toggleAutomaticUploadCheck(t){!1===t.target.selected?globalThis.backendaioptions.set("automatic_update_check",!1):(globalThis.backendaioptions.set("automatic_update_check",!0),globalThis.backendaioptions.set("automatic_update_count_trial",0))}setUserLanguage(t){if(t.target.selected.value!==globalThis.backendaioptions.get("language")){let e=t.target.selected.value;"default"===e&&(e=globalThis.navigator.language.split("-")[0]),globalThis.backendaioptions.set("language",t.target.selected.value),globalThis.backendaioptions.set("current_language",e),h(e),setTimeout((()=>{var t,e;this.languageSelect.selectedText=null===(e=null===(t=this.languageSelect.selected)||void 0===t?void 0:t.textContent)||void 0===e?void 0:e.trim()}),100)}}changePreferredSSHPort(t){const e=Number(t.target.value);if(e!==globalThis.backendaioptions.get("custom_ssh_port",""))if(0!==e&&e){if(e<1024||e>65534)return this.notification.text=u("usersettings.InvalidPortNumber"),void this.notification.show();globalThis.backendaioptions.set("custom_ssh_port",e)}else globalThis.backendaioptions.delete("custom_ssh_port")}toggleBetaFeature(t){!1===t.target.selected?(globalThis.backendaioptions.set("beta_feature",!1),this.beta_feature_panel=!1):(globalThis.backendaioptions.set("beta_feature",!0),this.beta_feature_panel=!0)}_fetchBootstrapScript(){return globalThis.backendaiclient.userConfig.get_bootstrap_script().then((t=>{const e=t||"";return this.lastSavedBootstrapScript=e,e})).catch((t=>{console.log(t),t&&t.message&&(this.notification.text=g.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))}))}async _saveBootstrapScript(){const t=this.bootstrapEditor.getValue();if(this.lastSavedBootstrapScript===t)return this.notification.text=u("resourceGroup.NochangesMade"),void this.notification.show();this.spinner.show(),globalThis.backendaiclient.userConfig.update_bootstrap_script(t).then((t=>{this.notification.text=u("usersettings.BootstrapScriptUpdated"),this.notification.show(),this.spinner.hide()}))}async _saveBootstrapScriptAndCloseDialog(){await this._saveBootstrapScript(),this._hideBootstrapScriptDialog()}async _launchBootstrapScriptDialog(){const t=await this._fetchBootstrapScript();this.bootstrapEditor.setValue(t),this.bootstrapEditor.focus(),this.bootstrapDialog.show()}_hideBootstrapScriptDialog(){this.bootstrapDialog.hide()}async _editUserConfigScript(){this.rcfiles=await this._fetchUserConfigScript();[".bashrc",".zshrc",".tmux.conf.local",".vimrc",".Renviron"].map((t=>{const e=this.rcfiles.findIndex((e=>e.path===t));if(-1===e)this.rcfiles.push({path:t,data:""}),this.userSettingEditor.setValue("");else{const t=this.rcfiles[e].data;this.userSettingEditor.setValue(t)}}));[".tmux.conf"].forEach((t=>{const e=this.rcfiles.findIndex((e=>e.path===t));e>-1&&this.rcfiles.splice(e,1)}));const t=this.rcfiles.findIndex((t=>t.path===this.rcfile));if(-1!=t){const e=this.rcfiles[t].data;this.userSettingEditor.setValue(e)}else this.userSettingEditor.setValue("");this.userSettingEditor.focus(),this.spinner.hide(),this._toggleDeleteButton()}_fetchUserConfigScript(){return globalThis.backendaiclient.userConfig.get().then((t=>t||"")).catch((t=>{console.log(t),t&&t.message&&(this.notification.text=g.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))}))}async _saveUserConfigScript(t=this.rcfile){const e=this.userSettingEditor.getValue(),i=this.rcfiles.findIndex((e=>e.path===t));if(this.rcFileTypeSelect.items.length>0){const e=this.rcFileTypeSelect.items.find((e=>e.value===t));if(e){const t=this.rcFileTypeSelect.items.indexOf(e);this.rcFileTypeSelect.select(t)}}if(-1!=i)if(""===this.rcfiles[i].data){if(""===e)return this.spinner.hide(),this.notification.text=u("usersettings.DescNewUserConfigFileCreated"),void this.notification.show();globalThis.backendaiclient.userConfig.create(e,this.rcfiles[i].path).then((t=>{this.spinner.hide(),this.notification.text=u("usersettings.DescScriptCreated"),this.notification.show()})).catch((t=>{this.spinner.hide(),console.log(t),t&&t.message&&(this.notification.text=g.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))}))}else{if(this.rcfiles[i].data===e)return this.notification.text=u("resourceGroup.NochangesMade"),void this.notification.show();if(""===e)return this.notification.text=u("usersettings.DescLetUserUpdateScriptWithNonEmptyValue"),void this.notification.show();await globalThis.backendaiclient.userConfig.update(e,t).then((t=>{this.notification.text=u("usersettings.DescScriptUpdated"),this.notification.show(),this.spinner.hide()})).catch((t=>{this.spinner.hide(),console.log(t),t&&t.message&&(this.notification.text=g.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))}))}setTimeout((()=>{this._editUserConfigScript()}),200),this.spinner.show()}async _saveUserConfigScriptAndCloseDialog(){await this._saveUserConfigScript(),this._hideUserConfigScriptDialog()}_hideUserConfigScriptDialog(){this.userconfigDialog.hide()}_hideCurrentEditorChangeDialog(){this.changeCurrentEditorDialog.hide()}_updateSelectedRcFileName(t){if(this.rcFileTypeSelect.items.length>0){const e=this.rcFileTypeSelect.items.find((e=>e.value===t));if(e){const t=this.rcFileTypeSelect.items.indexOf(e),i=this.rcfiles[t].data;this.rcFileTypeSelect.select(t),this.userSettingEditor.setValue(i)}}}_changeCurrentEditorData(){const t=this.rcfiles.findIndex((t=>t.path===this.rcFileTypeSelect.value)),e=this.rcfiles[t].data;this.userSettingEditor.setValue(e)}_toggleRcFileName(){var t;this.prevRcfile=this.rcfile,this.rcfile=this.rcFileTypeSelect.value;let e=this.rcfiles.findIndex((t=>t.path===this.prevRcfile)),i=e>-1?this.rcfiles[e].data:"";const a=this.userSettingEditor.getValue();this.rcFileTypeSelect.layout(),this._toggleDeleteButton(),i!==a?this._launchChangeCurrentEditorDialog():(e=this.rcfiles.findIndex((t=>t.path===this.rcfile)),i=(null===(t=this.rcfiles[e])||void 0===t?void 0:t.data)?this.rcfiles[e].data:"",this.userSettingEditor.setValue(i))}_toggleDeleteButton(){var t,e;const i=this.rcfiles.findIndex((t=>t.path===this.rcfile));i>-1&&(this.deleteRcfileButton.disabled=!((null===(t=this.rcfiles[i])||void 0===t?void 0:t.data)&&(null===(e=this.rcfiles[i])||void 0===e?void 0:e.permission)))}async _deleteRcFile(t){t||(t=this.rcfile),t&&globalThis.backendaiclient.userConfig.delete(t).then((e=>{const i=u("usersettings.DescScriptDeleted")+t;this.notification.text=i,this.notification.show(),this.spinner.hide(),this._hideUserConfigScriptDialog()})).catch((t=>{console.log(t),t&&t.message&&(this.notification.text=g.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))})),await setTimeout((()=>{this._editUserConfigScript()}),200)}async _deleteRcFileAll(){const t=this.rcfiles.filter((t=>""!==t.permission&&""!==t.data)).map((t=>{const e=t.path;return globalThis.backendaiclient.userConfig.delete(e)}));Promise.all(t).then((t=>{const e=u("usersettings.DescScriptAllDeleted");this.notification.text=e,this.notification.show(),this.spinner.hide()})).catch((t=>{console.log(t),t&&t.message&&(this.notification.text=g.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))})),await setTimeout((()=>{this._editUserConfigScript()}),200)}_createRcFile(t){t&&globalThis.backendaiclient.userConfig.create(t)}async _launchUserConfigDialog(){await this._editUserConfigScript(),this.userconfigDialog.closeWithConfirmation=!0,this.userconfigDialog.show()}_launchChangeCurrentEditorDialog(){this.changeCurrentEditorDialog.show()}_openSSHKeypairManagementDialog(){this.sshKeypairManagementDialog.show()}async _openSSHKeypairRefreshDialog(){globalThis.backendaiclient.fetchSSHKeypair().then((t=>{this.currentSSHPublicKeyInput.value=t.ssh_public_key?t.ssh_public_key:"",this.currentSSHPublicKeyInput.disabled=""===this.currentSSHPublicKeyInput.value,this.copyCurrentSSHPublicKeyButton.disabled=this.currentSSHPublicKeyInput.disabled,this.publicSSHkey=this.currentSSHPublicKeyInput.value?this.currentSSHPublicKeyInput.value:u("usersettings.NoExistingSSHKeypair"),this.sshKeypairManagementDialog.show()}))}_openSSHKeypairClearDialog(){this.clearSSHKeypairDialog.show()}_hideSSHKeypairGenerationDialog(){this.generateSSHKeypairDialog.hide();const t=this.sshPublicKeyInput.value;""!==t&&(this.currentSSHPublicKeyInput.value=t,this.copyCurrentSSHPublicKeyButton.disabled=!1)}_hideSSHKeypairDialog(){this.sshKeypairManagementDialog.hide()}_hideSSHKeypairClearDialog(){this.clearSSHKeypairDialog.hide()}async _refreshSSHKeypair(){globalThis.backendaiclient.refreshSSHKeypair().then((t=>{this.sshPublicKeyInput.value=t.ssh_public_key,this.sshPrivateKeyInput.value=t.ssh_private_key,this.generateSSHKeypairDialog.show()}))}_initManualSSHKeypairFormDialog(){this.enteredSSHPublicKeyInput.value="",this.enteredSSHPrivateKeyInput.value=""}_openSSHKeypairFormDialog(){this.sshKeypairFormDialog.show()}_hideSSHKeypairFormDialog(){this.sshKeypairFormDialog.hide()}_saveSSHKeypairFormDialog(){const t=this.enteredSSHPublicKeyInput.value,e=this.enteredSSHPrivateKeyInput.value;globalThis.backendaiclient.postSSHKeypair({pubkey:t,privkey:e}).then((t=>{this.notification.text=u("usersettings.SSHKeypairEnterManuallyFinished"),this.notification.show(),this._hideSSHKeypairFormDialog(),this._openSSHKeypairRefreshDialog()})).catch((t=>{t&&t.message&&(this.notification.text=g.relieve(t.title),this.notification.detail=t.message,this.notification.show(!0,t))}))}_clearCurrentSSHKeypair(){this._hideSSHKeypairClearDialog(),this._hideSSHKeypairGenerationDialog()}_openMyKeypairDialog(){this.isOpenMyKeypairInfoDialog=!0}_discardCurrentEditorChange(){this._updateSelectedRcFileName(this.rcfile),this._hideCurrentEditorChangeDialog()}_saveCurrentEditorChange(){this._saveUserConfigScript(this.prevRcfile),this._updateSelectedRcFileName(this.rcfile),this._hideCurrentEditorChangeDialog()}_cancelCurrentEditorChange(){this._updateSelectedRcFileName(this.prevRcfile),this._hideCurrentEditorChangeDialog()}_copySSHKey(t){var e;if(""!==t){const i=(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector(t)).value;if(0==i.length)this.notification.text=u("usersettings.NoExistingSSHKeypair"),this.notification.show();else if(void 0!==navigator.clipboard)navigator.clipboard.writeText(i).then((()=>{this.notification.text=u("usersettings.SSHKeyClipboardCopy"),this.notification.show()}),(t=>{console.error("Could not copy text: ",t)}));else{const t=document.createElement("input");t.type="text",t.value=i,document.body.appendChild(t),t.select(),document.execCommand("copy"),document.body.removeChild(t)}}}render(){return b`
      <lablup-loading-spinner id="loading-spinner"></lablup-loading-spinner>
      <h3 class="horizontal center layout">
        <span>${o("usersettings.Preferences")}</span>
        <span class="flex"></span>
      </h3>
      <div class="horizontal wrap layout">
        <div class="horizontal layout wrap setting-item">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${o("usersettings.DesktopNotification")}</div>
            <div class="description">
              ${v("usersettings.DescDesktopNotification")}
            </div>
          </div>
          <div class="vertical center-justified layout setting-button flex end">
            <mwc-switch
              id="desktop-notification-switch"
              @click="${t=>this.toggleDesktopNotification(t)}"
              ?selected="${globalThis.backendaioptions.get("desktop_notification")}"
            ></mwc-switch>
          </div>
        </div>
        <div class="horizontal layout wrap setting-item">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${o("usersettings.UseCompactSidebar")}</div>
            <div class="description">
              ${v("usersettings.DescUseCompactSidebar")}
            </div>
          </div>
          <div class="vertical center-justified layout setting-button flex end">
            <mwc-switch
              id="compact-sidebar-switch"
              @click="${t=>this.toggleCompactSidebar(t)}"
              ?selected="${globalThis.backendaioptions.get("compact_sidebar")}"
            ></mwc-switch>
          </div>
        </div>
        <div class="horizontal layout wrap setting-item">
          <div
            class="vertical start start-justified layout setting-select-desc"
            id="language-setting"
          >
            <div class="title">${o("usersettings.Language")}</div>
            <div class="description">${v("usersettings.DescLanguage")}</div>
          </div>
          <div class="vertical center-justified layout setting-select flex end">
            <mwc-select
              id="ui-language"
              required
              outlined
              @selected="${t=>this.setUserLanguage(t)}"
            >
              ${this.supportLanguages.map((t=>b`
                  <mwc-list-item
                    value="${t.code}"
                    ?selected=${globalThis.backendaioptions.get("language")===t.code}
                  >
                    ${t.name}
                  </mwc-list-item>
                `))}
            </mwc-select>
          </div>
        </div>
        ${globalThis.isElectron?b`
              <div class="horizontal layout wrap setting-item">
                <div class="vertical start start-justified layout setting-desc">
                  <div class="title">
                    ${o("usersettings.KeepLoginSessionInformation")}
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
                    @click="${t=>this.togglePreserveLogin(t)}"
                    ?selected="${globalThis.backendaioptions.get("preserve_login")}"
                  ></mwc-switch>
                </div>
              </div>
              <div class="horizontal layout wrap setting-item">
                <div
                  class="vertical start start-justified layout setting-text-desc"
                >
                  <div class="title">
                    ${o("usersettings.PreferredSSHPort")}
                  </div>
                  <div class="description">
                    ${v("usersettings.DescPreferredSSHPort")}
                  </div>
                </div>
                <div class="vertical center-justified layout setting-text">
                  <mwc-textfield
                    pattern="[0-9]*"
                    @change="${t=>this.changePreferredSSHPort(t)}"
                    value="${this.preferredSSHPort}"
                    validationMessage="${o("credential.validation.NumbersOnly")}"
                    auto-validate
                    maxLength="5"
                  ></mwc-textfield>
                </div>
              </div>
            `:b``}
        <div class="horizontal layout wrap setting-item">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${o("usersettings.SSHKeypairManagement")}</div>
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
            <div class="title">${o("usersettings.AutomaticUpdateCheck")}</div>
            <div class="description">
              ${v("usersettings.DescAutomaticUpdateCheck")}
            </div>
          </div>
          <div class="vertical center-justified layout setting-button flex end">
            <mwc-switch
              id="automatic-update-check-switch"
              @click="${t=>this.toggleAutomaticUploadCheck(t)}"
              ?selected="${globalThis.backendaioptions.get("automatic_update_check")}"
            ></mwc-switch>
          </div>
        </div>
        <div class="horizontal layout wrap setting-item" style="display:none;">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${o("usersettings.BetaFeatures")}</div>
            <div class="description">
              ${v("usersettings.DescBetaFeatures")}
            </div>
          </div>
          <div class="vertical center-justified layout setting-button flex end">
            <mwc-switch
              id="beta-feature-switch"
              @click="${t=>this.toggleBetaFeature(t)}"
              ?selected="${globalThis.backendaioptions.get("beta_feature")}"
            ></mwc-switch>
          </div>
        </div>
        <div class="horizontal layout wrap setting-item">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${o("usersettings.AutoLogout")}</div>
            <div class="description">${v("usersettings.DescAutoLogout")}</div>
          </div>
          <div class="vertical center-justified layout setting-button flex end">
            <mwc-switch
              id="auto-logout-switch"
              @click="${t=>this.toggleAutoLogout(t)}"
              ?selected="${globalThis.backendaioptions.get("auto_logout",!1)}"
            ></mwc-switch>
          </div>
        </div>
        <div class="horizontal layout wrap setting-item">
          <div class="vertical start start-justified layout setting-desc">
            <div class="title">${o("usersettings.MyKeypairInfo")}</div>
            <div class="description">
              ${v("usersettings.DescMyKeypairInfo")}
            </div>
          </div>
          <div class="vertical center-justified layout flex end">
            <mwc-icon-button
              id="ssh-keypair-details"
              icon="more"
              @click="${this._openMyKeypairDialog}"
            ></mwc-icon-button>
          </div>
        </div>
        ${this.beta_feature_panel?b`
              <h3 class="horizontal center layout">
                <span>${o("usersettings.BetaFeatures")}</span>
                <span class="flex"></span>
              </h3>
              <div class="description">
                ${o("usersettings.DescNoBetaFeatures")}
              </div>
            `:b``}
      </div>
      ${this.shell_script_edit?b`
            <h3 class="horizontal center layout">
              <span>${o("usersettings.ShellEnvironments")}</span>
              <span class="flex"></span>
            </h3>
            <div class="horizontal wrap layout">
              <mwc-button
                class="shell-button"
                icon="edit"
                outlined
                label="${o("usersettings.EditBootstrapScript")}"
                @click="${()=>this._launchBootstrapScriptDialog()}"
              ></mwc-button>
              <mwc-button
                class="shell-button"
                icon="edit"
                outlined
                label="${o("usersettings.EditUserConfigScript")}"
                @click="${()=>this._launchUserConfigDialog()}"
              ></mwc-button>
            </div>
            <h3 class="horizontal center layout" style="display:none;">
              <span>${o("usersettings.PackageInstallation")}</span>
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
          `:b``}
      <backend-ai-dialog
        id="bootstrap-dialog"
        fixed
        backdrop
        scrollable
        blockScrolling
        persistent
      >
        <span slot="title">${o("usersettings.EditBootstrapScript")}</span>
        <div slot="content" class="vertical layout terminal-area">
          <div style="margin-bottom:1em">
            ${o("usersettings.BootstrapScriptDescription")}
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
            label="${o("button.Cancel")}"
            @click="${()=>this._hideBootstrapScriptDialog()}"
          ></mwc-button>
          <mwc-button
            unelevated
            id="save-code"
            label="${o("button.Save")}"
            @click="${()=>this._saveBootstrapScript()}"
          ></mwc-button>
          <mwc-button
            unelevated
            id="save-code-and-close"
            label="${o("button.SaveAndClose")}"
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
          ${o("usersettings.Edit_ShellScriptTitle_1")} ${this.rcfile}
          ${o("usersettings.Edit_ShellScriptTitle_2")}
        </span>
        <div slot="content" class="vertical layout terminal-area">
          <mwc-select
            id="select-rcfile-type"
            label="${o("usersettings.ConfigFilename")}"
            required
            outlined
            fixedMenuPosition
            validationMessage="${o("credential.validation.PleaseSelectOption")}"
            @selected="${()=>this._toggleRcFileName()}"
            helper=${o("dialog.warning.WillBeAppliedToNewSessions")}
          >
            ${this.rcfiles.map((t=>b`
                <mwc-list-item
                  id="${t.path}"
                  value="${t.path}"
                  ?selected=${this.rcfile===t.path}
                >
                  ${t.path}
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
            label="${o("button.Cancel")}"
            @click="${()=>this._hideUserConfigScriptDialog()}"
          ></mwc-button>
          <mwc-button
            id="delete-rcfile"
            label="${o("button.Delete")}"
            @click="${()=>this._deleteRcFile()}"
          ></mwc-button>
          <mwc-button
            unelevated
            id="save-code"
            label="${o("button.Save")}"
            @click="${()=>this._saveUserConfigScript()}"
          ></mwc-button>
          <mwc-button
            unelevated
            id="save-code-and-close"
            label="${o("button.SaveAndClose")}"
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
          ${o("usersettings.DialogDiscardOrSave",{File:()=>this.prevRcfile})}
        </div>
        <div slot="content">${o("usersettings.DialogNoSaveNoPreserve")}</div>
        <div
          slot="footer"
          style="border-top:none;"
          class="end-justified layout flex horizontal"
        >
          <mwc-button
            id="cancel-editor"
            label="${o("button.Discard")}"
            @click="${()=>this._discardCurrentEditorChange()}"
          ></mwc-button>
          <mwc-button
            unelevated
            id="save-editor-data"
            label="${o("button.Save")}"
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
        <span slot="title">${o("usersettings.SSHKeypairManagement")}</span>
        <div slot="content" style="max-width:500px">
          <span slot="title">${o("usersettings.CurrentSSHPublicKey")}</span>
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
            label="${o("button.Close")}"
            @click="${this._hideSSHKeypairDialog}"
          ></mwc-button>
          <mwc-button
            unelevated
            label="${o("button.Generate")}"
            @click="${this._refreshSSHKeypair}"
          ></mwc-button>
          <mwc-button
            unelevated
            label="${o("button.EnterManually")}"
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
        <span slot="title">${o("usersettings.SSHKeypairGeneration")}</span>
        <div slot="content" style="max-width:500px;">
          <div class="vertical layout" style="display:inline-block;">
            <span slot="title">${o("usersettings.PublicKey")}</span>
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
            <span slot="title">${o("usersettings.PrivateKey")}</span>
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
              ${o("usersettings.SSHKeypairGenerationWarning")}
            </div>
          </div>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            label="${o("button.Close")}"
            @click="${this._openSSHKeypairClearDialog}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="clear-ssh-keypair-dialog" fixed persistent>
        <span slot="title">${o("usersettings.ClearSSHKeypairInput")}</span>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            outlined
            label="${o("button.No")}"
            @click="${this._hideSSHKeypairClearDialog}"
          ></mwc-button>
          <mwc-button
            unelevated
            label="${o("button.Yes")}"
            @click="${this._clearCurrentSSHKeypair}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="ssh-keypair-form-dialog" fixed persistent>
        <span slot="title">${o("usersettings.SSHKeypairEnterManually")}</span>
        <div slot="content" style="max-width:500px;">
          <div class="vertical layout" style="display:inline-block;">
            <span slot="title">${o("usersettings.PublicKey")}</span>
            <div class="horizontal layout flex">
              <mwc-textarea
                class="ssh-keypair"
                id="entered-ssh-public-key"
                outlined
              ></mwc-textarea>
            </div>
            <span slot="title">${o("usersettings.PrivateKey")}</span>
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
            label="${o("button.Cancel")}"
            @click="${this._hideSSHKeypairFormDialog}"
          ></mwc-button>
          <mwc-button
            unelevated
            label="${o("button.Save")}"
            @click="${this._saveSSHKeypairFormDialog}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-react-keypair-info-modal
        value="${this.isOpenMyKeypairInfoDialog?"true":"false"}"
        @close="${()=>{this.isOpenMyKeypairInfoDialog=!1}}"
      ></backend-ai-react-keypair-info-modal>
    `}};t([e({type:Object})],y.prototype,"notification",void 0),t([e({type:Array})],y.prototype,"supportLanguages",void 0),t([e({type:Boolean})],y.prototype,"beta_feature_panel",void 0),t([e({type:Boolean})],y.prototype,"shell_script_edit",void 0),t([e({type:Array})],y.prototype,"rcfiles",void 0),t([e({type:String})],y.prototype,"rcfile",void 0),t([e({type:String})],y.prototype,"prevRcfile",void 0),t([e({type:String})],y.prototype,"preferredSSHPort",void 0),t([e({type:String})],y.prototype,"publicSSHkey",void 0),t([i("#loading-spinner")],y.prototype,"spinner",void 0),t([i("#bootstrap-editor")],y.prototype,"bootstrapEditor",void 0),t([i("#usersetting-editor")],y.prototype,"userSettingEditor",void 0),t([i("#select-rcfile-type")],y.prototype,"rcFileTypeSelect",void 0),t([i("#ssh-public-key")],y.prototype,"sshPublicKeyInput",void 0),t([i("#ssh-private-key")],y.prototype,"sshPrivateKeyInput",void 0),t([i("#current-ssh-public-key")],y.prototype,"currentSSHPublicKeyInput",void 0),t([i("#copy-current-ssh-public-key-button")],y.prototype,"copyCurrentSSHPublicKeyButton",void 0),t([i("#bootstrap-dialog")],y.prototype,"bootstrapDialog",void 0),t([i("#change-current-editor-dialog")],y.prototype,"changeCurrentEditorDialog",void 0),t([i("#userconfig-dialog")],y.prototype,"userconfigDialog",void 0),t([i("#ssh-keypair-management-dialog")],y.prototype,"sshKeypairManagementDialog",void 0),t([i("#clear-ssh-keypair-dialog")],y.prototype,"clearSSHKeypairDialog",void 0),t([i("#generate-ssh-keypair-dialog")],y.prototype,"generateSSHKeypairDialog",void 0),t([i("#ssh-keypair-form-dialog")],y.prototype,"sshKeypairFormDialog",void 0),t([i("#entered-ssh-public-key")],y.prototype,"enteredSSHPublicKeyInput",void 0),t([i("#entered-ssh-private-key")],y.prototype,"enteredSSHPrivateKeyInput",void 0),t([e({type:Boolean})],y.prototype,"isOpenMyKeypairInfoDialog",void 0),t([i("#ui-language")],y.prototype,"languageSelect",void 0),t([i("#delete-rcfile")],y.prototype,"deleteRcfileButton",void 0),y=t([a("backend-ai-usersettings-general-list")],y);let f=class extends s{constructor(){super(),this.images=Object(),this.options=Object(),this._activeTab=Object(),this.logGrid=Object(),this.options={automatic_image_update:!1,cuda_gpu:!1,cuda_fgpu:!1,rocm_gpu:!1,tpu:!1,scheduler:"fifo"}}static get is(){return"backend-ai-usersettings-view"}static get styles(){return[n,l,r,c,d,p`
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
      `]}render(){return b`
      <link rel="stylesheet" href="resources/custom.css" />
      <lablup-loading-spinner id="loading-spinner"></lablup-loading-spinner>
      <lablup-activity-panel noheader narrow autowidth>
        <div slot="message">
          <h3 class="tab horizontal wrap layout">
            <mwc-tab-bar>
              <mwc-tab
                title="general"
                label="${o("usersettings.General")}"
                @click="${t=>this._showTab(t.target)}"
              ></mwc-tab>
              <mwc-tab
                title="logs"
                label="${o("usersettings.Logs")}"
                @click="${t=>this._showTab(t.target)}"
              ></mwc-tab>
            </mwc-tab-bar>
          </h3>
          <div id="general" class="item tab-content outer-space">
            <backend-ai-usersettings-general-list
              active="true"
            ></backend-ai-usersettings-general-list>
          </div>
          <div id="logs" class="item tab-content" style="display:none;">
            <backend-ai-react-error-log-list></backend-ai-react-error-log-list>
          </div>
        </div>
      </lablup-activity-panel>
    `}firstUpdated(){void 0===globalThis.backendaiclient||null===globalThis.backendaiclient?document.addEventListener("backend-ai-connected",(()=>{this.updateSettings()}),!0):this.updateSettings(),this.notification=globalThis.lablupNotification,document.addEventListener("backend-ai-usersettings-logs",(()=>{this._viewStateChanged()})),document.addEventListener("backend-ai-usersettings",(()=>{this._viewStateChanged()}))}async _viewStateChanged(){const t=m.getState().app.params.tab;t&&"logs"===t?globalThis.setTimeout((()=>{var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector('mwc-tab[title="logs"]')).click()}),0):globalThis.setTimeout((()=>{var t;(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector('mwc-tab[title="general"]')).click()}),0)}updateSettings(){}_showTab(t){var e,i;const a=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelectorAll(".tab-content");for(let t=0;t<a.length;t++)a[t].style.display="none";this._activeTab=t.title,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t.title)).style.display="block"}};t([e({type:Object})],f.prototype,"images",void 0),t([e({type:Object})],f.prototype,"options",void 0),t([e({type:Object})],f.prototype,"_activeTab",void 0),t([e({type:Object})],f.prototype,"logGrid",void 0),t([i("#loading-spinner")],f.prototype,"spinner",void 0),f=t([a("backend-ai-usersettings-view")],f);
