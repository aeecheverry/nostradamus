from flask import request, jsonify, Blueprint
import pandas as pd

api = Blueprint('api', __name__, template_folder='templates')


p_accidente_global = 1 #probabilidad de tener un accidente en chile, una constante que deberia mostrarse en el sitio web como una variable "p"
eod_freq = pd.read_csv('./resources/eod_freq.csv')
suseso_freq = pd.read_csv('./resources/suseso_freq.csv')
table = pd.read_csv('./resources/gravedades.csv')

# params: comuna_origen, comuna_destino, tramo_dist, vehiculo_paciente, day_period, rango_edad, genero, dow
# see suseso_freq.csv and eod_freq.csv files for possible values
@api.route('/api/probability', methods=['GET'])
def probability():
    comuna_origen = request.args.get('comuna_origen')
    comuna_destino = request.args.get('comuna_destino')
    tramo_dist = request.args.get('tramo_dist')
    vehiculo_paciente = request.args.get('vehiculo_paciente')
    day_period = request.args.get('day_period')
    rango_edad = request.args.get('rango_edad')
    genero = request.args.get('genero')
    dow = request.args.get('dow')
    
    query = []
    if(comuna_origen):
        query.append("ComunaOrigen == '{}'".format(comuna_origen))
    if(comuna_destino):
        query.append("ComunaDestino == '{}'".format(comuna_destino))
    if(tramo_dist):
        query.append("tramo_dist == '{}'".format(tramo_dist))
    if(vehiculo_paciente):
        query.append("vehiculo_paciente == '{}'".format(vehiculo_paciente))
    if(day_period):
        query.append("day_period == '{}'".format(day_period))
    if(rango_edad):
        query.append("rango_edad == {}".format(rango_edad))
    if(genero):
        query.append("genero == '{}'".format(genero))
    query_dow = []
    peso_eod = 'peso'
    if(dow):
        query_dow.append("day_week == {}".format(dow))
        if(dow == '6'):
            peso_eod = 'pesoSabado'
        elif(dow == '7'):
            peso_eod = 'pesoDomingo'
    
    p_accidente = suseso_freq.query(' & '.join(query + query_dow))['freq'].sum()
    #print(' & '.join(query + query_dow))
    #print("original", suseso_freq[(suseso_freq['vehiculo_paciente'] == 'Automóvil/Camioneta') & (suseso_freq['day_week'] == 0)]['freq'].sum())
    p_viaje = eod_freq.query(' & '.join(query))[peso_eod].sum()
    #print(p_accidente, p_viaje)
    probabilidad = p_accidente/p_viaje * p_accidente_global
    
    return jsonify({"probability": probabilidad})



def delta_gravedad(categoria, column):
    if categoria in ['DistManhattan', 'pcnt_edad']:
        delta = table[table['categoria']==categoria]['gravedad(dias)'].iloc[0]
        return [(int(column)+x, delta*x) for x in [-10, -1, 1, 10]]
       
    rows = table[table['categoria']==categoria]
    #if is reference value
    delta = 0
    referencia = rows['referencia'].iloc[0]
    if referencia != column:
        delta = rows[rows['columna'] == column]['gravedad(dias)'].iloc[0]
    return [(x if x != column else referencia, y if x!=column else -delta)
            for x,y in zip(rows['columna'], rows['gravedad(dias)'] - delta)]


options = ['vehiculo_paciente', 'pcnt_genero', 'day_of_week', 'day_period','month','DistManhattan','pcnt_edad']
# params: categoria, column
# to see possible values for category see gravedades.csv file
@api.route('/api/severity', methods=['GET'])
def severity():
    print(eod_freq)
    # Define a list of required parameters
    required_params = ['category', 'column']

    # Check if all required parameters are present
    missing_params = [param for param in required_params if param not in request.args]
    
    
    # If there are missing parameters, return an error message
    if missing_params:
        response = jsonify({
            "error": "Missing required parameters",
            "missing_parameters": missing_params
        })
        response.status_code = 400  # Bad Request
        return response
    
    category = request.args.get('category')
    if(category not in options):
        return jsonify({"error": "Category not found. Valid categories are: pcnt_genero, day_of_week, day_period, month, DistManhattan, pcnt_edad"})
    
    severity = delta_gravedad(category, request.args.get('column'))
    return jsonify({"severity": severity})
