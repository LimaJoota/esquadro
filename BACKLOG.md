# Backlog

Tudo o que falta para o Esquadro ser a melhor skill de desenho para explicar as coisas e apoiar documentos técnicos, nas áreas corporativa, industrial e de engenharia. **O centro é o sketch explicativo** (decisão do dono do projeto em 04/11/2026); o desenho técnico vem como apoio. *Project backlog, kept in Portuguese; translating it is item QUA-08.*

**Prioridade:** P0 próxima versão, P1 logo depois, P2 quando as anteriores estiverem firmes, P3 desejável.

**Marcas:** `NORMA PAGA` o item depende de norma paga, que nunca será reproduzida: aplicam-se as convenções, e o que não tiver fonte aberta vira dúvida registrada em `references/standards.md`. `DÚVIDA` há incerteza conhecida sobre a norma ou a licença.

Cada item traz o que é, por que importa e como saber que está pronto.

## Ordem sugerida

| Versão | Itens |
|---|---|
| v0.2 e v0.3 (feitas) | Chamadas, notas à mão, quadros, cotas livres, ênfase, certo e errado, acabamentos, perspectiva básica, objetos, figuras numeradas, canetas, aquarela, plugin, CI |
| v0.4: sketch melhor | EXP-01, EXP-02, EXP-03, EXP-04, EXP-05, SKE-04, SKE-06, QUA-04, QUA-06 |
| v0.5: documentos | EXP-06, EXP-07, EXP-08, COR-01, COR-04, COR-05, SKE-03, SKE-05, SKE-07, QUA-02, QUA-11 |
| v0.6: técnico de verdade | TEC-01, TEC-03, TEC-06, TEC-08, TEC-11, TEC-12, QUA-01, INT-01, IND-01, IND-03 |
| Depois | Todo o restante |

## Situação das normas brasileiras

Parte das normas citadas com frequência foi substituída entre 2020 e 2022. O mapa em `references/standards.md` veio de material didático, não da ABNT. **Item zero de todo trabalho técnico:** conferir no catálogo da ABNT o que está vigente.

| Citada | Substituída por | Assunto |
|---|---|---|
| NBR 8403 | NBR 16861:2020 | Linhas e escrita |
| NBR 8402 | `DÚVIDA` provavelmente NBR 16861:2020 | Escrita |
| NBR 10067 | NBR 17006:2021 | Projeções, vistas e cortes |
| NBR 10068 | NBR 16752:2020 | Folha |
| NBR 10126 | NBR 17068:2022 | Cotas e tolerâncias |
| NBR 12298 | NBR 17067:2022 | Hachuras |
| NBR 8196 | `DÚVIDA` sem indício de substituição | Escalas |

---

## Sketch explicativo

### EXP-01 · Biblioteca maior de objetos · P0
- **O que é:** válvula, bomba, tanque, tubo, viga, parafuso, ferramenta, computador, máquina, caixa, pallet, empilhadeira, em perspectiva e de lado. Todos desenhados por nós.
- **Por que importa:** explicar depende de ter o objeto à mão. Hoje são 4 objetos e 2 sólidos, e qualquer outro é feito do zero.
- **Pronto quando:** há 40 ou mais objetos, cada um com pontos de ancoragem e teste, e uma folha mostra todos.

### EXP-02 · Colocação automática de chamadas e notas · P0
- **O que é:** dado o alvo, escolher onde vai o marcador ou a nota, em espaço livre e sem cruzar outros líderes.
- **Por que importa:** é o ajuste mais repetido nos exemplos: cada posição foi acertada à mão, olhando a imagem.
- **Pronto quando:** `callout(d, alvo, n)` funciona sem `at`, e um lote de figuras sai sem cruzamento.

### EXP-03 · Mais sólidos e ocultação · P1
- **O que é:** cone, esfera, prisma, tubo curvo e chapa, com ordem de pintura automática.
- **Por que importa:** hoje a ordem é manual, e errar faz um objeto de trás aparecer na frente. Isso também é a base do isométrico de tubulação (IND-04).
- **Pronto quando:** uma cena com 20 sólidos sai certa em qualquer ordem de chamada, por teste de profundidade.

### EXP-04 · Linguagem visual para movimento e força · P1
- **O que é:** setas de força, rotação, fluxo de líquido, calor, vibração e linhas de movimento.
- **Por que importa:** o que mais se explica é o que se move, e o desenho é parado.
- **Pronto quando:** cada um tem função e exemplo, legível em P&B, e o guia diz quando usar.

### EXP-05 · Validador que olha a explicação · P1
- **O que é:** novas regras para líder atravessando objeto, marcador sobre o alvo, notas longas demais, mais de 7 chamadas e chamada sem item na legenda.
- **Por que importa:** esses erros passam hoje. Um líder atravessou a cabeça da pessoa num exemplo e só foi visto na imagem.
- **Pronto quando:** cada regra tem caso que passa e caso que falha, e os exemplos continuam limpos.

