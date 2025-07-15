import streamlit as st
import pandas as pd


transacoes = pd.read_csv("transacoes.csv", sep=';')

tab1, tab2, tab3 = st.tabs(["Compras", "Extrato", 'Visão Geral'])
tab1.write("Adicionar compras")
tab2.write("Extrato")
tab2.write("Visão Geral")

# You can also use "with" notation:
with tab1:

    tipo_options = ['Receita', 'Despesa']
    tipo_input = st.selectbox('Tipo', tipo_options)

    if tipo_input == 'Despesa':
        area_options = ['Refeição', 'Lanche', 'Café', 'Supermercado', 'Utilidades', 'Lazer', 'Transporte']
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
        transacoes.to_csv('transacoes.csv', sep=';')


with tab2:
    st.dataframe(transacoes)

with tab3:
    receita = transacoes[transacoes['tipo_input']=='Receita']['valor_input'].sum()
    receita_str = f"# Receita {receita}"
    st.markdown(receita_str)

    despesa = transacoes[transacoes['tipo_input']=='Despesa']['valor_input'].sum()
    despesa_str = f"# Despesa {despesa}"
    st.markdown(despesa_str)

    lucro_divida_str = f"# Lucro/Divida {receita - despesa}"
    st.markdown(lucro_divida_str)
