import{m as e,r as i,i as t,o as s,p as o,q as n,T as a,D as l,P as r,_ as c,n as d,e as u,t as p,B as m,b as h,I as g,a as v,d as _,Q as b,k as f,g as y,f as w,u as k,v as x,c as A}from"./backend-ai-webui-IlRp-wMX.js";import{J as $}from"./vaadin-iconset-CZFHCGnf.js";import"./backend-ai-resource-monitor-B1HfxIaA.js";import"./backend-ai-session-launcher-DDvnRQ1c.js";import"./backend-ai-list-status-DcROmRWA.js";import"./lablup-grid-sort-filter-column-DbDzS1KJ.js";import"./lablup-progress-bar-C2c3e07h.js";import"./vaadin-grid-filter-column-CozmkQTP.js";import"./lablup-activity-panel-BI3aowK_.js";import"./mwc-formfield-D9BqVf7g.js";import"./mwc-tab-bar-DoeSypsQ.js";import"./mwc-switch-C-zaXCpc.js";import"./slider-DSxqDIxt.js";import"./mwc-check-list-item-AcYXY5QB.js";
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */let S;var T;!function(e){e[e.EOS=0]="EOS",e[e.Text=1]="Text",e[e.Incomplete=2]="Incomplete",e[e.ESC=3]="ESC",e[e.Unknown=4]="Unknown",e[e.SGR=5]="SGR",e[e.OSCURL=6]="OSCURL"}(T||(T={}));var C=function(){function e(){this.VERSION="4.0.3",this.setup_palettes(),this._use_classes=!1,this._escape_for_html=!0,this.bold=!1,this.fg=this.bg=null,this._buffer="",this._url_whitelist={http:1,https:1}}return Object.defineProperty(e.prototype,"use_classes",{get:function(){return this._use_classes},set:function(e){this._use_classes=e},enumerable:!0,configurable:!0}),Object.defineProperty(e.prototype,"escape_for_html",{get:function(){return this._escape_for_html},set:function(e){this._escape_for_html=e},enumerable:!0,configurable:!0}),Object.defineProperty(e.prototype,"url_whitelist",{get:function(){return this._url_whitelist},set:function(e){this._url_whitelist=e},enumerable:!0,configurable:!0}),e.prototype.setup_palettes=function(){var e=this;this.ansi_colors=[[{rgb:[0,0,0],class_name:"ansi-black"},{rgb:[187,0,0],class_name:"ansi-red"},{rgb:[0,187,0],class_name:"ansi-green"},{rgb:[187,187,0],class_name:"ansi-yellow"},{rgb:[0,0,187],class_name:"ansi-blue"},{rgb:[187,0,187],class_name:"ansi-magenta"},{rgb:[0,187,187],class_name:"ansi-cyan"},{rgb:[255,255,255],class_name:"ansi-white"}],[{rgb:[85,85,85],class_name:"ansi-bright-black"},{rgb:[255,85,85],class_name:"ansi-bright-red"},{rgb:[0,255,0],class_name:"ansi-bright-green"},{rgb:[255,255,85],class_name:"ansi-bright-yellow"},{rgb:[85,85,255],class_name:"ansi-bright-blue"},{rgb:[255,85,255],class_name:"ansi-bright-magenta"},{rgb:[85,255,255],class_name:"ansi-bright-cyan"},{rgb:[255,255,255],class_name:"ansi-bright-white"}]],this.palette_256=[],this.ansi_colors.forEach((function(i){i.forEach((function(i){e.palette_256.push(i)}))}));for(var i=[0,95,135,175,215,255],t=0;t<6;++t)for(var s=0;s<6;++s)for(var o=0;o<6;++o){var n={rgb:[i[t],i[s],i[o]],class_name:"truecolor"};this.palette_256.push(n)}for(var a=8,l=0;l<24;++l,a+=10){var r={rgb:[a,a,a],class_name:"truecolor"};this.palette_256.push(r)}},e.prototype.escape_txt_for_html=function(e){return e.replace(/[&<>]/gm,(function(e){return"&"===e?"&amp;":"<"===e?"&lt;":">"===e?"&gt;":void 0}))},e.prototype.append_buffer=function(e){var i=this._buffer+e;this._buffer=i},e.prototype.__makeTemplateObject=function(e,i){return Object.defineProperty?Object.defineProperty(e,"raw",{value:i}):e.raw=i,e},e.prototype.get_next_packet=function(){var e={kind:T.EOS,text:"",url:""},i=this._buffer.length;if(0==i)return e;var t,s,o,n,a=this._buffer.indexOf("");if(-1==a)return e.kind=T.Text,e.text=this._buffer,this._buffer="",e;if(a>0)return e.kind=T.Text,e.text=this._buffer.slice(0,a),this._buffer=this._buffer.slice(a),e;if(0==a){if(1==i)return e.kind=T.Incomplete,e;var l=this._buffer.charAt(1);if("["!=l&&"]"!=l)return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;if("["==l){if(this._csi_regex||(this._csi_regex=I(this.__makeTemplateObject(["\n                        ^                           # beginning of line\n                                                    #\n                                                    # First attempt\n                        (?:                         # legal sequence\n                          [                      # CSI\n                          ([<-?]?)              # private-mode char\n                          ([d;]*)                    # any digits or semicolons\n                          ([ -/]?               # an intermediate modifier\n                          [@-~])                # the command\n                        )\n                        |                           # alternate (second attempt)\n                        (?:                         # illegal sequence\n                          [                      # CSI\n                          [ -~]*                # anything legal\n                          ([\0-:])              # anything illegal\n                        )\n                    "],["\n                        ^                           # beginning of line\n                                                    #\n                                                    # First attempt\n                        (?:                         # legal sequence\n                          \\x1b\\[                      # CSI\n                          ([\\x3c-\\x3f]?)              # private-mode char\n                          ([\\d;]*)                    # any digits or semicolons\n                          ([\\x20-\\x2f]?               # an intermediate modifier\n                          [\\x40-\\x7e])                # the command\n                        )\n                        |                           # alternate (second attempt)\n                        (?:                         # illegal sequence\n                          \\x1b\\[                      # CSI\n                          [\\x20-\\x7e]*                # anything legal\n                          ([\\x00-\\x1f:])              # anything illegal\n                        )\n                    "]))),null===(d=this._buffer.match(this._csi_regex)))return e.kind=T.Incomplete,e;if(d[4])return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;""!=d[1]||"m"!=d[3]?e.kind=T.Unknown:e.kind=T.SGR,e.text=d[2];var r=d[0].length;return this._buffer=this._buffer.slice(r),e}if("]"==l){if(i<4)return e.kind=T.Incomplete,e;if("8"!=this._buffer.charAt(2)||";"!=this._buffer.charAt(3))return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;this._osc_st||(this._osc_st=(t=this.__makeTemplateObject(["\n                        (?:                         # legal sequence\n                          (\\)                    # ESC                           |                           # alternate\n                          ()                      # BEL (what xterm did)\n                        )\n                        |                           # alternate (second attempt)\n                        (                           # illegal sequence\n                          [\0-]                 # anything illegal\n                          |                           # alternate\n                          [\b-]                 # anything illegal\n                          |                           # alternate\n                          [-]                 # anything illegal\n                        )\n                    "],["\n                        (?:                         # legal sequence\n                          (\\x1b\\\\)                    # ESC \\\n                          |                           # alternate\n                          (\\x07)                      # BEL (what xterm did)\n                        )\n                        |                           # alternate (second attempt)\n                        (                           # illegal sequence\n                          [\\x00-\\x06]                 # anything illegal\n                          |                           # alternate\n                          [\\x08-\\x1a]                 # anything illegal\n                          |                           # alternate\n                          [\\x1c-\\x1f]                 # anything illegal\n                        )\n                    "]),s=t.raw[0],o=/^\s+|\s+\n|\s*#[\s\S]*?\n|\n/gm,n=s.replace(o,""),new RegExp(n,"g"))),this._osc_st.lastIndex=0;var c=this._osc_st.exec(this._buffer);if(null===c)return e.kind=T.Incomplete,e;if(c[3])return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;var d,u=this._osc_st.exec(this._buffer);if(null===u)return e.kind=T.Incomplete,e;if(u[3])return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;if(this._osc_regex||(this._osc_regex=I(this.__makeTemplateObject(["\n                        ^                           # beginning of line\n                                                    #\n                        ]8;                    # OSC Hyperlink\n                        [ -:<-~]*       # params (excluding ;)\n                        ;                           # end of params\n                        ([!-~]{0,512})        # URL capture\n                        (?:                         # ST\n                          (?:\\)                  # ESC                           |                           # alternate\n                          (?:)                    # BEL (what xterm did)\n                        )\n                        ([!-~]+)              # TEXT capture\n                        ]8;;                   # OSC Hyperlink End\n                        (?:                         # ST\n                          (?:\\)                  # ESC                           |                           # alternate\n                          (?:)                    # BEL (what xterm did)\n                        )\n                    "],["\n                        ^                           # beginning of line\n                                                    #\n                        \\x1b\\]8;                    # OSC Hyperlink\n                        [\\x20-\\x3a\\x3c-\\x7e]*       # params (excluding ;)\n                        ;                           # end of params\n                        ([\\x21-\\x7e]{0,512})        # URL capture\n                        (?:                         # ST\n                          (?:\\x1b\\\\)                  # ESC \\\n                          |                           # alternate\n                          (?:\\x07)                    # BEL (what xterm did)\n                        )\n                        ([\\x21-\\x7e]+)              # TEXT capture\n                        \\x1b\\]8;;                   # OSC Hyperlink End\n                        (?:                         # ST\n                          (?:\\x1b\\\\)                  # ESC \\\n                          |                           # alternate\n                          (?:\\x07)                    # BEL (what xterm did)\n                        )\n                    "]))),null===(d=this._buffer.match(this._osc_regex)))return e.kind=T.ESC,e.text=this._buffer.slice(0,1),this._buffer=this._buffer.slice(1),e;e.kind=T.OSCURL,e.url=d[1],e.text=d[2];r=d[0].length;return this._buffer=this._buffer.slice(r),e}}},e.prototype.ansi_to_html=function(e){this.append_buffer(e);for(var i=[];;){var t=this.get_next_packet();if(t.kind==T.EOS||t.kind==T.Incomplete)break;t.kind!=T.ESC&&t.kind!=T.Unknown&&(t.kind==T.Text?i.push(this.transform_to_html(this.with_state(t))):t.kind==T.SGR?this.process_ansi(t):t.kind==T.OSCURL&&i.push(this.process_hyperlink(t)))}return i.join("")},e.prototype.with_state=function(e){return{bold:this.bold,fg:this.fg,bg:this.bg,text:e.text}},e.prototype.process_ansi=function(e){for(var i=e.text.split(";");i.length>0;){var t=i.shift(),s=parseInt(t,10);if(isNaN(s)||0===s)this.fg=this.bg=null,this.bold=!1;else if(1===s)this.bold=!0;else if(22===s)this.bold=!1;else if(39===s)this.fg=null;else if(49===s)this.bg=null;else if(s>=30&&s<38)this.fg=this.ansi_colors[0][s-30];else if(s>=40&&s<48)this.bg=this.ansi_colors[0][s-40];else if(s>=90&&s<98)this.fg=this.ansi_colors[1][s-90];else if(s>=100&&s<108)this.bg=this.ansi_colors[1][s-100];else if((38===s||48===s)&&i.length>0){var o=38===s,n=i.shift();if("5"===n&&i.length>0){var a=parseInt(i.shift(),10);a>=0&&a<=255&&(o?this.fg=this.palette_256[a]:this.bg=this.palette_256[a])}if("2"===n&&i.length>2){var l=parseInt(i.shift(),10),r=parseInt(i.shift(),10),c=parseInt(i.shift(),10);if(l>=0&&l<=255&&r>=0&&r<=255&&c>=0&&c<=255){var d={rgb:[l,r,c],class_name:"truecolor"};o?this.fg=d:this.bg=d}}}}},e.prototype.transform_to_html=function(e){var i=e.text;if(0===i.length)return i;if(this._escape_for_html&&(i=this.escape_txt_for_html(i)),!e.bold&&null===e.fg&&null===e.bg)return i;var t=[],s=[],o=e.fg,n=e.bg;e.bold&&t.push("font-weight:bold"),this._use_classes?(o&&("truecolor"!==o.class_name?s.push(o.class_name+"-fg"):t.push("color:rgb("+o.rgb.join(",")+")")),n&&("truecolor"!==n.class_name?s.push(n.class_name+"-bg"):t.push("background-color:rgb("+n.rgb.join(",")+")"))):(o&&t.push("color:rgb("+o.rgb.join(",")+")"),n&&t.push("background-color:rgb("+n.rgb+")"));var a="",l="";return s.length&&(a=' class="'+s.join(" ")+'"'),t.length&&(l=' style="'+t.join(";")+'"'),"<span"+l+a+">"+i+"</span>"},e.prototype.process_hyperlink=function(e){var i=e.url.split(":");return i.length<1?"":this._url_whitelist[i[0]]?'<a href="'+this.escape_txt_for_html(e.url)+'">'+this.escape_txt_for_html(e.text)+"</a>":""},e}();function I(e){var i=e.raw[0].replace(/^\s+|\s+\n|\s*#[\s\S]*?\n|\n/gm,"");return new RegExp(i)}i("vaadin-grid-tree-toggle",t`
    :host {
      --vaadin-grid-tree-toggle-level-offset: 2em;
      align-items: center;
      vertical-align: middle;
      transform: translateX(calc(var(--lumo-space-s) * -1));
      -webkit-tap-highlight-color: transparent;
    }

    :host(:not([leaf])) {
      cursor: default;
    }

    [part='toggle'] {
      display: inline-block;
      font-size: 1.5em;
      line-height: 1;
      width: 1em;
      height: 1em;
      text-align: center;
      color: var(--lumo-contrast-50pct);
      cursor: var(--lumo-clickable-cursor);
      /* Increase touch target area */
      padding: calc(1em / 3);
      margin: calc(1em / -3);
    }

    :host(:not([dir='rtl'])) [part='toggle'] {
      margin-right: 0;
    }

    @media (hover: hover) {
      :host(:hover) [part='toggle'] {
        color: var(--lumo-contrast-80pct);
      }
    }

    [part='toggle']::before {
      font-family: 'lumo-icons';
      display: inline-block;
      height: 100%;
    }

    :host(:not([expanded])) [part='toggle']::before {
      content: var(--lumo-icons-angle-right);
    }

    :host([expanded]) [part='toggle']::before {
      content: var(--lumo-icons-angle-right);
      transform: rotate(90deg);
    }

    /* Experimental support for hierarchy connectors, using an unsupported selector */
    :host([theme~='connectors']) #level-spacer {
      position: relative;
      z-index: -1;
      font-size: 1em;
      height: 1.5em;
    }

    :host([theme~='connectors']) #level-spacer::before {
      display: block;
      content: '';
      margin-top: calc(var(--lumo-space-m) * -1);
      height: calc(var(--lumo-space-m) + 3em);
      background-image: linear-gradient(
        to right,
        transparent calc(var(--vaadin-grid-tree-toggle-level-offset) - 1px),
        var(--lumo-contrast-10pct) calc(var(--vaadin-grid-tree-toggle-level-offset) - 1px)
      );
      background-size: var(--vaadin-grid-tree-toggle-level-offset) var(--vaadin-grid-tree-toggle-level-offset);
      background-position: calc(var(--vaadin-grid-tree-toggle-level-offset) / 2 - 2px) 0;
    }

    /* RTL specific styles */

    :host([dir='rtl']) {
      margin-left: 0;
      margin-right: calc(var(--lumo-space-s) * -1);
    }

    :host([dir='rtl']) [part='toggle'] {
      margin-left: 0;
    }

    :host([dir='rtl'][expanded]) [part='toggle']::before {
      transform: rotate(-90deg);
    }

    :host([dir='rtl'][theme~='connectors']) #level-spacer::before {
      background-image: linear-gradient(
        to left,
        transparent calc(var(--vaadin-grid-tree-toggle-level-offset) - 1px),
        var(--lumo-contrast-10pct) calc(var(--vaadin-grid-tree-toggle-level-offset) - 1px)
      );
      background-position: calc(100% - (var(--vaadin-grid-tree-toggle-level-offset) / 2 - 2px)) 0;
    }

    :host([dir='rtl']:not([expanded])) [part='toggle']::before,
    :host([dir='rtl'][expanded]) [part='toggle']::before {
      content: var(--lumo-icons-angle-left);
    }
  `,{moduleId:"lumo-grid-tree-toggle"});
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */
const D=document.createElement("template");D.innerHTML="\n  <style>\n    @font-face {\n      font-family: \"vaadin-grid-tree-icons\";\n      src: url(data:application/font-woff;charset=utf-8;base64,d09GRgABAAAAAAQkAA0AAAAABrwAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAABGRlRNAAAECAAAABoAAAAcgHwa6EdERUYAAAPsAAAAHAAAAB4AJwAOT1MvMgAAAZQAAAA/AAAAYA8TBIJjbWFwAAAB8AAAAFUAAAFeGJvXWmdhc3AAAAPkAAAACAAAAAgAAAAQZ2x5ZgAAAlwAAABLAAAAhIrPOhFoZWFkAAABMAAAACsAAAA2DsJI02hoZWEAAAFcAAAAHQAAACQHAgPHaG10eAAAAdQAAAAZAAAAHAxVAgBsb2NhAAACSAAAABIAAAASAIAAVG1heHAAAAF8AAAAGAAAACAACgAFbmFtZQAAAqgAAAECAAACTwflzbdwb3N0AAADrAAAADYAAABZQ7Ajh3icY2BkYGAA4twv3Vfi+W2+MnCzMIDANSOmbGSa2YEZRHEwMIEoAAoiB6sAeJxjYGRgYD7w/wADAwsDCDA7MDAyoAI2AFEEAtIAAAB4nGNgZGBg4GBgZgDRDAxMDGgAAAGbABB4nGNgZp7JOIGBlYGBaSbTGQYGhn4IzfiawZiRkwEVMAqgCTA4MDA+38d84P8BBgdmIAapQZJVYGAEAGc/C54AeJxjYYAAxlAIzQTELAwMBxgZGB0ACy0BYwAAAHicY2BgYGaAYBkGRgYQiADyGMF8FgYbIM3FwMHABISMDArP9/3/+/8/WJXC8z0Q9v8nEp5gHVwMMMAIMo+RDYiZoQJMQIKJARUA7WBhGN4AACFKDtoAAAAAAAAAAAgACAAQABgAJgA0AEIAAHichYvBEYBADAKBVHBjBT4swl9KS2k05o0XHd/yW1hAfBFwCv9sIlJu3nZaNS3PXAaXXHI8Lge7DlzF7C1RgXc7xkK6+gvcD2URmQB4nK2RQWoCMRiFX3RUqtCli65yADModOMBLLgQSqHddRFnQghIAnEUvEA3vUUP0LP0Fj1G+yb8R5iEhO9/ef/7FwFwj28o9EthiVp4hBlehcfUP4Ur8o/wBAv8CU+xVFvhOR7UB7tUdUdlVRJ6HnHWTnhM/V24In8JT5j/KzzFSi2E53hUz7jCcrcIiDDwyKSW1JEct2HdIPH1DFytbUM0PofWdNk5E5oUqb/Q6HHBiVGZpfOXkyUMEj5IyBuNmYZQjBobfsuassvnkKLe1OuBBj0VQ8cRni2xjLWsHaM0jrjx3peYA0/vrdmUYqe9iy7bzrX6eNP7Jh1SijX+AaUVbB8AAHicY2BiwA84GBgYmRiYGJkZmBlZGFkZ2djScyoLMgzZS/MyDQwMwLSruZMzlHaB0q4A76kLlwAAAAEAAf//AA94nGNgZGBg4AFiMSBmYmAEQnYgZgHzGAAD6wA2eJxjYGBgZACCKxJigiD6mhFTNowGACmcA/8AAA==) format('woff');\n      font-weight: normal;\n      font-style: normal;\n    }\n  </style>\n",document.head.appendChild(D.content),i("vaadin-grid-tree-toggle",t`
    :host {
      display: inline-flex;
      align-items: baseline;
      max-width: 100%;

      /* CSS API for :host */
      --vaadin-grid-tree-toggle-level-offset: 1em;
      --_collapsed-icon: '\\e7be\\00a0';
    }

    :host([dir='rtl']) {
      --_collapsed-icon: '\\e7bd\\00a0';
    }

    :host([hidden]) {
      display: none !important;
    }

    :host(:not([leaf])) {
      cursor: pointer;
    }

    #level-spacer,
    [part='toggle'] {
      flex: none;
    }

    #level-spacer {
      display: inline-block;
      width: calc(var(---level, '0') * var(--vaadin-grid-tree-toggle-level-offset));
    }

    [part='toggle']::before {
      font-family: 'vaadin-grid-tree-icons';
      line-height: 1em; /* make icon font metrics not affect baseline */
    }

    :host(:not([expanded])) [part='toggle']::before {
      content: var(--_collapsed-icon);
    }

    :host([expanded]) [part='toggle']::before {
      content: '\\e7bc\\00a0'; /* icon glyph + single non-breaking space */
    }

    :host([leaf]) [part='toggle'] {
      visibility: hidden;
    }

    slot {
      display: block;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  `,{moduleId:"vaadin-grid-tree-toggle-styles"});const E=e=>class extends e{static get properties(){return{level:{type:Number,value:0,observer:"_levelChanged",sync:!0},leaf:{type:Boolean,value:!1,reflectToAttribute:!0},expanded:{type:Boolean,value:!1,reflectToAttribute:!0,notify:!0,sync:!0}}}constructor(){super(),this.addEventListener("click",(e=>this._onClick(e)))}_onClick(e){this.leaf||s(e.target)||e.target instanceof HTMLLabelElement||(e.preventDefault(),this.expanded=!this.expanded)}_levelChanged(e){const i=Number(e).toString();this.style.setProperty("---level",i)}}
/**
 * @license
 * Copyright (c) 2016 - 2024 Vaadin Ltd.
 * This program is available under Apache License Version 2.0, available at https://vaadin.com/license/
 */;class R extends(E(a(l(r)))){static get is(){return"vaadin-grid-tree-toggle"}static get template(){return n`
      <span id="level-spacer"></span>
      <span part="toggle"></span>
      <slot></slot>
    `}}var j;o(R);let N=j=class extends m{constructor(){super(),this.active=!1,this.condition="running",this.jobs=Object(),this.filterAccessKey="",this.sessionNameField="name",this.appSupportList=[],this.appTemplate=Object(),this.imageInfo=Object(),this._boundControlRenderer=this.controlRenderer.bind(this),this._boundConfigRenderer=this.configRenderer.bind(this),this._boundUsageRenderer=this.usageRenderer.bind(this),this._boundReservationRenderer=this.reservationRenderer.bind(this),this._boundIdleChecksHeaderderer=this.idleChecksHeaderRenderer.bind(this),this._boundIdleChecksRenderer=this.idleChecksRenderer.bind(this),this._boundAgentListRenderer=this.agentListRenderer.bind(this),this._boundSessionInfoRenderer=this.sessionInfoRenderer.bind(this),this._boundArchitectureRenderer=this.architectureRenderer.bind(this),this._boundUserInfoRenderer=this.userInfoRenderer.bind(this),this._boundStatusRenderer=this.statusRenderer.bind(this),this._boundSessionTypeRenderer=this.sessionTypeRenderer.bind(this),this.refreshing=!1,this.is_admin=!1,this.is_superadmin=!1,this._connectionMode="API",this.notification=Object(),this.enableScalingGroup=!1,this.isDisplayingAllocatedShmemEnabled=!1,this.listCondition="loading",this.refreshTimer=Object(),this.kernel_labels=Object(),this.kernel_icons=Object(),this.indicator=Object(),this._helpDescription="",this._helpDescriptionTitle="",this._helpDescriptionIcon="",this.statusColorTable=new Proxy({"idle-timeout":"green","user-requested":"green",scheduled:"green","failed-to-start":"red","creation-failed":"red","self-terminated":"green"},{get:(e,i)=>e.hasOwnProperty(i)?e[i]:"lightgrey"}),this.idleChecksTable=new Proxy({network_timeout:"NetworkIdleTimeout",session_lifetime:"MaxSessionLifetime",utilization:"UtilizationIdleTimeout",expire_after:"ExpiresAfter",grace_period:"GracePeriod",cpu_util:"CPU",mem:"MEM",cuda_util:"GPU",cuda_mem:"GPU(MEM)",ipu_util:"IPU",ipu_mem:"IPU(MEM)"},{get:(e,i)=>e.hasOwnProperty(i)?e[i]:i}),this.sessionTypeColorTable=new Proxy({INTERACTIVE:"green",BATCH:"darkgreen",INFERENCE:"blue"},{get:(e,i)=>e.hasOwnProperty(i)?e[i]:"lightgrey"}),this.sshPort=0,this.vncPort=0,this.current_page=1,this.session_page_limit=50,this.total_session_count=0,this._APIMajorVersion=5,this.selectedSessionStatus=Object(),this.isUserInfoMaskEnabled=!1,this.pushImageInsteadOfCommiting=!1,this.canStartImagifying=!1,this.newImageName="",this._isContainerCommitEnabled=!1,this._isPerKernelLogSupported=!1,this.getUtilizationCheckerColor=(e,i=null)=>{const t="var(--token-colorSuccess)",s="var(--token-colorWarning)",o="var(--token-colorError)";if(i){let n=t;return"and"===i?Object.values(e).every((([e,i])=>e<Math.min(2*i,i+5)))?n=o:Object.values(e).every((([e,i])=>e<Math.min(10*i,i+10)))&&(n=s):"or"===i&&(Object.values(e).some((([e,i])=>e<Math.min(2*i,i+5)))?n=o:Object.values(e).some((([e,i])=>e<Math.min(10*i,i+10)))&&(n=s)),n}{const[i,n]=e;return i<2*n?o:i<10*n?s:t}},this.compute_sessions=[],this.selectedKernels=[],this._selected_items=[],this._manualCleanUpNeededContainers=[],this.terminationQueue=[],this.activeIdleCheckList=new Set}static get styles(){return[h,g,v,t`
        vaadin-grid {
          border: 0;
          font-size: 14px;
          height: calc(100vh - 265px);
        }

        mwc-icon.pagination {
          color: var(--paper-grey-700);
        }

        lablup-expansion {
          width: 100%;
          --expansion-header-padding: 15px;
          --expansion-header-font-size: 14px;
        }

        mwc-button.pagination {
          width: 15px;
          height: 15px;
          padding: 10px;
          box-shadow: 0px 2px 2px rgba(0, 0, 0, 0.2);
          --button-bg: transparent;
          --button-bg-hover: var(--paper-red-100);
          --button-bg-active: var(--paper-red-600);
          --button-bg-active-flat: var(--paper-red-600);
          --button-bg-disabled: var(--paper-grey-50);
          --button-color-disabled: var(--paper-grey-200);
        }

        mwc-button.pagination[disabled] {
          --button-shadow-color: transparent;
        }

        mwc-icon-button.controls-running {
          --mdc-icon-size: 24px;
        }

        img.indicator-icon {
          max-width: 16px !important;
          max-height: 16px !important;
          width: auto;
          height: auto;
          align-self: center;
          padding-right: 5px;
        }

        mwc-checkbox {
          margin: 0 0 0 -6px;
          padding: 0;
        }

        mwc-checkbox.list-check {
          margin: 6px 0 0 0;
        }

        mwc-icon {
          margin-right: 5px;
        }

        mwc-icon.indicator {
          --mdc-icon-size: 16px;
        }

        mwc-icon.status-check {
          --mdc-icon-size: 16px;
        }

        mwc-icon-button.apps {
          --mdc-icon-button-size: 48px;
          --mdc-icon-size: 36px;
          padding: 3px;
          margin-right: 5px;
        }

        mwc-icon-button.status {
          --mdc-icon-button-size: 36px;
          padding: 0;
        }

        mwc-list-item {
          --mdc-typography-body2-font-size: 12px;
          --mdc-list-item-graphic-margin: 10px;
        }

        mwc-textfield {
          width: 100%;
        }

        lablup-shields.right-below-margin {
          margin-right: 3px;
          margin-bottom: 3px;
        }

        #work-dialog {
          --component-width: calc(100% - 80px);
          --component-height: auto;
          right: 0;
          top: 50px;
        }

        #status-detail-dialog {
          --component-width: 375px;
        }

        #commit-session-dialog {
          --component-width: 390px;
        }

        #terminate-selected-sessions-dialog,
        #terminate-session-dialog {
          --component-width: 390px;
        }

        #force-terminate-confirmation-dialog {
          --component-width: 450px;
        }

        ul.force-terminate-confirmation {
          padding-left: 1rem;
        }

        div.force-terminate-confirmation-container-list {
          background-color: rgba(0, 0, 0, 0.2);
          border-radius: 5px;
          padding: 10px;
        }

        @media screen and (max-width: 899px) {
          #work-dialog,
          #work-dialog.mini_ui {
            left: 0;
            --component-width: 95%;
          }
        }

        @media screen and (min-width: 900px) {
          #work-dialog {
            left: 100px;
          }

          #work-dialog.mini_ui {
            left: 40px;
          }
        }

        #work-area {
          width: 100%;
          padding: 5px;
          font-size: 12px;
          line-height: 12px;
          height: calc(100vh - 120px);
          background-color: #222222;
          color: #efefef;
        }

        #work-area pre {
          white-space: pre-wrap;
          white-space: -moz-pre-wrap;
          white-space: -pre-wrap;
          white-space: -o-pre-wrap;
          word-wrap: break-word;
        }

        #help-description {
          --component-max-width: 70vw;
        }

        #help-description p,
        #help-description strong {
          padding: 5px 30px !important;
        }

        div.indicator,
        span.indicator {
          font-size: 9px;
          margin-right: 5px;
        }

        div.label,
        span.label {
          font-size: 12px;
        }

        div.configuration {
          width: 90px !important;
          height: 20px;
        }

        span.subheading {
          color: var(--token-colorTextSecondary, #666);
          font-weight: bold;
          font-size: 15px;
        }

        mwc-list-item.commit-session-info {
          height: 100%;
        }

        mwc-list-item.predicate-check {
          height: 100%;
          margin-bottom: 5px;
        }

        .predicate-check-comment {
          white-space: normal;
          font-size: 14px;
        }

        .error-description {
          font-size: 0.8rem;
          word-break: break-word;
        }

        h4.commit-session-title {
          margin-bottom: 0;
        }

        span.commit-session-subheading {
          font-size: smaller;
          font-family: monospace;
        }

        mwc-button.multiple-action-button {
          --mdc-theme-primary: var(--paper-red-600);
          --mdc-theme-on-primary: white;
        }

        div.pagination-label {
          background-color: var(--token-colorBgContainer, --paper-grey-100);
          min-width: 60px;
          font-size: 12px;
          font-family: var(--token-fontFamily);
          padding-top: 5px;
          width: auto;
          text-align: center;
        }

        lablup-progress-bar.usage {
          --progress-bar-height: 5px;
          --progress-bar-width: 120px;
          margin: 2px 0 5px 0;
        }

        div.filters #access-key-filter {
          --input-font-size: small;
          --input-label-font-size: small;
          --input-font-family: var(--token-fontFamily);
        }

        .mount-button,
        .status-button,
        .idle-check-key {
          border: none;
          background: none;
          padding: 0;
          outline-style: none;
          font-family: var(--token-fontFamily);
          color: var(--token-colorText);
        }

        .no-mount {
          color: var(--token-colorTextDisabled, --paper-grey-400);
        }

        .idle-check-key {
          font-size: 12px;
          font-weight: 500;
        }

        .idle-type {
          font-size: 11px;
          color: var(--paper-grey-600);
          font-weight: 400;
        }

        span#access-key-filter-helper-text {
          margin-top: 3px;
          font-size: 10px;
          color: var(--general-menu-color-2);
        }

        div.usage-items {
          font-size: 10px;
        }

        div.error-detail-panel {
          border-radius: var(--token-borderRadiusSM, 4px);
          background-color: var(--token-colorBgContainerDisabled);
          padding: var(--token-paddingSM, 10px);
          margin: var(--token-marginSM, 10px);
        }
      `]}get _isRunning(){return["batch","interactive","inference","system","running","others"].includes(this.condition)}get _isIntegratedCondition(){return["running","finished","others"].includes(this.condition)}_isPreparing(e){return-1!==["RESTARTING","PREPARED","PREPARING","PULLING"].indexOf(e)}_isError(e){return"ERROR"===e}_isPending(e){return"PENDING"===e}_isFinished(e){return["TERMINATED","CANCELLED","TERMINATING"].includes(e)}firstUpdated(){var e;null===(e=this._grid)||void 0===e||e.addEventListener("selected-items-changed",(()=>{this._selected_items=this._grid.selectedItems,this._selected_items.length>0?this.multipleActionButtons.style.display="flex":this.multipleActionButtons.style.display="none"})),this.imageInfo=globalThis.backendaimetadata.imageInfo,this.kernel_icons=globalThis.backendaimetadata.icons,this.kernel_labels=globalThis.backendaimetadata.kernel_labels,document.addEventListener("backend-ai-metadata-image-loaded",(()=>{this.imageInfo=globalThis.backendaimetadata.imageInfo,this.kernel_icons=globalThis.backendaimetadata.icons,this.kernel_labels=globalThis.backendaimetadata.kernel_labels}),{once:!0}),this.refreshTimer=null,this.notification=globalThis.lablupNotification,this.indicator=globalThis.lablupIndicator,document.addEventListener("backend-ai-group-changed",(e=>this.refreshList(!0,!1))),document.addEventListener("backend-ai-ui-changed",(e=>this._refreshWorkDialogUI(e))),document.addEventListener("backend-ai-clear-timeout",(()=>{clearTimeout(this.refreshTimer)})),this._refreshWorkDialogUI({detail:{"mini-ui":globalThis.mini_ui}})}async _viewStateChanged(e){var i;await this.updateComplete,!1!==e&&(void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{var e;globalThis.backendaiclient.is_admin?this.accessKeyFilterInput.style.display="block":(this.accessKeyFilterInput.style.display="none",this.accessKeyFilterHelperText.style.display="none",(null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("vaadin-grid")).style.height="calc(100vh - 225px)!important"),globalThis.backendaiclient.APIMajorVersion<5&&(this.sessionNameField="sess_id"),this.is_admin=globalThis.backendaiclient.is_admin,this.is_superadmin=globalThis.backendaiclient.is_superadmin,this._connectionMode=globalThis.backendaiclient._config._connectionMode,this.enableScalingGroup=globalThis.backendaiclient.supports("scaling-group"),this.isDisplayingAllocatedShmemEnabled=globalThis.backendaiclient.supports("display-allocated-shmem"),this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this._isContainerCommitEnabled=globalThis.backendaiclient._config.enableContainerCommit&&globalThis.backendaiclient.supports("image-commit"),this._isPerKernelLogSupported=globalThis.backendaiclient.supports("per-kernel-logs"),this._refreshJobData()}),!0):(globalThis.backendaiclient.is_admin?(this.accessKeyFilterInput.style.display="block",this.accessKeyFilterHelperText.style.display="block"):(this.accessKeyFilterInput.style.display="none",this.accessKeyFilterHelperText.style.display="none",(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("vaadin-grid")).style.height="calc(100vh - 225px)!important"),globalThis.backendaiclient.APIMajorVersion<5&&(this.sessionNameField="sess_id"),this.is_admin=globalThis.backendaiclient.is_admin,this.is_superadmin=globalThis.backendaiclient.is_superadmin,this._connectionMode=globalThis.backendaiclient._config._connectionMode,this.enableScalingGroup=globalThis.backendaiclient.supports("scaling-group"),this.isDisplayingAllocatedShmemEnabled=globalThis.backendaiclient.supports("display-allocated-shmem"),this._APIMajorVersion=globalThis.backendaiclient.APIMajorVersion,this.isUserInfoMaskEnabled=globalThis.backendaiclient._config.maskUserInfo,this._isContainerCommitEnabled=globalThis.backendaiclient._config.enableContainerCommit&&globalThis.backendaiclient.supports("image-commit"),this._isPerKernelLogSupported=globalThis.backendaiclient.supports("per-kernel-logs"),this._refreshJobData()))}async refreshList(e=!0,i=!0){return this._refreshJobData(e,i)}async _refreshJobData(e=!1,i=!0){if(await this.updateComplete,!0!==this.active)return;if(!0===this.refreshing)return;let t;switch(this.refreshing=!0,t="RUNNING",this.condition){case"running":case"interactive":case"system":case"batch":case"inference":case"others":t=["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING","ERROR"],globalThis.backendaiclient.supports("prepared-session-status")&&t.push("PREPARED");break;case"finished":t=["TERMINATED","CANCELLED"];break;default:t=["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING"],globalThis.backendaiclient.supports("prepared-session-status")&&t.push("PREPARED")}!globalThis.backendaiclient.supports("avoid-hol-blocking")&&t.includes("SCHEDULED")&&(t=t.filter((e=>"SCHEDULED"!==e))),globalThis.backendaiclient.supports("detailed-session-states")&&(t=t.join(","));const s=["id","session_id","name","image","architecture","created_at","terminated_at","status","status_info","service_ports","mounts","resource_opts","occupied_slots","requested_slots","access_key","starts_at","type","agents"];globalThis.backendaiclient.supports("multi-container")&&s.push("cluster_size"),globalThis.backendaiclient.supports("multi-node")&&s.push("cluster_mode"),globalThis.backendaiclient.supports("session-detail-status")&&s.push("status_data"),globalThis.backendaiclient.supports("idle-checks")&&s.push("idle_checks"),globalThis.backendaiclient.supports("inference-workload")&&s.push("inference_metrics"),globalThis.backendaiclient.supports("sftp-scaling-group")&&s.push("main_kernel_role"),this.enableScalingGroup&&s.push("scaling_group"),"SESSION"===this._connectionMode&&s.push("user_email"),globalThis.backendaiclient._config.hideAgents||s.push("containers {agent}");const o=globalThis.backendaiclient.current_group_id(),n=["container_id","occupied_slots","live_stat","last_stat"];globalThis.backendaiclient.is_superadmin&&n.push("agent"),globalThis.backendaiclient.supports("per-user-image")&&n.push("kernel_id role local_rank image_object { labels { key value } }"),this._isContainerCommitEnabled&&t.includes("RUNNING")&&s.push("commit_status"),s.push(`containers { ${n.join(" ")} }`),globalThis.backendaiclient.computeSession.list(s,t,this.filterAccessKey,this.session_page_limit,(this.current_page-1)*this.session_page_limit,o,2e4).then((t=>{var s,o,n,a,l,r;this.total_session_count=(null===(s=null==t?void 0:t.compute_session_list)||void 0===s?void 0:s.total_count)||0;let c,d=null===(o=null==t?void 0:t.compute_session_list)||void 0===o?void 0:o.items;if(0===this.total_session_count?(this.listCondition="no-data",null===(n=this._listStatus)||void 0===n||n.show(),this.total_session_count=1):["interactive","batch","inference"].includes(this.condition)&&0===d.filter((e=>e.type.toLowerCase()===this.condition)).length||"system"===this.condition&&0===d.filter((e=>e.main_kernel_role.toLowerCase()===this.condition)).length?(this.listCondition="no-data",null===(a=this._listStatus)||void 0===a||a.show()):null===(l=this._listStatus)||void 0===l||l.hide(),void 0!==d&&0!=d.length){const e=this.compute_sessions,i=[];Object.keys(e).map(((t,s)=>{i.push(e[t].session_id)})),Object.keys(d).map(((e,i)=>{var t,s,o,n,a;const l=d[e],r=JSON.parse(l.occupied_slots),c=JSON.parse(l.requested_slots),u=Object.keys(r).length>0?r:c,p=d[e].image.split("/")[2]||d[e].image.split("/")[1];if(d[e].cpu_slot=parseInt(u.cpu),d[e].mem_slot=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(u.mem,"g")),d[e].mem_slot=d[e].mem_slot.toFixed(2),d[e].elapsed=this._elapsed(d[e].created_at,d[e].terminated_at),d[e].created_at_hr=this._humanReadableTime(d[e].created_at),d[e].starts_at_hr=d[e].starts_at?this._humanReadableTime(d[e].starts_at):"",globalThis.backendaiclient.supports("idle-checks")){const i=JSON.parse(l.idle_checks||"{}");i&&(d[e].idle_checks=i),i&&i.network_timeout&&i.network_timeout.remaining&&(d[e].idle_checks.network_timeout.remaining=j.secondsToDHMS(i.network_timeout.remaining),null===(t=this.activeIdleCheckList)||void 0===t||t.add("network_timeout")),i&&i.session_lifetime&&i.session_lifetime.remaining&&(d[e].idle_checks.session_lifetime.remaining=j.secondsToDHMS(i.session_lifetime.remaining),null===(s=this.activeIdleCheckList)||void 0===s||s.add("session_lifetime")),i&&i.utilization&&i.utilization.remaining&&(d[e].idle_checks.utilization.remaining=j.secondsToDHMS(i.utilization.remaining),null===(o=this.activeIdleCheckList)||void 0===o||o.add("utilization"))}if(d[e].containers&&d[e].containers.length>0){const i={cpu_util:{capacity:0,current:0,ratio:0,slots:"0"},mem:{capacity:0,current:0,ratio:0},io_read:{current:0},io_write:{current:0}};d[e].containers.forEach((t=>{var s,o,n,a,l;const r=JSON.parse(t.live_stat);i.cpu_util.current+=parseFloat(null===(s=null==r?void 0:r.cpu_util)||void 0===s?void 0:s.current),i.cpu_util.capacity+=parseFloat(null===(o=null==r?void 0:r.cpu_util)||void 0===o?void 0:o.capacity),i.mem.current+=parseInt(null===(n=null==r?void 0:r.mem)||void 0===n?void 0:n.current),i.mem.capacity=u.mem,i.io_read.current+=parseFloat(j.bytesToMB(null===(a=null==r?void 0:r.io_read)||void 0===a?void 0:a.current)),i.io_write.current+=parseFloat(j.bytesToMB(null===(l=null==r?void 0:r.io_write)||void 0===l?void 0:l.current)),r&&(Object.keys(r).forEach((e=>{"cpu_util"!==e&&"cpu_used"!==e&&"mem"!==e&&"io_read"!==e&&"io_write"!==e&&"io_scratch_size"!==e&&"net_rx"!==e&&"net_tx"!==e&&(e.includes("_util")||e.includes("_mem"))&&(i[e]||(i[e]={capacity:0,current:0,ratio:0}),i[e].current+=parseFloat(r[e].current),i[e].capacity+=parseFloat(r[e].capacity))})),i.cpu_util.ratio=i.cpu_util.current/i.cpu_util.capacity*d[e].containers.length||0,i.cpu_util.slots=u.cpu,i.mem.ratio=i.mem.current/i.mem.capacity||0,Object.keys(i).forEach((e=>{"cpu_util"!==e&&"mem"!==e&&(-1!==e.indexOf("_util")&&i[e].capacity>0&&(i[e].ratio=i[e].current/100||0),-1!==e.indexOf("_mem")&&i[e].capacity>0&&(i[e].ratio=i[e].current/i[e].capacity||0))})),d[e].live_stat=i)}));const t=d[e].containers[0],s=t.live_stat?JSON.parse(t.live_stat):null;d[e].agent=t.agent,s&&s.cpu_used?d[e].cpu_used_time=this._automaticScaledTime(s.cpu_used.current):d[e].cpu_used_time=this._automaticScaledTime(0),!this.is_superadmin&&globalThis.backendaiclient._config.hideAgents||(d[e].agents_ids_with_container_ids=null===(a=null===(n=d[e].containers)||void 0===n?void 0:n.map((e=>{var i,t,s;return`${null!==(i=e.agent)&&void 0!==i?i:"-"}(${null!==(s=null===(t=e.container_id)||void 0===t?void 0:t.slice(0,4))&&void 0!==s?s:"-"})`})))||void 0===a?void 0:a.join("\n"))}const m=JSON.parse(d[e].service_ports);d[e].service_ports=m,!0===Array.isArray(m)?(d[e].app_services=m.map((e=>e.name)),d[e].app_services_option={},m.forEach((i=>{"allowed_arguments"in i&&(d[e].app_services_option[i.name]=i.allowed_arguments)}))):(d[e].app_services=[],d[e].app_services_option={}),0!==d[e].app_services.length&&["batch","interactive","inference","system","running"].includes(this.condition)?d[e].appSupport=!0:d[e].appSupport=!1,["batch","interactive","inference","system","running"].includes(this.condition)?d[e].running=!0:d[e].running=!1,"cuda.device"in u&&(d[e].cuda_gpu_slot=parseInt(u["cuda.device"])),"rocm.device"in u&&(d[e].rocm_gpu_slot=parseInt(u["rocm.device"])),"tpu.device"in u&&(d[e].tpu_slot=parseInt(u["tpu.device"])),"ipu.device"in u&&(d[e].ipu_slot=parseInt(u["ipu.device"])),"atom.device"in u&&(d[e].atom_slot=parseInt(u["atom.device"])),"atom-plus.device"in u&&(d[e].atom_plus_slot=parseInt(u["atom-plus.device"])),"gaudi2.device"in u&&(d[e].gaudi2_slot=parseInt(u["gaudi2.device"])),"warboy.device"in u&&(d[e].warboy_slot=parseInt(u["warboy.device"])),"rngd.device"in u&&(d[e].rngd_slot=parseInt(u["rngd.device"])),"hyperaccel-lpu.device"in u&&(d[e].hyperaccel_lpu_slot=parseInt(u["hyperaccel-lpu.device"])),"cuda.shares"in u&&(d[e].cuda_fgpu_slot=parseFloat(u["cuda.shares"]).toFixed(2)),d[e].kernel_image=p,d[e].icon=this._getKernelIcon(l.image),d[e].sessionTags=this._getKernelInfo(l.image);const h=l.image.split("/");d[e].cluster_size=parseInt(d[e].cluster_size);const g=h[h.length-1].split(":")[1],v=g.split("-");if(void 0!==v[1]){if(d[e].baseversion=v[0],d[e].baseimage=v[1],d[e].additional_reqs=v.slice(1,v.length).filter((e=>e.indexOf("customized_")<0)).map((e=>e.toUpperCase())),d[e].containers[0].image_object){const i=d[e].containers[0].image_object.labels.find((({key:e})=>"ai.backend.customized-image.name"===e));i&&(d[e].additional_reqs=[...d[e].additional_reqs,`Customized-${i.value}`])}}else void 0!==d[e].tag?d[e].baseversion=d[e].tag:d[e].baseversion=g;this._selected_items.includes(d[e].session_id)?d[e].checked=!0:d[e].checked=!1}))}if(["batch","interactive","inference"].includes(this.condition)){const e=d.reduce(((e,i)=>("SYSTEM"!==i.main_kernel_role&&e[i.type.toLowerCase()].push(i),e)),{batch:[],interactive:[],inference:[]});d=e[this.condition]}else d="system"===this.condition?d.filter((e=>"SYSTEM"===e.main_kernel_role)):d.filter((e=>"SYSTEM"!==e.main_kernel_role));if(this.compute_sessions=d,null===(r=this._grid)||void 0===r||r.recalculateColumnWidths(),this.requestUpdate(),this.refreshing=!1,!0===this.active){if(!0===e){const e=new CustomEvent("backend-ai-resource-refreshed",{detail:{}});document.dispatchEvent(e)}!0===i&&(c=["batch","interactive","inference","system","running"].includes(this.condition)?15e3:45e3,this.refreshTimer=setTimeout((()=>{this._refreshJobData()}),c))}this._handleSelectedItems()})).catch((e=>{var t;if(this.refreshing=!1,this.active&&i){const e=["batch","interactive","inference","system","running"].includes(this.condition)?2e4:12e4;this.refreshTimer=setTimeout((()=>{this._refreshJobData()}),e)}null===(t=this._listStatus)||void 0===t||t.hide(),e&&e.message&&(this.notification.text=_.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_refreshWorkDialogUI(e){Object.prototype.hasOwnProperty.call(e.detail,"mini-ui")&&!0===e.detail["mini-ui"]?this.workDialog.classList.add("mini_ui"):this.workDialog.classList.remove("mini_ui")}_humanReadableTime(e){return(e=new Date(e)).toLocaleString(globalThis.backendaioptions.get("language",null,"general"))}_getKernelInfo(e){const i=[];if(void 0===e)return[];const t=e.split("/"),s=(t[2]||t[1]).split(":")[0];if(s in this.kernel_labels)i.push(this.kernel_labels[s]);else{const t=e.split("/");let s,o;3===t.length?(s=t[1],o=t[2]):t.length>3?(s=null==t?void 0:t.slice(2,t.length-1).join("/"),o=t[t.length-1]):(s="",o=t[1]),o=o.split(":")[0],o=s?s+"/"+o:o,i.push([{category:"Env",tag:`${o}`,color:"lightgrey"}])}return i}_getKernelIcon(e){if(void 0===e)return[];const i=e.split("/"),t=(i[2]||i[1]).split(":")[0];return t in this.kernel_icons?this.kernel_icons[t]:""}_automaticScaledTime(e){let i=Object();const t=["D","H","M","S"],s=[864e5,36e5,6e4,1e3];for(let o=0;o<s.length;o++)Math.floor(e/s[o])>0&&(i[t[o]]=Math.floor(e/s[o]),e%=s[o]);return 0===Object.keys(i).length&&(i=e>0?{MS:e}:{NODATA:1}),i}static bytesToMB(e,i=1){return Number(e/10**6).toFixed(1)}static bytesToGiB(e,i=2){return e?(e/2**30).toFixed(i):e}static _prefixFormatWithoutTrailingZeros(e="0",i){const t="string"==typeof e?parseFloat(e):e;return parseFloat(t.toFixed(i)).toString()}_elapsed(e,i){return globalThis.backendaiclient.utils.elapsedTime(e,i)}_indexRenderer(e,i,t){const s=t.index+1;b(f`
        <div>${s}</div>
      `,e)}async sendRequest(e){let i,t;try{"GET"==e.method&&(e.body=void 0),i=await fetch(e.uri,e);const s=i.headers.get("Content-Type");if(t=s.startsWith("application/json")||s.startsWith("application/problem+json")?await i.json():s.startsWith("text/")?await i.text():await i.blob(),!i.ok)throw t}catch(e){}return t}async _terminateApp(e){const i=globalThis.backendaiclient._config.accessKey,t=await globalThis.appLauncher._getProxyURL(e),s={method:"GET",uri:new URL(`proxy/${i}/${e}`,t).href};return this.sendRequest(s).then((s=>{this.total_session_count-=1;let o=new URL(`proxy/${i}/${e}/delete`,t);if(localStorage.getItem("backendaiwebui.appproxy-permit-key")&&(o.searchParams.set("permit_key",localStorage.getItem("backendaiwebui.appproxy-permit-key")||""),o=new URL(o.href)),void 0!==s&&404!==s.code){const e={method:"GET",uri:o.href,credentials:"include",mode:"cors"};return this.sendRequest(e)}return Promise.resolve(!0)})).catch((e=>{console.log(e),e&&e.message&&(this.notification.text=_.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}))}_getProxyToken(){let e="local";return void 0!==globalThis.backendaiclient._config.proxyToken&&(e=globalThis.backendaiclient._config.proxyToken),e}_setSelectedSession(e){const i=e.target.closest("#controls"),t=i["session-uuid"],s=i["session-name"],o=i["access-key"];this.workDialog.sessionUuid=t,this.workDialog.sessionName=s,this.workDialog.accessKey=o}_setSelectedKernel(){var e;const i=null===(e=this.compute_sessions.find((e=>e.session_id===this.workDialog.sessionUuid)))||void 0===e?void 0:e.containers.map(((e,i)=>((null==e?void 0:e.role)?(null==e?void 0:e.role.includes("main"))?e.role="main1":e.role=`sub${e.local_rank}`:0===i&&(e.role="main1"),e))).sort(((e,i)=>e.role.localeCompare(i.role)));this.selectedKernels=this._isPerKernelLogSupported?i:i.filter((e=>e.role.includes("main")))}_updateLogsByKernelId(){var e,i;this.selectedKernelId=this._isPerKernelLogSupported?null===(i=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#kernel-id-select"))||void 0===i?void 0:i.value:null}_showLogs(){globalThis.backendaiclient.supports("session-node")?document.dispatchEvent(new CustomEvent("bai-open-session-log",{detail:this.workDialog.sessionUuid})):globalThis.backendaiclient.get_logs(this.workDialog.sessionUuid,this.workDialog.accessKey,""!==this.selectedKernelId?this.selectedKernelId:null,15e3).then((e=>{var i,t;const s=(new C).ansi_to_html(e.result.logs);(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#work-title")).innerHTML=`${this.workDialog.sessionName} (${this.workDialog.sessionUuid})`,(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#work-area")).innerHTML=`<pre>${s}</pre>`||y("session.NoLogs"),this.workDialog.show()})).catch((e=>{e&&e.message?(this.notification.text=_.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=_.relieve(e.title),this.notification.detail="",this.notification.show(!0,e))}))}_downloadLogs(){const e=this.workDialog.sessionUuid,i=this.workDialog.sessionName,t=globalThis.backendaiclient.APIMajorVersion<5?i:e,s=this.workDialog.accessKey;globalThis.backendaiclient.get_logs(t,s,""!==this.selectedKernelId?this.selectedKernelId:null,15e3).then((e=>{const t=e.result.logs;globalThis.backendaiutils.exportToTxt(i,t),this.notification.text=y("session.DownloadingSessionLogs"),this.notification.show()})).catch((e=>{e&&e.message?(this.notification.text=_.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=_.relieve(e.title),this.notification.detail="",this.notification.show(!0,e))}))}_refreshLogs(){const e=this.workDialog.sessionUuid,i=this.workDialog.sessionName,t=globalThis.backendaiclient.APIMajorVersion<5?i:e,s=this.workDialog.accessKey;globalThis.backendaiclient.get_logs(t,s,""!==this.selectedKernelId?this.selectedKernelId:null,15e3).then((e=>{var i;const t=(new C).ansi_to_html(e.result.logs);(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#work-area")).innerHTML=`<pre>${t}</pre>`||y("session.NoLogs")})).catch((e=>{e&&e.message?(this.notification.text=_.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e)):e&&e.title&&(this.notification.text=_.relieve(e.title),this.notification.detail="",this.notification.show(!0,e))}))}_showAppLauncher(e){const i=e.target.closest("#controls");return globalThis.appLauncher.showLauncher(i)}async _runTerminal(e){const i=e.target.closest("#controls")["session-uuid"];return globalThis.appLauncher.runTerminal(i)}async _getCommitSessionStatus(e=""){let i=!1;return""!==e&&globalThis.backendaiclient.computeSession.getCommitSessionStatus(e).then((e=>{i=e})).catch((e=>{console.log(e)})),i}async _requestCommitSession(e){try{const i=await globalThis.backendaiclient.computeSession.commitSession(e.session.name),t=Object.assign(e,{taskId:i.bgtask_id});this._showCommitStatus(i,t)}catch(e){console.log(e),e&&e.message&&(this.notification.text=_.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}finally{this.commitSessionDialog.hide()}}async _showCommitStatus(e,i){try{this._applyContainerCommitAsBackgroundTask(i)}catch(e){console.log(e),e&&e.message&&(this.notification.text=_.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}finally{this.commitSessionDialog.hide()}}async _requestConvertSessionToimage(e){try{const i=await globalThis.backendaiclient.computeSession.convertSessionToImage(e.session.name,this.newImageName),t=Object.assign(e,{taskId:i.task_id});this._showCommitStatus(i,t)}catch(e){console.log(e),e&&e.message&&(this.notification.text=_.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))}finally{this.commitSessionDialog.hide()}}_applyContainerCommitAsBackgroundTask(e){const i="commit-session:"+(new Date).getTime(),t=new CustomEvent("add-bai-notification",{detail:{key:i,message:y("session.CommitSession"),description:y("session.CommitOnGoing"),backgroundTask:{percent:0,status:"pending"},duration:0,open:!0}});document.dispatchEvent(t);const s=new CustomEvent("add-bai-notification",{detail:{key:i,description:y("session.CommitSession"),backgroundTask:{taskId:e.taskId,statusDescriptions:{pending:y("session.CommitOnGoing"),rejected:y("session.CommitFailed"),resolved:y("session.CommitFinished")},renderDataMessage:e=>(null==e?void 0:e.includes("QuotaExceeded"))?y("error.ReachedResourceLimitPleaseContact"):e,status:"pending",percent:0},duration:0}});document.dispatchEvent(s)}_removeCommitSessionFromTasker(e=""){globalThis.tasker.remove(e)}_getCurrentContainerCommitInfoListFromLocalStorage(){return JSON.parse(localStorage.getItem("backendaiwebui.settings.user.container_commit_sessions")||"[]")}_saveCurrentContainerCommitInfoToLocalStorage(e){const i=this._getCurrentContainerCommitInfoListFromLocalStorage();i.push(e),globalThis.backendaioptions.set("container_commit_sessions",JSON.stringify(i))}_removeFinishedContainerCommitInfoFromLocalStorage(e="",i=""){let t=this._getCurrentContainerCommitInfoListFromLocalStorage();t=t.filter((t=>t.session.id!==e&&t.taskId!==i)),globalThis.backendaioptions.set("container_commit_sessions",JSON.stringify(t))}_openCommitSessionDialog(e){var i;const t=e.target.closest("#controls"),s=t["session-name"],o=t["session-uuid"],n=t["kernel-image"];this.commitSessionDialog.sessionName=s,this.commitSessionDialog.sessionId=o,this.commitSessionDialog.kernelImage=n,(null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#new-image-name-field")).value="",this.requestUpdate(),this.commitSessionDialog.show()}_openTerminateSessionDialog(e){const i=e.target.closest("#controls"),t=i["session-name"],s=i["session-uuid"],o=i["access-key"];this.terminateSessionDialog.sessionName=t,this.terminateSessionDialog.sessionId=s,this.terminateSessionDialog.accessKey=o,this.terminateSessionDialog.show()}_terminateSession(e){const i=e.target.closest("#controls"),t=i["session-uuid"],s=i["access-key"];return this.terminationQueue.includes(t)?(this.notification.text=y("session.AlreadyTerminatingSession"),this.notification.detail="",this.notification.show(),!1):this._terminateKernel(t,s)}_terminateSessionWithCheck(e=!1){var i;return this.terminationQueue.includes(this.terminateSessionDialog.sessionId)?(this.notification.text=y("session.AlreadyTerminatingSession"),this.notification.detail="",this.notification.show(),!1):(this.listCondition="loading",null===(i=this._listStatus)||void 0===i||i.show(),this._terminateKernel(this.terminateSessionDialog.sessionId,this.terminateSessionDialog.accessKey,e).then((()=>{this._selected_items=[],this._clearCheckboxes(),this.terminateSessionDialog.hide(),this.notification.text=y("session.SessionTerminated"),this.notification.detail="",this.notification.show();const e=new CustomEvent("backend-ai-resource-refreshed",{detail:"running"});document.dispatchEvent(e)})).catch((()=>{this._selected_items=[],this._clearCheckboxes(),this.terminateSessionDialog.hide()})))}static _parseAgentBasedContainers(e){return Object.values(e.reduce(((e,i)=>{var t;return null===(t=i.containers)||void 0===t||t.forEach((i=>{i.agent&&i.container_id&&(e[i.agent]?e[i.agent].containers.includes(i.container_id)||e[i.agent].containers.push(i.container_id):e[i.agent]={agent:i.agent,containers:[i.container_id]})})),e}),{}))}_getManualCleanUpNeededContainers(){this._manualCleanUpNeededContainers=j._parseAgentBasedContainers(this._selected_items.length>0?this._selected_items:this.compute_sessions.filter((e=>(null==e?void 0:e.session_id)===this.terminateSessionDialog.sessionId)))}_openForceTerminateConfirmationDialog(e){this.forceTerminateConfirmationDialog.show()}_openTerminateSelectedSessionsDialog(e){this.terminateSelectedSessionsDialog.show()}_clearCheckboxes(){this._grid.selectedItems=[],this._selected_items=[],this._grid.clearCache()}_handleSelectedItems(){var e;if(null===(e=this._grid)||void 0===e||e.addEventListener("selected-items-changed",(()=>{this._selected_items=this._grid.selectedItems,this._selected_items.length>0?this.multipleActionButtons.style.display="flex":this.multipleActionButtons.style.display="none"})),0===this._selected_items.length)return;const i=this.compute_sessions.filter((e=>this._selected_items.some((i=>i.id===e.id))));this._grid.selectedItems=i}_terminateSelectedSessionsWithCheck(e=!1){var i;this.listCondition="loading",null===(i=this._listStatus)||void 0===i||i.show();const t=this._selected_items.map((i=>this._terminateKernel(i.session_id,i.access_key,e)));return this._selected_items=[],Promise.all(t).then((()=>{this.terminateSelectedSessionsDialog.hide(),this._clearCheckboxes(),this.multipleActionButtons.style.display="none",this.notification.text=y("session.SessionsTerminated"),this.notification.detail="",this.notification.show()})).catch((()=>{this.terminateSelectedSessionsDialog.hide(),this._clearCheckboxes()}))}_terminateSelectedSessions(){var e;this.listCondition="loading",null===(e=this._listStatus)||void 0===e||e.show();const i=this._selected_items.map((e=>this._terminateKernel(e.session_id,e.access_key)));return Promise.all(i).then((()=>{this._selected_items=[],this._clearCheckboxes(),this.multipleActionButtons.style.display="none",this.notification.text=y("session.SessionsTerminated"),this.notification.detail="",this.notification.show()})).catch((()=>{var e;null===(e=this._listStatus)||void 0===e||e.hide(),this._selected_items=[],this._clearCheckboxes()}))}_requestDestroySession(e,i,t){globalThis.backendaiclient.destroy(e,i,t).then((e=>{setTimeout((async()=>{this.terminationQueue=[];const e=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(e)}),1e3)})).catch((e=>{const i=new CustomEvent("backend-ai-session-list-refreshed",{detail:"running"});document.dispatchEvent(i),this.notification.text="description"in e?_.relieve(e.description):_.relieve("Problem occurred during termination."),this.notification.detail="",this.notification.show(!0,e)}))}async _terminateKernel(e,i,t=!1){return this.terminationQueue.push(e),this._terminateApp(e).then((()=>this._requestDestroySession(e,i,t))).catch((s=>{throw s&&s.message&&(404==s.statusCode||500==s.statusCode?this._requestDestroySession(e,i,t):(this.notification.text=_.relieve(s.title),this.notification.detail=s.message,this.notification.show(!0,s))),s}))}_hideDialog(e){var i;const t=e.target.closest("backend-ai-dialog");if(t.hide(),"ssh-dialog"===t.id){const e=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelector("#sshkey-download-link");globalThis.URL.revokeObjectURL(e.href)}}_updateFilterAccessKey(e){this.filterAccessKey=e.target.value,this.refreshTimer&&(clearTimeout(this.refreshTimer),this._refreshJobData())}_createMountedFolderDropdown(e,i){const t=e.target,s=document.createElement("mwc-menu");s.anchor=t,s.className="dropdown-menu",s.style.boxShadow="0 1px 1px rgba(0, 0, 0, 0.2)",s.setAttribute("open",""),s.setAttribute("fixed",""),s.setAttribute("x","10"),s.setAttribute("y","15"),i.length>=1&&(i.map(((e,t)=>{const o=document.createElement("mwc-list-item");o.style.height="25px",o.style.fontWeight="400",o.style.fontSize="14px",o.style.fontFamily="var(--token-fontFamily)",o.innerHTML=i.length>1?e:y("session.OnlyOneFolderAttached"),s.appendChild(o)})),document.body.appendChild(s))}_removeMountedFolderDropdown(){var e;const i=document.getElementsByClassName("dropdown-menu");for(;i[0];)null===(e=i[0].parentNode)||void 0===e||e.removeChild(i[0])}_renderStatusDetail(){var e,i,t,s,o,n,a,l,r,c;const d=JSON.parse(this.selectedSessionStatus.data);d.reserved_time=this.selectedSessionStatus.reserved_time;const u=null===(e=this.shadowRoot)||void 0===e?void 0:e.querySelector("#status-detail"),p=[];if(p.push(f`
      <div class="vertical layout justified start">
        <h3
          style="width:100%;padding-left:15px;border-bottom:1px solid var(--token-colorBorder, #ccc);"
        >
          ${y("session.Status")}
        </h3>
        <lablup-shields
          color="${this.statusColorTable[this.selectedSessionStatus.info]}"
          description="${this.selectedSessionStatus.info}"
          ui="round"
          style="padding-left:15px;"
        ></lablup-shields>
      </div>
    `),d.hasOwnProperty("kernel")||d.hasOwnProperty("session"))p.push(f`
        <div class="vertical layout start flex" style="width:100%;">
          <div style="width:100%;">
            <h3
              style="width:100%;padding-left:15px;border-bottom:1px solid var(--token-colorBorder, #ccc);"
            >
              ${y("session.StatusDetail")}
            </h3>
            <div class="vertical layout flex" style="width:100%;">
              <mwc-list>
                ${(null===(i=d.kernel)||void 0===i?void 0:i.exit_code)?f`
                      <mwc-list-item
                        twoline
                        noninteractive
                        class="predicate-check"
                      >
                        <span class="subheading">
                          <strong>Kernel Exit Code</strong>
                        </span>
                        <span
                          class="monospace predicate-check-comment"
                          slot="secondary"
                        >
                          ${null===(t=d.kernel)||void 0===t?void 0:t.exit_code}
                        </span>
                      </mwc-list-item>
                    `:f``}
                ${(null===(s=d.session)||void 0===s?void 0:s.status)?f`
                      <mwc-list-item
                        twoline
                        noninteractive
                        class="predicate-check"
                      >
                        <span class="subheading">Session Status</span>
                        <span
                          class="monospace predicate-check-comment"
                          slot="secondary"
                        >
                          ${null===(o=d.session)||void 0===o?void 0:o.status}
                        </span>
                      </mwc-list-item>
                    `:f``}
              </mwc-list>
            </div>
          </div>
        </div>
      `);else if(d.hasOwnProperty("scheduler")){const e=null!==(a=null===(n=d.scheduler.failed_predicates)||void 0===n?void 0:n.length)&&void 0!==a?a:0,i=null!==(r=null===(l=d.scheduler.passed_predicates)||void 0===l?void 0:l.length)&&void 0!==r?r:0;p.push(f`
        <div class="vertical layout start flex" style="width:100%;">
          <div style="width:100%;">
            <h3
              style="width:100%;padding-left:15px;border-bottom:1px solid var(--token-colorBorder, #ccc);margin-bottom:0px;"
            >
              ${y("session.StatusDetail")}
            </h3>
            <div class="vertical layout flex" style="width:100%;">
              <mwc-list>
                ${d.scheduler.msg?f`
                      <mwc-list-item
                        twoline
                        noninteractive
                        class="predicate-check"
                      >
                        <span class="subheading">
                          ${y("session.Message")}
                        </span>
                        <span
                          class="monospace predicate-check-comment"
                          slot="secondary"
                        >
                          ${d.scheduler.msg}
                        </span>
                      </mwc-list-item>
                    `:f``}
                ${d.scheduler.retries?f`
                      <mwc-list-item
                        twoline
                        noninteractive
                        class="predicate-check"
                      >
                        <span class="subheading">
                          ${y("session.TotalRetries")}
                        </span>
                        <span
                          class="monospace predicate-check-comment"
                          slot="secondary"
                        >
                          ${d.scheduler.retries}
                        </span>
                      </mwc-list-item>
                    `:f``}
                ${d.scheduler.last_try?f`
                      <mwc-list-item
                        twoline
                        noninteractive
                        class="predicate-check"
                      >
                        <span class="subheading">
                          ${y("session.LastTry")}
                        </span>
                        <span
                          class="monospace predicate-check-comment"
                          slot="secondary"
                        >
                          ${this._humanReadableTime(d.scheduler.last_try)}
                        </span>
                      </mwc-list-item>
                    `:f``}
              </mwc-list>
            </div>
          </div>
          <lablup-expansion summary="Predicates" open="true">
            <div slot="title" class="horizontal layout center start-justified">
              ${e>0?f`
                    <mwc-icon class="fg red">cancel</mwc-icon>
                  `:f`
                    <mwc-icon class="fg green">check_circle</mwc-icon>
                  `}
              Predicate Checks
            </div>
            <span slot="description">
              ${e>0?" "+(e+" Failed, "):""}
              ${i+" Passed"}
            </span>
            <mwc-list>
              ${d.scheduler.failed_predicates.map((e=>f`
                  ${"reserved_time"===e.name?f`
                        <mwc-list-item
                          twoline
                          graphic="icon"
                          noninteractive
                          class="predicate-check"
                        >
                          <span>${e.name}</span>
                          <span
                            slot="secondary"
                            class="predicate-check-comment"
                          >
                            ${e.msg+": "+d.reserved_time}
                          </span>
                          <mwc-icon
                            slot="graphic"
                            class="fg red inverted status-check"
                          >
                            close
                          </mwc-icon>
                        </mwc-list-item>
                      `:f`
                        <mwc-list-item
                          twoline
                          graphic="icon"
                          noninteractive
                          class="predicate-check"
                        >
                          <span>${e.name}</span>
                          <span
                            slot="secondary"
                            class="predicate-check-comment"
                          >
                            ${e.msg}
                          </span>
                          <mwc-icon
                            slot="graphic"
                            class="fg red inverted status-check"
                          >
                            close
                          </mwc-icon>
                        </mwc-list-item>
                      `}
                  <li divider role="separator"></li>
                `))}
              ${d.scheduler.passed_predicates.map((e=>f`
                  <mwc-list-item graphic="icon" noninteractive>
                    <span>${e.name}</span>
                    <mwc-icon
                      slot="graphic"
                      class="fg green inverted status-check"
                      style="padding-left:5px;"
                    >
                      checked
                    </mwc-icon>
                  </mwc-list-item>
                  <li divider role="separator"></li>
                `))}
            </mwc-list>
          </lablup-expansion>
        </div>
      `)}else if(d.hasOwnProperty("error")){const e=null!==(c=d.error.collection)&&void 0!==c?c:[d.error];p.push(f`
        <div class="vertical layout start flex" style="width:100%;">
          <div style="width:100%;">
            <h3
              style="width:100%;padding-left:15px;border-bottom:1px solid var(--token-colorBorder, #ccc);"
            >
              ${y("session.StatusDetail")}
            </h3>
            ${e.map((e=>f`
                <div class="error-detail-panel">
                  <div class="vertical layout start">
                    <span class="subheading">Error</span>
                    <lablup-shields
                      color="red"
                      description=${e.name}
                      ui="round"
                    ></lablup-shields>
                  </div>
                  ${!this.is_superadmin&&globalThis.backendaiclient._config.hideAgents||!e.agent_id?f``:f`
                        <div class="vertical layout start">
                          <span class="subheading">Agent ID</span>
                          <span>${e.agent_id}</span>
                        </div>
                      `}
                  <div class="vertical layout start">
                    <span class="subheading">Message</span>
                    <span class="error-description">${e.repr}</span>
                  </div>
                  ${e.traceback?f`
                        <div class="vertical layout start">
                          <span class="subheading">Traceback</span>
                          <pre
                            style="display: block; overflow: auto; width: 100%; height: 400px;"
                          >
                            ${e.traceback}
                          </pre
                          >
                        </div>
                      `:f``}
                </div>
              `))}
          </div>
        </div>
      `)}else p.push(f`
        <div class="vertical layout start flex" style="width:100%;">
          <h3
            style="width:100%;padding-left:15px;border-bottom:1px solid var(--token-colorBorder, #ccc);"
          >
            Detail
          </h3>
          <span style="margin:20px;">No Detail.</span>
        </div>
      `);b(p,u)}_openStatusDetailDialog(e,i,t){this.selectedSessionStatus={info:e,data:i,reserved_time:t},this._renderStatusDetail(),this.sessionStatusInfoDialog.show()}_validateSessionName(e){const i=this.compute_sessions.map((e=>e[this.sessionNameField])),t=e.target.parentNode,s=t.querySelector("#session-name-field").innerText,o=t.querySelector("#session-rename-field");o.validityTransform=(e,t)=>{if(t.valid){const t=!i.includes(e)||e===s;return t||(o.validationMessage=y("session.Validation.SessionNameAlreadyExist")),{valid:t,customError:!t}}return t.valueMissing?(o.validationMessage=y("session.Validation.SessionNameRequired"),{valid:t.valid,valueMissing:!t.valid}):t.patternMismatch?(o.validationMessage=y("session.Validation.SluggedStrings"),{valid:t.valid,patternMismatch:!t.valid}):(o.validationMessage=y("session.Validation.EnterValidSessionName"),{valid:t.valid,customError:!t.valid})}}_renameSessionName(e,i){const t=i.target.parentNode,s=t.querySelector("#session-name-field"),o=t.querySelector("#session-rename-field"),n=t.querySelector("#session-rename-icon");if("none"===s.style.display){if(!o.checkValidity())return o.reportValidity(),void(n.on=!0);{const i=globalThis.backendaiclient.APIMajorVersion<5?s.value:e;globalThis.backendaiclient.rename(i,o.value).then((e=>{this.refreshList(),this.notification.text=y("session.SessionRenamed"),this.notification.detail="",this.notification.show()})).catch((e=>{o.value=s.innerText,e&&e.message&&(this.notification.text=_.relieve(e.title),this.notification.detail=e.message,this.notification.show(!0,e))})).finally((()=>{this._toggleSessionNameField(s,o)}))}}else this._toggleSessionNameField(s,o)}_toggleSessionNameField(e,i){"block"===i.style.display?(e.style.display="block",i.style.display="none"):(e.style.display="none",i.style.display="block",i.focus())}static secondsToDHMS(e){const i=Math.floor(e/86400),t=Math.floor(e%86400/3600),s=Math.floor(e%3600/60),o=parseInt(e)%60,n=i<0||t<0||s<0||o<0?y("session.TimeoutExceeded"):"",a=`${void 0!==i&&i>0?String(i)+"d":""}${t.toString().padStart(2,"0")}:${s.toString().padStart(2,"0")}:${o.toString().padStart(2,"0")}`;return n.length>0?n:a}_getIdleSessionTimeout(e){if(globalThis.backendaiutils.isEmpty(e))return null;let i="",t=1/0;for(const[s,o]of Object.entries(e))null!=o&&"number"==typeof o&&null!=t&&o<t&&(i=s,t=o);return t?[i,j.secondsToDHMS(t)]:null}_openIdleChecksInfoDialog(){var e,i,t;this._helpDescriptionTitle=y("session.IdleChecks"),this._helpDescription=`\n      <p>${y("session.IdleChecksDesc")}</p>\n      ${(null===(e=this.activeIdleCheckList)||void 0===e?void 0:e.has("session_lifetime"))?`\n        <strong>${y("session.MaxSessionLifetime")}</strong>\n        <p>${y("session.MaxSessionLifetimeDesc")}</p>\n        `:""}\n      ${(null===(i=this.activeIdleCheckList)||void 0===i?void 0:i.has("network_timeout"))?`\n        <strong>${y("session.NetworkIdleTimeout")}</strong>\n        <p>${y("session.NetworkIdleTimeoutDesc")}</p>\n      `:""}\n      ${(null===(t=this.activeIdleCheckList)||void 0===t?void 0:t.has("utilization"))?`\n        <strong>${y("session.UtilizationIdleTimeout")}</strong>\n        <p>${y("session.UtilizationIdleTimeoutDesc")}</p>\n        <div style="margin:10px 5% 20px 5%;">\n          <li>\n            <span style="font-weight:500">${y("session.GracePeriod")}</span>\n            <div style="padding-left:20px;">${y("session.GracePeriodDesc")}</div>\n          </li>\n          <li>\n            <span style="font-weight:500">${y("session.UtilizationThreshold")}</span>\n            <div style="padding-left:20px;">${y("session.UtilizationThresholdDesc")}</div>\n          </li>\n        </div>\n      `:""}\n    `,this.helpDescriptionDialog.show()}async _openSFTPSessionConnectionInfoDialog(e,i){const t=await globalThis.backendaiclient.get_direct_access_info(e),s=t.public_host.replace(/^https?:\/\//,""),o=t.sshd_ports,n=new CustomEvent("read-ssh-key-and-launch-ssh-dialog",{detail:{sessionUuid:e,host:s,port:o,mounted:i}});document.dispatchEvent(n)}_createUtilizationIdleCheckDropdown(e,i){const t=e.target,s=document.createElement("mwc-menu");s.anchor=t,s.className="util-dropdown-menu",s.style.boxShadow="0 1px 1px rgba(0, 0, 0, 0.2)",s.setAttribute("open",""),s.setAttribute("fixed",""),s.setAttribute("corner","BOTTOM_START");let o=f``;globalThis.backendaiutils.isEmpty(i)||(o=f`
        <style>
          .util-detail-menu-header {
            height: 25px;
            border: none;
            box-shadow: none;
            justify-content: flex-end;
          }
          .util-detail-menu-header > div {
            font-size: 13px;
            font-family: var(--token-fontFamily);
            font-weight: 600;
          }
          .util-detail-menu-content {
            height: 25px;
            border: none;
            box-shadow: none;
          }
          .util-detail-menu-content > div {
            display: flex;
            flex-direction: row;
            justify-content: center;
            justify-content: space-between;
            font-size: 12px;
            font-family: var(--token-fontFamily);
            font-weight: 400;
            min-width: 155px;
          }
        </style>
        <mwc-list-item class="util-detail-menu-header">
          <div>
            ${y("session.Utilization")} / ${y("session.Threshold")} (%)
          </div>
        </mwc-list-item>
        ${Object.keys(i).map((e=>{let[t,s]=i[e];t=t>=0?parseFloat(t).toFixed(1):"-";const o=this.getUtilizationCheckerColor([t,s]);return f`
            <mwc-list-item class="util-detail-menu-content">
              <div>
                <div>${this.idleChecksTable[e]}</div>
                <div style="color:${o}">${t} / ${s}</div>
              </div>
            </mwc-list-item>
          `}))}
      `,document.body.appendChild(s)),b(o,s)}_removeUtilizationIdleCheckDropdown(){var e;const i=document.getElementsByClassName("util-dropdown-menu");for(;i[0];)null===(e=i[0].parentNode)||void 0===e||e.removeChild(i[0])}sessionTypeRenderer(e,i,t){const s=JSON.parse(t.item.inference_metrics||"{}");b(f`
        <div class="layout vertical start">
          <lablup-shields
            color="${this.sessionTypeColorTable[t.item.type]}"
            description="${t.item.type}"
            ui="round"
          ></lablup-shields>
          ${"INFERENCE"===t.item.type?f`
                <span style="font-size:12px;margin-top:5px;">
                  Inference requests: ${s.requests}
                </span>
                <span style="font-size:12px;">
                  Inference API last response time (ms):
                  ${s.last_response_ms}
                </span>
              `:""}
        </div>
      `,e)}copyText(e){var i,t;if(void 0!==navigator.clipboard)null===(t=null===(i=null===navigator||void 0===navigator?void 0:navigator.clipboard)||void 0===i?void 0:i.writeText(e))||void 0===t||t.then((e=>{console.error("Could not copy text: ",e)}));else{const i=document.createElement("input");i.type="text",i.value=e,document.body.appendChild(i),i.select(),document.execCommand("copy"),document.body.removeChild(i)}}sessionInfoRenderer(e,i,t){"system"===this.condition?b(f`
          <style>
            #session-name-field {
              display: block;
              white-space: pre-wrap;
              word-break: break-all;
              white-space-collapse: collapse;
            }
          </style>
          <div class="layout vertical start">
            <div class="horizontal center start-justified layout">
              <pre id="session-name-field">
                ${t.item.mounts[0]} SFTP Session
              </pre
              >
            </div>
          </div>
        `,e):b(f`
          <style>
            #session-name-field {
              display: block;
              margin-left: 16px;
              white-space: pre-wrap;
              white-space-collapse: collapse;
              word-break: break-all;
            }
            #session-rename-field {
              display: none;
              white-space: normal;
              word-break: break-word;
              font-family: var(--general-monospace-font-family);
              --mdc-ripple-color: transparent;
              --mdc-text-field-fill-color: transparent;
              --mdc-text-field-disabled-fill-color: transparent;
              --mdc-typography-font-family: var(
                --general-monospace-font-family
              );
              --mdc-typography-subtitle1-font-family: var(
                --general-monospace-font-family
              );
            }
            #session-rename-icon,
            #session-name-copy-icon {
              --mdc-icon-size: 20px;
            }
          </style>
          <div class="layout vertical start">
            <div class="horizontal center center-justified layout">
              <pre id="session-name-field">
