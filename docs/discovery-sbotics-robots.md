# Engenharia Reversa do Formato `.sBot` (sBotics)

Documentação técnica completa do formato de arquivos `.sBot`, processo criptográfico, chaves, anatomia dos componentes e instruções de uso.

---

## 1. Visão Geral da Arquitetura

O sBotics é um simulador de robótica educacional construído sobre a engine **Unity** (na arquitetura **Mono / .NET**).

Os arquivos de robôs com extensão `.sBot` são arquivos em formato **JSON** empacotados com criptografia simétrica autenticada. Todo robô pode ser convertido para um JSON legível e, inversamente, qualquer JSON com estrutura válida pode ser compilado de volta para um `.sBot` compatível com a simulação.

---

## 2. Processo Criptográfico

A segurança e integridade dos arquivos `.sBot` é gerenciada internamente pela classe `__sBotics__Crypto` contida no assembly `sBotics.dll`.

### 2.1 Especificações Criptográficas
* **Algoritmo de Cifra:** AES (Rijndael)
* **Tamanho da Chave:** 256 bits (32 bytes)
* **Tamanho do Bloco:** 128 bits (16 bytes)
* **Modo de Operação:** CBC (*Cipher Block Chaining*)
* **Padding:** PKCS7
* **Algoritmo de Autenticação/Integridade:** HMAC-SHA256
* **Chave Estática Compartilhada (Base64):**
  ```text
  JCZWRVPvlhQ0iSkIIxqeRyE6TFWHg6f2qP1tbK0del8=
  ```

---

## 3. Estrutura dos Arquivos

### 3.1 Camada Externa (Arquivo `.sBot` físico)
O arquivo `.sBot` contém um JSON simples de duas propriedades:
```json
{
  "name": "nome_do_robo",
  "data": "<string_base64>"
}
```

### 3.2 Camada Intermediária (Payload Decodificado de `data`)
Ao decodificar a string Base64 do campo `data` em UTF-8, obtém-se o objeto de controle criptográfico:
```json
{
  "iv": "JrGZKeVGgjdIKclAXSKkUA==",
  "value": "PXRUFqUjq1TIVKPiY6MiuXMSLa17JWljTgCtnY0o+...",
  "mac": "aae46a3dab3ca84389c8ff878cf3ac8bdadf524f3618544098ee622c80956fc8"
}
```
* **`iv`**: Vetor de inicialização de 16 bytes em Base64.
* **`value`**: Dados cifrados (ciphertext) em Base64, cujo tamanho em bytes é sempre múltiplo de 16.
* **`mac`**: Hash HMAC-SHA256 calculado sobre a string concatenada `iv + value` em minúsculas (hexadecimal de 64 caracteres).

---

## 4. O Formato Real do Robô (JSON Descriptografado)

Ao descriptografar o conteúdo de `value`, obtém-se o JSON de definição do robô:

```json
{
  "name": "tome",
  "blocks": [
    {
      "type": "UltrasonicSensor",
      "position": { "x": 1, "y": 0, "z": 0 },
      "rotation": { "x": 0, "y": 90, "z": 0 },
      "anchor": { "x": 0, "y": 0, "z": 0 },
      "name": "ultra_right"
    },
    {
      "type": "Cube",
      "position": { "x": 0, "y": 0, "z": 1 },
      "rotation": { "x": 0, "y": 0, "z": 0 },
      "anchor": { "x": 0, "y": 0, "z": 0 },
      "color": "ColorDarkGray"
    }
  ]
}
```

### 4.1 Propriedades de cada Bloco
* **`type`** *(obrigatório)*: Identificador da peça (ver tabela abaixo).
* **`position`** *(obrigatório)*: Vetor `{ "x": float, "y": float, "z": float }` indicando a posição na grade.
* **`rotation`** *(obrigatório)*: Vetor `{ "x": float, "y": float, "z": float }` com ângulos de rotação em graus.
* **`anchor`** *(obrigatório)*: Vetor `{ "x": float, "y": float, "z": float }` com as coordenadas do bloco pai ao qual a junta (*joint/hinge*) está conectada.
* **`name`** *(opcional)*: Nome identificador usado no código C#/REduc para acessar o componente (ex: `ultra_right`, `ultra_left`, `servomotor_1`, `cor_frente`).
* **`color`** *(opcional)*: Nome do material/cor aplicado ao bloco.

