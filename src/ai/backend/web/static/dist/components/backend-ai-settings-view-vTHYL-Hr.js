import{_ as t,n as i,e,t as s,B as o,g as n,b as l,I as a,a as c,u as d,c as r,i as u,x as p,f as h,h as v,d as g}from"./backend-ai-webui-CHZ-bl4E.js";import"./lablup-activity-panel-BRVLvaCu.js";import"./mwc-switch-BjHJLnvp.js";import"./vaadin-grid-BPP02Fg2.js";import"./vaadin-grid-sort-column-D98JUghL.js";import"./dir-utils-Oo-ABbXC.js";let m=class extends o{constructor(){super(),this.images=Object(),this.schedulerOptions=Object(),this.networkOptions=Object(),this.notification=Object(),this.imagePullingBehavior=[{name:n("settings.image.digest"),behavior:"digest"},{name:n("settings.image.tag"),behavior:"tag"},{name:n("settings.image.none"),behavior:"none"}],this.jobschedulerType=["fifo","lifo","drf"],this.selectedSchedulerType="",this._helpDescriptionTitle="",this._helpDescription="",this.optionRange=Object(),this.options={image_pulling_behavior:"digest",cuda_gpu:!1,cuda_fgpu:!1,rocm_gpu:!1,tpu:!1,ipu:!1,atom:!1,warboy:!1,hyperaccel_lpu:!1,schedulerType:"fifo",scheduler:{num_retries_to_skip:"0"},network:{mtu:""}},this.optionRange={numRetries:{min:0,max:1e3},mtu:{min:0,max:15e3}},this.optionsAndId=[{option:"num_retries_to_skip",id:"num-retries"},{option:"mtu",id:"mtu"}]}static get is(){return"backend-ai-settings-view"}static get styles(){return[l,a,c,d,r,u`
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

        .setting-desc,
        .setting-desc-select {
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

        mwc-select {
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
          .setting-desc,
          .setting-desc-shrink {
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
      `]}render(){return p`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="horizontal layout wrap" style="gap:24px">
        <lablup-activity-panel title="${h("settings.Image")}" autowidth>
          <div slot="message" class="horizontal wrap layout">
            <div class="horizontal layout setting-item">
              <div class="vertical center-justified layout setting-desc">
                <div class="title">
                  ${h("settings.RegisterNewImagesFromRepo")}
                </div>
                <div class="description">
                  ${h("settings.DescRegisterNewImagesFromRepo")}
                </div>
              </div>
              <div class="vertical center-justified layout setting-button">
                <mwc-switch
                  id="register-new-image-switch"
                  disabled
                ></mwc-switch>
              </div>
            </div>
            <div class="horizontal layout setting-item">
              <div class="vertical center-justified layout setting-desc-select">
                <div class="title">${h("settings.ImagePullBehavior")}</div>
                <div class="description-extra">
                  ${v("settings.DescImagePullBehavior")}
                  <br />
                  ${h("settings.Require2003orAbove")}
                </div>
              </div>
              <div class="vertical center-justified layout">
                <mwc-select
                  id="ui-image-pulling-behavior"
                  required
                  outlined
                  style="width:150px;"
                  @selected="${t=>this.setImagePullingBehavior(t)}"
                >
                  ${this.imagePullingBehavior.map((t=>p`
                      <mwc-list-item
                        value="${t.behavior}"
                        ?selected=${this.options.image_pulling_behavior===t.behavior}
                      >
                        ${t.name}
                      </mwc-list-item>
                    `))}
                </mwc-select>
              </div>
            </div>
          </div>
        </lablup-activity-panel>
        <lablup-activity-panel title="${h("settings.GUI")}" autowidth>
          <div slot="message" class="horizontal wrap layout">
            <div class="horizontal layout setting-item">
              <div class="vertical center-justified layout setting-desc-shrink">
                <div class="title">${h("settings.UseCLIonGUI")}</div>
                <div class="description-shrink">
                  ${v("settings.DescUseCLIonGUI")}
                </div>
              </div>
              <div class="vertical center-justified layout setting-button">
                <mwc-switch id="use-cli-on-gui-switch" disabled></mwc-switch>
              </div>
            </div>
            <div class="horizontal layout setting-item">
              <div class="vertical center-justified layout setting-desc-shrink">
                <div class="title">${h("settings.UseGUIonWeb")}</div>
                <div class="description-shrink">
                  ${v("settings.DescUseGUIonWeb")}
                </div>
              </div>
              <div class="vertical center-justified layout setting-button">
                <mwc-switch id="use-gui-on-web-switch" disabled></mwc-switch>
              </div>
            </div>
          </div>
        </lablup-activity-panel>
        <lablup-activity-panel
          title="${h("settings.Scaling")} & ${h("settings.Plugins")}"
          narrow
          autowidth
        >
          <div slot="message" class="vertical wrap layout">
            <div
              class="horizontal wrap layout note"
              style="background-color:var(--token-colorInfoBg,#FFFBE7);width:100%;padding:10px 0px;color:var(--token-colorText,rgba(0,0,0,0.88));"
            >
              <p style="margin:auto 10px;">
                ${h("settings.NoteAboutFixedSetup")}
              </p>
            </div>
            <div style="margin:auto 16px;">
              <h3 class="horizontal center layout">
                <span>${h("settings.Scaling")}</span>
                <span class="flex"></span>
              </h3>
              <div class="vertical wrap layout">
                <div class="horizontal layout wrap start start-justified">
                  <div class="horizontal layout setting-item">
                    <div
                      class="vertical center-justified layout setting-desc-shrink"
                    >
                      <div class="title">
                        ${h("settings.AllowAgentSideRegistration")}
                      </div>
                      <div class="description-shrink">
                        ${v("settings.DescAllowAgentSideRegistration")}
                      </div>
                    </div>
                    <div
                      class="vertical center-justified layout setting-button"
                    >
                      <mwc-switch
                        id="allow-agent-registration-switch"
                        selected
                        disabled
                      ></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div
                      class="vertical center-justified layout setting-desc-shrink"
                    >
                      <div class="title">${h("settings.OverlayNetwork")}</div>
                      <div class="description-shrink">
                        ${v("settings.OverlayNetworkConfiguration")}
                      </div>
                    </div>
                    <div class="vertical center-justified layout">
                      <mwc-button
                        unelevated
                        icon="rule"
                        label="${h("settings.Config")}"
                        style="float: right;"
                        @click="${()=>{this.updateNetworkOptionElements(),this._openDialogWithConfirmation("overlay-network-env-dialog")}}"
                      ></mwc-button>
                    </div>
                  </div>
                </div>
              </div>
              <h3 class="horizontal center layout">
                <span>${h("settings.Plugins")}</span>
                <span class="flex"></span>
              </h3>
              <div class="vertical layout wrap">
                <div class="horizontal layout wrap start start-justified">
                  <div class="horizontal layout setting-item">
                    <div
                      class="vertical center-justified layout setting-desc-shrink"
                    >
                      <div class="title">
                        ${h("settings.OpenSourceCUDAGPUsupport")}
                      </div>
                      <div class="description-shrink">
                        ${v("settings.DescCUDAGPUsupport")}
                        ${this.options.cuda_fgpu?p`
                              <br />
                              ${h("settings.CUDAGPUdisabledByFGPUsupport")}
                            `:p``}
                      </div>
                    </div>
                    <div
                      class="vertical center-justified layout setting-button"
                    >
                      <mwc-switch
                        id="cuda-gpu-support-switch"
                        ?selected="${this.options.cuda_gpu}"
                        disabled
                      ></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div
                      class="vertical center-justified layout setting-desc-shrink"
                    >
                      <div class="title">${h("settings.ROCMGPUsupport")}</div>
                      <div class="description-shrink">
                        ${v("settings.DescROCMGPUsupport")}
                      </div>
                    </div>
                    <div
                      class="vertical center-justified layout setting-button"
                    >
                      <mwc-switch
                        id="rocm-gpu-support-switch"
                        ?selected="${this.options.rocm_gpu}"
                        disabled
                      ></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div
                      class="vertical center-justified layout setting-desc-select"
                      style="margin: 15px 0px;"
                    >
                      <div class="title">${h("settings.Scheduler")}</div>
                      <div class="description-shrink">
                        ${h("settings.SchedulerConfiguration")}
                        <br />
                        ${h("settings.Require2009orAbove")}
                      </div>
                    </div>
                    <div class="vertical center-justified layout">
                      <mwc-button
                        style="white-space: nowrap;"
                        unelevated
                        icon="rule"
                        label="${h("settings.Config")}"
                        @click="${()=>this._openDialogWithConfirmation("scheduler-env-dialog")}"
                      ></mwc-button>
                    </div>
                  </div>
                </div>
                <h3 class="horizontal center layout">
                  <span>${h("settings.EnterpriseFeatures")}</span>
                  <span class="flex"></span>
                </h3>
                <div class="horizontal wrap layout">
                  <div class="horizontal layout setting-item">
                    <div
                      class="vertical center-justified layout setting-desc-shrink"
                    >
                      <div class="title">${h("settings.FractionalGPU")}</div>
                      <div class="description-shrink">
                        ${h("settings.DescFractionalGPU")}
                        <br />
                        ${h("settings.RequireFGPUPlugin")}
                      </div>
                    </div>
                    <div
                      class="vertical center-justified layout setting-button"
                    >
                      <mwc-switch
                        id="fractional-gpu-switch"
                        ?selected="${this.options.cuda_fgpu}"
                        disabled
                      ></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div
                      class="vertical center-justified layout setting-desc-shrink"
                    >
                      <div class="title">${h("settings.TPU")}</div>
                      <div class="description-shrink">
                        ${h("settings.DescTPU")}
                        <br />
                        ${h("settings.RequireTPUPlugin")}
                      </div>
                    </div>
                    <div
                      class="vertical center-justified layout setting-button"
                    >
                      <mwc-switch
                        id="tpu-switch"
                        ?selected="${this.options.tpu}"
                        disabled
                      ></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div
                      class="vertical center-justified layout setting-desc-shrink"
                    >
                      <div class="title">${h("settings.IPUsupport")}</div>
                      <div class="description-shrink">
                        ${v("settings.DescIPUsupport")}
                        <br />
                        ${h("settings.RequireIPUPlugin")}
                      </div>
                    </div>
                    <div
                      class="vertical center-justified layout setting-button"
                    >
                      <mwc-switch
                        id="ipu-support-switch"
                        ?selected="${this.options.ipu}"
                        disabled
                      ></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div
                      class="vertical center-justified layout setting-desc-shrink"
                    >
                      <div class="title">${h("settings.ATOMsupport")}</div>
                      <div class="description-shrink">
                        ${v("settings.DescATOMsupport")}
                        <br />
                        ${h("settings.RequireATOMPlugin")}
                      </div>
                    </div>
                    <div
                      class="vertical center-justified layout setting-button"
                    >
                      <mwc-switch
                        id="atom-support-switch"
                        ?selected="${this.options.atom}"
                        disabled
                      ></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div
                      class="vertical center-justified layout setting-desc-shrink"
                    >
                      <div class="title">${h("settings.Warboysupport")}</div>
                      <div class="description-shrink">
                        ${v("settings.DescWarboysupport")}
                        <br />
                        ${h("settings.RequireWarboyPlugin")}
                      </div>
                    </div>
                    <div
                      class="vertical center-justified layout setting-button"
                    >
                      <mwc-switch
                        id="warboy-support-switch"
                        ?selected="${this.options.warboy}"
                        disabled
                      ></mwc-switch>
                    </div>
                  </div>
                  <div class="horizontal layout setting-item">
                    <div
                      class="vertical center-justified layout setting-desc-shrink"
                    >
                      <div class="title">
                        ${h("settings.HyperaccelLPUsupport")}
                      </div>
                      <div class="description-shrink">
                        ${v("settings.DescHyperaccelLPUsupport")}
                        <br />
                        ${h("settings.RequireHyperaccelLPUPlugin")}
                      </div>
                    </div>
                    <div
                      class="vertical center-justified layout setting-button"
                    >
                      <mwc-switch
                        id="hyperaccel-lpu-support-switch"
                        ?selected="${this.options.hyperaccel_lpu}"
                        disabled
                      ></mwc-switch>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </lablup-activity-panel>
        <backend-ai-dialog
          id="scheduler-env-dialog"
          class="env-dialog"
          fixed
          backdrop
          persistent
          closeWithConfirmation
        >
          <span slot="title" class="horizontal layout center">
            ${v("settings.ConfigPerJobSchduler")}
          </span>
          <span slot="action">
            <mwc-icon-button
              icon="info"
              @click="${t=>this._showConfigDescription(t,"default")}"
              style="pointer-events:auto;"
            ></mwc-icon-button>
          </span>
          <div
            slot="content"
            id="scheduler-env-container"
            class="vertical layout centered env-container"
            style="width: 100%;"
          >
            <mwc-select
              id="scheduler-switch"
              required
              label="${h("settings.Scheduler")}"
              style="margin-bottom: 10px;"
              validationMessage="${h("settings.SchedulerRequired")}"
              @selected="${t=>this.changeSelectedScheduleType(t)}"
            >
              ${this.jobschedulerType.map((t=>p`
                  <mwc-list-item value="${t}">
                    ${t.toUpperCase()}
                  </mwc-list-item>
                `))}
            </mwc-select>
            <h4>${h("settings.SchedulerOptions")}</h4>
            <div class="horizontal center layout flex row">
              <span slot="title">${h("settings.SessionCreationRetries")}</span>
              <mwc-icon-button
                icon="info"
                @click="${t=>this._showConfigDescription(t,"retries")}"
                style="pointer-events:auto;"
              ></mwc-icon-button>
              <mwc-textfield
                id="num-retries"
                required
                autoValidate
                validationMessage="${h("settings.InputRequired")}"
                type="number"
                pattern="[0-9]+"
                min="${this.optionRange.numRetries.min}"
                max="${this.optionRange.numRetries.max}"
                style="margin-top: 18px"
                @change="${t=>this._validateInput(t)}"
                @input="${t=>this._customizeValidationMessage(t)}"
              ></mwc-textfield>
            </div>
          </div>
          <div slot="footer" class="horizontal end-justified flex layout">
            <mwc-button
              id="config-cancel-button"
              style="width:auto;margin-right:10px;"
              icon="delete"
              @click="${()=>this._clearOptions("scheduler-env-container")}"
              label="${h("button.DeleteAll")}"
            ></mwc-button>
            <mwc-button
              unelevated
              id="config-save-button"
              style="width:auto;"
              icon="check"
              @click="${()=>this.saveAndCloseDialog()}"
              label="${h("button.Save")}"
            ></mwc-button>
          </div>
        </backend-ai-dialog>
        <backend-ai-dialog
          id="overlay-network-env-dialog"
          class="env-dialog"
          fixed
          backdrop
          persistent
          closeWithConfirmation
        >
          <span slot="title" class="horizontal layout center">
            ${v("settings.OverlayNetworkSettings")}
          </span>
          <span slot="action">
            <mwc-icon-button
              icon="info"
              @click="${t=>this._showConfigDescription(t,"overlayNetwork")}"
              style="pointer-events:auto;"
            ></mwc-icon-button>
          </span>
          <div
            slot="content"
            id="overlay-network-env-container"
            class="vertical layout centered env-container"
            style="width: 100%;"
          >
            <div class="horizontal center layout flex row justified">
              <div class="horizontal center layout">
                <span slot="title">MTU</span>
                <mwc-icon-button
                  icon="info"
                  @click="${t=>this._showConfigDescription(t,"mtu")}"
                  style="pointer-events:auto;"
                ></mwc-icon-button>
              </div>
              <mwc-textfield
                id="mtu"
                class="network-option"
                value="${this.options.network.mtu}"
                required
                autoValidate
                validationMessage="${h("settings.InputRequired")}"
                type="number"
                pattern="[0-9]+"
                min="${this.optionRange.mtu.min}"
                max="${this.optionRange.mtu.max}"
                style="margin-top:18px;min-width:240px;"
                @change="${t=>this._validateInput(t)}"
                @input="${t=>this._customizeValidationMessage(t)}"
              ></mwc-textfield>
            </div>
          </div>
          <div slot="footer" class="horizontal end-justified flex layout">
            <mwc-button
              id="config-cancel-button"
              style="width:auto;margin-right:10px;"
              icon="delete"
              @click="${()=>this._clearOptions("overlay-network-env-container")}"
              label="${h("button.DeleteAll")}"
            ></mwc-button>
            <mwc-button
              unelevated
              id="config-save-button"
              style="width:auto;"
              icon="check"
              @click="${()=>this.saveAndCloseOverlayNetworkDialog()}"
              label="${h("button.Save")}"
            ></mwc-button>
          </div>
        </backend-ai-dialog>
        <backend-ai-dialog id="help-description" fixed backdrop>
          <span slot="title">${this._helpDescriptionTitle}</span>
          <div slot="content" class="horizontal layout">
            ${this._helpDescription}
          </div>
        </backend-ai-dialog>
        <backend-ai-dialog id="env-config-confirmation" warning fixed>
          <span slot="title">${h("dialog.title.LetsDouble-Check")}</span>
          <div slot="content">
            <p>${h("settings.EnvConfigWillDisappear")}</p>
            <p>${h("dialog.ask.DoYouWantToProceed")}</p>
          </div>
          <div slot="footer" class="horizontal end-justified flex layout">
            <mwc-button
              id="env-config-remain-button"
              style="width:auto;"
              label="${h("button.Cancel")}"
              @click="${()=>this.closeDialog("env-config-confirmation")}"
            ></mwc-button>
            <mwc-button
              unelevated
              id="env-config-reset-button"
              style="width:auto;margin-right:10px;"
              label="${h("button.DismissAndProceed")}"
              @click="${()=>this.closeAndResetEnvInput()}"
            ></mwc-button>
          </div>
        </backend-ai-dialog>
      </div>
    `}firstUpdated(){this.notification=globalThis.lablupNotification,void 0===globalThis.backendaiclient||null===globalThis.backendaiclient?document.addEventListener("backend-ai-connected",(()=>{this.updateSettings()}),!0):this.updateSettings(),this.schedulerEnvDialog.addEventListener("dialog-closing-confirm",(t=>{var i,e;const s=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#scheduler-env-container"),o=Array.from(null==s?void 0:s.querySelectorAll("mwc-textfield"));for(const t of o){if(this.options.scheduler[null!==(e=this._findOptionById(t.id))&&void 0!==e?e:-1]!==t.value&&""!==this.selectedSchedulerType){this.openDialog("env-config-confirmation");break}this._closeDialogWithConfirmation("scheduler-env-dialog")}})),this.overlayNetworkEnvDialog.addEventListener("dialog-closing-confirm",(t=>{var i,e;const s=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#overlay-network-env-container"),o=Array.from(null==s?void 0:s.querySelectorAll("mwc-textfield"));for(const t of o){if(this.options.network[null!==(e=this._findOptionById(t.id))&&void 0!==e?e:""]!==t.value){this.openDialog("env-config-confirmation");break}this._closeDialogWithConfirmation("overlay-network-env-dialog")}}))}async _viewStateChanged(t){await this.updateComplete}updatePulling(){globalThis.backendaiclient.setting.get("docker/image/auto_pull").then((t=>{null===t.result||"digest"===t.result?this.options.image_pulling_behavior="digest":"tag"===t.result?this.options.image_pulling_behavior="tag":this.options.image_pulling_behavior="none",this.requestUpdate()}))}updateScheduler(){for(const[t]of Object.entries(this.options.scheduler))globalThis.backendaiclient.setting.get(`plugins/scheduler/${this.selectedSchedulerType}/${t}`).then((i=>{this.options.scheduler[t]=i.result||"0"})),this.requestUpdate()}updateNetwork(){for(const[t]of Object.entries(this.options.network))globalThis.backendaiclient.setting.get(`network/overlay/${t}`).then((i=>{this.options.network[t]=i.result||""})),this.requestUpdate()}updateResourceSlots(){globalThis.backendaiclient.get_resource_slots().then((t=>{"cuda.device"in t&&(this.options.cuda_gpu=!0),"cuda.shares"in t&&(this.options.cuda_fgpu=!0),"rocm.device"in t&&(this.options.rocm_gpu=!0),"tpu.device"in t&&(this.options.tpu=!0),"ipu.device"in t&&(this.options.ipu=!0),"warboy.device"in t&&(this.options.warboy=!0),"hyperaccel-lpu.device"in t&&(this.options["hyperaccel-lpu"]=!0),this.requestUpdate()}))}updateSettings(){this.updatePulling(),this.updateScheduler(),this.updateNetwork(),this.updateResourceSlots()}updateNetworkOptionElements(){var t,i;this.updateNetwork();const e=Array.from(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".network-option"));for(const t of e){const e=null!==(i=this._findOptionById(t.id))&&void 0!==i?i:"";t.value=this.options.network[e]||""}}setImagePullingBehavior(t){if(null===t.target.selected)return!1;const i=t.target.selected.value;return i!==this.options.image_pulling_behavior&&["none","digest","tag"].includes(i)&&globalThis.backendaiclient.setting.set("docker/image/auto_pull",i).then((t=>{this.options.image_pulling_behavior=i,this.notification.text=n("notification.SuccessfullyUpdated"),this.notification.show(),this.requestUpdate(),console.log(t)})),!0}_findIdByOption(t){var i;return null===(i=this.optionsAndId.find((i=>i.option===t)))||void 0===i?void 0:i.id}_findOptionById(t){var i;return null===(i=this.optionsAndId.find((i=>i.id===t)))||void 0===i?void 0:i.option}_clearOptions(t){var i;const e=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t);null==e||e.querySelectorAll("mwc-textfield").forEach((t=>{t.value=""}))}_openDialogWithConfirmation(t){var i;const e=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t);e.closeWithConfirmation=!0,null==e||e.show()}_closeDialogWithConfirmation(t){var i;const e=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t);e.closeWithConfirmation=!1,e.hide()}closeAndResetEnvInput(){var t;const i=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".env-dialog");for(const t of Array.from(i))if(t.open){const i=t.querySelector(".env-container");this._clearOptions(null==i?void 0:i.id),this.closeDialog("env-config-confirmation"),this._closeDialogWithConfirmation(t.id),"scheduler-env-dialog"===t.id&&(this.schedulerSelect.value="");break}}_showConfigDescription(t,i){t.stopPropagation();const e={default:{title:n("settings.ConfigPerJobSchduler"),desc:n("settings.ConfigPerJobSchdulerDescription")},retries:{title:n("settings.SessionCreationRetries"),desc:n("settings.SessionCreationRetriesDescription")+"\n"+n("settings.FifoOnly")},overlayNetwork:{title:n("settings.OverlayNetworkSettings"),desc:n("settings.OverlayNetworkSettingsDescription")},mtu:{title:"MTU",desc:n("settings.MTUDescription")}};i in e&&(this._helpDescriptionTitle=e[i].title,this._helpDescription=e[i].desc,this.helpDescriptionDialog.show())}openDialog(t){var i;(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t)).show()}closeDialog(t){var i;(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#"+t)).hide()}saveAndCloseDialog(){const t=this.numberOfRetries.value,i=[this.schedulerSelect,this.numberOfRetries];if(!(i.filter((t=>null==t?void 0:t.reportValidity())).length<i.length)&&["fifo","lifo","drf"].includes(this.selectedSchedulerType))if("fifo"===this.selectedSchedulerType||"fifo"!==this.selectedSchedulerType&&"0"===t){const i={num_retries_to_skip:parseInt(t).toString()};globalThis.backendaiclient.setting.set(`plugins/scheduler/${this.selectedSchedulerType}`,i).then((t=>{this.notification.text=n("notification.SuccessfullyUpdated"),this.notification.show(),this.options.schedulerType=this.selectedSchedulerType,this.options.scheduler={...this.options.scheduler,...i},this.requestUpdate(),this._closeDialogWithConfirmation("scheduler-env-dialog")})).catch((t=>{this.notification.text=g.relieve("Couldn't update scheduler setting."),this.notification.detail=t,this.notification.show(!0,t)}))}else"0"!==t&&(this.notification.text=n("settings.FifoOnly"),this.notification.show(),this.numberOfRetries.value="0")}saveAndCloseOverlayNetworkDialog(){var t,i;const e=Array.from(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelectorAll(".network-option"));if(e.filter((t=>t.reportValidity())).length<e.length)return;const s={};for(const t of e){const e=null!==(i=this._findOptionById(t.id))&&void 0!==i?i:"",o=t.value;if(""===o&&null===o&&void 0===o)return;s[e]=o}globalThis.backendaiclient.setting.set("network/overlay",s).then((t=>{this.notification.text=n("notification.SuccessfullyUpdated"),this.notification.show(),this.options.network={...this.options.network,...s},this.requestUpdate(),this._closeDialogWithConfirmation("overlay-network-env-dialog")})).catch((t=>{this.notification.text=g.relieve("Couldn't update scheduler setting."),this.notification.detail=t,this.notification.show(!0,t)}))}changeSelectedScheduleType(t){this.selectedSchedulerType=t.target.value,this.updateScheduler();for(const[t]of Object.entries(this.options.scheduler))globalThis.backendaiclient.setting.get(`plugins/scheduler/${this.selectedSchedulerType}/${t}`).then((i=>{var e;(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#"+this._findIdByOption(t))).value=i.result||"0"}))}_validateInput(t){const i=t.target.closest("mwc-textfield");i.value&&(i.value=Math.round(i.value),i.min&&i.max&&(i.value=globalThis.backendaiclient.utils.clamp(i.value,i.min,i.max)))}_customizeValidationMessage(t){const i=t.target.closest("mwc-textfield");i.validityTransform=(t,e)=>e.valid?{valid:e.valid,customError:!e.valid}:e.valueMissing?(i.validationMessage=n("settings.InputRequired"),{valid:e.valid,customError:!e.valid}):e.rangeOverflow||e.rangeUnderflow?(i.validationMessage=n("settings.OutOfRange"),{valid:e.valid,customError:!e.valid}):(i.validationMessage=n("settings.InvalidValue"),{valid:e.valid,customError:!e.valid})}};t([i({type:Object})],m.prototype,"images",void 0),t([i({type:Object})],m.prototype,"options",void 0),t([i({type:Object})],m.prototype,"schedulerOptions",void 0),t([i({type:Object})],m.prototype,"networkOptions",void 0),t([i({type:Object})],m.prototype,"optionsAndId",void 0),t([i({type:Object})],m.prototype,"notification",void 0),t([i({type:Array})],m.prototype,"imagePullingBehavior",void 0),t([i({type:Array})],m.prototype,"jobschedulerType",void 0),t([i({type:String})],m.prototype,"selectedSchedulerType",void 0),t([i({type:String})],m.prototype,"_helpDescriptionTitle",void 0),t([i({type:String})],m.prototype,"_helpDescription",void 0),t([i({type:Object})],m.prototype,"optionRange",void 0),t([e("#scheduler-switch")],m.prototype,"schedulerSelect",void 0),t([e("#num-retries")],m.prototype,"numberOfRetries",void 0),t([e("#scheduler-env-dialog")],m.prototype,"schedulerEnvDialog",void 0),t([e("#overlay-network-env-dialog")],m.prototype,"overlayNetworkEnvDialog",void 0),t([e("#help-description")],m.prototype,"helpDescriptionDialog",void 0),m=t([s("backend-ai-settings-view")],m);
