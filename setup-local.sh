#!/usr/bin/env bash
# ============================================================================
# gbr-eval — Setup local completo
# ============================================================================
# Este script configura o ambiente completo do gbr-eval (backend + frontend)
# em uma maquina limpa. Ao final, voce tera:
#   - Framework Python rodando (533 testes passando)
#   - Frontend com banco SQLite populado (dashboard, golden sets, runs)
#   - Mesma visibilidade que o ambiente do Diogo
#
# Pre-requisitos:
#   - macOS ou Linux
#   - Git instalado
#   - Node.js >= 18 (recomendado: 20+)
#   - Python >= 3.12
#   - uv (https://docs.astral.sh/uv/getting-started/installation/)
#   - pnpm (npm install -g pnpm)
#
# Uso:
#   chmod +x setup-local.sh
#   ./setup-local.sh
# ============================================================================

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail()  { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

# ============================================================================
# 1. Verificar pre-requisitos
# ============================================================================
info "Verificando pre-requisitos..."

command -v git    >/dev/null 2>&1 || fail "Git nao encontrado. Instale: https://git-scm.com/"
command -v node   >/dev/null 2>&1 || fail "Node.js nao encontrado. Instale: https://nodejs.org/"
command -v pnpm   >/dev/null 2>&1 || fail "pnpm nao encontrado. Instale: npm install -g pnpm"
command -v uv     >/dev/null 2>&1 || fail "uv nao encontrado. Instale: curl -LsSf https://astral.sh/uv/install.sh | sh"
command -v python3 >/dev/null 2>&1 || fail "Python3 nao encontrado."

NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
  fail "Node.js >= 18 necessario (encontrado: $(node -v))"
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
  fail "Python >= 3.12 necessario (encontrado: $PYTHON_VERSION)"
fi

ok "Pre-requisitos: Git, Node $(node -v), Python $PYTHON_VERSION, uv, pnpm"

# ============================================================================
# 2. Clonar repositorios (se nao existirem)
# ============================================================================
WORK_DIR="${GBR_EVAL_DIR:-$(pwd)}"

info "Diretorio de trabalho: $WORK_DIR"

if [ ! -d "$WORK_DIR/gbr-eval" ]; then
  info "Clonando gbr-eval..."
  git clone https://github.com/diogodantasoliveira/gbr-eval.git "$WORK_DIR/gbr-eval"
  ok "gbr-eval clonado"
else
  warn "gbr-eval ja existe em $WORK_DIR/gbr-eval — pulando clone"
  cd "$WORK_DIR/gbr-eval" && git pull --ff-only 2>/dev/null || true
fi

if [ ! -d "$WORK_DIR/gbr-eval-frontend" ]; then
  info "Clonando gbr-eval-frontend..."
  git clone https://github.com/diogodantasoliveira/gbr-eval-frontend.git "$WORK_DIR/gbr-eval-frontend"
  ok "gbr-eval-frontend clonado"
else
  warn "gbr-eval-frontend ja existe em $WORK_DIR/gbr-eval-frontend — pulando clone"
  cd "$WORK_DIR/gbr-eval-frontend" && git pull --ff-only 2>/dev/null || true
fi

# ============================================================================
# 3. Setup do backend Python (gbr-eval)
# ============================================================================
info "Configurando gbr-eval (Python)..."
cd "$WORK_DIR/gbr-eval"

uv sync --all-extras
ok "Dependencias Python instaladas"

info "Rodando testes para validar instalacao..."
uv run pytest -q --tb=short 2>&1 | tail -5
ok "Testes do framework passando"

# ============================================================================
# 4. Setup do frontend (gbr-eval-frontend)
# ============================================================================
info "Configurando gbr-eval-frontend (Next.js)..."
cd "$WORK_DIR/gbr-eval-frontend"

pnpm install
ok "Dependencias Node instaladas"

# Criar .env.local para desenvolvimento
if [ ! -f .env.local ]; then
  cat > .env.local <<'ENVEOF'
# gbr-eval frontend — desenvolvimento local
DATABASE_URL=./gbr-eval.db
DISABLE_AUTH=true
ENVEOF
  ok "Criado .env.local (auth desabilitado para dev)"
else
  warn ".env.local ja existe — mantendo"
fi

# ============================================================================
# 5. Criar banco SQLite e popular com dados
# ============================================================================
info "Criando schema do banco SQLite..."
pnpm db:push 2>&1 | grep -v "^$" | head -5
ok "Schema criado (23 tabelas)"

info "Rodando seed (skills + fields)..."
pnpm db:seed 2>&1
ok "Seed completo (5 skills P0 + campos)"

# ============================================================================
# 6. Sincronizar dados do gbr-eval para o frontend
# ============================================================================
info "Iniciando frontend em background para sync..."
pnpm dev &
FRONTEND_PID=$!

# Esperar o servidor subir
info "Aguardando servidor (max 30s)..."
for i in $(seq 1 30); do
  if curl -s http://localhost:3002 >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -s http://localhost:3002 >/dev/null 2>&1; then
  kill $FRONTEND_PID 2>/dev/null || true
  fail "Frontend nao subiu em 30s. Verifique manualmente com: cd $WORK_DIR/gbr-eval-frontend && pnpm dev"
fi
ok "Frontend rodando em http://localhost:3002"

info "Sincronizando golden sets, tasks e runs..."
cd "$WORK_DIR/gbr-eval"
uv run python tools/sync_frontend.py --base-url http://localhost:3002 2>&1 | grep -E "(CREATE|IMPORT|imported|EXISTS|SYNC|OK)" | head -30
ok "Dados sincronizados com frontend"

# Parar o servidor de sync
kill $FRONTEND_PID 2>/dev/null || true
wait $FRONTEND_PID 2>/dev/null || true

# ============================================================================
# 7. Resumo final
# ============================================================================
echo ""
echo "============================================================================"
echo -e "${GREEN} SETUP COMPLETO${NC}"
echo "============================================================================"
echo ""
echo "  Backend (Python):"
echo "    cd $WORK_DIR/gbr-eval"
echo "    uv run pytest                    # rodar testes (533)"
echo "    uv run gbr-eval run --suite tasks/product/ --golden-dir golden/ --self-eval"
echo ""
echo "  Frontend (Next.js):"
echo "    cd $WORK_DIR/gbr-eval-frontend"
echo "    pnpm dev                         # http://localhost:3002"
echo ""
echo "  Dashboard: http://localhost:3002"
echo "  Golden Sets: http://localhost:3002/golden-sets"
echo "  Runs: http://localhost:3002/runs"
echo "  Tasks: http://localhost:3002/tasks"
echo "  Skills: http://localhost:3002/skills"
echo ""
echo "  Para re-sincronizar dados apos mudancas:"
echo "    cd $WORK_DIR/gbr-eval"
echo "    uv run python tools/sync_frontend.py"
echo ""
echo "============================================================================"
