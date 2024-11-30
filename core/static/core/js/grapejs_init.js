document.addEventListener("DOMContentLoaded", function () {
    const editor = grapesjs.init({
      container: "#gjs",
      plugins: [],
      storageManager: {
        type: "remote",
      urlStore: "/grapejs_integration/save_grapejs_content/",
      // Add any other required storage configuration options
      },
    });
  });
  