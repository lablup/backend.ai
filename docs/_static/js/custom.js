function addHeader() {
  const headerWrapper = document.createElement('div');

  const link = document.createElement('a');
  link.href = 'https://backend.ai';
  link.className = 'backend-ai-link';

  const logoWrapper = document.createElement('div');
  logoWrapper.className = 'backend-ai-logo';

  const logo = document.createElement('img');

  logoWrapper.append(logo);
  
  link.append(logoWrapper);

  headerWrapper.append(link);

  headerWrapper.id = 'backend-ai-header';

  const referenceNode = document.querySelector('.wy-grid-for-nav');

  referenceNode.prepend(headerWrapper);
}

function addSearchElementInDocument() {

  const element = document.getElementById('rtd-search-form');

  element.setAttribute('className', 'custom-rtd-search-form');

  const searchDiv = document.createElement('div');

  const input = element.querySelector('[name="q"]');

  input.placeholder = 'Search';

  searchDiv.className = 'customized-search-bar';

  searchDiv.append(element);

  const imageWrapper = document.createElement('div');
  imageWrapper.id = 'search-icon-wrapper';

  const imageTag = document.createElement('img');
  imageTag.className = 'search-icon';
  imageTag.alt = '';

  imageWrapper.append(imageTag);

  searchDiv.append(imageWrapper);

  const referenceNode = document.querySelector('.rst-content');
  
  referenceNode.prepend(searchDiv);

  const newSearchForm = element.cloneNode(true);

  newSearchForm.id = 'rtd-search-form-desktop';
  
  const searchDivInDesktop = document.createElement('div');

  searchDivInDesktop.className = 'customized-search-bar-in-desktop';

  searchDivInDesktop.append(newSearchForm);

  const imageWrapperInDesktopSearchForm = document.createElement('div');
  imageWrapperInDesktopSearchForm.id = 'search-icon-wrapper-in-desktop';

  const imageTagInDesktop = document.createElement('img');
  imageTagInDesktop.className = 'search-icon';
  imageTagInDesktop.alt = '';

  imageWrapperInDesktopSearchForm.append(imageTagInDesktop);

  searchDivInDesktop.append(imageWrapperInDesktopSearchForm);

  const bar = document.querySelector('[aria-label="Mobile navigation menu"]');

  bar.append(searchDivInDesktop);
}

function changeNavigationTitle() {
  const navigationElement = document.querySelector('.wy-nav-top');

  const linkElement = navigationElement.getElementsByTagName('a');

  linkElement[0].textContent = 'Documentation';
}

function addDimmedLayer() {
  const dimmedLayer = document.createElement('div');

  dimmedLayer.id = 'dimmed-layer';

  const referenceNode = document.querySelector('.wy-nav-content');

  referenceNode.prepend(dimmedLayer);
}

function addSnsLinks() {
  const urls = [
    'https://www.facebook.com/lablupInc',
    'https://www.youtube.com/c/lablupinc',
    'https://linkedin.com/company/lablup',
    'https://github.com/lablup'
  ];

  const wrapper = document.createElement('div');

  wrapper.id = 'sns-section';

  urls.forEach((url) => {
    const linkElement = document.createElement('a');

    linkElement.href = url;
    linkElement.target = '_blank';

    const imageWrapper = document.createElement('div');

    const imageTag = document.createElement('img');

    imageTag.className = 'sns-logo';

    imageWrapper.append(imageTag);

    linkElement.append(imageWrapper);

    wrapper.append(linkElement);
  })

  const referenceNode = document.querySelector('[role=contentinfo]');

  referenceNode.prepend(wrapper);
}

function getCurrentPageTitle() {
  const titleBar = document.querySelector(".wy-nav-top");

  const link = titleBar.getElementsByTagName('a')

  const elementToChange = link[0];

  elementToChange.href = "#";

  const breadcrumbs = document.querySelector('.wy-breadcrumbs');
  
  const breadcrumbItems = breadcrumbs.querySelectorAll('.breadcrumb-item');

  const root = breadcrumbItems[0];

  if (breadcrumbItems.length > 1) {

    const link = root.getElementsByTagName('*');

    const text = link[0].textContent;

    elementToChange.textContent = text;

    return;
  }

  elementToChange.textContent = root.textContent;
}

function moveFooterButtons() {
  const newButtonWrapper = document.createElement('div');

  newButtonWrapper.id = 'customized-rst-footer-buttons';

  const buttons = document.querySelector('.rst-footer-buttons');

  const next = buttons.querySelector('[rel=next]');

  const prev = buttons.querySelector('[rel=prev]');

  if (next && prev) {
    newButtonWrapper.append(buttons);

    const referenceNode = document.querySelector('[itemtype="http://schema.org/Article"]');
  
    referenceNode.insertAdjacentElement("afterend", newButtonWrapper);

    return;
  }

  if (prev) {
    const emptyDiv = document.createElement('div');
    
    emptyDiv.className = 'empty-right-div';

    buttons.append(emptyDiv);

    newButtonWrapper.append(buttons);

    const referenceNode = document.querySelector('[itemtype="http://schema.org/Article"]');
  
    referenceNode.insertAdjacentElement("afterend", newButtonWrapper);

    return;
  }

  if (next) {
    const emptyDiv = document.createElement('div');
    
    emptyDiv.className = 'empty-left-div';

    buttons.prepend(emptyDiv);

    newButtonWrapper.append(buttons);

    const referenceNode = document.querySelector('[itemtype="http://schema.org/Article"]');
  
    referenceNode.insertAdjacentElement("afterend", newButtonWrapper);

    return;
  }
  return;
}

// RTD 위치 테스트 용 div
function defineFlyoutMenu() {
  const readTheDocsDiv = document.createElement('div');

  readTheDocsDiv.className = 'rst-versions shift';

  const flyoutMenuSpan = document.createElement('span');

  flyoutMenuSpan.className = 'rst-current-version';

  const flyoutMenuDiv = document.createElement('div');

  flyoutMenuDiv.className = 'rst-other-versions';

  readTheDocsDiv.append(flyoutMenuSpan);

  readTheDocsDiv.append(flyoutMenuDiv);

  const referenceNode = document.querySelector('.wy-grid-for-nav');

  referenceNode.insertAdjacentElement("afterend", readTheDocsDiv);
}

window.onload = function() {
  addHeader();
  addSearchElementInDocument();
  changeNavigationTitle();
  addDimmedLayer();
  addSnsLinks();
  moveFooterButtons();
  getCurrentPageTitle();
  // defineFlyoutMenu();
}
