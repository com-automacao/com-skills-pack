# com-skills-pack

Pacote de **skills de desenvolvimento e programação** para o Claude Code, mantido pela Com Automação.

Cada skill é copiada do repositório original e **atualizada sozinha todo dia**. Quando uma origem muda de um jeito fora do padrão (script novo, licença trocada, texto suspeito), o robô **não aplica a mudança** e abre um alerta para revisão.

- [Situação de cada origem](STATUS.md): commit atual, data e estado.
- [Créditos e licenças](THIRD_PARTY_NOTICES.md)
- [Manifesto das origens](sources.yaml)

---

## Instalar

Pré-requisito: Python 3.

```bash
git clone https://github.com/com-automacao/com-skills-pack
cd com-skills-pack
python scripts/install.py --dry-run   # mostra o que seria instalado
python scripts/install.py             # instala em ~/.claude/skills
```

- Skills que você já tem **não são sobrescritas**. Use `--force` para trocar (o instalador guarda backup).
- Depois de instalar, reinicie o Claude Code.
- As skills de **plugins** (engineering, data, design, base44, ruflo, scroll-craft) ficam no pack como cópia de referência. Para usar, instale o plugin oficial: veja a coluna "Como instalar" no catálogo.

---

## Como o pack se mantém atualizado

Todo dia às 08:17 (Brasília), o GitHub Actions roda [`scripts/sync.py`](scripts/sync.py):

1. Baixa só as pastas das skills de cada repositório listado em [`sources.yaml`](sources.yaml).
2. Compara com a versão anterior, arquivo por arquivo.
3. Classifica o que mudou:

| Nível | O que acontece | Exemplos |
|---|---|---|
| 🟢 Normal | Atualiza o `main` sozinho | Texto da skill melhorado, exemplo novo |
| 🟡 Aviso | Atualiza o `main` **e** abre uma issue | Script existente alterado, instalação automática de pacote (`npx -y`), endereço externo novo, skill reescrita quase do zero, repositório arquivado |
| 🔴 Bloqueio | **Não** atualiza o `main`. Deixa a versão nova no branch `sync/pendente` e abre uma issue | Script ou executável novo, binário desconhecido, licença trocada, repositório renomeado ou apagado, histórico reescrito (force-push), skill renomeada ou removida, remoção em massa de arquivos, `curl … \| bash`, `Invoke-Expression`, código em base64, `rm -rf`, mudança em permissões do Claude Code, texto que tenta manipular o agente ("ignore previous instructions"), caracteres invisíveis, chaves e tokens embutidos |

**Ao receber um alerta 🔴:** abra o link `sync/pendente` da issue e confira as mudanças.
- Para **aceitar**, clique em *Create pull request* e faça o merge.
- Para **recusar**, feche a issue. O `main` continua na versão anterior.

Se o GitHub estiver instável (sem conexão, limite de uso, erro do servidor), a origem é adiada para o próximo sync, sem alerta. O mesmo alerta não é aberto duas vezes. Para rodar fora do horário: aba **Actions** → *Sincronizar skills* → *Run workflow*.

### Rodar na sua máquina

```bash
pip install pyyaml
python scripts/sync.py --dry-run          # só relata
python scripts/sync.py                    # aplica o que é seguro
python scripts/sync.py --only gsap-skills # uma origem só
```

### Testes do sincronizador

```bash
pip install pytest pyyaml
python -m pytest tests -q
```

Os testes usam uma origem falsa, sem rede nem git, e cobrem cada regra de detecção.

### Adicionar uma skill

Acrescente o caminho em `paths` da origem certa em `sources.yaml` (ou crie uma origem nova) e rode o sync. Ajustes próprios em cima de uma skill de terceiros ficam em `overrides` no mesmo arquivo. Hoje existe um: a descrição do `frontend-ui-engineering`, que dá prioridade ao genjutsu em trabalho visual.

---

## Catálogo

Coluna **Pasta**: onde a skill está dentro de `packs/`.

### 1. Fluxo de desenvolvimento (da ideia ao código)

Origem: [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT). Pasta: `agent-skills/skills/`.

