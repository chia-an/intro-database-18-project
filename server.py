import json
from flask import Flask, render_template, request
import random
import cx_Oracle

ip = 'diassrv2.epfl.ch'
port = 1521
SID = 'orcldias'
dsn_tns = cx_Oracle.makedsn(ip, port, SID)
con = cx_Oracle.connect('DB2018_G28', 'DB2018_G28', dsn_tns)

app = Flask(__name__)
app.debug = True

q = []
c = []
q.append("""SELECT T.TITLE, T.TIME
FROM (
  SELECT CLIPS.TITLE, CLIPS_RELEASES.TIME
  FROM CLIPS
  JOIN CLIPS_RELEASES ON CLIPS_RELEASES.CLIPID = CLIPS.CLIPID
  JOIN COUNTRIES ON COUNTRIES.COUNTRYID = CLIPS_RELEASES.COUNTRYID
  WHERE COUNTRIES.NAME = 'France' and CLIPS_RELEASES.TIME IS NOT NULL
  ORDER BY CLIPS_RELEASES.TIME DESC
) T
WHERE rownum <= 10""")
c.append(["title", "time"])

q.append("""SELECT COUNTRIES.NAME, T.CNT
FROM (
  SELECT CLIPS_RELEASES.COUNTRYID, COUNT(CLIPS.CLIPID) AS CNT
  FROM CLIPS
  JOIN CLIPS_RELEASES ON CLIPS_RELEASES.CLIPID = CLIPS.CLIPID
  WHERE EXTRACT(YEAR FROM CLIPS_RELEASES.RELEASEDATE) = 2001
  GROUP BY CLIPS_RELEASES.COUNTRYID
) T
JOIN COUNTRIES ON COUNTRIES.COUNTRYID = T.COUNTRYID""")
c.append(["name", "cnt"])

q.append("""SELECT GENRES.NAME, T.CNT
FROM (
  SELECT CLIPS_GENRES.GENREID, COUNT(CLIPS.CLIPID) AS CNT
  FROM CLIPS
  JOIN CLIPS_RELEASES ON CLIPS_RELEASES.CLIPID = CLIPS.CLIPID
  JOIN COUNTRIES ON COUNTRIES.COUNTRYID = CLIPS_RELEASES.COUNTRYID
  JOIN CLIPS_GENRES ON CLIPS_GENRES.CLIPID = CLIPS.CLIPID
  --JOIN GENRES ON GENRES.GENREID = CLIPS_GENRES.GENREID
  WHERE EXTRACT(YEAR FROM CLIPS_RELEASES.RELEASEDATE) >= 2013 and
        COUNTRIES.NAME = 'USA'
  GROUP BY CLIPS_GENRES.GENREID
) T
JOIN GENRES ON GENRES.GENREID = T.GENREID""")
c.append(["name", "cnt"])

q.append("""SELECT PERSONS.NAME
FROM (
	SELECT PERSONID
	FROM ACTING
	GROUP BY PERSONID
	ORDER BY COUNT(CLIPID) DESC
) T
JOIN PERSONS ON PERSONS.PERSONID = T.PERSONID
WHERE rownum = 1""")
c.append(["name"])

q.append("""SELECT CNT
FROM (
	SELECT COUNT(CLIPID) AS CNT
	FROM DIRECTING
	GROUP BY PERSONID
	ORDER BY CNT DESC
)
WHERE rownum = 1""")
c.append(["cnt"])

q.append("""SELECT PERSONS.NAME
FROM (
  SELECT DISTINCT PERSONID
  FROM (
    SELECT PERSONID, COUNT(*) AS CNT
    FROM (
      SELECT DISTINCT PERSONID, CLIPID FROM ACTING
      UNION ALL
      SELECT DISTINCT PERSONID, CLIPID FROM DIRECTING
      UNION ALL
      SELECT DISTINCT PERSONID, CLIPID FROM PRODUCING
      UNION ALL
      SELECT DISTINCT PERSONID, CLIPID FROM WRITING
    )
    GROUP BY PERSONID, CLIPID
  )
  WHERE CNT >= 2
) T
JOIN PERSONS ON PERSONS.PERSONID = T.PERSONID""")
c.append(["name"])

q.append("""SELECT LANGUAGES.NAME
FROM (
	SELECT LANGUAGEID
	FROM CLIPS_LANGUAGES
	GROUP BY LANGUAGEID
	ORDER BY COUNT(CLIPID) DESC
) T
JOIN LANGUAGES ON LANGUAGES.LANGUAGEID = T.LANGUAGEID
WHERE rownum <= 10""")
c.append(["name"])

q.append("""SELECT PERSONS.NAME
FROM (
  SELECT ACTING.PERSONID, COUNT(ACTING.CLIPID) AS CNT
	FROM ACTING
  JOIN CLIPS ON CLIPS.CLIPID = ACTING.CLIPID
	WHERE CLIPS.TYPE LIKE 'VG' -- __USER_SPECIFIED_TYPE__
	GROUP BY ACTING.PERSONID
	ORDER BY CNT DESC
) T
JOIN PERSONS ON PERSONS.PERSONID = T.PERSONID
WHERE rownum = 1""")
c.append(["type", "name"])