${t.item[this.sessionNameField]}</pre
              >
              ${this._isRunning&&!this._isPreparing(t.item.status)&&globalThis.backendaiclient.email==t.item.user_email?f`
                    <mwc-textfield
                      id="session-rename-field"
                      required
                      autoValidate
                      pattern="^[a-zA-Z0-9]([a-zA-Z0-9\\-_\\.]{2,})[a-zA-Z0-9]$"
                      minLength="4"
                      maxLength="64"
                      validationMessage="${y("session.Validation.EnterValidSessionName")}"
                      value="${t.item[this.sessionNameField]}"
                      @input="${e=>this._validateSessionName(e)}"
                    ></mwc-textfield>
                    <mwc-icon-button-toggle
                      id="session-rename-icon"
                      onIcon="done"
                      offIcon="edit"
                      @click="${e=>this._renameSessionName(t.item.session_id,e)}"
                    ></mwc-icon-button-toggle>
                  `:f``}
              <mwc-icon-button
                id="session-name-copy-icon"
                class="fg controls-running"
                icon="content_copy"
                @click="${()=>this.copyText(t.item[this.sessionNameField])}"
              ></mwc-icon-button>
            </div>
            <div class="horizontal center center-justified layout">
              ${t.item.icon?f`
                    <img
                      src="resources/icons/${t.item.icon}"
                      style="width:32px;height:32px;margin-right:10px;"
                    />
                  `:f``}
              <div class="vertical start layout">
                ${t.item.sessionTags?t.item.sessionTags.map((e=>f`
                        <div class="horizontal center layout">
                          ${e.map((e=>("Env"===e.category&&(e.category=e.tag),e.category&&t.item.baseversion&&(e.tag=t.item.baseversion),f`
                              <lablup-shields
                                app="${void 0===e.category?"":e.category}"
                                color="${e.color}"
                                description="${e.tag}"
                                ui="round"
                                class="right-below-margin"
                              ></lablup-shields>
                            `)))}
                        </div>
                      `)):f``}
                ${t.item.additional_reqs?f`
                      <div class="layout horizontal center wrap">
                        ${t.item.additional_reqs.map((e=>f`
                            <lablup-shields
                              app=""
                              color="green"
                              description="${e}"
                              ui="round"
                              class="right-below-margin"
                            ></lablup-shields>
                          `))}
                      </div>
                    `:f``}
                ${t.item.cluster_size>1?f`
                      <div class="layout horizontal center wrap">
                        <lablup-shields
                          app="${"single-node"===t.item.cluster_mode?"Multi-container":"Multi-node"}"
                          color="blue"
                          description="${"X "+t.item.cluster_size}"
                          ui="round"
                          class="right-below-margin"
                        ></lablup-shields>
                      </div>
                    `:f``}
              </div>
            </div>
          </div>
        `,e)}architectureRenderer(e,i,t){b(f`
        <lablup-shields
          app=""
          color="lightgreen"
          description="${t.item.architecture}"
          ui="round"
        ></lablup-shields>
      `,e)}controlRenderer(e,i,t){var s;let o=!0;o="API"===this._connectionMode&&t.item.access_key===globalThis.backendaiclient._config._accessKey||t.item.user_email===globalThis.backendaiclient.email,b(f`
        <div
          id="controls"
          class="layout horizontal wrap center"
          .session-uuid="${t.item.session_id}"
          .session-name="${t.item[this.sessionNameField]}"
          .access-key="${t.item.access_key}"
          .kernel-image="${t.item.kernel_image}"
          .app-services="${t.item.app_services}"
          .app-services-option="${t.item.app_services_option}"
          .service-ports="${t.item.service_ports}"
        >
          ${t.item.appSupport&&"system"!==this.condition?f`
                <mwc-icon-button
                  class="fg controls-running green"
                  id="${t.index+"-apps"}"
                  @click="${e=>this._showAppLauncher(e)}"
                  ?disabled="${!o}"
                  icon="apps"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${t.index+"-apps"}"
                  text="${w("session.SeeAppDialog")}"
                  position="top-start"
                ></vaadin-tooltip>
                <mwc-icon-button
                  class="fg controls-running"
                  id="${t.index+"-terminal"}"
                  ?disabled="${!o}"
                  @click="${e=>this._runTerminal(e)}"
                >
                  <svg
                    version="1.1"
                    id="Capa_1"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlns:xlink="http://www.w3.org/1999/xlink"
                    x="0px"
                    y="0px"
                    width="471.362px"
                    height="471.362px"
                    viewBox="0 0 471.362 471.362"
                    style="enable-background:new 0 0 471.362 471.362;"
                    xml:space="preserve"
                  >
                    <g>
                      <g>
                        <path
                          d="M468.794,355.171c-1.707-1.718-3.897-2.57-6.563-2.57H188.145c-2.664,0-4.854,0.853-6.567,2.57
                    c-1.711,1.711-2.565,3.897-2.565,6.563v18.274c0,2.662,0.854,4.853,2.565,6.563c1.713,1.712,3.903,2.57,6.567,2.57h274.086
                    c2.666,0,4.856-0.858,6.563-2.57c1.711-1.711,2.567-3.901,2.567-6.563v-18.274C471.365,359.068,470.513,356.882,468.794,355.171z"
                        />
                        <path
                          d="M30.259,85.075c-1.903-1.903-4.093-2.856-6.567-2.856s-4.661,0.953-6.563,2.856L2.852,99.353
                    C0.95,101.255,0,103.442,0,105.918c0,2.478,0.95,4.664,2.852,6.567L115.06,224.69L2.852,336.896C0.95,338.799,0,340.989,0,343.46
                    c0,2.478,0.95,4.665,2.852,6.567l14.276,14.273c1.903,1.906,4.089,2.854,6.563,2.854s4.665-0.951,6.567-2.854l133.048-133.045
                    c1.903-1.902,2.853-4.096,2.853-6.57c0-2.473-0.95-4.663-2.853-6.565L30.259,85.075z"
                        />
                      </g>
                    </g>
                  </svg>
                </mwc-icon-button>
                <vaadin-tooltip
                  for="${t.index+"-terminal"}"
                  text="${w("session.ExecuteTerminalApp")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:f``}
          ${this._isRunning&&"system"===this.condition?f`
                <mwc-icon-button
                  class="fg green controls-running"
                  id="${t.index+"-sftp-connection-info"}"
                  @click="${()=>this._openSFTPSessionConnectionInfoDialog(t.item.id,t.item.mounts.length>0?t.item.mounts.filter((e=>!e.startsWith(".")))[0]:"")}"
                >
                  <img src="/resources/icons/sftp.png" />
                </mwc-icon-button>
                <vaadin-tooltip
                  for="${t.index+"-sftp-connection-info"}"
                  text="${w("data.explorer.RunSSH/SFTPserver")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:f``}
          ${this._isRunning&&!this._isPreparing(t.item.status)||this._isError(t.item.status)?f`
                <mwc-icon-button
                  class="fg red controls-running"
                  id="${t.index+"-power"}"
                  ?disabled=${!this._isPending(t.item.status)&&"ongoing"===(null===(s=t.item)||void 0===s?void 0:s.commit_status)}
                  icon="power_settings_new"
                  @click="${e=>this._openTerminateSessionDialog(e)}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${t.index+"-power"}"
                  text="${w("session.TerminateSession")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:f``}
          ${(this._isRunning&&!this._isPreparing(t.item.status)||this._APIMajorVersion>4)&&!["RESTARTING","PENDING","PULLING"].includes(t.item.status)?f`
                <mwc-icon-button
                  class="fg blue controls-running"
                  id="${t.index+"-assignment"}"
                  icon="assignment"
                  ?disabled="${"CANCELLED"===t.item.status}"
                  @click="${e=>{var i,t;this._setSelectedSession(e),this._setSelectedKernel(),this.selectedKernelId=null===(i=this.selectedKernels[0])||void 0===i?void 0:i.kernel_id,(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#kernel-id-select")).value=this.selectedKernelId,this._showLogs()}}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${t.index+"-assignment"}"
                  text="${w("session.SeeContainerLogs")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:f`
                <mwc-icon-button
                  fab
                  flat
                  inverted
                  disabled
                  class="fg controls-running"
                  id="${t.index+"-assignment"}"
                  icon="assignment"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${t.index+"-assignment"}"
                  text="${w("session.NoLogMsgAvailable")}"
                  position="top-start"
                ></vaadin-tooltip>
              `}
          ${this._isContainerCommitEnabled&&"system"!==this.condition?f`
                <mwc-icon-button
                  class="fg blue controls-running"
                  id="${t.index+"-archive"}"
                  ?disabled=${this._isPending(t.item.status)||this._isPreparing(t.item.status)||this._isError(t.item.status)||this._isFinished(t.item.status)||"BATCH"===t.item.type||"ongoing"===t.item.commit_status||t.item.user_email!==globalThis.backendaiclient.email}
                  icon="archive"
                  @click="${e=>this._openCommitSessionDialog(e)}"
                ></mwc-icon-button>
                <vaadin-tooltip
                  for="${t.index+"-archive"}"
                  text="${w("session.RequestContainerCommit")}"
                  position="top-start"
                ></vaadin-tooltip>
              `:f``}
        </div>
      `,e)}configRenderer(e,i,t){const s=t.item.mounts.map((e=>e.startsWith("[")?JSON.parse(e.replace(/'/g,'"'))[0]:e));"system"===this.condition?b(f``,e):b(f`
          <div class="layout horizontal center flex">
            <div class="layout horizontal center configuration">
              ${t.item.mounts.length>0?f`
                    <mwc-icon class="fg green indicator">folder_open</mwc-icon>
                    <button
                      class="mount-button"
                      @mouseenter="${e=>this._createMountedFolderDropdown(e,s)}"
                      @mouseleave="${()=>this._removeMountedFolderDropdown()}"
                    >
                      ${s.join(", ")}
                    </button>
                  `:f`
                    <mwc-icon class="no-mount indicator">folder_open</mwc-icon>
                    <span class="no-mount">No mount</span>
                  `}
            </div>
          </div>
          ${t.item.scaling_group?f`
                <div class="layout horizontal center flex">
                  <div class="layout horizontal center configuration">
                    <mwc-icon class="fg green indicator">work</mwc-icon>
                    <span>${t.item.scaling_group}</span>
                    <span class="indicator">RG</span>
                  </div>
                </div>
              `:f``}
          <div class="layout vertical flex" style="padding-left: 25px">
            <div class="layout horizontal center configuration">
              <mwc-icon class="fg green indicator">developer_board</mwc-icon>
              <span>${t.item.cpu_slot}</span>
              <span class="indicator">${w("session.core")}</span>
            </div>
            <div class="layout horizontal center configuration">
              <mwc-icon class="fg green indicator">memory</mwc-icon>
              <span>${t.item.mem_slot}</span>
              <span class="indicator">GiB</span>
              ${this.isDisplayingAllocatedShmemEnabled?f`
                    <span class="indicator">
                      ${"(SHM: "+this._aggregateSharedMemory(JSON.parse(t.item.resource_opts))+"GiB)"}
                    </span>
                  `:f``}
            </div>
            <div class="layout horizontal center configuration">
              ${t.item.cuda_gpu_slot?f`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/file_type_cuda.svg"
                    />
                    <span>${t.item.cuda_gpu_slot}</span>
                    <span class="indicator">GPU</span>
                  `:f``}
              ${!t.item.cuda_gpu_slot&&t.item.cuda_fgpu_slot?f`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/file_type_cuda.svg"
                    />
                    <span>${t.item.cuda_fgpu_slot}</span>
                    <span class="indicator">FGPU</span>
                  `:f``}
              ${t.item.rocm_gpu_slot?f`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/rocm.svg"
                    />
                    <span>${t.item.rocm_gpu_slot}</span>
                    <span class="indicator">GPU</span>
                  `:f``}
              ${t.item.tpu_slot?f`
                    <mwc-icon class="fg green indicator">view_module</mwc-icon>
                    <span>${t.item.tpu_slot}</span>
                    <span class="indicator">TPU</span>
                  `:f``}
              ${t.item.ipu_slot?f`
                    <mwc-icon class="fg green indicator">view_module</mwc-icon>
                    <span>${t.item.ipu_slot}</span>
                    <span class="indicator">IPU</span>
                  `:f``}
              ${t.item.atom_slot?f`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/rebel.svg"
                    />
                    <span>${t.item.atom_slot}</span>
                    <span class="indicator">ATOM</span>
                  `:f``}
              ${t.item.gaudi2_slot?f`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/gaudi.svg"
                    />
                    <span>${t.item.gaudi2_slot}</span>
                    <span class="indicator">Gaudi 2</span>
                  `:f``}
              ${t.item.atom_plus_slot?f`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/rebel.svg"
                    />
                    <span>${t.item.atom_plus_slot}</span>
                    <span class="indicator">ATOM+</span>
                  `:f``}
              ${t.item.warboy_slot?f`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/furiosa.svg"
                    />
                    <span>${t.item.warboy_slot}</span>
                    <span class="indicator">Warboy</span>
                  `:f``}
              ${t.item.rngd_slot?f`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/furiosa.svg"
                    />
                    <span>${t.item.rngd_slot}</span>
                    <span class="indicator">RNGD</span>
                  `:f``}
              ${t.item.hyeraccel_lpu_slot?f`
                    <img
                      class="indicator-icon fg green"
                      src="/resources/icons/npu_generic.svg"
                    />
                    <span>${t.item.hyeraccel_lpu_slot}</span>
                    <span class="indicator">Hyperaccel LPU</span>
                  `:f``}
              ${t.item.cuda_gpu_slot||t.item.cuda_fgpu_slot||t.item.rocm_gpu_slot||t.item.tpu_slot||t.item.ipu_slot||t.item.atom_slot||t.item.atom_plus_slot||t.item.gaudi2_slot||t.item.warboy_slot||t.item.rngd_slot||t.item.hyperaccel_lpu_slot?f``:f`
                    <mwc-icon class="fg green indicator">view_module</mwc-icon>
                    <span>-</span>
                    <span class="indicator">GPU</span>
                  `}
            </div>
          </div>
        `,e)}usageRenderer(e,i,t){var s,o,n,a,l,r,c,d,u,p,m,h,g,v,_,y,w,k,x,A,$,S,T,C,I,D,E,R,N,F,M,z,L,B,P,O,G,U,K,W,H,q,Z,V,J,Y,Q,X,ee,ie,te,se,oe,ne,ae,le,re,ce,de,ue,pe,me,he,ge,ve,_e,be,fe,ye,we,ke,xe,Ae,$e,Se,Te,Ce,Ie,De,Ee,Re,je,Ne,Fe,Me,ze,Le,Be,Pe,Oe,Ge,Ue,Ke,We,He,qe,Ze,Ve,Je,Ye,Qe,Xe,ei,ii,ti,si,oi,ni,ai,li,ri,ci,di,ui,pi,mi,hi,gi,vi,_i,bi,fi,yi,wi,ki,xi,Ai,$i,Si,Ti,Ci,Ii,Di,Ei,Ri,ji,Ni,Fi,Mi,zi,Li,Bi,Pi,Oi,Gi,Ui,Ki,Wi,Hi,qi,Zi,Vi,Ji,Yi,Qi,Xi,et,it,tt,st,ot,nt,at,lt,rt,ct,dt,ut,pt;["batch","interactive","inference","running"].includes(this.condition)?b(f`
          <div class="vertical start start-justified layout">
            <div class="vertical start-justified layout">
              <div class="usage-items">
                CPU
                ${t.item.live_stat?(100*(null===(o=null===(s=t.item.live_stat)||void 0===s?void 0:s.cpu_util)||void 0===o?void 0:o.ratio)).toFixed(1):"-"}
                %
              </div>
              <div class="horizontal start-justified center layout">
                <lablup-progress-bar
                  class="usage"
                  progress="${(null===(a=null===(n=t.item.live_stat)||void 0===n?void 0:n.cpu_util)||void 0===a?void 0:a.ratio)/(null===(r=null===(l=t.item.live_stat)||void 0===l?void 0:l.cpu_util)||void 0===r?void 0:r.slots)||0}"
                  description=""
                ></lablup-progress-bar>
              </div>
            </div>
            <div class="vertical start-justified layout">
              <div class="usage-items">
                RAM
                ${t.item.live_stat?`${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(d=null===(c=t.item.live_stat)||void 0===c?void 0:c.mem)||void 0===d?void 0:d.current,2),2)} /\n                    ${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(p=null===(u=t.item.live_stat)||void 0===u?void 0:u.mem)||void 0===p?void 0:p.capacity,2),2)}`:"-"}
                GiB
              </div>
              <div class="horizontal start-justified center layout">
                <lablup-progress-bar
                  class="usage"
                  progress="${null===(h=null===(m=t.item.live_stat)||void 0===m?void 0:m.mem)||void 0===h?void 0:h.ratio}"
                  description=""
                ></lablup-progress-bar>
              </div>
            </div>
            ${t.item.cuda_gpu_slot&&parseInt(t.item.cuda_gpu_slot)>0?f`
                  <div class="vertical start-justified center layout">
                    <div class="usage-items">
                      GPU(util)
                      ${t.item.live_stat?(100*(null===(v=null===(g=t.item.live_stat)||void 0===g?void 0:g.cuda_util)||void 0===v?void 0:v.ratio)).toFixed(1):"-"}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(y=null===(_=t.item.live_stat)||void 0===_?void 0:_.cuda_util)||void 0===y?void 0:y.current)/(null===(k=null===(w=t.item.live_stat)||void 0===w?void 0:w.cuda_util)||void 0===k?void 0:k.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.cuda_fgpu_slot&&parseFloat(t.item.cuda_fgpu_slot)>0?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      GPU(util)
                      ${t.item.live_stat?(100*(null===(A=null===(x=t.item.live_stat)||void 0===x?void 0:x.cuda_util)||void 0===A?void 0:A.ratio)).toFixed(1):"-"}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(S=null===($=t.item.live_stat)||void 0===$?void 0:$.cuda_util)||void 0===S?void 0:S.current)/(null===(C=null===(T=t.item.live_stat)||void 0===T?void 0:T.cuda_util)||void 0===C?void 0:C.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.cuda_fgpu_slot?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      GPU(mem)
                      ${t.item.live_stat?`${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(D=null===(I=t.item.live_stat)||void 0===I?void 0:I.cuda_mem)||void 0===D?void 0:D.current,2),2)} /\n                            ${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(R=null===(E=t.item.live_stat)||void 0===E?void 0:E.cuda_mem)||void 0===R?void 0:R.capacity,2),2)}`:"-"}
                      GiB
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${null===(F=null===(N=t.item.live_stat)||void 0===N?void 0:N.cuda_mem)||void 0===F?void 0:F.ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.rocm_gpu_slot&&parseFloat(t.item.rocm_gpu_slot)>0?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      GPU(util)
                      ${t.item.live_stat?(100*(null===(z=null===(M=t.item.live_stat)||void 0===M?void 0:M.rocm_util)||void 0===z?void 0:z.ratio)).toFixed(1):"-"}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(B=null===(L=t.item.live_stat)||void 0===L?void 0:L.rocm_util)||void 0===B?void 0:B.current)/(null===(O=null===(P=t.item.live_stat)||void 0===P?void 0:P.rocm_util)||void 0===O?void 0:O.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.rocm_gpu_slot?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      GPU(mem)
                      ${t.item.live_stat?`${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(U=null===(G=t.item.live_stat)||void 0===G?void 0:G.rocm_mem)||void 0===U?void 0:U.current,2),2)} /\n                          ${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(W=null===(K=t.item.live_stat)||void 0===K?void 0:K.rocm_mem)||void 0===W?void 0:W.capacity,2),2)}`:"-"}
                      GiB
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${null===(q=null===(H=t.item.live_stat)||void 0===H?void 0:H.rocm_mem)||void 0===q?void 0:q.ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.tpu_slot&&parseFloat(t.item.tpu_slot)>0?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      TPU(util)
                      ${t.item.live_stat?(100*(null===(V=null===(Z=t.item.live_stat)||void 0===Z?void 0:Z.tpu_util)||void 0===V?void 0:V.ratio)).toFixed(1):"-"}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(Y=null===(J=t.item.live_stat)||void 0===J?void 0:J.tpu_util)||void 0===Y?void 0:Y.current)/(null===(X=null===(Q=t.item.live_stat)||void 0===Q?void 0:Q.tpu_util)||void 0===X?void 0:X.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.tpu_slot?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      TPU(mem)
                      ${t.item.live_stat?`${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(ie=null===(ee=t.item.live_stat)||void 0===ee?void 0:ee.tpu_mem)||void 0===ie?void 0:ie.current,2),2)} /\n                    ${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(se=null===(te=t.item.live_stat)||void 0===te?void 0:te.tpu_mem)||void 0===se?void 0:se.capacity,2),2)}`:"-"}
                      GiB
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${null===(ne=null===(oe=t.item.live_stat)||void 0===oe?void 0:oe.tpu_mem)||void 0===ne?void 0:ne.ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.ipu_slot&&parseFloat(t.item.ipu_slot)>0?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      IPU(util)
                      ${t.item.live_stat?(100*(null===(le=null===(ae=t.item.live_stat)||void 0===ae?void 0:ae.ipu_util)||void 0===le?void 0:le.ratio)).toFixed(1):"-"}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(de=null===(ce=null===(re=t.item)||void 0===re?void 0:re.live_stat)||void 0===ce?void 0:ce.ipu_util)||void 0===de?void 0:de.current)/(null===(me=null===(pe=null===(ue=t.item)||void 0===ue?void 0:ue.live_stat)||void 0===pe?void 0:pe.ipu_util)||void 0===me?void 0:me.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.ipu_slot?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      IPU(mem)
                      ${t.item.live_stat?`${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(ge=null===(he=t.item.live_stat)||void 0===he?void 0:he.ipu_mem)||void 0===ge?void 0:ge.current,2),2)} /\n                      ${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(_e=null===(ve=t.item.live_stat)||void 0===ve?void 0:ve.ipu_mem)||void 0===_e?void 0:_e.capacity,2),2)}`:"-"}
                      GiB
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${null===(fe=null===(be=t.item.live_stat)||void 0===be?void 0:be.ipu_mem)||void 0===fe?void 0:fe.ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.atom_slot&&parseFloat(t.item.atom_slot)>0?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      ATOM(util)
                      ${t.item.live_stat?(100*(null===(we=null===(ye=t.item.live_stat)||void 0===ye?void 0:ye.atom_util)||void 0===we?void 0:we.ratio)).toFixed(1):"-"}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(Ae=null===(xe=null===(ke=t.item)||void 0===ke?void 0:ke.live_stat)||void 0===xe?void 0:xe.atom_util)||void 0===Ae?void 0:Ae.current)/(null===(Te=null===(Se=null===($e=t.item)||void 0===$e?void 0:$e.live_stat)||void 0===Se?void 0:Se.atom_util)||void 0===Te?void 0:Te.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.atom_slot?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      ATOM(mem)
                      ${t.item.live_stat?`${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(Ie=null===(Ce=t.item.live_stat)||void 0===Ce?void 0:Ce.atom_mem)||void 0===Ie?void 0:Ie.current,2),2)} /\n                      ${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(Ee=null===(De=t.item.live_stat)||void 0===De?void 0:De.atom_mem)||void 0===Ee?void 0:Ee.capacity,2),2)}`:"-"}
                      GiB
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${null===(je=null===(Re=t.item.live_stat)||void 0===Re?void 0:Re.atom_mem)||void 0===je?void 0:je.ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.atom_plus_slot&&parseFloat(t.item.atom_plus_slot)>0?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      ATOM+(util)
                      ${(null===(Ne=t.item.live_stat)||void 0===Ne?void 0:Ne.atom_plus_util)?(100*(null===(Me=null===(Fe=t.item.live_stat)||void 0===Fe?void 0:Fe.atom_plus_util)||void 0===Me?void 0:Me.ratio)).toFixed(1):"-"}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(Be=null===(Le=null===(ze=t.item)||void 0===ze?void 0:ze.live_stat)||void 0===Le?void 0:Le.atom_plus_util)||void 0===Be?void 0:Be.current)/(null===(Ge=null===(Oe=null===(Pe=t.item)||void 0===Pe?void 0:Pe.live_stat)||void 0===Oe?void 0:Oe.atom_plus_util)||void 0===Ge?void 0:Ge.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.atom_plus_slot?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      ATOM+(mem)
                      ${t.item.live_stat?`${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(Ke=null===(Ue=t.item.live_stat)||void 0===Ue?void 0:Ue.atom_plus_mem)||void 0===Ke?void 0:Ke.current,2),2)} /\n                      ${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(He=null===(We=t.item.live_stat)||void 0===We?void 0:We.atom_plus_mem)||void 0===He?void 0:He.capacity,2),2)}`:"-"}
                      GiB
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${null===(Ze=null===(qe=t.item.live_stat)||void 0===qe?void 0:qe.atom_plus_mem)||void 0===Ze?void 0:Ze.ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.gaudi2_slot&&parseFloat(t.item.gaudi2_slot)>0?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      Gaudi 2(util)
                      ${(null===(Ve=t.item.live_stat)||void 0===Ve?void 0:Ve.gaudi2_util)?(100*(null===(Ye=null===(Je=t.item.live_stat)||void 0===Je?void 0:Je.gaudi2_util)||void 0===Ye?void 0:Ye.ratio)).toFixed(1):"-"}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(ei=null===(Xe=null===(Qe=t.item)||void 0===Qe?void 0:Qe.live_stat)||void 0===Xe?void 0:Xe.gaudi2_util)||void 0===ei?void 0:ei.current)/(null===(si=null===(ti=null===(ii=t.item)||void 0===ii?void 0:ii.live_stat)||void 0===ti?void 0:ti.gaudi2_util)||void 0===si?void 0:si.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.gaudi2_slot?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      Gaudi 2(mem)
                      ${t.item.live_stat?`${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(ni=null===(oi=t.item.live_stat)||void 0===oi?void 0:oi.gaudi2_mem)||void 0===ni?void 0:ni.current,2),2)} /\n                      ${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(li=null===(ai=t.item.live_stat)||void 0===ai?void 0:ai.gaudi2_mem)||void 0===li?void 0:li.capacity,2),2)}`:"-"}
                      GiB
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${null===(ci=null===(ri=t.item.live_stat)||void 0===ri?void 0:ri.gaudi2_mem)||void 0===ci?void 0:ci.ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.warboy_slot&&parseFloat(t.item.warboy_slot)>0?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      Warboy(util)
                      ${(null===(di=t.item.live_stat)||void 0===di?void 0:di.warboy_util)?(100*(null===(pi=null===(ui=t.item.live_stat)||void 0===ui?void 0:ui.warboy_util)||void 0===pi?void 0:pi.ratio)).toFixed(1):"-"}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(gi=null===(hi=null===(mi=t.item)||void 0===mi?void 0:mi.live_stat)||void 0===hi?void 0:hi.warboy_util)||void 0===gi?void 0:gi.current)/(null===(bi=null===(_i=null===(vi=t.item)||void 0===vi?void 0:vi.live_stat)||void 0===_i?void 0:_i.warboy_util)||void 0===bi?void 0:bi.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.warboy_slot?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      Warboy(mem)
                      ${t.item.live_stat?`${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(yi=null===(fi=t.item.live_stat)||void 0===fi?void 0:fi.warboy_mem)||void 0===yi?void 0:yi.current,2),2)} /\n                        ${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(ki=null===(wi=t.item.live_stat)||void 0===wi?void 0:wi.warboy_mem)||void 0===ki?void 0:ki.capacity,2),2)}`:"-"}
                      GiB
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${null===(Ai=null===(xi=t.item.live_stat)||void 0===xi?void 0:xi.warboy_mem)||void 0===Ai?void 0:Ai.ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.rngd_slot&&parseFloat(t.item.rngd_slot)>0?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      RNGD(util)
                      ${(null===($i=t.item.live_stat)||void 0===$i?void 0:$i.rngd_util)?(100*(null===(Ti=null===(Si=t.item.live_stat)||void 0===Si?void 0:Si.rngd_util)||void 0===Ti?void 0:Ti.ratio)).toFixed(1):"-"}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(Di=null===(Ii=null===(Ci=t.item)||void 0===Ci?void 0:Ci.live_stat)||void 0===Ii?void 0:Ii.rngd_util)||void 0===Di?void 0:Di.current)/(null===(ji=null===(Ri=null===(Ei=t.item)||void 0===Ei?void 0:Ei.live_stat)||void 0===Ri?void 0:Ri.rngd_util)||void 0===ji?void 0:ji.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.rngd_slot?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      RNGD(mem)
                      ${t.item.live_stat?`${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(Fi=null===(Ni=t.item.live_stat)||void 0===Ni?void 0:Ni.rngd_mem)||void 0===Fi?void 0:Fi.current,2),2)} /\n                      ${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(zi=null===(Mi=t.item.live_stat)||void 0===Mi?void 0:Mi.rngd_mem)||void 0===zi?void 0:zi.capacity,2),2)}`:"-"}
                      GiB
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${null===(Bi=null===(Li=t.item.live_stat)||void 0===Li?void 0:Li.rngd_mem)||void 0===Bi?void 0:Bi.ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.hyeraccel_lpu_slot&&parseFloat(t.item.hyeraccel_lpu_slot)>0?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      Hyperaccel LPU(util)
                      ${(null===(Pi=t.item.live_stat)||void 0===Pi?void 0:Pi.hyeraccel_lpu_util)?(100*(null===(Gi=null===(Oi=t.item.live_stat)||void 0===Oi?void 0:Oi.hyeraccel_lpu_util)||void 0===Gi?void 0:Gi.ratio)).toFixed(1):"-"}
                      %
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${(null===(Wi=null===(Ki=null===(Ui=t.item)||void 0===Ui?void 0:Ui.live_stat)||void 0===Ki?void 0:Ki.hyeraccel_lpu_util)||void 0===Wi?void 0:Wi.current)/(null===(Zi=null===(qi=null===(Hi=t.item)||void 0===Hi?void 0:Hi.live_stat)||void 0===qi?void 0:qi.hyeraccel_lpu_util)||void 0===Zi?void 0:Zi.capacity)||0}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            ${t.item.hyeraccel_lpu_slot?f`
                  <div class="vertical start-justified layout">
                    <div class="usage-items">
                      Hyperaccel LPU(mem)
                      ${t.item.live_stat?`${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(Ji=null===(Vi=t.item.live_stat)||void 0===Vi?void 0:Vi.hyeraccel_lpu_mem)||void 0===Ji?void 0:Ji.current,2),2)} /\n                      ${j._prefixFormatWithoutTrailingZeros(j.bytesToGiB(null===(Qi=null===(Yi=t.item.live_stat)||void 0===Yi?void 0:Yi.hyeraccel_lpu_mem)||void 0===Qi?void 0:Qi.capacity,2),2)}`:"-"}
                      GiB
                    </div>
                    <div class="horizontal start-justified center layout">
                      <lablup-progress-bar
                        class="usage"
                        progress="${null===(et=null===(Xi=t.item.live_stat)||void 0===Xi?void 0:Xi.hyeraccel_lpu_mem)||void 0===et?void 0:et.ratio}"
                        description=""
                      ></lablup-progress-bar>
                    </div>
                  </div>
                `:f``}
            <div class="horizontal start-justified center layout">
              <div class="usage-items">I/O</div>
              <div
                style="font-size:10px;margin-left:5px;"
                class="horizontal start-justified center layout"
              >
                R:
                ${t.item.live_stat?null===(st=null===(tt=null===(it=t.item)||void 0===it?void 0:it.live_stat)||void 0===tt?void 0:tt.io_read)||void 0===st?void 0:st.current.toFixed(1):"-"}
                MB / W:
                ${t.item.live_stat?null===(at=null===(nt=null===(ot=t.item)||void 0===ot?void 0:ot.live_stat)||void 0===nt?void 0:nt.io_write)||void 0===at?void 0:at.current.toFixed(1):"-"}
                MB
              </div>
            </div>
          </div>
        `,e):"finished"===this.condition&&b(f`
          <div class="layout horizontal center flex">
            <mwc-icon class="fg green indicator" style="margin-right:3px;">
              developer_board
            </mwc-icon>
            ${t.item.cpu_used_time.D?f`
                  <div class="vertical center-justified center layout">
                    <span style="font-size:11px">
                      ${t.item.cpu_used_time.D}
                    </span>
                    <span class="indicator">day</span>
                  </div>
                `:f``}
            ${t.item.cpu_used_time.H?f`
                  <div class="vertical center-justified center layout">
                    <span style="font-size:11px">
                      ${t.item.cpu_used_time.H}
                    </span>
                    <span class="indicator">hour</span>
                  </div>
                `:f``}
            ${t.item.cpu_used_time.M?f`
                  <div class="vertical start layout">
                    <span style="font-size:11px">
                      ${t.item.cpu_used_time.M}
                    </span>
                    <span class="indicator">min.</span>
                  </div>
                `:f``}
            ${t.item.cpu_used_time.S?f`
                  <div class="vertical start layout">
                    <span style="font-size:11px">
                      ${t.item.cpu_used_time.S}
                    </span>
                    <span class="indicator">sec.</span>
                  </div>
                `:f``}
            ${t.item.cpu_used_time.MS?f`
                  <div class="vertical start layout">
                    <span style="font-size:11px">
                      ${t.item.cpu_used_time.MS}
                    </span>
                    <span class="indicator">msec.</span>
                  </div>
                `:f``}
            ${t.item.cpu_used_time.NODATA?f`
                  <div class="vertical start layout">
                    <span style="font-size:11px">No data</span>
                  </div>
                `:f``}
          </div>
          <div class="layout horizontal center flex">
            <mwc-icon class="fg blue indicator" style="margin-right:3px;">
              device_hub
            </mwc-icon>
            <div class="vertical start layout">
              <span style="font-size:9px">
                ${null!==(ct=null===(rt=null===(lt=t.item.live_stat)||void 0===lt?void 0:lt.io_read)||void 0===rt?void 0:rt.current.toFixed(1))&&void 0!==ct?ct:"-"}
                <span class="indicator">MB</span>
              </span>
              <span class="indicator">READ</span>
            </div>
            <div class="vertical start layout">
              <span style="font-size:8px">
                ${null!==(pt=null===(ut=null===(dt=t.item.live_stat)||void 0===dt?void 0:dt.io_write)||void 0===ut?void 0:ut.current.toFixed(1))&&void 0!==pt?pt:"-"}
                <span class="indicator">MB</span>
              </span>
              <span class="indicator">WRITE</span>
            </div>
          </div>
        `,e)}reservationRenderer(e,i,t){b(f`
        <div class="layout vertical" style="padding:3px auto;">
          <span>
            ${t.item.starts_at_hr||t.item.created_at_hr}
          </span>
          <backend-ai-session-reservation-timer
            value="${JSON.stringify({starts_at:t.item.starts_at||t.item.created_at,terminated_at:t.item.terminated_at})}"
          ></backend-ai-session-reservation-timer>
        </div>
      `,e)}idleChecksHeaderRenderer(e,i){b(f`
        <div class="horizontal layout center">
          <div>${w("session.IdleChecks")}</div>
          <mwc-icon-button
            class="fg grey"
            icon="info"
            @click="${()=>this._openIdleChecksInfoDialog()}"
          ></mwc-icon-button>
        </div>
      `,e)}idleChecksRenderer(e,i,t){var s;const o=null===(s=Object.keys(t.item.idle_checks))||void 0===s?void 0:s.map((e=>{var i,s;const o=t.item.idle_checks[e],n=null==o?void 0:o.remaining;if(!n)return;const a=globalThis.backendaiclient.utils.elapsedTimeToTotalSeconds(n),l=null==o?void 0:o.remaining_time_type;let r,c="var(--token-colorSuccess";return!a||a<3600?c="var(--token-colorError)":a<14400&&(c="var(--token-colorWarning)"),"utilization"===e&&(null==o?void 0:o.extra)&&(!a||a<14400)&&(c=this.getUtilizationCheckerColor(null===(i=null==o?void 0:o.extra)||void 0===i?void 0:i.resources,null===(s=null==o?void 0:o.extra)||void 0===s?void 0:s.thresholds_check_operator)),r="utilization"===e?f`
            <button
              class="idle-check-key"
              style="color:#42a5f5;"
              @mouseenter="${e=>{var i,s,o;return this._createUtilizationIdleCheckDropdown(e,null===(o=null===(s=null===(i=t.item.idle_checks)||void 0===i?void 0:i.utilization)||void 0===s?void 0:s.extra)||void 0===o?void 0:o.resources)}}"
              @mouseleave="${()=>this._removeUtilizationIdleCheckDropdown()}"
            >
              ${y("session."+this.idleChecksTable[e])}
            </button>
          `:f`
            <button class="idle-check-key" style="color:#222222;">
              ${y("session."+this.idleChecksTable[e])}
            </button>
          `,e in this.idleChecksTable?f`
            <div class="layout vertical" style="padding:3px auto;">
              <div style="margin:4px;">
                ${r}
                <br />
                <strong style="color:${c}">${n}</strong>
                <div class="idle-type">
                  ${y("session."+this.idleChecksTable[l])}
                </div>
              </div>
            </div>
          `:f``})),n=f`
      ${o}
    `;b(n,e)}agentListRenderer(e,i,t){var s,o;b(f`
        <pre>${null!==(o=null===(s=null==t?void 0:t.item)||void 0===s?void 0:s.agents_ids_with_container_ids)&&void 0!==o?o:""}</pre>
      `,e)}_aggregateSharedMemory(e){let i=0;return Object.keys(e).forEach((t=>{var s,o;i+=Number(null!==(o=null===(s=e[t])||void 0===s?void 0:s.shmem)&&void 0!==o?o:0)})),j.bytesToGiB(i)}userInfoRenderer(e,i,t){const s="API"===this._connectionMode?t.item.access_key:t.item.user_email;b(f`
        <div class="layout vertical">
          <span class="indicator">${this._getUserId(s)}</span>
        </div>
      `,e)}statusRenderer(e,i,t){var s;b(f`
        <div class="horizontal layout center">
          <span style="font-size: 12px;">${t.item.status}</span>
          ${t.item.status_data&&"{}"!==t.item.status_data?f`
                <mwc-icon-button
                  class="fg green status"
                  icon="help"
                  @click="${()=>{var e;return this._openStatusDetailDialog(null!==(e=t.item.status_info)&&void 0!==e?e:"",t.item.status_data,t.item.starts_at_hr)}}"
                ></mwc-icon-button>
              `:f``}
        </div>
        ${t.item.status_info?f`
              <div class="layout horizontal">
                <lablup-shields
                  id="${t.item.name}"
                  app=""
                  color="${this.statusColorTable[t.item.status_info]}"
                  description="${t.item.status_info}"
                  ui="round"
                ></lablup-shields>
              </div>
            `:f``}
        ${this._isContainerCommitEnabled&&void 0!==(null===(s=t.item)||void 0===s?void 0:s.commit_status)?f`
              <lablup-shields
                app=""
                color="${this._setColorOfStatusInformation(t.item.commit_status)}"
                class="right-below-margin"
                description=${"ongoing"===t.item.commit_status?"commit on-going":""}
              ></lablup-shields>
            `:f``}
      `,e)}_setColorOfStatusInformation(e="ready"){return"ready"===e?"green":"lightgrey"}_getUserId(e=""){if(e&&this.isUserInfoMaskEnabled){const i=/^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/.test(e),t=i?2:0,s=i?e.split("@")[0].length-t:0;e=globalThis.backendaiutils._maskString(e,"*",t,s)}return e}_renderCommitSessionConfirmationDialog(e){var i,t,s,o,n,a,l;return f`
      <backend-ai-dialog id="commit-session-dialog" fixed backdrop>
        <span slot="title">${w("session.CommitSession")}</span>
        <div slot="content" class="vertical layout center flex">
          <span style="font-size:14px;">
            ${w("session.DescCommitSession")}
          </span>
          <div class="vertical flex start layout" style="width:100%;">
            <h4 class="commit-session-title">${w("session.SessionName")}</h4>
            <span class="commit-session-subheading">
              ${null!==(t=null===(i=null==e?void 0:e.session)||void 0===i?void 0:i.name)&&void 0!==t?t:"-"}
            </span>
          </div>
          <div class="vertical flex start layout" style="width:100%;">
            <h4 class="commit-session-title">${w("session.SessionId")}</h4>
            <span class="commit-session-subheading">
              ${null!==(o=null===(s=null==e?void 0:e.session)||void 0===s?void 0:s.id)&&void 0!==o?o:"-"}
            </span>
          </div>
          <div class="vertical flex start layout" style="width:100%;">
            <h4 class="commit-session-title">
              ${w("session.EnvironmentAndVersion")}
            </h4>
            <span class="commit-session-subheading">
              ${e?f`
                    <lablup-shields
                      app="${null!==(n=e.environment)&&void 0!==n?n:"-"}"
                      color="blue"
                      description="${null!==(a=e.version)&&void 0!==a?a:"-"}"
                      ui="round"
                      class="right-below-margin"
                    ></lablup-shields>
                  `:f``}
            </span>
          </div>
          <div class="vertical flex start layout" style="width:100%;">
            <h4 class="commit-session-title">${w("session.Tags")}</h4>
            <div class="horizontal wrap layout">
              ${e?null===(l=null==e?void 0:e.tags)||void 0===l?void 0:l.map((e=>f`
                      <lablup-shields
                        app=""
                        color="green"
                        description="${e}"
                        ui="round"
                        class="right-below-margin"
                      ></lablup-shields>
                    `)):f`
                    <lablup-shields
                      app=""
                      color="green"
                      description="-"
                      ui="round"
                      style="right-below-margin"
                    ></lablup-shields>
                  `}
            </div>
          </div>
          <div class="vertical flex start layout" style="width:100%;">
            <h4 class="commit-session-title">${w("session.SessionName")}</h4>
            <div class="horizontal layout flex" style="width:100%">
              <!--<mwc-checkbox
                class="list-check"
                ?checked="${this.pushImageInsteadOfCommiting}"
                @click="${()=>{this.pushImageInsteadOfCommiting=!this.pushImageInsteadOfCommiting}}"
              ></mwc-checkbox>-->
              <mwc-textfield
                id="new-image-name-field"
                required
                pattern="^[a-zA-Z0-9_\\-]{4,}$"
                minLength="4"
                maxLength="32"
                placeholder="${w("inputLimit.4to32chars")}"
                validationMessage="${y("session.Validation.EnterValidSessionName")}"
                style="margin-top:8px;width:100%;"
                autoValidate
                @input="${this._validateImageName}"
              ></mwc-textfield>
            </div>
          </div>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            unelevated
            class="ok"
            style="font-size:smaller"
            ?disabled="${!this.canStartImagifying}"
            @click=${()=>{this._requestConvertSessionToimage(e)}}
            label="${w("button.PushToImage")}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}_parseSessionInfoToCommitSessionInfo(e="",i="",t=""){const s=["",""],[o,n]=e?e.split(":"):s,[a,...l]=n?n.split("-"):s;return{environment:o,version:a,tags:l,session:{name:i,id:t}}}render(){var e,i,t;return f`
      <link rel="stylesheet" href="resources/custom.css">
      <div class="layout horizontal center filters">
        <div id="multiple-action-buttons" style="display:none;">
          <mwc-button icon="delete" class="multiple-action-button" raised style="margin:8px;"
            @click="${()=>this._openTerminateSelectedSessionsDialog()}">${w("session.Terminate")}
          </mwc-button>
        </div>
        <span class="flex"></span>
        <div class="vertical layout" style="display:none">
          <mwc-textfield id="access-key-filter" type="search" maxLength="64"
            label="${w("general.AccessKey")}" 
            no-label-float .value="${this.filterAccessKey}"
            style="margin-right:20px;"
            @change="${e=>this._updateFilterAccessKey(e)}">
          </mwc-textfield>
          <span id="access-key-filter-helper-text">${w("maxLength.64chars")}</span>
        </div>
      </div>
      <div class="list-wrapper">
        ${this.active?f`
                <vaadin-grid
                  id="list-grid"
                  theme="row-stripes column-borders compact dark"
                  aria-label="Session list"
                  .items="${this.compute_sessions}"
                  height-by-rows
                >
                  ${this._isRunning?f`
                        <vaadin-grid-selection-column
                          frozen
                        ></vaadin-grid-selection-column>
                      `:f``}
                  <vaadin-grid-column
                    frozen
                    width="40px"
                    flex-grow="0"
                    header="#"
                    .renderer="${this._indexRenderer}"
                  ></vaadin-grid-column>
                  ${this.is_admin?f`
                        <lablup-grid-sort-filter-column
                          frozen
                          path="${"API"===this._connectionMode?"access_key":"user_email"}"
                          header="${"API"===this._connectionMode?"API Key":"User ID"}"
                          resizable
                          .renderer="${this._boundUserInfoRenderer}"
                        ></lablup-grid-sort-filter-column>
                      `:f``}
                  <lablup-grid-sort-filter-column
                    frozen
                    path="${this.sessionNameField}"
                    width="260px"
                    header="${w("session.SessionInfo")}"
                    resizable
                    .renderer="${this._boundSessionInfoRenderer}"
                  ></lablup-grid-sort-filter-column>
                  <lablup-grid-sort-filter-column
                    width="120px"
                    path="status"
                    header="${w("session.Status")}"
                    resizable
                    .renderer="${this._boundStatusRenderer}"
                  ></lablup-grid-sort-filter-column>
                  <vaadin-grid-column
                    width=${this._isContainerCommitEnabled?"260px":"210px"}
                    flex-grow="0"
                    resizable
                    header="${w("general.Control")}"
                    .renderer="${this._boundControlRenderer}"
                  ></vaadin-grid-column>
                  <vaadin-grid-column
                    width="200px"
                    flex-grow="0"
                    resizable
                    header="${w("session.Configuration")}"
                    .renderer="${this._boundConfigRenderer}"
                  ></vaadin-grid-column>
                  <vaadin-grid-column
                    width="140px"
                    flex-grow="0"
                    resizable
                    header="${w("session.Usage")}"
                    .renderer="${this._boundUsageRenderer}"
                  ></vaadin-grid-column>
                  <vaadin-grid-sort-column
                    resizable
                    width="180px"
                    flex-grow="0"
                    header="${w("session.Reservation")}"
                    path="created_at"
                    .renderer="${this._boundReservationRenderer}"
                  ></vaadin-grid-sort-column>
                  ${globalThis.backendaiclient.supports("idle-checks")&&this.activeIdleCheckList.size>0?f`
                        <vaadin-grid-column
                          resizable
                          width="180px"
                          flex-grow="0"
                          .headerRenderer="${this._boundIdleChecksHeaderderer}"
                          .renderer="${this._boundIdleChecksRenderer}"
                        ></vaadin-grid-column>
                      `:f``}
                  ${this._isIntegratedCondition?f`
                        <lablup-grid-sort-filter-column
                          path="type"
                          width="140px"
                          flex-grow="0"
                          header="${w("session.launcher.SessionType")}"
                          resizable
                          .renderer="${this._boundSessionTypeRenderer}"
                        ></lablup-grid-sort-filter-column>
                      `:f``}
                  ${this.is_superadmin||!globalThis.backendaiclient._config.hideAgents?f`
                        <lablup-grid-sort-filter-column
                          path="agents_ids_with_container_ids"
                          width="140px"
                          flex-grow="0"
                          resizable
                          header="${w("session.Agents")}"
                          .renderer="${this._boundAgentListRenderer}"
                        ></lablup-grid-sort-filter-column>
                      `:f``}
                  <lablup-grid-sort-filter-column
                    width="110px"
                    path="architecture"
                    header="${w("session.Architecture")}"
                    resizable
                    .renderer="${this._boundArchitectureRenderer}"
                  ></lablup-grid-sort-filter-column>
                </vaadin-grid>
              `:f``}
        
          <backend-ai-list-status id="list-status" statusCondition="${this.listCondition}" message="${y("session.NoSessionToDisplay")}"></backend-ai-list-status>
        </div>
      </div>
      <div class="horizontal center-justified layout flex" style="padding: 10px;">
        <mwc-icon-button
          class="pagination"
          id="previous-page"
          icon="navigate_before"
          ?disabled="${1===this.current_page}"
          @click="${e=>this._updateSessionPage(e)}"></mwc-icon-button>
        <div class="pagination-label">
        ${this.current_page} / ${Math.ceil(this.total_session_count/this.session_page_limit)}</div>
        <mwc-icon-button
          class="pagination"
          id="next-page"
          icon="navigate_next"
          ?disabled="${this.total_session_count<=this.session_page_limit*this.current_page}"
          @click="${e=>this._updateSessionPage(e)}"></mwc-icon-button>
      </div>
      <backend-ai-dialog id="work-dialog" narrowLayout scrollable fixed backdrop>
        <span slot="title" id="work-title">
        </span>
        <div slot="action" class="horizontal layout center">
          <mwc-select
            id="kernel-id-select"
            label="Kernel Role"
            style="display: ${this._isPerKernelLogSupported?"block":"none"}"
            @selected=${()=>{this._updateLogsByKernelId(),this._showLogs()}}
          >
            ${this.selectedKernels.map((e=>f`
                <mwc-list-item
                  value=${e.kernel_id}
                  label="${e.role}"
                  ?selected=${e.role.includes("main")}
                >
                  ${e.role}
                </mwc-list-item>
              `))}
          </mwc-select>
          <mwc-icon-button fab flat inverted icon="download" @click="${()=>this._downloadLogs()}">
          </mwc-icon-button>
          <mwc-icon-button fab flat inverted icon="refresh" @click="${e=>this._refreshLogs()}">
          </mwc-icon-button>
        </div>
        <div slot="content" id="work-area" style="overflow:scroll;"></div>
        <iframe id="work-page" style="border-style: none;display: none;width: 100%;"></iframe>
      </backend-ai-dialog>
      <backend-ai-dialog id="terminate-session-dialog" fixed backdrop>
        <span slot="title">${w("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${w("usersettings.SessionTerminationDialog")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button class="warning fg red" @click="${()=>{this._getManualCleanUpNeededContainers(),this._openForceTerminateConfirmationDialog()}}">
            ${w("button.ForceTerminate")}
          </mwc-button>
          <span class="flex"></span>
          <mwc-button class="cancel" @click="${e=>this._hideDialog(e)}">${w("button.Cancel")}
          </mwc-button>
          <mwc-button class="ok" raised @click="${()=>this._terminateSessionWithCheck()}">${w("button.Okay")}</mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="terminate-selected-sessions-dialog" fixed backdrop>
        <span slot="title">${w("dialog.title.LetsDouble-Check")}</span>
        <div slot="content">
          <p>${w("usersettings.SessionTerminationDialog")}</p>
        </div>
        <div slot="footer" class="horizontal end-justified flex layout">
          <mwc-button
            class="warning fg red"
            @click="${()=>{this._getManualCleanUpNeededContainers(),this._openForceTerminateConfirmationDialog()}}">
            ${w("button.ForceTerminate")}
          </mwc-button>
          <span class="flex"></span>
          <mwc-button class="cancel" @click="${e=>this._hideDialog(e)}">${w("button.Cancel")}
          </mwc-button>
          <mwc-button class="ok" raised @click="${()=>this._terminateSelectedSessionsWithCheck()}">${w("button.Okay")}
          </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="force-terminate-confirmation-dialog" fixed backdrop>
        <span slot="title">${w("session.WarningForceTerminateSessions")}</span>
        <div slot="content">
          <span>${w("session.ForceTerminateWarningMsg")}</span>
          <ul class="force-terminate-confirmation">
            <li>${w("session.ForceTerminateWarningMsg2")}</li>
            <li>${w("session.ForceTerminateWarningMsg3")}</li>
          </ul>
          ${this._manualCleanUpNeededContainers.length>0&&this.is_superadmin?f`
                  <div
                    class="vertical layout flex start-justified force-terminate-confirmation-container-list"
                  >
                    <div class="horizontal layout center flex start-justified">
                      <h3 style="margin:0px;">
                        ${w("session.ContainerToCleanUp")}:
                      </h3>
                    </div>
                    ${this._manualCleanUpNeededContainers.map((e=>f`
                        <ul class="force-terminate-confirmation">
                          <li>Agent ID: ${e.agent}</li>
                          <ul class="force-terminate-confirmation">
                            ${e.containers.map((e=>f`
                                <li>
                                  Container ID:
                                  <span class="monospace">${e}</span>
                                </li>
                              `))}
                          </ul>
                          <ul></ul>
                        </ul>
                      `))}
                  </div>
                `:f``}
        </div>
        <div slot="footer" class="horizontal layout flex cetner-justified">
            <mwc-button
              raised
              class="warning fg red"
              style="width:100%;"
              @click="${()=>{this.forceTerminateConfirmationDialog.hide(),this.terminateSessionDialog.open?(this.terminateSessionDialog.hide(),this._terminateSessionWithCheck(!0)):(this.terminateSelectedSessionsDialog.hide(),this._terminateSelectedSessionsWithCheck(!0))}}">
                ${w("button.ForceTerminate")}
            </mwc-button>
        </div>
      </backend-ai-dialog>
      <backend-ai-dialog id="status-detail-dialog" narrowLayout fixed backdrop>
        <span slot="title">${w("session.StatusInfo")}</span>
        <div slot="content" id="status-detail"></div>
      </backend-ai-dialog>
      <backend-ai-dialog id="help-description" narrowLayout fixed backdrop>
        <span slot="title">${this._helpDescriptionTitle}</span>
        <div slot="content" class="horizontal layout center" style="margin:5px;">
        ${""==this._helpDescriptionIcon?f``:f`
                <img
                  slot="graphic"
                  alt="help icon"
                  src="resources/icons/${this._helpDescriptionIcon}"
                  style="width:64px;height:64px;margin-right:10px;"
                />
              `}
          <div style="font-size:14px;">${k(this._helpDescription)}</div>
        </div>
      </backend-ai-dialog>
      ${this._renderCommitSessionConfirmationDialog(this._parseSessionInfoToCommitSessionInfo(null===(e=this.commitSessionDialog)||void 0===e?void 0:e.kernelImage,null===(i=this.commitSessionDialog)||void 0===i?void 0:i.sessionName,null===(t=this.commitSessionDialog)||void 0===t?void 0:t.sessionId))}
    `}_updateSessionPage(e){"previous-page"===e.target.id?this.current_page-=1:this.current_page+=1,this.refreshList()}_validateImageName(){this.newImageNameInput.validityTransform=(e,i)=>i.valid?(this.canStartImagifying=!0,this.newImageName=e,{valid:i.valid,customError:!i.valid}):(this.canStartImagifying=!1,i.patternMismatch?(this.newImageNameInput.validationMessage=y("session.Validation.EnterValidSessionName"),{valid:i.valid,patternMismatch:!i.valid}):(this.newImageNameInput.validationMessage=y("session.Validation.EnterValidSessionName"),{valid:i.valid,customError:!i.valid}))}};var F;c([d({type:Boolean,reflect:!0})],N.prototype,"active",void 0),c([d({type:String})],N.prototype,"condition",void 0),c([d({type:Object})],N.prototype,"jobs",void 0),c([d({type:Array})],N.prototype,"compute_sessions",void 0),c([d({type:Array})],N.prototype,"terminationQueue",void 0),c([d({type:String})],N.prototype,"filterAccessKey",void 0),c([d({type:String})],N.prototype,"sessionNameField",void 0),c([d({type:Array})],N.prototype,"appSupportList",void 0),c([d({type:Object})],N.prototype,"appTemplate",void 0),c([d({type:Object})],N.prototype,"imageInfo",void 0),c([d({type:Array})],N.prototype,"_selected_items",void 0),c([d({type:Array})],N.prototype,"_manualCleanUpNeededContainers",void 0),c([d({type:Object})],N.prototype,"_boundControlRenderer",void 0),c([d({type:Object})],N.prototype,"_boundConfigRenderer",void 0),c([d({type:Object})],N.prototype,"_boundUsageRenderer",void 0),c([d({type:Object})],N.prototype,"_boundReservationRenderer",void 0),c([d({type:Object})],N.prototype,"_boundIdleChecksHeaderderer",void 0),c([d({type:Object})],N.prototype,"_boundIdleChecksRenderer",void 0),c([d({type:Object})],N.prototype,"_boundAgentListRenderer",void 0),c([d({type:Object})],N.prototype,"_boundSessionInfoRenderer",void 0),c([d({type:Object})],N.prototype,"_boundArchitectureRenderer",void 0),c([d({type:Object})],N.prototype,"_boundUserInfoRenderer",void 0),c([d({type:Object})],N.prototype,"_boundStatusRenderer",void 0),c([d({type:Object})],N.prototype,"_boundSessionTypeRenderer",void 0),c([d({type:Boolean})],N.prototype,"refreshing",void 0),c([d({type:Boolean})],N.prototype,"is_admin",void 0),c([d({type:Boolean})],N.prototype,"is_superadmin",void 0),c([d({type:String})],N.prototype,"_connectionMode",void 0),c([d({type:Object})],N.prototype,"notification",void 0),c([d({type:Boolean})],N.prototype,"enableScalingGroup",void 0),c([d({type:Boolean})],N.prototype,"isDisplayingAllocatedShmemEnabled",void 0),c([d({type:String})],N.prototype,"listCondition",void 0),c([d({type:Object})],N.prototype,"refreshTimer",void 0),c([d({type:Object})],N.prototype,"kernel_labels",void 0),c([d({type:Object})],N.prototype,"kernel_icons",void 0),c([d({type:Object})],N.prototype,"indicator",void 0),c([d({type:String})],N.prototype,"_helpDescription",void 0),c([d({type:String})],N.prototype,"_helpDescriptionTitle",void 0),c([d({type:String})],N.prototype,"_helpDescriptionIcon",void 0),c([d({type:Set})],N.prototype,"activeIdleCheckList",void 0),c([d({type:Array})],N.prototype,"selectedKernels",void 0),c([d({type:String})],N.prototype,"selectedKernelId",void 0),c([d({type:Proxy})],N.prototype,"statusColorTable",void 0),c([d({type:Proxy})],N.prototype,"idleChecksTable",void 0),c([d({type:Proxy})],N.prototype,"sessionTypeColorTable",void 0),c([d({type:Number})],N.prototype,"sshPort",void 0),c([d({type:Number})],N.prototype,"vncPort",void 0),c([d({type:Number})],N.prototype,"current_page",void 0),c([d({type:Number})],N.prototype,"session_page_limit",void 0),c([d({type:Number})],N.prototype,"total_session_count",void 0),c([d({type:Number})],N.prototype,"_APIMajorVersion",void 0),c([d({type:Object})],N.prototype,"selectedSessionStatus",void 0),c([d({type:Boolean})],N.prototype,"isUserInfoMaskEnabled",void 0),c([d({type:Boolean})],N.prototype,"pushImageInsteadOfCommiting",void 0),c([d({type:Boolean})],N.prototype,"canStartImagifying",void 0),c([d({type:String})],N.prototype,"newImageName",void 0),c([u("#loading-spinner")],N.prototype,"spinner",void 0),c([u("#list-grid")],N.prototype,"_grid",void 0),c([u("#access-key-filter")],N.prototype,"accessKeyFilterInput",void 0),c([u("#new-image-name-field")],N.prototype,"newImageNameInput",void 0),c([u("#multiple-action-buttons")],N.prototype,"multipleActionButtons",void 0),c([u("#access-key-filter-helper-text")],N.prototype,"accessKeyFilterHelperText",void 0),c([u("#terminate-session-dialog")],N.prototype,"terminateSessionDialog",void 0),c([u("#terminate-selected-sessions-dialog")],N.prototype,"terminateSelectedSessionsDialog",void 0),c([u("#force-terminate-confirmation-dialog")],N.prototype,"forceTerminateConfirmationDialog",void 0),c([u("#status-detail-dialog")],N.prototype,"sessionStatusInfoDialog",void 0),c([u("#work-dialog")],N.prototype,"workDialog",void 0),c([u("#help-description")],N.prototype,"helpDescriptionDialog",void 0),c([u("#commit-session-dialog")],N.prototype,"commitSessionDialog",void 0),c([u("#commit-current-session-path-input")],N.prototype,"commitSessionInput",void 0),c([u("#list-status")],N.prototype,"_listStatus",void 0),N=j=c([p("backend-ai-session-list")],N);let M=F=class extends m{constructor(){super(),this._status="inactive",this.active=!1,this.is_admin=!1,this.enableInferenceWorkload=!1,this.enableSFTPSession=!1,this.filterAccessKey="",this._connectionMode="API",this._defaultFileName="",this.active=!1,this._status="inactive"}static get styles(){return[h,g,v,x,A,t`
        mwc-menu {
          --mdc-menu-item-height: auto;
        }

        mwc-menu#dropdown-menu {
          position: relative;
          left: -170px;
          top: 50px;
        }

        mwc-list-item {
          font-size: 14px;
        }

        mwc-icon-button {
          --mdc-icon-size: 20px;
          color: var(--paper-grey-700);
        }

        mwc-icon-button#dropdown-menu-button {
          margin-left: 10px;
        }

        mwc-textfield {
          width: 100%;
          --mdc-text-field-fill-color: transparent;
          --mdc-theme-primary: var(--paper-green-600);
        }

        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }

        backend-ai-resource-monitor {
          margin: 10px 50px;
        }

        backend-ai-session-launcher#session-launcher {
          --component-width: 100px;
          --component-shadow-color: transparent;
        }
        @media screen and (max-width: 805px) {
          mwc-tab {
            --mdc-typography-button-font-size: 10px;
          }
        }
      `]}firstUpdated(){this.notification=globalThis.lablupNotification,document.addEventListener("backend-ai-session-list-refreshed",(()=>{this.runningJobs.refreshList(!0,!1)})),this.resourceBroker=globalThis.resourceBroker,void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{this.is_admin=globalThis.backendaiclient.is_admin,this._connectionMode=globalThis.backendaiclient._config._connectionMode}),!0):(this.is_admin=globalThis.backendaiclient.is_admin,this._connectionMode=globalThis.backendaiclient._config._connectionMode)}async _viewStateChanged(e){if(await this.updateComplete,!1===e){this.resourceMonitor.removeAttribute("active"),this._status="inactive";for(let e=0;e<this.sessionList.length;e++)this.sessionList[e].removeAttribute("active");return}const i=()=>{this.enableInferenceWorkload=globalThis.backendaiclient.supports("inference-workload"),this.enableSFTPSession=globalThis.backendaiclient.supports("sftp-scaling-group"),this.resourceMonitor.setAttribute("active","true"),this.runningJobs.setAttribute("active","true"),this._status="active"};void 0===globalThis.backendaiclient||null===globalThis.backendaiclient||!1===globalThis.backendaiclient.ready?document.addEventListener("backend-ai-connected",(()=>{i()}),!0):i()}_triggerClearTimeout(){const e=new CustomEvent("backend-ai-clear-timeout");document.dispatchEvent(e)}_showTab(e){var i,t,s;const o=null===(i=this.shadowRoot)||void 0===i?void 0:i.querySelectorAll(".tab-content");for(let e=0;e<o.length;e++)o[e].style.display="none";(null===(t=this.shadowRoot)||void 0===t?void 0:t.querySelector("#"+e.title+"-lists")).style.display="block";for(let e=0;e<this.sessionList.length;e++)this.sessionList[e].removeAttribute("active");this._triggerClearTimeout(),(null===(s=this.shadowRoot)||void 0===s?void 0:s.querySelector("#"+e.title+"-jobs")).setAttribute("active","true")}_toggleDropdown(e){const i=this.dropdownMenu,t=e.target;i.anchor=t,i.open||i.show()}_openExportToCsvDialog(){const e=this.dropdownMenu;e.open&&e.close(),console.log("Downloading CSV File..."),this._defaultFileName=this._getDefaultCSVFileName(),this.exportToCsvDialog.show()}_getFirstDateOfMonth(){const e=new Date;return new Date(e.getFullYear(),e.getMonth(),2).toISOString().substring(0,10)}_getDefaultCSVFileName(){return(new Date).toISOString().substring(0,10)+"_"+(new Date).toTimeString().slice(0,8).replace(/:/gi,"-")}_validateDateRange(){const e=this.dateToInput,i=this.dateFromInput;if(e.value&&i.value){new Date(e.value).getTime()<new Date(i.value).getTime()&&(e.value=i.value)}}static _automaticScaledTime(e){let i=Object();const t=["D","H","M","S"],s=[864e5,36e5,6e4,1e3];for(let o=0;o<s.length;o++)Math.floor(e/s[o])>0&&(i[t[o]]=Math.floor(e/s[o]),e%=s[o]);return 0===Object.keys(i).length&&(i=e>0?{MS:e}:{NODATA:1}),i}static bytesToMiB(e,i=1){return Number(e/2**20).toFixed(1)}_exportToCSV(){const e=this.exportFileNameInput;if(!e.validity.valid)return;const i=[];let t;t=globalThis.backendaiclient.supports("avoid-hol-blocking")?["RUNNING","RESTARTING","TERMINATING","PENDING","SCHEDULED","PREPARING","PULLING","TERMINATED","CANCELLED","ERROR"]:["RUNNING","RESTARTING","TERMINATING","PENDING","PREPARING","PULLING","TERMINATED","CANCELLED","ERROR"],globalThis.backendaiclient.supports("prepared-session-status")&&t.push("PREPARED"),globalThis.backendaiclient.supports("detailed-session-states")&&(t=t.join(","));const s=["id","name","user_email","image","created_at","terminated_at","status","status_info","access_key","cluster_mode","occupying_slots"];"SESSION"===this._connectionMode&&s.push("user_email"),globalThis.backendaiclient.is_superadmin?s.push("containers {container_id agent occupied_slots live_stat last_stat}"):s.push("containers {container_id occupied_slots live_stat last_stat}");const o=globalThis.backendaiclient.current_group_id(),n=Object.keys(this.resourceBroker.total_slot).filter((e=>!["cpu","mem"].includes(e))),a={cuda_device:"cuda.device",cuda_shares:"cuda.shares",rocm_device:"rocm.device",tpu_device:"tpu.device",ipu_device:"ipu.device",atom_device:"atom.device",atom_plus_device:"atom-plus.device",gaudi2_device:"gaudi2.device",warboy_device:"warboy.device",rngd_device:"rngd.device",hyperaccel_lpu_device:"hyperaccel-lpu.device"};globalThis.backendaiclient.computeSession.listAll(s,t,this.filterAccessKey,100,0,o).then((t=>{const s=t;if(0===s.length)return this.notification.text=y("session.NoSession"),this.notification.show(),void this.exportToCsvDialog.hide();s.forEach((e=>{const t=JSON.parse(e.occupying_slots),s={};if(s.id=e.id,s.name=e.name,s.image=e.image.split("/")[2]||e.image.split("/")[1],s.cluster_mode=e.cluster_mode,s.user_email=e.user_email,s.status=e.status,s.status_info=e.status_info,s.access_key=e.access_key,s.cpu_slot=parseInt(t.cpu),s.mem_slot=parseFloat(globalThis.backendaiclient.utils.changeBinaryUnit(t.mem,"g")).toFixed(2),n.forEach((e=>{var i;s[e]=null!==(i=t[a[e]])&&void 0!==i?i:0})),s.created_at=e.created_at,s.terminated_at=e.terminated_at,e.containers&&e.containers.length>0){let i=0,t=0,o=0,n=0,a=0,l=0,r=0;const c=[];e.containers.forEach((e=>{c.push(e.agent);const s=e.live_stat?JSON.parse(e.live_stat):null;s&&(s.cpu_used&&s.cpu_used.current&&(i+=parseFloat(s.cpu_used.current)),s.cpu_util&&s.cpu_util.pct&&(t+=parseFloat(s.cpu_util.pct)),s.mem&&s.mem.pct&&(o+=parseFloat(s.mem.pct)),s.cuda_util&&s.cuda_util.pct&&(n+=parseFloat(s.cuda_util.pct)),s.cuda_mem&&s.cuda_mem.current&&(a+=parseFloat(s.cuda_mem.current)),s.io_read&&(l+=parseFloat(s.io_read.current)),s.io_write&&(r+=parseFloat(s.io_write.current)))})),s.agents=[...new Set(c)],s.cpu_used_time=F._automaticScaledTime(i/e.containers.length),s.cpu_util=(t/e.containers.length).toFixed(2),s.mem_util=(o/e.containers.length).toFixed(2),s.cuda_util=(n/e.containers.length).toFixed(2),s.cuda_mem_bytes_mb=F.bytesToMiB(a/e.containers.length),s.io_read_bytes_mb=F.bytesToMiB(l/e.containers.length),s.io_write_bytes_mb=F.bytesToMiB(r/e.containers.length)}i.push(s)})),$.exportToCsv(e.value,i),this.notification.text=y("session.DownloadingCSVFile"),this.notification.show(),this.exportToCsvDialog.hide()}))}render(){return f`
      <link rel="stylesheet" href="resources/custom.css" />
      <div class="vertical layout" style="gap:24px;">
        <lablup-activity-panel
          title="${w("summary.ResourceStatistics")}"
          elevation="1"
          autowidth
        >
          <div slot="message">
            <backend-ai-resource-monitor
              location="session"
              id="resource-monitor"
              ?active="${!0===this.active}"
            ></backend-ai-resource-monitor>
          </div>
        </lablup-activity-panel>
        <lablup-activity-panel
          title="${w("summary.Announcement")}"
          elevation="1"
          horizontalsize="2x"
          style="display:none;"
        ></lablup-activity-panel>
        <lablup-activity-panel elevation="1" autowidth narrow noheader>
          <div slot="message">
            <h3
              class="tab horizontal center layout"
              style="margin-top:0;margin-bottom:0;"
            >
              <div class="scroll hide-scrollbar">
                <div
                  class="horizontal layout flex start-justified"
                  style="width:70%;"
                >
                  <mwc-tab-bar>
                    <mwc-tab
                      title="running"
                      label="${w("session.Running")}"
                      @click="${e=>this._showTab(e.target)}"
                    ></mwc-tab>
                    <mwc-tab
                      title="interactive"
                      label="${w("session.Interactive")}"
                      @click="${e=>this._showTab(e.target)}"
                    ></mwc-tab>
                    <mwc-tab
                      title="batch"
                      label="${w("session.Batch")}"
                      @click="${e=>this._showTab(e.target)}"
                    ></mwc-tab>
                    ${this.enableInferenceWorkload?f`
                            <mwc-tab
                              title="inference"
                              label="${w("session.Inference")}"
                              @click="${e=>this._showTab(e.target)}"
                            ></mwc-tab>
                          `:f``}
                    ${this.enableSFTPSession?f`
                            <mwc-tab
                              title="system"
                              label="${w("session.System")}"
                              @click="${e=>this._showTab(e.target)}"
                            ></mwc-tab>
                          `:f``}
                    <mwc-tab
                      title="finished"
                      label="${w("session.Finished")}"
                      @click="${e=>this._showTab(e.target)}"
                    ></mwc-tab>
                  </mwc-tab-bar>
                </div>
              </div>
              ${this.is_admin?f`
                      <div style="position: relative;">
                        <mwc-icon-button
                          id="dropdown-menu-button"
                          icon="more_horiz"
                          raised
                          @click="${e=>this._toggleDropdown(e)}"
                        ></mwc-icon-button>
                        <mwc-menu id="dropdown-menu">
                          <mwc-list-item>
                            <a
                              class="horizontal layout start center export-csv"
                              @click="${()=>this._openExportToCsvDialog()}"
                            >
                              <mwc-icon
                                style="color:var(--token-colorTextSecondary);padding-right:10px;"
                              >
                                get_app
                              </mwc-icon>
                              ${w("session.exportCSV")}
                            </a>
                          </mwc-list-item>
                        </mwc-menu>
                      </div>
                    `:f``}
              <div
                class="horizontal layout flex end-justified"
                style="margin-right:20px;"
              >
                <backend-ai-session-launcher
                  location="session"
                  id="session-launcher"
                  ?active="${!0===this.active}"
                  ?allowNEOSessionLauncher="${!0}"
                ></backend-ai-session-launcher>
              </div>
            </h3>
            <div id="running-lists" class="tab-content">
              <backend-ai-session-list
                id="running-jobs"
                condition="running"
              ></backend-ai-session-list>
            </div>
            <div
              id="interactive-lists"
              class="tab-content"
              style="display:none;"
            >
              <backend-ai-session-list
                id="interactive-jobs"
                condition="interactive"
              ></backend-ai-session-list>
            </div>
            <div id="batch-lists" class="tab-content" style="display:none;">
              <backend-ai-session-list
                id="batch-jobs"
                condition="batch"
              ></backend-ai-session-list>
            </div>
            ${this.enableInferenceWorkload?f`
                    <div
                      id="inference-lists"
                      class="tab-content"
                      style="display:none;"
                    >
                      <backend-ai-session-list
                        id="inference-jobs"
                        condition="inference"
                      ></backend-ai-session-list>
                    </div>
                  `:f``}
            ${this.enableSFTPSession?f`
                    <div
                      id="system-lists"
                      class="tab-content"
                      style="display:none;"
                    >
                      <backend-ai-session-list
                        id="system-jobs"
                        condition="system"
                      ></backend-ai-session-list>
                    </div>
                  `:f``}
            <div id="finished-lists" class="tab-content" style="display:none;">
              <backend-ai-session-list
                id="finished-jobs"
                condition="finished"
              ></backend-ai-session-list>
            </div>
            <div id="others-lists" class="tab-content" style="display:none;">
              <backend-ai-session-list
                id="others-jobs"
                condition="others"
              ></backend-ai-session-list>
            </div>
          </div>
        </lablup-activity-panel>
      </div>
      <backend-ai-dialog id="export-to-csv" fixed backdrop>
        <span slot="title">${w("session.ExportSessionListToCSVFile")}</span>
        <div slot="content">
          <mwc-textfield
            id="export-file-name"
            label="File name"
            validationMessage="${w("data.explorer.ValueRequired")}"
            value="${"session_"+this._defaultFileName}"
            required
            style="margin-bottom:10px;"
          ></mwc-textfield>
        <div slot="footer" class="horizontal flex layout">
          <mwc-button
            unelevated
            fullwidth
            icon="get_app"
            label="${w("session.ExportCSVFile")}"
            class="export-csv"
            @click="${this._exportToCSV}"
          ></mwc-button>
        </div>
      </backend-ai-dialog>
    `}};c([d({type:String})],M.prototype,"_status",void 0),c([d({type:Boolean,reflect:!0})],M.prototype,"active",void 0),c([d({type:Boolean})],M.prototype,"is_admin",void 0),c([d({type:Boolean})],M.prototype,"enableInferenceWorkload",void 0),c([d({type:Boolean})],M.prototype,"enableSFTPSession",void 0),c([d({type:String})],M.prototype,"filterAccessKey",void 0),c([d({type:String})],M.prototype,"_connectionMode",void 0),c([d({type:Object})],M.prototype,"_defaultFileName",void 0),c([d({type:Object})],M.prototype,"resourceBroker",void 0),c([function(i){return(t,s)=>e(t,s,{get(){return(this.renderRoot??(S??=document.createDocumentFragment())).querySelectorAll(i)}})}("backend-ai-session-list")],M.prototype,"sessionList",void 0),c([u("#running-jobs")],M.prototype,"runningJobs",void 0),c([u("#resource-monitor")],M.prototype,"resourceMonitor",void 0),c([u("#export-file-name")],M.prototype,"exportFileNameInput",void 0),c([u("#date-from")],M.prototype,"dateFromInput",void 0),c([u("#date-to")],M.prototype,"dateToInput",void 0),c([u("#dropdown-menu")],M.prototype,"dropdownMenu",void 0),c([u("#export-to-csv")],M.prototype,"exportToCsvDialog",void 0),M=F=c([p("backend-ai-session-view")],M);
