#!/usr/bin/env python3
"""
Script para organizar as intersecções similares entre as três pastas em uma estrutura de pastas.
Cria uma pasta para cada grupo de intersecção encontrado e copia os arquivos correspondentes.
"""

import os
import shutil
from collections import defaultdict
import re
from difflib import SequenceMatcher

def extrair_nome_base(nome_arquivo):
    """
    Extrai a parte do nome do arquivo após '_oai' e limpa para comparação
    """
    if '_oai_' in nome_arquivo:
        nome_base = nome_arquivo.split('_oai_', 1)[1]
    else:
        nome_base = nome_arquivo
    
    # Remove extensão
    nome_base = nome_base.replace('.txt', '')
    return nome_base

def normalizar_nome(nome):
    """
    Normaliza o nome para comparação mais flexível
    """
    # Convert to lowercase
    nome = nome.lower()
    
    # Remove caracteres especiais extras e normaliza espaços
    nome = re.sub(r'[_\-\(\)\[\]]+', ' ', nome)
    nome = re.sub(r'\s+', ' ', nome)
    nome = nome.strip()
    
    # Remove palavras comuns que podem variar
    palavras_remover = ['transcription', 'transcribed', 'by', 'edit', 'version', 'edition']
    palavras = nome.split()
    palavras_filtradas = [p for p in palavras if p not in palavras_remover]
    
    return ' '.join(palavras_filtradas)

def similaridade(nome1, nome2):
    """
    Calcula a similaridade entre dois nomes (0-1)
    """
    nome1_norm = normalizar_nome(nome1)
    nome2_norm = normalizar_nome(nome2)
    
    return SequenceMatcher(None, nome1_norm, nome2_norm).ratio()

def extrair_autor_obra(nome):
    """
    Extrai autor e obra principal do nome do arquivo
    """
    nome_norm = normalizar_nome(nome)
    
    # Divide por '__' se existir, senão usa o primeiro e segundo elemento após espaços
    if '__' in nome:
        partes = nome.split('__', 1)
        autor = normalizar_nome(partes[0])
        obra = normalizar_nome(partes[1]) if len(partes) > 1 else ""
    else:
        palavras = nome_norm.split()
        if len(palavras) >= 2:
            # Assume que as primeiras palavras são o autor
            autor = ' '.join(palavras[:2])
            obra = ' '.join(palavras[2:]) if len(palavras) > 2 else ""
        else:
            autor = nome_norm
            obra = ""
    
    return autor, obra

def listar_arquivos_pasta(pasta):
    """
    Lista todos os arquivos .txt de uma pasta
    """
    try:
        arquivos = []
        for arquivo in os.listdir(pasta):
            if arquivo.endswith('.txt'):
                arquivos.append(arquivo)
        return arquivos
    except FileNotFoundError:
        print(f"ERRO: Pasta '{pasta}' não encontrada")
        return []

