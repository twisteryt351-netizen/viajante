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

# --- RODÍZIO DE CIDADES DO MUNDO ---
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


IMAGEM_PADRAO = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?q=80&w=1000&auto=format&fit=crop"


def buscar_imagem_openverse(palavra_chave):
    try:
        resposta = requests.get(
            "https://api.openverse.org/v1/images/",
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
        'class="tr-caption-container" style="margin-left: auto; margin-right: auto; text-align: center;">'
        '<tbody><tr><td style="text-align: center;">'
        f'<img alt="{alt_title}" border="0" style="max-width: 100%; height: auto; border-radius: 8px;" src="{url_img}" '
        f'title="{alt_title}" /></td></tr></tbody></table><br />'
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
Você é um historiador, jornalista e autor de guias de viagem fascinado pelo incomum e pelo mistério urbano.

Cidade de hoje: {cidade}

Escolha UM lugar, monumento, museu incomum, passagem histórica oculta ou lenda fascinante REAL dessa cidade. Deve ser algo com personalidade, mistério ou grande valor cultural e arquitetônico.

Monte um roteiro denso com:
1. O local/história exata escolhida.
2. A atmosfera e o mistério por trás do lugar.
3. 4 a 5 aspectos detalhados que valem a pena explorar sobre ele (arquitetura, segredos, coleções, impacto no visitante, lendas).

Responda em texto simples e direto.
"""
    return pedir_ia_groq(prompt, temperatura=0.6)


def gerar_artigo_completo(esqueleto, cidade):
    prompt = f"""
Você é um renomado colunista de viagens e cultura, com um estilo literário denso, envolvente, poético e levemente irônico/bem-humorado (no estilo da revista Piauí ou National Geographic).

Cidade: {cidade}
Tema base:
{esqueleto}

DIRETRIZES OBRIGATÓRIAS DE REDAÇÃO:
1. IDIOMA E ACENTUAÇÃO: Escreva em Português do Brasil com ACENTUAÇÃO RIGOROSA E PERFEITA (use acentos agudos, circunflexos, tiis, crases corretamente em todas as palavras).
2. ESTILO NARRATIVO: Use um vocabulário rico, envolvente e imersivo. Descreva a atmosfera, as luzes, os cheiros e as sensações visuais com maestria.
3. SUBTÍTULOS IMAGINATIVOS: NUNCA use subtítulos genéricos como "O que torna especial", "Como é a experiência", "Curiosidades" ou "Dicas práticas". Crie subtítulos <h2> poéticos, intrigantes e dramáticos que pareçam títulos de capítulos de livro.
4. COMENTÁRIOS PESSOAIS BEM-HUMORADOS: Inclua de 2 a 3 parágrafos curtos no estilo de pensamento bem-humorado em primeira pessoa ("Sabe o que eu acho?...", "Olha, sinceramente...", "Pega essa:...") para quebrar a solenidade e criar conexão com o leitor.
5. TAMANHO E DENSIDADE: O artigo deve ter entre 900 e 1300 palavras, sendo muito bem desenvolvido, denso e repleto de detalhes ricos.

REGRAS DE FORMATO (Retorne APENAS HTML puro, sem Markdown e sem tags ```html):
- Subtítulos em tags <h2>.
- Parágrafos bem estruturados em tags <p>.
- Destaques de reflexões soltas ou frases de impacto estilizadas em <blockquote>.
- Palavras e conceitos chave destacados com <b>.
"""
    return pedir_ia_groq(prompt, temperatura=0.7)


def gerar_titulo(esqueleto, cidade):
    prompt = (
        f"Baseado neste tema sobre {cidade}:\n{esqueleto}\n\n"
        f"Crie um título longo, fascinante, magnético e poético para um artigo de blog, no estilo: "
        f"'[Nome do Local] em [Cidade]: Arte, Segredos e o Enigma [Adjetivo] no Coração de [Bairro] que Desafia a Razão'. "
        f"Responda apenas o título, em português do Brasil com acentuação perfeita, sem aspas."
    )
    return pedir_ia_groq(prompt, temperatura=0.7).replace('"', '').strip()


def extrair_palavra_chave(cidade, esqueleto):
    prompt = (
        f"Cidade: {cidade}\nTema: {esqueleto}\n\n"
        f"Responda apenas 2 palavras em inglês para buscar uma foto bonita e representativa no banco de imagens (exemplo: 'paris museum', 'rio architecture')."
    )
    return pedir_ia_groq(prompt, temperatura=0.3).strip().lower()


def gerar_cta():
    return """
<hr style="border: 0; height: 1px; background: #eee; margin: 30px 0;" />
<div style="background-color: #f4f6f8; border-radius: 12px; margin: 30px 0; padding: 25px; text-align: center; font-family: sans-serif;">
    <p style="font-size: 17px; font-weight: bold; color: #333; margin: 0 0 10px 0;">Já conhecia esse lugar?</p>
    <p style="font-size: 14px; color: #555; margin: 0 0 15px 0;">Curta, comente contando se já foi ou se colocou na lista, e compartilhe com quem ama viajar!</p>
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
    print(f"Postado com sucesso: '{titulo}' -> {resultado.get('url')}")


if __name__ == "__main__":
    print("Iniciando geração de artigo de altíssima qualidade...")
    cidade = proxima_cidade()
    print(f"Cidade selecionada: {cidade}")

    esqueleto = gerar_esqueleto(cidade)
    print("Elaborando tema denso e envolvente...")

    corpo = gerar_artigo_completo(esqueleto, cidade)
    titulo = gerar_titulo(esqueleto, cidade)
    palavra_chave = extrair_palavra_chave(cidade, esqueleto)
    img_url = buscar_imagem_openverse(palavra_chave)
    img_html = gerar_tabela_imagem_blogger(img_url, titulo)
    cta = gerar_cta()

    aviso = (
        '<p style="font-size: 12px; color: #888; font-style: italic; margin-top: 20px;">'
        'Informações de horários, preços e endereços podem mudar — confirme sempre no site oficial do local antes de planejar sua visita.</p>'
    )

    pais = cidade.split(",")[-1].strip() if "," in cidade else cidade
    tags = ["viagem", "curiosidades", cidade.split(",")[0].strip(), pais]

    html_final = f"{img_html}{corpo}{cta}{aviso}"
    publicar_no_blogger(titulo, html_final, tags)
    marcar_cidade_usada(cidade)
    print("Processo concluído com sucesso!")