### EXP-06 · Modelos de figura para documento · P0
- **O que é:** formatos prontos para manual, procedimento, relatório técnico e proposta, com tamanho, numeração e estilo de legenda consistentes.
- **Por que importa:** o sketch normalmente vive num documento, e o conjunto precisa parecer feito de uma vez.
- **Pronto quando:** um documento de 10 figuras sai com tudo numerado e citado, e um script confere as referências.

### EXP-07 · Conjunto consistente de figuras · P1
- **O que é:** mesma escala visual, mesmos objetos e numeração contínua em várias figuras de um mesmo assunto, como os quadros de um manual.
- **Por que importa:** figuras feitas uma a uma variam de tamanho de letra e de traço.
- **Pronto quando:** um objeto repetido sai igual em todas as figuras, por teste.

### EXP-08 · Do documento ao desenho · P1
- **O que é:** ler um procedimento ou relatório, propor onde uma figura ajuda e qual forma usar, e pedir confirmação antes de desenhar.
- **Por que importa:** muita gente não sabe qual figura pedir, e o trecho difícil do texto é onde a figura vale mais.
- **Pronto quando:** em 10 documentos de teste, a maioria das sugestões é aceita por um leitor.

### EXP-09 · Cores de caneta: vermelho e azul · feito na v0.3
- **O que é:** `ink="red"` e `ink="blue"` nas ferramentas de explicar e `with d.pen(...)` em qualquer traço. Falta conferir em impressora de verdade.
- **Por que importa:** uma cor de destaque aponta o olho, e é como se corrige um desenho à mão.
- **Pronto quando:** uma página impressa em preto e branco continua distinguindo vermelho, azul e lápis.

### EXP-10 · Aquarela · feito na v0.3, básico
- **O que é:** `d.wash()` e `color=` nos sólidos, com borda que vaza e pigmento acumulado, e versão chapada sem filtro. Falta variar a mancha por traço, escorrer e sobrepor com mais naturalidade.
- **Por que importa:** dá um acabamento diferente e separa materiais sem hachura.
- **Pronto quando:** numa comparação cega a mancha é aceita como aquarela, e a versão chapada é testada em Word, PowerPoint e Inkscape.

---

## Técnico

### TEC-01 · Vistas ortográficas alinhadas em 1º diedro · P0 · `NORMA PAGA`
ABNT NBR 17006 (antiga 10067), ISO 128 e ISO 5456-2.
- **O que é:** um conjunto de vistas que nasce de um único modelo paramétrico, com posição calculada e linhas de chamada coerentes entre as vistas.
- **Por que importa:** é o padrão no Brasil. Hoje o usuário posiciona cada vista à mão e pode desalinhar.
- **Pronto quando:** `d.projection(...)` posiciona frontal, superior e laterais; um teste mede o alinhamento; uma peça de exemplo sai com três vistas validadas.

### TEC-02 · Terceiro diedro · P1 · `NORMA PAGA`
ISO 5456-2 e ASME Y14.3.
- **O que é:** o mesmo conjunto de vistas com arranjo e símbolo do 3º diedro.
- **Por que importa:** fornecedores e clientes norte-americanos usam esse método.
- **Pronto quando:** `method="third"` troca o arranjo e o símbolo, com teste que cobre os dois.

### TEC-03 · Perfis de norma para linhas · P0 · `NORMA PAGA`
ABNT NBR 16861 (antiga 8403) e ISO 128-20.
- **O que é:** séries de espessura (0,18 a 2,0), todos os tipos de linha e regras de aplicação em perfis `iso` e `abnt`.
- **Por que importa:** hoje há um único par 0,5/0,25, sem escolha. Folhas grandes pedem outra série.
- **Pronto quando:** o perfil é escolhido na folha, a espessura acompanha o formato, e uma folha de referência mostra todos os tipos conferidos contra a norma comprada (QUA-10).

### TEC-04 · Caligrafia técnica · P1 · `NORMA PAGA` `DÚVIDA`
ISO 3098 e ABNT NBR 16861 (antiga 8402).
- **O que é:** fonte livre de traço único, próxima da escrita normalizada, com alturas e proporções da série. Candidata: osifont; **conferir a licença antes de incluir**.
- **Por que importa:** a Overpass é um substituto. Um desenho com caligrafia correta parece e é mais técnico.
- **Pronto quando:** a fonte tem licença compatível, cobre acentos e símbolos, e as métricas estão em `metrics.json`.

### TEC-05 · Folha completa · P1 · `NORMA PAGA` `DÚVIDA`
ISO 5457, ABNT NBR 16752 (antiga 10068) e NBR 13142 (dobramento).
- **O que é:** zonas de referência, marcas de corte, marcas de dobra para A4, formatos alongados e tabela conferida de margens.
- **Por que importa:** é o que distingue uma folha de arquivo de uma figura com moldura. Há fontes divergentes sobre margens.
- **Pronto quando:** as folhas A0 a A4 passam por regra de script, a divergência entre fontes está resolvida contra a norma, e há exemplo dobrável.

