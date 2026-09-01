# Importa o módulo 'datetime' para carimbar a data e hora na planilha e logs
from datetime import datetime
# Importa a biblioteca do Streamlit para criar a interface web
import streamlit as st
# Importa a biblioteca do Google Gemini para processar a inteligência artificial
import google.generativeai as genai
# Importa a biblioteca yfinance para buscar as cotações financeiras em tempo real
import yfinance as yf
# Importa a biblioteca gspread para manipular planilhas do Google Sheets
import gspread
# Importa o módulo Credentials para autenticar a conta de serviço do Google
from google.oauth2.service_account import Credentials
# Importa a biblioteca json para ler as credenciais protegidas no cofre do Streamlit
import json
# Importa a biblioteca requests para fazer chamadas em APIs web (como a de clima)
import requests

# --- BLOCO 1: INTEGRAÇÃO COM GOOGLE SHEETS ---
# Define a função responsável por gravar os resultados diretamente no Google Sheets
def salvar_no_sheets(bolsa, clima, macro, veredito):
    # Inicia o bloco de tentativa para capturar possíveis erros de conexão sem travar o app
    try:
        # Define os escopos de permissão necessários (acesso ao Sheets e ao Drive)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        # Puxa o texto do JSON salvo no cofre (st.secrets) e converte para dicionário Python
        credenciais_json = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        # Cria o objeto de credencial usando as informações do JSON e os escopos liberados
        credentials = Credentials.from_service_account_info(credenciais_json, scopes=scopes)
        # Autoriza a conexão com o servidor do Google usando as credenciais criadas
        cliente = gspread.authorize(credentials)
        
        # Abre a planilha pelo nome exato no seu Drive e acessa a primeira aba (sheet1)
        planilha = cliente.open("Base_Agente_Cafe").sheet1
        
        # Captura a data e a hora do momento da análise no formato padrão brasileiro
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        # Cria uma lista ordenada contendo todos os dados que formarão a nova linha no Excel
        nova_linha = [data_hora, bolsa, clima, macro, veredito]
        
        # Insere a lista inteira como uma nova linha na primeira fileira vazia encontrada na planilha
        planilha.append_row(nova_linha)
        # Exibe uma mensagem de sucesso verde na tela para o usuário confirmar a gravação
        st.success("Análise registrada com sucesso na sua planilha Base_Agente_Cafe!")
        
    # Captura qualquer erro ocorrido durante o processo de comunicação ou gravação
    except Exception as e:
        # Exibe um alerta de erro em vermelho na tela contendo o detalhe técnico da falha
        st.error(f"Erro ao salvar no Google Sheets: {e}")

# --- BLOCO 2: BUSCA AUTOMÁTICA DE CLIMA (NOVO) ---
# Define a função que busca as previsões do tempo via Open-Meteo API
def buscar_dados_clima():
    # Inicia o bloco de tentativa para prevenir que uma falha de rede quebre a aplicação
    try:
        # Dicionário mapeando os polos produtores com suas respectivas Latitudes e Longitudes
        regioes_cafe = {
            "Sul de Minas": {"lat": -21.37, "lon": -45.46},
            "Cerrado Mineiro": {"lat": -18.94, "lon": -46.99}
        }
        
        # Cria uma variável vazia (string) que vai acumular os textos das previsões
        texto_clima_final = ""
        
        # Inicia um loop de repetição para passar por cada região listada no dicionário acima
        for nome_regiao, coords in regioes_cafe.items():
            # Monta a URL da API injetando a latitude e longitude da região atual do loop (previsão de 3 dias)
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&daily=temperature_2m_max,precipitation_sum&timezone=America%2FSao_Paulo&forecast_days=3"
            
            # Executa a requisição web GET na URL e converte a resposta para formato JSON (dicionário)
            resposta = requests.get(url).json()
            
            # Navega no JSON da resposta para extrair a lista com a soma de chuva dos 3 dias
            chuva_diaria = resposta['daily']['precipitation_sum']
            # Navega no JSON da resposta para extrair a lista de temperaturas máximas dos 3 dias
            temp_diaria = resposta['daily']['temperature_2m_max']
            
            # Soma as chuvas dos 3 dias para ter o volume acumulado do período
            chuva_total_3dias = sum(chuva_diaria)
            # Encontra a temperatura mais alta prevista para essa janela de 3 dias
            temp_max_3dias = max(temp_diaria)
            
            # Adiciona um parágrafo formatado à nossa variável de texto final com os dados desta região
            texto_clima_final += f"*{nome_regiao}:* Previsão de {chuva_total_3dias:.1f}mm acumulados nos próximos 3 dias. Temperatura máxima de {temp_max_3dias}°C.\n"
            
        # Retorna o texto consolidado com o resumo climático de todas as regiões mapeadas
        return texto_clima_final
        
    # Tratamento de erro caso a API de clima esteja fora do ar ou sem internet
    except Exception as e:
        # Retorna uma mensagem amigável permitindo que o usuário digite o clima à mão se a API falhar
        return "Erro ao buscar clima. Por favor, insira manualmente."

