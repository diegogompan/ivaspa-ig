# Puesta en marcha · IVASPA publicador automático de Instagram

Todo el contenido ya está preparado en este repositorio:
- `hosting_img/` — 2.460 imágenes optimizadas a 4:5 (1080×1350), listas para Instagram.
- `queue.json` — los 1.257 posts con su fecha, hora, texto e imágenes (20/08/2026 → 30/06/2027, 4/día).
- `publish.py` — el motor que publica por la API.
- `.github/workflows/publish.yml` — el automatismo que lo dispara cada hora en la nube (gratis).

Faltan **dos llaves** que solo puede crear Diego. Con ellas, esto publica solo durante ~10 meses.

---

## Llave 1 · GitHub (alojar las imágenes) — ya casi hecho
El repositorio debe ser **público** (para que Instagram pueda leer las imágenes por su URL).
Lo sube Claude tras el login de `gh`. La base de las imágenes queda:
`https://raw.githubusercontent.com/USUARIO/REPO/main/hosting_img`

---

## Llave 2 · Meta / Instagram (publicar por la API)

Requisitos que YA tienes: Instagram `@ivaspabombero` es cuenta **Profesional** y está **vinculada a una Página de Facebook**.

### Paso 1 · Crear la app en Meta
1. Entra en **developers.facebook.com** con tu Facebook y pulsa **Mis apps → Crear app**.
2. Tipo: **Empresa / Business**. Ponle nombre (ej. "IVASPA Publicador").
3. En el panel de la app, añade el producto **Instagram → Graph API** (o "Instagram" con inicio de sesión de Facebook).

### Paso 2 · Conseguir el ID de tu cuenta de Instagram
1. Ve a **Herramientas → Graph API Explorer**.
2. Arriba a la derecha, selecciona tu app y pulsa **Generate Access Token**. Acepta los permisos:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`.
3. En la barra, escribe `me/accounts` y **Submit** → apunta el `id` de tu Página de Facebook.
4. Escribe `TU_PAGE_ID?fields=instagram_business_account` y **Submit** →
   apunta el `id` que sale en `instagram_business_account`. **Ese es tu `IG_USER_ID`.**

### Paso 3 · Conseguir un token que NO caduque
1. En Graph API Explorer, con el token generado, ve a **developers.facebook.com/tools/debug/accesstoken**,
   pega el token y pulsa **Debug → Extend Access Token** (te da uno de larga duración, ~60 días).
2. Con ese token largo, en el Explorer pide `me/accounts?fields=access_token` → el `access_token` de tu
   **Página** que aparece ahí **no caduca** mientras no cambies la contraseña ni revoques la app.
   **Ese es tu `IG_ACCESS_TOKEN`.**

> Resumen: `IG_USER_ID` (paso 2) y `IG_ACCESS_TOKEN` = token de Página (paso 3).

### Paso 4 · Guardar las llaves en GitHub (Secrets)
En el repositorio de GitHub → **Settings → Secrets and variables → Actions → New repository secret**.
Crea estos tres:
| Nombre | Valor |
|---|---|
| `IG_ACCESS_TOKEN` | el token de Página del Paso 3 |
| `IG_USER_ID` | el ID de Instagram del Paso 2 |
| `IMG_BASE_URL` | `https://raw.githubusercontent.com/USUARIO/REPO/main/hosting_img` |

### Paso 5 · Encender
En el repo → pestaña **Actions** → habilita los workflows.
Para probar sin esperar: **Actions → publicar-instagram → Run workflow**. Debería publicar el primer post en cola.

A partir de ahí, cada hora comprueba si toca publicar (09:00 / 14:00 / 18:00 / 21:00 hora de Madrid) y lo hace solo.

---

## Cómo comprobar que va
- Pestaña **Actions**: cada ejecución dice "OK #n ID" si publicó, o "Nada pendiente".
- `queue.json`: cada post publicado pasa a `"status": "published"`. Si alguno falla, queda `"status": "error"` con el motivo.
- ¿Pausar? Desactiva el workflow en Actions. ¿Cambiar horas/orden? Se edita `queue.json`.

## Límites y notas
- La API permite hasta 25 publicaciones/día por cuenta; nosotros hacemos 4. Sin problema.
- Publica **1 post por ejecución** para respetar el espaciado del feed.
- Si algún día cambias la contraseña de Facebook o quitas la app, el token muere: se repite el Paso 3.