### TEC-06 · Legenda completa e tabela de revisões · P0 · `NORMA PAGA`
ISO 7200 e ABNT NBR 16752 (antiga 10582).
- **O que é:** campos obrigatórios e opcionais, responsável, aprovação, material, massa, tolerância geral, histórico de revisões, logo vetorial.
- **Por que importa:** a legenda atual é mínima, e sem revisão não há controle de documento.
- **Pronto quando:** existem legendas configuráveis, o histórico cresce sem colidir com o desenho, e o validador confere campos obrigatórios por perfil.

### TEC-07 · Escalas e escala gráfica · P1 · `NORMA PAGA`
ISO 5455 e ABNT NBR 8196.
- **O que é:** barra de escala desenhada, séries próprias por área (1:25 na construção) e múltiplas escalas indicadas por vista.
- **Por que importa:** a barra continua certa depois de ampliar ou reduzir a impressão, e é o que mais protege contra medir errado.
- **Pronto quando:** `v.scale_bar()` funciona, a barra confere com a geometria por teste, e as séries são configuráveis por perfil.

### TEC-08 · Cortes completos · P0 · `NORMA PAGA`
ABNT NBR 17006 e ISO 128 (partes de cortes).
- **O que é:** corte total, meio corte, em desvio, parcial, rebatido e removido, com plano e rótulo automáticos, arestas visíveis atrás do plano de corte e seções de peças que não se cortam (eixos, nervuras).
- **Por que importa:** é onde desenho técnico mais erra, e a v0.1 só oferece as peças soltas.
- **Pronto quando:** um exemplo de cada tipo sai de geometria paramétrica; a seta e o rótulo do plano casam com a vista por script.

### TEC-09 · Hachuras por material · P1 · `NORMA PAGA`
ABNT NBR 17067 (antiga 12298) e ISO 128-50.
- **O que é:** biblioteca por material (aço, concreto, madeira, solo, isolante) e angulação automática em peças adjacentes.
- **Por que importa:** o arranjo de peças fica ilegível sem isso, e o material é informação.
- **Pronto quando:** `material="concreto"` funciona, peças vizinhas nunca recebem a mesma hachura por regra de script, e há tabela de referência.

### TEC-10 · Vistas auxiliares, parciais e detalhes · P1 · `NORMA PAGA`
ABNT NBR 17006.
- **O que é:** vista auxiliar em plano inclinado, parcial, interrompida e detalhe ampliado com círculo e rótulo.
- **Por que importa:** faces inclinadas são comuns, e sem isso a cota sai errada.
- **Pronto quando:** a vista auxiliar é projetada por cálculo, e `v.detail()` amplia com recorte de verdade.

### TEC-11 · Cotagem completa · P0 · `NORMA PAGA`
ISO 129-1 e ABNT NBR 17068 (antiga 10126).
- **O que é:** angular, comprimento de arco, ordenadas, base comum, furos em padrão (8× Ø18), chanfros, raios com centro deslocado e cotas de referência.
- **Por que importa:** a v0.1 só tem linear, diâmetro e raio.
- **Pronto quando:** cada tipo tem verificação de valor contra a geometria e aparece numa folha de referência.

### TEC-12 · Arranjo automático de cotas · P0
- **O que é:** organizar fileiras por tamanho, evitar colisão com a geometria e com outras cotas, e sugerir `pad` necessário.
- **Por que importa:** é o trabalho mais repetitivo hoje: ajuste de `offset` e `pad` a cada desenho. Foi o que mais apareceu nos testes.
- **Pronto quando:** dezenas de cotas numa peça saem sem colisão e sem cruzar linhas de chamada, medido em lote por script.

### TEC-13 · Tolerâncias dimensionais · P1 · `NORMA PAGA`
ISO 286, ISO 2768 e ABNT NBR 17068.
- **O que é:** valores com ±, limites, ajustes (H7/g6) com cálculo das folgas, e nota de tolerância geral.
- **Por que importa:** sem tolerância o desenho não fabrica nada.
- **Pronto quando:** as tabelas usadas têm origem registrada e licença clara, e `tol=` funciona com teste nos casos de ajuste. **Atenção:** tabelas numéricas de norma têm restrição; registrar a dúvida antes de embutir.

### TEC-14 · GD&T · P1 · `NORMA PAGA`
ISO 1101 e ASME Y14.5.
- **O que é:** quadro de tolerância, referências (datum), todos os símbolos geométricos e modificadores.
- **Por que importa:** é o que engenheiro mecânico e controle de qualidade esperam de um desenho de fabricação.
- **Pronto quando:** `v.gdt(...)` desenha o quadro, os símbolos estão em vetor próprio, e combinações inválidas são recusadas.

### TEC-15 · Rugosidade e acabamento · P2 · `NORMA PAGA` `DÚVIDA`
ISO 21920 (que substituiu a ISO 1302) e ABNT NBR 8404.
- **O que é:** símbolos de textura de superfície, com parâmetros e direção.
- **Por que importa:** é informação de fabricação. Há troca recente de norma, então a representação precisa de conferência.
- **Pronto quando:** o símbolo sai nos dois perfis, e a dúvida sobre a edição vigente está resolvida.

