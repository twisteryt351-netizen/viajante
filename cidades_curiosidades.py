import os
import re
import time
import base64
import random
import urllib.parse
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
MODELO_IA = "openai/gpt-oss-120b"

# --- GERACAO DE IMAGENS COM IA (Pollinations.ai) ---
# Gratuito, sem chave, sem cota diaria. Se qualquer etapa falhar, o script cai
# automaticamente no metodo antigo (busca de imagem no Openverse).
POLLINATIONS_TOKEN = os.environ.get("POLLINATIONS_TOKEN")  # opcional: remove marca dagua e aumenta limite
# Sem token: 1 requisicao a cada 15s. Com token gratuito (auth.pollinations.ai): a cada 5s.
INTERVALO_POLLINATIONS = 6 if POLLINATIONS_TOKEN else 16
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY")
QTD_MIN_IMAGENS = 3
QTD_MAX_IMAGENS = 5

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


DIMENSOES_RATIO = {
    "16:9": (1280, 720),
    "1:1": (1024, 1024),
    "9:16": (720, 1280),
}


def gerar_imagem_pollinations(prompt, ratio="16:9"):
    """Gera uma imagem via Pollinations.ai (gratuito, sem chave, sem cota diaria).
    Retorna bytes da imagem ou None se falhar."""
    largura, altura = DIMENSOES_RATIO.get(ratio, (1280, 720))
    try:
        prompt_codificado = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{prompt_codificado}"
        params = {
            "width": largura,
            "height": altura,
            "model": "flux",
            "seed": random.randint(1, 999999),
            "nologo": "true",
        }
        headers = {}
        if POLLINATIONS_TOKEN:
            headers["Authorization"] = f"Bearer {POLLINATIONS_TOKEN}"
        resposta = requests.get(url, params=params, headers=headers, timeout=120)
        resposta.raise_for_status()
        content_type = resposta.headers.get("Content-Type", "")
        if "image" not in content_type:
            raise ValueError(f"Resposta nao parece ser uma imagem (Content-Type: {content_type})")
        return resposta.content
    except Exception as e:
        print(f"⚠️ Pollinations.ai falhou para o prompt '{prompt[:40]}...': {e}")
        return None


def hospedar_imagem(imagem_bytes, nome_arquivo="imagem.png"):
    """Sobe a imagem gerada para o imgbb.com (host gratuito via API) e retorna a URL publica."""
    if not IMGBB_API_KEY:
        print("⚠️ Falha ao hospedar imagem: IMGBB_API_KEY nao configurada")
        return None
    try:
        b64 = base64.b64encode(imagem_bytes).decode("utf-8")
        resposta = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY, "image": b64, "name": nome_arquivo},
            timeout=30,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        if dados.get("success"):
            return dados["data"]["url"]
        raise ValueError(f"Resposta inesperada do imgbb: {dados}")
    except Exception as e:
        print(f"⚠️ Falha ao hospedar imagem gerada: {e}")
        return None


def gerar_imagem_ia(prompt, ratio="16:9"):
    """Pipeline completo: gera a imagem no Pollinations.ai e hospeda no imgbb. Retorna URL ou None."""
    imagem_bytes = gerar_imagem_pollinations(prompt, ratio)
    if not imagem_bytes:
        return None
    return hospedar_imagem(imagem_bytes)


def _limpar_tag(texto):
    return re.sub(r"<[^>]+>", "", texto).strip()


def extrair_titulos_h2(html):
    return re.findall(r"<h2[^>]*>(.*?)</h2>", html, flags=re.IGNORECASE | re.DOTALL)


def contar_palavras_html(html):
    texto = re.sub(r"<[^>]+>", " ", html)
    return len(texto.split())


def calcular_qtd_imagens(wc, minimo, maximo, base_palavras, palavras_por_imagem_extra):
    if wc <= base_palavras:
        return minimo
    extras = (wc - base_palavras) // palavras_por_imagem_extra
    return min(maximo, minimo + extras)


