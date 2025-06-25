import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import os

_headers = {
        'User-Agent': 'Python Scraper for Academic Project - Contact: cristian.martins@estudante.ufscar.br'
    }

def coletar_mestres_por_idioma(idioma_alvo=None):
    """
    FASE 1 : Realiza web scrapping na página de Mestres da Wiktenauer
    para coletar os links de todos os mestres de esgrima associados ao idioma do parametro idioma.
    """
    base_url = "https://wiktenauer.com"
    url_mestres = f"{base_url}/wiki/Masters"
    
    print("--- FASE 1: Coletando links dos Mestres ---")
    
    try:
        response = requests.get(url_mestres, headers=_headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # --- PONTO DA CORREÇÃO ---
        # Em vez de procurar uma única tabela 'wikitable', procuramos todas as
        # tabelas de mestres, que agora usam a classe 'smwtable'.
        tabelas_mestres = soup.find_all('table', class_='smwtable')
        
        if not tabelas_mestres:
            print("Erro: Nenhuma tabela de mestres ('smwtable') foi encontrada na página.")
            return []

        mestres_italianos = []
        # Loop sobre cada tabela encontrada (uma para cada século)
        for tabela in tabelas_mestres:
            # Garante que a tabela tem um corpo (tbody) antes de continuar
            if tabela.find('tbody'):
                # Loop sobre cada linha da tabela atual
                for linha in tabela.find('tbody').find_all('tr'):
                    celulas = linha.find_all('td')
                    
                    # A estrutura da célula mudou um pouco. O idioma está na segunda célula (índice 1)
                    if len(celulas) >= 2: # Precisa de pelo menos 2 células: Artigo e Idioma
                        idioma = celulas[1].get_text(strip=True)

                        if idioma_alvo in idioma:
                            celula_nome = celulas[0]
                            link_tag = celula_nome.find('a')
                            if link_tag and link_tag.has_attr('href'):
                                nome_mestre = link_tag.get_text(strip=True)
                                link_completo = f"{base_url}{link_tag['href']}"
                                
                                mestres_italianos.append({
                                    "Nome do Mestre": nome_mestre,
                                    "Link": link_completo
                                })

        print(f"Sucesso! {len(mestres_italianos)} mestres italianos encontrados em {len(tabelas_mestres)} tabelas.")
        return mestres_italianos
    except Exception as e:
        print(f"Ocorreu um erro na Fase 1: {e}")
        return []


def analisar_pagina_mestre(master_name):
    """
    Analisa a página de um mestre da Wiktenauer, buscando a seção de tratados e verificando
    se há traduções nas tabelas associadas.

    Args:
        master_name (str): Nome do mestre no formato da URL da Wiktenauer (ex: "Philippo_di_Vadi").

    Returns:
        dict: Relatório com status geral, presença de tratados e traduções.
    """
    base_url = "https://wiktenauer.com"
    url = f"{base_url}/wiki/{master_name}"

    relatorio = {
        "mestre": master_name,
        "url": url,
        "status_geral": "Falha",
        "detalhe_status": "",
        "secao_tratados_encontrada": False,
        "possui_traducao": False,
        "tratados": []
    }

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        relatorio["detalhe_status"] = f"Erro de rede: {e}"
        return relatorio

    # --- 1. Localiza seção Treatise(s) ou Manuscripts ---
    secao_alvo = None
    for secao_id in ["Treatises", "Treatise", "Manuscripts"]:
        span = soup.find('span', id=secao_id)
        if span:
            secao_alvo = span.find_parent(['h2', 'h3'])
            relatorio["secao_tratados_encontrada"] = True
            break

    if not secao_alvo:
        relatorio["detalhe_status"] = "Seção de tratados/manuscritos não encontrada."
        return relatorio

    # --- 2. Busca tabelas após essa seção e verifica colunas com "translation" ---
    for elemento in secao_alvo.find_all_next():
        if elemento.name == secao_alvo.name:
            break  # Saiu da seção
        if elemento.name == 'table':
            tratado_info = {
                "possui_traducao": False,
                "header_traducao": None
            }
            for th in elemento.find_all('th'):
                texto = th.get_text(strip=True).lower()
                if 'translation' in texto:
                    tratado_info["possui_traducao"] = True
                    tratado_info["header_traducao"] = th.get_text(strip=True)
                    relatorio["possui_traducao"] = True
                    break
            relatorio["tratados"].append(tratado_info)

    if relatorio["tratados"]:
        relatorio["status_geral"] = "Sucesso" if relatorio["possui_traducao"] else "Aviso"
        relatorio["detalhe_status"] = f"{len(relatorio['tratados'])} tratado(s)/ texto(s) encontrado(s)."
    else:
        relatorio["status_geral"] = "Aviso"
        relatorio["detalhe_status"] = "Seção encontrada, mas nenhum tratado com tradução detectado."

    return relatorio

def coletar_textos_de_mestre(master_name):
    """
    Coleta parágrafos de todas as versões de textos (original e traduções) da página do mestre na Wiktenauer.

    Args:
        master_name (str): Nome do mestre no formato da URL da Wiktenauer (ex: "Philippo_di_Vadi").

    Returns:
        list: Lista de dicionários JSON, cada um representando um parágrafo com todas as versões coletadas.
              As chaves correspondem aos títulos reais das colunas da tabela no site.
    """
    base_url = "https://wiktenauer.com"
    url = f"{base_url}/wiki/{master_name}"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        return {"erro": str(e)}

    dados_json = []
    tabelas_html = soup.find_all('table')
    par_id_global = 0

    for tabela in tabelas_html:
        linhas = tabela.find_all('tr')
        if not linhas or len(linhas[0].find_all(['td', 'th'])) < 2:
            continue  # pula tabelas não paralelas

        # Título da seção anterior à tabela
        titulo_secao = tabela.find_previous(['h2', 'h3', 'h4'])
        titulo_normalizado = titulo_secao.get_text(strip=True).lower().replace(" ", "_") if titulo_secao else "desconhecido"
        source_book = f"{master_name.lower()}__{titulo_normalizado}"

        # Cabeçalhos reais da tabela
        header_row = linhas[0].find_all('th')
        if not header_row:
            continue  # ignora se não tem cabeçalhos
        headers = [th.get_text(strip=True) for th in header_row]

        for row in linhas[1:]:
            cols = row.find_all(['td', 'th'])
            if len(cols) != len(headers):
                continue  # ignora linhas quebradas
            par_dict = {
                "master_name": master_name,
                "master_url": url,
                "source_book": source_book,
                "paragraph_id": par_id_global
            }
            for i, cell in enumerate(cols):
                texto = cell.get_text(separator=" ", strip=True)
                if texto:
                    par_dict[headers[i]] = texto
            if len(par_dict) > 2:  # ao menos uma coluna de texto
                dados_json.append(par_dict)
                par_id_global += 1
    print(dados_json)
    return dados_json

def quebrar_paragrafos_em_frases(master_text_paragraph_json_list):
    """
        Realiza a granularizacao da equivalencia de trechos italianos e ingles. Ou seja, transforma paragrafos equivalentes em frases equivalentes, acrescentando no json
    
        Args:
            lista de json com os paragrafos equivalentes

        Returns:
            master_text_json_list: json list contendo os textos de um mestre no seguinte formato: 
                {
                    "master_name": "philipo di vadi"
                    "source_book": "vadi_codex",
                    "paragraph_id": 3,
                    "phrase_id": 53,
                    "it": "Capitulo primo incipit. Se alcun volesse intender e sapere...",
                    "en": "Chapter I begins. If you wish to truly know whether fencing is an art or science..."
                }
            Cada linha seria uma frase
    """
    #TODO


def salvar_json_dos_textos(novos_jsons, path_alvo):
    """
    Salva os textos em formato JSONL no path alvo, evitando duplicatas.
    Se o arquivo existir, edita; se não, cria.
    Imprime a situação: sucesso, criação, edição e duplicatas removidas.
    """
    chave_identificadora = lambda d: (
        d.get("source_book", "") + "||" +
        str(d.get("paragraph_id", "")) + "||" +
        json.dumps({k: v for k, v in d.items() if k not in ["source_book", "paragraph_id"]}, sort_keys=True)
    )

    ja_existentes = []
    if os.path.exists(path_alvo):
        try:
            with open(path_alvo, 'r', encoding='utf-8') as f:
                ja_existentes = [json.loads(linha) for linha in f if linha.strip()]
        except Exception as e:
            print(f"Erro ao ler arquivo existente: {e}")
            return

    # Indexa entradas existentes
    index_existente = set(map(chave_identificadora, ja_existentes))
    novos_filtrados = [d for d in novos_jsons if chave_identificadora(d) not in index_existente]

    total_antes = len(ja_existentes)
    total_novos = len(novos_filtrados)
    total_duplicados = len(novos_jsons) - total_novos

    try:
        modo = 'a' if os.path.exists(path_alvo) else 'w'
        with open(path_alvo, modo, encoding='utf-8') as f:
            for item in novos_filtrados:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"✅ Salvo em '{path_alvo}'")
        print(f"📌 {'Arquivo criado' if modo == 'w' else 'Arquivo editado'}")
        print(f"➕ {total_novos} novo(s) parágrafo(s) salvo(s)")
        print(f"⚠️ {total_duplicados} duplicado(s) ignorado(s)")
    except Exception as e:
        print(f"❌ Erro ao salvar o arquivo: {e}")