import{t as e}from"./jsx-runtime-BapUIyWk.js";import{R as t}from"./usePressFeedback-BIoIGSxE.js";var n=e();function r({label:e,valueLabel:r,value:i,hasValueLabel:a=!0,color:o,width:s,size:c=`sm`,className:l,style:u,labelStyle:d}){let f=i===void 0||Number.isNaN(i),p=!i||Number.isNaN(i)?0:Math.min(i,100),m=typeof s==`number`||typeof s==`string`;return(0,n.jsxs)(`div`,{className:[`uic-progress-with-label`,`uic-progress-with-label--${c}`,!m&&`uic-progress-with-label--grow`,l].filter(Boolean).join(` `),style:{...m?{width:s}:null,...u},children:[(0,n.jsx)(`div`,{className:`uic-progress-with-label__fill`,style:{width:`${p}%`,...o?{backgroundColor:o}:null}}),(0,n.jsxs)(`div`,{className:`uic-progress-with-label__labels`,children:[(0,n.jsx)(t,{className:`uic-progress-with-label__text`,style:d,children:e}),(0,n.jsx)(t,{className:`uic-progress-with-label__text uic-progress-with-label__value`,color:f?`disabled`:void 0,style:d,children:a?r:` `})]})]})}r.displayName=`ProgressWithLabel`;
/**
@license
Copyright (c) 2015-2026 Lablup Inc. All rights reserved.

ui-common `ProgressWithLabel` under its BUI name (FR-4096): `title` →
`label`, `percent` → `value`, `showInfo` → `hasValueLabel`, `strokeColor` →
`color`, `progressStyle` → `style`, antd sizes → sm / md / lg.
BAIProgressWithLabel.css keeps the WebUI's 3px frame corner.
*/
var i={small:`sm`,middle:`md`,large:`lg`},a=({title:e,valueLabel:t,percent:a,width:o,strokeColor:s,labelStyle:c,progressStyle:l,showInfo:u=!0,size:d=`small`})=>(0,n.jsx)(r,{className:`bai-progress-with-label`,label:e,valueLabel:t,value:a,hasValueLabel:u,color:s,width:o,size:i[d],style:l,labelStyle:c});export{a as t};