def encontrar_grupos_similares(arquivos_por_pasta, limiar_similaridade=0.7):
    """
    Encontra grupos de arquivos similares entre as pastas
    """
    todos_arquivos = []
    
    # Preparar lista com todos os arquivos e suas informações
    for pasta, arquivos in arquivos_por_pasta.items():
        for arquivo in arquivos:
            nome_base = extrair_nome_base(arquivo)
            autor, obra = extrair_autor_obra(nome_base)
            todos_arquivos.append({
                'pasta': pasta,
                'caminho_pasta': pasta,
                'arquivo_completo': arquivo,
                'nome_base': nome_base,
                'autor': autor,
                'obra': obra,
                'nome_normalizado': normalizar_nome(nome_base)
            })
    
    grupos = []
    arquivos_processados = set()
    
    for i, arquivo1 in enumerate(todos_arquivos):
        if i in arquivos_processados:
            continue
            
        grupo_atual = [arquivo1]
        arquivos_processados.add(i)
        
        # Procurar arquivos similares
        for j, arquivo2 in enumerate(todos_arquivos):
            if j <= i or j in arquivos_processados:
                continue
            
            # Verificar similaridade por autor primeiro
            if arquivo1['autor'] and arquivo2['autor']:
                sim_autor = similaridade(arquivo1['autor'], arquivo2['autor'])
                if sim_autor > 0.8:  # Autor muito similar
                    sim_obra = similaridade(arquivo1['obra'], arquivo2['obra'])
                    if sim_obra > limiar_similaridade:
                        grupo_atual.append(arquivo2)
                        arquivos_processados.add(j)
                        continue
            
            # Verificar similaridade geral
            sim_geral = similaridade(arquivo1['nome_base'], arquivo2['nome_base'])
            if sim_geral > limiar_similaridade:
                grupo_atual.append(arquivo2)
                arquivos_processados.add(j)
        
        # Só adicionar grupos com mais de 1 arquivo
        if len(grupo_atual) > 1:
            grupos.append(grupo_atual)
    
    return grupos

def criar_nome_pasta_seguro(autor, obra, indice):
    """
    Cria um nome de pasta seguro baseado no autor e obra
    """
    # Limitar tamanho e remover caracteres especiais
    autor_clean = re.sub(r'[<>:"/\\|?*]', '_', autor)[:30]
    obra_clean = re.sub(r'[<>:"/\\|?*]', '_', obra)[:50]
    
    if obra_clean:
        nome = f"{indice:03d}_{autor_clean}__{obra_clean}"
    else:
        nome = f"{indice:03d}_{autor_clean}"
    
    # Limitar tamanho total
    if len(nome) > 100:
        nome = nome[:100]
    
    return nome

