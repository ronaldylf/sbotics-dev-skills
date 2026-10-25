---
name: sbotics-robots
description: >
  Módulo especializado para inspecionar, descriptografar, modelar, validar e gerar arquivos de robôs (.sBot) para a plataforma sBotics. Use quando o usuário mencionar '.sbot', 'sbot', 'robô sbotics', 'criar robô', 'gerar robô', 'modificar robô', 'descriptografar robô' ou 'peças do robô'.
license: MIT
metadata:
  author: ronaldylf
  version: "0.1.0"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
  - Bash(mkdir:*)
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(ls:*)
  - Bash(cat:*)
---

# sBotics Robots — Módulo de Manipulação e Criação de Robôs (.sBot)

Esta skill é um submódulo dedicado **exclusivamente aos robôs da plataforma sBotics** (arquivos `.sBot`). Ela não cobre a criação de arenas ou escrita de código de simulação, focando 100% em:
1. Descriptografar e inspecionar a anatomia de arquivos `.sBot`.
2. Modelar novos robôs ou editar robôs existentes em formato JSON.
3. Validar a consistência física, limites da grade e integridade de juntas (`anchor`).
4. Criptografar e assinar o robô gerando um `.sBot` válido para o simulador.

## Entradas

- `$action`: Ação desejada (`decrypt`, `encrypt`, `validate`, `generate`, `info`).
- `$input_file`: Caminho para o arquivo `.sBot` ou `.json`.
- `$output_file`: Caminho de saída desejado.
- `$robot_name`: Nome de identificação do robô na simulação.

## Objetivo

Gerenciar o ciclo de vida completo de arquivos de robôs (`.sBot`):
- Permitir engenharia reversa e inspeção de robôs existentes.
- Garantir que qualquer robô gerado programaticamente respeite as regras físicas da engine Unity do sBotics.
- Produzir arquivos binários/criptografados `.sBot` com assinatura HMAC íntegra.

---

## Contexto da Plataforma sBotics

O **sBotics** é um simulador de robótica educacional 3D (construído em **Unity** e originado no ecossistema **Weduc / Natalnet - UFRN**) utilizado oficialmente em treinamentos e etapas virtuais da **OBR (Olimpíada Brasileira de Robótica)**, simulando o desafio internacional *RoboCupJunior Rescue Line* (Resgate de Vítimas).

Os robôs criados na **Oficina de Robôs** (arquivos `.sBot`) são submetidos à física em tempo real (gravidade, centro de massa, atrito de rodas e colisões de juntas rígidas `Rigidbody`/`Joint`) e controlados via código em **Blockeduc** (blocos), **rEduc** ou **C#**. Por isso, a arquitetura física do robô deve ser projetada em função dos desafios da arena:

1. **Percurso de Linha e Encruzilhadas (Marcadores Verdes):**
   - O robô segue uma linha preta sobre ladrilhos brancos, enfrentando curvas de 90°, cruzamentos, becos sem saída (dois verdes) e *gaps* (falhas na linha).
   - Pequenos quadrados verdes antes das intersecções indicam para qual lado o robô deve convergir.
   - **Impacto no Projeto:** Exige sensores de cor (`ColorSensor`) voltados para o chão na dianteira. Robôs iniciantes usam 2 sensores; robôs competitivos usam de **4 a 5 sensores alinhados** para ler simultaneamente a linha central, bordas de curvas de 90° e marcadores verdes sem perder o alinhamento.
2. **Obstáculos, Redutores de Velocidade, Gangorras e Rampas:**
   - Obstáculos sólidos bloqueiam a linha e exigem detecção frontal e acompanhamento lateral para contorná-los.
   - Lombadas (redutores), gangorras e rampas íngremes alteram a inclinação do chassi, podendo fazer o robô empinar, raspar no chão ou perder a leitura dos sensores de cor.
   - **Impacto no Projeto:** Tração **4x4 (4WD)** oferece maior torque em subidas; o posicionamento de rodinhas auxiliares livres (`Hinge` + `SmallWheel`) nas extremidades dianteira/traseira evita que o robô empine ou trave nas transições de rampa.
3. **Sala de Resgate (Zona de Vítimas):**
   - No final da pista, o robô entra em uma sala cercada por paredes para localizar **vítimas** (esferas prateadas = vivas; esferas pretas = mortas) e depositá-las na **área de evacuação** (triângulo nos cantos da sala).
   - **Impacto no Projeto:** Requer sensores ultrassônicos em **duas alturas diferentes** (um nível baixo para detectar vítimas/bolinhas e um nível alto para enxergar apenas paredes), sensores de cor frontais para distinguir o tipo de vítima/área de resgate, e mecanismos ativos (`Servomotor` acoplado a cunhas `Wedge`) formando **garras frontais** e/ou **caçambas coletoras**.