| Skill | O que faz |
|---|---|
| `interview-me` | Faz uma pergunta por vez até entender o que você realmente quer construir, antes de qualquer plano ou código. |
| `idea-refine` | Refina uma ideia crua com pensamento divergente e convergente; testa premissas antes de virar plano. |
| `spec-driven-development` | Escreve a especificação (ou PRD) antes de codar. Para projetos novos ou requisitos ambíguos. |
| `planning-and-task-breakdown` | Quebra uma especificação em tarefas ordenadas e implementáveis. |
| `incremental-implementation` | Entrega mudanças em fatias finas e verificáveis em vez de um bloco gigante de código. |
| `test-driven-development` | Ciclo vermelho-verde-refatora: escreve o teste que falha, depois o código que passa. |
| `source-driven-development` | Baseia cada decisão de código na documentação oficial, com fontes citadas. |
| `doubt-driven-development` | Submete cada decisão importante a uma revisão adversária com contexto limpo. Para código crítico. |
| `context-engineering` | Organiza o contexto do agente: arquivos de regras (CLAUDE.md), troca de tarefa, queda de qualidade. |
| `documentation-and-adrs` | Registra decisões de arquitetura (ADRs) e documentação para quem vier depois. |
| `git-workflow-and-versioning` | Commits, branches, conflitos, versionamento semântico, changelog e releases. |

### 2. Qualidade, revisão e depuração