---

## 5. Dicionário de Peças e Cores

Extraídos dos tipos enumerados do código-fonte do simulador (`sBotics.enums`):

### 5.1 Tipos de Blocos e Pesos Físicos (`sBotics.enums.Placeables`)
O peso de cada bloco (medido em **Zg** na Oficina de Robôs) não é serializado no JSON do `.sBot`, pois é definido diretamente no `Rigidbody.mass` do *Prefab* correspondente na Unity. O bloco **Core (`RobotController`)** na origem `(0, 0, 0)` possui peso fixo de **`1.00 Zg`**.

| Nome no JSON | Código Interno | Peso (`Zg`) | Descrição |
| :--- | :---: | :---: | :--- |
| `Cube` | 1 | `1.00 Zg` | Cubo estrutural básico |
| `Wedge` | 2 | `0.50 Zg` | Rampa / Cunha |
| `Hinge` | 3 | `0.25 Zg` | Dobradiça passiva |
| `SmallWheel` | 4 | `0.75 Zg` | Roda pequena |
| `LargeWheel` | 5 | `1.50 Zg` | Roda grande |
| `Buzzer` | 6 | `1.00 Zg` | Emissor sonoro |
| `Light` | 7 | `0.75 Zg` | LED / Farol |
| `Servomotor` | 8 | `2.00 Zg` | Servomotor rotacional (peça mais pesada) |
| `ColorSensor` | 9 | `1.00 Zg` | Sensor de cor padrão |
| `UltrasonicSensor` | 10 | `1.00 Zg` | Sensor ultrassônico padrão |
| `TouchSensor` | 11 | `1.00 Zg` | Sensor de toque / fim de curso |
| `Slab` | 12 | `0.50 Zg` | Placa fina (meio bloco) |
| `Camera` | 13 | `1.00 Zg` | Módulo de câmera |
| `Pen` | 14 | `1.00 Zg` | Caneta de traçado |
| `Pyramid` | 15 | `0.66 Zg` | Bloco piramidal |
| `WedgeColorSensor` | 16 | `0.50 Zg` | Sensor de cor integrado em rampa |
| `WedgeUltrasonicSensor` | 17 | `0.50 Zg` | Sensor ultrassônico integrado em rampa |
| `Corner` | 18 | `0.35 Zg` | Canto chanfrado |

### 5.2 Cores e Materiais (`sBotics.enums.ObjectMaterials`)
* `ColorWhite` (Branco)
* `ColorGray` (Cinza claro)
* `ColorDarkGray` (Cinza escuro)
* `ColorBlack` (Preto)
* `ColorGreen` (Verde)
* `ColorLime` (Verde limão)
* `ColorTeal` (Verde-azulado)
* `ColorCyan` (Ciano)
* `ColorBlue` (Azul)
* `ColorPurple` (Roxo)
* `ColorMagenta` (Magenta)
* `ColorPink` (Rosa)
* `ColorRed` (Vermelho)
* `ColorBrown` (Marrom)
* `ColorOrange` (Laranja)
* `ColorYellow` (Amarelo)

---

## 6. Ferramenta CLI Oficial (`sbotics.py`)

A automação completa de validação, inspeção, conversão e compilação é centralizada no script Python:
**`skills/sbotics-robots/scripts/sbotics.py`**

### Comandos da CLI:
```bash
# Descriptografar .sBot para JSON
python skills/sbotics-robots/scripts/sbotics.py decrypt -i "Robo.sBot" -o "Robo.json"

# Criptografar JSON para .sBot
python skills/sbotics-robots/scripts/sbotics.py encrypt -i "Robo.json" -o "Robo.sBot"

# Validar regras e limites (JSON ou .sBot)
python skills/sbotics-robots/scripts/sbotics.py validate -i "Robo.json"

# Ver resumo e contagem de peças
python skills/sbotics-robots/scripts/sbotics.py info -i "Robo.sBot"

# Gerar robô base a partir de template
python skills/sbotics-robots/scripts/sbotics.py generate -n "MeuRobo" -o "MeuRobo.json"
```

