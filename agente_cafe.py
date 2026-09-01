# Importa a biblioteca 'streamlit', responsável por criar a interface visual do nosso site
import streamlit as st
# Importa a biblioteca 'google.generativeai' para conectar e enviar comandos para o modelo Gemini
import google.generativeai as genai
# Importa a biblioteca 'yfinance' para extrair as cotações financeiras direto do Yahoo Finance
import yfinance as yf
# Importa a biblioteca 'requests' para fazer o download dos dados de clima da API Open-Meteo
import requests

# --- BLOCO 1: BUSCA AUTOMÁTICA DE CLIMA ---
# Define a função responsável por buscar a previsão do tempo para as regiões cafeeiras
def buscar_dados_clima():
    # Inicia um bloco de tentativa para lidar com possíveis quedas na API de clima
    try:
        # Cria um dicionário contendo as coordenadas geográficas (latitude e longitude) do Sul de Minas e do Cerrado Mineiro
        regioes_cafe = {
            # Coordenadas exatas para a localidade central do Sul de Minas
            "Sul de Minas": {"lat": -21.37, "lon": -45.46},
            # Coordenadas exatas para a localidade central do Cerrado Mineiro
            "Cerrado Mineiro": {"lat": -18.94, "lon": -46.99}
        }
        
        # Cria uma variável de texto vazia para ir acumulando os resultados do clima
        texto_clima_final = ""
        
        # Inicia um laço de repetição que passará por cada região cadastrada no dicionário acima
        for nome_regiao, coords in regioes_cafe.items():
            # Constrói o endereço de internet (URL) da API Open-Meteo inserindo a latitude e longitude da região atual
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&daily=temperature_2m_max,precipitation_sum&timezone=America%2FSao_Paulo&forecast_days=3"
            # Faz a requisição à API, baixa os dados e converte o resultado no formato JSON
            resposta = requests.get(url).json()
            
            # Soma o valor de chuva previsto para os 3 dias daquela região
            chuva_total_3dias = sum(resposta['daily']['precipitation_sum'])
            # Encontra a temperatura máxima prevista entre os 3 dias analisados
            temp_max_3dias = max(resposta['daily']['temperature_2m_max'])
            
            # Formata um parágrafo com os dados da região e adiciona ao texto acumulador
            texto_clima_final += f"*{nome_regiao}:* Previsão de {chuva_total_3dias:.1f}mm acumulados nos próximos 3 dias. Temperatura máxima de {temp_max_3dias}°C.\n"
            
        # Quando o laço terminar, devolve o texto completo com o clima de todas as regiões
        return texto_clima_final
        
    # Caso a API de clima falhe ou não responda
    except Exception as e:
        # Retorna uma mensagem de aviso para que os dados sejam digitados manualmente
        return "Erro ao buscar clima. Por favor, insira manualmente."