def main():
    # Definir as três pastas
    pastas_caminhos = {
        'ENG_PT_Direct': 'Textos_Unificados_ENG_PT_Direct_OpenAI',
        'ENG_PT': 'Textos_Unificados_ENG_PT_OpenAI', 
        'PT': 'Textos_Unificados_PT_OpenAI'
    }
    
    print("🔍 ENCONTRANDO INTERSECÇÕES SIMILARES ENTRE 3 PASTAS...")
    print("=" * 70)
    
    # Coletar arquivos de cada pasta
    arquivos_por_pasta = {}
    for nome_pasta, caminho_pasta in pastas_caminhos.items():
        print(f"\n📁 Processando: {nome_pasta}")
        arquivos = listar_arquivos_pasta(caminho_pasta)
        arquivos_por_pasta[nome_pasta] = arquivos
        print(f"   Encontrados: {len(arquivos)} arquivos")
    
    # Encontrar grupos similares
    print(f"\n🔎 BUSCANDO GRUPOS SIMILARES...")
    grupos = encontrar_grupos_similares(arquivos_por_pasta, limiar_similaridade=0.7)
    
    # Filtrar apenas grupos que tem as 3 pastas
    grupos_3_pastas = []
    for grupo in grupos:
        pastas_no_grupo = set(arquivo['pasta'] for arquivo in grupo)
        if len(pastas_no_grupo) == 3:
            grupos_3_pastas.append(grupo)
    
    print(f"\n✨ ENCONTRADOS {len(grupos_3_pastas)} GRUPOS EM TODAS AS 3 PASTAS!")
    
    if not grupos_3_pastas:
        print("❌ Nenhuma intersecção entre 3 pastas encontrada.")
        return
    
    # Criar pasta principal para organizar
    pasta_intersecoes = 'Intersecoes_Similares_3_Pastas'
    if not os.path.exists(pasta_intersecoes):
        os.makedirs(pasta_intersecoes)
        print(f"\n✅ Criada pasta principal: {pasta_intersecoes}")
    
    print(f"\n📁 ORGANIZANDO INTERSECÇÕES...")
    arquivos_copiados = 0
    
    for i, grupo in enumerate(grupos_3_pastas, 1):
        # Usar o primeiro arquivo como referência para o nome da pasta
        arquivo_ref = grupo[0]
        nome_pasta_seguro = criar_nome_pasta_seguro(arquivo_ref['autor'], arquivo_ref['obra'], i)
        pasta_destino = os.path.join(pasta_intersecoes, nome_pasta_seguro)
        
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
        
        print(f"\n{i:2d}. {arquivo_ref['autor']} - {arquivo_ref['obra'][:50]}...")
        print(f"    📂 Pasta: {nome_pasta_seguro}")
        
        # Organizar arquivos por pasta e copiar
        arquivos_por_pasta_grupo = defaultdict(list)
        for arquivo in grupo:
            arquivos_por_pasta_grupo[arquivo['pasta']].append(arquivo)
        
        # Copiar arquivos de cada pasta
        for pasta, arquivos_pasta in arquivos_por_pasta_grupo.items():
            print(f"    📄 {pasta}: {len(arquivos_pasta)} arquivo(s)")
            
            for j, arquivo in enumerate(arquivos_pasta):
                arquivo_origem = os.path.join(pastas_caminhos[arquivo['pasta']], arquivo['arquivo_completo'])
                
                # Se há múltiplos arquivos da mesma pasta, numerar
                if len(arquivos_pasta) > 1:
                    arquivo_destino = os.path.join(pasta_destino, f"{pasta}_{j+1:02d}_{arquivo['arquivo_completo']}")
                else:
                    arquivo_destino = os.path.join(pasta_destino, f"{pasta}_{arquivo['arquivo_completo']}")
                
                try:
                    shutil.copy2(arquivo_origem, arquivo_destino)
                    arquivos_copiados += 1
                    print(f"        ✅ {arquivo['nome_base'][:60]}...")
                except Exception as e:
                    print(f"        ❌ ERRO: {e}")
        
        # Calcular e mostrar similaridades
        print(f"    📈 Similaridades:")
        for j in range(len(grupo)):
            for k in range(j+1, len(grupo)):
                if grupo[j]['pasta'] != grupo[k]['pasta']:  # Apenas entre pastas diferentes
                    sim = similaridade(grupo[j]['nome_base'], grupo[k]['nome_base'])
                    print(f"        {grupo[j]['pasta']} ↔ {grupo[k]['pasta']}: {sim:.3f}")
    
    # Criar arquivo de resumo
    arquivo_resumo = os.path.join(pasta_intersecoes, 'RESUMO_INTERSECOES_SIMILARES.txt')
    with open(arquivo_resumo, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE INTERSECÇÕES SIMILARES - 3 PASTAS\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Total de grupos organizados: {len(grupos_3_pastas)}\n")
        f.write(f"Total de arquivos copiados: {arquivos_copiados}\n\n")
        
        f.write("GRUPOS ORGANIZADOS:\n")
        f.write("-" * 40 + "\n\n")
        
        for i, grupo in enumerate(grupos_3_pastas, 1):
            arquivo_ref = grupo[0]
            f.write(f"{i:2d}. {arquivo_ref['autor']} - {arquivo_ref['obra']}\n")
            
            # Mostrar quantos arquivos de cada pasta
            pastas_count = defaultdict(int)
            for arquivo in grupo:
                pastas_count[arquivo['pasta']] += 1
            
            for pasta, count in pastas_count.items():
                f.write(f"    {pasta}: {count} arquivo(s)\n")
            f.write("\n")
    
    print(f"\n💾 Resumo salvo em: {arquivo_resumo}")
    print(f"\n🎉 ORGANIZAÇÃO CONCLUÍDA!")
    print(f"📁 Verifique a pasta: {pasta_intersecoes}")
    print(f"📊 Total: {len(grupos_3_pastas)} grupos organizados")
    print(f"📄 Total: {arquivos_copiados} arquivos copiados")

if __name__ == "__main__":
    main() 