---

## 7. Regras de Montagem e Validação da Simulação

Ao analisar os métodos internos de `__sBotics__RobotManager`, foram descobertas as seguintes regras e algoritmos que o simulador aplica ao carregar ou editar um robô:

### 7.1 Limites Espaciais de Construção (`OutOfBounds`)
O simulador define uma caixa delimitadora rígida (*bounding box*) para as coordenadas de cada bloco do robô:

* **Eixo X (Largura):** $-8 \le x \le 8$ (extensão de 17 blocos)
* **Eixo Y (Altura):** $-4 \le y \le 12$ (extensão de 17 blocos)
* **Eixo Z (Comprimento):** $-8 \le z \le 8$ (extensão de 17 blocos)

Se qualquer bloco do robô estiver com coordenada fora desse intervalo, o método `OutOfBounds(Vector3)` retorna `true` e a posição é considerada inválida pelo editor.

### 7.2 Como Funciona o Sistema de Fixação (`anchor`) e Juntas Físicas
O simulador instancia o robô em **duas passagens**:

1. **Primeira Passagem (Geometria e Registro):**
   * Cada bloco é instanciado na sua posição `localPosition` e rotação `localRotation`.
   * Os blocos são mapeados em um dicionário interno indexado por sua posição: `Dictionary<Vector3, GameObject>`.
   * Se o bloco for um componente ativo (Sensor, Motor, Farol, etc.) e tiver o campo `"name"` preenchido, ele é registrado no catálogo de componentes do robô (`RobotController.__sBotics__ComponentDictionary`).
   * É rastreado o valor mínimo do eixo Y (`minY`) entre todos os blocos.

2. **Segunda Passagem (Amarras Físicas / Joints):**
   * O simulador percorre novamente todos os blocos e lê o vetor `"anchor"`.
   * Ele busca se existe outro bloco instanciado na coordenada indicada pelo `anchor`:
     ```csharp
     if (dictionary.ContainsKey(anchor)) {
         joint.connectedBody = dictionary[anchor].GetComponent<Rigidbody>();
     }
     ```
   * **Bloco Raiz:** O bloco central do robô não possui pai; seu `anchor` deve apontar para `{ "x": 0, "y": 0, "z": 0 }` ou para a sua própria coordenada.

### 7.3 Adjacência de Peças (`Adjacents`)
No editor, duas peças são consideradas adjacentes se compartilharem uma face direta na grade (distância de Manhattan igual a 1):
$$\text{round}(|dx| + |dy| + |dz|) \le 1 \quad \text{onde } dx, dy, dz \text{ não são todos nulos.}$$

### 7.4 Cálculo da Altura de Inicialização (`SpawnHeight`)
Para garantir que o robô não comece colidindo ou cravado no chão da arena, o sBotics calcula a altura de *spawn* automaticamente a partir do bloco mais baixo (`minY`):
$$\text{SpawnHeight} = 0.3 + (-\text{minY} \times 0.6)$$
* Se o bloco mais baixo estiver em $y = 0$, o robô nasce a $0.3$ unidades de altura.
* Se o bloco mais baixo estiver em $y = -1$, ele nasce a $0.9$ unidades.

