# Transforme Files OpenFinance

    Este programa tem por objetivo processar os arquivos do OpenFinance de forma anonimizada oriundos de um fulllog qualquer.

## Pré-requisitos
    para utilizar este programa é necessário ter a versão 3.9.6 do Python ou superior compatível.

## Como utilizar
    1. Disponibilize os arquivos que deseja processar no diretório "/files/to_process".
    2. Execute o comando "py ./main.py" Na pasta raiz onde está o arquivo man.py;
    3. Os resultados serão disponibilizados nos seguintes diretórios:
    3.1. Processed: significa que os arquivos foram processados com sucesso;
    3.2. Ignored: significa que o arquivo não atende aos padrões necessários, ou seja, todos os arquivos que não forem de pessoa física (personal) serão movidos para cá;
    3.3. With_Errors: siginifica que ocorreu alguma exceção durante o processamento e um debug para este arquivo será necessário;