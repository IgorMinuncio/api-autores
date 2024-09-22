from flask import Flask, jsonify, request, make_response
from estrutura_db import Autor,Postagem,app,db
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps

def sort_list_by_id(json):
    try:
        return int(json['id'])
    except KeyError:
        return 0

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

# Obter postagens - GET https://localhost:5000/postagem
@app.route('/postagem', methods=['GET'])
@token_obrigatorio
def obter_postagens(postagem):
    postagens = Postagem.query.all()
    lista_postagens = []
    for postagem in postagens:
        postagem_atual = {}
        postagem_atual['id'] = postagem.id_postagem
        postagem_atual['titulo'] = postagem.titulo
        postagem_atual['id_autor'] = postagem.id_autor
        lista_postagens.append(postagem_atual)
        lista_postagens.sort(key=sort_list_by_id, reverse=False)

    return jsonify({'postagens': lista_postagens})

# Obter postagem por ID - GET http://localhost:5000/postagem/1
@app.route('/postagem/<int:id_postagem>', methods=['GET'])
@token_obrigatorio
def obter_postagem_por_indice(postagem, id_postagem):
    postagem = Postagem.query.filter_by(id_postagem=id_postagem).first()
    if not postagem:
        return jsonify({'Mensagem':'Esta postagem não existe ou foi excluída'})
    
    postagem_atual = {}
    postagem_atual['id'] = postagem.id_postagem
    postagem_atual['titulo'] = postagem.titulo
    postagem_atual['id_autor'] = postagem.id_autor

    return jsonify({'postagem': postagem_atual})

# Criar uma nova postagem - POST http://localhost:5000/postagem
@app.route('/postagem', methods=['POST'])
@token_obrigatorio
def nova_postagem(postagem):
    novas_postagens = request.get_json()
    for postagem in novas_postagens:
        autor_conforme_id = Autor.query.filter_by(id_autor=postagem['id_autor']).first()
        if not autor_conforme_id:
            return jsonify({'Mensagem':'Id de autor informado não é válido!'})
        else:
            nova_postagem = Postagem(titulo=postagem['titulo'], id_autor=postagem['id_autor'])
            db.session.add(nova_postagem)
    
    db.session.commit()

    return jsonify({'Mensagem': 'Postage(s) criada(s) com sucesso!'})

# Alterar uma postagem - PUT http://localhost:5000/postagem/1
@app.route('/postagem/<int:id_postagem>', methods=['PUT'])
@token_obrigatorio
def alterar_postagem(postagem, id_postagem):
    json_com_alteracao = request.get_json()
    postagem_a_alterar = Postagem.query.filter_by(id_postagem=id_postagem).first()
    
    if not postagem_a_alterar:
        return jsonify({'Mensagem': 'Esta postagem não existe ou foi excluída.'})
    try:       
        postagem_a_alterar.titulo = json_com_alteracao['titulo']
    except:
        pass
    try:
        postagem_a_alterar.id_autor = json_com_alteracao['id_autor']
    except:
        pass
    
    db.session.commit()
    return jsonify({'Mensagem': 'Postagem alterada com sucesso!'})

# Excluir uma postagem - DELETE http://localhost:5000/postagem/1
@app.route('/postagem/<int:id_postagem>', methods=['DELETE'])
@token_obrigatorio
def excluir_postagem(postagem, id_postagem):
    postagem_a_excluir = Postagem.query.filter_by(id_postagem=id_postagem).first()
    if not postagem_a_excluir:
        return jsonify({'Mensagem': 'Postagem não foi encontrada!'})
    else:    
        db.session.delete(postagem_a_excluir)

    db.session.commit()
    return jsonify({'Mensagem': 'Postagem excluída com sucesso!'})

# Obter autores - GET http://localhost:5000/autor
@app.route('/autor', methods=['GET'])
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
        lista_de_autores.sort(key=sort_list_by_id, reverse=False)

    return jsonify({'autores': lista_de_autores})

# Obter autores por id - GET http://localhost:5000/autor/1
@app.route('/autor/<int:id_autor>', methods=['GET'])
@token_obrigatorio
def obter_autor_por_id(autor, id_autor):
    autor = Autor.query.filter_by(id_autor=id_autor).first()
    if not autor:
        return jsonify({'Mensagem':'Este Autor não existe ou foi excluído!'})
    autor_atual = {}
    autor_atual['id_autor'] = autor.id_autor
    autor_atual['nome'] = autor.nome
    autor_atual['email'] = autor.email

    return jsonify({'autor': autor_atual})

# Criar um novo autor - POST http://localhost:5000/autor
@app.route('/autor', methods=['POST'])
@token_obrigatorio
def novo_autor(autor):
    novos_autores = request.get_json()
    for autor in novos_autores:
        novo_autor = Autor(nome=autor['nome'], senha=autor['senha'], email=autor['email'])
        db.session.add(novo_autor)
    
    db.session.commit()
    return jsonify({'Mensagem': 'Autor(es) criado(s) com sucesso!'})

# Alterar um autor - PUT http://localhost:5000/autor/1
@app.route('/autor/<int:id_autor>', methods=['PUT'])
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
    return jsonify({'Mensagem': 'Usuário alterado com sucesso!'})

# Excluir um autor - DELETE http://localhost:5000/autor/1
@app.route('/autor/<int:id_autor>', methods=['DELETE'])
@token_obrigatorio
def excluir_autor(autor, id_autor):
    autor_existente = Autor.query.filter_by(id_autor=id_autor).first()
    if not autor_existente:
        return jsonify({'Mensagem': 'Este autor não foi encontrado'})

    db.session.delete(autor_existente)
    db.session.commit()

    return jsonify({'Mensagem': 'Autor excluído com sucesso!'})

app.run(port=5000, host='0.0.0.0', debug=True)