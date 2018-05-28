import json
from flask import Flask, render_template, request
import random
import time


app = Flask(__name__)
app.debug = True


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/_get_data', methods=["POST"])
def get_data():
    """
    This function is called by an ajax function call to
    pass queries parameters and to get query results.
    """

    # Parameters for SQl queries is given by the POST method
    print(request.form['query_id'])

    # The query result is returned in JSON format:
    # 'columns': column name.
    #            [{'title': COLUMN_1_NAME},
    #             {'title': COLUMN_2_NAME}, ...]
    # 'data': query result.
    #         [[ROW_1_COLUMN_1, ROW_1_COLUMN_2, ...],
    #          [ROW_2_COLUMN_1, ROW_2_COLUMN_2, ...], ...]
    n_cols = 3
    n_data = 10
    cols = [{'title': 'column_' + str(i + 1)}
            for i in range(n_cols)]
    data = [[0 * i + col + 1 + random.random()
              for col in range(n_cols)]
            for i in range(n_data)]
    json_data = {'columns': cols,
                 'data': data}
    print(json_data)

    return json.dumps(json_data)


if __name__ == "__main__":
    app.run()