def predefined(qID):
    cur = con.cursor()
    result = cur.execute(q[qID]).fetchall()
    cols = []
    for x in c[qID]:
        cols.append({"title": x, "data": x})
    ret = []
    for x in result:
        dc = {}
        for i in range(len(x)):
            dc[c[qID][i]] = x[i]
        ret.append(dc)
    # print(ret)
    return cols, ret


@app.route('/')
def index():
    return render_template('index.html')


def search(keyword, entity):
    keyword = "%" + keyword + "%"
    cur = con.cursor()
    ret = []
    if entity == "person":
        response = cur.execute("SELECT * FROM PERSONS WHERE NAME LIKE :1",
                               (keyword,)).fetchall()
        # print(type(response))
        for x in response:
            ret.append({'personId': x[0], 'name': x[1]})
        cols = [{'title': 'personId', 'data': 'personId', 'idType': 'person'},
                {'title': 'name', 'data': 'name'}, ]
    else:
        response = cur.execute("SELECT * FROM CLIPS WHERE TITLE LIKE :1",
                               (keyword,)).fetchall()
        # print(type(response))
        for x in response:
            ret.append({'filmId': x[0], 'title': x[1]})
        cols = [{'title': 'filmId', 'data': 'filmId', 'idType': 'film'},
                {'title': 'title', 'data': 'title'}, ]

    return cols, ret


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
    req = request.form
    if 'queryId' in req:
        queryId = int(req['queryId'])
        cols, data = predefined(queryId)
    elif 'entity' in req:
        entity = req['entity']
        keyword = req['keyword']
        cols, data = search(keyword, entity)

    else:
        return "Invalid query"

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
    # n_cols = 5
    # n_data = 10
    #
    # # basic table
    # cols = [{'title': 'column_' + str(i + 1),
    #          'data': 'column_' + str(i + 1)}
    #         for i in range(n_cols)]
    # data = [{cols[col]['data']: 0 * i + col + 1 + random.random()
    #          for col in range(n_cols)}
    #         for i in range(n_data)]
    #
    # # add ids
    # [p, f] = random.sample(list(range(n_cols)), k=2)
    # cols[p]['idType'] = 'person'
    # cols[f]['idType'] = 'film'
    # print(cols)
    # for row in data:
    #     row['personId'] = random.random()
    #     row['filmId'] = random.random()
    #     row.pop('column_' + str(random.randrange(n_cols) + 1))

    # print(cols)
    json_data = {'columns': cols, 'data': data}
    # print(json_data)

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
        cur = con.cursor()
        pID = int(request.form['p'])
        ret = cur.execute("SELECT * FROM PERSONS WHERE PERSONID=:1", (pID,)).fetchall()
        return json.dumps("Name of this person is " + str(ret[0][1]))
    elif 'f' in request.form:
        cur = con.cursor()
        cID = int(request.form['f'])
        ret = cur.execute("SELECT * FROM CLIPS WHERE CLIPID=:1", (cID,)).fetchall()
        output = "Title: " + str(ret[0][1]) + ";  "
        if ret[0][2] is not None:
            output += " Year: " + str(ret[0][2]) + ";  "
        return json.dumps(output)
    else:
        pass

    return ""


@app.route('/_insert_data', methods=['POST'])
def insert_data():
    """
    Insert new person or film.
    The request form is a dictionary:
        entity: 'film' or 'person'
        name: name/title of the new data entry
    """

    cur = con.cursor()
    if request.form['entity'] == 'person':
        cur = con.cursor()

        personId = cur.execute("SELECT MAX(PERSONID) FROM PERSONS").fetchall()[0][0]
        cur = con.cursor()
        cur.execute("insert into PERSONS (PERSONID, NAME) "
                    "values (:1, :2)", (personId + 1, request.form['name'],))
    else:
        cur = con.cursor()

        clipID = cur.execute("SELECT MAX(CLIPID) FROM CLIPS").fetchall()[0][0]
        cur = con.cursor()
        cur.execute("insert into CLIPS (CLIPID, TITLE) "
                    "values (:1, :2)", (clipID + 1, request.form['name'],))
    con.commit()
    return 'Insert success.'


@app.route('/_delete', methods=['POST'])
def delete():
    """
    Delete a person or a film.
    The request form has the form {'p': personId} or {'f': filmId}.
    The return value can be any message.
    """
    cur = con.cursor()
    # print('delete:', request.form)
    if 'p' in request.form:
        pID = int(request.form['p'])
        cur.execute("DELETE FROM PERSONS WHERE PERSONID=:1",
                    (pID,))
    else:
        fID = int(request.form['f'])
        cur.execute("DELETE FROM CLIPS WHERE CLIPID=:1",
                    (fID,))
    con.commit()
    return 'Delete success.'


if __name__ == '__main__':
    app.run()
