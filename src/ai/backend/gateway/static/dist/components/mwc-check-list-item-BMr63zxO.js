import{_ as e,au as t,av as s,aw as i,A as c,E as h,H as a,ax as o,ay as r}from"./backend-ai-webui-dvRyOX_e.js";
/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */class d extends i{constructor(){super(...arguments),this.left=!1,this.graphic="control"}render(){const e={"mdc-deprecated-list-item__graphic":this.left,"mdc-deprecated-list-item__meta":!this.left},t=this.renderText(),s=this.graphic&&"control"!==this.graphic&&!this.left?this.renderGraphic():c``,i=this.hasMeta&&this.left?this.renderMeta():c``,a=this.renderRipple();return c`
      ${a}
      ${s}
      ${this.left?"":t}
      <span class=${h(e)}>
        <mwc-checkbox
            reducedTouchTarget
            tabindex=${this.tabindex}
            .checked=${this.selected}
            ?disabled=${this.disabled}
            @change=${this.onChange}>
        </mwc-checkbox>
      </span>
      ${this.left?t:""}
      ${i}`}async onChange(e){const t=e.target;this.selected===t.checked||(this._skipPropRequest=!0,this.selected=t.checked,await this.updateComplete,this._skipPropRequest=!1)}}e([t("slot")],d.prototype,"slotElement",void 0),e([t("mwc-checkbox")],d.prototype,"checkboxElement",void 0),e([s({type:Boolean})],d.prototype,"left",void 0),e([s({type:String,reflect:!0})],d.prototype,"graphic",void 0);
/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-LIcense-Identifier: Apache-2.0
 */
const l=a`:host(:not([twoline])){height:56px}:host(:not([left])) .mdc-deprecated-list-item__meta{height:40px;width:40px}`
/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */;let p=class extends d{};p.styles=[o,l],p=e([r("mwc-check-list-item")],p);
