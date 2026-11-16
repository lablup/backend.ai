import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{Zn as t}from"./icons-Btg1s2wy.js";import{t as n}from"./compiler-runtime-CZQb2eIb.js";import{t as r}from"./jsx-runtime-BapUIyWk.js";import{t as i}from"./react-relay-BfoHYpUf.js";import{t as a}from"./BAISkeleton-MIjJv1Hr.js";import{t as o}from"./react-error-boundary-DESmfvQ5.js";import{t as s}from"./BAIEntityLabelSettingModal-BzN4qIYx.js";import{t as c}from"./BAIEntityLabelCell-DOyaclRH.js";var l=n(),u=(function(){var e=[{defaultValue:null,kind:`LocalArgument`,name:`scope`}],t=[{kind:`Literal`,name:`limit`,value:100},{kind:`Variable`,name:`scope`,variableName:`scope`}];return{fragment:{argumentDefinitions:e,kind:`Fragment`,metadata:null,name:`BAIEntityLabelTargetCellQuery`,selections:[{alias:null,args:t,concreteType:`EntityLabelConnection`,kind:`LinkedField`,name:`entityLabels`,plural:!1,selections:[{args:null,kind:`FragmentSpread`,name:`BAIEntityLabelTokensFragment`},{args:null,kind:`FragmentSpread`,name:`BAIEntityLabelSettingModalFragment`}],storageKey:null}],type:`Query`,abstractKey:null},kind:`Request`,operation:{argumentDefinitions:e,kind:`Operation`,name:`BAIEntityLabelTargetCellQuery`,selections:[{alias:null,args:t,concreteType:`EntityLabelConnection`,kind:`LinkedField`,name:`entityLabels`,plural:!1,selections:[{alias:null,args:null,concreteType:`EntityLabelEdge`,kind:`LinkedField`,name:`edges`,plural:!0,selections:[{alias:null,args:null,concreteType:`EntityLabel`,kind:`LinkedField`,name:`node`,plural:!1,selections:[{alias:null,args:null,kind:`ScalarField`,name:`key`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`value`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`id`,storageKey:null},{alias:null,args:null,kind:`ScalarField`,name:`fieldId`,storageKey:null}],storageKey:null}],storageKey:null}],storageKey:null}]},params:{cacheID:`da85370b5fbee3a4d5125f0e691c372e`,id:null,metadata:{},name:`BAIEntityLabelTargetCellQuery`,operationKind:`query`,text:`query BAIEntityLabelTargetCellQuery(
  $scope: [EntityTarget!]!
) {
  entityLabels(scope: $scope, limit: 100) {
    ...BAIEntityLabelTokensFragment
    ...BAIEntityLabelSettingModalFragment
  }
}

fragment BAIEntityLabelSettingModalFragment on EntityLabelConnection {
  edges {
    node {
      fieldId
      key
      value
      id
    }
  }
}

fragment BAIEntityLabelTokensFragment on EntityLabelConnection {
  edges {
    node {
      key
      value
      id
    }
  }
}
`}}})();u.hash=`18dfa7c4e46860362bbe714962ffb5d1`;var d=e(t(),1),f=i(),p=r(),m=e=>{"use memo";let t=(0,l.c)(22),{entityType:n,entityId:r,name:i,readOnly:a,editDisabledReason:o,onLabelClick:m}=e,h=a!==void 0&&a,[_,v]=(0,d.useState)(0),[,y]=(0,d.useTransition)(),[b,x]=(0,d.useState)(!1),S;t[0]!==r||t[1]!==n?(S={scope:[{entityType:n,entityId:r}]},t[0]=r,t[1]=n,t[2]=S):S=t[2];let C;t[3]===_?C=t[4]:(C={fetchKey:_,fetchPolicy:`store-and-network`},t[3]=_,t[4]=C);let{entityLabels:w}=(0,f.useLazyLoadQuery)(u,S,C),T;t[5]===h?T=t[6]:(T=h?void 0:()=>x(!0),t[5]=h,t[6]=T);let E;t[7]!==o||t[8]!==w||t[9]!==m||t[10]!==T?(E=(0,p.jsx)(c,{entityLabelsFrgmt:w,onEdit:T,editDisabledReason:o,onLabelClick:m}),t[7]=o,t[8]=w,t[9]=m,t[10]=T,t[11]=E):E=t[11];let D;t[12]!==r||t[13]!==w||t[14]!==n||t[15]!==b||t[16]!==i||t[17]!==h?(D=!h&&(0,p.jsx)(s,{open:b,entityType:n,targets:[{entityId:r,name:i}],entityLabelsFrgmt:w,onRequestClose:e=>{x(!1),e&&y(()=>{v(g)})}}),t[12]=r,t[13]=w,t[14]=n,t[15]=b,t[16]=i,t[17]=h,t[18]=D):D=t[18];let O;return t[19]!==E||t[20]!==D?(O=(0,p.jsxs)(p.Fragment,{children:[E,D]}),t[19]=E,t[20]=D,t[21]=O):O=t[21],O},h=e=>(0,p.jsx)(o,{fallback:(0,p.jsx)(p.Fragment,{children:`-`}),children:(0,p.jsx)(d.Suspense,{fallback:(0,p.jsx)(a,{variant:`input`,size:`small`}),children:(0,p.jsx)(m,{...e})})});function g(e){return e+1}export{h as t};
