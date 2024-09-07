from flask import Flask, jsonify, request, make_response
from estrutura_db import Autor,Postagem,app,db
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps

#Configuração da porta
if __name__ == '__main__': app.run(host='0.0.0.0', port=8080, debug=False)

# Função para reutilizar a validação de tokens
def token_obrigatorio(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Verificar se um token foi enviado
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'mensagem': 'Token não foi incluído!'}, 401)

        # Se temos um token, validar acess consutalndo o BD
        try:
            resultado = jwt.decode(token, app.config['SECRET_KEY'],algorithms=["HS256"])
            autor = Autor.query.filter_by(id_autor=resultado['id_autor']).first()
        except:
            return jsonify({'mensagem': 'Token é inválido'}, 401)
        return f(autor, *args, **kwargs)
    return decorated


# Função de login
@app.route('/login')
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Login inválido', 401, {'WWW-Authenticate': 'Basic realm="Login obrigatório"'})

    usuario = Autor.query.filter_by(nome=auth.username).first() 
    if not usuario:
        return make_response('Login inválido', 401, {'WWW-Authenticate': 'Basic realm="Login obrigatório"'})
    
    if auth.password == usuario.senha:
        token = jwt.encode({'id_autor': usuario.id_autor,'exp': datetime.now(timezone.utc) + timedelta(minutes=30)},app.config['SECRET_KEY'])
        return jsonify({'token':token})
    return make_response('Login inválido', 401, {'WWW-Authenticate': 'Basic realm="Login obrigatório"'})

# Rota padrão - GET https://localhost:5000
@app.route('/postagem', methods=['GET'])
@token_obrigatorio
def obter_postagens(autor):
    postagens = Postagem.query.all()
    lista_postagens = []
    for postagem in postagens:
        postagem_atual = {}
        postagem_atual['titulo'] = postagem.titulo
        postagem_atual['id_autor'] = postagem.id_autor
        lista_postagens.append(postagem_atual)
    return jsonify({'postagens': lista_postagens})

# Obter postagem por ID - GET http://localhost:5000/postagem/1
@app.route('/postagem/<int:id_postagem>', methods=['GET'])
@token_obrigatorio
def obter_postagem_por_indice(autor, id_postagem):
    postagem = Postagem.query.filter_by(id_postagem=id_postagem).first()
    if not postagem:
        return jsonify('Esta postagem não foi encontrada')
    
    postagem_atual = {}
    postagem_atual['titulo'] = postagem.titulo
    postagem_atual['id_autor'] = postagem.id_autor

    return jsonify({'postagem': postagem_atual})

# Criar uma nova postagem - POST http://localhost:5000/postagem
@app.route('/postagem', methods=['POST'])
@token_obrigatorio
def nova_postagem(autor):
    novas_postagens = request.get_json()
    for postagem in novas_postagens:
        autor_conforme_id = Autor.query.filter_by(id_autor=postagem['id_autor']).first()
        if not autor_conforme_id:
            pass
        else:
            nova_postagem = Postagem(titulo=postagem['titulo'], id_autor=postagem['id_autor'])
            db.session.add(nova_postagem)
    
    db.session.commit()

    return jsonify({'mensagem': 'Postage(s) criada(s) com sucesso!'})

# Alterar uma postagem - PUT http://localhost:5000/postagem/1
@app.route('/postagem/<int:id_postagem>', methods=['PUT'])
@token_obrigatorio
def alterar_postagem(autor, id_postagem):
    postagem_a_alterar = request.get_json()
    postagem_alterado = Postagem.query.filter_by(id_postagem=id_postagem).first()
    
    if not postagem_a_alterar:
        return jsonify({'Mensagem': 'Está postagem não foi encontrada!'})
    try:       
        postagem_alterado.titulo = postagem_a_alterar['titulo']
    except:
        pass
    try:
        postagem_alterado.id_autor = postagem_a_alterar['id_autor']
    except:
        pass
    
    db.session.commit()
    return jsonify({'mensagem': 'Postagem alterada com sucesso!'})

# Alterar uma postagem - DELETE http://localhost:5000/postagem/1
@app.route('/postagem/<int:id_postagem>', methods=['DELETE'])
@token_obrigatorio
def excluir_postagem(autor, id_postagem):
    try:
        postagem_a_excluir = Postagem.query.filter_by(id_postagem=id_postagem).first()
        if postagem_a_excluir[id_postagem] is not None:
            del postagem_a_excluir[id_postagem]
            return jsonify(f'Foi excluído a postagem {postagem_a_excluir[id_postagem]}', 200)
    except:
        return jsonify(f'Não foi possível encontrar a postagem para exclusão', 400)


@app.route('/autores', methods=['GET'])
@token_obrigatorio
def obter_autores(autor):
    autores = Autor.query.all()
    lista_de_autores = []
    for autor_buscado in autores:
        autor_atual = {}
        autor_atual['id_autor'] = autor_buscado.id_autor
        autor_atual['nome'] = autor_buscado.nome
        autor_atual['email'] = autor_buscado.email
        lista_de_autores.append(autor_atual)

    return jsonify({'autores': lista_de_autores})

@app.route('/autores/<int:id_autor>', methods=['GET'])
@token_obrigatorio
def obter_autor_por_id(autor, id_autor):
    autor = Autor.query.filter_by(id_autor=id_autor).first()
    if not autor:
        return jsonify('Autor não encontrado!')
    autor_atual = {}
    autor_atual['id_autor'] = autor.id_autor
    autor_atual['nome'] = autor.nome
    autor_atual['email'] = autor.email

    return jsonify({'autor': autor_atual})

@app.route('/autores', methods=['POST'])
@token_obrigatorio
def novo_autor(autor):
    novos_autores = request.get_json()
    for autor in novos_autores:
        novo_autor = Autor(nome=autor['nome'], senha=autor['senha'], email=autor['email'])
        db.session.add(novo_autor)
    
    db.session.commit()

    return jsonify({'mensagem': 'Usuário(s) criado com sucesso!'})

@app.route('/autores/<int:id_autor>', methods=['PUT'])
@token_obrigatorio
def alterar_autor(autor, id_autor):
    autor_a_alterar = request.get_json()
    autor_alterado = Autor.query.filter_by(id_autor=id_autor).first()
    
    if not autor_a_alterar:
        return jsonify({'Mensagem': 'Este usuário não foi encontrado!'})
    try:       
        autor_alterado.nome = autor_a_alterar['nome']
    except:
        pass
    try:
        autor_alterado.email = autor_a_alterar['email']
    except:
        pass

    try:
        autor_alterado.senha = autor_a_alterar['senha']
    except:
        pass
    
    db.session.commit()
    return jsonify({'mensagem': 'Usuário alterado com sucesso!'})


@app.route('/autores/<int:id_autor>', methods=['DELETE'])
@token_obrigatorio
def excluir_autor(autor, id_autor):
    autor_existente = Autor.query.filter_by(id_autor=id_autor).first()
    if not autor_existente:
        return jsonify({'mensagem': 'Este autor não foi encontrado'})

    db.session.delete(autor_existente)
    db.session.commit()

    return jsonify({'mensagem': 'Autor excluído com sucesso!'})





app.run(port=5000, host='localhost', debug=True)