### TEC-16 · Símbolos de solda · P2 · `NORMA PAGA`
ISO 2553 e AWS A2.4.
- **O que é:** seta, linha de referência e símbolos de junta, com as diferenças entre os dois sistemas.
- **Por que importa:** é essencial para caldeiraria e estrutura, e confundir os sistemas muda o lado da solda.
- **Pronto quando:** ambos os sistemas existem com aviso explícito na legenda, e uma folha de casos foi revisada por soldador ou inspetor.

### TEC-17 · Elementos de máquina · P2 · `NORMA PAGA`
Série ISO 6410 (roscas) e outras.
- **O que é:** roscas, parafusos, engrenagens, rolamentos, molas e chavetas em representação simplificada.
- **Por que importa:** evita desenhar cada elemento do zero.
- **Pronto quando:** cada elemento é paramétrico e tem exemplo e teste.

### TEC-18 · Lista de materiais e balões · P1 · `NORMA PAGA`
ISO 6433 e ISO 7573.
- **O que é:** posição numerada em balão, tabela que soma quantidade e massa, sincronizadas com o desenho.
- **Por que importa:** todo conjunto precisa disso, e a tabela manual costuma divergir do desenho.
- **Pronto quando:** cada balão tem uma linha na tabela e vice-versa, por regra do validador.

---

## Industrial

### IND-01 · Biblioteca P&ID · P0 · `NORMA PAGA` `DÚVIDA`
ISA-5.1 e ISO 10628-2.
- **O que é:** válvulas, bombas, trocadores, vasos e instrumentos, com tipos de sinal e de letra. Símbolos desenhados por nós.
- **Por que importa:** é o pedido industrial mais comum, e a v0.1 tem só 6 símbolos simplificados.
- **Pronto quando:** há 80 ou mais símbolos com origem registrada e conferidos contra a norma comprada (QUA-10). Pacotes de terceiros só com licença livre (QUA-07).

### IND-02 · Numeração de linhas e lista de equipamentos · P1
- **O que é:** identificação de linha (diâmetro, fluido, classe), tags únicos e listas geradas do próprio diagrama.
- **Por que importa:** a lista manual sempre diverge do diagrama.
- **Pronto quando:** um tag repetido é erro, e a lista sai junto do desenho como tabela e CSV.

### IND-03 · Roteamento automático de tubulação · P0
- **O que é:** rotas ortogonais que desviam dos símbolos, salto de linha no cruzamento e validação de sobreposição.
- **Por que importa:** hoje a rota é manual e cruzamentos não são sinalizados. No exemplo o vapor precisou parar antes do sinal.
- **Pronto quando:** um diagrama de 30 equipamentos sai sem linha sobre símbolo, com todos os cruzamentos marcados por salto.

### IND-04 · Isométricos de tubulação · P1 · `NORMA PAGA`
ISO 6412.
- **O que é:** isométrico de linha com curvas, flanges, cotas por trecho e lista de materiais.
- **Por que importa:** é o documento de quem fabrica e monta tubulação. A projeção isométrica (SKE-02) é a base.
- **Pronto quando:** de uma lista de pontos sai o isométrico com comprimentos conferidos por soma, e a lista de materiais.

### IND-05 · Arranjo de planta · P2
- **O que é:** eixos, projeção de equipamento, áreas de manutenção e circulação.
- **Por que importa:** decisões de arranjo são tomadas em reunião, sobre um desenho assim.
- **Pronto quando:** uma folha de arranjo com eixos cotados sai de uma tabela e o script aponta invasão de áreas livres.

### IND-06 · Pneumática e hidráulica · P1 · `NORMA PAGA`
ISO 1219.
- **O que é:** válvulas direcionais, atuadores, reguladores, bombas e circuitos.
- **Por que importa:** todo equipamento industrial tem, e é um desenho que manutenção usa de verdade.
- **Pronto quando:** há biblioteca conferida e um circuito de exemplo com sequência de acionamento.

### IND-07 · Esquemas elétricos · P1 · `NORMA PAGA` `DÚVIDA`
IEC 60617, IEC 81346 e ABNT NBR 5444.
- **O que é:** unifilar e comando de força com símbolos de planta. **Verificar a situação da NBR 5444**, possivelmente cancelada. Avaliar integrar o schemdraw (MIT) em vez de refazer.
- **Por que importa:** é pedido frequente.
- **Pronto quando:** um quadro de comando simples sai com referência cruzada e identificação de bornes.

### IND-08 · Estruturas metálicas e de concreto · P2 · `NORMA PAGA`
- **O que é:** perfis por catálogo paramétrico, ligações, armaduras e lista de corte.
- **Por que importa:** a parte de estrutura aparece em vários projetos.
- **Pronto quando:** uma treliça e um pilar saem com lista de corte calculada e soma de massas conferida.