# --- BLOCO 3: BUSCA AUTOMÁTICA DO MERCADO FINANCEIRO ---
# Define a função que busca as cotações na biblioteca do Yahoo Finance
def buscar_dados_mercado():
    # Inicia a tentativa de conexão com a API de mercado para evitar travamentos
    try:
        # Define o ticker (código) do café arábica na bolsa ICE de Nova York
        cafe_ticker = yf.Ticker("KC=F")
        # Captura o preço exato do fechamento da sessão do dia anterior usando fast_info
        cafe_fechamento_ontem = cafe_ticker.fast_info['previousClose']
        # Captura o preço em tempo real no momento exato desta consulta
        cafe_preco_atual = cafe_ticker.fast_info['lastPrice']
        
        # Estrutura de proteção matemática para garantir que não haverá divisão por zero
        if cafe_fechamento_ontem > 0:
            # Calcula o delta (variação percentual) comparando o preço atual com o fechamento anterior
            var_cafe_pct = ((cafe_preco_atual - cafe_fechamento_ontem) / cafe_fechamento_ontem) * 100
        # Caso a cotação base seja retornada como zero por uma falha do Yahoo
        else:
            # Trava a variação em 0.0 para não estourar erro de cálculo
            var_cafe_pct = 0.0
            
        # Avalia a variação matemática para definir a palavra de viés direcional
        if var_cafe_pct > 0:
            # Variação maior que zero recebe o status nominal de Alta
            direcao_cafe = "Alta"
        elif var_cafe_pct < 0:
            # Variação menor que zero recebe o status nominal de Queda
            direcao_cafe = "Queda"
        else:
            # Variação cravada em zero recebe o status de Estabilidade
            direcao_cafe = "Estabilidade"

        # Define o ticker (código) do Dólar comercial brasileiro em relação ao Real
        dolar_ticker = yf.Ticker("BRL=X")
        # Captura o fechamento oficial anterior da taxa de câmbio
        dolar_fechamento_ontem = dolar_ticker.fast_info['previousClose']
        # Captura a cotação atual operada no mercado de câmbio
        dolar_preco_atual = dolar_ticker.fast_info['lastPrice']
        
        # Proteção matemática espelhada para a base cambial
        if dolar_fechamento_ontem > 0:
            # Calcula a oscilação percentual diária do dólar
            var_dolar_pct = ((dolar_preco_atual - dolar_fechamento_ontem) / dolar_fechamento_ontem) * 100
        # Condição de segurança caso o fechamento do dólar não seja lido corretamente
        else:
            # Zera o percentual de variação por segurança
            var_dolar_pct = 0.0
            
        # Avalia a oscilação cambial para definir seu comportamento verbal
        if var_dolar_pct > 0:
            # Dólar subindo
            direcao_dolar = "Alta"
        elif var_dolar_pct < 0:
            # Dólar caindo
            direcao_dolar = "Queda"
        else:
            # Dólar no zero a zero
            direcao_dolar = "Estabilidade"
        
        # Formata a string de saída contendo as informações financeiras completas da Bolsa de NY
        texto_bolsa = (
            f"Fechamento Anterior (ICE NY): {cafe_fechamento_ontem:.2f} c/lb\n"
            f"Cotação Atual: {cafe_preco_atual:.2f} c/lb | Variação: {direcao_cafe} de {var_cafe_pct:.2f}%"
        )
        
        # Formata a string de saída contendo a matriz macroeconômica de câmbio
        texto_macro = (
            f"Fechamento Anterior (Dólar): R$ {dolar_fechamento_ontem:.4f}\n"
            f"Cotação Atual: R$ {dolar_preco_atual:.4f} | Variação: {direcao_dolar} de {var_dolar_pct:.2f}%"
        )
        
        # Retorna as duas matrizes de texto prontas para serem injetadas nos componentes da interface
        return texto_bolsa, texto_macro
    
    # Exceção geral para capturar indisponibilidade da API do Yahoo ou bloqueios de firewall
    except Exception as e:
        # Retorna textos de aviso permitindo que a operação humana não seja interrompida
        return "Erro ao buscar dados automáticos. Insira manualmente.", "Erro ao buscar dados automáticos. Insira manualmente."

# --- INTERFACE GRÁFICA (FRONT-END STREAMLIT) ---
# Configura a renderização da página web para usar toda a largura do monitor do usuário
st.set_page_config(layout="wide")
# Renderiza o cabeçalho principal (H1) do aplicativo no topo da tela
st.title("Agente Analista de Sentimento: Café Arábica Global")
# Renderiza um texto auxiliar explicando o fluxo de automação da ferramenta
st.write("Dados de bolsa e clima importados automaticamente. A análise será salva no Google Sheets.")