def gerar_prompts_imagens_ia(titulo_post, cidade, secoes, quantidade):
    """Pede a IA prompts de imagem em ingles: o primeiro uma capa turistica de alto
    impacto visual para atrair o clique, e os demais ligados a cada momento/secao do post."""
    qtd_secoes = max(0, quantidade - 1)
    secoes_usadas = secoes[:qtd_secoes]
    lista_secoes = "\n".join(f"- {s}" for s in secoes_usadas) or "- (sem subtitulos definidos, use o tema geral do post)"

    prompt = f"""
Voce e um diretor de arte criando prompts para um gerador de imagens por IA (estilo Stable Diffusion/Flux)
para uma revista de viagem e cultura (estilo National Geographic / Piaui).
Cidade: "{cidade}"
Titulo do post: "{titulo_post}"

Preciso de exatamente {quantidade} prompts de imagem em INGLES, cada um em uma linha separada, SEM numeracao,
SEM aspas, SEM explicacoes - apenas os prompts, um por linha, nesta ordem:

1) A PRIMEIRA linha e a imagem de CAPA: fotografia de viagem cinematografica e deslumbrante,
   luz dourada ou atmosferica, composicao editorial de revista, alto impacto visual, sem
   texto escrito na imagem, pensada para maximizar cliques mantendo qualidade jornalistica.
2) As proximas linhas sao uma imagem para CADA um destes momentos/secoes do post (nesta ordem):
{lista_secoes}
   Cada prompt deve remeter visualmente ao conteudo daquela secao especifica (arquitetura,
   detalhes, atmosfera do local), mantendo consistencia estetica de fotografia de viagem
   realista com o tema geral.

Cada prompt: descritivo, rico em detalhes visuais (cenario, iluminacao, estilo fotografico,
composicao), fotorrealista, SEM citar nomes proprios de pessoas reais, marcas registradas
ou obras protegidas por direitos autorais especificos. Responda APENAS com as {quantidade}
linhas de prompt.
"""
    resposta = pedir_ia_groq(prompt, temperatura=0.8)
    linhas = [l.strip(" -\"") for l in resposta.strip().splitlines() if l.strip()]
    if len(linhas) < quantidade:
        while len(linhas) < quantidade:
            linhas.append(linhas[-1] if linhas else titulo_post)
    return linhas[:quantidade]


def montar_galeria_ia(titulo_post, cidade, corpo_html, minimo, maximo):
    """Gera a galeria completa de imagens via Pollinations.ai. Lanca excecao se qualquer
    etapa falhar, para o chamador cair no fallback do Openverse."""
    if not IMGBB_API_KEY:
        raise RuntimeError("IMGBB_API_KEY nao configurada")

    secoes_brutas = extrair_titulos_h2(corpo_html)
    secoes = [_limpar_tag(s) for s in secoes_brutas]

    wc = contar_palavras_html(corpo_html)
    qtd = calcular_qtd_imagens(wc, minimo, maximo, base_palavras=800, palavras_por_imagem_extra=350)
    if secoes:
        qtd = min(qtd, len(secoes) + 1)
    qtd = max(1, qtd)

    prompts = gerar_prompts_imagens_ia(titulo_post, cidade, secoes, qtd)

    galeria = []
    for i, prompt in enumerate(prompts):
        url = gerar_imagem_ia(prompt, ratio="16:9")
        if not url:
            raise RuntimeError(f"Falha ao gerar/hospedar imagem {i + 1}/{qtd} da galeria")
        alt = titulo_post if i == 0 else (secoes[i - 1] if i - 1 < len(secoes) else titulo_post)
        galeria.append((url, alt))
        if i < len(prompts) - 1:
            time.sleep(INTERVALO_POLLINATIONS)  # respeita o rate limit do Pollinations.ai

    return galeria, secoes_brutas


def inserir_imagens_no_corpo(corpo_html, secoes_brutas, galeria):
    """Insere as imagens de secao (a partir do indice 1 da galeria) logo apos os respectivos <h2>."""
    novo_html = corpo_html
    imagens_secao = galeria[1:]
    for i, (url, alt) in enumerate(imagens_secao):
        if i >= len(secoes_brutas):
            break
        h2_bruto = secoes_brutas[i]
        padrao = re.compile(r"(<h2[^>]*>" + re.escape(h2_bruto) + r"</h2>)", re.IGNORECASE)
        img_html = gerar_tabela_imagem_blogger(url, alt)
        novo_html, _ = padrao.subn(lambda m: m.group(1) + img_html, novo_html, count=1)
    return novo_html


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
5. TAMANHO E DENSIDADE: O artigo deve ter entre 1200 e 2800 palavras, sendo muito bem desenvolvido, denso e repleto de detalhes ricos, caso não tiver muito oque falar, procure noticias e fatos históricos coerentes para preencher o texto lembre-se que você é um guia e contrutor de uma comunidade online, não lhe pode faltar contéudo!
6.Cide fontes das pesquisas!

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

    try:
        galeria, secoes_brutas = montar_galeria_ia(
            titulo,
            cidade,
            corpo,
            minimo=QTD_MIN_IMAGENS,
            maximo=QTD_MAX_IMAGENS,
        )
        img_html = gerar_tabela_imagem_blogger(galeria[0][0], titulo)
        corpo = inserir_imagens_no_corpo(corpo, secoes_brutas, galeria)
        print(f"🎨 Galeria com {len(galeria)} imagem(ns) gerada via Pollinations.ai.")
    except Exception as e:
        print(f"⚠️ Geracao de imagens via IA falhou, usando metodo padrao (Openverse): {e}")
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
