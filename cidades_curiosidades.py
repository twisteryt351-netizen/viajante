import os
import random
import requests
from groq import Groq
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- CONFIGURAÇÕES ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BLOGGER_ID = os.environ.get("BLOGGER_ID")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

# Validação das variáveis de ambiente necessárias
for nome, valor in [
    ("GROQ_API_KEY", GROQ_API_KEY),
    ("BLOGGER_ID", BLOGGER_ID),
    ("BLOGGER_CLIENT_ID", CLIENT_ID),
    ("BLOGGER_CLIENT_SECRET", CLIENT_SECRET),
    ("BLOGGER_REFRESH_TOKEN", REFRESH_TOKEN),
]:
    if not valor:
        raise ValueError(f"Faltou configurar a variavel/segredo: {nome}")

groq_client = Groq(api_key=GROQ_API_KEY)
MODELO_IA = "llama-3.3-70b-versatile"

# --- RODÍZIO DE CIDADES DO MUNDO (uma por dia) ---
CIDADES = [
    # --- BRASIL ---
    "Rio de Janeiro, Brasil", "São Paulo, Brasil", "Salvador, Brasil", "Ouro Preto, Brasil", "Manaus, Brasil",
    "Florianópolis, Brasil", "Curitiba, Brasil", "Gramado, Brasil", "Paraty, Brasil", "Recife, Brasil",
    "Fortaleza, Brasil", "Belo Horizonte, Brasil", "Foz do Iguaçu, Brasil", "Natal, Brasil", "Brasília, Brasil",
    "Bonito, Brasil", "Lençóis, Brasil", "Pirenópolis, Brasil", "Tiradentes, Brasil", "Trancoso, Brasil",
    "Olinda, Brasil", "Campos do Jordão, Brasil", "Maceió, Brasil", "São Luís, Brasil", "Vitória, Brasil",
    "Belém, Brasil", "Balneário Camboriú, Brasil", "Canela, Brasil", "Ilhabela, Brasil", "Petrópolis, Brasil",
    "Búzios, Brasil", "Arraial do Cabo, Brasil", "Goiânia, Brasil", "Cuiabá, Brasil", "Palmas, Brasil",
    "João Pessoa, Brasil", "Aracaju, Brasil", "Porto Alegre, Brasil", "Ribeirão Preto, Brasil", "Campinas, Brasil",

    # --- JAPÃO ---
    "Tóquio, Japão", "Quioto, Japão", "Osaka, Japão", "Hiroshima, Japão", "Nara, Japão",
    "Sapporo, Japão", "Fukuoka, Japão", "Nagoya, Japão", "Yokohama, Japão", "Kobe, Japão",

    # --- ITÁLIA ---
    "Roma, Itália", "Milão, Itália", "Veneza, Itália", "Florença, Itália", "Nápoles, Itália",
    "Turim, Itália", "Bolonha, Itália", "Verona, Itália", "Gênova, Itália", "Pisa, Itália",

    # --- FRANÇA ---
    "Paris, França", "Nice, França", "Lyon, França", "Marseille, França", "Bordeaux, França",
    "Estrasburgo, França", "Toulouse, França", "Lille, França", "Nantes, França", "Montpellier, França",

    # --- ESPANHA E PORTUGAL ---
    "Madrid, Espanha", "Barcelona, Espanha", "Sevilha, Espanha", "Valência, Espanha", "Granada, Espanha",
    "Lisboa, Portugal", "Porto, Portugal", "Coimbra, Portugal", "Braga, Portugal", "Sintra, Portugal",

    # --- ESTADOS UNIDOS E CANADÁ ---
    "Nova York, Estados Unidos", "Los Angeles, Estados Unidos", "Chicago, Estados Unidos", "Miami, Estados Unidos", "São Francisco, Estados Unidos",
    "Toronto, Canadá", "Vancouver, Canadá", "Montreal, Canadá", "Quebec City, Canadá", "Ottawa, Canadá",

    # --- REINO UNIDO E ALEMANHA ---
    "Londres, Reino Unido", "Edimburgo, Escócia", "Manchester, Reino Unido",
    "Berlim, Alemanha", "Munique, Alemanha", "Frankfurt, Alemanha", "Hamburgo, Alemanha"
]