# Executa a função financeira e desempacota os resultados nas variáveis da bolsa e macro
auto_bolsa, auto_macro = buscar_dados_mercado()
# Executa a função meteorológica e guarda o texto formatado na variável de clima
auto_clima = buscar_dados_clima()

# Monta o campo de texto 1, preenchendo automaticamente com os dados da ICE
dados_bolsa = st.text_area("1. Bolsa de NY (ICE) e Mercado Futuro:", value=auto_bolsa, height=120)
# Monta o campo de texto 2, PREENCHENDO AGORA AUTOMATICAMENTE com a previsão do Open-Meteo
dados_clima = st.text_area("2. Clima nas Regiões Produtoras (Próximos 3 dias):", value=auto_clima, height=120)
# Monta o campo de texto 3, preenchendo automaticamente com a cotação cambial do BRL
dados_macro = st.text_area("3. Câmbio (Dólar) e Macroeconomia:", value=auto_macro, height=120)

# Renderiza o botão de submissão primário que fará o trigger de toda a operação de IA
botao_analisar = st.button("Analisar Cenário Cruzado")

# Escuta permanentemente o estado lógico do botão (True se foi clicado)
if botao_analisar:
    # Trava de segurança: impede gasto de token na API se os campos base estiverem vazios
    if dados_bolsa or dados_clima or dados_macro:
        # Aciona o componente de carregamento visual (spinner) enquanto a IA processa o *prompt*
        with st.spinner('O Agente está cruzando as variáveis do mercado e salvando no Sheets...'):
            # Inicia o bloco restrito de comunicação com serviços externos de IA
            try:
                # Conecta ao serviço do Google Gemini resgatando a chave do cofre blindado (Secrets)
                genai.configure(api_key=st.secrets["CHAVE_GEMINI"])
                # Instancia o objeto do modelo utilizando a versão flash para otimizar velocidade
                modelo = genai.GenerativeModel('gemini-3.6-flash')
                
                # Constrói o texto do prompt unindo as regras de negócio de exportação e os inputs da tela
                prompt_sistema = f"""
                Você é um analista sênior de inteligência focado exclusivamente no mercado internacional de café arábica.
                Cruze as informações das três frentes fornecidas abaixo e estruture um resumo executivo avançado.
                
                Instrução Crítica: Avalie o sentimento com base na VARIAÇÃO DIÁRIA (Cotação Atual vs Fechamento Anterior).

                Regra estrita e inquebrável: Remova, ignore e não cite qualquer referência a preços físicos de mercado interno, especialmente valores praticados pelas cooperativas.

                Variáveis a serem analisadas:
                1. Bolsa de NY (ICE): {dados_bolsa}
                2. Clima nas Regiões Produtoras: {dados_clima}
                3. Macroeconomia e Câmbio (Dólar): {dados_macro}

                Sua resposta deve conter exatamente a seguinte estrutura:
                * Sentimento Geral Integrado: (ALTISTA, BAIXISTA ou NEUTRO)
                * Análise Cruzada: (Avalie em 1 parágrafo como o clima e o câmbio potencializam ou atenuam o movimento da Bolsa)
                * Impactos na Exportação: (Avalie em 1 parágrafo curto como esse cenário afeta a fixação de novos contratos internacionais)
                * Mitigação de Risco: (Sugira em 1 parágrafo curto os pontos de atenção imediatos para proteção financeira)
                """
                
                # Executa a chamada HTTPS para a rede neural e aguarda a geração da análise final
                resposta_ia = modelo.generate_content(prompt_sistema)
                # Extrai o texto limpo da resposta empacotada retornada pela API do Gemini
                texto_resposta = resposta_ia.text
                
                # Adiciona uma linha horizontal estilizada para separar visualmente os parâmetros do resultado final
                st.divider()
                # Imprime um subtítulo em destaque indicando o início do parecer da IA
                st.subheader("Veredito Avançado do Agente:")
                # Renderiza o conteúdo textual completo gerado pelo Gemini na interface
                st.write(texto_resposta)
                
                # Executa a função assíncrona passando todos os dados consolidados para registrar a linha no Google Sheets
                salvar_no_sheets(dados_bolsa, dados_clima, dados_macro, texto_resposta)
                
            # Intercepta qualquer falha no processamento da API da inteligência artificial (ex: cota excedida)
            except Exception as erro:
                # Dispara o card de erro vermelho no Streamlit expondo a descrição original da anomalia
                st.error(f"Ocorreu um erro na comunicação com a IA: {erro}")
    # Retorno lógico caso a validação primária dos campos de input falhe
    else:
        # Dispara um alerta em amarelo instruindo o operador a preencher os dados faltantes
        st.warning("Por favor, preencha pelo menos um dos campos de mercado antes de solicitar a análise.")
