import streamlit as st
import pandas as pd

# 2. Carregamento e Preparação dos Dados
@st.cache_data
def load_data():
    mapa_meses_num = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }
    mapa_meses_str = {
        'jan': 'Jan', 'fev': 'Fev', 'mar': 'Mar', 'abr': 'Abr', 'mai': 'Mai', 'jun': 'Jun',
        'jul': 'Jul', 'ago': 'Ago', 'set': 'Set', 'out': 'Out', 'nov': 'Nov', 'dez': 'Dez'
    }

    # ==========================================
    # 1. CARREGAR DANOS
    # ==========================================
    try:
        df_danos = pd.read_csv("base_pronta.csv", sep=";", encoding="latin-1")
        df_danos.columns = [str(c).strip() for c in df_danos.columns]
        
        df_danos = df_danos.rename(columns={
            'Motorista última viagem': 'Motorista', 
            'filial': 'Filial', 
            'id_rota': 'Rota', 
            'qtd_reclamada': 'Quantidade', 
            'data_ref': 'Periodo', 
            'categoria': 'Categoria', 
            'cliente': 'Cliente',
            'pedido': 'Pedido'  # ✨ Padronizando o Pedido
        })
        df_danos['Tipo_Ocorrencia'] = 'Dano'
        df_danos['Periodo'] = pd.to_datetime(df_danos['Periodo'], errors='coerce').dt.month.map(mapa_meses_num)
    except Exception as e:
        df_danos = pd.DataFrame()

    # ==========================================
    # 2. CARREGAR FALTAS
    # ==========================================
    try:
        df_faltas = pd.read_csv("base_falta_pronta.csv", sep=";", encoding="latin-1")
        df_faltas.columns = [str(c).strip() for c in df_faltas.columns]

        df_faltas = df_faltas.rename(columns={
            'Motorista última viagem': 'Motorista', 
            'filial': 'Filial', 
            'rota': 'Rota', 
            'cantidad_itens': 'Quantidade', 
            'mes': 'Periodo', 
            'categoria': 'Categoria',
            'nm_pedido': 'Pedido' # ✨ Padronizando o Pedido
        })
        df_faltas['Tipo_Ocorrencia'] = 'Falta'
        df_faltas['Periodo'] = df_faltas['Periodo'].astype(str).str.lower().map(mapa_meses_str)
    except Exception as e:
        df_faltas = pd.DataFrame()

    # ==========================================
    # 3. CARREGAR MAPAS E COORDENADAS
    # ==========================================
    try:
        df_coord = pd.read_csv("base_coordenadas.csv", sep=";", encoding="latin-1", skiprows=7)
        df_mapa = pd.read_csv("rotas e bairros.csv", sep=";", encoding="latin-1", skiprows=7)
        
        df_mapa_agg = df_mapa.groupby('Rota').agg({'Setor': 'first', 'Bairro': lambda x: ', '.join(x.dropna().unique()[:3])}).reset_index()
        df_coord_agg = df_coord.groupby('Rota').agg({'LATITUDE': 'mean', 'LONGITUDE': 'mean'}).reset_index()
    except Exception:
        df_mapa_agg, df_coord_agg = pd.DataFrame(), pd.DataFrame()

    # ==========================================
    # 4. CARREGAR TRATATIVAS
    # ==========================================
    try:
        df_trat1 = pd.read_csv("Tratativas.csv", sep=";", encoding="latin-1")
        df_trat1 = df_trat1.dropna(subset=['MOTORISTA'])
        df_trat1 = df_trat1[~df_trat1['MOTORISTA'].astype(str).str.strip().str.upper().isin(['NAN', '', ' '])]
    except Exception:
        df_trat1 = pd.DataFrame()

    try:
        df_trat2 = pd.read_csv("tratativas2.csv", sep=";", encoding="latin-1")
        df_trat2 = df_trat2.dropna(subset=['MOTORISTA'])
        df_trat2 = df_trat2[~df_trat2['MOTORISTA'].astype(str).str.strip().str.upper().isin(['NAN', '', ' '])]
    except Exception:
        df_trat2 = pd.DataFrame() 

    # ==========================================
    # 5. UNIFICAR BASES
    # ==========================================
    colunas_comuns = ['Cliente', 'Pedido', 'Motorista', 'Filial', 'Categoria', 'Rota', 'Tipo_Ocorrencia', 'Quantidade', 'Periodo']
    
    for col in colunas_comuns:
        if col not in df_danos.columns: df_danos[col] = 'Não Identificado'
        if col not in df_faltas.columns: df_faltas[col] = 'Não Identificado'

    df_danos['Motorista'] = df_danos['Motorista'].fillna('Não Identificado')
    df_faltas['Motorista'] = df_faltas['Motorista'].fillna('Não Identificado')
    df_danos['Filial'] = df_danos['Filial'].fillna('Não Identificada')
    df_faltas['Filial'] = df_faltas['Filial'].fillna('Não Identificada')

    df_unificado = pd.concat([df_danos[colunas_comuns], df_faltas[colunas_comuns]], ignore_index=True)
    df_unificado['Rota'] = df_unificado['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().fillna('N/A')

    return df_danos, df_faltas, df_unificado, df_mapa_agg, df_coord_agg, df_trat1, df_trat2