# --- BLOCO 2: BUSCA AUTOMÁTICA DO MERCADO FINANCEIRO ---
# Define a função que buscará os dados do contrato futuro de café e da moeda
def buscar_dados_mercado():
    # Inicia um bloco de tentativa para lidar com possíveis falhas no Yahoo Finance
    try:
        # Cria um objeto Ticker apontando para o contrato de Arábica com vencimento em Dezembro de 2026 (KCZ26.NYB)
        cafe_ticker = yf.Ticker("KCZ26.NYB")
        # Solicita à biblioteca o histórico de preços dos últimos 5 dias deste contrato
        hist_cafe = cafe_ticker.history(period="5d")
        
        # Acessa a coluna de fechamento ('Close') e pega a penúltima linha (índice -2), que representa o fechamento do dia útil anterior
        cafe_fechamento_ontem = hist_cafe['Close'].iloc[-2]
        # Pega o preço atual em tempo real usando a propriedade otimizada 'fast_info'
        cafe_preco_atual = cafe_ticker.fast_info['lastPrice']
        
        # Verifica se o preço de fechamento anterior é maior que zero (para evitar erro matemático de divisão por zero)
        if cafe_fechamento_ontem > 0:
            # Calcula a variação percentual entre o preço atual e o preço de fechamento de ontem
            var_cafe_pct = ((cafe_preco_atual - cafe_fechamento_ontem) / cafe_fechamento_ontem) * 100
        # Caso o fechamento venha zerado por instabilidade da bolsa de valores
        else:
            # Define a variação percentual neutra como 0.0 para não quebrar o cálculo e a exibição
            var_cafe_pct = 0.0
            
        # Verifica se a variação percentual calculada foi positiva
        if var_cafe_pct > 0:
            # Atribui a palavra "Alta" à variável para compor o texto visual na tela
            direcao_cafe = "Alta"
        # Verifica se a variação percentual calculada foi negativa
        elif var_cafe_pct < 0:
            # Atribui a palavra "Queda" à variável para compor o texto visual na tela
            direcao_cafe = "Queda"
        # Se a variação percentual for exatamente zero
        else:
            # Atribui a palavra "Estabilidade" para indicar que o mercado não se moveu
            direcao_cafe = "Estabilidade"

        # Cria um objeto Ticker apontando para a cotação oficial cambial do Dólar frente ao Real (BRL=X)
        dolar_ticker = yf.Ticker("BRL=X")
        # Solicita à biblioteca o histórico de fechamentos do Dólar dos últimos 5 dias
        hist_dolar = dolar_ticker.history(period="5d")
        
        # Acessa a coluna de fechamento e extrai o valor exato do encerramento da sessão cambial anterior
        dolar_fechamento_ontem = hist_dolar['Close'].iloc[-2]
        # Pega o valor exato do Dólar negociado neste exato momento
        dolar_preco_atual = dolar_ticker.fast_info['lastPrice']
        
        # Verifica se o fechamento do Dólar é maior que zero de forma lógica
        if dolar_fechamento_ontem > 0:
            # Calcula matematicamente a variação percentual do câmbio Dólar vs Real
            var_dolar_pct = ((dolar_preco_atual - dolar_fechamento_ontem) / dolar_fechamento_ontem) * 100
        # Caso a cotação de ontem retorne um vazio ou zero do provedor
        else:
            # Define a variação macroeconômica neutra como 0.0
            var_dolar_pct = 0.0
            
        # Verifica se o Dólar encareceu em relação ao fechamento anterior
        if var_dolar_pct > 0:
            # Marca a direção descritiva como "Alta"
            direcao_dolar = "Alta"
        # Verifica se o Dólar barateou em relação ao fechamento anterior
        elif var_dolar_pct < 0:
            # Marca a direção descritiva como "Queda"
            direcao_dolar = "Queda"
        # Se não houve nenhum movimento cambial no par de moedas
        else:
            # Marca a direção descritiva como "Estabilidade"
            direcao_dolar = "Estabilidade"
        
        # Formata a string de texto exibindo o valor de fechamento de ontem, cotação de hoje e a diferença consolidada
        texto_bolsa = (
            f"Fechamento Anterior (ICE NY - Dez/26): {cafe_fechamento_ontem:.2f} c/lb\n"
            f"Cotação Atual: {cafe_preco_atual:.2f} c/lb | Variação: {direcao_cafe} de {var_cafe_pct:.2f}%"
        )
        
        # Formata a string contendo os valores do câmbio aplicando quatro casas decimais para precisão do Dólar
        texto_macro = (
            f"Fechamento Anterior (Dólar): R$ {dolar_fechamento_ontem:.4f}\n"
            f"Cotação Atual: R$ {dolar_preco_atual:.4f} | Variação: {direcao_dolar} de {var_dolar_pct:.2f}%"
        )
        
        # Ao final do processamento sem erros, devolve os dois blocos de texto devidamente montados
        return texto_bolsa, texto_macro
    
    # Se houver qualquer falha sistêmica ao tentar contatar o Yahoo Finance para ações ou moedas
    except Exception as e:
        # Retorna frases de fallback instruindo o usuário final a preencher o dado a partir de fonte externa
        return "Erro ao buscar dados automáticos. Insira manualmente.", "Erro ao buscar dados automáticos. Insira manualmente."

