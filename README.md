# Sistema Distribuído para Monitoramento Ambiental Urbano

Projeto acadêmico de Atividades Práticas Supervisionadas (APS) do curso de Ciência da Computação, 2026. A proposta é desenvolver uma aplicação para dispositivo móvel, baseada em sistemas distribuídos, voltada ao gerenciamento de informações ambientais urbanas.

## Objetivo

Planejar e desenvolver uma aplicação que permita organizar informações sobre condições e ocorrências ambientais nas cidades, aplicando conceitos de sistemas distribuídos e tecnologias móveis. A proposta final deverá ser submetida à análise e aprovação da coordenação auxiliar, conforme as orientações da disciplina.

## Escopo proposto

A aplicação poderá contemplar informações relacionadas a:

- poluição do ar e inversão térmica;
- trânsito, incluindo transportes públicos;
- áreas de alagamento e inundação;
- invasões de áreas de mananciais;
- desmatamento;
- outras condições ambientais urbanas definidas pelo grupo.

As funcionalidades específicas, fontes de dados e tecnologias ainda serão definidas pelo grupo. Este repositório registra a proposta inicial; não representa funcionalidades já implementadas.

## Plano de trabalho

1. Definir o problema, a motivação e a proposta a ser submetida à coordenação.
2. Escolher a plataforma móvel e as tecnologias adequadas.
3. Planejar os componentes, módulos e a arquitetura distribuída.
4. Implementar a aplicação, com tratamento de erros e funcionalidades acordadas pelo grupo.
5. Testar e demonstrar o sistema em um dispositivo ou simulador.
6. Documentar as tecnologias, o processo de desenvolvimento, a interdisciplinaridade e os resultados.

## Entregáveis da APS

O trabalho escrito deverá incluir objetivo e motivação, introdução, fundamentos das tecnologias móveis escolhidas, plano de desenvolvimento, estrutura do programa, relatório de código, bibliografia e ficha cronológica de atividades. A apresentação deverá demonstrar a aplicação em funcionamento. Para o documento impresso, a orientação fornecida especifica formato A4, fonte Arial 12, espaçamento 1,5, margens de 2,5 cm e encadernação em espiral.

A formação prevista é de três alunos; grupos com número diferente dependem de aprovação da coordenação auxiliar.

## Aplicação inicial

Este repositório contém um protótipo web responsivo para registrar e consultar ocorrências ambientais e urbanas. A aplicação foi feita com HTML, CSS, JavaScript, Python e SQLite, sem dependências externas:

- a interface funciona no navegador de um computador ou celular;
- o navegador troca dados com uma API HTTP em Python;
- os relatos ficam em um banco SQLite no computador que executa o servidor e são compartilhados entre os clientes que o acessam.

O protótipo permite criar, listar e excluir relatos de poluição do ar, trânsito, alagamento, desmatamento, áreas de manancial e outras ocorrências. Cada relato inclui local, descrição e data. Não inclui mapa, login, localização automática nem verificação da veracidade dos relatos.

## Como executar

Requisito: Python 3.10 ou superior. Não é necessário instalar pacotes.

```powershell
py -3 app.py
```

Abra `http://localhost:8000` no computador. Para demonstrar em um celular conectado à mesma rede Wi-Fi, abra no navegador do celular `http://IP-DO-COMPUTADOR:8000`. O sistema operacional pode pedir autorização para conexões na rede privada.

Os dados são salvos em `data/reports.sqlite3`. O servidor não tem autenticação nem criptografia; use apenas em uma rede confiável e não o exponha diretamente à internet.

## Testes

```powershell
py -3 -m unittest discover -s tests -v
```

## Próximos passos

Confirmar a proposta com a coordenação, definir a equipe e as tecnologias finais, testar em dispositivos, e evoluir o protótipo conforme os requisitos aprovados.
