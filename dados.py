import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    mapa_meses_num = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }

    # ==========================================
    # 🛡️ MOTOR DE EXTRAÇÃO DE DATA DA COLUNA A
    # ==========================================
    def extrair_periodo(valor):
        if pd.isna(valor): return 'Não Identificado'
        val_str = str(valor).strip().lower()
        
        # 1. Tenta identificar nomes diretos ou números isolados
        mapa_texto = {
            '1': 'Jan', '01': 'Jan', 'jan': 'Jan', 'janeiro': 'Jan',
            '2': 'Fev', '02': 'Fev', 'fev': 'Fev', 'fevereiro': 'Fev',
            '3': 'Mar', '03': 'Mar', 'mar': 'Mar', 'março': 'Mar', 'marco': 'Mar',
            '4': 'Abr', '04': 'Abr', 'abr': 'Abr', 'abril': 'Abr',
            '5': 'Mai', '05': 'Mai', 'mai': 'Mai', 'maio': 'Mai',
            '6': 'Jun', '06': 'Jun', 'jun': 'Jun', 'junho': 'Jun',
            '7': 'Jul', '07': 'Jul', 'jul': 'Jul', 'julho': 'Jul',
            '8': 'Ago', '08': 'Ago', 'ago': 'Ago', 'agosto': 'Ago',
            '9': 'Set', '09': 'Set', 'set': 'Set', 'setembro': 'Set',
            '10': 'Out', 'out': 'Out', 'outubro': 'Out',
            '11': 'Nov', 'nov': 'Nov', 'novembro': 'Nov',
            '12': 'Dez', 'dez': 'Dez', 'dezembro': 'Dez'
        }
        if val_str in mapa_texto:
            return mapa_texto[val_str]
            
        # 2. Tenta identificar data de série do Excel (ex: 45046 -> 01/05/2023)
        if str(valor).isdigit() and len(str(valor)) >= 4:
            try:
                dt = pd.to_datetime('1899-12-30') + pd.to_timedelta(int(valor), unit='D')
                return mapa_meses_num.get(dt.month, 'Não Identificado')
            except:
                pass

        # 3. Tenta parsear como data tradicional (dd/mm/yyyy, yyyy-mm etc)
        try:
            dt = pd.to_datetime(valor, dayfirst=True)
            return mapa_meses_num.get(dt.month, 'Não Identificado')
        except:
            return 'Não Identificado'

    # ==========================================
    # 1. CARREGAR DANOS (base_pronta.csv)
    # ==========================================
    try:
        df_danos = pd.read_csv("base_pronta.csv", sep=";", encoding="latin-1")
        df_danos.columns = [str(c).strip() for c in df_danos.columns]
        
        # Puxa o mês obrigatoriamente da primeira coluna (índice 0)
        df_danos['Periodo'] = df_danos.iloc[:, 0].apply(extrair_periodo)
        
        df_danos = df_danos.rename(columns={
            'motorista': 'Motorista', 'filial': 'Filial', 'id_rota': 'Rota', 
            'qtd_reclamada': 'Quantidade', 'cliente': 'Cliente', 
            'pedido': 'Pedido', 'empresa': 'Empresa'
        })
        
        df_danos['Tipo_Ocorrencia'] = 'Dano'
        df_danos['Canal'] = 'N/A'
    except Exception:
        df_danos = pd.DataFrame()

    # ==========================================
    # 2. CARREGAR FALTAS (base_falta_pronta.csv)
    # ==========================================
    try:
        df_faltas = pd.read_csv("base_falta_pronta.csv", sep=";", encoding="latin-1")
        df_faltas.columns = [str(c).strip() for c in df_faltas.columns]

        # Puxa o mês obrigatoriamente da primeira coluna (índice 0)
        df_faltas['Periodo'] = df_faltas.iloc[:, 0].apply(extrair_periodo)

        df_faltas = df_faltas.rename(columns={
            'Motorista ultima viagem': 'Motorista', 'name1': 'Cliente',                     
            'filial': 'Filial', 'rota': 'Rota', 'cantidad_itens': 'Quantidade', 
            'nm_pedido': 'Pedido', 'marca_canal': 'Canal'
        })

        df_faltas['Tipo_Ocorrencia'] = 'Falta'
        df_faltas['Empresa'] = 'NATURA'
    except Exception:
        df_faltas = pd.DataFrame()

    # ==========================================
    # 3. UNIFICAR E BLINDAR
    # ==========================================
    colunas_comuns = ['Cliente', 'Pedido', 'Motorista', 'Filial', 'Rota', 'Tipo_Ocorrencia', 'Quantidade', 'Periodo', 'Empresa', 'Canal']
    
    for df in [df_danos, df_faltas]:
        if not df.empty:
            for col in colunas_comuns:
                if col not in df.columns: df[col] = 'Não Identificado'
                df[col] = df[col].fillna('Não Identificado')

    if not df_danos.empty or not df_faltas.empty:
        df_unificado = pd.concat([df_danos[colunas_comuns], df_faltas[colunas_comuns]], ignore_index=True)
        df_unificado['Rota'] = df_unificado['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    else:
        df_unificado = pd.DataFrame(columns=colunas_comuns)

    # CARREGAMENTO DE MAPAS (Mantido igual)
    try:
        df_coord_agg = pd.read_csv("base_coordenadas.csv", sep=";", encoding="latin-1", skiprows=7, decimal=",").rename(columns={'ROTA': 'Rota'}).groupby('Rota').agg({'LATITUDE': 'mean', 'LONGITUDE': 'mean'}).reset_index()
        df_mapa_agg = pd.read_csv("rotas e bairros.csv", sep=";", encoding="latin-1", skiprows=7).groupby('Rota').agg({'Setor': 'first', 'Bairro': lambda x: ', '.join(x.dropna().unique()[:3])}).reset_index()
    except Exception:
        df_coord_agg, df_mapa_agg = pd.DataFrame(), pd.DataFrame()

    # CARREGAMENTO DE TRATATIVAS (Mantido igual)
    try:
        df_trat1 = pd.read_csv("Tratativas.csv", sep=";", encoding="latin-1").dropna(subset=['MOTORISTA'])
        df_trat2 = pd.read_csv("tratativas2.csv", sep=";", encoding="latin-1").dropna(subset=['MOTORISTA'])
    except Exception:
        df_trat1, df_trat2 = pd.DataFrame(), pd.DataFrame()

    return df_danos, df_faltas, df_unificado, df_mapa_agg, df_coord_agg, df_trat1, df_trat2