### IND-09 · Arranjo de carga e transporte · P1
- **O que é:** centro de gravidade, carga por eixo, amarração, calços e checagem de limites por regra configurável. Fontes públicas: resoluções do CONTRAN.
- **Por que importa:** é o caso de uso que originou o projeto. Hoje o exemplo só calcula a altura.
- **Pronto quando:** de uma lista de volumes saem o desenho e a tabela de distribuição por eixo, e os limites citam a fonte com data.

### IND-10 · Esquemas de obra e valas · P2
- **O que é:** corte de vala, berço, reaterro, escoramento e taludes com ângulo e volume calculados.
- **Por que importa:** é pedido recorrente em infraestrutura e obras.
- **Pronto quando:** de parâmetros saem o corte cotado e o volume por metro, e há aviso de que segurança da vala depende de projeto (NR-18).

### IND-11 · Segurança de máquinas e NR-12 · P2 · `NORMA PAGA`
NR-12 (pública) e ABNT NBR ISO 13857 (paga).
- **O que é:** proteções, distâncias de segurança, zonas de acesso e sinalização em croquis de máquina.
- **Por que importa:** é exigência legal no Brasil, e o desenho ajuda a mostrar a adequação.
- **Pronto quando:** existem símbolos e modelo de laudo gráfico, sempre com o aviso de que não substitui análise de risco por profissional habilitado.

### IND-12 · Diagrama de blocos com balanço · P1
- **O que é:** fluxograma de blocos com tabela de correntes e balanço de massa e energia conferido.
- **Por que importa:** é o documento de quem define o processo, e o balanço precisa fechar.
- **Pronto quando:** um balanço que não fecha é erro, com tolerância configurável.

### IND-13 · Arquitetura e construção civil · P3 · `NORMA PAGA`
ABNT NBR 6492 ou sucessora.
- **O que é:** planta baixa, cortes, níveis e símbolos civis.
- **Por que importa:** há público, embora não seja o foco.
- **Pronto quando:** um pequeno galpão sai em planta, corte e fachada coerentes.

---

## Corporativo

### COR-01 · Fluxos e BPMN · P1
BPMN 2.0, especificação pública da OMG.
- **O que é:** fluxograma e BPMN com raias, disposição automática e formas conforme a especificação.
- **Por que importa:** é o desenho que empresas mais pedem.
- **Pronto quando:** um processo de 30 passos sai sem cruzamento evitável, e um arquivo exportado abre em ferramenta BPMN.

### COR-02 · Organogramas · P1
- **O que é:** organograma por tabela, com disposição automática, cargos e nomes opcionais.
- **Por que importa:** é pedido recorrente em relatório e apresentação.
- **Pronto quando:** de um CSV sai um organograma de 50 caixas sem colisão.

### COR-03 · Cronogramas · P1
- **O que é:** Gantt e linha do tempo por tabela, com caminho crítico calculado, marcos e dependências.
- **Por que importa:** cronograma à mão erra datas. Aqui a posição vem da data.
- **Pronto quando:** o caminho crítico confere com um caso calculado, e a impressão em P&B distingue as tarefas críticas.

### COR-04 · Identidade visual configurável · P0
- **O que é:** arquivo de tema com fontes, cores, logo vetorial, modelo de legenda e estilos de linha, validado contra impressão em P&B.
- **Por que importa:** toda empresa quer a própria marca, e hoje nada é configurável.
- **Pronto quando:** `Drawing(theme="arquivo.toml")` troca tudo, e o validador avisa quando o tema perde contraste. Temas de exemplo nunca usam marcas reais.

### COR-05 · Modelos de caderno e relatório · P1
- **O que é:** HTML e PDF com capa, numeração de figuras e lista de desenhos, usando regras seguras de quebra de página.
- **Por que importa:** o desenho normalmente vive dentro de um documento.
- **Pronto quando:** um caderno de 20 páginas sai sem página quase vazia, e um script confere a ocupação de cada página.

### COR-06 · Outros diagramas de gestão · P2
- **O que é:** SIPOC, matriz RACI, mapa de fluxo de valor, Ishikawa e 5W2H em forma gráfica.
- **Por que importa:** são comuns em qualidade e melhoria contínua.
- **Pronto quando:** cada um tem função e exemplo próprios.

### COR-07 · Exportação para PowerPoint e Word · P2
- **O que é:** SVG ou PNG inseridos com tamanho correto em `.pptx` e `.docx`.
- **Por que importa:** é onde o desenho costuma terminar. O filtro de tremor provavelmente não sobrevive lá.
- **Pronto quando:** o tutorial está testado nos programas reais, com `wobble="geometry"` como padrão nesse caminho.

---

## Sketch

### SKE-01 · Níveis de acabamento · feito na v0.2, básico
- **O que é:** `finish="napkin"`, `"study"` e `"clean"` já mudam tremor e ultrapassagem. Falta variar peso e hachura.
- **Por que importa:** o mesmo desenho serve a públicos diferentes.
- **Pronto quando:** os três níveis também variam peso e densidade, com folha comparativa.

