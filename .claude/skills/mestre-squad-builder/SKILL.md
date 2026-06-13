# Skill: Mestre Squad Builder

## Propósito

Guia completo para projetar, construir e operar squads multi-agente autônomos usando Claude Code e o Agent SDK. Um squad é um conjunto de agentes especializados que colaboram para resolver tarefas complexas que vão além das capacidades de um único agente.

---

## Conceitos Fundamentais

### O que é um Squad Multi-Agente?

Um squad é uma rede de agentes onde cada membro tem:
- **Papel definido** — especialização clara (pesquisador, desenvolvedor, revisor, orquestrador)
- **Ferramentas específicas** — acesso apenas ao que precisa para sua função
- **Autonomia limitada** — age dentro de limites definidos pelo orquestrador
- **Comunicação estruturada** — passa resultados em formato padronizado

### Padrões de Arquitetura

```
1. ORQUESTRADOR → AGENTES PARALELOS (fan-out)
   Orquestrador divide a tarefa e dispara N agentes em paralelo,
   coleta resultados e sintetiza a resposta final.

2. PIPELINE (cadeia)
   Agente A → Agente B → Agente C
   Cada agente transforma o output do anterior.

3. HIERÁRQUICO (árvore)
   Orquestrador Principal
   ├── Sub-Orquestrador A
   │   ├── Agente A1
   │   └── Agente A2
   └── Sub-Orquestrador B
       └── Agente B1

4. REVISOR/CRITICADOR (loop de qualidade)
   Gerador → Revisor → (aprovado ou volta pro Gerador)
```

---

## Como Criar um Squad — Passo a Passo

### Passo 1: Defina o Problema e Decomponha em Subtarefas

Antes de escrever código, responda:
- Quais subtarefas são **independentes** entre si? (candidatas a paralelo)
- Quais têm **dependência sequencial**? (candidatas a pipeline)
- Qual agente tem **visão global** da tarefa? (o orquestrador)
- Qual é o **formato de saída** esperado de cada agente?

### Passo 2: Projete os Papéis

Para cada agente, defina:

```markdown
## Agente: [Nome]
- **Responsabilidade:** o que ele faz (uma frase)
- **Input:** o que recebe (tipo e formato)
- **Output:** o que produz (tipo e formato)
- **Ferramentas:** quais ferramentas tem acesso
- **Restrições:** o que ele NÃO deve fazer
```

### Passo 3: Construa o Orquestrador

O orquestrador é o cérebro do squad. Ele:
1. Recebe a tarefa original
2. Decompõe em subtarefas
3. Dispara agentes (em paralelo quando possível)
4. Coleta e valida os resultados
5. Sintetiza a resposta final

```python
# Exemplo de orquestrador com Agent SDK
import anthropic

client = anthropic.Anthropic()

def orquestrador(tarefa: str) -> str:
    # 1. Planejamento
    plano = planejar_tarefa(tarefa)
    
    # 2. Execução paralela de subtarefas independentes
    resultados = {}
    for subtarefa in plano.subtarefas_paralelas:
        resultados[subtarefa.id] = executar_agente(
            agente=subtarefa.agente_responsavel,
            input=subtarefa.input,
            ferramentas=subtarefa.ferramentas
        )
    
    # 3. Síntese
    return sintetizar(resultados)
```

### Passo 4: Implemente o Mecanismo de Comunicação

Agentes se comunicam via **mensagens estruturadas**. Use JSON com schema fixo:

```json
{
  "agent_id": "pesquisador-001",
  "task_id": "tarefa-xyz",
  "status": "completed",
  "output": {
    "tipo": "research_findings",
    "conteudo": "...",
    "fontes": [],
    "confianca": 0.9
  },
  "metadata": {
    "tokens_usados": 1500,
    "duracao_ms": 3200
  }
}
```

### Passo 5: Adicione Guardas e Validação

Todo squad precisa de:

```python
# Validação de output de agente antes de passar adiante
def validar_output(output: dict, schema_esperado: dict) -> bool:
    campos_obrigatorios = schema_esperado.get("required", [])
    for campo in campos_obrigatorios:
        if campo not in output:
            return False
    return True

# Timeout por agente (evita que um agente trave o squad)
import asyncio

async def executar_com_timeout(agente_fn, input, timeout_segundos=60):
    try:
        return await asyncio.wait_for(agente_fn(input), timeout=timeout_segundos)
    except asyncio.TimeoutError:
        return {"status": "timeout", "error": "Agente excedeu o tempo limite"}

# Retry com backoff exponencial
import time

def executar_com_retry(agente_fn, input, max_tentativas=3):
    for tentativa in range(max_tentativas):
        try:
            return agente_fn(input)
        except Exception as e:
            if tentativa == max_tentativas - 1:
                raise
            time.sleep(2 ** tentativa)
```

