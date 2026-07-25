import os
import random
import requests
from groq import Groq
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- CONFIGURACOES ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BLOGGER_ID = os.environ.get("BLOGGER_ID")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

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

# --- RODÍZIO DE CIDADES DO MUNDO (uma por dia, ciclo de ~1.8 anos) ---
CIDADES = [
    # --- BRASIL (Turismo, História, Litoral e Interior) ---
    "Rio de Janeiro, Brasil", "São Paulo, Brasil", "Salvador, Brasil", "Ouro Preto, Brasil", "Manaus, Brasil",
    "Florianópolis, Brasil", "Curitiba, Brasil", "Gramado, Brasil", "Paraty, Brasil", "Recife, Brasil",
    "Fortaleza, Brasil", "Belo Horizonte, Brasil", "Foz do Iguaçu, Brasil", "Natal, Brasil", "Brasília, Brasil",
    "Bonito, Brasil", "Lençóis, Brasil", "Pirenópolis, Brasil", "Tiradentes, Brasil", "Trancoso, Brasil",
    "Olinda, Brasil", "Campos do Jordão, Brasil", "Maceió, Brasil", "São Luís, Brasil", "Vitória, Brasil",
    "Belém, Brasil", "Balneário Camboriú, Brasil", "Canela, Brasil", "Ilhabela, Brasil", "Petrópolis, Brasil",
    "Búzios, Brasil", "Arraial do Cabo, Brasil", "Goiânia, Brasil", "Cuiabá, Brasil", "Palmas, Brasil",
    "João Pessoa, Brasil", "Aracaju, Brasil", "Porto Alegre, Brasil", "Ribeirão Preto, Brasil", "Campinas, Brasil",
    "São José dos Campos, Brasil", "Santos, Brasil", "Sorocaba, Brasil", "Uberlândia, Brasil", "Juiz de Fora, Brasil",
    "Montes Claros, Brasil", "Caxias do Sul, Brasil", "Joinville, Brasil", "Blumenau, Brasil", "Lages, Brasil",
    "Cascavel, Brasil", "Londrina, Brasil", "Maringá, Brasil", "Chapecó, Brasil", "Criciúma, Brasil",
    "Pelotas, Brasil", "Santa Maria, Brasil", "Passo Fundo, Brasil", "Uruguaiana, Brasil", "Bento Gonçalves, Brasil",
    "Alter do Chão, Brasil", "Santarém, Brasil", "Macapá, Brasil", "Boa Vista, Brasil", "Rio Branco, Brasil",
    "Porto Velho, Brasil", "Ji-Paraná, Brasil", "Sinop, Brasil", "Rondonópolis, Brasil", "Anápolis, Brasil",
    "Caldas Novas, Brasil", "Rio Verde, Brasil", "Uberaba, Brasil", "Poços de Caldas, Brasil", "São João del-Rei, Brasil",
    "Diamantina, Brasil", "Governador Valadares, Brasil", "Ipatinga, Brasil", "Angra dos Reis, Brasil", "Cabo Frio, Brasil",
    "Macaé, Brasil", "Nova Friburgo, Brasil", "Teresópolis, Brasil", "Volta Redonda, Brasil", "Guaratinguetá, Brasil",
    "Aparecida, Brasil", "Ubatuba, Brasil", "Caraguatatuba, Brasil", "São Sebastião, Brasil", "Guaruja, Brasil",

    # --- JAPÃO (Tradição, Metrópoles, Ilhas e Cultura Anime/Pop) ---
    "Tóquio, Japão", "Quioto, Japão", "Osaka, Japão", "Hiroshima, Japão", "Nara, Japão",
    "Sapporo, Japão", "Fukuoka, Japão", "Nagoya, Japão", "Yokohama, Japão", "Kobe, Japão",
    "Kamakura, Japão", "Kanazawa, Japão", "Hakone, Japão", "Takayama, Japão", "Nikko, Japão",
    "Okinawa, Japão", "Sendai, Japão", "Nagano, Japão", "Kagoshima, Japão", "Nagasaki, Japão",
    "Kumamoto, Japão", "Matsuyama, Japão", "Otaru, Japão", "Hakodate, Japão", "Kawagoe, Japão",
    "Ise, Japão", "Beppu, Japão", "Atami, Japão", "Chiba, Japão", "Saitama, Japão",
    "Shizuoka, Japão", "Hamamatsu, Japão", "Okayama, Japão", "Kurashiki, Japão", "Himeji, Japão",

    # --- ITÁLIA (História, Gastronomia, Ilhas e Arte) ---
    "Roma, Itália", "Milão, Itália", "Veneza, Itália", "Florença, Itália", "Nápoles, Itália",
    "Turim, Itália", "Bolonha, Itália", "Verona, Itália", "Gênova, Itália", "Pisa, Itália",
    "Siena, Itália", "Palermo, Itália", "Catânia, Itália", "Bari, Itália", "Perúgia, Itália",
    "Siracusa, Itália", "Lecce, Itália", "Moscazzano, Itália", "Aosta, Itália", "Bolzano, Itália",
    "Trieste, Itália", "Ravena, Itália", "Párnia, Itália", "Mântua, Itália", "Matera, Itália",
    "Positano, Itália", "Amalfi, Itália", "San Gimignano, Itália", "Assis, Itália", "Taormina, Itália",

    # --- FRANÇA (Cultura, Vinhedos, Litoral e Alpes) ---
    "Paris, França", "Nice, França", "Lyon, França", "Marseille, França", "Bordeaux, França",
    "Estrasburgo, França", "Toulouse, França", "Lille, França", "Nantes, França", "Montpellier, França",
    "Cannes, França", "Aix-en-Provence, França", "Avignon, França", "Carcassonne, França", "Annecy, França",
    "Chamonix, França", "Rouen, França", "Rennes, França", "Dijon, França", "Reims, França",
    "Colmar, França", "Biarrits, França", "Saint-Malo, França", "Blois, França", "Tours, França",

    # --- ESPANHA E PORTUGAL (Península Ibérica) ---
    "Madrid, Espanha", "Barcelona, Espanha", "Sevilha, Espanha", "Valência, Espanha", "Granada, Espanha",
    "Málaga, Espanha", "Bilbau, Espanha", "San Sebastián, Espanha", "Toledo, Espanha", "Córdoba, Espanha",
    "Santiago de Compostela, Espanha", "Salamanca, Espanha", "Saragoça, Espanha", "Palma de Maiorca, Espanha", "Ibiza, Espanha",
    "Lisboa, Portugal", "Porto, Portugal", "Coimbra, Portugal", "Braga, Portugal", "Évora, Portugal",
    "Faro, Portugal", "Sintra, Portugal", "Cascais, Portugal", "Guimarães, Portugal", "Aveiro, Portugal",
    "Funchal, Portugal", "Ponta Delgada, Portugal", "Viseu, Portugal", "Tomar, Portugal", "Lagos, Portugal",

    # --- ESTADOS UNIDOS E CANADÁ ---
    "Nova York, Estados Unidos", "Los Angeles, Estados Unidos", "Chicago, Estados Unidos", "Miami, Estados Unidos", "São Francisco, Estados Unidos",
    "Las Vegas, Estados Unidos", "Orlando, Estados Unidos", "Seattle, Estados Unidos", "Boston, Estados Unidos", "Washington D.C., Estados Unidos",
    "Austin, Estados Unidos", "Nova Orleans, Estados Unidos", "San Diego, Estados Unidos", "Honolulu, Estados Unidos", "Denver, Estados Unidos",
    "Philadelphia, Estados Unidos", "Atlanta, Estados Unidos", "Dallas, Estados Unidos", "Houston, Estados Unidos", "Nashville, Estados Unidos",
    "Portland, Estados Unidos", "Salt Lake City, Estados Unidos", "Anchorage, Estados Unidos", "Savannah, Estados Unidos", "Charleston, Estados Unidos",
    "Toronto, Canadá", "Vancouver, Canadá", "Montreal, Canadá", "Quebec City, Canadá", "Ottawa, Canadá",
    "Calgary, Canadá", "Edmonton, Canadá", "Victoria, Canadá", "Halifax, Canadá", "Banff, Canadá",

    # --- ALEMANHA, REINO UNIDO E IRLANDA ---
    "Londres, Reino Unido", "Edimburgo, Escócia", "Manchester, Reino Unido", "Liverpool, Reino Unido", "Oxford, Reino Unido",
    "Cambridge, Reino Unido", "Bath, Reino Unido", "Glasgow, Escócia", "Belfast, Irlanda do Norte", "Cardiff, País de Gales",
    "Dublin, Irlanda", "Galway, Irlanda", "Cork, Irlanda", "Killarney, Irlanda", "Limerick, Irlanda",
    "Berlim, Alemanha", "Munique, Alemanha", "Frankfurt, Alemanha", "Hamburgo, Alemanha", "Colônia, Alemanha",
    "Heidelberg, Alemanha", "Dresden, Alemanha", "Nuremberg, Alemanha", "Stuttgart, Alemanha", "Leipzig, Alemanha",

    # --- AMÉRICA DO SUL (Sem Brasil) ---
    "Buenos Aires, Argentina", "Bariloche, Argentina", "Mendoza, Argentina", "Córdoba, Argentina", "Ushuaia, Argentina",
    "Salta, Argentina", "Rosário, Argentina", "El Calafate, Argentina", "Puerto Iguazú, Argentina", "Mar del Plata, Argentina",
    "Santiago, Chile", "Valparaíso, Chile", "San Pedro de Atacama, Chile", "Pucón, Chile", "Punta Arenas, Chile",
    "Montevidéu, Uruguai", "Colonia del Sacramento, Uruguai", "Punta del Este, Uruguai", "Salto, Uruguai", "Rocha, Uruguai",
    "Cusco, Peru", "Lima, Peru", "Arequipa, Peru", "Puno, Peru", "Iquitos, Peru",
    "Bogotá, Colômbia", "Cartagena, Colômbia", "Medellín, Colômbia", "Cali, Colômbia", "Santa Marta, Colômbia",
    "Quito, Equador", "Guayaquil, Equador", "Cuenca, Equador", "Baños, Equador", "Galápagos (Puerto Ayora), Equador",
    "La Paz, Bolívia", "Sucre, Bolívia", "Uyuni, Bolívia", "Santa Cruz de la Sierra, Bolívia", "Cochabamba, Bolívia",
    "Assunção, Paraguai", "Encarnación, Paraguai", "Ciudad del Este, Paraguai", "Paramaribo, Suriname", "Caiena, Guiana Francesa",

    # --- MÉXICO, AMÉRICA CENTRAL E CARIBE ---
    "Cidade do México, México", "Cancún, México", "Guadalajara, México", "Oaxaca, México", "Guanajuato, México",
    "Playa del Carmen, México", "Mérida, México", "San Miguel de Allende, México", "Monterrey, México", "Puebla, México",
    "Tulum, México", "Cabo San Lucas, México", "Puerto Vallarta, México", "Querétaro, México", "Morelia, México",
    "Havana, Cuba", "Trinidad, Cuba", "Santiago de Cuba, Cuba", "San José, Costa Rica", "Tamarindo, Costa Rica",
    "Cidade do Panamá, Panamá", "Bocas del Toro, Panamá", "Antigua, Guatemala", "Cidade da Guatemala, Guatemala", "San Salvador, El Salvador",
    "Tegucigalpa, Honduras", "Roatán, Honduras", "Manágua, Nicarágua", "Granada, Nicarágua", "San Juan, Porto Rico",
    "Santo Domingo, República Dominicana", "Punta Cana, República Dominicana", "Kingston, Jamaica", "Montego Bay, Jamaica", "Nassau, Bahamas",

    # --- ÁSIA (China, Coreia, Sudeste Asiático e Índia) ---
    "Seul, Coreia do Sul", "Busan, Coreia do Sul", "Incheon, Coreia do Sul", "Jeju, Coreia do Sul", "Gyeongju, Coreia do Sul",
    "Xangai, China", "Pequim, China", "Xi'an, China", "Chengdu, China", "Guilin, China",
    "Hangzhou, China", "Shenzhen, China", "Guangzhou, China", "Lhasa, Tibet (China)", "Hong Kong, China",
    "Bangcoc, Tailândia", "Chiang Mai, Tailândia", "Phuket, Tailândia", "Ayutthaya, Tailândia", "Krabi, Tailândia",
    "Hanói, Vietnã", "Ho Chi Minh (Saigon), Vietnã", "Hoi An, Vietnã", "Da Nang, Vietnã", "Hue, Vietnã",
    "Singapura", "Kuala Lumpur, Malásia", "Penang, Malásia", "Malaca, Malásia", "Langkawi, Malásia",
    "Djakarta, Indonésia", "Ubud (Bali), Indonésia", "Yogyakarta, Indonésia", "Lombok, Indonésia", "Komodo, Indonésia",
    "Manila, Filipinas", "Cebu, Filipinas", "El Nido (Palawan), Filipinas", "Boracay, Filipinas", "Siem Reap, Camboja",
    "Phnom Penh, Camboja", "Luang Prabang, Laos", "Vientiane, Laos", "Yangon, Mianmar", "Bagan, Mianmar",
    "Nova Délhi, Índia", "Mumbai, Índia", "Jaipur, Índia", "Agra, Índia", "Varanasi, Índia",
    "Udaipur, Índia", "Goa, Índia", "Kolkata, Índia", "Bengaluru, Índia", "Kochi, Índia",

    # --- EUROPA CENTRAL, LESTE EUROPEU E NÓRDICOS ---
    "Amsterdã, Holanda", "Roterdã, Holanda", "Haia, Holanda", "Utrecht, Holanda", "Groningen, Holanda",
    "Bruxelas, Bálgica", "Bruges, Bálgica", "Gente, Bálgica", "Antuérpia, Bálgica", "Luxemburgo, Luxemburgo",
    "Viena, Áustria", "Salzburgo, Áustria", "Innsbruck, Áustria", "Graz, Áustria", "Hallstatt, Áustria",
    "Zurique, Suíça", "Genebra, Suíça", "Lucerna, Suíça", "Interlaken, Suíça", "Basileia, Suíça",
    "Praga, República Tcheca", "Ceský Krumlov, República Tcheca", "Brno, República Tcheca", "Bratislava, Eslováquia", "Budapeste, Hungria",
    "Varsóvia, Polônia", "Cracóvia, Polônia", "Gdańsk, Polônia", "Wrocław, Polônia", "Poznań, Polônia",
    "Copenhague, Dinamarca", "Aarhus, Dinamarca", "Estocolmo, Suécia", "Gotemburgo, Suécia", "Malmö, Suécia",
    "Oslo, Noruega", "Bergen, Noruega", "Tromsø, Noruega", "Stavanger, Noruega", "Helsinque, Finlândia",
    "Rovaniemi, Finlândia", "Tampere, Finlândia", "Reiquiavique, Islândia", "Akureyri, Islândia", "Tallinn, Estônia",
    "Riga, Letônia", "Vilnius, Lituânia", "Bucareste, Romênia", "Brașov, Romênia", "Sibiu, Romênia",
    "Sófia, Bulgária", "Plovdiv, Bulgária", "Belgrado, Sérvia", "Zagreb, Croácia", "Dubrovnik, Croácia",
    "Split, Croácia", "Zadar, Croácia", "Ljubljana, Eslovênia", "Bled, Eslovênia", "Sarajevo, Bósnia e Herzegovina",
    "Mostar, Bósnia e Herzegovina", "Kotor, Montenegro", "Ohrid, Macedônia do Norte", "Tirana, Albânia", "Valletta, Malta",

    # --- MEDITERRÂNEO, ORIENTE MÉDIO E ÁSIA CENTRAL ---
    "Atenas, Grécia", "Santorini, Grécia", "Míconos, Grécia", "Salônica, Grécia", "Rodes, Grécia",
    "Meteora, Grécia", "Cefalônia, Grécia", "Meteora, Grécia", "Nicósia, Chipre", "Paphos, Chipre",
    "Istambul, Turquia", "Capadócia (Göreme), Turquia", "Antália, Turquia", "Éfeso, Turquia", "Bodrum, Turquia",
    "Esmirna, Turquia", "Bursa, Turquia", "Pamukkale, Turquia", "Trabzon, Turquia", "Ancara, Turquia",
    "Tel Aviv, Israel", "Jerusalém, Israel", "Haifa, Israel", "Amã, Jordânia", "Petra, Jordânia",
    "Wadi Rum, Jordânia", "Beirute, Líbano", "Byblos, Líbano", "Mascate, Omã", "Salalah, Omã",
    "Dubai, Emirados Árabes Unidos", "Abu Dhabi, Emirados Árabes Unidos", "Doha, Catar", "Manama, Bahrein", "Al Ula, Arábia Saudita",
    "Riad, Arábia Saudita", "Jidá, Arábia Saudita", "Tbilisi, Geórgia", "Batumi, Geórgia", "Erevan, Armênia",
    "Baku, Azerbaijão", "Tashkent, Uzbequistão", "Samarcanda, Uzbequistão", "Bukhara, Uzbequistão", "Almaty, Cazaquistão",

    # --- ÁFRICA (Norte, Leste, Oeste e Sul) ---
    "Cairo, Egito", "Alexandria, Egito", "Luxor, Egito", "Aswan, Egito", "Sharm El Sheikh, Egito",
    "Marrakech, Marrocos", "Fès, Marrocos", "Chefchaouen, Marrocos", "Casablanca, Marrocos", "Essaouira, Marrocos",
    "Túnis, Tunísia", "Sousse, Tunísia", "Djerba, Tunísia", "Argel, Argélia", "Oran, Argélia",
    "Cidade do Cabo, África do Sul", "Joanesburgo, África do Sul", "Durban, África do Sul", "Kruger (Skukuza), África do Sul", "Stellenbosch, África do Sul",
    "Nairóbi, Quênia", "Mombaça, Quênia", "Zanzibar, Tanzânia", "Dar es Salaam, Tanzânia", "Arusha, Tanzânia",
    "Vitória Falls, Zimbábue", "Livingstone, Zâmbia", "Windhoek, Namíbia", "Swakopmund, Namíbia", "Kasane, Botsuana",
    "Dakar, Senegal", "Saint-Louis, Senegal", "Acra, Gana", "Cape Coast, Gana", "Lagos, Nigéria",
    "Mali, Bamako", "Praia, Cabo Verde", "Mindelo, Cabo Verde", "Santo Antão, Cabo Verde", "São Tomé, São Tomé e Príncipe",
    "Antananarivo, Madagascar", "Nosy Be, Madagascar", "Port Louis, Maurício", "Victoria, Seychelles", "Moroni, Comores",

    # --- OCEANIA E ILHAS DO PACÍFICO ---
    "Sydney, Austrália", "Melbourne, Austrália", "Brisbane, Austrália", "Perth, Austrália", "Cairns, Austrália",
    "Adelaide, Austrália", "Gold Coast, Austrália", "Hobart (Tasmânia), Austrália", "Darwin, Austrália", "Byron Bay, Austrália",
    "Auckland, Nova Zelândia", "Queenstown, Nova Zelândia", "Wellington, Nova Zelândia", "Christchurch, Nova Zelândia", "Rotorua, Nova Zelândia",
    "Suva, Fiji", "Nadi, Fiji", "Port Vila, Vanuatu", "Apia, Samoa", "Papeete (Taiti), Polinésia Francesa",
    "Bora Bora, Polinésia Francesa", "Nouméa, Nova Caledônia", "Koror, Palau", "Hononi, Ilhas Salomão", "Majuro, Ilhas Marshall",

    # --- ÁSIA DO SUL, RÚSSIA E OUTROS DESTINOS ---
    "Moscou, Rússia", "São Petersburgo, Rússia", "Kazan, Rússia", "Sochi, Rússia", "Vladivostok, Rússia",
    "Irkutsk (Lago Baikal), Rússia", "Murmansk, Rússia", "Ulaanbaatar, Mongólia", "Thimphu, Butão", "Paro, Butão",
    "Katmandu, Nepal", "Pokhara, Nepal", "Colombo, Sri Lanka", "Kandy, Sri Lanka", "Galle, Sri Lanka",
    "Sigiriya, Sri Lanka", "Malé, Maldivas", "Dhaka, Bangladesh", "Chittagong, Bangladesh", "Islamabad, Paquistão",
    "Lahore, Paquistão", "Karachi, Paquistão", "Skardu, Paquistão", "Kabul, Afeganistão", "Teerã, Irã",
    "Isfahan, Irã", "Shiraz, Irã", "Yazd, Irã", "Tabriz, Irã", "Masqat, Omã",

    # --- CIDADES HISTÓRICAS, PEQUENAS VILAS E CURIOSIDADES GLOBAIS ---
    "Giverny, França", "Hallstatt, Áustria", "Rothenburg ob der Tauber, Alemanha", "Giethoorn, Holanda", "Cinque Terre (Vernazza), Itália",
    "Shirakawa-go, Japão", "Hobbiton (Matamata), Nova Zelândia", "Sidi Bou Said, Tunísia", "Chefchaouen, Marrocos", "Bled, Eslovênia",
    "Oia, Grécia", "Cochem, Alemanha", "Reine (Ilhas Lofoten), Noruega", "Mostar, Bósnia", "Sighişoara, Romênia",
    "Albarracín, Espanha", "Ronda, Espanha", "Mittenwald, Alemanha", "Bagnone, Itália", "Bibury, Reino Unido",
    "Portree (Ilha de Skye), Escócia", "Kinsale, Irlanda", "Dinant, Bélgica", "Gruyères, Suíça", "Zermatt, Suíça",
    "Sankt Moritz, Suíça", "Eguisheim, França", "Riquewihr, França", "Castelmezzano, Itália", "Tropea, Itália",
    "Piran, Eslovênia", "Rovinj, Croácia", "Korčula, Croácia", "Kotor, Montenegro", "Perast, Montenegro",
    "Kruja, Albânia", "Berat, Albânia", "Ohrid, Macedônia do Norte", "Veliko Tarnovo, Bulgária", "Nessebar, Bulgária",
    "Bamberg, Alemanha", "Quedlinburg, Alemanha", "Cesky Krumlov, República Tcheca", "Telč, República Tcheca", "Kazimierz Dolny, Polônia",
    "Trakai, Lituânia", "Sigulda, Letônia", "Haapsalu, Estônia", "Porvoo, Finlândia", "Sigtuna, Suécia",
    "Ærøskøbing, Dinamarca", "Vik, Islândia", "Seyðisfjörður, Islândia", "Longyearbyen, Noruega", "Kiruna, Suécia",
    "Ouro Preto, Brasil", "Tiradentes, Brasil", "Paraty, Brasil", "Lençóis, Brasil", "Pirenópolis, Brasil",
    "São Luiz do Paraitinga, Brasil", "Alcântara, Brasil", "Goiás Velho, Brasil", "Laranjeiras, Brasil", "Marechal Deodoro, Brasil",
    "San Pedro de Atacama, Chile", "Bariloche, Argentina", "Colonia del Sacramento, Uruguai", "Baños, Equador", "Cusco, Peru",
    "Ollantaytambo, Peru", "Villa de Leyva, Colômbia", "Guatapé, Colômbia", "Barichara, Colômbia", "Jericó, Colômbia",
    "San Miguel de Allende, México", "Guanajuato, México", "Taxco, México", "Tepoztlán, México", "Izamal, México",
    "Antigua, Guatemala", "Suchitoto, El Salvador", "Granada, Nicarágua", "Trinidad, Cuba", "Viñales, Cuba",
    "Jiufen, Taiwan", "Tainan, Taiwan", "Takayama, Japão", "Shirakawa, Japão", "Kurashiki, Japão",
    "Luang Prabang, Laos", "Hoi An, Vietnã", "Bagan, Mianmar", "Inle Lake, Mianmar", "Ella, Sri Lanka",
    "Pushkar, Índia", "Rishikesh, Índia", "Leh (Ladakh), Índia", "Pokhara, Nepal", "Paro, Butão",
    "Kandovan, Irã", "Meymand, Irã", "Al Ula, Arábia Saudita", "Wadi Rum, Jordânia", "Byblos, Líbano",
    "Sidi Bou Said, Tunísia", "Chefchaouen, Marrocos", "Essaouira, Marrocos", "Ait Benhaddou, Marrocos", "Siwa, Egito",
    "Lamu, Quênia", "Stone Town (Zanzibar), Tanzânia", "Ilha de Moçambique, Moçambique", "Cidade Velha, Cabo Verde", "Grand-Bassam, Costa do Marfim"
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


IMAGEM_PADRAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/News_icon.svg/640px-News_icon.svg.png"


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
    return response.choices[0].message.content.strip()


def gerar_esqueleto(cidade):
    prompt = f"""
Voce e um redator de viagens especializado em encontrar cantos curiosos e pouco conhecidos
de grandes cidades.

Cidade de hoje: {cidade}

Escolha UM lugar, historia ou curiosidade REAL, especifica e pouco conhecida dessa cidade
(um museu incomum, um bairro secreto, uma lenda urbana, uma curiosidade arquitetonica, um
fato historico bizarro) - algo que voce tenha confianca real de que existe, sem inventar
nomes ou fatos.

Monte um ESQUELETO com:
- O nome exato do lugar/curiosidade escolhido.
- 5 a 6 topicos que o artigo vai cobrir (contexto/historia, o que torna especial, curiosidades,
  como e a experiencia de visitar, dicas praticas gerais).
- 1-2 frases resumindo cada topico, sem repetir informacao entre eles.

Responda so o esqueleto, texto simples.
"""
    return pedir_ia_groq(prompt, temperatura=0.6)


def gerar_artigo_completo(esqueleto, cidade):
    prompt = f"""
Voce e um redator de viagens premiado, escrevendo para um blog de curiosidades urbanas do
mundo todo. Escreva com capricho, sem pressa.

Cidade: {cidade}
Esqueleto obrigatorio a seguir (desenvolva cada topico em profundidade, sem repetir):
{esqueleto}

REGRAS DE CONTEUDO E PRECISAO:
- Baseie-se em fatos reais e conhecidos. NAO invente numeros de endereco, horarios de
  funcionamento especificos, precos de ingresso ou dados que podem estar desatualizados -
  para esse tipo de informacao pratica, oriente o leitor a confirmar no site oficial do
  local antes de visitar, em vez de fabricar um dado especifico.
- PROIBIDO repetir a mesma ideia com palavras diferentes.
- Tamanho: entre 900 e 1400 palavras, bem escrito e envolvente.

REGRAS DE FORMATO (HTML puro, sem Markdown):
1. Paragrafo de abertura instigante.
2. Cada topico do esqueleto vira um subtitulo <h2> proprio.
3. Inclua 2 notas do autor leves e engracadas, cada uma dentro de <blockquote>.
4. Nao inclua links no corpo do texto.
5. Termine com um paragrafo convidando o leitor a comentar se ja foi nessa cidade ou
   conhece esse lugar, e a compartilhar com quem ama viajar.
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
