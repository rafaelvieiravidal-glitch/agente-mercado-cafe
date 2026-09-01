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
def salvar_no_sheets(bolsa, clima, macro, veredito):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credenciais_json = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        credentials = Credentials.from_service_account_info(credenciais_json, scopes=scopes)
        cliente = gspread.authorize(credentials)
        
        planilha = cliente.open("Base_Agente_Cafe").sheet1
        
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        nova_linha = [data_hora, bolsa, clima, macro, veredito]
        
        planilha.append_row(nova_linha)
        st.success("Análise registrada com sucesso na sua planilha Base_Agente_Cafe!")
        
    except Exception as e:
        st.error(f"Erro ao salvar no Google Sheets: {e}")

# --- BLOCO 2: BUSCA AUTOMÁTICA DE CLIMA ---
def buscar_dados_clima():
    try:
        regioes_cafe = {
            "Sul de Minas": {"lat": -21.37, "lon": -45.46},
            "Cerrado Mineiro": {"lat": -18.94, "lon": -46.99}
        }
        
        texto_clima_final = ""
        
        for nome_regiao, coords in regioes_cafe.items():
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&daily=temperature_2m_max,precipitation_sum&timezone=America%2FSao_Paulo&forecast_days=3"
            
            resposta = requests.get(url).json()
            
            chuva_diaria = resposta['daily']['precipitation_sum']
            temp_diaria = resposta['daily']['temperature_2m_max']
            
            chuva_total_3dias = sum(chuva_diaria)
            temp_max_3dias = max(temp_diaria)
            
            texto_clima_final += f"*{nome_regiao}:* Previsão de {chuva_total_3dias:.1f}mm acumulados nos próximos 3 dias. Temperatura máxima de {temp_max_3dias}°C.\n"
            
        return texto_clima_final
        
    except Exception as e:
        return "Erro ao buscar clima. Por favor, insira manualmente."

# --- BLOCO 3: BUSCA AUTOMÁTICA DO MERCADO FINANCEIRO ---
def buscar_dados_mercado():
    try:
        # ATUALIZAÇÃO: Busca apontada especificamente para o contrato de Dezembro/26
        cafe_ticker = yf.Ticker("KCZ26.NYB")
        cafe_fechamento_ontem = cafe_ticker.fast_info['previousClose']
        cafe_preco_atual = cafe_ticker.fast_info['lastPrice']
        
        if cafe_fechamento_ontem > 0:
            var_cafe_pct = ((cafe_preco_atual - cafe_fechamento_ontem) / cafe_fechamento_ontem) * 100
        else:
            var_cafe_pct = 0.0
            
        if var_cafe_pct > 0:
            direcao_cafe = "Alta"
        elif var_cafe_pct < 0:
            direcao_cafe = "Queda"
        else:
            direcao_cafe = "Estabilidade"

        dolar_ticker = yf.Ticker("BRL=X")
        dolar_fechamento_ontem = dolar_ticker.fast_info['previousClose']
        dolar_preco_atual = dolar_ticker.fast_info['lastPrice']
        
        if dolar_fechamento_ontem > 0:
            var_dolar_pct = ((dolar_preco_atual - dolar_fechamento_ontem) / dolar_fechamento_ontem) * 100
        else:
            var_dolar_pct = 0.0
            
        if var_dolar_pct > 0:
            direcao_dolar = "Alta"
        elif var_dolar_pct < 0:
            direcao_dolar = "Queda"
        else:
            direcao_dolar = "Estabilidade"
        
        texto_bolsa = (
            f"Fechamento Anterior (ICE NY - Dez/26): {cafe_fechamento_ontem:.2f} c/lb\n"
            f"Cotação Atual: {cafe_preco_atual:.2f} c/lb | Variação: {direcao_cafe} de {var_cafe_pct:.2f}%"
        )
        
        texto_macro = (
            f"Fechamento Anterior (Dólar): R$ {dolar_fechamento_ontem:.4f}\n"
            f"Cotação Atual: R$ {dolar_preco_atual:.4f} | Variação: {direcao_dolar} de {var_dolar_pct:.2f}%"
        )
        
        return texto_bolsa, texto_macro
    
    except Exception as e:
        return "Erro ao buscar dados automáticos. Insira manualmente.", "Erro ao buscar dados automáticos. Insira manualmente."

# --- INTERFACE GRÁFICA (FRONT-END STREAMLIT) ---
st.set_page_config(layout="wide")
st.title("Agente de IA Analista: Café Arábica Global")
st.write("Dados de bolsa (Contrato Dez/26) e clima importados automaticamente (https://finance.yahoo.com/quote/KCZ26.NYB/history/). A análise será salva no Google Sheets.")

auto_bolsa, auto_macro = buscar_dados_mercado()
auto_clima = buscar_dados_clima()

dados_bolsa = st.text_area("1. Bolsa de NY (ICE) e Mercado Futuro:", value=auto_bolsa, height=120)
dados_clima = st.text_area("2. Clima nas Regiões Produtoras (Próximos 3 dias):", value=auto_clima, height=120)
dados_macro = st.text_area("3. Câmbio (Dólar) e Macroeconomia:", value=auto_macro, height=120)

botao_analisar = st.button("Analisar Cenário Cruzado")

if botao_analisar:
    if dados_bolsa or dados_clima or dados_macro:
        with st.spinner('O Agente está cruzando as variáveis do mercado e salvando no Sheets...'):
            try:
                genai.configure(api_key=st.secrets["CHAVE_GEMINI"])
                modelo = genai.GenerativeModel('gemini-3.6-flash')
                
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
                
                resposta_ia = modelo.generate_content(prompt_sistema)
                texto_resposta = resposta_ia.text
                
                st.divider()
                st.subheader("Veredito Avançado do Agente:")
                st.write(texto_resposta)
                
                salvar_no_sheets(dados_bolsa, dados_clima, dados_macro, texto_resposta)
                
            except Exception as erro:
                st.error(f"Ocorreu um erro na comunicação com a IA: {erro}")
    else:
        st.warning("Por favor, preencha pelo menos um dos campos de mercado antes de solicitar a análise.")
