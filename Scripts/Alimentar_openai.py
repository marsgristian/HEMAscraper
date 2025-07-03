# Pegar o corpus_sentences.jsonl e traduzir apenas as linhas que contém lang": "it"
# Criar um novo arquivo corpus_sentences_openai_pt.jsonl com as traduções usando OpenAI
# Sistema de checkpoint para retomar processamento

import json
import time
import os
from Traducao import traduzir_texto_contextualizado_openai

# Configurações
CHECKPOINT_FILE = '/HEMAscraper/Scripts/checkpoint_openai.json'
OUTPUT_FILE = '/HEMAscraper/Scripts/corpus_sentences_openai_pt.jsonl'
INPUT_FILE = '/HEMAscraper/Scripts/corpus_sentences.jsonl'

def load_checkpoint():
    """Carrega o checkpoint se existir"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {'last_processed_line': 0, 'translated_count': 0}

def save_checkpoint(line_number, translated_count):
    """Salva o checkpoint atual"""
    checkpoint = {
        'last_processed_line': line_number,
        'translated_count': translated_count,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)

def count_total_italian_lines():
    """Conta o total de linhas em italiano para mostrar progresso"""
    count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data['lang'] == 'it':
                    count += 1
            except:
                continue
    return count

checkpoint = load_checkpoint()
start_line = checkpoint['last_processed_line']
translated_count = checkpoint['translated_count']
total_italian_lines = count_total_italian_lines()

print(f"Iniciando processamento OpenAI...")
print(f"Total linhas italiano: {total_italian_lines}")
print(f"Retomando da linha: {start_line}")
print(f"Ja traduzidas: {translated_count}")

current_line = 0
italian_lines_found = 0

# Determinar modo de abertura do arquivo de saída
output_mode = 'a' if start_line > 0 else 'w'

# Abrir o arquivo de saída para escrever as traduções
with open(OUTPUT_FILE, output_mode, encoding='utf-8') as output_file:
    with open(INPUT_FILE, 'r', encoding='utf-8') as input_file:
        for line in input_file:
            current_line += 1
            
            # Pular linhas já processadas
            if current_line <= start_line:
                continue
                
            try:
                data = json.loads(line)
                if data['lang'] == 'it':
                    italian_lines_found += 1
                    print(f"[OpenAI] Processando {italian_lines_found}/{total_italian_lines} - linha {current_line}")
                    
                    # Traduzir o texto para o português usando OpenAI
                    contexto = f"Texto histórico sobre esgrima medieval do mestre {data['master_name']} do século XV"
                    traducao = traduzir_texto_contextualizado_openai(
                        data['text'], 
                        'italiano medieval', 
                        'português', 
                        contexto
                    )
                    
                    if traducao:
                        # Criar nova entrada com tradução
                        new_data = data.copy()
                        new_data['lang'] = 'pt-oai'
                        new_data['text'] = traducao.strip()
                        
                        # Escrever no arquivo de saída
                        output_file.write(json.dumps(new_data, ensure_ascii=False) + '\n')
                        output_file.flush()  # Garantir que seja escrito imediatamente
                        translated_count += 1
                        print(f"[OpenAI] Traduzido ({translated_count})")
                    else:
                        print("Erro na traducao OpenAI")
                    
                    # Salvar checkpoint a cada 10 traduções
                    if translated_count % 10 == 0:
                        save_checkpoint(current_line, translated_count)
                        print(f"Checkpoint OpenAI salvo - {translated_count}/{total_italian_lines}")
                    
                    # Pausa menor para OpenAI (sem limite de RPM tão restritivo)
                    time.sleep(1)
                        
            except json.JSONDecodeError:
                print(f"Erro JSON linha {current_line}")
            except KeyboardInterrupt:
                print("Interrompido pelo usuario")
                save_checkpoint(current_line, translated_count)
                break
            except Exception as e:
                print(f"Erro linha {current_line}: {e}")

# Salvar checkpoint final
save_checkpoint(current_line, translated_count)

print("Processamento OpenAI concluido")
print(f"Total traduzidas: {translated_count}")
print(f"Arquivo: {OUTPUT_FILE}")

# Remover checkpoint se processamento completo
if translated_count >= total_italian_lines:
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print("Checkpoint OpenAI removido") 