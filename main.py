import streamlit as st
import pandas as pd
from datetime import datetime


mes_options = [i for i in range(1,13)]

mes = st.selectbox("Mês", options=mes_options, index=datetime.today().month)

try:
    transacoes = pd.read_csv(f"transacoes{mes}{datetime.today().year}.csv", sep=';', index_col=None)
except:
    transacoes = pd.DataFrame(columns=['area_input','local_input','valor_input','tipo_input','moeda_input','dia_input','hora_input'])



tab1, tab2, tab3 = st.tabs(["Compras", "Extrato", 'Visão Geral'])
tab1.write("Adicionar compras")
tab2.write("Extrato")
tab2.write("Visão Geral")

# You can also use "with" notation:
with tab1:

    tipo_options = ['Despesa', 'Receita']
    tipo_input = st.selectbox('Tipo', tipo_options)

    if tipo_input == 'Despesa':
        area_options = ['Refeição', 'Bar', 'Lanche', 'Café', 'Vestuário', 'Supermercado', 'Utensílios', 'Lazer', 'Transporte', 'Lavanderia']
    elif tipo_input == 'Receita':
        area_options = ['Salário', 'Outro']

    area_input = st.selectbox("Área", area_options)

    local_input = st.text_input("Local/empresa")

    valor_input = st.number_input('Valor')

    moeda_options = ['R$', 'U$']
    moeda_input = st.selectbox('Moeda', moeda_options)

    dia_input = st.date_input("Dia da compra:")

    hora_input = st.time_input("Hora da compra")

    if st.button("Adicionar transação"):
        new_row_df = pd.DataFrame(
            [{
                'area_input': area_input,
                'local_input': local_input,
                'valor_input': valor_input,
                'tipo_input': tipo_input,
                'moeda_input': moeda_input,
                'dia_input': dia_input,
                'hora_input': hora_input,
            }])

        transacoes = pd.concat([transacoes, new_row_df], ignore_index=True)
        st.write("Transação adicionada com sucesso!")
        transacoes.to_csv(f'transacoes{mes}{datetime.today().year}.csv', sep=';', index=False)


with tab2:

    if "transacoes" not in st.session_state:
        st.session_state.df = transacoes

        event = st.dataframe(
            st.session_state.df,
            key="data",
            on_select="rerun",
            selection_mode=["multi-row"],
        )

        #event.selection
        #print(event.selection["rows"])

        if st.button("Apagar transações marcadas"):
            transacoes.drop(event.selection["rows"], inplace=True)
            transacoes.to_csv(f'transacoes{mes}{datetime.today().year}.csv', sep=';', index=False)
            st.session_state.df = transacoes


with tab3:
    receita = transacoes[transacoes['tipo_input']=='Receita']['valor_input'].sum()
    receita_str = f"## Receita {round(receita, 2)}"
    st.markdown(receita_str)

    despesa = transacoes[transacoes['tipo_input']=='Despesa']['valor_input'].sum()
    despesa_str = f"## Despesa {round(despesa,2)}"
    st.markdown(despesa_str)

    lucro_divida_str = f"## Lucro/Divida {round(receita - despesa,2)}"
    st.markdown(lucro_divida_str)

    group_despesa = transacoes[transacoes['tipo_input']=='Despesa'].groupby(by=['area_input'])['valor_input'].sum()
    st.bar_chart(group_despesa)

    group_despesa_local = transacoes[transacoes['tipo_input']=='Despesa'].groupby(by=['local_input'])['valor_input'].sum()
    st.bar_chart(group_despesa_local)

    group_receita = transacoes[transacoes['tipo_input']=='Receita'].groupby(by=['area_input'])['valor_input'].sum()
    st.bar_chart(group_receita)

    group_receita_local = transacoes[transacoes['tipo_input']=='Receita'].groupby(by=['local_input'])['valor_input'].sum()
    st.bar_chart(group_receita_local)
