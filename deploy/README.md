# Nasazení FilmDB (deployment)

Tahle složka přidává **nasazení aplikace na reálný server** — aplikace běží na
**https://vch.gawt.dtcloud.cz**. Navazuje na lekci o Dockeru: aplikaci zabalíme do
kontejnerů a pošleme ji na server přes **Ansible**, celé to spouští **GitHub Actions**
a provoz zvenčí na ni pouští **traefik** (reverzní proxy na serveru).

> Lokální vývoj se nemění — dál platí `./manage.py runserver` + `npm run dev`
> z hlavního [README](../README.md). Tady je řeč jen o produkci.

## Jak to vypadá na serveru

```
                       ┌──────────────────── server gawt.dtcloud.cz ───────────────────────┐
                       │  traefik  (HTTPS / Let's Encrypt, síť `proxy`)                    │
 návštěvník ──HTTPS──► │     │  Host(vch.gawt.dtcloud.cz)                                  │
                       │     ▼                                                             │
                       │  frontend (nginx)                                                 │
                       │    /app/     →  Vue SPA (build z frontend/)                       │
                       │    /static/  →  statika Djanga   (volume static_data)             │
                       │    /media/   →  média            (volume media_data)              │
                       │    /…        →  proxy ──► web (gunicorn :8000)   [síť `internal`] │
                       │                          Django: /, /movies, /admin, /api         │
                       │                          SQLite (volume db_data)                  │
                       └───────────────────────────────────────────────────────────────────┘
```

Dvě služby (viz [docker-compose.yml](docker-compose.yml)):

| služba | image | co dělá |
|--------|-------|---------|
| `web` | [../Dockerfile](../Dockerfile) | Django + gunicorn. Při startu pustí `migrate` a `collectstatic` (viz [web-entrypoint.sh](web-entrypoint.sh)). |
| `frontend` | [../frontend/Dockerfile](../frontend/Dockerfile) | nginx = vstupní brána. Postaví Vue SPA a servíruje statiku/média + proxuje na `web`. |

Dva frontendy nad stejným backendem koexistují tak, že **Django zůstává v kořeni**
(`/`, `/movies`, `/admin`, `/api`) a **Vue SPA se přesune pod `/app/`** (build s
`VITE_BASE=/app/`, router používá `import.meta.env.BASE_URL`). Rozcestník `/` na Vue
odkazuje přes `settings.VUE_FRONTEND_URL` (v produkci `/app/`, lokálně `:5173`).

## Konfigurace

- [inventory.ini](inventory.ini) — **verzovaný** seznam serverů. Uprav si tu
  `ansible_host` (kam) a `ansible_user` (jako kdo). `project_dir` je cesta na serveru,
  kam se rozbalí zdroják.
- [config/production.env](config/production.env) — **necitlivé** nastavení (doména
  `APP_HOST`, traefik entrypoint/certresolver, DEBUG, ALLOWED_HOSTS, cesty k datům).
  Commitnuté schválně.
- **Jediné tajemství** je SSH klíč v GitHub secrets jako `SSH_PRIVATE_KEY`
  (Settings → Secrets and variables → Actions). Veřejnou půlku klíče přidej do
  `~/.ssh/authorized_keys` uživatele `ansible_user` na serveru. Ten uživatel musí
  umět spouštět `docker`.

> ⚠️ Bezpečnost jsme tu **záměrně zjednodušili** (školní projekt): `SECRET_KEY` i
> ostatní nastavení jsou v gitu, ven jde jen SSH klíč přes secret. Pro ostrý provoz
> by tajemství patřila do secrets / vaultu, ne do repa.

## Nasazení přes GitHub Actions

Dva oddělené workflowy:

- **Deploy** ([.github/workflows/deploy.yml](../.github/workflows/deploy.yml)) — nasadí
  kód. Spustí se automaticky při pushi do `main`, nebo ručně (Actions → *Deploy* →
  *Run workflow*). Data v databázi zůstanou.
- **Seed database** ([.github/workflows/seed.yml](../.github/workflows/seed.yml)) — jen
  ručně. Znovu naplní databázi z fixtures (**POZOR: napřed ji vyprázdní**). Pro
  potvrzení se do pole *confirm* píše `SEED`, nebo přes CLI:
  `gh workflow run "Seed database" -f confirm=SEED`.

## Ruční nasazení (bez Actions)

Z této složky (potřebuješ SSH přístup na server + nainstalovaný Ansible):

```bash
pip install ansible-core
ansible-galaxy collection install community.docker

# nasazení (build + up)
ansible-playbook playbooks/deploy.yml

# naplnění daty — POZOR: napřed databázi vyprázdní (flush), pak nahraje fixtures
ansible-playbook playbooks/seed.yml
```

