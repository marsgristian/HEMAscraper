import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re

# Baixar recursos necessários do NLTK
try:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('punkt_tab')
except:
    pass

# Função para ler e processar arquivos
def ler_arquivo(caminho):
    """Lê um arquivo e retorna seu conteúdo"""
    try:
        with open(caminho, 'r', encoding='utf-8') as arquivo:
            return arquivo.read()
    except:
        with open(caminho, 'r', encoding='latin-1') as arquivo:
            return arquivo.read()

# Função para limpar texto
def limpar_texto(texto):
    """Remove metadados e limpa o texto"""
    linhas = texto.split('\n')
    texto_limpo = []
    
    for linha in linhas:
        # Pula linhas de metadados
        if linha.startswith('MASTER:') or linha.startswith('SOURCE BOOK:') or \
           linha.startswith('FIELD NAME:') or linha.startswith('TOTAL TEXTOS:') or \
           linha.startswith('=') or linha.startswith('[') and linha.endswith(']'):
            continue
        
        # Remove referências como (P1.S0)
        linha = re.sub(r'\(P\d+\.S\d+\)', '', linha)
        linha = re.sub(r'\[\s*\d+\s*\]', '', linha)
        
        if linha.strip():
            texto_limpo.append(linha.strip())
    
    return ' '.join(texto_limpo)

# Função para tokenizar e filtrar palavras
def processar_texto(texto):
    """Tokeniza o texto e remove stopwords"""
    # Stopwords em português
    stop_words = set(stopwords.words('portuguese'))
    
    # Adicionar palavras comuns específicas do contexto
    stop_words.update(['que', 'você', 'ele', 'ela', 'seu', 'sua', 'deve', 'fazer', 'como', 
                      'quando', 'onde', 'porque', 'então', 'assim', 'muito', 'mais', 'sem',
                      'ter', 'ser', 'estar', 'há', 'não', 'sim', 'bem', 'mal', 'todo',
                      'toda', 'todos', 'todas', 'um', 'uma', 'uns', 'umas', 'o', 'a',
                      'os', 'as', 'ao', 'aos', 'da', 'das', 'do', 'dos', 'na', 'nas',
                      'no', 'nos', 'com', 'por', 'para', 'de', 'em', 'se', 'lhe', 'me',
                      'te', 'nos', 'vos', 'lhes', 'isso', 'isto', 'aquilo', 'este',
                      'esta', 'estes', 'estas', 'esse', 'essa', 'esses', 'essas',
                      'aquele', 'aquela', 'aqueles', 'aquelas'])
    
    # Tokenizar
    tokens = word_tokenize(texto.lower())
    
    # Filtrar palavras
    palavras_filtradas = [palavra for palavra in tokens 
                         if palavra.isalpha() and 
                         len(palavra) > 2 and 
                         palavra not in stop_words]
    
    return palavras_filtradas



# Função para gerar nuvem de palavras
def gerar_nuvem_palavras():
    """Gera nuvem de palavras para cada arquivo"""
    
    # Ler arquivos
    arquivos = {
        'PT_UNI~1.TXT': ler_arquivo('PT_UNI~1.TXT'),
        'ENG_PT~1.TXT': ler_arquivo('ENG_PT~1.TXT'),
        'ENG_PT~2.TXT': ler_arquivo('ENG_PT~2.TXT')
    }
    
    # Processar textos
    textos_processados = {}
    for nome, conteudo in arquivos.items():
        texto_limpo = limpar_texto(conteudo)
        palavras = processar_texto(texto_limpo)
        textos_processados[nome] = palavras
    
    # Configurar figura
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Nuvens de Palavras - Arte Mestra de Giuseppe Colombani', fontsize=16)
    
    # Nuvem individual para cada arquivo
    for i, (nome, palavras) in enumerate(textos_processados.items()):
        if i < 3:  # Apenas os primeiros 3 arquivos
            ax = axes[i//2, i%2]
            
            # Criar texto para WordCloud
            texto_wc = ' '.join(palavras)
            
            # Configurar WordCloud
            wordcloud = WordCloud(
                width=400, 
                height=300,
                background_color='white',
                colormap='viridis',
                max_words=100,
                relative_scaling=0.5,
                min_font_size=10
            ).generate(texto_wc)
            
            # Plotar
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.set_title(f'{nome}', fontsize=12)
            ax.axis('off')
    
    # Nuvem combinada
    ax = axes[1, 1]
    todas_palavras = []
    for palavras in textos_processados.values():
        todas_palavras.extend(palavras)
    
    texto_combinado = ' '.join(todas_palavras)
    
    wordcloud_combinada = WordCloud(
        width=400, 
        height=300,
        background_color='white',
        colormap='plasma',
        max_words=150,
        relative_scaling=0.5,
        min_font_size=10
    ).generate(texto_combinado)
    
    ax.imshow(wordcloud_combinada, interpolation='bilinear')
    ax.set_title('Nuvem Combinada', fontsize=12)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('nuvem_palavras_esgrima.png', dpi=300, bbox_inches='tight')
    plt.show()

# Função principal
def main():
    """Função principal"""
    gerar_nuvem_palavras()

if __name__ == "__main__":
    main()
