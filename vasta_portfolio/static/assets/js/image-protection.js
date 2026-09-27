(function () {
  "use strict";

  function protectImage(image) {
    image.draggable = false;
    image.setAttribute("draggable", "false");
  }

  function protectImages(root) {
    if (root instanceof HTMLImageElement) {
      protectImage(root);
      return;
    }

    if (root.querySelectorAll) {
      root.querySelectorAll("img").forEach(protectImage);
    }
  }

  function eventTargetsImage(event) {
    return event.target instanceof Element && Boolean(event.target.closest("img"));
  }

  document.addEventListener("contextmenu", function (event) {
    if (eventTargetsImage(event)) {
      event.preventDefault();
    }
  });

  document.addEventListener("dragstart", function (event) {
    if (eventTargetsImage(event)) {
      event.preventDefault();
    }
  });

  document.addEventListener("copy", function (event) {
    if (eventTargetsImage(event)) {
      event.preventDefault();
      return;
    }

    var selection = window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
      return;
    }

    var range = selection.getRangeAt(0);
    var images = document.querySelectorAll("img");
    for (var index = 0; index < images.length; index += 1) {
      if (range.intersectsNode(images[index])) {
        event.preventDefault();
        return;
      }
    }
  });

  protectImages(document);

  new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeType === Node.ELEMENT_NODE) {
          protectImages(node);
        }
      });
    });
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
