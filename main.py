import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import altair as alt
from google.oauth2 import service_account
from google.cloud import firestore
import json

st.set_page_config(page_title="ifinance", page_icon='logo.png')

st.logo("logo.png", size="large")
if not st.user.is_logged_in:

    st.title('Autentique-se para acessar.')


    if st.button("Entrar com Google", icon=":material/g_mobiledata:"):
        st.login("google")


else:

    # Initialize the default app

    st.markdown('# Finanças')

    st.header(f'Bem-vindo {st.user.given_name}')
    st.image(st.user.picture)

    # st.json(st.user)

    #firestore_client = firestore.Client.from_service_account_json('firestore-key.json')
    key_dict = st.secrets["gcp"]
    creds = service_account.Credentials.from_service_account_info(key_dict)

    firestore_client = firestore.Client(credentials=creds, project=key_dict["project_id"])

    print(firestore_client.project)

    with st.expander("Injetar dados de relatório"):

        uploaded = st.file_uploader("Anexe um arquivo CSV.")

        tabela_options = ['Transações']
        tabela = st.selectbox("Selecione a tabela que deseja adicionar", options=tabela_options)

        if st.button("Adicionar ao baco de dados:"):
            st.write("Adicionando dados...")
            if uploaded.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded, sep=',', index_col=None)
            else:
                df = pd.read_excel(uploaded, index_col=None)

            records = df.to_dict(orient='records')

            if tabela == 'Transações':
                collection_ref = firestore_client.collection('transacoes')

            for record in records:
                print(f"Adicionando record {record}.")
                collection_ref.add(record)


            st.write(f"{tabela} adicionadas com sucesso.")



    transacoes_ref = firestore_client.collection('transacoes')

    tab_auxiliares_ref = firestore_client.collection('tabelas_auxiliares')

    forma_pgto_ref = firestore_client.collection('forma_pagto')

    def iterate_dates_by_month(start_date, end_date):
        """
        Iterates through dates from a start date to an end date, month by month.

        Args:
            start_date (datetime.date): The initial date.
            end_date (datetime.date): The final date.

        Yields:
            datetime.date: The first day of each month within the range.
        """
        parcela=1
        current_date = start_date
        while current_date <= end_date:
            yield parcela, current_date
            parcela += 1
            current_date += relativedelta(months=1)

    def delete_documents_from_id_list(list, ref):

        docs = (ref.where('id', 'in', list).stream())
        for doc in docs:
            document = ref.document(doc.id)
            document.delete()

        return True

    def get_forma_pgto_list_usuario(user, ref):
        docs = ref.stream()

        data = []
        for doc in docs:
            doc_dict = doc.to_dict()
            if doc_dict['user']==st.user.email:
                data.append(doc_dict['forma_pagto'])

        return data

    def get_transactions_dataframe_from_month(mes, ref):
        docs = ref.stream()

        data = []
        for doc in docs:
            doc_dict = doc.to_dict()
            print(f"{doc_dict['user']} == {st.user.email} || {doc_dict['mes']} ({type(doc_dict['mes'])}) == {mes}({type(mes)}) --> {doc_dict['mes'] == mes and doc_dict['user']==st.user.email}")
            if doc_dict['mes'] == mes and doc_dict['user']==st.user.email:
                data.append(doc_dict)

        return pd.DataFrame(data)

    def get_document_values_as_list(doc_id, ref):
        doc_ref = ref.document(doc_id)
        doc = doc_ref.get()
        return list(doc.to_dict().values())

    mes_options = [i for i in range(1,13)]

    mes = st.selectbox("Selecione o mês da fatura", options=mes_options, index=datetime.today().month-1)

    transacoes = get_transactions_dataframe_from_month(mes, transacoes_ref)

    # try:
    #     transacoes = pd.read_csv(f"transacoes{mes}{datetime.today().year}.csv", sep=';', index_col=None)
    # except:
    #     transacoes = pd.DataFrame(columns=['area_input','local_input','valor_input','tipo_input','moeda_input','dia_input','hora_input'])

    tab1, tab2, tab3, tab4 = st.tabs(["Compras", "Extrato", 'Visão Geral', 'Tabelas Auxiliares'])
    tab1.write("Adicionar compras")
    tab2.write("Extrato")
    tab3.write("Visão Geral - Dashboard")
    tab4.write("Tabelas auxiliares")

    # You can also use "with" notation:
    with tab1:

        tipo_options = ['Despesa', 'Receita']
        tipo_input = st.selectbox('Tipo', tipo_options)

        if tipo_input == 'Despesa':
            #area_options = ['Refeição', 'Bar', 'Lanche', 'Café', 'Vestuário', 'Supermercado', 'Utensílios', 'Lazer', 'Transporte', 'Lavanderia']

            area_options = get_document_values_as_list('area_options_despesa', tab_auxiliares_ref)

        elif tipo_input == 'Receita':
            # area_options = ['Salário', 'Outro']
            area_options = get_document_values_as_list('area_options_receita', tab_auxiliares_ref)

        fixa_check = st.checkbox("Fixa")

        parcela_check = st.checkbox("Parcela")

        if parcela_check:
            n_parcelas = st.number_input("Número de parcelas a partir do mês da fatura selecionado", 0, 1000)

            col1, col2 = st.columns(2)
            month_ini = col1.number_input('Mês da efetuação da compra', value=datetime.today().month)
            year_fim = col2.number_input('Mês da do início da compra', value=datetime.today().year)
            valor_total = st.number_input("Valor total")

        area_input = st.selectbox("Área", area_options)

        local_input = st.text_input("Estabelecimento/Local/empresa")

        descricao_input = st.text_input("Descrição")

        if parcela_check:
            valor_input = st.number_input('Valor', value= valor_total/n_parcelas if valor_total and n_parcelas else 0)
        else:
            valor_input = st.number_input('Valor')


        forma_pgto_options = get_forma_pgto_list_usuario(st.user.email, forma_pgto_ref)
        forma_pgto_input = st.selectbox('Cartão', forma_pgto_options)

        moeda_options = ['R$', 'U$']
        moeda_input = st.selectbox('Moeda', moeda_options)

        dia_input = st.date_input("Dia da compra:")

        hora_input = st.time_input("Hora da compra")

        if st.button("Adicionar transação"):

            if fixa_check:
                # TODO tabela de gastos e receitas fixas
                pass
            elif parcela_check:

                data_ini = dia_input.replace(month=month_ini, year=year_fim)
                data_fim = data_ini + relativedelta(months=n_parcelas)
                for parcela, data_pgto in iterate_dates_by_month(data_ini, data_fim):
                    print(f"DIA INPUT: {dia_input}")
                    nova_transacao = {
                        'area_input': area_input,
                        'local_input': local_input,
                        'descricao_input': descricao_input,
                        'valor_input': valor_input,
                        'tipo_input': tipo_input,
                        'moeda_input': moeda_input,
                        'mes': int(data_pgto.month),
                        'forma_pgto_input': forma_pgto_input,
                        'dia_input': str(data_pgto),
                        'hora_input': str(hora_input),
                        'valor_total': valor_total,
                        'parcelas': n_parcelas,
                        'parcela_atual': parcela,
                        'fim_do_pagamento': str(data_fim),
                        'user': st.user.email
                    }

                    doc_ref = transacoes_ref.document()

                    nova_transacao['id'] = doc_ref.id
                    doc_ref.set(nova_transacao)

                transacoes = get_transactions_dataframe_from_month(mes, transacoes_ref)
                st.write("Transações parceladas adicionada com sucesso!")

            else:
                print(f"DIA INPUT: {dia_input}")
                nova_transacao = {
                    'area_input': area_input,
                    'local_input': local_input,
                    'descricao_input': descricao_input,
                    'valor_input': valor_input,
                    'tipo_input': tipo_input,
                    'moeda_input': moeda_input,
                    'mes': int(mes),
                    'forma_pgto_input': forma_pgto_input,
                    'dia_input': str(dia_input),
                    'hora_input': str(hora_input),
                    'user': st.user.email
                }

                doc_ref = transacoes_ref.document()

                nova_transacao['id'] = doc_ref.id
                doc_ref.set(nova_transacao)

                # new_row_df = pd.DataFrame(
                #     [{
                #         'area_input': area_input,
                #         'local_input': local_input,
                #         'valor_input': valor_input,
                #         'tipo_input': tipo_input,
                #         'moeda_input': moeda_input,
                #         'dia_input': dia_input,
                #         'hora_input': hora_input,
                #     }])

                # transacoes = pd.concat([transacoes, new_row_df], ignore_index=True)
                # transacoes.to_csv(f'transacoes{mes}{datetime.today().year}.csv', sep=';', index=False)

                transacoes = get_transactions_dataframe_from_month(mes, transacoes_ref)

                st.write("Transação adicionada com sucesso!")

    with tab2:

        if "transacoes" not in st.session_state:
            st.session_state.df = transacoes.rename(columns={
                'cartao': 'Cartão',
                'user': 'Usuário',
                'dia_input': 'Data',
                'id': 'ID',
                'area_input': 'Área',
                'local_input': 'Estabelecimento',
                'mes': 'Mês',
                'valor_input': 'Valor',
                'tipo_input': 'Tipo',
                'moeda_input': 'Moeda',
                'descricao_input': 'Descrição',
                'hora_input': 'Hora'
            })

            event = st.dataframe(
                st.session_state.df,
                key="data",
                on_select="rerun",
                selection_mode=["multi-row"],
            )

            #event.selection
            #print(event.selection["rows"])


            st.download_button(
               label="Download",
               data=transacoes.to_csv(index=False, sep=';').encode("utf-8"),
               file_name = f"transacoes{mes}{datetime.today().year}.csv",
               mime="text/csv",
               key='download-csv'
            )

            if st.button("Apagar transações marcadas"):
                # print(event.selection["rows"])
                list = transacoes.iloc[event.selection["rows"]]['id'].tolist()
                print(transacoes.iloc[event.selection["rows"]]['id'].tolist())
                if delete_documents_from_id_list(list, transacoes_ref):
                    transacoes = get_transactions_dataframe_from_month(mes, transacoes_ref)
                    st.session_state.df = transacoes
                    st.write('Transações apagadas com sucesso!')
                # transacoes.drop(event.selection["rows"], inplace=True)
                # transacoes.to_csv(f'transacoes{mes}{datetime.today().year}.csv', sep=';', index=False)
                # st.session_state.df = transacoes


    with tab3:
        col1, col2, col3 = st.columns(3)


        try:
            receita = transacoes[transacoes['tipo_input']=='Receita']['valor_input'].sum()
            # receita_str = f"## Receita {round(receita, 2)}"
            #st.markdown(receita_str)
            col1.metric("Receita", "R${:,.2f}".format(receita), border=True)

        except:
            st.markdown("### *Não há receitas a serem calculadas.*")


        try:
            despesa = transacoes[transacoes['tipo_input']=='Despesa']['valor_input'].sum()
            # despesa_str = f"## Despesa {round(despesa,2)}"
            col2.metric("Despesa", "R${:,.2f}".format(despesa), border=True)
        except:
            st.markdown("### *Não há despesas a serem calculadas.*")

        try:
            # lucro_divida_str = f"## Lucro/Divida {round(receita - despesa,2)}"
            # st.markdown(lucro_divida_str)
            col3.metric("Saldo", "R${:,.2f}".format(receita-despesa), delta=round(receita-despesa,2), border=True)
        except:
            st.markdown("### *Não há saldo a ser calculadas.*")

        try:
            group_despesa = transacoes[transacoes['tipo_input']=='Despesa'].groupby(by=['area_input'])['valor_input'].sum()
            st.markdown("###### Gastos por tipo de transação")
            st.bar_chart(group_despesa, x_label="Gastos", y_label="Tipo de transação")
        except:
            pass

        try:
            group_despesa_local = transacoes[transacoes['tipo_input']=='Despesa'].groupby(by=['local_input'])['valor_input'].sum()
            st.markdown("###### Gastos por estabelecimento ou localidade")
            st.bar_chart(group_despesa_local, x_label="Gastos", y_label="Estabelecimento de transação")
        except:
            pass

        try:
            group_receita = transacoes[transacoes['tipo_input']=='Receita'].groupby(by=['area_input'])['valor_input'].sum()
            st.markdown("###### Recebimentos por área")
            st.bar_chart(group_receita, x_label="Área", y_label="Valor recebido")
        except:
            pass

        try:
            group_receita_local = transacoes[transacoes['tipo_input']=='Receita'].groupby(by=['local_input'])['valor_input'].sum()
            st.markdown("###### Receita por estabelecimento ou localidade")
            st.bar_chart(group_receita_local, x_label="Estabelecimentos/localidades", y_label="Gastos")
        except:
            pass

        try:
            daily_sum_despesa = transacoes[transacoes['tipo_input']=='Despesa'].groupby(pd.to_datetime(transacoes['dia_input']).dt.date)['valor_input'].sum()
            st.markdown("###### Gastos por dia do mês")
            st.line_chart(daily_sum_despesa, x_label="Dias do mês da fatura", y_label="Gastos")
        except:
            pass

        try:
            daily_sum_receita = transacoes[transacoes['tipo_input']=='Receita'].groupby(pd.to_datetime(transacoes['dia_input']).dt.date)['valor_input'].sum()
            st.markdown("###### Recebimentos por dia do mês")
            st.bar_chart(daily_sum_receita, x_label="Dias do mês da fatura", y_label="Recebimentos")
        except:
            pass

    with tab4:

        st.markdown("## Forma de pagamento")

        forma_pagto = st.text_input("Adicione forma de pagamento")

        if st.button('Adicione forma de pagamento'):
            nova_forma_pagto = {
                'forma_pagto': forma_pagto,
                'user': st.user.email
            }

            doc_ref = forma_pgto_ref.document()

            doc_ref.set(nova_forma_pagto)

            transacoes = get_transactions_dataframe_from_month(mes, transacoes_ref)

            st.write("Forma de pagamanento adicionada com sucesso!")


    st.button("Log out", on_click=st.logout)
