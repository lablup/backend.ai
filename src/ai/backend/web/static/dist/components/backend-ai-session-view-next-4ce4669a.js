import{_ as i,e as s,B as t,c as a,I as e,a as r,i as o,x as n,j as m,k as c}from"./backend-ai-webui-313ccdcb.js";import"./backend-ai-session-launcher-aceb0b8f.js";import"./backend-ai-session-view-46b3adc0.js";import"./lablup-codemirror-aadc2540.js";import"./lablup-progress-bar-d53d89ea.js";import"./vaadin-grid-selection-column-8cfdb1f9.js";import"./vaadin-grid-1ec33dab.js";import"./dir-utils-700bf3b5.js";import"./mwc-check-list-item-ff01ea59.js";import"./vaadin-grid-filter-column-0778fd47.js";import"./vaadin-iconset-4fa1ac14.js";import"./backend-ai-resource-monitor-bf2108fa.js";import"./mwc-switch-6ccfff6c.js";import"./backend-ai-list-status-08ca4851.js";import"./lablup-grid-sort-filter-column-abec5e81.js";import"./vaadin-grid-sort-column-f9554c60.js";import"./lablup-activity-panel-f1333160.js";import"./mwc-formfield-8492fde0.js";import"./mwc-tab-bar-9bef57da.js";let p=class extends t{static get styles(){return[a,e,r,o``]}async _viewStateChanged(i){await this.updateComplete}render(){return n`
      <backend-ai-react-session-list
        @moveTo="${i=>{const s=i.detail.path;globalThis.history.pushState({},"",s),m.dispatch(c(decodeURIComponent(s),{}))}}"
      ></backend-ai-react-session-list>
    `}};p=i([s("backend-ai-session-view-next")],p);