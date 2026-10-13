---
name: checklist-publicacao-site
description: "Roda um checklist de 20 itens de prontidão antes de publicar um site, verificando cada um no código e no navegador em vez de perguntar ao usuário. Cobre SEO (favicon, og image, sitemap, robots, títulos, meta descriptions, 404), funcionalidade (formulário, link de WhatsApp, links quebrados), performance (PageSpeed, peso de imagens, responsividade mobile), conformidade brasileira (cookies/LGPD, CNPJ e dados no rodapé, Google Analytics) e infraestrutura (domínio, HTTPS, hospedagem, cabeçalhos de segurança). Use sempre que o usuário disser que vai publicar, subir, lançar, entregar ou colocar no ar um site, ou perguntar se está pronto, o que falta, ou pedir 'o checklist' — mesmo sem citar itens específicos. Também serve para revisar um site já no ar. Diferente de website-finishing-director (que dá nota de polimento visual) e de shipping-and-launch (que trata de estratégia de deploy e rollback): esta é um portão objetivo de pode-subir / não-pode-subir."
---

# Checklist de publicação de site

Um portão de go/no-go antes de um site ir ao ar. São 20 itens, e o valor está em **verificar cada um**, não em listá-los — o usuário já tem a lista. Se ele quisesse apenas o lembrete, não precisaria de você.

## O princípio que sustenta tudo

Este checklist existe para evitar a vergonha de descobrir um problema depois que o cliente viu. Um item marcado como aprovado sem verificação real destrói exatamente o valor que ele deveria entregar: dá confiança falsa na véspera do lançamento. É melhor devolver "não consegui verificar" em cinco itens do que aprovar vinte no escuro.

Por isso cada item tem exatamente três desfechos possíveis:

- **OK** — você verificou e passou. Cite a evidência (arquivo, linha, valor medido).
- **FALHA** — você verificou e reprovou. Diga o que falta e onde.
- **VOCÊ CONFIRMA** — está fora do alcance de leitura de código. Diga o que a pessoa deve olhar.

Nunca use OK como sinônimo de "provavelmente está bem".

## Antes de começar: descubra o alvo

Os itens se dividem por *onde* vivem. Estabeleça o que você tem em mãos:

- **Repositório** (quase sempre) — permite verificar 16 dos 20 itens lendo código e configuração.
- **URL no ar** (staging ou produção) — libera os checks de navegador e os de infraestrutura.

Se só houver repositório, rode os 16 e liste os 4 restantes como pendentes de confirmação. Não empurre a auditoria inteira para o usuário só porque falta a URL — a maior parte é verificável sem ela.

Pergunte a URL apenas se ela mudar o que você entrega. Se o usuário disser "ainda não subiu", siga sem ela.

## Os 20 itens

Os caminhos abaixo assumem Next.js App Router. Para outros stacks (Vite, Astro, WordPress, HTML estático), a ideia do check é a mesma — procure o equivalente em vez de reprovar por não achar o arquivo exato.

### A. SEO e presença — 7 itens, verificáveis no repositório

**4. Página 404** — Existe uma 404 própria, com o visual do site e caminho de volta para a home? Em Next: `src/app/not-found.tsx`. Falha comum: a 404 padrão do framework, sem identidade e sem link de saída.

**9. Favicon** — Procure `favicon.ico`, `icon.*` ou `apple-icon.*` em `src/app/` ou `public/`. Passa quando existe e tem versão adequada para tela retina (180×180 para Apple). Um `.ico` de 16px sozinho passa raspando; diga isso em vez de aprovar em silêncio.

**10. OG image** — A imagem que aparece quando alguém compartilha no WhatsApp. Procure `opengraph-image.*` ou a chave `openGraph` no export `metadata`. Passa quando existe e mede 1200×630. É o item mais esquecido e o mais visível: sem ele, o link do cliente aparece como um retângulo cinza no grupo de WhatsApp.

**11. Sitemap.xml** — `src/app/sitemap.ts` ou `public/sitemap.xml`. Passa quando existe e cobre as rotas reais. Compare com os diretórios de página do projeto: um sitemap que lista só a home num site de 8 páginas é falha, não aprovação.

**15. Robots.txt** — `src/app/robots.ts` ou `public/robots.txt`. Verifique também se não sobrou um `Disallow: /` de ambiente de teste, nem `noindex` no `metadata`. Bloquear o Google sem querer é o erro mais caro da lista, e o mais silencioso.

**16. Títulos** — Cada rota tem `title` próprio, único e descritivo, entre 30 e 60 caracteres? Falha quando várias páginas repetem o mesmo título ou quando sobrou o placeholder do template.

**17. Meta descriptions** — Cada rota tem `description`, entre 120 e 160 caracteres? Mesma regra de unicidade dos títulos.

### B. Funcionalidade — 3 itens, repositório e navegador

**2. Formulário** — Leia o handler de submit e responda uma pergunta: para onde os dados vão? Passa quando o destino existe de fato (endpoint, serviço ou `mailto:` com endereço preenchido), há retorno visível após enviar, e os campos obrigatórios estão marcados. Falha clássica: formulário bonito que não envia para lugar nenhum, ou com o e-mail de destino ainda vazio numa constante.

