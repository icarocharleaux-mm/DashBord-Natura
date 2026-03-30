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
    # CARREGAR DANOS (Base Automatizada)
    # ==========================================
    try:
        df_danos = pd.read_csv("base_pronta.csv", sep=";", encoding="latin-1")
    except Exception as e:
        df_danos = pd.DataFrame()
        st.error(f"Erro ao carregar a nova base de danos: {e}")

    if not df_danos.empty:
        df_danos.columns = [c.strip() for c in df_danos.columns]
        
        renomeacoes_danos = {
            'Motorista última viagem': 'Motorista', 
            'filial': 'Filial', 
            'categoria': 'Categoria',
            'qtd_reclamada': 'Quantidade',
            'id_rota': 'Rota'
        }
        
        for col in df_danos.columns:
            if col.strip().lower() == 'rota':
                renomeacoes_danos[col] = 'Rota'
                
        df_danos = df_danos.rename(columns=renomeacoes_danos)
        df_danos['Tipo_Ocorrencia'] = 'Dano'
        
        if 'Quantidade' in df_danos.columns:
            df_danos['Quantidade'] = pd.to_numeric(df_danos['Quantidade'], errors='coerce').fillna(0)
        if 'Rota' not in df_danos.columns:
            df_danos['Rota'] = 'N/A'

        coluna_mes_danos = None
        for col in df_danos.columns:
            if col.strip().lower() in ['data_ref', 'data', 'mes', 'mês', 'periodo']:
                coluna_mes_danos = col
                break
                
        if coluna_mes_danos:
            df_danos['Mes_Limpo'] = df_danos[coluna_mes_danos].astype(str).str.strip().str.lower().str[:3]
            df_danos['Periodo'] = df_danos['Mes_Limpo'].map(mapa_meses_str)
            mask_na = df_danos['Periodo'].isna()
            if mask_na.any():
                datas_reais = pd.to_datetime(df_danos.loc[mask_na, coluna_mes_danos], errors='coerce', dayfirst=True)
                df_danos.loc[mask_na, 'Periodo'] = datas_reais.dt.month.map(mapa_meses_num)
            df_danos['Periodo'] = df_danos['Periodo'].fillna('N/A')
        else:
            df_danos['Periodo'] = 'N/A'

    # ==========================================
    # CARREGAR FALTAS (A NOVA BASE AUTOMATIZADA)
    # ==========================================
    try:
        # Agora o painel lê o arquivo limpo gerado pelo seu robô!
        df_faltas = pd.read_csv("base_falta_pronta.csv", sep=";", encoding="latin-1")
    except Exception as e:
        df_faltas = pd.DataFrame()
        st.error(f"Erro ao carregar a nova base de faltas: {e}")

    if not df_faltas.empty:
        df_faltas.columns = [c.strip() for c in df_faltas.columns]
        
        # Ensinando ao Python os nomes corretos da nova planilha de faltas
        renomeacoes_faltas = {
            'Motorista última viagem': 'Motorista', # O resultado do PROCV
            'filial': 'Filial',
            'categoria': 'Categoria',
            'cantidad_itens': 'Quantidade',
            'mes': 'Mes'
        }
        
        for col in df_faltas.columns:
            if col.strip().lower() == 'rota':
                renomeacoes_faltas[col] = 'Rota'
                
        df_faltas = df_faltas.rename(columns=renomeacoes_faltas)
        df_faltas['Tipo_Ocorrencia'] = 'Falta'
        
        if 'Quantidade' in df_faltas.columns:
            df_faltas['Quantidade'] = pd.to_numeric(df_faltas['Quantidade'], errors='coerce').fillna(0)
        if 'Rota' not in df_faltas.columns:
            df_faltas['Rota'] = 'N/A'

        if 'Mes' in df_faltas.columns:
            df_faltas['Mes_Num'] = pd.to_numeric(df_faltas['Mes'], errors='coerce')
            df_faltas['Periodo'] = df_faltas['Mes_Num'].map(mapa_meses_num).fillna('N/A')
        else:
            df_faltas['Periodo'] = 'N/A'

    # ==========================================
    # CARREGAR MAPA DE ROTAS E COORDENADAS
    # ==========================================
    try:
        df_mapa_rotas = pd.read_csv("Rotas e bairros.csv", sep=";", encoding="latin-1", skiprows=7)
        df_mapa_rotas.columns = [c.strip() for c in df_mapa_rotas.columns]
        df_mapa_rotas['Rota'] = df_mapa_rotas['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        def resumir_bairros(bairros):
            b_unicos = bairros.str.strip().dropna().unique()
            if len(b_unicos) <= 3:
                return ", ".join(b_unicos)
            else:
                return ", ".join(b_unicos[:3]) + f" (+{len(b_unicos)-3} bairros)"
        df_mapa_agg = df_mapa_rotas.groupby('Rota').agg({
            'Setor': lambda x: x.mode()[0] if not x.empty else "N/A",
            'Bairro': resumir_bairros
        }).reset_index()
    except Exception as e:
        df_mapa_agg = pd.DataFrame(columns=['Rota', 'Setor', 'Bairro'])

    try:
        try:
            df_coord = pd.read_csv("base_coordenadas.csv", sep=",", encoding="utf-8", skiprows=7)
        except:
            df_coord = pd.read_csv("base_coordenadas.csv", sep=";", encoding="latin-1", skiprows=7)
            
        df_coord.columns = [str(c).strip().upper() for c in df_coord.columns]
        
        if 'LATITUDE' in df_coord.columns and 'LONGITUDE' in df_coord.columns and 'ROTA' in df_coord.columns:
            df_coord['ROTA'] = df_coord['ROTA'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            df_coord['LATITUDE'] = df_coord['LATITUDE'].astype(str).str.replace(',', '.').astype(float)
            df_coord['LONGITUDE'] = df_coord['LONGITUDE'].astype(str).str.replace(',', '.').astype(float)
            
            df_coord_agg = df_coord.dropna(subset=['LATITUDE', 'LONGITUDE']).groupby('ROTA').agg({
                'LATITUDE': 'mean', 
                'LONGITUDE': 'mean'
            }).reset_index()
        else:
            df_coord_agg = pd.DataFrame(columns=['ROTA', 'LATITUDE', 'LONGITUDE'])
    except Exception as e:
        df_coord_agg = pd.DataFrame(columns=['ROTA', 'LATITUDE', 'LONGITUDE'])

    # ==========================================
    # CARREGAR TRATATIVAS
    # ==========================================
    try:
        try:
            df_trat1 = pd.read_csv("Tratativas.csv", sep=";", encoding="utf-8")
        except UnicodeDecodeError:
            df_trat1 = pd.read_csv("Tratativas.csv", sep=";", encoding="latin-1")
        df_trat1.columns = [str(c).strip().upper() for c in df_trat1.columns]
        if 'MOTORISTA' in df_trat1.columns:
            df_trat1 = df_trat1.dropna(subset=['MOTORISTA'])
            df_trat1 = df_trat1[~df_trat1['MOTORISTA'].astype(str).str.strip().str.upper().isin(['NAN', '', ' '])]
        else:
            df_trat1 = pd.DataFrame()
    except Exception:
        df_trat1 = pd.DataFrame() 

    try:
        try:
            df_trat2 = pd.read_csv("tratativas2.csv", sep=";", encoding="utf-8")
        except UnicodeDecodeError:
            df_trat2 = pd.read_csv("tratativas2.csv", sep=";", encoding="latin-1")
        df_trat2.columns = [str(c).strip().upper() for c in df_trat2.columns]
        if 'MOTORISTA' in df_trat2.columns:
            df_trat2 = df_trat2.dropna(subset=['MOTORISTA'])
            df_trat2 = df_trat2[~df_trat2['MOTORISTA'].astype(str).str.strip().str.upper().isin(['NAN', '', ' '])]
        else:
            df_trat2 = pd.DataFrame()
    except Exception:
        df_trat2 = pd.DataFrame() 

    # ==========================================
    # CRIAR A BASE UNIFICADA
    # ==========================================

    colunas_comuns = ['Motorista', 'Filial', 'Categoria', 'Rota', 'Tipo_Ocorrencia', 'Quantidade', 'Periodo']
    for col in colunas_comuns:
        if col not in df_danos.columns: df_danos[col] = 'N/A'
        if col not in df_faltas.columns: df_faltas[col] = 'N/A'

    # Preenchendo os motoristas e filiais não encontrados com texto, para NÃO perder as linhas nos gráficos!
    df_danos['Motorista'] = df_danos['Motorista'].fillna('Não Identificado')
    df_faltas['Motorista'] = df_faltas['Motorista'].fillna('Não Identificado')
    
    df_danos['Filial'] = df_danos['Filial'].fillna('Não Identificada')
    df_faltas['Filial'] = df_faltas['Filial'].fillna('Não Identificada')

    # Juntando as duas bases de forma segura
    df_unificado = pd.concat([df_danos[colunas_comuns], df_faltas[colunas_comuns]], ignore_index=True)
    
    # Tratando as rotas vazias
    df_unificado['Rota'] = df_unificado['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().fillna('N/A')

    return df_danos, df_faltas, df_unificado, df_mapa_agg, df_coord_agg, df_trat1, df_trat2