# --- INTERFACE GRÁFICA (FRONT-END STREAMLIT) ---
# Instrui a página web a maximizar o seu tamanho útil, desabilitando as bordas laterais gigantescas do layout padrão
st.set_page_config(layout="wide")
# Registra e desenha o Título Primário (H1) formatado em fonte grande no topo da página
st.title("Agente Analista (IA): Café Arábica Global")

# Escreve um parágrafo simples esclarecendo que os dados são apenas gerados na tela
st.write("Dados importados automaticamente. A análise é gerada em tempo real na tela.")

# Executa as leituras de mercado e desempacota o retorno triplo da API nas variáveis auto_bolsa e auto_macro
auto_bolsa, auto_macro = buscar_dados_mercado()
# Executa as leituras de clima da função dedicada e isola o texto retornado na variável auto_clima
auto_clima = buscar_dados_clima()
# Fixa o texto extraído do último boletim climático como condição padrão de El Niño
auto_enso = "Sinopse: O El Niño está se intensificando, com uma probabilidade superior a 90% de ocorrência de um evento muito forte durante o outono e o inverno de 2026-27 no Hemisfério Norte."

# Renderiza em Markdown enriquecido o título da seção de Bolsa contendo a formatação azul de link clicável (<a>)
st.markdown("**1. Bolsa de NY (ICE) e Mercado Futuro** - [(Acessar Yahoo Finance)](https://finance.yahoo.com/quote/KCZ26.NYB/history/)")
# Gera e renderiza um elemento HTML de input de texto estendido, pré-preenchido com o texto formatado do contrato futuro
dados_bolsa = st.text_area("Bolsa", value=auto_bolsa, height=120, label_visibility="collapsed")

# Renderiza em Markdown enriquecido o título da seção Climática incluindo a rota de acesso web à fonte da informação
st.markdown("**2. Clima nas Regiões Produtoras (Próximos 3 dias)** - [(Acessar Fonte: Open-Meteo)](https://open-meteo.com/)")
# Gera a respectiva caixa de input multilinha e a popula imediatamente com as chuvas e graus em Celsius calculados
dados_clima = st.text_area("Clima", value=auto_clima, height=120, label_visibility="collapsed")

# Renderiza em Markdown enriquecido o título focado no fenômeno Oceânico/Atmosférico contendo o acesso à fonte NOAA
st.markdown("**3. Fenômeno Climático Global (El Niño / La Niña)** - [(Acessar Monitoramento NOAA)](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml)")
# Posiciona a caixa de edição e recebe de forma antecipada a previsão extraída do texto sinótico do El Niño
dados_enso = st.text_area("ENSO", value=auto_enso, height=80, label_visibility="collapsed")

# Renderiza em Markdown enriquecido o título da seção Macroeconômica final acoplando o atalho web pertinente
st.markdown("**4. Câmbio (Dólar) e Macroeconomia** - [(Acessar Yahoo Finance)](https://finance.yahoo.com/quote/BRL=X/history/)")
# Materializa o campo de formulário e insere a string de preços de dólar devidamente interpolada e calculada
dados_macro = st.text_area("Macro", value=auto_macro, height=120, label_visibility="collapsed")

# Cria e expõe um botão de ação primário no sistema e guarda na variável True/False caso ele seja pressionado
botao_analisar = st.button("Analisar Cenário Cruzado")