---

## Catálogo de Templates e Análise dos Robôs Padrão (`<skill-dir>/templates/`)

A pasta `<skill-dir>/templates/` contém o template mínimo (`basic_robot.json`) e os **4 robôs padrões oficiais da plataforma sBotics** decodificados (`Trekker.json`, `Bruna.json`, `Boryszin.json`, `Obsidian.json`). Utilize esta análise para recomendar, selecionar como base ou inspirar a geração de um novo robô conforme o perfil do usuário:

| Template | Blocos (+1 Core) | Peso Total (`Zg`) | Centro de Massa $(X, Y, Z)$ | Dimensões $(X \times Y \times Z)$ | Tração e Apoio | Sensores | Atuadores Extras / Destaques | Perfil de Uso Ideal |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| **[`basic_robot.json`](templates/basic_robot.json)** | 8 | `12.00 Zg` | `(0.00, -0.08, +0.25)` | $5 \times 2 \times 4$ | 2WD (`motor_left`, `motor_right`) | 1 Cor (`color_ground`), 1 Ultra (`ultra_front`) | Chassi mínimo esquelético | Esqueleto mínimo para testes rápidos de script/validação. |
| **[`Trekker.json`](templates/Trekker.json)** | 22 | `24.75 Zg` | `(0.00, +0.21, +0.08)` | $7 \times 2 \times 5$ | 2WD frontal (`l`, `r`) + 1 roda boba traseira | 2 Cor (`lc`, `rc`) | 1 LED (`led`) | **Iniciante / Didático:** Seguidor de linha clássico de 2 sensores, ideal para primeiros passos em Blockeduc/rEduc. |
| **[`Bruna.json`](templates/Bruna.json)** | 71 | `67.50 Zg` | `(-0.50, +0.70, -1.47)` | $6 \times 3 \times 8$ | 4WD (`frontLeftMotor`, `frontRightMotor`, `leftMotor`, `rightMotor`) + 4 `SmallWheel` com `Hinge` | 4 Cor (`S0`–`S3`), 4 Ultra (`centerUltra0/1`, `leftUltra`, `rightUltra`) | 10 LEDs (`L01`–`L23`), 2 Buzzers (`B0`, `B1`) | **Intermediário (Pista Completa sem Garra):** Excelente estabilidade em rampas/redutores, linha com 4 sensores, desvio de obstáculos e rico feedback visual/sonoro. |
| **[`Boryszin.json`](templates/Boryszin.json)** | 58 | `60.25 Zg` | `(+0.49, -0.01, -1.04)` | $6 \times 5 \times 7$ | 4WD rebaixado em $y=-1$ (`E`, `D`, `E2`, `D2`) + rodinhas frontais com `Hinge` | 6 Cor (`CCE`, `CE`, `CD`, `CCD`, `CF`, `CT`), 9 Ultra (360° em 2 níveis), 1 Toque (`TF`) | 5 Servos de mecanismo (`G`, `G2`, `T`, `V1`, `a`) | **Avançado Compacto / Ágil:** Altíssima densidade de sensores (9 ultrassônicos em dois andares) e múltiplos atuadores em chassi curto e centro de gravidade baixo. |
| **[`Obsidian.json`](templates/Obsidian.json)** | 93 | `82.50 Zg` | `(-0.01, +1.39, +0.42)` | $7 \times 6 \times 10$ | 4WD (`leftMotor`, `rightMotor`, `backLeftMotor`, `backRightMotor`) | 9 Cor (5 de linha `colorLL`–`colorRR`, 2 frontais, 2 na caçamba), 7 Ultra, 3 Toque traseiros | Garra articulada (`arm`, `hand`) + Caçamba traseira (`bag`) | **Competição Full-Spec (Resgate Completo):** Arquitetura pesada com garra dupla frontal, caçamba elevatória com sensores próprios e *bumper* traseiro de toque. |

### Detalhamento Arquitetural de Cada Robô Padrão

