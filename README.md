<img align="right" alt="RSS Logo" width="30%" height="auto" src="https://rss.com/blog/wp-content/uploads/2019/10/social_style_3_rss-512-1.png">

# RSSNewsDay

Envio automático de feed RSS para pessoa, canal ou grupo no Telegram.

[Mais explicações e exemplos de uso aqui](https://blog.gabrf.com/posts/Rss2Telegram/).

## Participe:

Participe das conversas sobre o projeto na aba [Discussions](https://github.com/GabrielRF/Rss2Telegram/discussions).

Issues também são sempre bem vindas.

## Configuração:

Defina as variáveis na aba `Secrets` do repositório:

`BOT_TOKEN`: Token do bot que enviará as mensagens no canal ([@BotFather](https://t.me/BotFather));

Defina as variáveis na aba `Variables` do repositório:

`DESTINATION`: Destinos das mensagens separados por vírgulas (`@destino` ou ID). Opcionalmente, remova a variável e crie um arquivo de nome `DESTINATION.txt` com os valores;

`URL`: Endereços de feeds RSS, separados por "enter", ou seja, um por linha. Opcionalmente, remova a variável e crie um arquivo de nome `URL.txt` com os valores;

`PARAMETERS`: (opcional) Parâmetros que serão adicionados ao fim do link;

`MESSAGE_TEMPLATE`: (opcional) Texto da mensagem. Valor padrão: `<b>{TITLE}</b>` ([ver opções](#opções-de-variáveis));

`BUTTON_TEXT`: (opcional) Texto do botão com o link. Sugestão: `{SITE_NAME}`. Se esta variável não for criada não será enviado um botão. ([Ver opções](#opções-de-variáveis));

`EMOJIS`: (opcional) Emojis separados por vírgulas. Podem ser usados na mensagem ou no botão;

`TOPIC`: (opcional) ID do tópico em que a mensagem será enviada. Necessário para grupos com a opção de tópicos ativada. [Como obter um ID de um tópico](#id-de-tópico)

`TELEGRAPH_TOKEN`: (opcional) Chave para acesso ao Telegraph. [Como obter uma chave Telegraph](#chave-telegraph)

`HIDE_BUTTON`: (opcional) Caso definida, desabilita o botão no envio, permitindo assim a existência do `Leitura Rápida`.

### Opções de variáveis

`{SITE_NAME}`: Nome do site;

`{TITLE}`: Título do post;

`{SUMMARY}`: Sumário do post;

`{LINK}`: Link do post;

`{EMOJI}`: Emoji escolhido aleatoriamente da lista.

## Filtros

Por padrão, todos os elementos do feed RSS serão enviados. Caso queira filtrar o conteúdo, crie um arquivo chamado `RULES.txt` e adicione as regras desejadas ao arquivo. As regras serão executadas em ordem!

> O valor contido em termo funcionará independente de letras maiúsculas ou minúsculas.

`ACCEPT:ALL`: Todas as mensagens serão enviadas;

`DROP:ALL`: Todas as mensagens não serão enviadas;

`ACCEPT:termo`: A mensagem será enviada se `termo` estiver presente;

`DROP:termo`: A mensagem não será enviada se `termo` estiver presente.

### Exemplos de Filtros:

1. Todos as mensagens serão enviadas, menos as que tiverem o termo `política`:

```
ACCEPT:ALL
DROP:Política
```

2. Nenhuma mensagem será enviada, com exceção das mensagens com os termos `futebol` e `vôlei`:

```
DROP:ALL
ACCEPT:futebol
ACCEPT:vôlei
```

## Uso

Faça um *Fork*, defina as variáveis e habilite a ação em "*Enable workflow*". Pronto! 

![Enable Workflow](https://user-images.githubusercontent.com/7331540/178158090-bf774cae-071b-4ac2-ab03-9c5c1132b79e.png)

A ação irá buscar as atualizações a cada hora conforme definido no arquivo [cron.yml](.github/workflows/cron.yml).

## ID de tópico

Caso o grupo tenha a opção de tópicos ativada, será necessário indicar em qual tópico a mensagem será enviada. Isto é feito usando-se a variável `TOPIC`. A maneira mais fácil de se obter um ID de um tópico é copiando o link de uma mensagem de um tópico. O ID será o penúltimo número do link.

Exemplo: O link para uma mensagem de um tópico seria `https://t.me/c/987654321/123/4567`. Neste caso, `123` seria o ID do tópico, o número que deveria ser colocado na variável.

## Chave Telegraph

> Atenção: Caso a variável <i>TELEGRAPH_TOKEN</i> esteja definida, o post não terá botão ou imagem, pois ambos não permitiriam a existência da opção "Visualização Rápida".

Para criar sua chave de acesso ao Telegraph e gerar a <i>Visualização Rápida</i> de qualquer site, acesse:

```
https://api.telegra.ph/createAccount?short_name=<SHORT_NAME>&author_name=<AUTHOR_NAME>
```

* `SHORT_NAME`: Uma abreviação de seu nome;

* `AUTHOR_NAME`: Seu nome.

A resposta do site será algo como:

```
{
  "ok": true,
  "result": {
    "short_name": "NOME",
    "author_name": "NOME",
    "author_url": "",
    "access_token": "abcdefghijklmnopqrtuvxz123456789",
    "auth_url": "https://edit.telegra.ph/auth/123456789012345678901234567890"
  }
}
```

O valor presente em `access_token` é o valor a ser usado na variável `TELEGRAPH_TOKEN`.
