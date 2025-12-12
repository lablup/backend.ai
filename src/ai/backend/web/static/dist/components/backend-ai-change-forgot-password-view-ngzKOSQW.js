import{_ as e,c as t,t as i,B as a,a as o,I as s,b as n,d as l,e as d,i as r,C as c,f as h,g,h as p,j as w,k as u}from"./backend-ai-webui-CiZihJrO.js";let v=class extends a{constructor(){super(...arguments),this.webUIShell=Object(),this.clientConfig=Object(),this.client=Object(),this.notification=Object(),this.passwordChangeDialog=Object(),this.failDialog=Object(),this.token=""}static get styles(){return[o,s,n,l,d,r`
        mwc-textfield {
          width: 100%;
        }

        mwc-button,
        mwc-button[unelevated] {
          margin: auto 10px;
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
        }
      `]}_initClient(e){var t,i;this.webUIShell=document.querySelector("#webui-shell"),this.notification=globalThis.lablupNotification,this.passwordChangeDialog=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#update-password-dialog"),this.failDialog=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#verification-fail-dialog"),this.clientConfig=new c("","",e,"SESSION"),this.client=new h(this.clientConfig,"Backend.AI Web UI."),this.passwordChangeDialog.addEventListener("didHide",(()=>{this._redirectToLoginPage()})),this.failDialog.addEventListener("didHide",(()=>{this._redirectToLoginPage()}))}_redirectToLoginPage(){window.location.href="/"}open(e){var t;const i=new URLSearchParams(window.location.search);this.token=i.get("token")||"",this._initClient(e),this.token?(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#update-password-dialog")).show():this.failDialog.show()}async _updatePassword(){var e,t,i;const a=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#email"),o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#password1"),s=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#password2");if(a.value&&a.validity.valid&&o.value&&o.validity.valid){if(o.value!==s.value)return this.notification.text=g("webui.menu.PasswordMismatch"),void this.notification.show();try{await this.client.cloud.change_password(a.value,o.value,this.token),this.notification.text=g("login.PasswordChanged"),this.notification.show(),setTimeout((()=>{this._redirectToLoginPage()}),2e3)}catch(e){this.notification.text=e.message||g("error.UpdateError"),this.notification.show(),this.failDialog.show()}}}render(){return u`
      <backend-ai-dialog
        id="update-password-dialog"
        fixed
        backdrop
        blockscrolling
        persistent
        style="padding:0;"
      >
        <span slot="title">${p("webui.menu.ChangePassword")}</span>

        <div slot="content" class="login-panel intro centered">
          <div class="horizontal layout center" style="margin:10px;">
            <p style="width:350px;">${p("login.UpdatePasswordMessage")}</p>
          </div>
          <div style="margin:20px;">
            <mwc-textfield
              id="email"
              label="${p("data.explorer.EnterEmailAddress")}"
              autofocus
              auto-validate
              validationMessage="${p("signUp.InvalidEmail")}"
              pattern="^[A-Z0-9a-z#-_]+@.+\\..+$"
              maxLength="64"
              placeholder="${p("maxLength.64chars")}"
            ></mwc-textfield>
            <mwc-textfield
              id="password1"
              label="${p("webui.menu.NewPassword")}"
              type="password"
              auto-validate
              validationMessage="${p("webui.menu.InvalidPasswordMessage")}"
              pattern=${w.passwordRegex}
              maxLength="64"
            ></mwc-textfield>
            <mwc-textfield
              id="password2"
              label="${p("webui.menu.NewPasswordAgain")}"
              type="password"
              auto-validate
              validationMessage="${p("webui.menu.InvalidPasswordMessage")}"
              pattern=${w.passwordRegex}
              maxLength="64"
            ></mwc-textfield>
            <div style="height:1em"></div>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
            unelevated
            fullwidth
            label="${p("webui.menu.Update")}"
            @click="${()=>this._updatePassword()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog
        id="verification-fail-dialog"
        fixed
        backdrop
        blockscrolling
        persistent
        style="padding:0;"
      >
        <span slot="title">${p("login.InvalidChangePasswordToken")}</span>

        <div slot="content" class="login-panel intro centered">
          <h3 class="horizontal center layout">
            <span>${p("login.InvalidChangePasswordToken")}</span>
          </h3>
          <div class="horizontal layout center" style="margin:10px;">
            <p style="width:350px;">
              ${p("login.InvalidChangePasswordTokenMessage")}
            </p>
          </div>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            label="${p("button.Close")}"
            @click="${()=>this._redirectToLoginPage()}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};e([t({type:Object})],v.prototype,"webUIShell",void 0),e([t({type:Object})],v.prototype,"clientConfig",void 0),e([t({type:Object})],v.prototype,"client",void 0),e([t({type:Object})],v.prototype,"notification",void 0),e([t({type:Object})],v.prototype,"passwordChangeDialog",void 0),e([t({type:Object})],v.prototype,"failDialog",void 0),e([t({type:String})],v.prototype,"token",void 0),v=e([i("backend-ai-change-forgot-password-view")],v);
