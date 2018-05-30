import json
from flask import Flask, render_template, request
import random


app = Flask(__name__)
app.debug = True


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/_get_data', methods=['POST'])
def get_data():
    """
    This function is called by an ajax function call to
    pass queries parameters and to get query results.
    """

    # Parameters for SQl queries is given by the POST method.
    # queryId is for predefined queries, others are for keyword search.
    # queryId: indicate predefined queries
    # keyword: for keyword search
    # entity: searching persons or films
    print('get data:', request.form)

    # The query/search results is returned in JSON format:
    # 'data': [{FIELD_1: VALUE_1_1, FIELD_2: VALUE_1_2, ...},
    #          {FIELD_1: VALUE_2_1, FIELD_2: VALUE_2_2, ...}, ...]
    #         To support follow-up search (for some entries),
    #         'personId' or 'filmId' as a field should be included in those dicts.
    # 'columns': a list of dictionaries
    #            Required fields:
    #                'title': title displayed on table
    #                'data': field name in data
    #            Optional fields:
    #                'idType': for follow-up search,
    #                           should be 'person' or 'film'
    n_cols = 5
    n_data = 10

    # basic table
    cols = [{'title': 'column_' + str(i + 1),
             'data': 'column_' + str(i + 1)}
            for i in range(n_cols)]
    data = [{cols[col]['data']: 0 * i + col + 1 + random.random()
             for col in range(n_cols)}
            for i in range(n_data)]

    # add ids
    [p, f] = random.sample(list(range(n_cols)), k=2)
    cols[p]['idType'] = 'person'
    cols[f]['idType'] = 'film'
    for row in data:
        row['personId'] = random.random()
        row['filmId'] = random.random()
        row.pop('column_' + str(random.randrange(n_cols) + 1))

    json_data = {'columns': cols, 'data': data}
    print(json_data)

    return json.dumps(json_data)


@app.route('/_get_info', methods=['POST'])
def get_info():
    """
    This function is for follow-up info on a person or a film.
    The request form has the form {'p': personId} or {'f': filmId}.
    The return value is displayed as a string.
    """

    print('get info:', request.form)

    if 'p' in request.form:
        ret = 'personID: ' + request.form['p']
    elif 'f' in request.form:
        ret = 'filmID: ' + request.form['f']
    else:
        assert 0

    ret += '\n\nWrite some information here.'

    return ret


@app.route('/_insert_data', methods=['POST'])
def insert_data():
    """
    Insert new person or film.
    The request form is a dictionary:
        entity: 'film' or 'person'
        name: name/title of the new data entry
    """

    print('insert:', request.form)

    return 'Insert success.'


@app.route('/_delete', methods=['POST'])
def delete():
    """
    Delete a person or a film.
    The request form has the form {'p': personId} or {'f': filmId}.
    The return value can be any message.
    """

    print('delete:', request.form)

    return 'Delete success.'


if __name__ == '__main__':
    app.run()
