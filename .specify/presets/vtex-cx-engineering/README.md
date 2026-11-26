# Preset `vtex-cx-engineering`

Preset do [Spec Kit](https://github.com/github/spec-kit) que faz o `/speckit.specify`
produzir uma **Engineering Spec** no formato do Golden Path VTEX CX, em vez da spec
de produto que o Spec Kit gera por padrão.

## Por que ele existe

O comando `speckit.specify` original instrui o agente a escrever *"focus on WHAT
users need and WHY, avoid HOW to implement, written for business stakeholders"* — e
ainda roda um loop de validação que remove conteúdo técnico que escape para a spec.
Nenhuma constitution vence isso, porque é instrução explícita do comando.

No nosso Golden Path a Engineering Spec é o oposto: o **o quê** já foi decidido na
Product Spec, e a spec do repositório existe para responder **o como naquele
serviço**. Isso não é um ajuste de template — é outro artefato. Por isso um preset,
que é o mecanismo do Spec Kit para redefinir comando e template juntos.

## O que ele substitui

| Arquivo | Estratégia | Efeito |
|---------|-----------|--------|
| `commands/speckit.specify.md` | replace | Gate de origem (Product Spec fixada ou ausência declarada), constitution como entrada vinculante e checklist de conformidade de engenharia |
| `templates/spec-template.md` | replace | Seção de herança ou de origem sem Product Spec + seções técnicas: escopo no repo, estado atual, abordagem, contratos, dados e migrações, carga de pico, observabilidade, testes, rollout, alinhamento com a constitution e divergências |
| `templates/plan-additions.md` | append | Acrescenta herança, sequência de entrega, plano de carga de pico, observabilidade, rollout e gate de divergência ao `plan-template` oficial — sem manter cópia dele |

O `append` no plano é deliberado: o template oficial continua sendo a base, então
um upgrade do Spec Kit não exige reconciliar um fork nosso.

## Gate da Product Spec

O comando para antes de criar qualquer arquivo e pede o caminho do arquivo da
Product Spec no clone local do repositório de specs de produto (e o do documento
de arquitetura, quando existir). A partir daí ele resolve sozinho, por `git`, a URL
permanente e o commit/tag, montando a seção de herança exigida pela constitution.

Ele se recusa a gerar a spec quando:

- o caminho não existe ou não está dentro de um repositório git;
- o arquivo tem alteração local não commitada — o conteúdo lido não é o conteúdo
  que o commit fixado aponta;
- o clone está atrasado e ninguém confirmou qual versão vale.

Isso é o Princípio de Traceability deixando de ser recomendação e passando a ser
bloqueio.

### Sem Product Spec

Nem toda mudança nasce no produto. Hotfix, fix e dívida técnica podem não ter
Product Spec, e isso é um caminho normal do processo, sem justificativa. Quando o
desenvolvedor responde que não há Product Spec, o comando pula a resolução por
`git` e a spec abre com `## Origin Without Product Spec`: `Product Spec: none`, o
problema e os critérios de aceite. A estratégia de testes mapeia esses critérios,
e a seção de divergências sai, porque não há herança.

O agente nunca conclui sozinho que não há Product Spec: ele pergunta, ou usa o que
a entrada do usuário já disse. Uma Product Spec que existe mas não pode ser fixada
continua sendo bloqueio, não ausência.

Os dois caminhos de origem valem tanto para o SDD Full quanto para o SDD Lite; o
ciclo continua sendo escolhido pela complexidade.

## Instalação num repositório

Pré-requisitos: `specify init` já executado e constitution gerada pela skill
`setup-engineering`.

Hoje a instalação é a partir de um clone deste repositório:

```bash
git clone --depth 1 https://github.com/weni-ai/vtex-cx-engineering-constitutions /tmp/vtex-cx
specify preset add --dev /tmp/vtex-cx/speckit/vtex-cx-engineering
specify preset resolve spec-template
```

Para distribuir sem clone, falta publicar um artefato: um release com
`vtex-cx-engineering.zip`, instalável por
`specify preset add vtex-cx-engineering --from <url do zip>`, ou um catálogo
próprio registrado com
`specify preset catalog add <url> --name vtex-cx --install-allowed`. Marque
`--install-allowed` apenas em catálogo nosso e auditado.

O `preset add` materializa o comando no diretório da integração ativa. Se o
repositório usa mais de um agente, troque a integração ativa para rematerializar:

```bash
specify integration use cursor-agent
specify integration use claude
```

`.cursor/skills/` e `.claude/skills/` são **saída de build**. Não edite à mão: a
fonte é este diretório.

## Verificação

```bash
specify preset list              # ordem de precedência
specify preset resolve spec-template
specify preset resolve plan-template   # deve mostrar core + nossas adições
```

## Requer PyYAML no interpretador que resolve templates

A resolução de template lê o `preset.yml` em tempo de execução
(`.specify/scripts/python/common.py`), e isso exige PyYAML no Python que o agente
usa. Quando não houver, aponte um interpretador que tenha:

```bash
export SPECKIT_PYTHON_EXECUTABLE=/caminho/para/python   # com PyYAML instalado
```

O interpretador em que você instalou a `specify-cli` serve, porque a CLI já depende
de PyYAML. Sem isso, `resolve_template.py` sai com código 1 e
`ERROR: PyYAML is required to resolve preset template composition`. A falha é
explícita, mas o risco é o agente contornar lendo `.specify/templates/` direto e
seguir com o template oficial como se o preset não existisse — trate esse erro
como bloqueio, não como aviso.

## Camadas

A precedência do Spec Kit é `override do projeto > preset > extension > core`, e
presets empilham por prioridade (número menor vence). Isso espelha a camada das
constitutions:

| Camada | Onde vive | Prioridade |
|--------|-----------|-----------|
| Engenharia (sempre) | este preset | 10 |
| Domínio, se divergir de fato | preset de domínio | 5 |
| Exceção de um repositório | `.specify/templates/overrides/` | acima de tudo |

Só crie um preset de domínio quando o formato da spec realmente precisar ser
diferente — e prefira `append`/`wrap` a `replace`, para não duplicar este.

## Manutenção

Altere aqui, nunca no repositório consumidor. Versione o `preset.version` em SemVer
no mesmo PR que muda o comportamento, e sinalize o impacto na descrição: mudança
aqui afeta todos os repositórios que instalaram o preset. Repositórios já
configurados não atualizam sozinhos — rode `specify preset update
vtex-cx-engineering`.
