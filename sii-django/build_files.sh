#!/bin/bash
# Genera STATIC_ROOT para Vercel (@vercel/static-build) y para CI.
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || PYTHON=python

echo "collectstatic: usando $PYTHON"
"$PYTHON" -m pip install --disable-pip-version-check -q -r requirements.txt
export COLLECTSTATIC=1
echo "collectstatic: copiando css/js/img a staticfiles/"
if ! "$PYTHON" manage.py collectstatic --noinput; then
  echo "collectstatic falló; se publican los staticfiles ya versionados"
  test -f staticfiles/img/logo.png
  test -f staticfiles/css/main.css
fi
echo "collectstatic: listo"
ls -la staticfiles/img staticfiles/js staticfiles/css