Co playbooky dělají:

- [playbooks/deploy.yml](playbooks/deploy.yml) — `git archive HEAD` zabalí commitnutý
  stav, pošle ho na server do `project_dir`, tam `docker compose up -d --build`.
  Migrace a collectstatic doběhnou z entrypointu kontejneru.
- [playbooks/seed.yml](playbooks/seed.yml) — `manage.py flush` + `loaddata
  /app/fixtures/*.yaml` uvnitř kontejneru `web` (fixtures jsou zabalené v image).

## Spustit celý stack přímo na serveru (debug)

```bash
cd /home/vasek/filmdb/deploy   # = project_dir z inventory.ini
docker compose --env-file config/production.env -f docker-compose.yml up -d --build
docker compose --env-file config/production.env -f docker-compose.yml logs -f web
```

## Předpoklady na serveru

- Nainstalovaný Docker + plugin `docker compose`.
- `ansible_user` smí používat docker a má v `authorized_keys` veřejný klíč k `SSH_PRIVATE_KEY`.
- Běžící **traefik** se sdílenou externí sítí **`proxy`** (entrypoint `websecure`,
  certresolver `letsencrypt` — názvy uprav v `production.env`, pokud má platforma jiné).
  Síť musí existovat předem: `docker network create proxy`.
- **DNS** pro `vch.gawt.dtcloud.cz` míří na server (aby traefik dostal Let's Encrypt cert).

## Jak nasazení probíhá (krok za krokem)

Od `git push` po běžící web — co dělá GitHub Actions a co docker compose:

```
  ┌─ tvůj počítač ─┐      ┌──────── GitHub Actions (runner) ──────────┐      ┌───── server gawt.dtcloud.cz ─────┐
  │  git push main │ ───► │  workflow „Deploy"                        │      │  docker compose up -d --build    │
  └────────────────┘      │   1. checkout repa                        │      │    ├─ build image web+frontend   │
                          │   2. instalace Ansible                    │ SSH  │    ├─ web: migrate+collectstatic │
                          │   3. SSH klíč ze secrets (SSH_PRIVATE_KEY)│ ───► │    └─ kontejnery běží            │
                          │   4. ansible-playbook deploy.yml          │      │  traefik → HTTPS pro doménu      │
                          └───────────────────────────────────────────┘      └──────────────────────────────────┘
```

1. **Push do `main`** (nebo ruční spuštění z Actions) nastartuje workflow
   [.github/workflows/deploy.yml](../.github/workflows/deploy.yml).
2. Runner si **checkoutne repo**, doinstaluje **Ansible** (`ansible-core` + kolekci
   `community.docker`) a z **GitHub secrets** vytáhne **SSH klíč** do souboru.
3. Spustí **`ansible-playbook playbooks/deploy.yml`**. Ansible se přes SSH připojí na
   server (uživatel + host z [inventory.ini](inventory.ini)) a:
   - `git archive HEAD` zabalí **commitnutý** stav (žádné `venv/`, `node_modules/`,
     `db.sqlite3`), pošle tarball na server a rozbalí ho do `project_dir`,
   - spustí na serveru **`docker compose up -d --build`**.
4. **docker compose** postaví dva image a spustí dva kontejnery:
   - **`web`** (Django + gunicorn) si při startu sám pustí `migrate` a `collectstatic`,
   - **`frontend`** (nginx) servíruje Vue SPA (`/app/`), statiku a média a zbytek
     proxuje na `web`.
5. **traefik** si všimne štítků na kontejneru `frontend`, vystaví pro
   `vch.gawt.dtcloud.cz` HTTPS certifikát (Let's Encrypt) a začne na nginx posílat
   provoz. Web je živý.

Celé je to **idempotentní**: další push znovu postaví image a přepne kontejnery na
novou verzi; data v databázi (volume `db_data`) zůstanou. Naplnění daty je zvlášť
(ruční *seed*, který databázi nejdřív vyprázdní).

> **Proč traefik a ne publikovaný port?** Na serveru běží sdílená reverzní proxy
> (traefik), která podle domény rozhoduje, kam request pošle, a řeší HTTPS pro všechny
> appky najednou. Náš `frontend` se proto nepřipojuje na hostitelský port, ale do
> sdílené sítě `proxy`, a routování si traefik přečte z `labels` v
> [docker-compose.yml](docker-compose.yml). TLS končí v traefiku; dovnitř jde HTTP +
> hlavička `X-Forwarded-Proto: https`, kterou Django respektuje (`SECURE_PROXY_SSL_HEADER`).
