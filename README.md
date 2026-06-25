# Karate Manager 🥋🏆

O **Karate Manager** é uma aplicação desktop desenvolvida em Python e PyQt6 concebida para simplificar a organização, gestão e exibição de competições de karaté (IRIKUMI/KUMITE). A aplicação suporta tanto torneios **individuais** como em **equipa**, oferecendo um sistema interativo de brackets (chaves de torneio) com suporte a arrastar-e-soltar (drag-and-drop) e uma consola administrativa integrada com ecrã secundário de apresentação para o público e júri.

---

## 🙏 Agradecimentos Especiais

Um agradecimento honorífico e profundo ao **Clube Karate Budo Dojo**. Esta aplicação foi inspirada e moldada pela vivência dentro do dojo. Deixo uma menção especial de gratidão a toda a estrutura, mestres e colegas:
* Pela total **confiança** depositada no meu percurso.
* Pelos **10 anos de treino**, dedicação e ensinamentos valiosos que me proporcionaram, tanto nas artes marciais como para a vida.
* Pelo exigente caminho e conquista do **cinto negro** 🥋, um marco que carrego com imenso orgulho.

*Arigato!*

---

## 🌟 Principais Funcionalidades

### 1. Modos de Competição Flexíveis (Irikumi & Kata)
*   **Irikumi (Individual e Equipas)**:
    *   **Individual**: Combates individuais à melhor de 3 rondas com aviso sonoro aos 15 segundos restantes.
    *   **Equipa (Dojos)**: Equipas formadas por 2, 3 ou 4 atletas. O sistema suporta confrontos assimétricos detetando interativamente a necessidade de repetição de atletas.
*   **Kata (Individual e Equipas)**:
    *   Disputado à melhor de 1 ronda.
    *   No formato por equipa, a equipa entra e compete em simultâneo (sem necessidade de ordenar atletas individuais).
    *   As faltas/advertências e o temporizador encontram-se totalmente desativados e ocultados das janelas e painéis.

### 2. Bracket Dinâmico e Interativo
*   Geração automática de chaves com potências de 2 (suporte a *Byes* automáticos para números ímpares ou incompletos de participantes).
*   Movimentação fluida de atletas e equipas por arrastamento a partir do painel lateral.
*   Tooltips informativos nos nós do bracket que revelam instantaneamente a lista de atletas de cada Dojo ao passar o rato (hover).

### 3. Scoreboard Premium & Apresentação (Dual-Screen)
*   **Ecrã de Apresentação**: Janela desenhada para ser projetada ou exibida num segundo monitor (via HDMI/Projector), totalmente responsiva e livre de botões administrativos.
*   **Controlo Simétrico**: O rodapé exibe o número do Tatami ativo (canto esquerdo), o temporizador centralizado e o escalão/categoria da competição (canto direito).
*   **Comandos de Visualização**:
    *   Atalho **F11** ou **Duplo Clique** para ativar o ecrã inteiro nativo, ocultando por completo a barra superior do sistema operativo.
    *   **Janela Arrastável**: Pode mover o ecrã de apresentação clicando e arrastando em qualquer ponto do seu fundo.
    *   Tecla **ESC** para reverter o ecrã inteiro.

### 4. Painel de Controle e Organização
*   **Lados Invertidos no Operador**: No painel administrativo da mesa de júri, o **AO (Azul)** situa-se do lado esquerdo e o **AKA (Vermelho)** do lado direito para acompanhar a perspetiva visual real de quem está sentado de frente para o tatami.
*   **Temporizador de Irikumi**: Emissão de aviso sonoro automático (`warning.mp3`) exatamente aos 15 segundos restantes do combate.
*   **Filtragem de Competições de Dois Níveis**: Menu "Competições Criadas" com filtros encadeados por modalidade (**Irikumi** / **Kata**) e localização (**Tatami 1**, **Tatami 2** e **Sem Tatami**) para uma melhor organização do evento.

---

## 🛠️ Como Instalar e Executar (Desenvolvimento)

Para correr a aplicação a partir do código fonte no Windows ou macOS, necessita do Python 3 instalado.

### 1. Clonar o repositório
```bash
git clone https://github.com/crastoo/KarateApp.git
cd KarateApp
```

### 2. Criar e ativar o Ambiente Virtual (venv)
*   **Windows (Prompt de Comando)**:
    ```cmd
    python -m venv venv
    venv\Scripts\activate
    ```
*   **macOS / Linux**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

### 3. Instalar as Dependências
```bash
pip install PyQt6 pyinstaller
```

### 4. Executar a Aplicação
```bash
python main.py
```

---

## 📦 Como Criar o Executável (.exe / .app)

Para empacotar a aplicação num único ficheiro executável independente (que corre sem necessidade de ter o Python instalado):

### No Windows:
Com o `venv` ativo, corra:
```cmd
venv\Scripts\pyinstaller --clean --noconsole --onefile --add-data "sounds;sounds" --name="KarateManager" main.py
```
O executável final independente de cerca de 40MB a 60MB será guardado em `dist/KarateManager.exe`.

---

## 📖 Guia Rápido de Utilização

1.  **Criar Competição**: Clique em "Criar Competição", selecione o tipo (*Individual* ou *Equipa*), insira os detalhes (Nome, Tatami, Categoria) e adicione os nomes e respetivos atletas das equipas (Dojos).
2.  **Organizar o Bracket**: No ecrã de gestão, arraste as equipas/atletas da barra lateral esquerda para os slots de início do bracket eliminatório.
3.  **Iniciar Combate**: Clique sobre um slot de combate preenchido para abrir o painel administrativo.
4.  **Lançar Apresentação**: Clique em "📺 Mostrar Apresentação" para abrir a janela do público e arraste-a para a segunda TV/Monitor. Dê duplo clique ou prima **F11** para a colocar em ecrã inteiro.
5.  **Controlar o Placar**: Use a barra de espaço para iniciar/pausar o temporizador. Use os botões de faltas para registar advertências e selecione os resultados de bandeiras ao final de cada luta.
