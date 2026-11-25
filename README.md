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
| `reanimate` | `reanimate/skills/` | **Nova.** Clona uma animação, seção ou efeito de um site, vídeo, gif ou Lottie para o seu código, grava o clone e compara quadro a quadro com a referência até tempo, curva e sequência baterem. Cobre CSS, JS, canvas, WebGL e three.js. Depois de instalar, rode `bash scripts/setup.sh` na pasta dela (precisa do [bun](https://bun.sh); no Windows, rode no Git Bash, porque o `bash` do PowerShell abre o WSL). ([NiazMorshed2007/reanimate](https://github.com/NiazMorshed2007/reanimate), MIT) |

Origem do genjutsu: [AThevon/genjutsu](https://github.com/AThevon/genjutsu) (MIT). **Atenção:** a skill única `genjutsu` foi dividida pelo autor em `paint`, `cast` e `bunshin`. Quem tem a versão antiga instalada deve trocá-la pelas três.

**genjutsu ou illumi?** O genjutsu cria a aparência e o movimento. O illumi (seção 20) acerta os detalhes e revisa. Nas tarefas grandes, rode o genjutsu primeiro e o illumi depois.

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
| `teardown` | `teardown/` | **Nova.** Simulador 3D de uma máquina real (motor, trem de pouso, engrenagens) numa página HTML offline: a máquina funciona, os painéis mostram os números reais, cada botão abre uma parte e a página faz um tour sozinha. Também grava vídeo de 60 fps com som. ([elvarofficial/teardown](https://github.com/elvarofficial/teardown), MIT) |
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

**`teardown` precisa de instalação extra:** depois do instalador, rode `npm install && npx playwright install chromium` dentro de `~/.claude/skills/teardown` (Node 20 ou mais novo; o vídeo usa `ffmpeg` e o som, Python 3). O `--force` do instalador troca a pasta inteira, então repita esse passo depois dele. Os GIFs de exemplo (`docs/`, 14 MB) ficam fora do pack.

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
| `cad` | Cria e edita peças e montagens 3D paramétricas em código, com visualização ao vivo na conversa. Também faz perfis 2D e DXF para corte, verifica se a peça pode ser usinada, dobrada, injetada ou impressa, busca peças prontas e anima montagens. Exporta STEP, STL, 3MF, GLB e DXF. |
| `engineering-drawing` | Gera desenho técnico em PDF: vistas, cotas, furos, notas e carimbo em folha ISO. |
| `fea` | **Nova.** Simulação de esforço: diz se a peça aguenta a carga, onde concentra tensão, quanto deforma e o fator de segurança. |
| `pcb` | **Nova.** Cria, posiciona, roteia e revisa placas de circuito no KiCad (esquemático, regras elétricas, arquivos para fabricar na JLCPCB ou PCBWay). |
| `print3d` | **Nova.** Fatia STL, 3MF ou OBJ em G-code com o OrcaSlicer e envia para impressoras Bambu Lab. Nunca inicia a impressão sozinho. |
| `robot-simulation` | **Nova.** Descrições de robôs e cenas (URDF, SRDF, SDF) para ROS, MoveIt e Gazebo. |
| `sendcutsend` | Revisa arquivos DXF e STEP antes do pedido no SendCutSend: material, espessura e se o arquivo será aceito. |

Na versão 0.11 o autor juntou as skills antigas: `dxf`, `dfm`, `dfam-check` e `step-parts` viraram parte da `cad`; `gcode` e `bambu-labs` viraram `print3d`; `urdf`, `srdf` e `sdf` viraram `robot-simulation`.

### 18. Auditoria de segurança (Cloudflare)

Origem: [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) (MIT). Pasta: `security-audit/skills/`. Instalada pelo `scripts/install.py`.

| Skill | O que faz |
|---|---|
| `security-audit` | Revisão de segurança defensiva de código, APIs, serviços, CLIs e bibliotecas: acha falhas que cruzam uma fronteira de confiança real e entrega evidência no código, reprodução segura, prioridade e a menor correção eficaz. Por padrão só orienta; a auditoria completa em várias fases, com relatório validado por script, roda só quando pedida. |

### 19. Ponytail (o sênior mais preguiçoso da sala)

Origem: [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (MIT). Pasta: `ponytail/skills/`. Como instalar: `/plugin marketplace add DietrichGebert/ponytail` e depois `/plugin install ponytail@ponytail`.

**Atenção:** fica ativo em toda sessão (hooks de início de sessão, subagente e envio de prompt) e grava um registro de cada tarefa (custo, turnos, tokens) em `~/.config/ponytail/band/`. Um webhook opcional pode enviar esse registro para fora; vem vazio, e assim nada sai da máquina. O sync acompanha a pasta `hooks/`.

| Skill | O que faz |
|---|---|
| `ponytail` | Modo "sênior preguiçoso": a menor mudança que resolve o problema por inteiro (YAGNI, biblioteca padrão primeiro, sem abstração não pedida) e respostas que se entendem numa leitura. Níveis `lite`, `full`, `ultra` ou `off`. |
| `ponytail-review` | Revisa uma mudança: lógica, segurança, carga real, código arriscado sem teste, lentidão e o que dá para cortar. Lê o código conectado, não só o diff. |
| `ponytail-audit` | A mesma revisão para o repositório inteiro, do mais importante para o menos. |
| `ponytail-debt` | Lista os comentários `shortcut:` deixados para depois, como um livro de dívidas. |
| `ponytail-gain` | Mostra a economia medida (menos código, custo e tempo) no benchmark do autor. |
| `ponytail-help` | Referência rápida de níveis e comandos. |

### 20. illumi (revisão e acabamento de interface)

Origem: [jakubkrehel/skills](https://github.com/jakubkrehel/skills) (MIT), publicado pelo autor como plugin `interfaces`. Aqui o conjunto se chama illumi. Pasta: `illumi/skills/`. Instalada pelo `scripts/install.py`. **Nova.**

- Quem já instalou o plugin oficial (`/plugin marketplace add jakubkrehel/skills` e `/plugin install interfaces@interfaces`) deve rodar o instalador com `--skip illumi`, para não ter as skills em dobro.
- A `teardown` do autor fica fora do pack: o nome colide com a `teardown` da seção 6. Quem quiser as duas instala o plugin oficial, em que ela vira `interfaces:teardown`.
- As marcadas com *comando* não rodam sozinhas: você chama com `/nome`.

| Skill | O que faz |
|---|---|
| `better-interface` | Revisa uma tela, um fluxo ou a interface inteira (acessibilidade, layout, texto, tipografia, cor e acabamento) e entrega um relatório em ordem de prioridade. |
| `better-ui` | Acabamento com valores exatos: arredondamento, alinhamento óptico, sombras, estados de ícone e animação. |
| `better-typography` | Escala tipográfica, espaçamento, recursos de fonte, quebra de linha, corte de texto e pontuação. |
| `better-colors` | Gera paletas, nomeia cores semânticas, converte formatos e mede contraste. |
| `better-layout` | Agrupamento, alinhamento, ordem de leitura e estrutura responsiva que aguenta tradução e espelhamento. |
| `better-accessibility` | Teclado e foco, ARIA, nomes acessíveis, formulários, leitor de tela, movimento e zoom, pela WCAG 2.2. |
| `better-writing` | Escreve e revisa o texto da interface (rótulos, erros, estados vazios, confirmações) no tom do produto. |
| `build-design` | Monta a tela a partir de um Figma ou de uma imagem, usando os tokens e componentes do projeto. |
| `interface-review` | *Comando.* Revisa um branch, PR ou mudança não commitada atrás de problemas de interface que ela criou. |
| `explain-interface` | *Comando.* Explica como um site, efeito ou animação foi feito, a partir de uma URL ou print. |
| `variant` | *Comando.* Gera várias versões de um componente para você comparar e escolher. |
| `break` | *Comando.* Mostra um componente em todos os cenários possíveis numa página temporária e testa os limites. |
| `state-machine` | *Comando.* Mostra todos os estados de um componente com dados falsos e um seletor. |
| `afk` | *Comando.* Trabalha no projeto enquanto você está fora: cria melhorias num branch local e deixa um relatório. Use só com tudo salvo no Git. |

### 21. ub-mode (Uncle Bob)

Origem: [unclebob/ub-mode](https://github.com/unclebob/ub-mode) (MIT desde novembro de 2026; antes ficava fora do pack por não ter licença). Pasta: `ub-mode/`. Instalada pelo `scripts/install.py`. **Nova no pack.**

| Skill | O que faz |
|---|---|
| `ub-mode` | Método de engenharia do Uncle Bob: fazer funcionar, fazer direito, prática. As ferramentas que ele cita (crapper, dryer, mutator) são instaladas à parte; veja o README da origem. |

### 22. Impeccable (direção visual e vocabulário de design)

Origem: [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (Apache-2.0). Pasta: `impeccable/.claude/`. A skill é instalada pelo `scripts/install.py`; na primeira vez que roda, o script dela baixa o motor nativo (cerca de 22 MB) das releases do próprio repositório e confere o checksum. **Nova no pack.**

| Skill | O que faz |
|---|---|
| `impeccable` | Um comando com vários modos: `init` (entrevista e contexto de design do projeto), `document` (gera o DESIGN.md), `critique` e `audit` (revisão), `polish`, `bolder`, `quieter`, `typeset`, `colorize`, `animate`, `layout` e outros. Detecta padrões de "cara de IA" antes de publicar. O `bunshin` a usa para a direção visual quando ela está instalada. |

Os 5 agentes de apoio (`impeccable-finish-reviewer` e outros) ficam em `impeccable/.claude/agents/`. Para usá-los, copie os arquivos para `~/.claude/agents/`; sem eles, a skill usa uma versão reduzida de cada papel. O instalador oficial faz tudo de uma vez: `npx impeccable install --user --providers=claude --no-hooks -y`.

**genjutsu, illumi ou Impeccable?** Pedido genérico de interface continua no genjutsu, e revisão de detalhes no illumi. Use o Impeccable quando pedir por nome, para criar o contexto de design do projeto (`init`, `document`), ou dentro do bunshin.

### 23. Emil Kowalski (testes de interface e mobile)

Origem: [emilkowalski/skills](https://github.com/emilkowalski/skills) (MIT), de Emil Kowalski (autor do Sonner e do Vaul). Pasta: `emil-skills/skills/`. Instalada pelo `scripts/install.py`. **Nova.**

Entram só 3 das 20 skills do repositório. As de criar animação ficam fora porque o genjutsu (`cast`) já faz isso, e as de revisar animação porque o illumi já faz. Também ficam fora as de nicho: Expo, Swift, Sonner, `prototype` e `learn-taste`.

| Skill | O que faz |
|---|---|
| `break-ui` | Testa uma tela com os piores dados realistas (nome enorme, e-mail sem quebra, lista vazia, contagem de 1, número gigante, emoji), coloca um botão "dados de demonstração / pior caso" e lista o que quebrou com a correção de cada item. Só corrige quando você pedir. |
| `mobile-native` | Faz o site parecer app no celular: hover que gruda, piscada ao tocar, bug do 100vh, campo que dá zoom, toque lento, conteúdo embaixo do notch, PWA, carrossel e folha inferior. |
| `animation-vocabulary` | Dá o nome certo de um efeito de movimento que você só sabe descrever ("o pulinho quando o menu abre" → *pop in*), para pedir à IA ou ao designer. |

**`break-ui` ou `/break` do illumi?** A `break-ui` entra sozinha quando você pede para testar o pior caso, e usa dados realistas e os limites do banco. O `/break` do illumi só roda quando você chama, e mostra o componente em todos os cenários numa página temporária, com larguras, RTL e temas.

### 24. LGPD (privacidade e proteção de dados)

Origem: [goul4rt/lgpd-skills](https://github.com/goul4rt/lgpd-skills) (MIT). Pasta: `lgpd-skills/skills/`. Instalada pelo `scripts/install.py` e também incluída no Pack B como plugin. **Nova.**

São 19 skills em português sobre a LGPD (Lei 13.709/2018), as resoluções da ANPD e o ECA Digital. As skills inspecionam código, schemas e configurações e redigem documentos, mas **não substituem revisão jurídica**: o maestro pausa para revisão humana antes de fechar o registro de operações, o RIPD, a política de privacidade e a comunicação à ANPD.

| Skill | O que faz |
|---|---|
| `lgpd-audit` | Maestro: pergunta o contexto, descobre o que o projeto trata de dado pessoal e chama as outras na ordem certa. Num vazamento em andamento, pula direto para a resposta a incidente. Guarda tudo em `.lgpd/` no projeto. |
| `lgpd-legacy-retrofit` | Entrada para sistema que já existe: varre o código, aponta as lacunas e monta um plano de correção por prioridade. |
| `lgpd-data-mapping`, `lgpd-legal-basis`, `lgpd-ropa`, `lgpd-ripd` | Mapa de dados, base legal de cada tratamento, registro de operações (Art. 37) e relatório de impacto (RIPD). |
| `lgpd-consent-schema`, `lgpd-dsar`, `lgpd-retention-erasure` | Consentimento em registro que não se apaga, pedidos do titular (acesso, correção, exclusão) com prazo, e retenção e exclusão de dados. |
| `lgpd-encryption-keys`, `lgpd-anonymization`, `lgpd-audit-logging` | Criptografia e chaves, anonimização e pseudonimização, e log de auditoria à prova de alteração. |
| `lgpd-incident-response` | Roteiro de incidente: contenção, prazo e modelos de comunicação à ANPD e ao titular. |
| `lgpd-privacy-policy`, `lgpd-dpo-encarregado`, `lgpd-dpa`, `lgpd-vendor-audit`, `lgpd-international-transfer` | Política de privacidade, encarregado (DPO), contrato com operadores, avaliação de fornecedores e transferência para fora do país. |
| `lgpd-eca-digital-minors` | Obrigações do ECA Digital (Lei 15.211/2025) para produtos usados por crianças e adolescentes. |

Quem já instalou o plugin oficial (`/plugin marketplace add goul4rt/lgpd-skills`) deve rodar o instalador com `--skip lgpd-skills`, para não ter as skills em dobro.

---

## ECC no Pack A (curadoria)

Origem: [affaan-m/ECC](https://github.com/affaan-m/ECC) (MIT). Pasta: `ecc/skills/`. Das 327 skills do ECC, **249 entram no Pack A** e são instaladas pelo `scripts/install.py` como as outras. Ficam de fora 49 que repetem o que o pack já tem e 29 que só funcionam com o ECC instalado; essas estão no Pack B.

Destaques para quem trabalha com sites e conteúdo: `seo`, `web-perimeter-owasp-2025-audit`, `production-audit`, `mysql-patterns`, `frontend-slides`, `brand-voice`, `article-writing`, `remotion-video-creation`. Para cuidar do próprio arsenal: `skill-stocktake`, `mcp-dependency-review`, `security-scan`, `skill-scout`, `config-gc`, `config-health`.

<details><summary>As 249 skills do ECC no Pack A</summary>

`agent-architecture-audit`, `agent-eval`, `agent-harness-construction`, `agent-introspection-debugging`, `agent-payment-x402`, `agent-runtime-gateway-smoke-test`, `agent-security-hardening`, `agent-self-evaluation`, `agentic-engineering`, `ai-first-engineering`, `ai-regression-testing`, `android-clean-architecture`, `angular-developer`, `api-connector-builder`, `article-writing`, `backend-patterns`, `benchmark-methodology`, `benchmark-optimization-loop`, `bengali-nlp`, `blender-motion-state-inspection`, `brand-discovery`, `brand-voice`, `bun-runtime`, `canary-watch`, `carrier-relationship-management`, `change-impact`, `cisco-ios-patterns`, `click-path-audit`, `clickhouse-io`, `code-tour`, `codebase-onboarding`, `codehealth-mcp`, `competitive-platform-analysis`, `competitive-report-structure`, `compose-multiplatform-patterns`, `config-gc`, `config-health`, `connections-optimizer`, `content-engine`, `content-hash-cache-pattern`, `context-budget`, `contract-first`, `cost-aware-llm-pipeline`, `council`, `council-multi-model`, `counterparty-channel-discipline`, `cpp-coding-standards`, `cpp-testing`, `crosspost`, `csharp-testing`, `customer-billing-ops`, `customs-trade-compliance`, `dart-flutter-patterns`, `dashboard-builder`, `data-scraper-agent`, `data-throughput-accelerator`, `database-migrations`, `deep-research`, `defi-amm-security`, `django-celery`, `django-patterns`, `django-security`, `django-tdd`, `django-verification`, `docker-patterns`, `dotnet-patterns`, `dynamic-workflow-mode`, `e2e-testing`, `energy-procurement`, `enterprise-agent-ops`, `error-handling`, `esign-field-placement`, `eval-harness`, `evm-token-decimals`, `exa-search`, `fal-ai-media`, `fastapi-patterns`, `flox-environments`, `flutter-dart-code-review`, `foundation-models-on-device`, `frontend-patterns`, `frontend-slides`, `fsharp-testing`, `gan-style-harness`, `generating-python-installer`, `godot-patterns`, `godot-testing`, `golang-patterns`, `golang-testing`, `google-workspace-ops`, `growth-log`, `healthcare-cdss-patterns`, `healthcare-emr-patterns`, `healthcare-eval-harness`, `healthcare-phi-compliance`, `hexagonal-architecture`, `hipaa-compliance`, `homelab-network-readiness`, `homelab-network-setup`, `homelab-pihole-dns`, `homelab-vlan-segmentation`, `homelab-wireguard-vpn`, `hookify-rules`, `i18n-sync`, `inherit-legacy-style`, `inventory-demand-planning`, `investor-materials`, `investor-outreach`, `ios-icon-gen`, `issue-review`, `iterative-retrieval`, `ito-baskets`, `ito-compute`, `ito-inference`, `ito-training`, `java-coding-standards`, `jira-integration`, `jpa-patterns`, `knowledge-ops`, `kotlin-coroutines-flows`, `kotlin-exposed-patterns`, `kotlin-ktor-patterns`, `kotlin-patterns`, `kotlin-testing`, `kubernetes-patterns`, `laravel-patterns`, `laravel-plugin-discovery`, `laravel-security`, `laravel-tdd`, `laravel-verification`, `latency-critical-systems`, `lead-intelligence`, `liquid-glass-design`, `living-docs-governance`, `llm-trading-agent-security`, `logistics-exception-management`, `loop-design-check`, `mailtrap-email-integration`, `manim-video`, `market-research`, `marketing-campaign`, `master-agreement-generator`, `mcp-dependency-review`, `ml-adoption-playbook`, `mle-workflow`, `module-governance`, `module-regression`, `mybatis-patterns`, `mysql-patterns`, `nestjs-patterns`, `netmiko-ssh-automation`, `network-bgp-diagnostics`, `network-config-validation`, `network-interface-health`, `nextjs-turbopack`, `nodejs-keccak256`, `nutrient-document-processing`, `nuxt4-patterns`, `opensource-pipeline`, `operator-approval-loop`, `osint-investigation`, `perl-patterns`, `perl-security`, `perl-testing`, `plan-canvas`, `plankton-code-quality`, `platform-factory`, `postgres-patterns`, `prediction-market-oracle-research`, `prediction-market-risk-review`, `prisma-patterns`, `production-audit`, `production-scheduling`, `project-flow-ops`, `prompt-caching-strategy`, `python-patterns`, `python-testing`, `pytorch-patterns`, `quality-nonconformance`, `quarkus-patterns`, `quarkus-security`, `quarkus-tdd`, `quarkus-verification`, `rails-patterns`, `rails-security`, `react-native-patterns`, `react-patterns`, `react-performance`, `react-testing`, `recsys-pipeline-architect`, `recursive-decision-ledger`, `redis-patterns`, `regex-vs-llm-structured-text`, `remotion-video-creation`, `returns-reverse-logistics`, `roundhouse-x402`, `rules-distill`, `rust-patterns`, `rust-testing`, `safety-guard`, `santa-method`, `scientific-db-openalex-database`, `scientific-db-pubmed-database`, `scientific-db-uspto-database`, `scientific-pkg-gget`, `scientific-thinking-literature-review`, `scientific-thinking-scholar-evaluation`, `search-first`, `security-scan`, `seo`, `short-video-distribution`, `skill-comply`, `skill-scout`, `skill-stocktake`, `social-graph-ranker`, `social-publisher`, `springboot-patterns`, `springboot-security`, `springboot-tdd`, `springboot-verification`, `story-lifecycle`, `strategic-compact`, `swift-actor-persistence`, `swift-concurrency-6-2`, `swift-protocol-di-testing`, `swiftui-patterns`, `taste`, `taste-application`, `taste-distillation`, `tasteforge-video`, `terminal-opener`, `terraform-patterns`, `test-collaboration`, `tinystruct-patterns`, `token-budget-advisor`, `token-card`, `typescript-patterns`, `ui-demo`, `ui-to-vue`, `uncloud`, `video-editing`, `videodb`, `visa-doc-translate`, `vite-patterns`, `vue-patterns`, `web-perimeter-owasp-2025-audit`, `windows-desktop-e2e`, `x-api`, `yoruba-localization-testing`

</details>

<details><summary>As 49 que ficaram de fora por repetir o pack (e o que já cobre cada uma)</summary>

| Skill do ECC | Já coberta por |
|---|---|
| `accessibility` | better-accessibility |
| `frontend-a11y` | better-accessibility |
| `api-design` | api-and-interface-design |
| `architecture-decision-records` | documentation-and-adrs |
| `context-and-decisions` | documentation-and-adrs |
| `design-system` | paint / design:design-system |
| `documentation-lookup` | Context7 |
| `frontend-design-direction` | genjutsu / impeccable |
| `git-workflow` | git-workflow-and-versioning |
| `conventional-commit-review` | git-workflow-and-versioning |
| `make-interfaces-feel-better` | illumi |
| `motion-advanced` | motion-design / cast |
| `motion-foundations` | motion-design / cast |
| `motion-patterns` | motion-design / cast |
| `security-review` | security-and-hardening |
| `security-bounty-hunter` | security-audit |
| `tdd-workflow` | test-driven-development |
| `verification-loop` | superpowers:verification-before-completion |
| `coding-standards` | code-review-and-quality |
| `deployment-patterns` | ci-cd-and-automation / shipping-and-launch |
| `benchmark` | performance-optimization |
| `github-ops` | github-* (Ruflo) |
| `browser-qa` | browser-testing-with-devtools |
| `mcp-server-patterns` | mcp-builder |
| `intent-driven-development` | spec-driven-development |
| `product-capability` | product-management:write-spec |
| `product-lens` | idea-refine |
| `blueprint` | superpowers:writing-plans |
| `plan-orchestrate` | superpowers:executing-plans |
| `parallel-execution-optimizer` | superpowers:dispatching-parallel-agents |
| `orch-add-feature` | superpowers |
| `orch-build-mvp` | superpowers |
| `orch-change-feature` | superpowers |
| `orch-fix-defect` | superpowers:systematic-debugging |
| `orch-pipeline` | superpowers |
| `orch-refine-code` | code-simplification |
| `ralphinho-rfc-pipeline` | Ruflo |
| `dev-team` | Ruflo |
| `team-agent-orchestration` | Ruflo |
| `team-builder` | Ruflo |
| `devfleet` | Ruflo |
| `dmux-workflows` | Ruflo |
| `autonomous-loops` | Ruflo / /loop |
| `continuous-agent-loop` | Ruflo / /loop |
| `agentic-os` | Ruflo |
| `autonomous-agent-harness` | Ruflo |
| `leanrea` | REA |
| `ck` | ai-memory |
| `unified-memory` | ai-memory |

</details>

As 29 que só funcionam com o ECC instalado: `agent-sort`, `automation-audit-ops`, `brownfield-retrospective`, `configure-ecc`, `continuous-learning`, `continuous-learning-v2`, `cost-tracking`, `deepseek-harness-setup`, `delivery-gate`, `docs-governance`, `ecc-contribution-review`, `ecc-guide`, `ecc-recipes`, `ecc-tools-cost-audit`, `email-ops`, `finance-billing-ops`, `gateguard`, `hermes-imports`, `messages-ops`, `nanoclaw-repl`, `nasiko-control-plane`, `openclaw-persona-forge`, `prompt-optimizer`, `repo-scan`, `research-ops`, `skill-host-compat`, `terminal-ops`, `unified-notifications-ops`, `workspace-surface-audit`.

## Pack B: ECC completo

Origem: [affaan-m/ECC](https://github.com/affaan-m/ECC) (MIT). Pasta: `ecc-full/`. O ECC inteiro: plugin, 327 skills, 72 agentes, 98 comandos, regras, hooks e instaladores. Fica fora só o que não serve para usar: `assets/` (23 MB de imagens), `docs/` (13 MB), `tests/` (9 MB) e `.github/`. No zip, vem separado (`skills-dev-pack-B.zip`).

Não é instalado pelo `scripts/install.py`. Use o próprio ECC, a partir da pasta `packs/ecc-full`:

- Como plugin do Claude Code: `claude plugin marketplace add ./packs/ecc-full` e depois `claude plugin install ecc@ecc`.
- Ou pelo instalador dele: `npx ecc-universal@2.2.3 install --guided`.

**LGPD no Pack B:** o zip B leva também `packs/lgpd-skills` (seção 24), que se instala como plugin: `claude plugin marketplace add ./packs/lgpd-skills` e depois `claude plugin install lgpd-skills@lgpd-skills`. Não tem hooks. Se já instalou o Pack A, não precisa: as mesmas skills já estão nele.

**Atenção:** o plugin vem com hooks ligados (perfil `standard`), que rodam scripts sozinhos durante as sessões; dá para desligar na configuração do plugin (`hooks_enabled`). As skills do Pack B repetem as do Pack A: se instalar os dois, as do ECC aparecem em dobro (com o prefixo `ecc:` no plugin).

## Pack C: vídeo

Um zip à parte (`skills-video-pack-C.zip`) com as skills de vídeo, para quem só quer essa parte. Instala com o mesmo `scripts/install.py`.

| Skill | Origem | Para quê |
|---|---|---|
| `video-shotcraft` | [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) (Apache-2.0) | Vídeo de produto em Remotion a partir de capturas reais do site: 124 receitas de tomada, modelo pronto, sincronia com a batida, efeitos sonoros do Freesound e editor no navegador. |
| `effects` | [Vibha-Ramprakash/claude-video-effects](https://github.com/Vibha-Ramprakash/claude-video-effects) (MIT) | 51 efeitos em vídeo de rosto falando (Reels, TikTok, Shorts), com rastreio do rosto; Python + ffmpeg. |
| `video-cleanup` | [Mehdi-Ks/video-cleanup](https://github.com/Mehdi-Ks/video-cleanup) (MIT) | Limpa o áudio de fala (ruído, volume baixo, estéreo de um lado só), melhora imagem recomprimida e põe logo, tarja com nome e tela final; Python + ffmpeg. |
| `video-editing` | ECC | Corte e montagem de gravação real com FFmpeg e Remotion. |
| `remotion-video-creation` | ECC | Boas práticas de Remotion (vídeo em React). |
| `manim-video` | ECC | Vídeos explicativos com animação técnica (Manim). |
| `ui-demo` | ECC | Grava demonstrações de sistema web com o Playwright. |
| `short-video-distribution` | ECC | Confere o arquivo e prepara legenda e título para TikTok, Shorts e Reels. |
| `fal-ai-media` | ECC | Gera imagem, vídeo e áudio pelo fal.ai (pago, precisa de chave). |
| `videodb` | ECC | Indexa, busca e edita vídeo pela API do VideoDB (precisa de chave). |
| `taste`, `taste-distillation`, `taste-application`, `tasteforge-video` | ECC | Direção de estilo para clipes curtos: mede vídeos de referência num pacote de estilo e aplica em material novo. |
| `motion-design` | [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill) (MIT) | Princípios de movimento para motion graphics, Lottie e vídeo. |

As skills do ECC e o `motion-design` também estão no Pack A; o zip C só as reúne. `video-shotcraft`, `effects` e `video-cleanup` ficam fora do zip A.

**Créditos:** nenhuma destas skills é da Com Automação. Cada uma pertence ao autor indicado na tabela, mantém a licença original (arquivo `LICENSE` na pasta dela) e aparece em [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). O pack só reúne as cópias para instalar nos computadores da equipe; a versão oficial e as atualizações ficam nos repositórios dos autores.

Depois de instalar:

- `video-shotcraft`: Node 20+ e ffmpeg; `npm install` em `template/` e em `workbench/` na primeira produção. O arquivo da skill é em chinês (o Claude responde em português). Fica fora do pack a pasta de músicas de fundo (`assets/audio`, licença Mixkit), as notas internas e as imagens do README.
- `video-cleanup`: ffmpeg e Python 3.9+; `python scripts/setup_tools.py` na pasta da skill instala numpy e Pillow e baixa o DeepFilterNet (~30 MB). Se o plugin oficial `video-cleanup` já está instalado, rode o instalador com `--skip video-cleanup` para não ficar em dobro.
- `effects`: ffmpeg e Python 3.10+. No Windows, crie o ambiente à mão na pasta da skill: `python -m venv .venv` e `.venv\Scripts\python.exe -m pip install -r requirements.txt`.

## Fora do pack

| O quê | Por quê |
|---|---|
| `maestri-*` (7) | Vêm com o app comercial Maestri; não há repositório público. |
| Nativas do Claude Code (`/code-review`, `/simplify`, `/security-review`, `/init`, `run`, `claude-api`, `dataviz`, `plugin-authoring`, `update-config`) | Já vêm com o Claude Code em qualquer instalação. |
| Design visual, documentos, vendas, marketing | Não são de programação. |

## Licenças

Cada pasta em `packs/` mantém a licença da origem; veja [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Os scripts deste repositório (`scripts/`, `.github/`) e a skill `checklist-publicacao-site` são da Com Automação.
