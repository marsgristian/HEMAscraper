# Pós-processamento para unificar textos por source_book e field_name
# Cria arquivos de texto unificados para facilitar a leitura

import json
import os
from collections import defaultdict

def processar_arquivo(arquivo_entrada, prefixo_saida, pasta_saida):
    """
    Processa um arquivo JSONL e agrupa textos por source_book e field_name
    """
    print(f"Processando {arquivo_entrada}...")
    
    # Criar pasta de saída se não existir
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
        print(f"Pasta criada: {pasta_saida}")
    
    # Dicionário para agrupar textos
    grupos = defaultdict(lambda: defaultdict(list))
    
    # Ler arquivo JSONL
    with open(arquivo_entrada, 'r', encoding='utf-8') as f:
        for linha_num, linha in enumerate(f, 1):
            try:
                data = json.loads(linha)
                
                # Extrair informações necessárias
                source_book = data.get('source_book', 'unknown')
                field_name = data.get('field_name', 'unknown')
                texto = data.get('text', '')
                master_name = data.get('master_name', 'unknown')
                paragraph_id = data.get('paragraph_id', 0)
                sentence_id = data.get('sentence_id', 0)
                
                # Agrupar por source_book e field_name
                grupos[source_book][field_name].append({
                    'texto': texto,
                    'master_name': master_name,
                    'paragraph_id': paragraph_id,
                    'sentence_id': sentence_id,
                    'linha_original': linha_num
                })
                
            except json.JSONDecodeError:
                print(f"Erro JSON na linha {linha_num}")
            except Exception as e:
                print(f"Erro na linha {linha_num}: {e}")
    
    # Criar arquivos unificados
    total_arquivos = 0
    for source_book, fields in grupos.items():
        for field_name, textos in fields.items():
            # Ordenar por paragraph_id e sentence_id
            textos.sort(key=lambda x: (x['paragraph_id'], x['sentence_id']))
            
            # Nome do arquivo de saída
            nome_arquivo = f"{prefixo_saida}_{source_book}_{field_name}.txt"
            nome_arquivo = nome_arquivo.replace(' ', '_').replace('/', '_').replace('\\', '_')
            
            # Caminho completo do arquivo
            caminho_arquivo = os.path.join(pasta_saida, nome_arquivo)
            
            # Criar arquivo unificado
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write(f"MASTER: {textos[0]['master_name']}\n")
                f.write(f"SOURCE BOOK: {source_book}\n")
                f.write(f"FIELD NAME: {field_name}\n")
                f.write(f"TOTAL TEXTOS: {len(textos)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, item in enumerate(textos, 1):
                    f.write(f"[{i}] (P{item['paragraph_id']}.S{item['sentence_id']})\n")
                    f.write(f"{item['texto']}\n\n")
            
            total_arquivos += 1
            print(f"Criado: {caminho_arquivo} ({len(textos)} textos)")
    
    print(f"Total de arquivos criados: {total_arquivos}")
    return total_arquivos

def main():
    # Arquivos de entrada com suas respectivas pastas
    arquivos = [
        ('corpus_sentences_openai_pt.jsonl', 'unificado_pt_oai', 'Textos_Unificados_PT_OpenAI'),
        ('corpus_sentences_openai_eng_pt.jsonl', 'unificado_eng_pt_oai', 'Textos_Unificados_ENG_PT_OpenAI'),
        ('corpus_sentences_openai_eng.jsonl', 'unificado_eng_oai', 'Textos_Unificados_ENG_OpenAI')
    ]
    
    total_geral = 0
    
    for arquivo, prefixo, pasta in arquivos:
        if os.path.exists(arquivo):
            try:
                total = processar_arquivo(arquivo, prefixo, pasta)
                total_geral += total
                print(f"Concluído: {arquivo} -> {total} arquivos em {pasta}\n")
            except Exception as e:
                print(f"Erro ao processar {arquivo}: {e}\n")
        else:
            print(f"Arquivo não encontrado: {arquivo}\n")
    
    print(f"PROCESSAMENTO CONCLUÍDO")
    print(f"Total geral de arquivos unificados: {total_geral}")

if __name__ == "__main__":
    main()

