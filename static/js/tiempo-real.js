// Refresca cada bloque marcado con data-refresco pidiendo al servidor su versión parcial (?parcial=1).
(function () {
  document.querySelectorAll("[data-refresco]").forEach(function (bloque) {
    var intervalo = parseInt(bloque.dataset.intervalo || "5000", 10);

    function refrescar() {
      if (document.hidden) return;
      var url = new URL(window.location.href);
      url.searchParams.set("parcial", "1");
      fetch(url, { credentials: "same-origin", headers: { "X-Requested-With": "fetch" } })
        .then(function (respuesta) {
          // Si la sesión expiró, el servidor redirige al login: no se inserta esa página.
          return respuesta.ok && !respuesta.redirected ? respuesta.text() : null;
        })
        .then(function (html) {
          if (html !== null && html !== bloque.innerHTML) bloque.innerHTML = html;
        })
        .catch(function () {});
    }

    setInterval(refrescar, intervalo);
  });
})();