#### 1. `Trekker` — O Triciclo Didático
- **Estrutura e Mecânica:** Chassi leve (22 peças) em formato triciclo. Duas rodas grandes dianteiras tracionadas (`l` em `(-2,0,1)` e `r` em `(2,0,1)`) e uma `LargeWheel` traseira central sem motor em `(0,0,-2)` atuando como roda de apoio.
- **Sensoriamento:** Apenas 2 sensores de cor frontais voltados ao solo (`lc` em `(-1,0,2)` e `rc` em `(1,0,2)`) espaçados por 1 bloco vazio no meio (`x=0`), permitindo enquadrar a linha preta entre eles. Possui um indicador luminoso (`led`) no topo.
- **Quando usar como base:** Quando o usuário quiser um robô simples, leve, fácil de programar do zero, focado apenas em seguir linha básica ou aprender controle proporcional/condicional sem lidar com dezenas de portas.

#### 2. `Bruna` — Plataforma 4x4 Estável com Painel de Diagnóstico
- **Estrutura e Mecânica:** Chassi robusto de 71 peças com tração 4x4 (`frontLeftMotor`, `frontRightMotor`, `leftMotor`, `rightMotor`). Seu diferencial mecânico são os **4 conjuntos de `Hinge` + `SmallWheel`** montados nas extremidades dianteira (`z=2`) e traseira (`z=-5`), que funcionam como rodízios anti-impacto para subir e descer rampas ou passar por redutores sem travar o chassi.
- **Sensoriamento e Feedback:** Matriz linear contínua de 4 sensores de cor no chão (`S0`, `S1`, `S2`, `S3` de `x=-2` a `x=1`), 2 ultrassônicos frontais elevados (`centerUltra0`, `centerUltra1`) e 2 ultrassônicos laterais (`leftUltra`, `rightUltra`). Conta ainda com 10 LEDs no teto (`L01` a `L23`) e 2 buzzers (`B0`, `B1`) para depuração visual de estados do código.
- **Quando usar como base:** Quando o usuário precisar vencer toda a pista inferior/superior (linha complexa, verde, obstáculos e rampas) com máxima estabilidade física e feedback visual, mas ainda não precisar de garra mecânica para coletar vítimas.

#### 3. `Boryszin` — Caçador Compacto com Sensoriamento 360° em Duas Alturas
- **Estrutura e Mecânica:** Projeto de competição compacto (58 peças) construído com **chassi rebaixado em `y = -1`** (`SpawnHeight = 0.90`), mantendo o centro de massa muito baixo. Tração 4x4 (`E`, `D`, `E2`, `D2`) auxiliada por dobradiças (`Hinge`) e rodas pequenas frontais.
- **Sensoriamento e Atuadores:** Impressionantes **9 sensores ultrassônicos** distribuídos na frente (`UF`, `UFC`), nas laterais superiores (`UE`, `UD`), laterais inferiores (`UEB`, `UDB`) e traseira (`UT`, `UT2`, `UTC`) — permitindo diferenciar perfeitamente paredes (lidas em cima e embaixo) de vítimas/obstáculos baixos (lidos apenas embaixo). Possui 4 sensores de cor de linha (`CCE`, `CE`, `CD`, `CCD`), sensor de cor frontal (`CF`), sensor de cor superior (`CT`), sensor de toque (`TF`) e 5 servomotores auxiliares (`G`, `G2`, `T`, `V1`, `a`) para manipulação.
- **Quando usar como base:** Quando o usuário buscar um robô de competição ágil, compacto para girar dentro da sala de resgate sem colidir nas paredes e com leitura espacial completa em duas alturas.

#### 4. `Obsidian` — Especialista "Full-Spec" em Sala de Resgate (Garra + Caçamba)
- **Estrutura e Mecânica:** O maior e mais complexo dos robôs padrões (93 peças, estendendo-se de `Z=-3` até `Z=6` e altura até `Y=5`). Totalmente simétrico no eixo X (`[-3, 3]`) com tração 4x4 (`leftMotor`, `rightMotor`, `backLeftMotor`, `backRightMotor`).
- **Sistema de Coleta e Despejo:**
  - **Frente (`Z=3` a `Z=6`):** Braço articulado acionado pelo servo `arm` `(0,3,3)` e garra acionada pelo servo `hand` `(-1,1,4)`, construída com rampas `Wedge` que canalizam e prendem as vítimas.
  - **Topo/Traseira (`Y=2` a `Y=5`):** Compartimento/caçamba basculante controlado pelo servo `bag` `(0,2,-2)` cercado por `Wedge`s, capaz de armazenar múltiplas vítimas e despejá-las na área de resgate.