**3. WhatsApp** — Procure `wa.me` ou `api.whatsapp.com`. Passa quando o número está em formato internacional sem símbolos (`5511987654321`). Um `wa.me/(11) 98765-4321` não abre — confira o formato, não apenas a existência do link.

**19. Links** — Extraia todos os `href` internos e confirme que cada destino existe como rota. Com URL no ar, verifique também os externos pelo navegador. Reporte `href="#"` remanescentes de template.

### C. Performance e mídia — 3 itens

**1. Responsividade mobile** — Com URL: abra em 375×812 e percorra a página inteira. Procure rolagem horizontal (o sintoma mais comum), texto abaixo de 14px, alvos de toque menores que 44px e conteúdo cortado. Sem URL: procure larguras fixas em px e grids sem breakpoint. Um print em 375px vale mais que qualquer descrição.

**7. PageSpeed** — Com URL e Chrome DevTools disponível, rode a auditoria e reporte LCP, CLS e INP com os números medidos. Passa com LCP abaixo de 2,5s e CLS abaixo de 0,1. Sem URL, avalie riscos estruturais: fontes sem `display: swap`, imagens sem dimensão declarada, bibliotecas pesadas no bundle inicial.

**8. Comprimir imagens** — Liste `public/` por tamanho. Sinalize imagens acima de 300 KB e vídeos acima de 5 MB. Verifique o formato (`.jpg`/`.png` onde caberia `.webp`/`.avif`) e se o projeto usa o componente de imagem do framework em vez de `<img>` cru. Costuma render o maior ganho de PageSpeed com o menor esforço — ao achar um hero de 4 MB, diga quanto ele custa em segundos.

### D. Confiança e conformidade — 3 itens

**13. Cookies** — No Brasil a régua é a **LGPD**, não o GDPR. Se o site usa apenas cookies essenciais, banner não é obrigatório, e um banner desnecessário só atrapalha a conversão. Se há analytics ou pixel de rastreamento, aí sim é preciso aviso com consentimento antes do disparo. Descubra qual dos dois casos é o do projeto antes de exigir banner.

**14. Dados no rodapé** — Razão social, CNPJ, endereço e forma de contato. Não é burocracia: é o que separa um site que parece confiável de um que parece golpe, e o Google lê esses sinais. Falha quando o rodapé tem só um logo e o ano.

**12. Google Analytics** — Procure `gtag`, `G-`, `googletagmanager` ou equivalente (Plausible, Umami). Passa quando o ID está preenchido de verdade; um `G-XXXXXXXXXX` de placeholder é falha. Confirme também que o disparo respeita o consentimento do item 13.

### E. Infraestrutura — 4 itens, quase sempre humanos

Estes raramente são verificáveis pelo repositório. Não invente aprovação: descreva o que a pessoa precisa olhar.

**5. Domínio próprio** — O site responde no domínio do cliente, e não em `vercel.app` ou `netlify.app`? Com URL, confirma-se direto. Sem URL, pergunte se o DNS já aponta.

**6. HTTPS** — Certificado válido e `http://` redirecionando para `https://`. Do repositório dá para conferir só se há recurso `http://` embutido gerando conteúdo misto.

**18. Hospedagem** — Fora do alcance do código. Pergunte onde está hospedado, se há backup automático e qual o plano. Não opine sobre qualidade sem saber o provedor.

**20. Configurações de segurança** — Parcialmente verificável: procure cabeçalhos em `next.config.ts` ou equivalente (`Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, e CSP se houver). Verifique também que não há chave de API ou segredo em código que vai para o cliente. A parte de servidor precisa da URL.

## Formato do relatório

Abra com o veredito, porque é a única coisa que a pessoa precisa para decidir se publica hoje:

```
## Veredito: PODE SUBIR / NÃO PODE SUBIR
<uma frase dizendo o que trava, se algo trava>

| # | Item | Status | Evidência |
|---|------|--------|-----------|
| 1 | Responsividade mobile | OK | sem rolagem horizontal em 375px |
| 4 | Página 404 | FALHA | não existe src/app/not-found.tsx |
| 18 | Hospedagem | VOCÊ CONFIRMA | onde está hospedado? há backup? |
```

Depois da tabela, detalhe **só as falhas**, cada uma com o arquivo e a correção concreta. Itens aprovados não precisam de parágrafo — ninguém lê elogio a checklist.

Ordene as falhas por custo de deixar passar, não pela numeração. Um `robots.txt` bloqueando o Google e uma OG image faltando são categorias diferentes de problema: o primeiro apaga o site da busca por semanas, o segundo deixa o link feio. Diga qual é qual.

Ao terminar, ofereça corrigir as falhas — a maioria (404, sitemap, robots, metadata, favicon) são arquivos pequenos, de minutos. Mas espere o aceite antes de mexer no projeto: o checklist é diagnóstico, e quem decide o que entra antes do lançamento é o dono do site.
