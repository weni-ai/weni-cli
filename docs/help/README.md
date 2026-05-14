# Weni Agents — Cursor Skill

Skill personalizada para o Cursor que auxilia na criação e atualização de agentes Weni.

## O que é isso?

Um conjunto de 2 arquivos que ensinam o Cursor a entender todo o padrão de desenvolvimento de agentes:

- Como criar Tools com `TextResponse` e `FinalResponse`
- Como usar Broadcasts (catalogs, PIX, WhatsApp Flows, etc.)
- Como registrar Events no Datalake
- Como autenticar nas Flows APIs e no Retail Setup (VTEX proxy)
- Validação de `agent_definition.yaml`

Na prática, quando você pedir pro Cursor "cria uma tool que busca o pedido no VTEX", ele já vai saber usar `context.project.get("auth_token")`, retornar `FinalResponse()` com broadcast, registrar evento — tudo no padrão.

## Estrutura desta pasta

```
docs/help/
├── README.md                         ← você está aqui (guia de instalação)
└── cursor-skill/                     ← arquivos para copiar no Cursor
    ├── SKILL.md                      ← referência rápida (obrigatório)
    └── constitution.md               ← referência completa
```

| Arquivo | Descrição |
|---------|-----------|
| [cursor-skill/SKILL.md](cursor-skill/SKILL.md) | Referência rápida — resumo dos padrões, importações e exemplos |
| [cursor-skill/constitution.md](cursor-skill/constitution.md) | Referência completa — todas as regras, validações, API endpoints e exemplos detalhados |

## Instalação

### macOS

1. Abra o Finder e pressione `Cmd + Shift + G`
2. Cole o caminho `~/.cursor/skills` e pressione Enter
   > Se a pasta `skills` não existir, vá para `~/.cursor/` e crie manualmente
3. Crie uma nova pasta chamada `weni-agents`
   > O nome DEVE ser exatamente `weni-agents` (minúsculo, com hífen)
4. Copie os 2 arquivos da pasta `cursor-skill/` para dentro de `~/.cursor/skills/weni-agents/`
5. Reinicie o Cursor

Resultado esperado:

```
~/.cursor/skills/
└── weni-agents/
    ├── SKILL.md
    └── constitution.md
```

### Instalação por projeto (opcional)

Se quiser que a skill seja específica de um projeto (ao invés de global), coloque a pasta em `.cursor/skills/` dentro da raiz do projeto, em vez de `~/.cursor/skills/`.

## Como verificar se funcionou

Após reiniciar o Cursor:

1. Abra o Agent Chat (`Cmd + I` no Mac)
2. Digite `/` e procure por `weni-agents` — se aparecer, a skill está instalada
3. Ou peça algo como: *"Cria uma tool que busca o status de um pedido VTEX"* — se o Cursor usar `context.project.get("auth_token")`, `FinalResponse`, broadcasts etc., a skill está ativa

## Como atualizar

1. Substitua os arquivos na pasta `weni-agents` com as versões novas da pasta `cursor-skill/`
2. Reinicie o Cursor

## Dicas de uso

- **Ativação automática** — quando o Cursor detecta que sua pergunta é sobre agentes Weni, ele puxa o contexto da skill sozinho
- **Memória permanente** — diferente de colar instruções no chat toda vez, a skill está sempre disponível