### 7.5 Regra Crítica: O Bloco 'Core' na Origem `(0, 0, 0)`
O simulador instancia o `RobotController` (o "Core") automaticamente na posição `Vector3.zero` antes de iterar sobre os blocos e o adiciona ao dicionário interno:
```csharp
dict.Add(Vector3.zero, Controller.gameObject);
```
* **Comportamento de Erro:** Se o arquivo JSON contiver um bloco com `"position": { "x": 0, "y": 0, "z": 0 }`, a execução da chamada `dict.Add(localPosition, block)` dispara uma exceção imediata do .NET (`System.ArgumentException: An item with the same key has already been added`), abortando o carregamento do robô antes que os blocos restantes sejam criados. Como resultado, **apenas o Core aparece na cena**.
* **Regra Obrigatória:** **Nenhum bloco no JSON pode ter `position = (0, 0, 0)`**. As peças centrais que se ligam ao Core devem ficar em coordenadas adjacentes (ex: `(0, 0, 1)`, `(0, 0, -1)`, `(1, 0, 0)`, `(-1, 0, 0)`) e apontar seu `"anchor"` para `{ "x": 0, "y": 0, "z": 0 }`.

### 7.6 Orientações Padrão de Sensores (`rotation`)
A direção de leitura dos sensores segue a orientação do modelo 3D (prefab) na simulação:

* **Sensor de Cor (`ColorSensor`):**
  * `rotation: { "x": 0, "y": 0, "z": 0 }`: A lente fica na face inferior do bloco, apontada **diretamente para o chão** (configuração padrão para seguidores de linha).
  * `rotation: { "x": 270, "y": 0, "z": 0 }`: Inclina o sensor para a **frente horizontal** (útil para ler cores em paredes ou obstáculos).
* **Sensor Ultrassônico (`UltrasonicSensor`):**
  * `rotation: { "x": 0, "y": 0, "z": 0 }`: Apontado para a **frente** ($+Z$).
  * `rotation: { "x": 0, "y": 90, "z": 0 }`: Apontado para a **direita** ($+X$).
  * `rotation: { "x": 0, "y": 270, "z": 0 }`: Apontado para a **esquerda** ($-X$).

### 7.7 Liberdade de Montagem vs. Regras Mandatórias da Plataforma
A configuração de sensores voltados para o chão foi adotada por se tratar de um robô seguidor de linha. No entanto, o usuário e os geradores têm **liberdade total de montagem**:
* Sensores de cor podem ser colocados na vertical, nas laterais, na traseira ou em braços robóticos (ex: identificar cubos de resgate).
* Sensores ultrassônicos podem ser colocados em qualquer face (laterais para acompanhar paredes, traseiro para ré).
* Servomotores podem ser usados tanto para tração de rodas quanto para juntas móveis (braços, cancelas, garras de resgate).

**As únicas regras que NUNCA podem ser violadas são:**
1. **Regra do Core:** Nenhuma peça na coordenada `(0, 0, 0)`.
2. **Caixa Delimitadora:** Todos os blocos dentro de $[-8, 8] \times [-4, 12] \times [-8, 8]$.
3. **Conexão Física:** Todo bloco deve ter um `anchor` válido apontando para outro bloco existente ou para o Core `(0, 0, 0)`.
4. **Nomes de Componentes:** Nomes de sensores e atuadores devem ser únicos no robô.
5. **Criptografia Oficial:** Chave `JCZWRVPvlhQ0iSkIIxqeRyE6TFWHg6f2qP1tbK0del8=`, AES-256-CBC e assinatura HMAC-SHA256.

---

## 8. Integridade Completa do Esquema (Schema Exhaustion)

A inspeção do bytecode do método de serialização `GetRobotJSON` confirmou que **não existem propriedades ou campos ocultos**. O sBotics lê e persiste exclusivamente:

1. `name` (string): Nome do robô.
2. `blocks` (lista de objetos):
   * `type` (string): Nome exato do enum `Placeables`.
   * `position` ({x, y, z}): Coordenadas relativas do bloco na grade.
   * `rotation` ({x, y, z}): Ângulos de Euler em graus.
   * `anchor` ({x, y, z}): Coordenada do bloco pai ao qual a junta se conecta.
   * `name` (string, opcional): Identificador do componente para uso em código.
   * `color` (string, opcional): Nome do material do enum `ObjectMaterials`.

Qualquer robô construído respeitando essa estrutura e criptografado com o algoritmo documentado na Seção 2 é carregado nativamente pelo simulador sBotics sem erros ou avisos.


