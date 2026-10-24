<p align="center">
  <img src="../../images/hindsight-logo.png" alt="Hindsight" width="140">
</p>

<h1 align="center">Tienda de plugins de Hindsight</h1>

<p align="center">
  Explora plugins, crea el tuyo y envía una nueva versión a la tienda.
</p>

<p align="center">
  <a href="../zh/README.md">简体中文</a> · <a href="../zh-TW/README.md">繁體中文</a> · <a href="../../../README.md">English</a> · <a href="../ja/README.md">日本語</a> · <a href="../pt/README.md">Português</a> · <a href="README.md">Español</a>
</p>

<p align="center">
  <a href="https://github.com/Tomotsugu-dev/Hindsight/releases"><img alt="Última versión de Hindsight" src="https://img.shields.io/github/v/release/Tomotsugu-dev/Hindsight?color=blue&amp;logo=github"></a>
  <a href="../../../LICENSE"><img alt="Licencia MIT" src="https://img.shields.io/badge/license-MIT-green"></a>
</p>

<p align="center">
  <a href="#plugins">Ver plugins</a> · <a href="#crear-un-plugin">Crear un plugin</a> · <a href="#publicar-un-plugin">Publicar un plugin</a>
</p>

---

La lista de plugins de la tienda de plugins de [Hindsight](https://github.com/Tomotsugu-dev/Hindsight). Cada vez que el usuario abre Ajustes → Plugins, Hindsight lee [plugins.json](../../../plugins.json) y los iconos de [icons/](../../../icons/) desde la rama `main` de este repositorio. GitHub guarda estos archivos en caché hasta 5 minutos, así que un cambio publicado puede tardar ese tiempo en aparecer.

## Plugins

| Icono | Plugin | Qué hace | Código |
|---|---|---|---|
| <img src="../../../icons/hindsight-focus.png" alt="" width="28"> | Focus | Cronometra tu trabajo a tu ritmo, te avisa cuando te distraes y funciona con la isla | [Tomotsugu-dev/hindsight-focus](https://github.com/Tomotsugu-dev/hindsight-focus) |

## Crear un plugin

La documentación para desarrolladores está disponible en [inglés](../../en/getting-started.md) y [chino simplificado](../../zh/getting-started.md):

- [Primeros pasos](../../en/getting-started.md): crea un plugin pequeño e instálalo desde un zip
- [Referencia de la API](../../en/api.md): campos del manifest, métodos, eventos y límites
- [Permisos](../../en/permissions.md): qué permite cada permiso, con cuál debe pedirse y qué ve el usuario al instalar
- [La isla](../../en/island.md): qué puede mostrar un plugin en la isla de la barra de menús de macOS, con una página por componente

Los plugins necesitan Hindsight 0.10.0 o posterior.

## Publicar un plugin

Los plugins y sus nuevas versiones se publican mediante pull request. Los pasos, los campos de `plugins.json` y lo que se revisa están en [CONTRIBUTING.md](../../../CONTRIBUTING.md) (en inglés).

## Plugins de terceros

Cualquiera puede enviar un plugin mediante pull request. Cada plugin se revisa antes de publicarse. Un plugin cuyo repositorio no está bajo `Tomotsugu-dev` es un plugin de terceros: antes de instalarlo, se avisa al usuario de que no es oficial y de que podría filtrar información personal.

<h2 align="center">Licencia</h2>

<p align="center">
  La lista de plugins de este repositorio se publica bajo la <a href="../../../LICENSE">Licencia MIT</a>.<br/>
  Cada plugin se distribuye bajo la licencia de su propio repositorio.
</p>
