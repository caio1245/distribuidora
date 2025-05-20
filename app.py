from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3

app = Flask(__name__)

# Criar banco de dados se não existir
def criar_banco():
    conn = sqlite3.connect('banco.db')
    c = conn.cursor()
    # Criação da tabela de produtos
    c.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        preco REAL
    )
    ''')
    # Criação da tabela de vendas
    c.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER,
        quantidade INTEGER,
        total REAL,
        FOREIGN KEY (produto_id) REFERENCES produtos (id)
    )
    ''')
    conn.commit()
    conn.close()


# Inicializa o banco ao iniciar
#init_db()

# Rotas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/produtos', methods=['GET', 'POST'])
def produtos():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        cursor.execute('INSERT INTO produtos (nome, preco) VALUES (?, ?)', (nome, preco))
        conn.commit()
        return redirect(url_for('produtos'))

    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    conn.close()
    return render_template('produtos.html', produtos=produtos)

@app.route('/vendas', methods=['GET', 'POST'])
def vendas():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            produto_id = request.form['produto_id']
            quantidade = int(request.form['quantidade'])
            cursor.execute('SELECT preco FROM produtos WHERE id = ?', (produto_id,))
            preco = cursor.fetchone()[0]
            if preco is None:
                raise ValueError("Produto inválido.")
            
            total = quantidade * preco
            cursor.execute('INSERT INTO vendas (produto_id, quantidade, total) VALUES (?, ?, ?)', 
                           (produto_id, quantidade, total))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return render_template('vendas.html', error=str(e))

    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()

    # Formatar dados de vendas como dicionários
    cursor.execute('''
        SELECT v.id, p.nome AS produto, v.quantidade, v.total 
        FROM vendas v 
        JOIN produtos p ON v.produto_id = p.id
    ''')
    vendas = [
        {"id": row[0], "produto": row[1], "quantidade": row[2], "total": row[3]}
        for row in cursor.fetchall()
    ]
    conn.close()

    return render_template('vendas.html', produtos=produtos, vendas=vendas)

@app.route('/relatorio')
def relatorio():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(total) FROM vendas')
    total_vendas = cursor.fetchone()[0] or 0
    cursor.execute('SELECT COUNT(*) FROM vendas')
    total_transacoes = cursor.fetchone()[0]
    conn.close()
    return render_template('relatorio.html', total_vendas=total_vendas, total_transacoes=total_transacoes)

@app.route('/remover_venda/<int:venda_id>', methods=['POST'])
def remover_venda(venda_id):
    with sqlite3.connect('banco.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM vendas WHERE id = ?', (venda_id,))
        conn.commit()
    return redirect(url_for('vendas'))

@app.route('/remover_produto/<int:produto_id>', methods=['POST'])
def remover_produto(produto_id):
    with sqlite3.connect('banco.db') as conn:
        cursor = conn.cursor()
        # Antes de remover, você pode verificar se esse produto está em alguma venda e decidir se remove ou não
        cursor.execute('DELETE FROM produtos WHERE id = ?', (produto_id,))
        conn.commit()
    return redirect(url_for('produtos'))


@app.route('/editar_produto/<int:produto_id>', methods=['GET', 'POST'])
def editar_produto(produto_id):
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        cursor.execute('UPDATE produtos SET nome = ?, preco = ? WHERE id = ?', (nome, preco, produto_id))
        conn.commit()
        conn.close()
        return redirect(url_for('produtos'))

    cursor.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,))
    produto = cursor.fetchone()
    conn.close()
    if produto is None:
        return "Produto não encontrado", 404
    return render_template('editar_produto.html', produto=produto)








if __name__ == '__main__':
    criar_banco()
    app.run(debug=True)
