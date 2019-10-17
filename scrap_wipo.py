# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as bs
import pandas as pd
from pandas import read_excel
import requests
import os
import openpyxl

def corrige_texto(texto):
    txt = texto.strip().replace('\n', '').replace('\t', '')
    return txt

# cwd = os.getcwd()  # Get the current working directory (cwd)
# files = os.listdir(cwd)  # Get all the files in that directory
# print("Files in %r: %s" % (cwd, files))
#
# dir_arqs = cwd + '\\scrap_wipo_files\\' # concat directory files
# wipo_files = os.listdir(dir_arqs)
# print(wipo_files)
#
# df_list = []
# i = 1
# for arq in wipo_files:
#     print('laço - ',format(i))
#     dir = dir_arqs + arq
#     print("Dir - ",format(dir))
#     df = pd.read_excel(dir, index_col=None, nrows=None)
#     df_list.append(df)
#     i += 1
# df_result = pd.concat(df_list)
# df_links_proc = df_result
#
# df_links_proc.to_excel("dados.xlsx", sheet_name='dados')
# import pdb;pdb.set_trace()

# ------- lendo e selecionando os links para scrap --------
df_links_proc = pd.read_excel("dados.xlsx")
df_links_proc_links = df_links_proc['Links']
#df_links_proc_links = df_links_proc_links[1:20] # selecionando os 20 primeiros links para test
dados_scrap = []

for link in df_links_proc_links:
    scrap_result = {}
    inter_fill_date = ''
    applicants_names = []
    applicants_address = []
    inventors_names = []
    agents_names = []
    agents_address = []
    title_br = ''

    print(link)
    pg_proc  = requests.get(link)
    soup_proc = bs(pg_proc.content, "html.parser")
    form = soup_proc.find('form', {'id':'detailMainForm'})
    div_content = form.find('div',{'id':'detailMainForm:PCTBIBLIO_content'})
    tbl_content = div_content.find('table', {'id':'detailPCTtableHeader'})

    # tra contem todas as infos que se quer
    tra = tbl_content.findAll('tr', recursive=False)

    # ------------   filing date -------------------
    tb_inter_fill = tra[3].find('table', {'id': 'detailPCTtableDetail'})
    tr_filing = tb_inter_fill.findAll('tr')
    text_tr_filling = tr_filing[1].find('td', {'id':'detailPCTtableFilingDate'}).text
    #funcao para corrigir os espaços do texto
    inter_fill_date = corrige_texto(text_tr_filling)

    # ----------- Applicants -----------------------
    tb_inter_app = tra[5].find('span',{'id' : 'PCTapplicants'}).findAll('td')
    ap = 0
    applicants_names.clear()
    applicants_address.clear()

    while ap < len(tb_inter_app):
        text_ap = tb_inter_app[ap].text
        text_ap = text_ap.split(';')
        applicant = text_ap[0]
        try:
            ender_app = text_ap[1].replace('\n', ' ')
            ender_app = ender_app.strip()
            if ender_app != 'BR':
                applicants_address.append(ender_app.strip())
        except:
            print('Não tem endereço do(s) colaboradores')
            ender_app = 'Sem Info'
            applicants_address.append(ender_app.strip())

        names = applicant.split(';')[0]
        applicants_names.append(names)
        ap += 1

    #----------- inventors -----------------------
    inventors_names.clear()
    try:
        tb_inter_inv = tra[6].find('span', {'id': 'PCTinventors'}).findAll('td')
        for inventor in tb_inter_inv:
            name = inventor.text
            name = corrige_texto(name)
            inventors_names.append(name)
    except:
        print('Não foi possível extrair as informações dos inventores!')

    # ----------- Agents --------------------------
    agents_names.clear()
    agents_address.clear()
    name_agent = ''
    addr_agent = ''
    try:
        tb_agents = tra[7].find('span',{'id':'PCTagents'}).findAll('td')

        for tb in tb_agents:
            name_agent = tb.b.text
            if ender_app != 'BR':
                addr_agent = tb.text.split(';')[1].replace('\n', ' ')

    except:
        print("Não foi possível extrair as informações dos agentes!")
        name_agent = 'Sem Info'
        addr_agent = 'Sem Info'

    agents_names.append(name_agent)
    agents_address.append(addr_agent.strip())

    # --------- title br ------------------------
    try:
        title_br = tra[9].find(lang='pt').text
    except:
        print("Não contém a informação em português!")
        title_br = 'sem Info'

    # --------- tratando os campos ---------------

    links = link
    applicants_names = ', '.join(applicants_names)
    applicants_address = ', '.join(applicants_address)
    inventors_names = ', '.join(inventors_names)
    agents_names = ', '.join(agents_names)
    agents_address = ', '.join(agents_address)

    # --------- montando os dados do scrap -------

    scrap_result = {'Links': links,'International Filing Date': inter_fill_date, 'Applicants': applicants_names,
    'Applicant_address': applicants_address, 'Inventors': inventors_names, 'Agent': agents_names,
    'Agent_address': agents_address, 'Title_br': title_br }

    dados_scrap.append(scrap_result)

# --------- criando o dataframe final -------------------------
df_scrap = pd.DataFrame.from_dict(dados_scrap, orient='columns')

# --------- exportando o dataframe scrap em uma planilha -------
df_scrap.to_excel("dados_scrap.xlsx", sheet_name='dados_scrap')

# --------------- lendo a planilha e criando o dataframe--------
df_dados_iniciais = pd.read_excel('dados.xlsx')
df_dados_scrap = pd.read_excel('dados_scrap.xlsx')

# ------------- fazendo o merge entre os 2 dataframes ----------
df_merged = df_dados_iniciais.merge(df_dados_scrap, on='Links')

# --------- exportando o dataframe final em uma planilha -------
df_merged.to_excel("dados_merged_full.xlsx", sheet_name='dados_completos')

print("FIM")
# ----------- priority data ------------------
# p_dt = tra[8].find('span', {'class':'PCTpriority'}).findAll('td')
# priority_data.clear()
# for dt in p_dt:
#     data = dt.text
#     priority_data.append(data)
# priority_data = priority_data[0] + ' ' + priority_data[2] + ' ' + priority_data[3]

# ---------- publication language -----------
# trp = len(tra) - 2
# p_lang = tra[trp].findAll('td')
# p_lang = p_lang[1].text
# publication_language = corrige_texto(p_lang)

# ----------- filing language ---------------
# trf = len(tra) - 1
# f_lang = tra[trf].findAll('td')
# f_lang = f_lang[1].textp
# filing_language = corrige_texto(f_lang)


# base_url = 'https://patentscope.wipo.int/search/en/result.jsf?_vid='
# end_url = 'P22-K089AJ-79311'
# full_url = base_url + end_url
# pagina  = requests.get(full_url)
# import pdb;pdb.set_trace()
# soup = bs(pagina.content, "html.parser")
# form = soup.find('form', {'id':'resultListForm'})
# tb = form.find('tbody', {'id':'resultListForm:resultTable_data'})
# trs = tb.findAll('tr')
# import pdb;pdb.set_trace()
#
# collection_links_search = list()
#
# for tr in trs:
#     attr_a = tr.find('a')
#     link_a = attr_a['href']
#     url_do_proc = base_url + link_a
#     collection_links_search.append(url_do_proc)
#     print("Aqui no for!")
#     import pdb;pdb.set_trace()
