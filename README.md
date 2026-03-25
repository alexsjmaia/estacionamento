# Sistema de Estacionamento

Base inicial do sistema de estacionamento em Python, preparada para rodar em Windows e evoluir com MySQL.

## Requisitos

- Windows 10 ou superior
- Python 3.11 ou superior instalado e disponível no PATH
- MySQL
- Impressora Elgin i9 instalada no Windows

## Instalação

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Execução

```powershell
python app.py
```

O sistema ficará disponível em `http://localhost:5000`.

Ou, se preferir, execute:

```powershell
.\start.bat
```

## Configuração do MySQL

Use o arquivo `.env.exemplo` como referência para configurar:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

Nesta primeira etapa, a tela principal apenas mostra o status da conexão com o banco.

## Inicialização do banco

O projeto agora inclui o script [init_database.py](/D:/Projetos/Estacionamento/init_database.py) para criar:

- banco `estacionamento`
- tabela `usuarios`
- tabela `codigos_marcas`
- usuário inicial `ROOT`
- senha inicial `ROOT`
- carga inicial de códigos e marcas

Execute no Windows:

```powershell
python init_database.py
```

Se o seu MySQL usar senha no usuário `root`, ajuste a variável `password` no arquivo [init_database.py](/D:/Projetos/Estacionamento/init_database.py).

## Impressao direta na Elgin i9

O comprovante agora pode ser enviado diretamente para a impressora termica via spooler do Windows, sem abrir a tela de impressao do navegador.

Configuracao:

- instale as dependencias com `pip install -r requirements.txt`
- confirme o nome da impressora no Windows
- se necessario, ajuste `PRINTER_NAME` em [.env.exemplo](/D:/Projetos/Estacionamento/.env.exemplo) ou como variavel de ambiente
- no seu ambiente atual, o nome listado foi `Elgin`

Para listar as impressoras instaladas:

```powershell
python list_printers.py
```

Fluxo:

- ao gerar a entrada, o sistema envia o comprovante automaticamente para a Elgin i9
- depois da impressao, retorna para a tela de entrada de veiculos

Observacao:

- a impressao direta usa `pywin32` e comandos RAW/ESC-POS
- isso melhora o negrito, o tamanho da placa/modelo e o avanço de papel na impressora termica

## Login inicial

- Usuário: `ROOT`
- Senha: `ROOT`

## Funcionalidades da tela principal

- Entrada de Veiculos
- Reimprime a ultima Entrada
- Cancela ultima Entrada
- Saida de veiculos
- Consulta Estacionamento
- Cadastra precos

As telas operacionais ainda estão como placeholder e podem ser implementadas em seguida.

## Observações para Windows

- Se o PowerShell bloquear a ativação do ambiente virtual, execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

- Se o comando `python` não funcionar, reinstale o Python marcando a opção `Add Python to PATH`.
