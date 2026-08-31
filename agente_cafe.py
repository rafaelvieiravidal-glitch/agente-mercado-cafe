# Importa o módulo 'datetime' para gerar datas e horas automatizadas
from datetime import datetime
# Importa a biblioteca do Streamlit para a interface web
import streamlit as st
# Importa a biblioteca do Google Gemini para a IA
import google.generativeai as genai
# Importa a biblioteca financeira do Yahoo
import yfinance as yf

# Define a função que busca as cotações financeiras em tempo real
def buscar_dados_mercado():
    # Inicia a tentativa de conexão com a API do Yahoo
    try:
        # Define o ticker do café na bolsa de Nova York
        cafe_ticker = yf.Ticker("KC=F")
        # Captura o preço do fechamento anterior do café
        cafe_fechamento_ontem = cafe_ticker.fast_info['previousClose']
        # Captura o preço em tempo real do café
        cafe_preco_atual = cafe_ticker.fast_info['lastPrice']
        
        # Verifica se há dados válidos de ontem para evitar divisão por zero
        if cafe_fechamento_ontem > 0:
            # Calcula a variação percentual do café
            var_cafe_pct = ((cafe_preco_atual - cafe_fechamento_ontem) / cafe_fechamento_ontem) * 100
        # Caso não haja dados válidos, zera a variação
        else:
            # Define variação como zero
            var_cafe_pct = 0.0
            
        # Define a palavra Alta se a variação for positiva
        if var_cafe_pct > 0:
            # Atribui a string correspondente
            direcao_cafe = "Alta"
        # Define a palavra Queda se a variação for negativa
        elif var_cafe_pct < 0:
            # Atribui a string correspondente
            direcao_cafe = "Queda"
        # Define Estabilidade se não houver variação
        else:
            # Atribui a string correspondente
            direcao_cafe = "Estabilidade"

        # Define o ticker do Dólar comercial contra o Real
        dolar_ticker = yf.Ticker("BRL=X")
        # Captura o preço de fechamento anterior do Dólar
        dolar_fechamento_ontem = dolar_ticker.fast_info['previousClose']
        # Captura a cotação em tempo real do Dólar
        dolar_preco_atual = dolar_ticker.fast_info['lastPrice']
        
        # Verifica se há dados válidos de ontem
        if dolar_fechamento_ontem > 0:
            # Calcula a variação percentual do dólar
            var_dolar_pct = ((dolar_preco_atual - dolar_fechamento_ontem) / dolar_fechamento_ontem) * 100
        # Tratamento de erro para base zerada
        else:
            # Define a variação como zero
            var_dolar_pct = 0.0
            
        # Avalia se a variação cambial é positiva
        if var_dolar_pct > 0:
            # Atribui a string de Alta
            direcao_dolar = "Alta"
        # Avalia se a variação cambial é negativa
        elif var_dolar_pct < 0:
            # Atribui a string de Queda
            direcao_dolar = "Queda"
        # Avalia se ficou no zero a zero
        else:
            # Atribui a string de Estabilidade
            direcao_dolar = "Estabilidade"
        
        # Monta o texto final da bolsa estruturado com quebra de linha
        texto_bolsa = (
            f"Fechamento Anterior (ICE NY): {cafe_fechamento_ontem:.2f} c/lb\n"
            f"Cotação Atual: {cafe_preco_atual:.2f} c/lb | Variação: {direcao_cafe} de {var_cafe_pct:.2f}%"
        )
        
        # Monta o texto final da macroeconomia com quebra de linha
        texto_macro = (
            f"Fechamento Anterior (Dólar): R$ {dolar_fechamento_ontem:.4f}\n"
            f"Cotação Atual: R$ {dolar_preco_atual:.4f} | Variação: {direcao_dolar} de {var_dolar_pct:.2f}%"
        )
        
        # Retorna os textos formatados
        return texto_bolsa, texto_macro
    
    # Captura falhas de rede na busca
    except Exception as e:
        # Retorna mensagens de erro padronizadas
        return "Erro ao buscar dados automáticos. Insira manualmente.", "Erro ao buscar dados automáticos. Insira manualmente."

# Define as configurações globais da página web
st.set_page_config(layout="wide")
# Escreve o título principal da aplicação na tela
st.title("Agente Analista de Sentimento: Café Arábica Global")
# Adiciona o subtítulo explicativo
st.write("Revise os dados importados. Corrija o texto se necessário antes de analisar.")

# Executa a função de busca
auto_bolsa, auto_macro = buscar_dados_mercado()

# Cria as três caixas de texto da interface
dados_bolsa = st.text_area("1. Bolsa de NY (ICE) e Mercado Futuro:", value=auto_bolsa, height=120)
dados_clima = st.text_area("2. Clima e Chuvas nas Regiões Produtoras:", height=120)
dados_macro = st.text_area("3. Câmbio (Dólar) e Macroeconomia:", value=auto_macro, height=120)

# Renderiza o botão principal de análise
botao_analisar = st.button("Analisar Cenário Cruzado")

# Verifica se o botão foi clicado
if botao_analisar:
    # Valida se há conteúdo nos campos
    if dados_bolsa or dados_clima or dados_macro:
        # Ativa o spinner de carregamento
        with st.spinner('O Agente está cruzando as variáveis do mercado...'):
            # Inicia o bloco de conexão com a IA
            try:
                # --- MUDANÇA CRÍTICA PARA NUVEM ---
                # A chave agora é puxada do cofre de segurança (Secrets) do Streamlit Cloud
                genai.configure(api_key=st.secrets["CHAVE_GEMINI"])
                
                # Define a versão do modelo de IA
                modelo = genai.GenerativeModel('gemini-3.6-flash')
                
                # Monta a instrução de sistema rigorosa
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
                
                # Gera o conteúdo
                resposta_ia = modelo.generate_content(prompt_sistema)
                
                # Exibe a resposta na tela
                st.divider()
                st.subheader("Veredito Avançado do Agente:")
                st.write(resposta_ia.text)
                
                # Formata o arquivo TXT de exportação
                data_atual_formatada = datetime.now().strftime("%d/%m/%Y %H:%M")
                conteudo_arquivo = f"Relatório de Mercado de Café Arábica\nGerado em: {data_atual_formatada}\n\n{resposta_ia.text}"
                nome_do_arquivo = f"Relatorio_Mercado_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                
                # Cria o botão de download
                st.download_button(
                    label="📥 Baixar Relatório (TXT)",
                    data=conteudo_arquivo,
                    file_name=nome_do_arquivo,
                    mime="text/plain"
                )
                
            # Tratamento de erro geral
            except Exception as erro:
                st.error(f"Ocorreu um erro na comunicação com a IA: {erro}")
    # Alerta se não houver dados
    else:
        st.warning("Por favor, preencha pelo menos um dos campos de mercado antes de solicitar a análise.")