---

## Exemplos de Squads Prontos

### Squad de Pesquisa e Relatório

```
Tarefa: "Pesquise X e produza um relatório executivo"

Orquestrador
├── Agente Buscador      → busca fontes na web
├── Agente Leitor        → lê e extrai conteúdo das fontes
├── Agente Sintetizador  → consolida os achados
└── Agente Escritor      → formata o relatório final
```

### Squad de Code Review Autônomo

```
Tarefa: "Revise o PR #42"

Orquestrador
├── Agente Segurança     → analisa vulnerabilidades
├── Agente Performance   → analisa gargalos e complexidade
├── Agente Estilo        → verifica convenções e legibilidade
└── Agente Consolidador  → unifica os comentários e prioriza
```

### Squad de Desenvolvimento TDD

```
Tarefa: "Implemente a feature X"

Orquestrador
├── Agente Arquiteto     → desenha a solução
├── Agente Testador      → escreve os testes primeiro
├── Agente Desenvolvedor → implementa para os testes passarem
└── Agente Revisor       → revisa e pede ajustes se necessário
    └── (loop volta pro Desenvolvedor se não aprovado)
```

---

## Boas Práticas

### Do (Faça)

- **Minimize o contexto compartilhado** — agentes devem operar com o mínimo de informação necessária (princípio do menor privilégio)
- **Use outputs imutáveis** — cada agente produz um resultado, nunca modifica o input
- **Falha rápida** — se um agente falhar, o orquestrador deve detectar imediatamente e decidir: retry, fallback ou abort
- **Logs estruturados** — registre cada chamada de agente com ID, timestamps e tokens consumidos
- **Idempotência** — agentes devem poder ser re-executados com o mesmo input e produzir o mesmo output
- **Paralelize quando possível** — tarefas independentes em paralelo reduzem latência drasticamente

### Don't (Evite)

- **Estado compartilhado mutável** entre agentes sem controle de concorrência
- **Agentes que chamam agentes sem o orquestrador saber** — isso cria loops ocultos
- **Prompts genéricos** — cada agente precisa de um system prompt focado em seu papel específico
- **Confiar cegamente no output de outro agente** — sempre valide antes de usar
- **Squads maiores que o necessário** — 3-5 agentes bem definidos batem um squad de 10 vagos

---

## Template de System Prompt por Papel

### Orquestrador

```
Você é o orquestrador de um squad multi-agente.
Sua única responsabilidade é: receber a tarefa, decompô-la em subtarefas,
delegar para os agentes corretos, validar os resultados e sintetizar a resposta final.
Você NÃO executa subtarefas diretamente. Você coordena.
Formato de output: JSON com campos [plano, delegacoes, sintese].
```

### Agente Especialista

```
Você é um agente especializado em [DOMÍNIO].
Sua única responsabilidade é: [UMA FRASE CLARA].
Você recebe como input: [FORMATO DE INPUT].
Você produz como output: [FORMATO DE OUTPUT EXATO].
Você NÃO deve: [LISTA DE RESTRIÇÕES].
Se o input for inválido ou insuficiente, retorne status "error" com descrição do problema.
```

---

## Checklist de Lançamento de um Squad

Antes de colocar em produção:

- [ ] Cada agente tem papel único e bem definido?
- [ ] O orquestrador conhece todos os agentes e seus contratos de input/output?
- [ ] Há timeout configurado para cada agente?
- [ ] Há retry com backoff para falhas transitórias?
- [ ] Os outputs de agentes são validados antes de serem usados?
- [ ] O squad tem logs suficientes para debugar uma falha em produção?
- [ ] Tarefas independentes estão sendo executadas em paralelo?
- [ ] O custo máximo (tokens) por execução foi estimado e é aceitável?
- [ ] Há um mecanismo de abort se o squad entrar em loop?
- [ ] Você testou o caso de um agente retornar output inválido?

---

## Referências

- [Claude Agent SDK — Documentação Oficial](https://docs.anthropic.com/en/docs/agents)
- [Building effective agents — Anthropic](https://www.anthropic.com/research/building-effective-agents)
- [Multi-agent patterns — Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook)