### SKE-02 · Perspectiva isométrica · feito na v0.2, básico · `NORMA PAGA`
ISO 5456-3.
- **O que é:** `Iso` já faz caixas e cilindros. Falta ocultação (EXP-03), cotas no plano e medidas conferidas.
- **Por que importa:** é o que mais explica uma peça a quem não lê vistas, e é a base do isométrico de tubulação (IND-04).
- **Pronto quando:** medidas no eixo são convertidas certo, com teste, e cotas acompanham o plano do objeto.

### SKE-03 · Perspectiva cônica · P1
- **O que é:** um e dois pontos de fuga, com linhas de construção opcionais.
- **Por que importa:** dá leitura realista a reuniões de projeto.
- **Pronto quando:** paralelas convergem para o ponto calculado por teste, e um galpão sai nos dois modos.

### SKE-04 · Sombreado à mão · P0
- **O que é:** hoje há hachura fixa numa face e sombra manual no chão. Falta hachura de sombra, contra-hachura e pontilhado por direção de luz.
- **Por que importa:** é o que faz um croqui parecer desenho de quem sabe.
- **Pronto quando:** a sombra é função da luz e da geometria, e imprime bem em P&B.

### SKE-05 · Mais fontes manuscritas livres · P1
- **O que é:** escolher entre fontes OFL como Caveat e Kalam, com acentos e dígitos legíveis.
- **Por que importa:** dá variedade. Critério: dígito sem ambiguidade. A Architects Daughter foi rejeitada na v0.1 porque o 1 parece um l.
- **Pronto quando:** `font="caveat"` funciona, com métricas e licença incluídas, e há teste de cobertura de caracteres.

### SKE-06 · Tremor por traço de alta qualidade · P1
- **O que é:** melhorar o modo `geometry` com pressão, passada dupla e variação de espessura, até igualar o filtro aprovado.
- **Por que importa:** o filtro vira imagem no PDF do Chrome, e programas de escritório podem ignorá-lo. Traço calculado é vetor em qualquer lugar.
- **Pronto quando:** numa comparação cega o resultado é aceito como lápis, e pode virar o padrão para PDF.

### SKE-07 · Papéis · P2
- **O que é:** fundo de engenharia, quadriculado e pontilhado, que imprimem claros.
- **Por que importa:** reforça a leitura de croqui e ajuda a estimar proporção.
- **Pronto quando:** `paper="grid"` funciona e o quadriculado pode representar uma escala conhecida.

### SKE-08 · Do croqui ao técnico · P1
- **O que é:** padrão documentado de uma fonte, dois modos, com uma função que recebe qualquer vista.
- **Por que importa:** uma ideia aprovada em croqui vira desenho técnico sem redesenhar.
- **Pronto quando:** todos os exemplos usam o padrão, e o guia mostra o caminho.

---

## Interoperabilidade

### INT-01 · Exportar DXF · P0
- **O que é:** escritor DXF sem dependências, com camadas por tipo de linha, texto e cotas.
- **Por que importa:** quem é de engenharia precisa abrir no CAD, e sem isso o desenho termina no papel.
- **Pronto quando:** o arquivo passa pelo `audit` do ezdxf (MIT) em teste e abre no LibreCAD e no FreeCAD, com as dimensões conferidas.

### INT-02 · Exportar DWG · P2 · `DÚVIDA`
- **O que é:** conversão opcional por ferramenta externa (ODA File Converter, proprietário e gratuito; LibreDWG, GPL). Nunca embutida.
- **Por que importa:** ainda é o formato mais pedido.
- **Pronto quando:** o caminho funciona se a ferramenta estiver instalada e falha com mensagem clara se não estiver. Conferir licenças antes.

### INT-03 · De STEP para desenho · P1
- **O que é:** gerar vistas e cortes de um STEP com remoção de linhas ocultas, pelo CadQuery/OCCT (Apache-2.0, dependência opcional).
- **Por que importa:** a peça já modelada vira desenho cotado.
- **Pronto quando:** um STEP de exemplo vira folha com três vistas validadas, sem CadQuery ser exigido para o uso comum.

### INT-04 · Ponte com o FreeCAD · P2
- **O que é:** ler e enviar páginas TechDraw (LGPL, processo separado).
- **Por que importa:** o FreeCAD é a referência aberta.
- **Pronto quando:** uma página gerada abre no FreeCAD editável e uma página de lá é validada aqui.

### INT-05 · Ponte com o OpenSCAD · P2
- **O que é:** projeção para SVG importada como geometria de vista (GPL, processo separado).
- **Por que importa:** muita gente modela peças simples por script nele.
- **Pronto quando:** um `.scad` vira vista cotável por comando.

### INT-06 · Modelo 3D no próprio script · P2
- **O que é:** descrever um sólido simples em CadQuery e extrair as vistas no mesmo fluxo.
- **Por que importa:** evita vistas inconsistentes entre si, um erro comum do 2D.
- **Pronto quando:** as vistas derivadas do mesmo sólido nunca divergem, em teste com peça conhecida.

