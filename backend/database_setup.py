import sqlite3

# Nome do arquivo do banco de dados
BD_NOME = 'irrigacao_data.db'

# Função para criar tabela
def criar_tabela():
    conexao = None; # Inicializa conn como None
    try:
        # Conecta ao banco de dados (cria o arquivo se não existir)
        conexao = sqlite3.connect(BD_NOME)
        cursor = conexao.cursor()

        # Cria a tabela se ela não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumo_agua (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                quantidade_ml REAL NOT NULL
            )
        ''')

        conexao.commit()
        print(f"Tabela 'consumo_agua' verificada/criada com sucesso no banco '{BD_NOME}'!")

    except sqlite3.Error as e:
        print("Erro ao criar tabela: {e}")
    finally:
        if conexao:
            conexao.close()

if __name__ == '__main__':
    criar_tabela()
    
        
        