- **Sensoriamento Especializado:**
  - **Linha (5 sensores):** `colorLL`, `colorLeft`, `colorMiddle`, `colorRight`, `colorRR` (`x = -2` a `2`), garantindo cobertura total em qualquer ângulo de ataque.
  - **Frente e Garra:** Sensores de cor frontais (`frontLeft`, `frontRight`) e ultrassônicos em múltiplos níveis (`ultraDown`, `ultraMid`, `ultraMidRight`, `ultraBag`).
  - **Caçamba e Ré:** Sensores de cor internos na caçamba (`bagColorL`, `bagColorR`), ultrassônico traseiro (`ultraBack`) e **parachoque traseiro com 3 sensores de toque** (`touchLeft`, `touchMid`, `touchRight` em `z=-3`) para alinhar perfeitamente de ré contra a parede ou área de evacuação antes de acionar o servo `bag`.
- **Quando usar como base:** Quando o usuário quiser um robô de alto nível focado em pontuação máxima na Sala de Resgate (captura com garra articulada, armazenamento em caçamba e alinhamento de ré por toque).

### Guia de Decisão para Geração de Robôs
Ao receber um pedido para criar ou customizar um robô, utilize estas diretrizes:
1. **Iniciante / Seguidor de Linha Simples:** Parta do template `Trekker` (ou `basic_robot`) — mantenha 2 motores e 2 a 3 sensores de cor, sem garras pesadas que alterem o centro de gravidade.
2. **Foco em Pista Difícil / Rampas / Obstáculos (Sem Resgate):** Parta do template `Bruna` — use tração 4x4, 4 sensores de cor na base, ultrassônicos frontais/laterais e rodinhas auxiliares (`Hinge` + `SmallWheel`) nas pontas.
3. **Competição Ágil / Varredura por Ultrassom Duplo:** Parta do template `Boryszin` — posicione pares de sensores ultrassônicos em alturas distintas ($y=-1$ e $y=0$ ou $y=0$ e $y=2$) para separar leituras de vítimas (esferas baixas) das paredes da arena.
4. **Resgate Avançado de Múltiplas Vítimas:** Parta do template `Obsidian` — combine linha de 5 sensores de cor, garra frontal de 2 graus de liberdade (`arm` + `hand`), caçamba superior (`bag`) e sensores de toque traseiros para alinhamento na área de resgate.

## Passos de Execução

> [!NOTE]
> **Resolução de `<skill-dir>`:** O identificador `<skill-dir>` nos comandos abaixo representa a pasta onde este arquivo `SKILL.md` reside (seja no repositório local em `skills/sbotics-robots`, seja instalado no harness do usuário como `~/.gemini/antigravity-cli/skills/sbotics-robots` ou `~/.claude/skills/sbotics-robots`). Substitua `<skill-dir>` pelo caminho real do diretório desta skill.

### 1. Inspecionar ou Descriptografar Robô (`decrypt` / `info`)
Para extrair a estrutura, lista de peças ou nomes de sensores de um robô existente:
- Executa a descriptografia AES-256-CBC com verificação do hash HMAC-SHA256 usando a chave oficial:
  `JCZWRVPvlhQ0iSkIIxqeRyE6TFWHg6f2qP1tbK0del8=`
- Decodifica o Base64 e produz o arquivo JSON legível.

Comandos:
```bash
# Ver resumo e contagem de peças
python <skill-dir>/scripts/sbotics.py info -i "Caminho/Robo.sBot"

# Descriptografar para JSON editável
python <skill-dir>/scripts/sbotics.py decrypt -i "Caminho/Robo.sBot" -o "Caminho/Robo.json"
```

**Critério de sucesso**: Obter um arquivo JSON válido contendo `name` e a lista `blocks`, com HMAC validado sem erros.

### 2. Modelar ou Gerar Estrutura do Robô (`generate`)
Ao criar um novo robô ou editar um chassi:

> [!IMPORTANT]
> **Liberdade de Montagem:** Sensores, atuadores e blocos podem ser posicionados em **qualquer lugar e em qualquer orientação** (frente, laterais, traseira, para cima ou para baixo, garras de resgate, etc.), de acordo com a estratégia do robô (seguidor de linha, desvio de obstáculos, rampa, sala de resgate).