### INT-07 · De foto de croqui para desenho limpo · P1
- **O que é:** Claude lê a foto, transcreve a geometria e as cotas, marca o que está ilegível e redesenha.
- **Por que importa:** é como muita engenharia começa de fato: um rabisco no papel.
- **Pronto quando:** 20 fotos de teste têm as cotas transcritas certo em mais de 90% dos casos, e nada ilegível é inventado.

### INT-08 · Importar PDF técnico · P2
- **O que é:** extrair vetor e texto de PDF, calibrar a escala por uma cota conhecida e comparar medidas.
- **Por que importa:** desenhos antigos só existem em PDF.
- **Pronto quando:** de um PDF vetorial sai um SVG validável com medidas conferidas contra as cotas impressas.

### INT-09 · Correção de SVG existente · P2
- **O que é:** além de apontar, propor o movimento de texto em SVG de terceiros.
- **Por que importa:** há muito SVG feito à mão por aí, inclusive por IA.
- **Pronto quando:** `validate.py --fix` resolve casos simples de sobreposição sem mudar geometria, com testes.

### INT-10 · Exportar para ferramentas editáveis · P3
- **O que é:** gerar `.excalidraw` e `.drawio`.
- **Por que importa:** não engenheiros podem ajustar depois.
- **Pronto quando:** o arquivo abre nas duas ferramentas com texto editável.

### INT-11 · PDF vetorial sem navegador · P1
- **O que é:** escritor de PDF próprio ou opcional, com fonte embutida, tamanho correto e sem rasterizar o tremor.
- **Por que importa:** o Chrome rasteriza o filtro, e nem toda máquina tem navegador.
- **Pronto quando:** o PDF tem 0 imagens nos modos técnico e `geometry`, e sai igual sem Chrome instalado.

### INT-12 · Integração com o schemdraw · P2
- **O que é:** usar o schemdraw (MIT) para circuitos e passar o resultado pelo validador.
- **Por que importa:** evita refazer o que já é bom.
- **Pronto quando:** um circuito de exemplo sai em folha com legenda e é validado.

---

## Qualidade

### QUA-01 · Conferência de regras de norma por script · P0 · `NORMA PAGA`
- **O que é:** perfil verifica espessuras, proporção 2:1, alturas de texto, setas, margens, legenda e sequência de escala.
- **Por que importa:** é a diferença em relação a qualquer gerador de diagrama. Conformidade verificável vale mais que aparência.
- **Pronto quando:** cada regra tem um caso que passa e outro que falha, e cita a norma sem reproduzir o texto.

### QUA-02 · Ampliar o validador · P0
- **O que é:** líder cruzando cota ou outro líder já gera aviso desde a v0.2. Faltam folga mínima entre texto e traço, cotas se cruzando, linha de chamada cortando valor, seta sobre seta, tubulação sobre símbolo, e texto sobre hachura sem máscara.
- **Por que importa:** esses erros passaram pelo validador e só foram vistos na imagem. Um rótulo encostado numa tabela é caso real do desenvolvimento.
- **Pronto quando:** esses casos são detectados por teste, e os exemplos continuam limpos.

### QUA-03 · Conferência de somas · P1
- **O que é:** cotas em cadeia conferidas contra a cota total; tabelas conferidas contra o desenho.
- **Por que importa:** é erro de fabricação clássico.
- **Pronto quando:** uma cadeia que não fecha é erro, e há marcação explícita de cota de referência.

### QUA-04 · Avaliação com casos reais · P0
- **O que é:** ampliar `evals/` para 30 ou mais pedidos reais anonimizados, com e sem a skill, medindo acerto, erros de validador e custo. Roda com `claude plugin eval`.
- **Por que importa:** só isso prova que a skill ajuda. A v0.1 não mediu.
- **Pronto quando:** há tabela comparativa publicada, sem nenhum dado de cliente ou empresa, e nova versão só entra se não piorar.

### QUA-05 · Comparação visual · P1
- **O que é:** comparação de PNG contra referência aprovada, com relatório de diferença.
- **Por que importa:** evita mudança acidental, que testes de geometria não veem.
- **Pronto quando:** mudança de 1 traço é detectada no CI, e atualizar a referência é ato explícito.

### QUA-06 · Otimizar a descrição da skill · P0
- **O que é:** rodar a otimização de gatilho do `skill-creator`, com 20 pedidos revisados, incluindo os quase iguais (gráficos, arquitetura de software, ilustração).
- **Por que importa:** não importa ser boa se não for chamada, ou se tomar o lugar da archify ou de gráficos.
- **Pronto quando:** a taxa de acerto no conjunto de teste está registrada.

### QUA-07 · Bibliotecas de símbolos com licença livre · P1 · `DÚVIDA`
- **O que é:** arquivo de origem de cada símbolo: autor, licença e fonte. Antes de usar um pacote de terceiros, conferir a licença; desenho próprio no caso de dúvida.
- **Por que importa:** evita problema de direito autoral num repositório público.
- **Pronto quando:** um teste falha se um símbolo não tem origem registrada.