ARQUIVO_HISTORICO = "historico_cidades.txt"


def proxima_cidade():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return CIDADES[0]
    with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
        linhas = f.read().splitlines()
    if not linhas:
        return CIDADES[0]
    ultima = linhas[-1]
    if ultima not in CIDADES:
        return CIDADES[0]
    indice = (CIDADES.index(ultima) + 1) % len(CIDADES)
    return CIDADES[indice]


def marcar_cidade_usada(cidade):
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(cidade + "\n")


IMAGEM_PADRAO = "[https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/News_icon.svg/640px-News_icon.svg.png](https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/News_icon.svg/640px-News_icon.svg.png)"


def buscar_imagem_openverse(palavra_chave):
    try:
        resposta = requests.get(
            "[https://api.openverse.org/v1/images/](https://api.openverse.org/v1/images/)",
            params={
                "q": palavra_chave,
                "license_type": "commercial",
                "page_size": 3,
                "mature": "false",
            },
            headers={"User-Agent": "RoboCidades/1.0"},
            timeout=10,
        )
        resultados = resposta.json().get("results", [])
        return resultados[0]["url"] if resultados else IMAGEM_PADRAO
    except Exception as e:
        print(f"Erro ao buscar imagem: {e}")
        return IMAGEM_PADRAO


def gerar_tabela_imagem_blogger(url_img, alt_title):
    return (
        '<table align="center" cellpadding="0" cellspacing="0" '
        'class="tr-caption-container" style="margin-left: auto; margin-right: auto;">'
        '<tbody><tr><td style="text-align: center;">'
        f'<img alt="{alt_title}" border="0" height="360" src="{url_img}" '
        f'title="{alt_title}" width="640" /></td></tr></tbody></table><br />'
    )


def pedir_ia_groq(prompt, temperatura=0.7):
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODELO_IA,
        temperature=temperatura,
    )
    texto = response.choices[0].message.content.strip()
    
    # Limpa marcadores de código Markdown caso a IA adicione
    if texto.startswith("```html"):
        texto = texto[7:]
    elif texto.startswith("```"):
        texto = texto[3:]
    if texto.endswith("```"):
        texto = texto[:-3]
        
    return texto.strip()


def gerar_esqueleto(cidade):
    prompt = f"""
Voce e um redator de viagens especializado em encontrar cantos curiosos e pouco conhecidos de grandes cidades.

Cidade de hoje: {cidade}

Escolha UM lugar, historia ou curiosidade REAL, especifica e pouco conhecida dessa cidade (um museu incomum, um bairro secreto, uma lenda urbana, uma curiosidade arquitetonica, um fato historico bizarro) - algo que voce tenha confianca real de que existe, sem inventar nomes ou fatos.

Monte um ESQUELETO com:
- O nome exato do lugar/curiosidade escolhido.
- 5 a 6 topicos que o artigo vai cobrir (contexto/historia, o que torna especial, curiosidades, como e a experiencia de visitar, dicas praticas gerais).
- 1-2 frases resumindo cada topico, sem repetir informacao entre eles.

Responda so o esqueleto, texto simples.
"""
    return pedir_ia_groq(prompt, temperatura=0.6)


def gerar_artigo_completo(esqueleto, cidade):
    prompt = f"""
Voce e um redator de viagens premiado, escrevendo para um blog de curiosidades urbanas do mundo todo. Escreva com capricho, sem pressa.

Cidade: {cidade}
Esqueleto obrigatorio a seguir (desenvolva cada topico em profundidade, sem repetir):
{esqueleto}

REGRAS DE CONTEUDO E PRECISAO:
- Baseie-se em fatos reais e conhecidos. NAO invente numeros de endereco, horarios de funcionamento especificos, precos de ingresso ou dados que podem estar desatualizados - para esse tipo de informacao pratica, oriente o leitor a confirmar no site oficial do local antes de visitar, em vez de fabricar um dado especifico.
- PROIBIDO repetir a mesma ideia com palavras diferentes.
- Tamanho: entre 900 e 1400 palavras, bem escrito e envolvente.

REGRAS DE FORMATO (HTML puro, sem Markdown):
1. Paragrafo de abertura instigante.
2. Cada topico do esqueleto vira um subtitulo <h2> proprio.
3. Inclua 2 notas do autor leves e engracadas, cada uma dentro de <blockquote>.
4. Nao inclua links no corpo do texto.
5. Termine com um paragrafo convidando o leitor a comentar se ja foi nessa cidade ou conhece esse lugar, e a compartilhar com quem ama viajar.
"""
    return pedir_ia_groq(prompt, temperatura=0.75)