Ao posicionar qualquer peça, atente-se às seguintes diretrizes:
- **Origem (0, 0, 0) é exclusiva do Core:** NUNCA coloque blocos em `position = {x: 0, y: 0, z: 0}`. Essa posição é instanciada automaticamente pelo simulador para o "Core" (`RobotController`). Peças centrais devem ficar adjacentes (ex: `z: 1`, `z: -1`, `x: 1`, `x: -1`) e usar `"anchor": {x: 0, y: 0, z: 0}`.
- **Estrutura e Chassi:** Adicione blocos estruturais (`Cube`, `Wedge`, `Slab`, `Corner`).
- **Atuadores e Rodas:** Posicione servomotores (`Servomotor`, `Hinge`) e rodas (`SmallWheel`, `LargeWheel`).
- **Sensores:** Posicione `ColorSensor`, `UltrasonicSensor`, `TouchSensor`, `Camera`, atribuindo nomes descritivos e únicos (ex: `"ultra_frente"`, `"ultra_lateral_dir"`, `"cor_resgate"`, `"toque_garra"`).
- **Âncoras Físicas (`anchor`):** Toda peça adicionada precisa apontar seu `"anchor"` para as coordenadas do bloco pai ao qual está fisicamente conectada, garantindo a árvore de juntas rígidas da física Unity.

Comando para gerar robô base a partir de um dos templates (`basic_robot`, `Trekker`, `Bruna`, `Boryszin` ou `Obsidian`):
```bash
# Gera a partir do template mínimo padrão (basic_robot)
python <skill-dir>/scripts/sbotics.py generate -n "MeuRobo" -o "MeuRobo.json"

# Gera usando um dos robôs padrões oficiais da plataforma como base
python <skill-dir>/scripts/sbotics.py generate -n "MeuRobo" -t "Obsidian" -o "MeuRobo.json"
```

**Critério de sucesso**: Ter uma lista de blocos com coordenadas consistentes e âncoras válidas.

### 3. Validar Regras e Restrições da Plataforma (`validate`)
Antes de compilar, o robô deve passar pelas **regras invioláveis da plataforma**:
1. **Regra do Core:** Nenhum bloco em `{x: 0, y: 0, z: 0}`.
2. **Limites Espaciais:** Coordenadas estritamente dentro de $-8 \le x \le 8$, $-4 \le y \le 12$, $-8 \le z \le 8$.
3. **Catálogo de Peças:** O campo `type` deve ser um dos 18 tipos do catálogo `Placeables`.
4. **Catálogo de Cores:** Se especificada, `color` deve ser um dos 16 materiais de `ObjectMaterials`.
5. **Conectividade de Âncoras:** Todo `anchor` (exceto `0,0,0`) deve coincidir com as coordenadas de uma peça real existente.
6. **Nomes Únicos:** Não pode haver nomes de componentes duplicados no mesmo robô.

Comando:
```bash
python <skill-dir>/scripts/sbotics.py validate -i "Caminho/Robo.json"
```

**Critério de sucesso**: Relatório de validação com 0 erros de limites ou âncoras órfãs.

### 4. Compilar e Assinar o Robô (`encrypt`)
- O JSON validado é criptografado com **AES-256-CBC (PKCS7)** com IV aleatório de 16 bytes.
- Chave oficial estática: `JCZWRVPvlhQ0iSkIIxqeRyE6TFWHg6f2qP1tbK0del8=`
- É calculado o HMAC-SHA256 da concatenação `iv_b64 + value_b64` para garantir a assinatura de integridade aceita pelo sBotics.
- Salvo com extensão `.sBot`.

Comando:
```bash
python <skill-dir>/scripts/sbotics.py encrypt -i "Caminho/Robo.json" -o "Caminho/Robo.sBot"
```

**Critério de sucesso**: Arquivo `.sBot` gerado e testado pelo decodificador, pronto para carregar na simulação.

---

## Referência Técnica Rápida

### Orientações Comuns de Sensores
* **Sensores de Linha / Chão:** `rotation: { x: 0, y: 0, z: 0 }` (a lente aponta naturalmente para o chão).
* **Sensores de Obstáculo / Paredes Dianteiros:** `rotation: { x: 270, y: 0, z: 0 }` (sensor de cor) ou `rotation: { x: 0, y: 0, z: 0 }` (ultrassônico).
* **Sensores Laterais (Direita):** `rotation: { x: 0, y: 90, z: 0 }`.
* **Sensores Laterais (Esquerda):** `rotation: { x: 0, y: 270, z: 0 }`.
* **Sensores Traseiros:** `rotation: { x: 0, y: 180, z: 0 }`.

### Catálogo de Peças e Pesos Físicos (`Placeables` e Massa em `Zg`)
No sBotics, o peso de cada peça não fica salvo no JSON, pois é uma constante física do *Prefab* na Unity (`Rigidbody.mass`, medida em **Zg**). A soma ponderada das posições de cada peça (incluindo o **Core** em `(0,0,0)` que pesa `1.00 Zg`) define o **Centro de Massa (`CoM`)** do robô:

| Peça (`type`) | Peso (`Zg`) | Notas de Equilíbrio e Construção |
| :--- | :---: | :--- |
| **`Servomotor`** | **2.00 Zg** | **Peça mais pesada.** Um servo unilateral (ex: em braço ou garra) exige contrapeso no lado oposto. |
| **`LargeWheel`** | **1.50 Zg** | Roda grande de tração; excelente para manter o centro de gravidade baixo. |
| **Core `(0,0,0)`**, **`Cube`**, **`ColorSensor`**, **`UltrasonicSensor`**, **`TouchSensor`**, **`Camera`**, **`Buzzer`**, **`Pen`** | **1.00 Zg** | Peso unitário padrão (`1 Zg`). Um `Cube` compensa exatamente o peso de qualquer sensor padrão. |
| **`SmallWheel`**, **`Light`** | **0.75 Zg** | Peso intermediário. `SmallWheel` também é usada como contrapeso/apoio em mecanismos articulados (visto em `Obsidian` e `Boryszin`). |
| **`Pyramid`** | **0.66 Zg** | Bloco estrutural piramidal. |
| **`Wedge`**, **`Slab`**, **`WedgeColorSensor`**, **`WedgeUltrasonicSensor`** | **0.50 Zg** | Metade do peso de um cubo. Essenciais para construir garras longas e carenagens sem fazer o robô tombar para frente. |
| **`Corner`** | **0.35 Zg** | Canto chanfrado leve. |
| **`Hinge`** | **0.25 Zg** | Peça mais leve do catálogo (dobradiça passiva). |

### Diretrizes de Balanceamento e Centro de Massa (`CoM`)
1. **Simetria Lateral no Eixo X (`Desvio Lateral ≈ 0.00`):**
   - Robôs de largura **ímpar** (ex: `Trekker` e `Obsidian`, com `X` de `-3` a `+3`) têm o centro das rodas em `X = 0.00`.
   - Robôs de largura **par** (ex: `Bruna` com `X` de `-3` a `+2`, ou `Boryszin` com `X` de `-2` a `+3`) têm o centro das rodas em `X = -0.50` ou `X = +0.50`.
   - O `CoM_x` deve coincidir com o **centro lateral das rodas** (tolerância ideal $|\Delta X| \le 0.05$, limite de alerta no validador $|\Delta X| > 0.25$). Se instalar sensores ou um `Servomotor` (`2.00 Zg`) em uma lateral (como na garra ou caçamba), adicione blocos (`Cube` = `1.00 Zg`, `SmallWheel` = `0.75 Zg` ou `Wedge` = `0.50 Zg`) no lado oposto para zerar o desvio lateral (como faz o `Obsidian` ao compensar 2 sensores de cor na direita da caçamba com 2 `Cube`s vermelhos na esquerda).
2. **Equilíbrio Longitudinal no Eixo Z (Evitar Empinar/Capotar):**
   - O `CoM_z` deve permanecer **estritamente dentro da distância entre-eixos das rodas** (`[wheel_min_z, wheel_max_z]`).
   - Ao projetar garras frontais extensas (ex: `Z = 3` a `6`), construa os dedos da garra com `Wedge` ou `Slab` (`0.50 Zg`) em vez de `Cube` (`1.00 Zg`), e posicione estruturas pesadas (como caçamba ou bateria de cubos) da metade para trás do chassi.

### Catálogo de Cores (`ObjectMaterials`)
`ColorWhite`, `ColorGray`, `ColorDarkGray`, `ColorBlack`, `ColorGreen`, `ColorLime`, `ColorTeal`, `ColorCyan`, `ColorBlue`, `ColorPurple`, `ColorMagenta`, `ColorPink`, `ColorRed`, `ColorBrown`, `ColorOrange`, `ColorYellow`.

### Regras Mandatórias da Plataforma
- **Core Fixo:** A coordenada `(0, 0, 0)` é o ponto de ancoragem do Core e não aceita peças sobrepostas.
- **Grid de Construção:** Limites máximos $[-8, 8] \times [-4, 12] \times [-8, 8]$.
- **Fórmula de Spawn:** $\text{SpawnHeight} = 0.3 + (-\text{minY} \times 0.6)$
- **Ligação física:** Blocos adjacentes conectados pelo vetor `"anchor"` geram `Joint.connectedBody`.