| Skill | Pasta | O que faz |
|---|---|---|
| `code-review-and-quality` | `agent-skills/skills/` | Revisão em vários eixos (correção, legibilidade, segurança, performance) antes do merge. |
| `code-simplification` | `agent-skills/skills/` | Refatora para clareza sem mudar o comportamento. |
| `debugging-and-error-recovery` | `agent-skills/skills/` | Depuração sistemática pela causa raiz quando testes falham ou o build quebra. |
| `deprecation-and-migration` | `agent-skills/skills/` | Planeja a remoção de sistemas/APIs antigos e a migração para a versão nova. |
| `improve-codebase-architecture` | `mattpocock-skills/skills/engineering/` | Varre o código atrás de melhorias estruturais, gera relatório HTML e aprofunda a que você escolher. ([mattpocock/skills](https://github.com/mattpocock/skills), MIT) |

### 3. Arquitetura, segurança, performance e produção

Origem: [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills). Pasta: `agent-skills/skills/`.

| Skill | O que faz |
|---|---|
| `api-and-interface-design` | APIs e interfaces estáveis: REST/GraphQL, contratos de tipos, fronteiras entre módulos e entre front e back. |
| `security-and-hardening` | Protege contra vulnerabilidades: entrada do usuário, autenticação, armazenamento, integrações. |
| `performance-optimization` | Otimiza front, back, queries e banco; Core Web Vitals, consultas N+1, gargalos. |
| `observability-and-instrumentation` | Logs, métricas, tracing e alertas para o comportamento em produção ficar visível. |
| `ci-cd-and-automation` | Pipelines de build e deploy, portões de qualidade, testes no CI. |
| `shipping-and-launch` | Lançamento em produção: checklist, monitoramento, rollout gradual e rollback. |
| `browser-testing-with-devtools` | Testa no navegador real via Chrome DevTools MCP: DOM, console, rede, performance. |

### 4. Front-end, interface e motion

| Skill | Pasta | O que faz |
|---|---|---|
| `frontend-ui-engineering` | `agent-skills/skills/` | Acessibilidade (WCAG), responsividade, HTML semântico e estado. *Ajustada neste pack* para rodar depois do genjutsu. |
| `paint` | `genjutsu/skills/` | Cria um universo visual completo: direção de arte, design system, implementação e auditoria. Anti "cara de IA". |
| `cast` | `genjutsu/skills/` | Aplica motion, micro-interações e efeito "uau" numa interface existente. |
| `bunshin` | `genjutsu/skills/` | Pipeline completo para um site ou app inteiro, do zero ou redesign, com vários agentes. |
| `_jutsu/*` | `genjutsu/skills/_jutsu/` | 17 módulos internos que as três acima carregam: CSS nativo, Framer Motion, GSAP, Three.js/R3F, Compose, SwiftUI, princípios mobile e desktop, auditoria. |
| `motion-design` | `motion-design/skills/` | Princípios de motion: tempo, easing, coreografia e os princípios da Disney aplicados a UI. ([LottieFiles](https://github.com/LottieFiles/motion-design-skill), MIT) |
| `design-dna` | `design-dna/` | Extrai de prints ou URLs um perfil JSON com tokens, estilo e efeitos, e gera designs a partir dele. ([zanwei/design-dna](https://github.com/zanwei/design-dna), MIT) |

Origem do genjutsu: [AThevon/genjutsu](https://github.com/AThevon/genjutsu) (MIT). **Atenção:** a skill única `genjutsu` foi dividida pelo autor em `paint`, `cast` e `bunshin`. Quem tem a versão antiga instalada deve trocá-la pelas três.

### 5. Animação com GSAP (oficiais)

Origem: [greensock/gsap-skills](https://github.com/greensock/gsap-skills) (MIT). Pasta: `gsap-skills/skills/`.

| Skill | O que faz |
|---|---|
| `gsap-core` | API principal: `to/from/fromTo`, easing, stagger, `matchMedia` (responsivo e movimento reduzido). |
| `gsap-timeline` | Sequenciar animações, parâmetro de posição, aninhamento. |
| `gsap-scrolltrigger` | Animação ligada à rolagem: pinning, scrub, parallax. |
| `gsap-plugins` | Flip, Draggable, SplitText, ScrollSmoother, SVG, CustomEase e outros. |
| `gsap-react` | GSAP em React/Next.js: `useGSAP`, refs, limpeza ao desmontar. |
| `gsap-frameworks` | GSAP em Vue, Nuxt, Svelte e SvelteKit. |
| `gsap-performance` | 60 fps: transforms, evitar layout thrashing, `will-change`. |
| `gsap-utils` | `clamp`, `mapRange`, `snap`, `wrap`, `random`, `toArray`. |

### 6. 3D

Origem das `threejs-*`: [CloudAI-X/threejs-skills](https://github.com/CloudAI-X/threejs-skills) (MIT desde 18/10/2026; antes não tinha licença e ficava só como link).

| Skill | Pasta | O que faz |
|---|---|---|
| `img2threejs` | `img2threejs/` | Transforma uma imagem de referência em modelo 3D procedural em código Three.js, pronto para animar. ([img2threejs/img2threejs](https://github.com/img2threejs/img2threejs), Apache-2.0) |
| `threejs-fundamentals` | `threejs-skills/skills/` | Cena, câmeras, renderer, hierarquia de objetos e coordenadas. |
| `threejs-geometry` | `threejs-skills/skills/` | Formas prontas, BufferGeometry, geometria customizada e instancing. |
| `threejs-materials` | `threejs-skills/skills/` | Materiais PBR, basic, phong e de shader. |
| `threejs-textures` | `threejs-skills/skills/` | Texturas, mapeamento UV, environment maps e HDR. |
| `threejs-lighting` | `threejs-skills/skills/` | Luzes, sombras e iluminação por ambiente (IBL). |
| `threejs-loaders` | `threejs-skills/skills/` | Carregar GLTF, texturas e HDR, com progresso. |
| `threejs-animation` | `threejs-skills/skills/` | Keyframes, esqueleto, morph targets e mixer. |
| `threejs-interaction` | `threejs-skills/skills/` | Raycasting, controles de câmera, clique e toque em objetos. |
| `threejs-shaders` | `threejs-skills/skills/` | GLSL, ShaderMaterial, uniforms e efeitos customizados. |
| `threejs-postprocessing` | `threejs-skills/skills/` | EffectComposer: bloom, profundidade de campo, efeitos de tela. |
| `threejs-performance` | `threejs-skills/skills/` | **Nova.** Mede e otimiza a velocidade: estatísticas de render, memória, menos draw calls (merge, instancing, LOD), sombras e shaders. |
| `threejs-asset-pipeline` | `threejs-skills/skills/` | **Nova.** Comprime modelos glTF com gltf-transform: Draco, meshopt e texturas KTX2/WebP/AVIF. |
| `threejs-react-three-fiber` | `threejs-skills/skills/` | **Nova.** Cenas Three.js em React com React Three Fiber e drei. |

### 7. Dados e SQL (plugin `data`)

Origem: [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) (Apache-2.0). Pasta: `knowledge-work-plugins/data/skills/`. Como instalar: `/plugin install data@knowledge-work-plugins`.

| Skill | O que faz |
|---|---|
| `sql-queries` | SQL correto e performático em Snowflake, BigQuery, Databricks, PostgreSQL etc. |
| `write-query` | Traduz uma pergunta em linguagem natural para SQL otimizado no dialeto certo. |
| `explore-data` | Perfil de uma tabela ou arquivo: nulos, distribuições, qualidade, padrões. |
| `create-viz` | Gráficos de qualidade de publicação em Python a partir de uma query ou DataFrame. |
| `data-visualization` | matplotlib, seaborn e plotly; escolha do tipo de gráfico certo. |
| `build-dashboard` | Dashboard HTML interativo com KPIs, gráficos, filtros e tabelas. |

### 8. Engenharia, design e produto (plugins oficiais)

Origem: [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) (Apache-2.0). Como instalar: `/plugin install <plugin>@knowledge-work-plugins`.

| Skill | Plugin | O que faz |
|---|---|---|
| `architecture` | engineering | Cria ou avalia um ADR comparando tecnologias, com prós e contras. |
| `system-design` | engineering | Desenha sistemas, serviços e arquiteturas a partir de requisitos. |
| `code-review` | engineering | Revisão de mudanças com foco em segurança, performance e correção. |
| `debug` | engineering | Debug estruturado: reproduzir, isolar, diagnosticar, corrigir. |
| `tech-debt` | engineering | Identifica, classifica e prioriza dívida técnica. |
| `testing-strategy` | engineering | Estratégia e plano de testes. |
| `documentation` | engineering | README, runbooks, guias de onboarding. |
| `deploy-checklist` | engineering | Checklist pré-deploy: migrações, feature flags, CI. |
| `incident-response` | engineering | Triagem, comunicação e postmortem de incidentes. |
| `standup` | engineering | Resumo do standup a partir de commits, PRs e tickets. |
| `accessibility-review` | design | Auditoria WCAG 2.1 AA de uma tela ou página. |
| `design-handoff` | design | Especificação para desenvolvedores: layout, tokens, props, interações. |
| `design-system` | design | Audita, documenta ou estende um design system. |
| `write-spec` | product-management | Transforma uma ideia em PRD / especificação estruturada. |

### 9. Plataformas e SDKs

| Skill | Pasta | O que faz |
|---|---|---|
| `base44-cli` | `base44/skills/` | CLI do Base44: entidades, funções de backend, agentes de IA, deploy. |
| `base44-sdk` | `base44/skills/` | SDK para falar com entidades, funções e agentes do Base44. |
| `base44-sandbox` | `base44/skills/` | Desenvolve um app Base44 dentro do sandbox na nuvem, sem checkout local. |
| `base44-remote-dev` | `base44/skills/` | Conecta seu agente ao sandbox Base44 para desenvolver remotamente. |
| `base44-troubleshooter` | `base44/skills/` | Investiga erros de produção pelos logs das funções e workflows. |
| `codeigniter` | `codeigniter-skills/skills/` | CodeIgniter 3 e 4: controllers, models, rotas, banco, migrações. |

Origens: [base44/skills](https://github.com/base44/skills) (MIT; como instalar: `/plugin marketplace add base44/skills` e depois `/plugin install base44@base44-skills`), [yasserstudio/codeigniter-skills](https://github.com/yasserstudio/codeigniter-skills) (MIT).

### 10. Construir ferramentas para IA

| Skill | Pasta | O que faz |
|---|---|---|
| `mcp-builder` | `anthropic-skills/skills/` | Guia para criar servidores MCP (conectar LLMs a serviços externos). |
| `skill-creator` | `anthropic-skills/skills/` | Cria, edita e mede o desempenho de skills, com avaliações. |
| `find-skills` | `find-skills/skills/` | Procura e instala skills prontas quando você pergunta "tem skill para X?". |

Origens: [anthropics/skills](https://github.com/anthropics/skills) (Apache-2.0 por skill), [vercel-labs/skills](https://github.com/vercel-labs/skills) (MIT).

### 11. Publicação de sites

| Skill | Pasta | O que faz |
|---|---|---|
| `checklist-publicacao-site` | `com-automacao/skills/` | Portão objetivo de 20 itens antes de publicar: SEO, formulários, WhatsApp, PageSpeed, LGPD/CNPJ, HTTPS, cabeçalhos de segurança. Verifica no código e no navegador. **Skill própria da Com Automação.** |
| `scroll-craft` | `scroll-craft/plugins/nateherk-design/skills/` | Landing pages premium guiadas por rolagem, com padrão de qualidade e verificação. Como instalar: `/plugin marketplace add nateherkai/scroll-craft`. ([nateherkai/scroll-craft](https://github.com/nateherkai/scroll-craft), MIT) |

### 12. Memória de longo prazo (ai-memory)

Origem: [akitaonrails/ai-memory](https://github.com/akitaonrails/ai-memory) (MIT). Pasta: `ai-memory/crates/ai-memory-core/src/routing_skills/`. Essas skills são instaladas pelo próprio programa: `ai-memory install-skills --scope global`.

| Skill | O que faz |
|---|---|
| `ai-memory-retrieval` | Busca histórico, decisões e contexto anterior do projeto. |
| `ai-memory-handoff` | Passa o bastão entre sessões e agentes: retomar trabalho, salvar contexto. |
| `ai-memory-durable-pages` | Grava, atualiza ou apaga conhecimento permanente na wiki. |
| `ai-memory-learning-maintenance` | Consolida observações, revisa lições e limpa memória velha. |
| `ai-memory-messaging` | Mensagens entre agentes de projetos diferentes. |
| `ai-memory-routing-install` | Instala ou repara as instruções e skills do ai-memory. |

### 13. Orquestração multiagente (Ruflo, antigo Claude Flow)

Origem: [ruvnet/ruflo](https://github.com/ruvnet/ruflo) (MIT; o repositório se chamava `claude-flow`). Pasta: `ruflo/`. Como instalar: `npx ruflo@latest init` no projeto, ou os plugins `ruflo-core` e `ruflo-swarm`.

Só vale a pena em tarefas grandes, com 3 ou mais agentes.

| Grupo | Skills | O que fazem |
|---|---|---|
| Núcleo | `swarm-orchestration`, `swarm-advanced`, `sparc-methodology`, `pair-programming`, `verification-quality`, `hooks-automation`, `stream-chain`, `browser`, `skill-builder` | Enxames de agentes em paralelo, metodologia SPARC, programação em par, verificação com nota de qualidade, hooks e pipelines. |
| GitHub | `github-code-review`, `github-workflow-automation`, `github-release-management`, `github-project-management`, `github-multi-repo` | Revisão de PR, Actions, releases, issues e vários repositórios com agentes. |
| Memória | `agentdb-memory-patterns`, `agentdb-vector-search`, `agentdb-optimization`, `agentdb-learning`, `agentdb-advanced`, `reasoningbank-intelligence`, `reasoningbank-agentdb` | Memória persistente, busca vetorial (RAG) e aprendizado por reforço para agentes. |
| Nuvem | `flow-nexus-platform`, `flow-nexus-swarm`, `flow-nexus-neural` | Sandboxes, enxames e redes neurais na plataforma Flow Nexus. |
| Interno v3 | `v3-*` (9) | Desenvolvimento do próprio Ruflo, não dos seus projetos. |
| Plugins | `init-project`, `ruflo-doctor`, `ruflo-status`, `discover-plugins`, `witness`, `swarm-init`, `monitor-stream` | Instalar, diagnosticar e monitorar o Ruflo. |
| Comandos | `.claude/commands/` (~168) | Atalhos `/sparc:*`, `/swarm:*`, `/github:*`, `/hive-mind:*` e outros. |

### 14. Engenharia reversa (REA)

Origem: [morluto/rea](https://github.com/morluto/rea) (MIT). Pasta: `rea/.agents/skills/`. A skill depende do servidor MCP do REA; instale pelo programa oficial: `npm install --global rea-agents` e depois `rea setup --client claude_code`. Para atualizar: `rea update`.

| Skill | O que faz |
|---|---|
| `reverse-engineer-anything` | Investiga como um programa funciona sem o código-fonte: apps JavaScript/Electron, .NET, sites, binários nativos e firmware. Explica a funcionalidade com evidências, compara versões e guia uma reconstrução no seu projeto. Binários nativos exigem Ghidra, IDA ou Hopper instalados. Uso apenas em software próprio, autorizado ou para pesquisa, educação e interoperabilidade. |

### 15. Superpowers (fluxo de trabalho com agentes)

Origem: [obra/superpowers](https://github.com/obra/superpowers) (MIT). Pasta: `superpowers/skills/`. Como instalar: `/plugin install superpowers@claude-plugins-official`.

**Atenção:** o plugin tem um hook que roda no início de toda sessão e orienta o agente a preferir estas skills. O sync acompanha a pasta `hooks/`: qualquer mudança nela gera aviso ou bloqueio. Várias skills se sobrepõem às da seção 1 (TDD, debug, revisão, planejamento).

| Skill | O que faz |
|---|---|
| `brainstorming` | Explora a ideia com perguntas antes de qualquer código e fecha um design aprovado. |
| `writing-plans` | Transforma o design em um plano de implementação passo a passo. |
| `executing-plans` | Executa um plano em lotes, com pontos de revisão. |
| `subagent-driven-development` | Executa o plano despachando um subagente por tarefa, com revisão entre elas. |
| `dispatching-parallel-agents` | Divide problemas independentes entre agentes em paralelo. |
| `test-driven-development` | TDD estrito: teste que falha primeiro, sempre. |
| `systematic-debugging` | Depuração em 4 fases, pela causa raiz. |
| `verification-before-completion` | Exige prova (comando rodado, saída vista) antes de dizer que terminou. |
| `requesting-code-review` / `receiving-code-review` | Pedir revisão e responder a ela com rigor técnico, sem concordar por educação. |
| `using-git-worktrees` | Isola o trabalho em worktrees do git. |
| `finishing-a-development-branch` | Fecha o branch: testes, opções de merge ou PR, limpeza. |
| `writing-skills` | Cria e testa skills novas. |
| `using-superpowers` / `diagnosing-superpowers` | Como o plugin escolhe as skills, e diagnóstico quando algo não carrega. |

### 16. Context7 (documentação atualizada)

Origem: [upstash/context7](https://github.com/upstash/context7) (MIT). Pasta: `context7/plugins/claude/context7/`. Como instalar: `/plugin install context7@claude-plugins-official`.

| Item | O que faz |
|---|---|
| MCP `context7` | Busca a documentação atual da versão certa de uma biblioteca no momento de programar, em vez de confiar no que o modelo lembra. Funciona sem conta (limite compartilhado); para limite próprio e gratuito, rode `npx ctx7 setup --claude` e confirme o login no navegador. |

O sync acompanha o `.mcp.json`: se o endereço do servidor mudar, gera aviso.

### 17. CAD e fabricação (text-to-cad)

Origem: [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad) (MIT), branch `latest`. Pasta: `text-to-cad/skills/`. Como instalar: `claude plugin marketplace add earthtojake/text-to-cad#latest` e depois `claude plugin install text-to-cad@earthtojake`. Precisa do [uv](https://docs.astral.sh/uv/).

O plugin traz o servidor local `cad`, que mostra os modelos na conversa. **Windows 11:** se o Smart App Control estiver ligado, o núcleo de CAD é bloqueado; `uvx cadgen doctor` diz se está tudo certo. **Telemetria:** vem ligada; desligue com `uvx cadgen telemetry off`.

| Skill | O que faz |
|---|---|
| `cad` | Cria e edita peças e montagens 3D paramétricas em código, com visualização ao vivo na conversa; exporta STEP, STL, 3MF e GLB, mede geometria e articula montagens. |
| `step-parts` | Busca e baixa peças compráveis prontas no step.parts (servos, motores, placas, conectores, parafusos, rolamentos). |
| `engineering-drawing` | Gera desenho técnico em PDF: vistas, cotas, furos, notas e carimbo em folha ISO. |
| `dfm` | Revisa se a peça é viável de fabricar (usinagem, chapa, injeção). |
| `dfam-check` | Revisa se a peça é viável em impressão 3D. |
| `gcode` | Fatia o modelo e gera G-code para impressão 3D. |
| `bambu-labs` | Envia e acompanha impressões em impressoras Bambu Lab. |
| `dxf` | Gera arquivos DXF 2D para corte a laser, plasma ou jato d'água. |
| `sendcutsend` | Revisa arquivos DXF e STEP antes do pedido no SendCutSend: material, espessura e se o arquivo será aceito. |
| `urdf` / `srdf` / `sdf` | Descrições de robôs e cenas para simulação (ROS, MoveIt, Gazebo). |

---

## Fora do pack

| O quê | Por quê |
|---|---|
| `ub-mode` ([unclebob/ub-mode](https://github.com/unclebob/ub-mode)) | Método de engenharia do Uncle Bob: fazer funcionar, fazer direito, prática. O repositório não tem licença: **só monitorado**, sem cópia no pack. Para instalar, copie o `SKILL.md` para `~/.claude/skills/ub-mode/`. |
| `maestri-*` (7) | Vêm com o app comercial Maestri; não há repositório público. |
| Nativas do Claude Code (`/code-review`, `/simplify`, `/security-review`, `/init`, `run`, `claude-api`, `dataviz`, `plugin-authoring`, `update-config`) | Já vêm com o Claude Code em qualquer instalação. |
| Design visual, documentos, vendas, marketing | Não são de programação. |

## Licenças

Cada pasta em `packs/` mantém a licença da origem; veja [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Os scripts deste repositório (`scripts/`, `.github/`) e a skill `checklist-publicacao-site` são da Com Automação.