def gerar_titulo(esqueleto, cidade):
    prompt = (
        f"Baseado neste esqueleto sobre {cidade}:\n{esqueleto}\n\n"
        f"Crie um titulo de blog chamativo, otimizado para SEO, em portugues do Brasil, "
        f"sem aspas. Responda apenas o titulo."
    )
    return pedir_ia_groq(prompt, temperatura=0.7).replace('"', '').strip()


def extrair_palavra_chave(cidade, esqueleto):
    prompt = (
        f"Baseado nesta cidade ({cidade}) e neste esqueleto de artigo:\n{esqueleto}\n\n"
        f"De apenas UMA palavra-chave em ingles para buscar uma foto relacionada "
        f"(ex: 'paris street', 'tokyo temple', 'rio de janeiro'). Responda so a palavra ou frase curta."
    )
    return pedir_ia_groq(prompt, temperatura=0.3).strip().lower()


def gerar_cta():
    return """
<div style="background-color: #f4f6f8; border-radius: 12px; margin: 30px 0; padding: 25px; text-align: center; font-family: sans-serif;">
    <p style="font-size: 17px; font-weight: bold; color: #333; margin: 0 0 10px 0;">Ja conhecia esse lugar?</p>
    <p style="font-size: 14px; color: #555; margin: 0 0 15px 0;">Curta, comenta contando se ja foi ou se colocou na lista, e compartilha com quem ama viajar!</p>
    <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
        <a href="#" onclick="window.open('https://api.whatsapp.com/send?text=' + encodeURIComponent(document.title + ' - ' + window.location.href), '_blank'); return false;" style="background-color: #25d366; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">WhatsApp</a>
        <a href="#" onclick="window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(window.location.href), '_blank'); return false;" style="background-color: #1877f2; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">Facebook</a>
        <a href="#" onclick="window.open('https://twitter.com/intent/tweet?url=' + encodeURIComponent(window.location.href), '_blank'); return false;" style="background-color: #000; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">X</a>
    </div>
</div>
"""


def obter_credenciais():
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return creds


def publicar_no_blogger(titulo, conteudo, tags):
    creds = obter_credenciais()
    blogger = build('blogger', 'v3', credentials=creds)
    corpo_postagem = {
        'kind': 'blogger#post',
        'title': titulo,
        'content': conteudo,
        'labels': tags,
    }
    resultado = blogger.posts().insert(blogId=BLOGGER_ID, body=corpo_postagem).execute()
    print(f"Postado: '{titulo}' -> {resultado.get('url')}")


if __name__ == "__main__":
    print("Gerando curiosidade de cidade do dia...")
    cidade = proxima_cidade()
    print(f"Cidade de hoje: {cidade}")

    esqueleto = gerar_esqueleto(cidade)
    print("Esqueleto gerado, escrevendo artigo completo...")

    corpo = gerar_artigo_completo(esqueleto, cidade)
    titulo = gerar_titulo(esqueleto, cidade)
    palavra_chave = extrair_palavra_chave(cidade, esqueleto)
    img_url = buscar_imagem_openverse(palavra_chave)
    img_html = gerar_tabela_imagem_blogger(img_url, titulo)
    cta = gerar_cta()

    aviso = (
        '<p style="font-size: 12px; color: #888; font-style: italic;">Informacoes de '
        'horarios, precos e enderecos podem mudar - confirme sempre no site oficial do '
        'local antes de planejar sua visita.</p>'
    )

    pais = cidade.split(",")[-1].strip() if "," in cidade else cidade
    tags = ["viagem", "curiosidades", cidade.split(",")[0].strip(), pais]

    html_final = f"{img_html}{corpo}{cta}{aviso}"
    publicar_no_blogger(titulo, html_final, tags)
    marcar_cidade_usada(cidade)
    print("Concluido!")