### QUA-08 · Internacionalização · P1
- **O que é:** espanhol e inglês completos em desenhos e documentação, formatos locais de número e data, e este backlog em inglês.
- **Por que importa:** amplia o público e melhora o uso fora do Brasil.
- **Pronto quando:** `lang="es"` funciona e nenhum texto impresso vem fixo do código.

### QUA-09 · Acessibilidade · P2
- **O que é:** `title` e `desc` gerados com dados relevantes, e descrição textual do desenho.
- **Por que importa:** documentos públicos pedem isso, e também ajuda a busca.
- **Pronto quando:** toda saída tem descrição útil, conferida por leitor de tela.

### QUA-10 · Revisão por profissional com as normas · P1 · `NORMA PAGA`
- **O que é:** um engenheiro com as normas compradas confere folhas de referência e responde às dúvidas registradas.
- **Por que importa:** nada aqui foi conferido contra a norma. Hoje, tudo vem de fonte secundária.
- **Pronto quando:** cada convenção em `standards.md` tem marca de revisão com a edição e a data, sem copiar o conteúdo da norma.

### QUA-11 · Outros renderizadores · P1
- **O que é:** testar Safari, Firefox, Inkscape, resvg, librsvg, LibreOffice, Word e PowerPoint, inclusive impressão real em papel.
- **Por que importa:** a v0.1 só foi testada no Chrome e numa pré-visualização de PDF do macOS. Nada foi impresso.
- **Pronto quando:** há tabela do que funciona em cada um, com o filtro e o `geometry`, e o `render.py` aceita alternativas.

### QUA-12 · Testes com geometria aleatória · P2
- **O que é:** fuzz em dimensões e layouts, buscando erro do validador e colisões.
- **Por que importa:** descobre o que os exemplos bem-comportados não mostram.
- **Pronto quando:** roda no CI com semente registrada, e nenhum erro acontece nos parâmetros válidos.

### QUA-13 · Modo estático mais próximo do real · P2
- **O que é:** aplicar kerning e calibrar a caixa de texto contra o navegador em lote.
- **Por que importa:** no modo sem navegador pode haver falso positivo ou negativo.
- **Pronto quando:** a diferença média de largura entre os dois modos fica abaixo de 1%.

### QUA-14 · Desempenho e tamanho · P2
- **O que é:** agrupar traços de hachura em um único caminho e medir tempo do validador em folhas grandes.
- **Por que importa:** muitos elementos deixam o SVG pesado, e o validador compara todos com todos.
- **Pronto quando:** uma folha A0 com 50 mil traços é validada em menos de 10 s, com tamanho medido.

---

## Distribuição

### DIS-01 · Plugin e marketplace · manifesto feito na v0.3
- **O que é:** o manifesto existe e a instalação foi testada numa configuração isolada. Falta entrar em marketplaces de terceiros. **Só publicar com autorização do dono do repositório.**
- **Por que importa:** é como a maioria vai achar e atualizar.
- **Pronto quando:** `/plugin install` funciona e a skill é carregada.

### DIS-02 · Versões · parte feita na v0.3
- **O que é:** o CHANGELOG já existe. Falta automatizar tags e o pacote `.skill` em cada release.
- **Por que importa:** quem depende precisa saber o que mudou.
- **Pronto quando:** cada tag gera um release com o pacote, e a versão em `SKILL.md` confere por teste.

### DIS-03 · CI · feito na v0.3, a confirmar no primeiro envio
- **O que é:** GitHub Actions com pytest, ruff e black em Linux e macOS, Python 3.10 a 3.14, com Chromium; regera os exemplos e falha se divergirem; varre segredos.
- **Por que importa:** o README declara Python 3.10 ou mais novo, mas a v0.1 só rodou no 3.14 em macOS.
- **Pronto quando:** o selo está verde no README, e um PR que quebra exemplo falha.

### DIS-04 · Guia de contribuição · P1
- **O que é:** CONTRIBUTING, modelos de issue, guia para símbolos e a regra de nunca copiar texto de norma.
- **Por que importa:** bibliotecas de símbolos crescem com contribuição, e a regra precisa estar clara.
- **Pronto quando:** um colaborador externo consegue acrescentar um símbolo seguindo só o guia.

### DIS-05 · Outros agentes · P2
- **O que é:** testar o formato em outros agentes que aceitam skills e documentar a instalação.
- **Por que importa:** amplia o público sem custo no código, que é só Python.
- **Pronto quando:** pelo menos dois agentes têm instruções testadas.

### DIS-06 · Galeria e documentação · P2
- **O que é:** página com galeria, API e guia de cada norma.
- **Por que importa:** README tem limite, e uma galeria vende melhor o que a skill faz.
- **Pronto quando:** a página é gerada do repositório a cada release, sem edição manual.

### DIS-07 · Política de segurança · P2
- **O que é:** SECURITY.md, varredura de dependências de desenvolvimento e revisão do parser diante de SVG hostil.
- **Por que importa:** o validador roda em arquivos de terceiros e abre navegador.
- **Pronto quando:** há fuzz do parser e um processo publicado para reportar falhas.
