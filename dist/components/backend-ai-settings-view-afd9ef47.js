import{B as t,g as i,d as e,I as s,b as o,x as n,f as l,i as a,y as c,t as d,h as r,_ as u,e as h,c as p,a as v}from"./backend-ai-webui-efd2500f.js";import{t as g}from"./translate-unsafe-html-8abe2c79.js";import"./vaadin-grid-af1e810c.js";import"./vaadin-grid-sort-column-46341c17.js";import"./mwc-switch-f419f24b.js";import"./lablup-activity-panel-b5a6a642.js";
/**
 @license
 Copyright (c) 2015-2022 Lablup Inc. All rights reserved.
 */let m=class extends t{constructor(){super(),this.images=Object(),this.schedulerOptions=Object(),this.networkOptions=Object(),this.notification=Object(),this.imagePullingBehavior=[{name:i("settings.image.digest"),behavior:"digest"},{name:i("settings.image.tag"),behavior:"tag"},{name:i("settings.image.none"),behavior:"none"}],this.jobschedulerType=["fifo","lifo","drf"],this.selectedSchedulerType="",this._helpDescriptionTitle="",this._helpDescription="",this.optionRange=Object(),this.options={image_pulling_behavior:"digest",cuda_gpu:!1,cuda_fgpu:!1,rocm_gpu:!1,tpu:!1,schedulerType:"fifo",scheduler:{num_retries_to_skip:"0"},network:{mtu:""}},this.optionRange={numRetries:{min:0,max:1e3},mtu:{min:0,max:15e3}},this.optionsAndId=[{option:"num_retries_to_skip",id:"num-retries"},{option:"mtu",id:"mtu"}]}static get is(){return"backend-ai-settings-view"}static get styles(){return[e,s,o,n,l,a`
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
          max-width: 500px;
        }

        div.description-shrink {
          font-size: 13px;
          margin-top: 5px;
          margin-right: 5px;
          width: 260px;
        }

        div.description-extra {
          font-size: 13px;
          margin-top: 5px;
          margin-right: 5px;
          max-width: 500px;
        }

        .setting-item {
          margin: 15px 10px 15px 0px;
          width: auto;
        }

        .setting-desc, .setting-desc-select {
          float: left;
          width: 100%;
        }

        .setting-desc-shrink {
          float: left;
          width: auto;
        }

        .setting-button {
          float: right;
          width: 35px;
          white-space: nowrap;
        }

        .setting-desc-pulldown {
          width: 265px;
        }

        .setting-pulldown {
          width: 70px;
        }

        #help-description {
          --component-width: 350px;
        }

        #scheduler-env-dialog {
          --component-max-height: 800px;
          --component-width: 400px;
        }

        lablup-activity-panel {
          color: #000;
        }

        mwc-select {
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

        mwc-textfield#num-retries {
          width: 10rem;
        }

        mwc-button {
          word-break: keep-all;
        }
        @media screen and (max-width: 750px) {
          .setting-desc, .setting-desc-shrink {
            width: 275px;
          }

          .setting-desc-select {
            width: 190px;
          }

          div.description-shrink {
            width: auto;
          }

        }

        @media screen and (min-width: 1400px) {
          div.description-extra {
            max-width: 100%;
          }
        }
      `]}render(){return c`
      <link rel="stylesheet" href="resources/custom.css">
      <div class="horizontal layout wrap">
        <lablup-activity-panel title="${d("settings.Image")}" autowidth>
          <div slot="message" class="horizontal wrap layout">
            <div class="horizontal layout setting-item">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">${d("settings.RegisterNewImagesFromRepo")}</div>
                <div class="description">${d("settings.DescRegisterNewImagesFromRepo")}
                </div>
              </div>
              <div class="vertical center-justified layout setting-button">
                <mwc-switch id="register-new-image-switch" disabled></mwc-switch>
              </div>
            </div>
            <div class="horizontal layout setting-item">
              <div class="vertical center-justified layout setting-desc-select">
                <div class="title">${d("settings.ImagePullBehavior")}</div>
                <div class="description-extra">${g("settings.DescImagePullBehavior")}<br />
                    ${d("settings.Require2003orAbove")}
                </div>
              </div>
              <div class="vertical center-justified layout">
                <mwc-select id="ui-image-pulling-behavior"
                            required
                            outlined
                            style="width:150px;"
                            @selected="${t=>this.setImagePullingBehavior(t)}">
                ${this.imagePullingBehavior.map((t=>c`
                  <mwc-list-item value="${t.behavior}"
                                 ?selected=${this.options.image_pulling_behavior===t.behavior}>
                    ${t.name}
                  </mwc-list-item>`))}
                </mwc-select>
              </div>
            </div>
          </div>
        </lablup-activity-panel>
        <lablup-activity-panel title="${d("settings.GUI")}" autowidth>
          <div slot="message" class="horizontal wrap layout">
            <div class="horizontal layout setting-item">
              <div class="vertical center-justified layout setting-desc-shrink">
                <div class="title">${d("settings.UseCLIonGUI")}</div>
                <div class="description-shrink">${g("settings.DescUseCLIonGUI")}
                </div>
              </div>
              <div class="vertical center-justified layout setting-button">
                <mwc-switch id="use-cli-on-gui-switch" disabled></mwc-switch>
              </div>
            </div>
            <div class="horizontal layout setting-item">
              <div class="vertical center-justified layout setting-desc-shrink">
                <div class="title">${d("settings.UseGUIonWeb")}</div>
                <div class="description-shrink">${g("settings.DescUseGUIonWeb")}
                </div>
              </div>
              <div class="vertical center-justified layout setting-button">
                <mwc-switch id="use-gui-on-web-switch" disabled></mwc-switch>
              </div>
            </div>
          </div>
        </lablup-activity-panel>
        <lablup-activity-panel title="${d("settings.Scaling")} & ${d("settings.Plugins")}" narrow autowidth>
          <div slot="message" class="vertical wrap layout">
            <div class="horizontal wrap layout note" style="background-color:#FFFBE7;width:100%;padding:10px 0px;">
              <p style="margin:auto 10px;">
                ${d("settings.NoteAboutFixedSetup")}
              </p>
            </div>
            <div style="margin:auto 16px;">
              <h3 class="horizontal center layout">
                <span>${d("settings.Scaling")}</span>
                <span class="flex"></span>
              </h3>
              <div class="vertical wrap layout">
                <div class="horizontal layout wrap start start-justified">
                  <div class="horizontal layout setting-item">
                    <div class="vertical center-justified layout setting-desc-shrink">
                      <div class="title">${d("settings.AllowAgentSideRegistration")}</div>
                      <div class="description-shrink">${g("settings.DescAllowAgentSideRegistration")}
                      </div>
                    </div>
                    <div class="vertical center-justified layout setting-button">
                      <mwc-switch id="allow-agent-registration-switch" selected disabled></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div class="vertical center-justified layout setting-desc-shrink">
                      <div class="title">${d("settings.OverlayNetwork")}</div>
                      <div class="description-shrink">${g("settings.OverlayNetworkConfiguration")}
                      </div>
                    </div>
                    <div class="vertical center-justified layout">
                      <mwc-button
                        unelevated
                        icon="rule"
                        label="${d("settings.Config")}"
                        style="float: right;"
                        @click="${()=>{this.updateNetworkOptionElements(),this._openDialogWithConfirmation("overlay-network-env-dialog")}}"></mwc-button>
                    </div>
                  </div>
                </div>
              </div>
              <h3 class="horizontal center layout">
                <span>${d("settings.Plugins")}</span>
                <span class="flex"></span>
              </h3>
              <div class="vertical layout wrap">
                <div class="horizontal layout wrap start start-justified">
                  <div class="horizontal layout setting-item">
                    <div class="vertical center-justified layout setting-desc-shrink">
                      <div class="title">${d("settings.CUDAGPUsupport")}</div>
                      <div class="description-shrink">${g("settings.DescCUDAGPUsupport")}
                        ${this.options.cuda_fgpu?c`<br />${d("settings.CUDAGPUdisabledByFGPUsupport")}`:c``}
                      </div>
                    </div>
                    <div class="vertical center-justified layout setting-button">
                      <mwc-switch id="cuda-gpu-support-switch" ?selected="${this.options.cuda_gpu}" disabled></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div class="vertical center-justified layout setting-desc-shrink">
                      <div class="title">${d("settings.ROCMGPUsupport")}</div>
                      <div class="description-shrink">${g("settings.DescROCMGPUsupport")}<br />${d("settings.Require1912orAbove")}
                      </div>
                    </div>
                    <div class="vertical center-justified layout setting-button">
                      <mwc-switch id="rocm-gpu-support-switch" ?selected="${this.options.rocm_gpu}" disabled></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div class="vertical center-justified layout setting-desc-select" style="margin: 15px 0px;">
                      <div class="title">${d("settings.Scheduler")}</div>
                      <div class="description-shrink">${d("settings.SchedulerConfiguration")}<br/>
                          ${d("settings.Require2009orAbove")}
                      </div>
                    </div>
                    <div class="vertical center-justified layout">
                      <mwc-button style="white-space: nowrap;"
                        unelevated
                        icon="rule"
                        label="${d("settings.Config")}"
                        @click="${()=>this._openDialogWithConfirmation("scheduler-env-dialog")}"></mwc-button>
                    </div>
                  </div>
                </div>
                <h3 class="horizontal center layout">
                  <span>${d("settings.EnterpriseFeatures")}</span>
                  <span class="flex"></span>
                </h3>
                <div class="horizontal wrap layout">
                  <div class="horizontal layout setting-item">
                    <div class="vertical center-justified layout setting-desc-shrink">
                      <div class="title">${d("settings.FractionalGPU")}</div>
                      <div class="description-shrink">${d("settings.DescFractionalGPU")} <br/> ${d("settings.RequireFGPUPlugin")}
                      </div>
                    </div>
                    <div class="vertical center-justified layout setting-button">
                      <mwc-switch id="fractional-gpu-switch" ?selected="${this.options.cuda_fgpu}" disabled></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div class="vertical center-justified layout setting-desc-shrink">
                      <div class="title">${d("settings.TPU")}</div>
                      <div class="description-shrink">${d("settings.DescTPU")} <br/>${d("settings.RequireTPUPlugin")}
                      </div>
                    </div>
                    <div class="vertical center-justified layout setting-button">
                      <mwc-switch id="tpu-switch" ?selected="${this.options.tpu}" disabled></mwc-switch>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </lablup-activity-panel>
        <backend-ai-dialog id="scheduler-env-dialog" class="env-dialog" fixed backdrop persistent closeWithConfirmation>
          <span slot="title" class="horizontal layout center">${g("settings.ConfigPerJobSchduler")}</span>
          <span slot="action">
            <mwc-icon-button icon="info" @click="${t=>this._showConfigDescription(t,"default")}" style="pointer-events:auto;"></mwc-icon-button>
          </span>
          <div slot="content" id="scheduler-env-container" class="vertical layout centered env-container" style="width: 100%;">
            <mwc-select
              id="scheduler-switch"
              required
              label="${d("settings.Scheduler")}"
              style="margin-bottom: 10px;"
              validationMessage="${d("settings.SchedulerRequired")}"
              @selected="${t=>this.changeSelectedScheduleType(t)}">
              ${this.jobschedulerType.map((t=>c`
                <mwc-list-item value="${t}">
                  ${t.toUpperCase()}
                </mwc-list-item>`))}
            </mwc-select>
            <h4>${d("settings.SchedulerOptions")}</h4>
            <div class="horizontal center layout flex row">
              <span slot="title">${d("settings.SessionCreationRetries")}</span>
              <mwc-icon-button icon="info" @click="${t=>this._showConfigDescription(t,"retries")}" style="pointer-events:auto;"></mwc-icon-button>
              <mwc-textfield  id="num-retries"
                              required
                              autoValidate
                              validationMessage="${d("settings.InputRequired")}"
                              type="number"
                              pattern="[0-9]+"
                              min="${this.optionRange.numRetries.min}"
                              max="${this.optionRange.numRetries.max}"
                              style="margin-top: 18px"
                              @change="${t=>this._validateInput(t)}"
                              @input="${t=>this._customizeValidationMessage(t)}"></mwc-textfield>
            </div>
          </div>
          <div slot="footer" class="horizontal end-justified flex layout">
            <mwc-button
              id="config-cancel-button"
              style="width:auto;margin-right:10px;"
              icon="delete"
              @click="${()=>this._clearOptions("scheduler-env-container")}"
              label="${d("button.DeleteAll")}"></mwc-button>
            <mwc-button
              unelevated
              id="config-save-button"
              style="width:auto;"
              icon="check"
              @click="${()=>this.saveAndCloseDialog()}"
              label="${d("button.Save")}"></mwc-button>
          </div>
        </backend-ai-dialog>
        <backend-ai-dialog id="overlay-network-env-dialog" class="env-dialog" fixed backdrop persistent closeWithConfirmation>
          <span slot="title" class="horizontal layout center">${g("settings.OverlayNetworkSettings")}</span>
          <span slot="action">
            <mwc-icon-button icon="info" @click="${t=>this._showConfigDescription(t,"overlayNetwork")}" style="pointer-events:auto;"></mwc-icon-button>
          </span>
          <div slot="content" id="overlay-network-env-container" class="vertical layout centered env-container" style="width: 100%;">
            <div class="horizontal center layout flex row justified">
              <div class="horizontal center layout">
                <span slot="title">MTU</span>
                <mwc-icon-button icon="info" @click="${t=>this._showConfigDescription(t,"mtu")}" style="pointer-events:auto;"></mwc-icon-button>
              </div>
              <mwc-textfield id="mtu"
                             class="network-option"
                             value="${this.options.network.mtu}"
                             required
                             autoValidate
                             validationMessage="${d("settings.InputRequired")}"
                             type="number"
                             pattern="[0-9]+"
                             min="${this.optionRange.mtu.min}"
                             max="${this.optionRange.mtu.max}"
                             style="margin-top:18px;min-width:240px;"
                             @change="${t=>this._validateInput(t)}"
                             @input="${t=>this._customizeValidationMessage(t)}"></mwc-textfield>
            </div>
          </div>
          <div slot="footer" class="horizontal end-justified flex layout">
            <mwc-button
              id="config-cancel-button"
              style="width:auto;margin-right:10px;"
              icon="delete"
              @click="${()=>this._clearOptions("overlay-network-env-container")}"
              label="${d("button.DeleteAll")}"></mwc-button>
            <mwc-button
              unelevated
              id="config-save-button"
              style="width:auto;"
              icon="check"
              @click="${()=>this.saveAndCloseOverlayNetworkDialog()}"
              label="${d("button.Save")}"></mwc-button>
          </div>
        </backend-ai-dialog>
        <backend-ai-dialog id="help-description" fixed backdrop>
          <span slot="title">${this._helpDescriptionTitle}</span>
          <div slot="content" class="horizontal layout">${this._helpDescription}</div>
        </backend-ai-dialog>
        <backend-ai-dialog id="env-config-confirmation" warning fixed>
          <span slot="title">${d("dialog.title.LetsDouble-Check")}</span>
          <div slot="content">
            <p>${d("settings.EnvConfigWillDisappear")}</p>
            <p>${d("dialog.ask.DoYouWantToProceed")}</p>
          </div>
          <div slot="footer" class="horizontal end-justified flex layout">
            <mwc-button
               id="env-config-remain-button"
               style="width:auto;"
               label="${d("button.Cancel")}"
               @click="${()=>this.closeDialog("env-config-confirmation")}">
           </mwc-button>
            <mwc-button
                unelevated
                id="env-config-reset-button"
                style="width:auto;margin-right:10px;"
                label="${d("button.DismissAndProceed")}"
                @click="${()=>this.closeAndResetEnvInput()}">
            </mwc-button>
          </div>
        </backend-ai-dialog>
      </div>
    `}firstUpdated(){this.notification=globalThis.lablupNotification,void 0===globalThis.backendaiclient||null===globalThis.backendaiclient?document.addEventListener("backend-ai-connected",(()=>{this.updateSettings()}),!0):this.updateSettings(),this.schedulerEnvDialog.addEventListener("dialog-closing-confirm",(t=>{var i,e;const s=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#scheduler-env-container"),o=Array.from(null==s?void 0:s.querySelectorAll("mwc-textfield"));for(const t of o){if(this.options.scheduler[null!==(e=this._findOptionById(t.id))&&void 0!==e?e:-1]!==t.value&&""!==this.selectedSchedulerType){this.openDialog("env-config-confirmation");break}this._closeDialogWithConfirmation("scheduler-env-dialog")}})),this.overlayNetworkEnvDialog.addEventListener("dialog-closing-confirm",(t=>{var i,e;const s=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#overlay-network-env-container"),o=Array.from(null==s?void 0:s.querySelectorAll("mwc-textfield"));for(const t of o){if(this.options.network[null!==(e=this._findOptionById(t.id))&&void 0!==e?e:""]!==t.value){this.openDialog("env-config-confirmation");break}this._closeDialogWithConfirmation("overlay-network-env-dialog")}}))}async _viewStateChanged(t){await this.updateComplete}updatePulling(){globalThis.backendaiclient.setting.get("docker/image/auto_pull").then((t=>{null===t.result||"digest"===t.result?this.options.image_pulling_behavior="digest":"tag"===t.result?this.options.image_pulling_behavior="tag":this.options.image_pulling_behavior="none",this.requestUpdate()}))}updateScheduler(){for(const[t]of Object.entries(this.options.scheduler))globalThis.backendaiclient.setting.get(`plugins/scheduler/${this.selectedSchedulerType}/${t}`).then((i=>{this.options.scheduler[t]=i.result||"0"})),this.requestUpdate()}updateNetwork(){for(const[t]of Object.entries(this.options.network))globalThis.backendaiclient.setting.get(`network/overlay/${t}`).then((i=>{this.options.network[t]=i.result||""})),this.requestUpdate()}updateResourceSlots(){globalThis.backendaiclient.get_resource_slots().then((t=>{"cuda.device"in t&&(this.options.cuda_gpu=!0),"cuda.shares"in t&&(this.options.cuda_fgpu=!0),"rocm.device"in t&&(this.options.rocm_gpu=!0),"tpu.device"in t&&(this.options.tpu=!0),this.requestUpdate()}))}updateSettings(){this.updatePulling(),this.updateScheduler(),this.updateNetwork(),this.updateResourceSlots()}updateNetworkOptionElements(){var t,i;this.updateNetwork();const e=Array.from(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".network-option"));for(const t of e){const e=null!==(i=this._findOptionById(t.id))&&void 0!==i?i:"";t.value=this.options.network[e]||""}}setImagePullingBehavior(t){if(null===t.target.selected)return!1;const e=t.target.selected.value;return e!==this.options.image_pulling_behavior&&["none","digest","tag"].includes(e)&&globalThis.backendaiclient.setting.set("docker/image/auto_pull",e).then((t=>{this.options.image_pulling_behavior=e,this.notification.text=i("notification.SuccessfullyUpdated"),this.notification.show(),this.requestUpdate(),console.log(t)})),!0}_findIdByOption(t){var i;return null===(i=this.optionsAndId.find((i=>i.option===t)))||void 0===i?void 0:i.id}_findOptionById(t){var i;return null===(i=this.optionsAndId.find((i=>i.id===t)))||void 0===i?void 0:i.option}_clearOptions(t){var i;const e=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t);null==e||e.querySelectorAll("mwc-textfield").forEach((t=>{t.value=""}))}_openDialogWithConfirmation(t){var i;const e=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t);e.closeWithConfirmation=!0,null==e||e.show()}_closeDialogWithConfirmation(t){var i;const e=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t);e.closeWithConfirmation=!1,e.hide()}closeAndResetEnvInput(){var t;const i=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".env-dialog");for(const t of Array.from(i))if(t.open){const i=t.querySelector(".env-container");this._clearOptions(null==i?void 0:i.id),this.closeDialog("env-config-confirmation"),this._closeDialogWithConfirmation(t.id),"scheduler-env-dialog"===t.id&&(this.schedulerSelect.value="");break}}_showConfigDescription(t,e){t.stopPropagation();const s={default:{title:i("settings.ConfigPerJobSchduler"),desc:i("settings.ConfigPerJobSchdulerDescription")},retries:{title:i("settings.SessionCreationRetries"),desc:i("settings.SessionCreationRetriesDescription")+"\n"+i("settings.FifoOnly")},overlayNetwork:{title:i("settings.OverlayNetworkSettings"),desc:i("settings.OverlayNetworkSettingsDescription")},mtu:{title:"MTU",desc:i("settings.MTUDescription")}};e in s&&(this._helpDescriptionTitle=s[e].title,this._helpDescription=s[e].desc,this.helpDescriptionDialog.show())}openDialog(t){var i;(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t)).show()}closeDialog(t){var i;(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t)).hide()}saveAndCloseDialog(){const t=this.numberOfRetries.value,e=[this.schedulerSelect,this.numberOfRetries];if(!(e.filter((t=>null==t?void 0:t.reportValidity())).length<e.length)&&["fifo","lifo","drf"].includes(this.selectedSchedulerType))if("fifo"===this.selectedSchedulerType||"fifo"!==this.selectedSchedulerType&&"0"===t){const e={num_retries_to_skip:parseInt(t).toString()};globalThis.backendaiclient.setting.set(`plugins/scheduler/${this.selectedSchedulerType}`,e).then((t=>{this.notification.text=i("notification.SuccessfullyUpdated"),this.notification.show(),this.options.schedulerType=this.selectedSchedulerType,this.options.scheduler={...this.options.scheduler,...e},this.requestUpdate(),this._closeDialogWithConfirmation("scheduler-env-dialog")})).catch((t=>{this.notification.text=r.relieve("Couldn't update scheduler setting."),this.notification.detail=t,this.notification.show(!0,t)}))}else"0"!==t&&(this.notification.text=i("settings.FifoOnly"),this.notification.show(),this.numberOfRetries.value="0")}saveAndCloseOverlayNetworkDialog(){var t,e;const s=Array.from(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".network-option"));if(s.filter((t=>t.reportValidity())).length<s.length)return;const o={};for(const t of s){const i=null!==(e=this._findOptionById(t.id))&&void 0!==e?e:"",s=t.value;if(""===s&&null===s&&void 0===s)return;o[i]=s}globalThis.backendaiclient.setting.set("network/overlay",o).then((t=>{this.notification.text=i("notification.SuccessfullyUpdated"),this.notification.show(),this.options.network={...this.options.network,...o},this.requestUpdate(),this._closeDialogWithConfirmation("overlay-network-env-dialog")})).catch((t=>{this.notification.text=r.relieve("Couldn't update scheduler setting."),this.notification.detail=t,this.notification.show(!0,t)}))}changeSelectedScheduleType(t){this.selectedSchedulerType=t.target.value,this.updateScheduler();for(const[t]of Object.entries(this.options.scheduler))globalThis.backendaiclient.setting.get(`plugins/scheduler/${this.selectedSchedulerType}/${t}`).then((i=>{var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#"+this._findIdByOption(t))).value=i.result||"0"}))}_validateInput(t){const i=t.target.closest("mwc-textfield");i.value&&(i.value=Math.round(i.value),i.min&&i.max&&(i.value=globalThis.backendaiclient.utils.clamp(i.value,i.min,i.max)))}_customizeValidationMessage(t){const e=t.target.closest("mwc-textfield");e.validityTransform=(t,s)=>s.valid?{valid:s.valid,customError:!s.valid}:s.valueMissing?(e.validationMessage=i("settings.InputRequired"),{valid:s.valid,customError:!s.valid}):s.rangeOverflow||s.rangeUnderflow?(e.validationMessage=i("settings.OutOfRange"),{valid:s.valid,customError:!s.valid}):(e.validationMessage=i("settings.InvalidValue"),{valid:s.valid,customError:!s.valid})}};u([h({type:Object})],m.prototype,"images",void 0),u([h({type:Object})],m.prototype,"options",void 0),u([h({type:Object})],m.prototype,"schedulerOptions",void 0),u([h({type:Object})],m.prototype,"networkOptions",void 0),u([h({type:Object})],m.prototype,"optionsAndId",void 0),u([h({type:Object})],m.prototype,"notification",void 0),u([h({type:Array})],m.prototype,"imagePullingBehavior",void 0),u([h({type:Array})],m.prototype,"jobschedulerType",void 0),u([h({type:String})],m.prototype,"selectedSchedulerType",void 0),u([h({type:String})],m.prototype,"_helpDescriptionTitle",void 0),u([h({type:String})],m.prototype,"_helpDescription",void 0),u([h({type:Object})],m.prototype,"optionRange",void 0),u([p("#scheduler-switch")],m.prototype,"schedulerSelect",void 0),u([p("#num-retries")],m.prototype,"numberOfRetries",void 0),u([p("#scheduler-env-dialog")],m.prototype,"schedulerEnvDialog",void 0),u([p("#overlay-network-env-dialog")],m.prototype,"overlayNetworkEnvDialog",void 0),u([p("#help-description")],m.prototype,"helpDescriptionDialog",void 0),m=u([v("backend-ai-settings-view")],m);var f=m;export{f as default};
