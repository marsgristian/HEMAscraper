import nltk
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score
from nltk.tokenize import word_tokenize
from nltk.util import ngrams
import re
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
from difflib import SequenceMatcher
import matplotlib.pyplot as plt
import seaborn as sns

# Baixar recursos necessários do NLTK
try:
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('punkt_tab')
    nltk.download('omw-1.4')
except:
    pass

class MetricasTraducao:
    def __init__(self):
        self.smoothing = SmoothingFunction()
        
    def ler_arquivo(self, caminho):
        """Lê um arquivo e retorna seu conteúdo"""
        try:
            with open(caminho, 'r', encoding='utf-8') as arquivo:
                return arquivo.read()
        except:
            with open(caminho, 'r', encoding='latin-1') as arquivo:
                return arquivo.read()
    
    def limpar_texto(self, texto):
        """Remove metadados e limpa o texto"""
        linhas = texto.split('\n')
        texto_limpo = []
        
        for linha in linhas:
            # Pula linhas de metadados
            if linha.startswith('MASTER:') or linha.startswith('SOURCE BOOK:') or \
               linha.startswith('FIELD NAME:') or linha.startswith('TOTAL TEXTOS:') or \
               linha.startswith('=') or (linha.startswith('[') and linha.endswith(']')):
                continue
            
            # Remove referências como (P1.S0)
            linha = re.sub(r'\(P\d+\.S\d+\)', '', linha)
            linha = re.sub(r'\[\s*\d+\s*\]', '', linha)
            
            if linha.strip():
                texto_limpo.append(linha.strip())
        
        return ' '.join(texto_limpo)
    
    def tokenizar(self, texto):
        """Tokeniza o texto"""
        return word_tokenize(texto.lower())
    
    def calcular_bleu(self, referencia, candidato, max_n=4):
        """Calcula BLEU score para diferentes n-gramas"""
        ref_tokens = self.tokenizar(referencia)
        cand_tokens = self.tokenizar(candidato)
        
        # BLEU scores para diferentes n-gramas
        bleu_scores = {}
        
        for n in range(1, max_n + 1):
            if n == 1:
                weights = (1.0, 0, 0, 0)
            elif n == 2:
                weights = (0.5, 0.5, 0, 0)
            elif n == 3:
                weights = (0.33, 0.33, 0.33, 0)
            else:
                weights = (0.25, 0.25, 0.25, 0.25)
            
            try:
                bleu = sentence_bleu([ref_tokens], cand_tokens, 
                                   weights=weights, 
                                   smoothing_function=self.smoothing.method1)
                bleu_scores[f'BLEU-{n}'] = bleu
            except:
                bleu_scores[f'BLEU-{n}'] = 0.0
        
        return bleu_scores
    
    def calcular_ter(self, referencia, candidato):
        """Calcula Translation Error Rate (TER)"""
        ref_tokens = self.tokenizar(referencia)
        cand_tokens = self.tokenizar(candidato)
        
        # Usar SequenceMatcher para calcular edições
        matcher = SequenceMatcher(None, ref_tokens, cand_tokens)
        
        # Calcular operações de edição
        operations = matcher.get_opcodes()
        edits = 0
        
        for op, i1, i2, j1, j2 in operations:
            if op == 'replace':
                edits += max(i2 - i1, j2 - j1)
            elif op == 'delete':
                edits += i2 - i1
            elif op == 'insert':
                edits += j2 - j1
        
        # TER = número de edições / número de palavras na referência
        ter = edits / len(ref_tokens) if len(ref_tokens) > 0 else 0
        return ter
    
    def calcular_chrf(self, referencia, candidato, beta=2):
        """Calcula chrF score (Character-level F-score)"""
        ref_chars = list(referencia.lower().replace(' ', ''))
        cand_chars = list(candidato.lower().replace(' ', ''))
        
        # Calcular n-gramas de caracteres (1-6)
        precision_scores = []
        recall_scores = []
        
        for n in range(1, 7):
            ref_ngrams = Counter([''.join(gram) for gram in ngrams(ref_chars, n)])
            cand_ngrams = Counter([''.join(gram) for gram in ngrams(cand_chars, n)])
            
            if sum(cand_ngrams.values()) == 0:
                precision = 0
            else:
                matches = sum((ref_ngrams & cand_ngrams).values())
                precision = matches / sum(cand_ngrams.values())
            
            if sum(ref_ngrams.values()) == 0:
                recall = 0
            else:
                matches = sum((ref_ngrams & cand_ngrams).values())
                recall = matches / sum(ref_ngrams.values())
            
            precision_scores.append(precision)
            recall_scores.append(recall)
        
        # Calcular F-score média
        avg_precision = np.mean(precision_scores)
        avg_recall = np.mean(recall_scores)
        
        if avg_precision + avg_recall == 0:
            return 0
        
        chrf = (1 + beta**2) * avg_precision * avg_recall / (beta**2 * avg_precision + avg_recall)
        return chrf
    
    def analise_ngramas(self, texto, max_n=4):
        """Analisa n-gramas no texto"""
        tokens = self.tokenizar(texto)
        ngramas_stats = {}
        
        for n in range(1, max_n + 1):
            ngramas = list(ngrams(tokens, n))
            contador = Counter(ngramas)
            
            ngramas_stats[f'{n}-gramas'] = {
                'total': len(ngramas),
                'unicos': len(contador),
                'mais_comuns': contador.most_common(10)
            }
        
        return ngramas_stats
    
    def calcular_similaridade_jaccard(self, ref_tokens, cand_tokens):
        """Calcula similaridade de Jaccard"""
        set_ref = set(ref_tokens)
        set_cand = set(cand_tokens)
        
        intersection = len(set_ref & set_cand)
        union = len(set_ref | set_cand)
        
        return intersection / union if union > 0 else 0
    
    def comparar_arquivos(self):
        """Compara os três arquivos usando todas as métricas"""
        
        # Carregar arquivos
        arquivos = {
            'PT_UNI~1.TXT': self.ler_arquivo('PT_UNI~1.TXT'),
            'ENG_PT~1.TXT': self.ler_arquivo('ENG_PT~1.TXT'),
            'ENG_PT~2.TXT': self.ler_arquivo('ENG_PT~2.TXT')
        }
        
        # Limpar textos
        textos_limpos = {}
        for nome, conteudo in arquivos.items():
            textos_limpos[nome] = self.limpar_texto(conteudo)
        
        # Comparações par a par
        nomes = list(textos_limpos.keys())
        resultados = []
        
        for i, ref_nome in enumerate(nomes):
            for j, cand_nome in enumerate(nomes):
                if i != j:
                    ref_texto = textos_limpos[ref_nome]
                    cand_texto = textos_limpos[cand_nome]
                    
                    # Calcular métricas
                    bleu_scores = self.calcular_bleu(ref_texto, cand_texto)
                    ter = self.calcular_ter(ref_texto, cand_texto)
                    chrf = self.calcular_chrf(ref_texto, cand_texto)
                    
                    # Similaridade Jaccard
                    ref_tokens = self.tokenizar(ref_texto)
                    cand_tokens = self.tokenizar(cand_texto)
                    jaccard = self.calcular_similaridade_jaccard(ref_tokens, cand_tokens)
                    
                    # METEOR (se disponível)
                    try:
                        meteor = meteor_score([ref_tokens], cand_tokens)
                    except:
                        meteor = 0.0
                    
                    resultado = {
                        'Referência': ref_nome,
                        'Candidato': cand_nome,
                        'BLEU-1': bleu_scores['BLEU-1'],
                        'BLEU-2': bleu_scores['BLEU-2'],
                        'BLEU-3': bleu_scores['BLEU-3'],
                        'BLEU-4': bleu_scores['BLEU-4'],
                        'TER': ter,
                        'chrF': chrf,
                        'Jaccard': jaccard,
                        'METEOR': meteor
                    }
                    
                    resultados.append(resultado)
        
        # Criar DataFrame
        df = pd.DataFrame(resultados)
        
        # Salvar resultados
        df.to_csv('metricas_comparacao.csv', index=False)
        
        # Gerar gráficos
        self.gerar_graficos(df)
        
        return df
    
    def gerar_graficos(self, df):
        """Gera gráficos das métricas"""
        
        # Configurar estilo
        plt.style.use('seaborn-v0_8')
        
        # Gráfico 1: Heatmap das métricas
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # BLEU scores
        bleu_data = df.pivot_table(index='Referência', columns='Candidato', values='BLEU-1')
        sns.heatmap(bleu_data, annot=True, fmt='.3f', cmap='YlOrRd', ax=axes[0,0])
        axes[0,0].set_title('BLEU-1 Scores')
        
        # TER
        ter_data = df.pivot_table(index='Referência', columns='Candidato', values='TER')
        sns.heatmap(ter_data, annot=True, fmt='.3f', cmap='YlOrRd_r', ax=axes[0,1])
        axes[0,1].set_title('TER Scores')
        
        # chrF
        chrf_data = df.pivot_table(index='Referência', columns='Candidato', values='chrF')
        sns.heatmap(chrf_data, annot=True, fmt='.3f', cmap='YlOrRd', ax=axes[1,0])
        axes[1,0].set_title('chrF Scores')
        
        # Jaccard
        jaccard_data = df.pivot_table(index='Referência', columns='Candidato', values='Jaccard')
        sns.heatmap(jaccard_data, annot=True, fmt='.3f', cmap='YlOrRd', ax=axes[1,1])
        axes[1,1].set_title('Jaccard Similarity')
        
        plt.tight_layout()
        plt.savefig('metricas_heatmap.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Gráfico 2: Comparação BLEU
        fig, ax = plt.subplots(figsize=(12, 8))
        
        x = np.arange(len(df))
        width = 0.2
        bleu_metrics = ['BLEU-1', 'BLEU-2', 'BLEU-3', 'BLEU-4']
        
        for i, bleu in enumerate(bleu_metrics):
            ax.bar(x + i*width, df[bleu], width, label=bleu, alpha=0.8)
        
        ax.set_xlabel('Comparações')
        ax.set_ylabel('BLEU Score')
        ax.set_title('Comparação de Scores BLEU por N-gramas')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels([f"{row['Referência'][:8]} vs {row['Candidato'][:8]}" 
                           for _, row in df.iterrows()], rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('bleu_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    """Função principal"""
    analisador = MetricasTraducao()
    df_resultados = analisador.comparar_arquivos()
    return df_resultados

if __name__ == "__main__":
    resultados = main()