# Dispara a cadeia condicional verificando se o booleano do botão mudou de False para True via clique
if botao_analisar:
    # Levanta uma proteção lógica (if) que impede o envio de dados totalmente brancos ou limpos pelo usuário
    if dados_bolsa or dados_clima or dados_macro or dados_enso:
        # Coloca a interface em estado visual de processamento exibindo uma roda giratória de espera para o usuário
        with st.spinner('O Agente está cruzando as variáveis do mercado e elaborando a análise...'):
            # Aciona a estrutura try/except vital para que um tombo isolado no modelo de IA não congele ou quebre o site inteiro
            try:
                # Injeta nos componentes da biblioteca de nuvem as senhas descriptografadas previamente armazenadas nos Secrets
                genai.configure(api_key=st.secrets["CHAVE_GEMINI"])
                # Associa à variável modelo a identidade da rede neural específica almejada para a inferência analítica avançada
                modelo = genai.GenerativeModel('gemini-3.6-flash')
                
                # Formula em uma grande string multilinha (f-string) todas as ordens sistêmicas de raciocínio da IA (prompt design)
                prompt_sistema = f"""
                Você é um analista sênior de inteligência focado exclusivamente no mercado internacional de café arábica.
                Cruze as informações das quatro frentes fornecidas abaixo e estruture um resumo executivo avançado.
                
                Instrução Crítica: Avalie o sentimento com base na VARIAÇÃO DIÁRIA (Cotação Atual vs Fechamento Anterior).

                Regra estrita e inquebrável: Remova, ignore e não cite qualquer referência a preços físicos de mercado interno, especialmente valores praticados pelas cooperativas.

                Variáveis a serem analisadas:
                1. Bolsa de NY (ICE): {dados_bolsa}
                2. Clima nas Regiões Produtoras: {dados_clima}
                3. Fenômeno Global (El Niño/La Niña): {dados_enso}
                4. Macroeconomia e Câmbio (Dólar): {dados_macro}

                Sua resposta deve conter exatamente a seguinte estrutura:
                * Sentimento Geral Integrado: (ALTISTA, BAIXISTA ou NEUTRO)
                * Análise Cruzada: (Avalie em 1 parágrafo robusto como o clima local, o fenômeno global ENSO e o câmbio potencializam ou atenuam o movimento da Bolsa)
                * Impactos na Exportação: (Avalie em 1 parágrafo curto como esse cenário afeta a fixação de novos contratos internacionais)
                * Mitigação de Risco: (Sugira em 1 parágrafo curto os pontos de atenção imediatos para proteção financeira)
                """
                
                # Transmite os comandos textuais ao provedor em nuvem e armazena de volta na variável local toda a saída em cadeia
                resposta_ia = modelo.generate_content(prompt_sistema)
                # Extrai limpo o texto formatado ignorando todos os demais cabeçalhos técnicos internos empacotados na resposta bruta
                texto_resposta = resposta_ia.text
                
                # Posiciona graficamente um risco divisor leve criando quebra de contexto entre a coleta e a impressão dos resultados
                st.divider()
                # Desenha o cabeçalho secundário (H3) delimitando formalmente a janela de leitura da avaliação
                st.subheader("Veredito Avançado do Agente:")
                # Publica em tempo real a narrativa sintática gerada e avaliada nativamente pela própria Inteligência Artificial
                st.write(texto_resposta)
                
            # Dispara imediatamente o tratamento da exceção caso algum código retorne erros de conexão ou cota esgotada (Status 500/403)
            except Exception as erro:
                # Mostra o log exato de falha envolto numa caixa vermelha elegante orientada ao diagnóstico primário do usuário final
                st.error(f"Ocorreu um erro na comunicação com a IA: {erro}")
    # Quando o usuário inadvertidamente esvaziar tudo na página e forçar a barra do envio desprovido de referências base
    else:
        # Coloca em campo uma mensagem visual laranja obstrutiva requisitando educadamente o reabastecimento mínimo necessário
        st.warning("Por favor, preencha pelo menos um dos campos de mercado antes de solicitar a análise.")
