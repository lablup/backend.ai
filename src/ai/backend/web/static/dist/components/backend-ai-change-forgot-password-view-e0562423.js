import{B as e,d as t,I as i,b as a,x as o,f as s,i as l,ax as n,ay as d,g as r,y as c,t as h,aw as g,_ as p,e as w,a as u}from"./backend-ai-webui-efd2500f.js";let v=class extends e{constructor(){super(...arguments),this.webUIShell=Object(),this.clientConfig=Object(),this.client=Object(),this.notification=Object(),this.passwordChangeDialog=Object(),this.failDialog=Object(),this.token=""}static get styles(){return[t,i,a,o,s,l`
        mwc-textfield {
          width: 100%;
        }

        mwc-button, mwc-button[unelevated] {
          margin: auto 10px;
          background-image: none;
          --mdc-theme-primary: var(--general-button-background-color);
          --mdc-theme-on-primary: var(--general-button-color);
        }
      `]}_initClient(e){var t,i;this.webUIShell=document.querySelector("#webui-shell"),this.webUIShell.appBody.style.visibility="visible",this.notification=globalThis.lablupNotification,this.passwordChangeDialog=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#update-password-dialog"),this.failDialog=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#verification-fail-dialog"),this.clientConfig=new n("","",e,"SESSION"),this.client=new d(this.clientConfig,"Backend.AI Web UI."),this.passwordChangeDialog.addEventListener("didHide",(()=>{this._redirectToLoginPage()})),this.failDialog.addEventListener("didHide",(()=>{this._redirectToLoginPage()}))}_redirectToLoginPage(){window.location.href="/"}open(e){var t;const i=new URLSearchParams(window.location.search);this.token=i.get("token")||"",this._initClient(e),this.token?(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#update-password-dialog")).show():this.failDialog.show()}async _updatePassword(){var e,t,i;const a=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#email"),o=null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#password1"),s=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#password2");if(a.value&&a.validity.valid&&o.value&&o.validity.valid){if(o.value!==s.value)return this.notification.text=r("webui.menu.PasswordMismatch"),void this.notification.show();try{await this.client.cloud.change_password(a.value,o.value,this.token),this.notification.text=r("login.PasswordChanged"),this.notification.show(),setTimeout((()=>{this._redirectToLoginPage()}),2e3)}catch(e){console.error(e),this.notification.text=e.message||r("error.UpdateError"),this.notification.show(),this.failDialog.show()}}}render(){return c`
      <backend-ai-dialog id="update-password-dialog" fixed backdrop blockscrolling persistent style="padding:0;">
        <span slot="title">${h("webui.menu.ChangePassword")}</span>

        <div slot="content" class="login-panel intro centered">
          <div class="horizontal layout center" style="margin:10px;">
            <p style="width:350px;">${h("login.UpdatePasswordMessage")}</p>
          </div>
          <div style="margin:20px;">
            <mwc-textfield id="email" label="${h("data.explorer.EnterEmailAddress")}"
                autofocus auto-validate validationMessage="${h("signup.InvalidEmail")}"
                pattern="^[A-Z0-9a-z#-_]+@.+\\..+$" maxLength="64"
                placeholder="${h("maxLength.64chars")}">
            </mwc-textfield>
            <mwc-textfield id="password1" label="${h("webui.menu.NewPassword")}" type="password"
                auto-validate validationMessage="${h("webui.menu.InvalidPasswordMessage")}"
                pattern=${g.passwordRegex}
                maxLength="64">
            </mwc-textfield>
            <mwc-textfield id="password2" label="${h("webui.menu.NewPasswordAgain")}" type="password"
                auto-validate validationMessage="${h("webui.menu.InvalidPasswordMessage")}"
                pattern=${g.passwordRegex}
                maxLength="64">
            </mwc-textfield>
            <div style="height:1em"></div>
          </div>
        </div>
        <div slot="footer" class="horizontal center-justified flex layout">
          <mwc-button
              unelevated
              fullwidth
              label="${h("webui.menu.Update")}"
              @click="${()=>this._updatePassword()}"></mwc-button>
        </div>
      </backend-ai-dialog>

      <backend-ai-dialog id="verification-fail-dialog" fixed backdrop blockscrolling persistent style="padding:0;">
        <span slot="title">${h("login.InvalidChangePasswordToken")}</span>

        <div slot="content" class="login-panel intro centered">
          <h3 class="horizontal center layout">
            <span>${h("login.InvalidChangePasswordToken")}</span>
          </h3>
          <div class="horizontal layout center" style="margin:10px;">
            <p style="width:350px;">${h("login.InvalidChangePasswordTokenMessage")}</p>
          </div>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
              unelevated
              label="${h("button.Close")}"
              @click="${()=>this._redirectToLoginPage()}"></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};p([w({type:Object})],v.prototype,"webUIShell",void 0),p([w({type:Object})],v.prototype,"clientConfig",void 0),p([w({type:Object})],v.prototype,"client",void 0),p([w({type:Object})],v.prototype,"notification",void 0),p([w({type:Object})],v.prototype,"passwordChangeDialog",void 0),p([w({type:Object})],v.prototype,"failDialog",void 0),p([w({type:String})],v.prototype,"token",void 0),v=p([u("backend-ai-change-forgot-password-view")],v);var b=v;export{b as default};
