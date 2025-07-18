# 🚀 Ambiente de Desenvolvimento com Dev Containers (VS Code)

Este guia descreve como configurar e utilizar o ambiente de desenvolvimento padronizado para este projeto usando [Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers) no Visual Studio Code.

O uso de Dev Containers garante que todos os desenvolvedores trabalhem em um ambiente idêntico e isolado, contendo todas as dependências necessárias (Python, bibliotecas, banco de dados, etc.), sem a necessidade de instalar tudo manualmente na sua máquina.

---

### ✅ Pré-requisitos

Antes de começar, garanta que você tenha instalado:

1. **Docker Desktop**: Essencial para criar e gerenciar os contêineres. [Faça o download aqui](https://www.docker.com/products/docker-desktop/).
2. **Visual Studio Code**: O editor onde o ambiente será executado. [Faça o download aqui](https://code.visualstudio.com/).
3. **Extensão Dev Containers**: A extensão oficial da Microsoft para o VS Code.
    - [Instalar a partir do Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

---

### ⚙️ Configuração Inicial (Apenas na primeira vez)

O projeto precisa de uma pasta de configuração de ambiente chamado `.envs`, disponível no discord

---

### ▶️ Como Iniciar o Ambiente

1. Abra a pasta raiz do projeto no **Visual Studio Code**.
2. O VS Code pode detectar automaticamente a configuração do Dev Container e mostrar uma notificação. Se isso acontecer, clique em **"Reopen in Container"**.
3. Caso a notificação não apareça, inicie manualmente:
    - Pressione `F1` para abrir a paleta de comandos.
    - Digite e selecione a opção: **`Dev Containers: Reopen in Container`**.

> 💡 **Aguarde a construção:** Na primeira vez, o Docker irá baixar as imagens e construir o ambiente, o que pode levar alguns minutos. Nas próximas vezes, o processo será quase instantâneo.

---

### ⚡ Executando a Aplicação

Com o ambiente rodando dentro do contêiner, você pode usar o terminal integrado do VS Code (`Ctrl + '` ou `Cmd + '`) para executar os comandos do Django.

#### Rodando o servidor de desenvolvimento

```bash
python manage.py runserver 0.0.0.0:8001
```

#### Aplicando migrations

Rodar os comandos abaixo quando a aplicação não estiver rodando

```bash
python manage.py makemigrations (demonstra modificações a serem aplicadas no banco)

python manage.py migrate (aplica as modificações)
```

- Terabyte:

```bash
python -m track_save.webscrapping_amazon.scraper.scraper
```

Depois acesse o endpoint em api/save_terabyte para salvar os dados no banco
